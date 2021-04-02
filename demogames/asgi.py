import os
import django

django.setup()
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import cofx.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'demogames.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            cofx.routing.websocket_urlpatterns
        )
    ),
})