from django.urls import re_path
from battle_wizard.consumers import BattleWizardConsumer
from battle_wizard.consumers import BattleWizardMatchFinderConsumer

websocket_urlpatterns = [
    re_path(r'^ws/find_match/$', BattleWizardMatchFinderConsumer.as_asgi()),
    re_path(r'^ws/play/(?P<player_type>\w+)/(?P<room_code>\w+)/$', BattleWizardConsumer.as_asgi()),
    re_path(r'^ws/play/(?P<player_type>\w+)/(?P<room_code>\w+)/(?P<ai>\w+)/$', BattleWizardConsumer.as_asgi()),
]