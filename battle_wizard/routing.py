from django.urls import re_path
from battle_wizard.consumers import battle_wizardConsumer
from battle_wizard.consumers import battle_wizardCustomConsumer

websocket_urlpatterns = [
    re_path(r'^ws/play/(?P<game_type>\w+)/(?P<room_code>\w+)/$', battle_wizardConsumer.as_asgi()),
    re_path(r'^ws/play_custom/(?P<custom_game_id>\w+)/(?P<room_code>\w+)/$', battle_wizardCustomConsumer.as_asgi()),
]