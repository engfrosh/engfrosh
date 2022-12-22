import os

from channels.routing import ProtocolTypeRouter
from django.core.asgi import get_asgi_application
from check_in.consumers import CheckInConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'engfrosh_site.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter([
    ])
})
