from rest_framework import permissions, authentication, status
from rest_framework.views import APIView
from .serializers import VerificationPhotoSerializer
from rest_framework.response import Response
from common_models.models import VerificationPhoto, UserDetails, FacilShiftSignup, FacilShift
from datetime import datetime
from schedule.models import CalendarRelation, Calendar
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


def get_events(user):
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
    result = []
    for calendar in calendars:
        # create flat list of events from each calendar
        for event in calendar.events.all():
            e = {"name": event.title, "start": event.start, "end": event.end,
                 "desc": event.description, "created_at": event.created_on,
                 "updated_at": event.updated_on, "creator": str(event.creator),
                 "id": event.id, "colour": event.color_event, "calendar": event.calendar.slug,
                 "all": True}
            result.append(e)
    for s in FacilShiftSignup.objects.select_related('shift').filter(user=user):
        shift = s.shift
        # start=shift.start, end=shift.end, title=shift.name, description=shift.desc
        e = {"name": shift.name, "start": shift.start, "end": shift.end, "desc": shift.desc,
             "created_at": None, "updated_at": None, "creator": None, "id": "shift", "colour": "blue",
             "calendar": "shifts", "all": True}
        result.append(e)
    if user.has_perm("common_models.shift_manage"):
        for shift in FacilShift.objects.all():
            # start=shift.start, end=shift.end, title=shift.name, description=shift.desc
            e = {"name": shift.name, "start": shift.start, "end": shift.end, "desc": shift.desc,
                 "created_at": None, "updated_at": None, "creator": None, "id": "allshift", "colour": "green",
                 "calendar": "allshifts", "all": False}
            result.append(e)
    if user.has_perm("common_models.calendar_manage"):
        slugs = []
        for c in calendars:
            slugs.append(c.slug)
        for calendar in Calendar.objects.exclude(slug__in=slugs):
            for event in calendar.events.all():
                e = {"name": event.title, "start": event.start, "end": event.end,
                     "desc": event.description, "created_at": event.created_on,
                     "updated_at": event.updated_on, "creator": str(event.creator),
                     "id": event.id, "colour": event.color_event, "calendar": event.calendar.slug,
                     "all": False}
                result.append(e)
    return result


class ICSAPI(APIView):
    renderer_classes = [renderer.PassthroughRenderer, rest_framework.renderers.JSONRenderer]

    def get(self, request, **kwargs):
        uid = kwargs.get("uid")
        details = UserDetails.objects.filter(int_frosh_id=uid).first()
        if details is None:
            return Response("Invalid request", status=status.HTTP_400_BAD_REQUEST)
        cal = ics.Calendar()
        event_list = get_events(details.user)
        for event in event_list:
            if not event['all']:
                continue
            e = Event()
            e.name = event['name']
            e.begin = event['start']
            e.end = event['end']
            e.description = event['desc']
            e.created = event['created_at']
            e.last_modified = event['updated_at']
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
        response_data = []
        event_list = get_events(user)
        """
                {"name": event.title, "start": event.start, "end": event.end,
                 "desc": event.description, "created_at": event.created_on,
                 "updated_at": event.updated_on, "creator": str(event.creator),
                 "id": event.id, "colour": event.color_event, "calendar": event.calendar.slug}
        """
        for event in event_list:
            if event['start'] is None or event['end'] is None or \
               event['start'] <= end_time and event['start'] >= start_time:
                url = ""
                if event['id'] != "shift" and event['id'] != "allshift":
                    if request.user.has_perm("auth.change_user"):
                        url = reverse("edit_event", args=[event['id']])
                    else:
                        url = reverse("view_event", args=[event['id']])
                else:
                    if event['id'] == "shift":
                        url = reverse("facil_shifts")
                    else:
                        url = reverse("mailing_list")
                response_data.append(
                    {
                        "id": event['id'],
                        "title": event['name'],
                        "start": event['start'],
                        "end": event['end'],
                        "existed": True,
                        "event_id": event['id'],
                        "color": event['colour'],
                        "description": event['desc'],
                        "creator": event['creator'],
                        "calendar": event['calendar'],
                        "url": url,
                        "all": event['all'],
                    })
        return Response(response_data)
