import json
import copy 
import random
import time

from asgiref.sync import async_to_sync
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

        # run AI if it's the AI's move or if the other player just chose their race
        if self.ai_type == "pvai" and (self.game.current_player() == self.game.players[1] or \
            (self.game.players[0].race != None and self.game.players[1].race == None)): 
            self.run_ai()

    def run_ai(self):
        # todo don't reference AI by index 1
        while True:
            moves = self.game.legal_moves_for_ai(self.game.players[1])
            if self.ai == "random_bot":
                chosen_move = random.choice(moves)
                while len(moves) > 1 and chosen_move["move_type"] == "END_TURN":
                    chosen_move = random.choice(moves) 
            elif self.ai == "aggro_bot":
                chosen_move = random.choice(moves)
                while len(moves) > 1 and chosen_move["move_type"] == "END_TURN":
                    chosen_move = random.choice(moves) 
                for move in moves:
                    if move["move_type"] == "PLAY_CARD":
                        being_cast = self.game.get_in_play_for_id(move["card"])
                        target = self.game.get_in_play_for_id(move["effect_targets"][0].id)
                        if target in self.game.current_player().in_play: 
                            if being_cast.name in ["Faerie War Chant", "Faerie's Blessing", "Kill", "Zap", "Stiff Wind", "Siz Pop"]:
                                chosen_move = move
                        elif target in self.game.opponent().in_play:
                            if being_cast.name in ["Unwind"]:
                                chosen_move = move
                        else:
                            print("should never happen") 

                    if move["move_type"] == "PLAY_CARD":
                        being_cast = self.game.get_in_play_for_id(move["card"])
                        target = self.game.get_in_play_for_id(move["effect_targets"][0]["id"])
                        if target in self.game.current_player().in_play: 
                            if being_cast.name in ["Faerie War Chant", "Faerie's Blessing", "Kill", "Zap", "Stiff Wind", "Siz Pop"] and target.name not in ["Familiar", "Thought Sprite"]:
                                chosen_move = move

                    if move["move_type"] == "RESOLVE_ENTITY_EFFECT":
                        coming_into_play = self.game.get_in_play_for_id(move["card"])
                        target = self.game.get_in_play_for_id(move["effect_targets"][0]["id"])
                        if target in self.game.current_player().in_play: 
                            if coming_into_play.name in ["Training Master"]:
                                chosen_move = move
                        elif target in self.game.opponent().in_play:
                            if coming_into_play.name in ["Lightning Elemental", "Tempest Elemental"]:
                                chosen_move = move
                        else:
                            print("should never happen") 
                        chosen_move = move
                    if move["move_type"] == "SELECT_ENTITY":
                        chosen_move = move
                for move in moves:
                    if move["move_type"] == "SELECT_OPPONENT":
                        chosen_move = move
            else:
                print(f"Unknown AI bot: {self.ai}")
            chosen_move["log_lines"] = []
            message = self.game.play_move(chosen_move)    
            self.send_game_message(self.game.as_dict(), message)
            if message['move_type'] == "END_TURN" or message['move_type'] == "CHOOSE_RACE" or self.game.players[0].hit_points <= 0 or self.game.players[1].hit_points <= 0:
                break
            #time.sleep(.1)

    def send_game_message(self, game_dict, message):
        # send current-game-related message to players
        if DEBUG:
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
