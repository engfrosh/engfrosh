from django.urls import re_path
import check_in.routing as check_in_routing
from channels.routing import URLRouter

websocket_urlpatterns = URLRouter([
    re_path('ws/check_in/', URLRouter(check_in_routing.websocket_urlpatterns)),
])
