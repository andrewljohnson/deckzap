from django.contrib import admin
from django.urls import path
from cofx.views import create
from cofx.views import find_game
from cofx.views import game
from cofx.views import games
from cofx.views import index
from ss.views import dnd
from ss.views import hangman

urlpatterns = [
    path('admin/', admin.site.urls),
  	path('', index),
    path('games', games),
    path('create', create),
  	path('play/<game_type>/<room_code>', game),
    path('play/<game_type>', find_game),
    path('ss/hangman', hangman),
    path('ss/dnd', dnd),
 ]
