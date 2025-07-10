from django.urls import path

from . import views

urlpatterns = [
    path('photo', views.VerificationPhotoAPI.as_view(), name="photo"),
    path('calendar', views.CalendarAPI.as_view(), name="calendar_api"),
    path('ics/<slug:uid>', views.ICSAPI.as_view(), name="ics_api"),
    path('randall/locate', views.RandallAPI.as_view(), name="randall_locate_api"),
    path('randall/availability', views.RandallAvailabilityAPI.as_view(), name="randall_availability_api")
]
