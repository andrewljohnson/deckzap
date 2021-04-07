"""demogames URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
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
  	path('play/<game_type>/<room_code>', game),
    path('play/<game_type>', find_game),
    path('ss/hangman', hangman),
    path('ss/dnd', dnd),
 ]
