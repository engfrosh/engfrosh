from django.urls import path
import check_in.consumers

websocket_urlpatterns = [
    path('ws/check_in/', check_in.consumers.CheckInConsumer.as_asgi())
]

