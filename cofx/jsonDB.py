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
            print("need to make a new game for that ID")
            return None

    def save_game_database(self, game_dict, game_id):
        with open(f"database/games/{game_id}.json", 'w') as outfile:
            json.dump(game_dict, outfile)

    def custom_game_database(self):
        try:
            json_data = open("database/custom_game_database.json")
            custom_game_database = json.load(json_data) 
        except:
            custom_game_database = {"games": []}
        return custom_game_database

    def save_to_custom_game_database(self, game_info, custom_game_database):
        custom_game_database["games"].append(game_info)
        with open("database/custom_game_database.json", 'w') as outfile:
            json.dump(custom_game_database, outfile)

    def queue_database(self):
        try:
            json_data = open("database/queue_database.json")
            queue_database = json.load(json_data) 
        except:
            queue_database = {"ingame": {"open_games":[], "starting_id":3000}, "pregame": {"open_games":[], "starting_id":3000}}
        return queue_database
    
    def join_game_in_queue_database(self, game_type, queue_database):
        if len(queue_database[game_type]["open_games"]) > 0:
            room_code = queue_database[game_type]["open_games"].pop()
        else:
            room_code = queue_database[game_type]["starting_id"]
            queue_database[game_type]["starting_id"] += 1
            queue_database[game_type]["open_games"].append(room_code)
        return room_code
        with open("database/queue_database.json", 'w') as outfile:
            json.dump(queue_database, outfile)

    def remove_from_queue_database(self, game_type, room_code, queue_database):
        if room_code in queue_database[game_type]["open_games"]:
            queue_database[game_type]["open_games"].remove(room_code)
        with open("database/queue_database.json", 'w') as outfile:
            json.dump(queue_database, outfile)

    def all_cards(self):
        json_data = open('cofx/cofx_cards.json')
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
