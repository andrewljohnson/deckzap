import datetime
import json
import pathlib
from battle_wizard.models import Deck, GameRecord, GlobalDeck
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User


class JsonDB:
    def __init__(self):
        pathlib.Path('database/games').mkdir(parents=True, exist_ok=True) 

    def game_database(self, game_filename):
        try:
            json_data = open(f"database/games/{game_filename}.json")
            game_database = json.load(json_data) 
            return game_database
        except:
            return {}

    def save_game_database(self, game_dict, game_filename):
        with open(f"database/games/{game_filename}.json", 'w') as outfile:
            json.dump(game_dict, outfile)

    def save_new_to_decks_database(self, username, deck):
        self.maybe_save_global_deck(deck, username)
        self.save_new_deck(deck, username)

    def save_new_deck(self, deck, username):
        cards_hash = self.hash_for_deck(deck)
        global_deck = GlobalDeck.objects.get(cards_hash=cards_hash)
        deck = Deck.objects.create(global_deck=global_deck, owner=User.objects.get(username=username), date_created=datetime.datetime.now(), title=deck["title"])
        deck.save()

    def maybe_save_global_deck(self, deck, username):
        cards_hash = self.hash_for_deck(deck)
        global_deck = None
        try:
            global_deck = GlobalDeck.objects.get(cards_hash=cards_hash)
        except ObjectDoesNotExist:
            global_deck = GlobalDeck.objects.create(cards_hash=cards_hash, deck_json=deck, author=User.objects.get(username=username), date_created=datetime.datetime.now())
            global_deck.save()
        return global_deck

    def hash_for_deck(self, deck):
        strings = []
        for key in deck["cards"]:
            strings.append(f"{key}{deck['cards'][key]}")
        strings.sort()
        return "".join(strings)

    def queue_database(self):
        try:
            json_data = open("database/queue_database.json")
            queue_database = json.load(json_data) 
        except:
            queue_database = {"pvp": {"waiting_players":[]}}
        return queue_database
    
    def join_ai_game_in_queue_database(self):
        game_record = GameRecord.objects.create(date_created=datetime.datetime.now())
        game_record.save()
        game_record_id = game_record.id
        return game_record_id

    def all_cards(self, require_images=False, include_tokens=True):
        json_data = open('battle_wizard/battle_wizard_cards.json')
        all_cards = json.load(json_data)
        subset = []
        for c in all_cards:
            if include_tokens or ("is_token" not in c or c["is_token"] == False):
                if "image" in c or not require_images:
                    subset.append(c)
        return subset
