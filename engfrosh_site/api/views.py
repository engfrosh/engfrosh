from rest_framework import permissions, authentication, status
from rest_framework.views import APIView
from .serializers import VerificationPhotoSerializer
from rest_framework.response import Response
from common_models.models import VerificationPhoto
from datetime import datetime
from schedule.models import Calendar, Occurrence
import pytz


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
        print(user.groups)
        start = request.GET.get("start")
        end = request.GET.get("end")
        if start is None or end is None:
            return Response("Invalid request", status=status.HTTP_400_BAD_REQUEST)
        utc = pytz.utc
        start_time = utc.localize(datetime.utcfromtimestamp(int(start)))
        end_time = utc.localize(datetime.utcfromtimestamp(int(end)))
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
                    }
                )
        return Response(response_data)
