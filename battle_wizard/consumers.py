import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from battle_wizard.game_objects import battle_wizardCard
from battle_wizard.game_objects import battle_wizardCardEffect
from battle_wizard.game_objects import battle_wizardGame
from battle_wizard.game_objects import battle_wizardPlayer
from battle_wizard.jsonDB import JsonDB

class battle_wizardConsumer(WebsocketConsumer):

    def connect(self):
        self.game_type = self.scope['url_route']['kwargs']['game_type']
        self.room_name = self.scope['url_route']['kwargs']['room_code']
        self.room_group_name = 'room_%s' % self.room_name
        self.db_name = f"standard-{self.game_type}-{self.room_name}"

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
        event = response.get("event", None)
        message = response.get("message", None)

        if event == 'NEXT_ROOM':
            self.send_game_message(None, event, None, message)
            return

        game_dict = JsonDB().game_database(self.db_name)
        game = battle_wizardGame(self.game_type, info=game_dict)        
        message, game_dict = game.play_move(event, message, self.db_name)    
        if game_dict:
            self.send_game_message(game_dict, event, message["move_type"], message)

    def send_game_message(self, game_dict, event, move_type, message):
        # send current-game-related message to players
        message["game"] = game_dict
        message['event'] = event
        message['move_type'] = move_type

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


class battle_wizardCustomConsumer(battle_wizardConsumer):
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
