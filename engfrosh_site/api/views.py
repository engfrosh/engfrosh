from rest_framework import permissions, authentication, status
from rest_framework.views import APIView
from .serializers import VerificationPhotoSerializer
from rest_framework.response import Response
from common_models.models import VerificationPhoto, UserDetails
from datetime import datetime
from schedule.models import CalendarRelation
from django.urls import reverse
from django.contrib.auth.models import User
from engfrosh_common.AWS_SES import send_SES
from ics import Event
import ics
from api import renderer
import rest_framework
from django.contrib.contenttypes.models import ContentType
import logging

logger = logging.getLogger("api.views")


class ICSAPI(APIView):
    renderer_classes = [renderer.PassthroughRenderer, rest_framework.renderers.JSONRenderer]

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
                ct = ContentType.objects.get_for_model(group)
                relations = CalendarRelation.objects.filter(content_type=ct, object_id=group.id)
                for relation in relations:
                    calendars.update({relation.calendar})
            except Exception as e:
                logger.error(e)
                continue
        try:
            ct = ContentType.objects.get_for_model(user)
            relations = CalendarRelation.objects.filter(content_type=ct, object_id=user.id)
            for relation in relations:
                calendars.update({relation.calendar})
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
            e = Event()
            e.name = event.title
            e.begin = event.start
            e.end = event.end
            e.description = event.description
            e.created = event.created_on
            e.last_modified = event.updated_on
            cal.events.add(e)
        data = cal.serialize()
        resp = Response(data, content_type="text/calendar")
        resp.accepted_media_type = "text/calendar"
        return resp


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
                ct = ContentType.objects.get_for_model(group)
                relations = CalendarRelation.objects.filter(content_type=ct, object_id=group.id)
                for relation in relations:
                    calendars.update({relation.calendar})
            except Exception as e:
                logger.error(e)
                continue
        try:
            ct = ContentType.objects.get_for_model(user)
            relations = CalendarRelation.objects.filter(content_type=ct, object_id=user.id)
            for relation in relations:
                calendars.update({relation.calendar})
        except Exception:
            pass
        # This is ripped right from the django-scheduler code
        # https://github.com/llazzaro/django-scheduler/blob/8aa6f877f17e5b05f17d7c39e93d8e73625b0a65/schedule/views.py#L357
        response_data = []
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
            url = ""
            if request.user.has_perm("auth.change_user"):
                url = reverse("edit_event", args=[event.id])
            else:
                url = reverse("view_event", args=[event.id])
            response_data.append(
                {
                    "id": event.id,
                    "title": event.title,
                    "start": event.start,
                    "end": event.end,
                    "existed": True,
                    "event_id": event.id,
                    "color": event.color_event,
                    "description": event.description,
                    "creator": str(event.creator),
                    "calendar": event.calendar.slug,
                    "url": url
                })
        return Response(response_data)
