import json
import random
import string

from django.shortcuts import render, redirect
from django.http import Http404

def index(request):
    if request.method == "POST":
        return redirect("/games")
        #username = request.POST.get("username")
        #game_type = request.POST.get("game_type")
        #room_code = request.POST.get("room_code_ccg")
        #if not room_code:
        #    room_code = request.POST.get("room_code_deckbuilder")
        #return redirect(
        #    '/play/%s/%s?&username=%s' 
        #    %(game_type, room_code, username)
        #)
    return render(request, "index.html", {})

def game(request, room_code, game_type):
    context = {
        "username": request.GET.get("username"), 
        "room_code": room_code,
        "game_type": game_type
    }
    return render(request, "game.html", context)


def games(request):
    game_types = ["ingame", "pregame"]
    try:
        json_data = open("queue_database.json")
        queue_database = json.load(json_data) 
    except:
        queue_database = {"ingame": {"open_games":[], "starting_id":3000}, "pregame": {"open_games":[], "starting_id":3000}}
    return render(request, "games.html", {"game_types": game_types, "queue_database": queue_database})


def find_game(request, game_type):
    try:
        json_data = open("queue_database.json")
        queue_database = json.load(json_data) 
    except:
        queue_database = {"ingame": {"open_games":[], "starting_id":3000}, "pregame": {"open_games":[], "starting_id":3000}}

    if len(queue_database[game_type]["open_games"]) > 0:
        room_code = queue_database[game_type]["open_games"].pop()
    else:
        room_code = queue_database[game_type]["starting_id"]
        queue_database[game_type]["starting_id"] += 1
        queue_database[game_type]["open_games"].append(room_code)

    with open("queue_database.json", 'w') as outfile:
        json.dump(queue_database, outfile)

    username = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10)) 

    return redirect(
            '/play/%s/%s?&username=%s' 
            %(game_type, room_code, username)
    )
