import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter
from django.core.asgi import get_asgi_application
import engfrosh_site.routing as routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'engfrosh_site.settings')
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        routing.websocket_urlpatterns
    ),
})
