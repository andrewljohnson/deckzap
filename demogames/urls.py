from django.contrib import admin
from django.urls import path
from cofx.views import create
from cofx.views import find_custom_game
from cofx.views import find_game
from cofx.views import games
from cofx.views import index
from cofx.views import play_custom_game
from cofx.views import play_game
from ss.views import dnd
from ss.views import hangman

urlpatterns = [
    path('admin/', admin.site.urls),
  	path('', index),
    path('games', games),
    path('create', create),
    path('play/custom/<game_id>/<room_code>', play_custom_game),
    path('play/custom/<game_id>', find_custom_game),
  	path('play/<game_type>/<room_code>', play_game),
    path('play/<game_type>', find_game),
    path('ss/hangman', hangman),
    path('ss/dnd', dnd),
 ]
