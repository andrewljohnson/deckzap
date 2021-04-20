import json
import random
import string

from battle_wizard.jsonDB import JsonDB
from django.shortcuts import render, redirect
from django.http import Http404


def manifesto(request):
    return render(request, "manifesto.html", {})

def index(request):
    if request.method == "POST":
        if 'Play Games' == request.POST.get('menu'):
            return redirect("/games")
        else:
            return redirect("/create")
    return render(request, "index.html", {})

def games(request):
    queue_database = JsonDB().queue_database()
    custom_game_database = JsonDB().custom_game_database()
    for g in custom_game_database["games"]:
        custom_game_id = f"custom-{g['id']}"
        if custom_game_id in queue_database:
            g["open_games"] = queue_database[g["ai_type"]][custom_game_id]["open_games"]
    return render(request, "games.html", {"queue_database": queue_database, "custom_games": custom_game_database["games"]})

def create(request):
    context = {
    }
    if request.method == "POST":
        username = request.POST.get("username")
        ai_type = request.POST.get("ai_type")
        game_type = request.POST.get("game_type")
        if not username:
            context["error"] = "Username required."
            return render(request, "create.html", context)
        else:
            custom_game_database = JsonDB().custom_game_database()
            game_info = {
                "username": username,
                "ai_type": ai_type,
                "game_type": game_type
            }
            JsonDB().save_to_custom_game_database(game_info, custom_game_database)
            return redirect("/games")
    else:
        return render(request, "create.html", context)

def find_game(request, ai_type, game_type):
    room_code = JsonDB().join_game_in_queue_database(ai_type, game_type, JsonDB().queue_database())
    username = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10)) 
    return redirect(
            '/play/%s/%s/%s?&username=%s' 
            %(ai_type, game_type, room_code, username)
    )

def find_custom_game(request, game_id):
    room_code = JsonDB().join_custom_game_in_queue_database(game_id, JsonDB().queue_database())
    username = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10)) 
    return redirect(
            '/play/custom/%s/%s?&username=%s' 
            %(game_id, room_code, username)
    )

def play_game(request, ai_type, game_type, room_code):
    room_code_int = int(room_code)
    queue_database = JsonDB().queue_database()
    last_room = request.GET.get("new_game_from_button")
    if last_room:
        return redirect(f"/play/{ai_type}/{game_type}")

    context = {
        "username": request.GET.get("username"), 
        "room_code": room_code,
        "ai_type": ai_type,
        "game_type": game_type,
        "is_custom": False,
        "all_cards": json.dumps(JsonDB().all_cards())
    }
    return render(request, "game.html", context)


def play_custom_game(request, game_id, room_code):
    cgd = JsonDB().custom_game_database()
    game_type = None
    ai_type = None
    for game in cgd["games"]:
        if game["id"] == int(game_id):
            game_type = game["game_type"]
            ai_type = game["ai_type"]

    context = {
        "username": request.GET.get("username"), 
        "room_code": room_code,
        "game_type": game_type,
        "ai_type": ai_type,
        "is_custom": True,
        "custom_game_id": game_id,
        "all_cards": json.dumps(JsonDB().all_cards())
    }
    return render(request, "game.html", context)