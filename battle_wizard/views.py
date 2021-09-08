import datetime
import json
import random
import string

from battle_wizard.data import default_deck_dwarf_bard
from battle_wizard.data import default_deck_dwarf_tinkerer
from battle_wizard.data import default_deck_genie_wizard
from battle_wizard.data import default_deck_vampire_lich
from battle_wizard.forms import SignUpForm
from battle_wizard.jsonDB import JsonDB
from battle_wizard.models import Deck, GameRecord
from django.contrib.auth import authenticate 
from django.contrib.auth import login
from django.contrib.auth import logout as logout_django
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
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
    decks = Deck.objects.filter(owner__username=username).order_by("-date_created")

    if len(decks) == 0:
        add_initial_decks(username)
        decks = Deck.objects.filter(owner__username=username).order_by("-date_created")

    # todo use ID, not username, for when we allow changing usernames
    player_list = player_records()
    player_list.sort(key=lambda x: x["win_rate"], reverse=True)
    player_rank = 0
    index = 0
    for player in player_list:
        index += 1
        if player["username"] == username:
            player_rank = index


    return render(request, "profile.html", 
        {
            "decks": decks,
            "username": username, 
            "account_number": User.objects.get(username=username).id - 3,
            "player_rank": player_rank
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
    JsonDB().save_new_to_decks_database(username, default_deck_vampire_lich())
    JsonDB().save_new_to_decks_database(username, default_deck_genie_wizard())
    JsonDB().save_new_to_decks_database(username, default_deck_dwarf_tinkerer())
    JsonDB().save_new_to_decks_database(username, default_deck_dwarf_bard())
   
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
    
    return render(request, "choose_deck_for_match.html", 
        {
            "all_cards": json.dumps(all_cards),
            "json_decks": json.dumps(json_decks(request.user.username))
        }
    )

def json_decks(username):
    deck_dicts = []
    for deck in Deck.objects.filter(owner__username=username):
        json_deck = deck.global_deck.deck_json
        json_deck["id"] = deck.id
        json_deck["title"] = deck.title
        deck_dicts.append(json_deck)
    return deck_dicts

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
    game_record_id = JsonDB().join_ai_game_in_queue_database()
    url = f"/play/{player_type}/{game_record_id}"
    url+= f"?deck_id={deck_id}"
    url+= f"&ai={ai}"
    if opponent_deck_id:
        url+= f"&opponent_deck_id={opponent_deck_id}"
    return redirect(url)

def play_game(request, player_type, game_record_id):
    """
        Play a game.
    """
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
        "game_record_id": game_record_id,
        "player_type": player_type,
        "opponent_deck_id": opponent_deck_id,
        "deck_id": deck_id
    }

    return render(request, "game.html", context)

def build_deck(request):
    """
        A view to create and edit decks.
    """
    deck_id = request.GET.get("deck_id", None)
    deck = None
    if deck_id:
        deck_object = Deck.objects.get(id=int(deck_id))
        deck = deck_object.global_deck.deck_json
        deck["id"] = deck_id
        deck["username"] = deck_object.owner.username
        deck["title"] = deck_object.title
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
        # todo enfore tech and magic limits serverside too
        if deck_count < 2:
            error_message = "can't build a deck that doesn't have 30 cards"
            print(error_message)
            return JsonResponse({"error": error_message})
        else: 
            print(deck)
            global_deck = JsonDB().maybe_save_global_deck(deck, request.user.username)
            deck_object = None
            if not "id" in deck or deck["id"] == None:
                deck_object = Deck.objects.create(date_created=datetime.datetime.now(), owner=request.user, global_deck=global_deck)
            else:
                deck_object = Deck.objects.get(id=int(deck["id"]))
                deck_object.global_deck = global_deck
                if deck_object.owner != request.user:
                    deck_object = Deck.objects.create(date_created=datetime.datetime.now(), owner=request.user, global_deck=global_deck)
            deck_object.title = info["deck"]["title"]
            deck_object.save()
            return JsonResponse({})
    else:
        return JsonResponse({"error": "Unsupported request type"})

def top_players(request):
    """
        A leaderboard showing players ranked.
    """
    player_list = player_records()
    player_list.sort(key=lambda x: x["win_rate"], reverse=True)

    sort_parameter = request.GET.get("sort", None)
    order_parameter = request.GET.get("order", None)

    if sort_parameter:
        if order_parameter and order_parameter == "descending":
            player_list.sort(key=lambda x: x[sort_parameter], reverse=True)
        else:
            player_list.sort(key=lambda x: x[sort_parameter])

    return render(request, "top_players.html", {"players": json.dumps(player_list)})

def player_records():
    players = {}
    complete_games = GameRecord.objects.filter(winner__isnull=False)
    for game in complete_games:
        for player in [game.player_one, game.player_two]:
            if player.username not in players:
                players[player.username] = {"wins":0, "losses":0, "win_rate": 0, "username": player.username}
            if player == game.winner:
                players[player.username]["wins"] += 1
            else:
                players[player.username]["losses"] += 1
            players[player.username]["win_rate"] = players[player.username]["wins"] * 1.0 / (players[player.username]["wins"] + players[player.username]["losses"])
    player_list = []
    for key in players:
        player_list.append(players[key])
    return player_list

def top_decks(request):
    """
        A leaderboard showing decks ranked.
    """
    deck_list = deck_records(request)
    deck_list.sort(key=lambda x: x["win_rate"], reverse=True)

    sort_parameter = request.GET.get("sort", None)
    order_parameter = request.GET.get("order", None)

    if sort_parameter:
        if order_parameter and order_parameter == "descending":
            deck_list.sort(key=lambda x: x[sort_parameter], reverse=True)
        else:
            deck_list.sort(key=lambda x: x[sort_parameter])

    return render(request, "top_decks.html", {"decks": json.dumps(deck_list)})

def deck_records(request):
    decks = {}
    complete_games = GameRecord.objects.filter(winner__isnull=False)
    for game in complete_games:
        for info in [(game.player_one, game.player_one_deck), (game.player_one, game.player_two_deck)]:
            player = info[0]
            deck = info[1]
            if deck.cards_hash not in decks:
                decks[deck.cards_hash] = {"wins":0, "losses":0, "win_rate": 0, "id": deck.id, "author": player.username, "title": deck.deck_json["title"] or "Unnamed Deck"}
                deck_objects = []
                if request.user.is_authenticated:
                    deck_objects = Deck.objects.filter(owner=request.user).filter(global_deck=deck)
                if len(deck_objects) == 0:
                    deck_objects = Deck.objects.filter(global_deck=deck)
                if len(deck_objects) > 0:
                    decks[deck.cards_hash]["id"] = deck_objects[0].id

            if player == game.winner:
                decks[deck.cards_hash]["wins"] += 1
            else:
                decks[deck.cards_hash]["losses"] += 1
            decks[deck.cards_hash]["win_rate"] = decks[deck.cards_hash]["wins"] * 1.0 / (decks[deck.cards_hash]["wins"] + decks[deck.cards_hash]["losses"])
    deck_list = []
    for key in decks:
        deck_list.append(decks[key])
    return deck_list
