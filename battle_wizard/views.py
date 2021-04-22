import json
import random
import string

from battle_wizard.jsonDB import JsonDB
from django.shortcuts import render, redirect
from django.http import Http404, JsonResponse


def index(request):
    return render(request, "index.html", {})

def manifesto(request):
    return render(request, "manifesto.html", {})

def build_deck(request):
    deck_id = request.GET.get("deck_id", None)
    deck = {"cards": {}, "id": None}
    if deck_id:
        decks = JsonDB().decks_database()[request.GET.get("username")]["decks"]
        for d in decks:
            if d["id"] == int(deck_id):
                deck = d
                print(d)
    return render(request, "build_deck.html", 
        {
            "all_cards": json.dumps(JsonDB().all_cards()),
            "deck_id": deck_id,
            "deck": json.dumps(deck),
            "username": request.GET.get("username", ''.join(random.choices(string.ascii_uppercase + string.digits, k=10)) )
        }
    )

def profile(request, username):
    return render(request, "profile.html", 
        {
            "decks": JsonDB().decks_database()[username]["decks"] if username in JsonDB().decks_database() else [],
            "username": username 
        }
    )

def save_deck(request):
    if request.method == "POST":
        info = json.load(request)
        username = info["username"]
        deck = info["deck"]
        deck_count = 0
        for key in deck["cards"]:
            deck_count += deck["cards"][key]
        if not username or len(username) == 0:
            error_message = "username required"
            return JsonResponse({"error": error_message})
        elif deck_count < 2:
            error_message = "can't build a deck that doesn't have 30 cards"
            print(error_message)
            return JsonResponse({"error": error_message})
        else: 
            decks_db = JsonDB().decks_database()
            JsonDB().save_to_decks_database(username, deck, decks_db)
            return JsonResponse({})
    else:
        return JsonResponse({"error": "Unsupported request type"})

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
    room_code, is_new_room = JsonDB().join_game_in_queue_database(ai_type, game_type, JsonDB().queue_database())
    username = request.GET.get("username", ''.join(random.choices(string.ascii_uppercase + string.digits, k=10)) )
    url = f"/play/{ai_type}/{game_type}/{room_code}?username={username}"
    deck_id = request.GET.get("deck_id", None)
    ai = request.GET.get("ai")
    if deck_id:
        url+= f"&deck_id={deck_id}"
    if ai:
        url+= f"&ai={ai}"
    return redirect(url)

def find_custom_game(request, game_id):
    room_code, is_new_room = JsonDB().join_custom_game_in_queue_database(game_id, JsonDB().queue_database())
    username = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10)) 
    return redirect(
            '/play/custom/%s/%s?&username=%s' 
            %(game_id, room_code, username)
    )

def play_game(request, ai_type, game_type, room_code):
    room_code_int = int(room_code)
    queue_database = JsonDB().queue_database()
    last_room = request.GET.get("new_game_from_button")
    username = request.GET.get("username", None)
    ai = request.GET.get("ai") if request.GET.get("ai") and len(request.GET.get("ai")) else None
    deck_id = request.GET.get("deck_id", None)

    get_params = ""
    added_one = False 
    for param in [["username", username], ["ai", ai], ["deck_id", deck_id]]:
        if param[1]:
            if added_one:
                get_params += "&"
            else:
                get_params += "?"
            get_params += param[0]
            get_params += "="
            get_params += param[1]
            added_one = True

    if last_room and ai:
        return redirect(f"/play/{ai_type}/{game_type}{get_params}")    

    context = {
        "username": request.GET.get("username"), 
        "ai": request.GET.get("ai"), 
        "room_code": room_code,
        "ai_type": ai_type,
        "game_type": game_type,
        "deck_id": deck_id,
        "is_custom": False,
        "all_cards": json.dumps(JsonDB().all_cards())
    }

    return render(request, "game.html", context)


def play_custom_game(request, game_id, room_code):
    cgd = JsonDB().custom_game_database()
    game_type = None
    ai_type = None
    ai = None
    for game in cgd["games"]:
        if game["id"] == int(game_id):
            game_type = game["game_type"]
            ai_type = game["ai_type"]
            ai = game["ai"]

    context = {
        "username": request.GET.get("username"), 
        "ai": ai, 
        "room_code": room_code,
        "game_type": game_type,
        "ai_type": ai_type,
        "is_custom": True,
        "custom_game_id": game_id,
        "all_cards": json.dumps(JsonDB().all_cards())
    }
    return render(request, "game.html", context)