from django.urls import re_path
from cofx.consumers import CoFXConsumer

websocket_urlpatterns = [
    re_path(r'^ws/play/(?P<room_code>\w+)/$', CoFXConsumer.as_asgi()),
]