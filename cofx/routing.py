from django.urls import re_path
from cofx.consumers import CoFXConsumer
from cofx.consumers import CoFXCustomConsumer

websocket_urlpatterns = [
    re_path(r'^ws/play/(?P<game_type>\w+)/(?P<room_code>\w+)/$', CoFXConsumer.as_asgi()),
    re_path(r'^ws/play_custom/(?P<custom_game_id>\w+)/(?P<room_code>\w+)/$', CoFXCustomConsumer.as_asgi()),
]