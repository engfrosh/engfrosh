import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import check_in.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'engfrosh_site.settings')
import logging
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            check_in.routing.websocket_urlpatterns
        )
    ),
})
