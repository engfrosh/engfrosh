from django.urls import path

from . import views

urlpatterns = [
    path('photo', views.VerificationPhotoAPI.as_view(), name="photo"),
    path('calendar', views.CalendarAPI.as_view(), name="calendar_api"),
    path('waiver', views.WaiverAPI.as_view(), name="waiver_api"),
    path('ics/<int:uid>', views.ICSAPI.as_view(), name="ics_api")
]
