from django.shortcuts import render, redirect
from django.http import Http404

def index(request):
    if request.method == "POST":
        username = request.POST.get("username")
        game_type = request.POST.get("game_type")
        room_code = request.POST.get("room_code_ccg")
        if not room_code:
            room_code = request.POST.get("room_code_deckbuilder")
        return redirect(
            '/play/%s/%s?&username=%s' 
            %(game_type, room_code, username)
        )
    return render(request, "index.html", {})

def game(request, room_code, game_type):
    context = {
        "username": request.GET.get("username"), 
        "room_code": room_code,
        "game_type": game_type
    }
    return render(request, "game.html", context)