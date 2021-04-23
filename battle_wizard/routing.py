from django.urls import re_path
from battle_wizard.consumers import BattleWizardConsumer
from battle_wizard.consumers import BattleWizardCustomConsumer

websocket_urlpatterns = [
    re_path(r'^ws/play/(?P<ai_type>\w+)/(?P<game_type>\w+)/(?P<room_code>\w+)/$', BattleWizardConsumer.as_asgi()),
    re_path(r'^ws/play/(?P<ai_type>\w+)/(?P<game_type>\w+)/(?P<room_code>\w+)/(?P<ai>\w+)/$', BattleWizardConsumer.as_asgi()),
    re_path(r'^ws/play_custom/(?P<custom_game_id>\w+)/(?P<room_code>\w+)/$', BattleWizardCustomConsumer.as_asgi()),
]