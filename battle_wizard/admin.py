from battle_wizard.models import Deck
from battle_wizard.models import GameRecord
from battle_wizard.models import GlobalDeck
from django.contrib import admin

admin.site.register(Deck)
admin.site.register(GameRecord)
admin.site.register(GlobalDeck)
