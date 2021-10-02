import datetime
import json
import copy 
import random
import time

from asgiref.sync import async_to_sync, sync_to_async
from channels.generic.websocket import WebsocketConsumer
from battle_wizard.game.data import all_cards
from battle_wizard.game.data import hash_for_deck
from battle_wizard.game.game import Game
from battle_wizard.models import GameRecord
from battle_wizard.models import GlobalDeck
from deckzap.settings import DEBUG
from django.contrib.auth.models import User


class BattleWizardMatchFinderConsumer(WebsocketConsumer):

    def connect(self):
        print(f"Connected to Match Finder")
        self.room_group_name = 'match_finder'

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        queue_database = self.queue_database()
        if self.username in queue_database["pvp"]["waiting_players"]:
            queue_database["pvp"]["waiting_players"].remove(self.username)
            with open("database/queue_database.json", 'w') as outfile:
                json.dump(queue_database, outfile)
        print("Disconnected from Match Finder")
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        message = json.loads(text_data)

        self.username = message["username"]

        queue_database = self.queue_database()
        if not self.username in queue_database["pvp"]["waiting_players"]:
            queue_database["pvp"]["waiting_players"].append(self.username)
            with open("database/queue_database.json", 'w') as outfile:
                json.dump(queue_database, outfile)

        if len(queue_database["pvp"]["waiting_players"]) == 2:
            game_record = GameRecord.objects.create(date_created=datetime.datetime.now())
            game_record.save()
            game_record_id = game_record.id            
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'matchfinder_message',
                    'message': {"message_type": "start_match", "game_record_id": game_record_id}
                }
            )
            queue_database["pvp"]["waiting_players"] = []
            with open("database/queue_database.json", 'w') as outfile:
                json.dump(queue_database, outfile)
        else:
            print("waiting for match")

    def queue_database(self):
        try:
            json_data = open("database/queue_database.json")
            queue_database = json.load(json_data) 
        except:
            queue_database = {"pvp": {"waiting_players":[]}}
        return queue_database
    
    def matchfinder_message(self, event):
        message = event['message']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'payload': message
        }))


class BattleWizardConsumer(WebsocketConsumer):

    def connect(self):
        self.player_type = self.scope['url_route']['kwargs']['player_type']
        self.ai = self.scope['url_route']['kwargs']['ai'] if 'ai' in self.scope['url_route']['kwargs'] else None
        self.game_record_id = self.scope['url_route']['kwargs']['game_record_id']
        self.room_group_name = 'room_%s' % self.game_record_id
        self.moves = []
        self.is_reviewing = False
        self.decks = [[], []]

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        print("Disconnected")
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        message = json.loads(text_data)

        game_record = GameRecord.objects.get(id=self.game_record_id)

        if "game" in message:
            info = message["game"]
        else:
            info = game_record.game_json
        info["game_record_id"] = self.game_record_id

        game = Game(self.player_type, info=info, player_decks=self.decks)        

        if message["move_type"] == 'NAVIGATE_GAME':
            message["log_lines"] = []
            message = self.navigate_game(game, message)  
            self.send_game_message(game.as_dict(), message)
            return

        if message["move_type"] == 'NEXT_ROOM':
            self.send_game_message(None, message)
            return

        message["log_lines"] = []
        should_add_to_move_list = message["move_type"] not in [
            "ATTACK", 
            "ACTIVATE_ARTIFACT", 
            "PLAY_CARD",
            "RESOLVE_MOB_EFFECT",
            "SELECT_ARTIFACT",
        ]
        message = game.play_move(message, should_add_to_move_list=should_add_to_move_list, is_reviewing=self.is_reviewing)   

        if message and message["move_type"] == 'JOIN':
            if len(game.players) == 1 and game.player_type == "pvai":
                message["username"] = self.ai
                message = game.play_move(message, should_add_to_move_list=True, is_reviewing=self.is_reviewing)

            if len(game.players) == 2:
                if not self.is_reviewing:
                    self.save_to_database(game, game_record)

        if len(game.players) == 2 and not self.is_reviewing:
            if game.players[0].hit_points <= 0 or game.players[1].hit_points <= 0:
                game_record.date_finished = datetime.datetime.now()
                if game.players[0].hit_points <= 0 and game.players[1].hit_points >= 0:
                    game_record.winner = User.objects.get(username=game.players[1].username)
                elif game.players[1].hit_points <= 0 and game.players[0].hit_points >= 0:
                    game_record.winner = User.objects.get(username=game.players[0].username)

        game_record.game_json = game.as_dict()
        game_record.save()

        if message:
            self.send_game_message(game.as_dict(), message)
            if message["move_type"] == "GET_TIME" and not self.is_reviewing:
                if self.player_type == "pvai":
                    game.players[1].maybe_run_ai(self)

    def save_to_database(self, game, game_record):
        game_record.date_started = datetime.datetime.now()
        game_record.player_one = User.objects.get(username=game.players[0].username)
        try:
            game_record.player_two = User.objects.get(username=game.players[1].username)
        except ObjectDoesNotExist:
            game_record.player_two = User.objects.create(username=game.players[1].username)
            game_record.player_two.save()
        game_record.player_one_deck = GlobalDeck.objects.get(cards_hash=hash_for_deck(game.players[0].deck_for_id_or_url(game.players[0].deck_id)))
        game_record.player_two_deck = GlobalDeck.objects.get(cards_hash=hash_for_deck(game.players[1].deck_for_id_or_url(game.players[1].deck_id)))
        game_record.save()

    def send_game_message(self, game_dict, message):
        # send current-game-related message to players
        if DEBUG and message and message["move_type"] != "GET_TIME":
            self.print_move(message)
        message["game"] = game_dict
        if message["move_type"] == "JOIN" and len(game_dict["players"]) == 1:
            message[ "all_cards"] = json.dumps(all_cards())

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'game_message',
                'message': message
            }
        )

    def print_move(self, message):
        move_copy = copy.deepcopy(message)
        if "game" in move_copy:
            del move_copy['game']
        if "log_lines" in move_copy:
            del move_copy['log_lines']
        if "show_spell" in move_copy:
            del move_copy['show_spell']
        if "defending_card" in move_copy:
            del move_copy['defending_card']

        self.moves.append(move_copy)
        print(f"send_game_message: {json.dumps(move_copy, indent=4)}")

    def game_message(self, event):
        '''
            Gets called once per recipient of a message.
        '''
        message = event['message']
        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'payload': message
        }))

    # todo move review_game and is_reviewing to consumer
    def navigate_game(self, game, original_message):
        review_game = Game("pvp", info={}, player_decks=self.decks)
        self.is_reviewing = True
        game.moves[0]["discipline"] = game.players[0].discipline
        game.moves[1]["discipline"] = game.players[1].discipline
        game.moves[0]["initial_deck"] = [c.as_dict() for c in game.players[0].initial_deck]
        game.moves[1]["initial_deck"] = [c.as_dict() for c in game.players[1].initial_deck]
        index = 0
        log_lines = []
        for move in game.moves:
            if index > original_message["index"] - 1 and original_message["index"] > -1:
                break
            move["log_lines"] = []
            message = review_game.play_move(move, is_reviewing=self.is_reviewing)
            if message["log_lines"] != []:
                log_lines += message["log_lines"]
            index += 1
        original_message["log_lines"] = log_lines  
        username = original_message['username']
        if original_message["index"] == -1:
            self.is_reviewing = False
            original_message["log_lines"].append(f"{username} resumed the game.")
        else:
            original_message["review_game"] = review_game.as_dict()
            original_message["log_lines"].append(f"{username} navigated the game to move {original_message['index']}.")
        return original_message

