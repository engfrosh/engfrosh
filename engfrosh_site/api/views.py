from rest_framework import permissions, authentication, status
from rest_framework.views import APIView
from .serializers import VerificationPhotoSerializer
from rest_framework.response import Response
from common_models.models import VerificationPhoto, Team, UserDetails
from datetime import datetime, timedelta
from schedule.models import Calendar, Occurrence
# import schedule.models
from django.urls import reverse
from django.contrib.auth.models import User
from engfrosh_common.AWS_SES import send_SES
from ics import Event
import ics
import pytz
from api import renderer


class ICSAPI(APIView):
    renderer_classes = [renderer.PassthroughRenderer]

    def get(self, request, **kwargs):
        uid = kwargs.get("uid")
        details = UserDetails.objects.filter(int_frosh_id=uid).first()
        if details is None:
            return Response("Invalid request", status=status.HTTP_400_BAD_REQUEST)
        cal = ics.Calendar()
        calendars = set()
        user = details.user
        for group in user.groups.all():
            try:
                calendar = Calendar.objects.get_calendar_for_object(group)
                calendars.update({calendar})
            except Exception:
                continue
        try:
            calendar = Calendar.objects.get_calendar_for_object(user)
            calendars.update({calendar})
        except Exception:
            pass
        # This is ripped right from the django-scheduler code
        # https://github.com/llazzaro/django-scheduler/blob/8aa6f877f17e5b05f17d7c39e93d8e73625b0a65/schedule/views.py#L357
        event_list = []
        # relations = schedule.models.EventRelation.objects.get_events_for_object(user)
        # for e in relations:
        #     event_list += [e.event]
        for calendar in calendars:
            # create flat list of events from each calendar
            for event in calendar.events.all():
                event_list += [event]
        for event in event_list:
            now = datetime.now(pytz.timezone("America/Toronto"))
            start = now - timedelta(days=365)
            end = now + timedelta(days=365)
            occurrences = event.get_occurrences(start, end)
            for o in occurrences:
                e = Event()
                e.name = o.title
                e.begin = o.start
                e.end = o.end
                e.description = o.description
                cal.events.add(e)
        data = cal.serialize()
        return Response(data, content_type="text/calendar")


class TreeAPI(APIView):
    authentication_classes = {authentication.SessionAuthentication, authentication.BasicAuthentication}
    permission_classes = {permissions.IsAuthenticated}

    def get(self, request, format=None):
        if not request.user.has_perm('common_models.photo_api'):
            return Response({"Error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN, content_type="application/json")
        from scavenger.views import update_tree
        id = request.GET.get("id")
        if id is None:
            return Response("Invalid request", status=status.HTTP_400_BAD_REQUEST)
        team = Team.objects.filter(group_id=id).first()
        update_tree(team)
        return Response({"success": True})


class WaiverAPI(APIView):
    def get(self, request):
        email = request.GET.get("email")
        user = User.objects.filter(email=email).first()
        if user is None:
            # Freak out
            print("Uh oh spaghetti O's, failed to find user " + email)
            body = "Hello,\nA user with email: " + email + " could not be found!"
            send_SES("noreply@engfrosh.com", "technical@engfrosh.com", "Waiver User Not Found", body, body)
            return Response({"success": False})
        else:
            details = UserDetails.objects.filter(user=user).first()
            details.waiver_completed = True
            details.save()
            return Response({"success": True})


class VerificationPhotoAPI(APIView):
    authentication_classes = {authentication.SessionAuthentication, authentication.BasicAuthentication}
    permission_classes = {permissions.IsAuthenticated}

    def post(self, request, format=None):
        if not request.user.has_perm('common_models.photo_api'):
            return Response({"Error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN, content_type="application/json")
        photo = VerificationPhoto()
        serializer = VerificationPhotoSerializer(photo, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"id": photo.id}, content_type="application/json")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CalendarAPI(APIView):
    authentication_classes = {authentication.SessionAuthentication, authentication.BasicAuthentication}
    permission_classes = {permissions.IsAuthenticated}

    def get(self, request, format=None):
        user = request.user
        start = request.GET.get("start")
        end = request.GET.get("end")
        if start is None or end is None:
            return Response("Invalid request", status=status.HTTP_400_BAD_REQUEST)
        start = datetime.strptime(start, "%Y-%m-%dT%H:%M:%S%z")
        end = datetime.strptime(end, "%Y-%m-%dT%H:%M:%S%z")
        start_time = start
        end_time = end
        calendars = set()
        for group in user.groups.all():
            try:
                calendar = Calendar.objects.get_calendar_for_object(group)
                calendars.update({calendar})
            except Exception:
                continue
        try:
            calendar = Calendar.objects.get_calendar_for_object(user)
            calendars.update({calendar})
        except Exception:
            pass
        # This is ripped right from the django-scheduler code
        # https://github.com/llazzaro/django-scheduler/blob/8aa6f877f17e5b05f17d7c39e93d8e73625b0a65/schedule/views.py#L357
        response_data = []
        i = 1
        if Occurrence.objects.all().exists():
            i = Occurrence.objects.latest("id").id + 1
        event_list = []
        # relations = schedule.models.EventRelation.objects.get_events_for_object(user)
        # for e in relations:
        #     event_list += [e.event]
        for calendar in calendars:
            # create flat list of events from each calendar
            for event in calendar.events.all():
                if event.start <= end_time and (event.end_recurring_period is None or event.end_recurring_period > start_time):  # noqa: E501
                    event_list += [event]
        for event in event_list:
            occurrences = event.get_occurrences(start_time, end_time)
            for occurrence in occurrences:
                occurrence_id = i + occurrence.event.id
                existed = False

                if occurrence.id:
                    occurrence_id = occurrence.id
                    existed = True

                recur_rule = occurrence.event.rule.name if occurrence.event.rule else None

                if occurrence.event.end_recurring_period:
                    recur_period_end = occurrence.event.end_recurring_period
                    recur_period_end = recur_period_end
                else:
                    recur_period_end = None

                event_start = occurrence.start
                event_end = occurrence.end
                url = ""
                if request.user.has_perm("auth.change_user"):
                    url = reverse("edit_event", args=[event.id])
                if occurrence.cancelled:
                    # fixes bug 508
                    continue
                response_data.append(
                    {
                        "id": occurrence_id,
                        "title": occurrence.title,
                        "start": event_start,
                        "end": event_end,
                        "existed": existed,
                        "event_id": occurrence.event.id,
                        "color": occurrence.event.color_event,
                        "description": occurrence.description,
                        "rule": recur_rule,
                        "end_recurring_period": recur_period_end,
                        "creator": str(occurrence.event.creator),
                        "calendar": occurrence.event.calendar.slug,
                        "cancelled": occurrence.cancelled,
                        "url": url
                    }
                )
        return Response(response_data)
