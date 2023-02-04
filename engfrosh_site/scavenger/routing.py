from django.urls import path
import scavenger.consumers
from channels.routing import URLRouter


websocket_urlpatterns = URLRouter([
    path('approval', scavenger.consumers.ScavConsumer.as_asgi())
])
