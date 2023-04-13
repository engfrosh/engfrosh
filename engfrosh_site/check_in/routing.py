from django.urls import path
import check_in.consumers
from channels.routing import URLRouter


websocket_urlpatterns = URLRouter([
    path('', check_in.consumers.CheckInConsumer.as_asgi())
])
