import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'demogames.settings')
django.setup()
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import battle_wizard.routing


application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            battle_wizard.routing.websocket_urlpatterns
        )
    ),
})