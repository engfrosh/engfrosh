from . import views
from django.urls import path

urlpatterns = [
    path('', views.create_ticket),
    path('create', views.create_ticket, name="create_ticket"),
    path('view/<int:id>', views.view_ticket),
    path('view/<int:id>/comment', views.create_comment),
    path('view/<int:id>/action', views.ticket_action),
    path('view/', views.view_all_tickets),
]
