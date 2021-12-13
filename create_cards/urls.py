from django.urls import path
from create_cards.views import create_card
from create_cards.views import delete
from create_cards.views import effects
from create_cards.views import get_card_info
from create_cards.views import get_effect_for_info
from create_cards.views import get_power_points
from create_cards.views import mob
from create_cards.views import name_and_image
from create_cards.views import save_effects
from create_cards.views import save_mob
from create_cards.views import save_name_and_image
from create_cards.views import save_new_card
from create_cards.views import save_spell
from create_cards.views import spell

urlpatterns = [
    path('delete', delete),    
    path('save_effects', save_effects),    
    path('save_mob', save_mob),    
    path('save_name_and_image', save_name_and_image),    
    path('save_new', save_new_card),    
    path('save_spell', save_spell),    
    path('<card_id>/effects/<effect_index>', effects),
    path('<card_id>/mob', mob),
    path('<card_id>/name_and_image', name_and_image),
    path('<card_id>/spell', spell),
    path('get_card_info', get_card_info),    
    path('get_effect_for_info', get_effect_for_info),    
    path('get_power_points', get_power_points),    
    path('', create_card),    
 ]
