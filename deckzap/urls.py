from django.contrib import admin
from django.contrib.auth.views import LoginView
from django.urls import path
from battle_wizard.views import build_deck
# from battle_wizard.views import create
# from battle_wizard.views import find_custom_game
from battle_wizard.views import find_game
from battle_wizard.views import games
from battle_wizard.views import index
from battle_wizard.views import logout
# from battle_wizard.views import manifesto
# from battle_wizard.views import play_custom_game
from battle_wizard.views import play_game
from battle_wizard.views import profile
from battle_wizard.views import save_deck
from battle_wizard.views import signup
from ss.views import dnd
from ss.views import hangman

urlpatterns = [
    path('admin/', admin.site.urls),
  	path('', index),
    # path('manifesto', manifesto),
    path('games', games),
    # path('create', create),
    path('signup', signup),
     path('login', 
        LoginView.as_view(
            template_name='login.html'
        ), 
        name="login"
    ),
    path('logout', logout),
    path('build_deck', build_deck),
    path('build_deck/save', save_deck),
    # path('play/custom/<game_id>/<room_code>', play_custom_game),
    # path('play/custom/<game_id>', find_custom_game),
  	path('play/<ai_type>/<game_type>/<room_code>', play_game),
    path('play/<ai_type>/<game_type>', find_game),
    path('ss/hangman', hangman),
    path('ss/dnd', dnd),
    path('u/<username>', profile),
 ]
