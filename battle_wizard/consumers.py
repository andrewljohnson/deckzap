import json
import copy 
import time
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from battle_wizard.game_objects import Game
from battle_wizard.jsonDB import JsonDB

DEBUG = True

class BattleWizardConsumer(WebsocketConsumer):

    def connect(self):
        self.game_type = self.scope['url_route']['kwargs']['game_type']
        self.room_name = self.scope['url_route']['kwargs']['room_code']
        self.room_group_name = 'room_%s' % self.room_name
        self.db_name = f"standard-{self.game_type}-{self.room_name}"
        self.moves = []
        game_dict = JsonDB().game_database(self.db_name)
        self.game = Game(self, self.db_name, self.game_type, info=game_dict)        

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

    def receive(self, text_data, run_ai=True):
        message = json.loads(text_data)

        if message["move_type"] == 'NEXT_ROOM':
            self.send_game_message(None, message)
            return

        message = self.game.play_move(message)    
        self.send_game_message(self.game.as_dict(), message)

        if run_ai and self.game.game_type == "p_vs_ai" and self.game.current_player() == self.game.players[1]:
            self.run_ai()

    def run_ai(self):
        # todo don't reference AI by index 1
        while True:
            moves = self.game.legal_moves(self.game.players[1])
            message = self.game.play_move(moves[0])    
            self.send_game_message(self.game.as_dict(), message)
            if message['move_type'] == "END_TURN" or self.game.players[0].hit_points <= 0 or self.game.players[1].hit_points <= 0:
                break
            #time.sleep(.1)

    def send_game_message(self, game_dict, message):
        # send current-game-related message to players
        move_copy = copy.deepcopy(message)
        if "game" in move_copy:
            del move_copy['game']
        if "log_lines" in move_copy:
            del move_copy['log_lines']
        self.moves.append(move_copy)
        if DEBUG:
            print(f"WIRE MOVE: {json.dumps(move_copy, indent=4)}")
        message["game"] = game_dict
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'game_message',
                'message': message
            }
        )

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
  
        cgd = JsonDB().custom_game_database()
        self.game_type = None
        for game in cgd["games"]:
            if game["id"] == int(self.custom_game_id):
                self.game_type = game["game_type"]            

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
