from django.urls import path

from . import views

urlpatterns = [
    path('photo', views.VerificationPhotoAPI.as_view(), name="photo"),
]
