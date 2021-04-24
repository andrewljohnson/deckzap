import json
import random
import string

from battle_wizard.jsonDB import JsonDB
from battle_wizard.forms import SignUpForm
from django.contrib.auth import login, authenticate 
from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import logout as logout_django
from django.contrib.auth.models import User

def index(request):
    if request.user.is_authenticated:
        return redirect(f'/u/{request.user.username}')

    return render(request, "index.html", {})

def signup(request):
    if request.user.is_authenticated:
        return redirect(f'/u/{request.user.username}')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect(f'/u/{user.username}')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

def logout(request):
    logout_django(request)
    return redirect('/')

def manifesto(request):
    return render(request, "manifesto.html", {})

def build_deck(request):
    if not request.user.is_authenticated:
        return redirect('/signup')
    deck_id = request.GET.get("deck_id", None)
    deck = {"cards": {}, "id": None}
    if deck_id:
        decks = JsonDB().decks_database()[request.user.username]["decks"]
        for d in decks:
            if d["id"] == int(deck_id):
                deck = d
    all_cards = JsonDB().all_cards()
    all_cards = sorted(all_cards, key = lambda i: (i['cost'], i['card_type']))
    return render(request, "build_deck.html", 
        {
            "all_cards": json.dumps(all_cards),
            "deck_id": deck_id,
            "json_deck": json.dumps(deck),
            "deck": deck,
        }
    )

def profile(request, username):
    return render(request, "profile.html", 
        {
            "decks": JsonDB().decks_database()[username]["decks"] if username in JsonDB().decks_database() else [],
            "username": username, 
            "account_number": User.objects.get(username=username).id - 3
        }
    )

def save_deck(request):
    if request.method == "POST":
        info = json.load(request)
        deck = info["deck"]
        deck_count = 0
        for key in deck["cards"]:
            deck_count += deck["cards"][key]
        if deck_count < 2:
            error_message = "can't build a deck that doesn't have 30 cards"
            print(error_message)
            return JsonResponse({"error": error_message})
        else: 
            decks_db = JsonDB().decks_database()
            JsonDB().save_to_decks_database(request.user.username, deck, decks_db)
            return JsonResponse({})
    else:
        return JsonResponse({"error": "Unsupported request type"})

def games(request):
    if not request.user.is_authenticated:
        return redirect('/signup')
    queue_database = JsonDB().queue_database()
    custom_game_database = JsonDB().custom_game_database()
    for g in custom_game_database["games"]:
        custom_game_id = f"custom-{g['id']}"
        if custom_game_id in queue_database:
            g["open_games"] = queue_database[g["ai_type"]][custom_game_id]["open_games"]
    return render(request, "games.html", {"queue_database": queue_database, "custom_games": custom_game_database["games"]})

def create(request):
    if not request.user.is_authenticated:
        return redirect('/signup')
    context = {
    }
    if request.method == "POST":
        ai_type = request.POST.get("ai_type")
        game_type = request.POST.get("game_type")
        custom_game_database = JsonDB().custom_game_database()
        game_info = {
            "username": request.user.username,
            "ai_type": ai_type,
            "game_type": game_type
        }
        JsonDB().save_to_custom_game_database(game_info, custom_game_database)
        return redirect("/games")
    else:
        return render(request, "create.html", context)

def find_game(request, ai_type, game_type):
    room_code, is_new_room = JsonDB().join_game_in_queue_database(ai_type, game_type, JsonDB().queue_database())
    url = f"/play/{ai_type}/{game_type}/{room_code}"
    deck_id = request.GET.get("deck_id", None)
    ai = request.GET.get("ai")
    added_one = False
    if deck_id:
        url+= f"?deck_id={deck_id}"
        added_one = True
    if ai:
        if added_one:
            url+= f"&ai={ai}"
        else:
            url+= f"?ai={ai}"
    return redirect(url)

def find_custom_game(request, game_id):
    room_code, is_new_room = JsonDB().join_custom_game_in_queue_database(game_id, JsonDB().queue_database())
    return redirect(
            '/play/custom/%s/%s' 
            %(game_id, room_code)
    )

def play_game(request, ai_type, game_type, room_code):
    room_code_int = int(room_code)
    queue_database = JsonDB().queue_database()
    last_room = request.GET.get("new_game_from_button")
    ai = request.GET.get("ai") if request.GET.get("ai") and len(request.GET.get("ai")) else None
    deck_id = request.GET.get("deck_id", None)

    get_params = ""
    added_one = False 
    for param in [["ai", ai], ["deck_id", deck_id]]:
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
        "ai": ai, 
        "room_code": room_code,
        "game_type": game_type,
        "ai_type": ai_type,
        "is_custom": True,
        "custom_game_id": game_id,
        "all_cards": json.dumps(JsonDB().all_cards())
    }
    return render(request, "game.html", context)