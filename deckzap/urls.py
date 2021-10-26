from django.contrib import admin
from django.contrib.auth.views import LoginView
from django.urls import path
from battle_wizard.views import build_deck
from battle_wizard.views import choose_deck_for_match
from battle_wizard.views import choose_opponent
from battle_wizard.views import create_card
from battle_wizard.views import create_card_effects
from battle_wizard.views import create_card_get_card_info
from battle_wizard.views import create_card_mob_stats
from battle_wizard.views import create_card_name_and_image
from battle_wizard.views import find_game
from battle_wizard.views import find_match
from battle_wizard.views import index
from battle_wizard.views import logout
from battle_wizard.views import play_game
from battle_wizard.views import profile
from battle_wizard.views import save_deck
from battle_wizard.views import save_effects
from battle_wizard.views import save_new_card
from battle_wizard.views import signup
from battle_wizard.views import top_decks
from battle_wizard.views import top_players


urlpatterns = [
    path('admin/', admin.site.urls),
  	path('', index),
    path('signup', signup),
    path('login', 
        LoginView.as_view(
            template_name='login.html'
        ), 
        name="login"
    ),
    path('logout', logout),
    path('u/<username>', profile),
    path('choose_opponent/<deck_id>', choose_opponent),
    path('choose_deck_for_match', choose_deck_for_match),
    path('find_match', find_match),
    path('build_deck', build_deck),
    path('build_deck/save', save_deck),
    path('play/<player_type>', find_game),
  	path('play/<player_type>/<game_record_id>', play_game),
    path('top_decks', top_decks),
    path('top_players', top_players),
    path('create_card', create_card),    
    path('create_card/save_effects', save_effects),    
    path('create_card/save_new', save_new_card),    
    path('create_card/<card_id>/effects', create_card_effects),
    path('create_card/<card_id>/mob_stats', create_card_mob_stats),
    path('create_card/<card_id>/name_and_image', create_card_name_and_image),
    path('create_card/get_card_info', create_card_get_card_info),    
 ]
