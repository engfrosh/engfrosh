from . import views
from django.urls import path

urlpatterns = [
    path('', views.index, name="randall_index"),
    path('manage', views.manage, name="randall_manage"),
    path('book', views.book, name="randall_book")
]
