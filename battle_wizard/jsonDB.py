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
            queue_database = {"pvai": {},
                              "pvp": {}
            }
            game_types = ["constructed"]
            for gt in game_types:
                queue_database["pvai"][gt] = {"starting_id":0} 
                queue_database["pvp"][gt] = {"open_games":[], "starting_id":0}

        return queue_database
    
    def join_game_in_queue_database(self, ai_type, game_type, queue_database):
        return self.room_code_for_type(ai_type, game_type, queue_database)

    def room_code_for_type(self, ai_type, game_type, queue_database):
        is_new_room = True
        if ai_type == "pvai":
            room_code = queue_database[ai_type][game_type]["starting_id"]
            queue_database[ai_type][game_type]["starting_id"] += 1
        elif ai_type == "pvp":
            if len(queue_database[ai_type][game_type]["open_games"]) > 0:
                room_code = queue_database[ai_type][game_type]["open_games"].pop()
                is_new_room = False
            else:
                room_code = queue_database[ai_type][game_type]["starting_id"]
                queue_database[ai_type][game_type]["starting_id"] += 1
                queue_database[ai_type][game_type]["open_games"].append(room_code)
        with open("database/queue_database.json", 'w') as outfile:
            json.dump(queue_database, outfile)
        return room_code, is_new_room

    def remove_from_queue_database(self, game_type, room_code, queue_database):
        if room_code in queue_database["pvp"][game_type]["open_games"]:
            queue_database["pvp"][game_type]["open_games"].remove(room_code)
        with open("database/queue_database.json", 'w') as outfile:
            json.dump(queue_database, outfile)

    def all_cards(self):
        json_data = open('battle_wizard/battle_wizard_cards.json')
        return json.load(json_data)  

    def player_database(self):
        try:
            json_data = open("database/player_database.json")
            player_db = json.load(json_data) 
        except:
            player_db = {}
        return player_db

    def add_to_player_database(self, username, player_db):
        if username not in player_db:
            player_db[username] = {"card_counts": {}}
        with open("database/player_database.json", 'w') as outfile:
            json.dump(player_db, outfile)

    def update_deck_in_player_database(self, username, deck, player_db):
        player_db[username]["card_counts"] = deck
        with open("database/player_database.json", 'w') as outfile:
            json.dump(player_db, outfile)
        return player_db
