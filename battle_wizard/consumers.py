import datetime
import json
import copy 
import random
import time

from asgiref.sync import async_to_sync, sync_to_async
from channels.generic.websocket import WebsocketConsumer
from battle_wizard.game_objects import Game
from battle_wizard.jsonDB import JsonDB

DEBUG = True

class BattleWizardConsumer(WebsocketConsumer):

    def connect(self):
        self.ai_type = self.scope['url_route']['kwargs']['ai_type']
        self.ai = self.scope['url_route']['kwargs']['ai'] if 'ai' in self.scope['url_route']['kwargs'] else None
        self.game_type = self.scope['url_route']['kwargs']['game_type']
        self.room_name = self.scope['url_route']['kwargs']['room_code']
        self.room_group_name = 'room_%s' % self.room_name
        self.db_name = f"standard-{self.ai_type}-{self.game_type}-{self.room_name}"
        self.moves = []
        self.ai_running = False
        self.last_move_time = None
        self.decks = [[], []]

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        print("Disconnected")
        JsonDB().remove_from_queue_database(self.game_type, int(self.room_name), JsonDB().queue_database())
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        if self.game_type == "constructed":
            self.game = Game(self, self.ai_type, self.db_name, self.game_type, info=JsonDB().game_database(self.db_name), ai=self.ai, player_decks=self.decks)        
        else:
            self.game = Game(self, self.ai_type, self.db_name, self.game_type, info=JsonDB().game_database(self.db_name), ai=self.ai)        
        message = json.loads(text_data)

        if message["move_type"] == 'NEXT_ROOM':
            self.send_game_message(None, message)
            return

        message["log_lines"] = []
        message = self.game.play_move(message)    
        if message:
            self.send_game_message(self.game.as_dict(), message)

            if message["move_type"] == "GET_TIME":
                # run AI if it's the AI's move or if the other player just chose their race
                if self.ai_type == "pvai" and (self.game.current_player() == self.game.players[1] or \
                    (self.game.players[0].race != None and self.game.players[1].race == None)):                     
                    time_for_next_move = False
                    if not self.last_move_time or (datetime.datetime.now() - self.last_move_time).seconds >= 1:
                        time_for_next_move = True
                    if (time_for_next_move or len(self.game.legal_moves_for_ai(self.game.players[1])) == 1) and not self.ai_running:
                        if self.game.players[0].hit_points > 0 and self.game.players[1].hit_points > 0: 
                            print("RUN AI")
                            self.run_ai()
                    else:
                        print("get time while ai running")


    def run_ai(self):
        self.ai_running = True
        self.last_move_time = datetime.datetime.now()
        # todo don't reference AI by index 1
        self.game.set_clickables()
        moves = self.game.legal_moves_for_ai(self.game.players[1])
        if self.ai == "random_bot":
            chosen_move = random.choice(moves)
            #while len(moves) > 1 and chosen_move["move_type"] == "END_TURN":
            #    chosen_move = random.choice(moves) 
        elif self.ai == "aggro_bot":
            chosen_move = random.choice(moves)
            while len(moves) > 1 and chosen_move["move_type"] == "END_TURN":
                chosen_move = random.choice(moves) 
            for move in moves:
                if move["move_type"] == "PLAY_CARD":
                    being_cast, _ = self.game.get_in_play_for_id(move["card"])
                    target, _ = self.game.get_in_play_for_id(move["effect_targets"][0].id)
                    if target in self.game.opponent().in_play: 
                        if being_cast.name in ["Kill", "Zap", "Stiff Wind", "Siz Pop", "Unwind"]:
                            chosen_move = move
                if move["move_type"] == "PLAY_CARD":
                    being_cast, _ = self.game.get_in_play_for_id(move["card"])
                    target, _ = self.game.get_in_play_for_id(move["effect_targets"][0]["id"])
                    if target in self.game.current_player().in_play: 
                        if being_cast.name in ["Faerie War Chant", "Faerie's Blessing"]:
                            chosen_move = move

                if move["move_type"] == "RESOLVE_ENTITY_EFFECT":
                    coming_into_play, _ = self.game.get_in_play_for_id(move["card"])
                    print(f"{coming_into_play.name} is resolving on {move['effect_targets'][0]['id']}")
                    target, _ = self.game.get_in_play_for_id(move["effect_targets"][0]["id"])
                    if target and target.id in [card.id for card in self.game.current_player().in_play]: 
                        if coming_into_play.name in ["Training Master"]:
                            chosen_move = move
                    elif target and target.id in [card.id for card in self.game.opponent().in_play]:
                        if coming_into_play.name in ["Lightning Elemental", "Tempest Elemental", "Tame Tempest"]:
                            chosen_move = move
                    else:
                        print("this move is targetting a player, maybe this code isnt so great") 
                        print(move) 
                        # target is none for people targets print(f"{target.name} {target.id}") 
                        print(f"ids for curr: {[card.id for card in self.game.current_player().in_play]}")
                        print(f"ids for opp: {[card.id for card in self.game.opponent().in_play]}")
                    chosen_move = move
                if move["move_type"] == "SELECT_ENTITY":
                    chosen_move = move
            for move in moves:
                if move["move_type"] == "SELECT_OPPONENT":
                    chosen_move = move
            for move in moves:
                if move["move_type"] == "RESOLVE_ENTITY_EFFECT" and move["effect_targets"][0]["id"] == self.game.opponent().username :
                    chosen_move = move
        else:
            print(f"Unknown AI bot: {self.ai}")
        chosen_move["log_lines"] = []
        message = self.game.play_move(chosen_move)    
        self.send_game_message(self.game.as_dict(), message)
        self.ai_running = False
            

    def send_game_message(self, game_dict, message):
        # send current-game-related message to players
        if DEBUG and message and message["move_type"] != "GET_TIME":
            self.print_move(message)
        message["game"] = game_dict
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
        self.moves.append(move_copy)
        print(f"WIRE MOVE: {json.dumps(move_copy, indent=4)}")

    def game_message(self, event):
        '''
            Gets called once per recipient of a message.
        '''
        message = event['message']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'payload': message
        }))


# todo fix for AI and self.game?
class BattleWizardCustomConsumer(BattleWizardConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_code']
        self.room_group_name = 'room_%s' % self.room_name
        self.custom_game_id = self.scope['url_route']['kwargs']['custom_game_id']
        self.db_name = f"custom-{self.custom_game_id}-{self.room_name}"
        self.moves = []

        cgd = JsonDB().custom_game_database()
        self.game_type = None
        for game in cgd["games"]:
            if game["id"] == int(self.custom_game_id):
                self.game_type = game["game_type"]            
                self.ai_type = game["ai_type"]   

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        print("Disconnected")

        JsonDB().remove_custom_from_queue_database(int(self.custom_game_id), int(self.room_name), JsonDB().queue_database())

        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )
