from django.urls import path
from channels.routing import URLRouter
import check_in.routing

websocket_urlpatterns = URLRouter([
    path('ws/', URLRouter([
        path('check_in/', check_in.routing.websocket_urlpatterns),
    ]))
])
