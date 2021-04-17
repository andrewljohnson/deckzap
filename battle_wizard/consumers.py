import json
import copy 
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from battle_wizard.game_objects import Game
from battle_wizard.jsonDB import JsonDB

class BattleWizardConsumer(WebsocketConsumer):

    def connect(self):
        self.game_type = self.scope['url_route']['kwargs']['game_type']
        self.room_name = self.scope['url_route']['kwargs']['room_code']
        self.room_group_name = 'room_%s' % self.room_name
        self.db_name = f"standard-{self.game_type}-{self.room_name}"
        self.moves = []

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
        response = json.loads(text_data)
        message = response.get("message", None)

        if message["move_type"] == 'NEXT_ROOM':
            self.send_game_message(None, None, message)
            return

        game_dict = JsonDB().game_database(self.db_name)
        game = Game(self, self.db_name, self.game_type, info=game_dict)        
        message = game.play_move(message)    
        self.send_game_message(game.as_dict(), message["move_type"], message)

        if game.game_type == "p_vs_ai" and game.current_player() == game.players[1]:
            game.current_player().run_ai()

    def send_game_message(self, game_dict, move_type, message):
        # send current-game-related message to players
        # message['move_type'] = move_type
        move_copy = copy.deepcopy(message)
        move_copy['game'] = None 
        move_copy['log_lines'] = None 
        self.moves.append(move_copy)
        for m in self.moves:
            print(json.dumps(m, indent=4))
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
