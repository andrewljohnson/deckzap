import json
import random
import string

from battle_wizard.data import default_deck_dwarf_bard
from battle_wizard.data import default_deck_dwarf_tinkerer
from battle_wizard.data import default_deck_genie_wizard
from battle_wizard.data import default_deck_vampire_lich
from battle_wizard.forms import SignUpForm
from battle_wizard.jsonDB import JsonDB
from django.contrib.auth import authenticate 
from django.contrib.auth import login
from django.contrib.auth import logout as logout_django
from django.contrib.auth.models import User
from django.http import Http404
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render


def index(request):
    """
        The logged out home page, or the logged in profile page.
    """
    if request.user.is_authenticated:
        return redirect(f'/u/{request.user.username}')

    return render(request, "index.html", {})

def profile(request, username):
    """
        The home view for the logged in app.
    """
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

def signup(request):
    """
        A view to sign up for the app.
    """
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
    """
        The initial decks for a new player.
    """
    decks_db = JsonDB().decks_database()
    JsonDB().save_to_decks_database(username, default_deck_vampire_lich(), decks_db)
    JsonDB().save_to_decks_database(username, default_deck_genie_wizard(), decks_db)
    JsonDB().save_to_decks_database(username, default_deck_dwarf_tinkerer(), decks_db)
    JsonDB().save_to_decks_database(username, default_deck_dwarf_bard(), decks_db)
   
def logout(request):
    """
        A POST view to log out of the app.
    """
    logout_django(request)
    return redirect('/')

def choose_deck_for_match(request):
    """
        A view to choose a deck for a match, part of the main matching flow.
    """
    if not request.user.is_authenticated:
        return redirect('/signup')
    all_cards = JsonDB().all_cards(require_images=True, include_tokens=False)
    all_cards = sorted(all_cards, key = lambda i: (i['cost'], i['card_type'], i['name']))
    decks = JsonDB().decks_database()[request.user.username]["decks"]
    return render(request, "choose_deck_for_match.html", 
        {
            "all_cards": json.dumps(all_cards),
            "json_decks": json.dumps(decks)
        }
    )

def choose_opponent(request, deck_id):
    """
        A view to choose a human or AI opponent for a match, part of the main matching flow.
    """
    if not request.user.is_authenticated:
        return redirect('/signup')
    all_cards = JsonDB().all_cards(require_images=True, include_tokens=False)
    all_cards = sorted(all_cards, key = lambda i: (i['cost'], i['card_type'], i['name']))
    json_opponent_decks = [
        default_deck_vampire_lich(),
        default_deck_genie_wizard(),
        default_deck_dwarf_tinkerer(),
        default_deck_dwarf_bard()
    ]
    return render(request, "choose_opponent.html", 
        {
            "all_cards": json.dumps(all_cards),
            "deck_id": deck_id,
            "json_opponent_decks": json.dumps(json_opponent_decks)
        }
    )

def find_game(request, player_type):
    """
        Either start a game with player_type AI, or redirect to the match finder for [player_type human.
    """
    deck_id = request.GET.get("deck_id", None)
    ai = request.GET.get("ai")
    if not ai:
        return redirect(f"/find_match?deck_id={deck_id}")
    return play_ai_game(request, player_type, deck_id, ai)

def find_match(request):
    """
        A view to be matched with a human player.
    """
    deck_id = request.GET.get("deck_id", None)
    return render(request, "find_match.html", {"deck_id": deck_id})

def play_ai_game(request, player_type, deck_id, ai):
    """
        Redirect to start a game with an AI player.
    """
    opponent_deck_id = request.GET.get("opponent_deck_id", None)
    # if deck_id:
    room_code, is_new_room = JsonDB().join_ai_game_in_queue_database(player_type, JsonDB().queue_database())
    url = f"/play/{player_type}/{room_code}"
    url+= f"?deck_id={deck_id}"
    url+= f"&ai={ai}"
    if opponent_deck_id:
        if added_one:
            url+= f"&opponent_deck_id={opponent_deck_id}"
        else:
            url+= f"?opponent_deck_id={opponent_deck_id}"
    return redirect(url)

def play_game(request, player_type, room_code):
    """
        Play a game.
    """
    room_code_int = int(room_code)
    queue_database = JsonDB().queue_database()
    last_room = request.GET.get("new_game_from_button")
    ai = request.GET.get("ai") if request.GET.get("ai") and len(request.GET.get("ai")) else None
    deck_id = request.GET.get("deck_id", None)
    opponent_deck_id = request.GET.get("opponent_deck_id", None)

    get_params = ""
    added_one = False 
    for param in [["ai", ai], ["deck_id", deck_id], ["opponent_deck_id", opponent_deck_id]]:
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
        return redirect(f"/play/{player_type}{get_params}")    

    context = {
        "ai": request.GET.get("ai"), 
        "room_code": room_code,
        "player_type": player_type,
        "opponent_deck_id": opponent_deck_id,
        "deck_id": deck_id,
        "is_custom": False,
        "all_cards": json.dumps(JsonDB().all_cards())
    }

    return render(request, "game.html", context)

def build_deck(request):
    """
        A view to create and edit decks.
    """
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

def save_deck(request):
    """
        A POST view to save a deck.
    """
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
