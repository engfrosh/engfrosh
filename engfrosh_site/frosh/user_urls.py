from django.urls import path

from . import views

urlpatterns = [
    path('', views.user_home, name="user_home"),
    path('resources_public', views.inclusivity_public, name="inclusivity_public"),
    path('resources_private', views.inclusivity_private, name="inclusivity_private"),
    path('view_event/<int:id>', views.view_event, name="view_event"),
    path('upload_charter', views.upload_charter, name="upload_charter"),
    path('faq/<int:id>', views.faq_page, name="view_faq")
]
