import json
import random
import string

from battle_wizard.data import default_deck_genie_wizard, default_deck_dwarf_tinkerer, default_deck_dwarf_bard, default_deck_vampire_lich
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

def add_initial_decks(username):
    decks_db = JsonDB().decks_database()
    JsonDB().save_to_decks_database(username, default_deck_genie_wizard(), decks_db)
    JsonDB().save_to_decks_database(username, default_deck_dwarf_tinkerer(), decks_db)
    JsonDB().save_to_decks_database(username, default_deck_dwarf_bard(), decks_db)
    JsonDB().save_to_decks_database(username, default_deck_vampire_lich(), decks_db)
   
def logout(request):
    logout_django(request)
    return redirect('/')

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
    all_cards = JsonDB().all_cards(require_images=True, include_tokens=False)
    all_cards = sorted(all_cards, key = lambda i: (i['cost'], i['card_type'], i['name']))
    return render(request, "build_deck.html", 
        {
            "all_cards": json.dumps(all_cards),
            "deck_id": deck_id,
            "json_deck": json.dumps(deck),
            "deck": deck,
        }
    )

def profile(request, username):
    decks = JsonDB().decks_database()[username]["decks"] if username in JsonDB().decks_database() else []
    decks.reverse()

    if len(decks) == 0:
        add_initial_decks(username)
        decks = JsonDB().decks_database()[username]["decks"] if username in JsonDB().decks_database() else []
        decks.reverse()

    return render(request, "profile.html", 
        {
            "decks": decks,
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

def find_game(request, ai_type, game_type):
    return find_game_with_ux_type(request, ai_type, game_type, "play")

def find_game_with_ux_type(request, ai_type, game_type, ux_type):
    room_code, is_new_room = JsonDB().join_game_in_queue_database(ai_type, game_type, JsonDB().queue_database())
    url = f"/{ux_type}/{ai_type}/{game_type}/{room_code}"
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
