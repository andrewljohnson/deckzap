from django.urls import path
from create_cards.views import create_card
from create_cards.views import cost
from create_cards.views import effects
from create_cards.views import get_effect_for_info
from create_cards.views import mob_stats
from create_cards.views import name_and_image
from create_cards.views import save_cost
from create_cards.views import save_effects
from create_cards.views import save_mob_stats
from create_cards.views import save_name_and_image
from create_cards.views import save_new_card

urlpatterns = [
    path('save_cost', save_cost),    
    path('save_effects', save_effects),    
    path('save_mob_stats', save_mob_stats),    
    path('save_name_and_image', save_name_and_image),    
    path('save_new', save_new_card),    
    path('<card_id>/cost', cost),
    path('<card_id>/effects/<effect_index>', effects),
    path('<card_id>/effects', effects),
    path('<card_id>/mob_stats', mob_stats),
    path('<card_id>/name_and_image', name_and_image),
    path('get_effect_for_info', get_effect_for_info),    
    path('', create_card),    
 ]
