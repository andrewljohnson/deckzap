import json
import pathlib

class JsonDB:
    def __init__(self):
        pathlib.Path('database/games').mkdir(parents=True, exist_ok=True) 

    def game_database(self, game_id):
        try:
            json_data = open(f"database/games/{game_id}.json")
            custom_game_database = json.load(json_data) 
            return custom_game_database
        except:
            return None

    def save_game_database(self, game_dict, game_id):
        with open(f"database/games/{game_id}.json", 'w') as outfile:
            json.dump(game_dict, outfile)

    def custom_game_database(self):
        try:
            json_data = open("database/custom_game_database.json")
            custom_game_database = json.load(json_data) 
        except:
            custom_game_database = {"games": [], "starting_id":0}
        return custom_game_database

    def save_to_custom_game_database(self, game_info, custom_game_database):
        custom_game_database["games"].append(game_info)
        game_info["id"] = custom_game_database["starting_id"]
        custom_game_database["starting_id"] += 1
        with open("database/custom_game_database.json", 'w') as outfile:
            json.dump(custom_game_database, outfile)

    def decks_database(self):
        try:
            json_data = open("database/decks_database.json")
            decks_database = json.load(json_data) 
        except:
            decks_database = {}
        return decks_database

    def save_to_decks_database(self, username, deck, decks_database):
        if not username in decks_database:
            decks_database[username] = {"decks": [], "next_id": 0} 
        if not "id" in deck or deck["id"] == None:
            deck["id"] = decks_database[username]["next_id"]
            decks_database[username]["next_id"] += 1
            decks_database[username]["decks"].append(deck)
        else:
            found_index = None
            for d in decks_database[username]["decks"]:
                if d["id"] == deck["id"]:
                    found_index = decks_database[username]["decks"].index(d)
            try:
                decks_database[username]["decks"][found_index] = deck
            except:
                deck["id"] = decks_database[username]["next_id"]
                decks_database[username]["next_id"] += 1
                decks_database[username]["decks"].append(deck)
        with open("database/decks_database.json", 'w') as outfile:
            json.dump(decks_database, outfile)

    def queue_database(self):
        try:
            json_data = open("database/queue_database.json")
            queue_database = json.load(json_data) 
        except:
            queue_database = {"pvai": {"starting_id":0},
                              "pvp": {"waiting_players":[], "starting_id":0}
            }
        return queue_database
    
    def join_ai_game_in_queue_database(self, player_type, queue_database):
        is_new_room = True
        print(f"player_type is {player_type}")
        if player_type == "pvai":
            room_code = queue_database[player_type]["starting_id"]
            queue_database[player_type]["starting_id"] += 1
        with open("database/queue_database.json", 'w') as outfile:
            json.dump(queue_database, outfile)
        return room_code, is_new_room

    def all_cards(self, require_images=False, include_tokens=True):
        json_data = open('battle_wizard/battle_wizard_cards.json')
        all_cards = json.load(json_data)
        subset = []
        for c in all_cards:
            if include_tokens or ("is_token" not in c or c["is_token"] == False):
                if "image" in c or not require_images:
                    subset.append(c)
        return subset
