import json
import math
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
# from channels.generic.websocket import AsyncJsonWebsocketConsumer


class CoFXGame:

    def __init__(self, info=None):
        self.players = []
        self.cards = []
        self.turn = 0

        if info:
            for u in info["players"]:
                self.players.append(CoFXPlayer(self, u))
            for c_info in info["cards"]:
                self.cards.append(CoFXCard(c_info["id"], c_info["name"], c_info["power"], c_info["toughness"], c_info["cost"]))
            self.turn = int(info["turn"])

    def as_dict(self):
        return {
            "players": [p.as_dict() for p in self.players], 
            "cards": [c.as_dict() for c in self.cards], 
            "turn": self.turn, 
        }

    def new_card(self):
        card = CoFXCard(len(self.cards), "Big Bug", 3, 2, 1)
        self.cards.append(card)
        return card


class CoFXPlayer:

    def __init__(self, game, info, new=False):
        self.username = info["username"]
        self.game = game
        if new:
            self.hit_points = 30
            self.mana = 0
            self.hand = []
            self.in_play = []
        else:
            self.hand = [CoFXCard(c_info["id"], c_info["name"], c_info["power"], c_info["toughness"], c_info["cost"]) for c_info in info["hand"]]
            self.in_play = [CoFXCard(c_info["id"], c_info["name"], c_info["power"], c_info["toughness"], c_info["cost"]) for c_info in info["in_play"]]
            self.hit_points = info["hit_points"]
            self.mana = info["mana"]

    def __repr__(self):
        return f"{self.username} - {self.hit_points} hp, {self.mana} mana, {len(self.hand)} cards, {len(self.in_play)} in play"

    def draw(self, number_of_cards):
        for i in range(0,number_of_cards):
            self.hand.append(self.game.new_card())

    def as_dict(self):
        return {
            "username": self.username,
            "hit_points": self.hit_points,
            "mana": self.mana,
            "hand": [c.as_dict() for c in self.hand],
            "in_play": [c.as_dict() for c in self.in_play],
        }

    def play_card(self, card):
        self.hand.remove(card)
        self.in_play.append(card)
        self.mana -= card.cost


class CoFXCard:

    def __init__(self, card_id, name, power, toughness, cost):
        self.id = card_id
        self.name = name
        self.power = power
        self.toughness = toughness
        self.cost = cost

    def __repr__(self):
        return f"{self.name} ({self.cost}) - {self.power}/{self.toughness} (id: {self.id})" 

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "power": self.power,
            "toughness": self.toughness,
            "cost": self.cost,
        }


class CoFXConsumer(WebsocketConsumer):

    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_code']
        self.room_group_name = 'room_%s' % self.room_name

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
        response = json.loads(text_data)
        event = response.get("event", None)
        message = response.get("message", None)

        game_dict = None;
        try:
            json_data = open(self.room_name)
            game_dict = json.load(json_data) 
        except:
            print("making a new game")
        game = CoFXGame(info=game_dict)            

        if event == 'JOIN':
            # Send message to room group
            if len(game.players) <= 1:
                game.players.append(CoFXPlayer(game, {"username":message["username"]}, new=True))
                with open(self.room_name, 'w') as outfile:
                    json.dump(game.as_dict(), outfile)
            else:
                print(f"an extra player tried to join players {[p.username for p in game.players]}")

            if len(game.players) == 2:
                message["game"] = game.as_dict()
            
            message['event'] = event
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'game_message',
                    'message': message
                }
            )

        json_data = open(self.room_name)
        game_dict = json.load(json_data)
        game = CoFXGame(game_dict)

        if event == 'START_TURN':
            message_player = None
            for p in game.players:
                if p.username == message["username"]:
                    message_player = p
            print(f"Received START_TURN event from player {message_player.username}")
            if game.turn == 0:
                if len(message_player.hand) == 0:
                    message_player.draw(4)
            else:
                    message_player.draw(1)
            
            message_player.mana = math.floor(game.turn/2) + 1

            game_dict = game.as_dict()
            with open(self.room_name, 'w') as outfile:
                json.dump(game_dict, outfile)

            # send message to players
            message["game"] = game_dict
            message['event'] = event

            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'game_message',
                    'message': message
                }
            )

        if event == 'END_TURN':
            current_player_index = game.turn % 2
            current_player = game.players[current_player_index]
            if (message["username"] != current_player.username):
                print("can't end turn on opponent's turn")
                return

            game.turn += 1
            game_dict = game.as_dict()
            with open(self.room_name, 'w') as outfile:
                json.dump(game_dict, outfile)

            # send message to players
            message["game"] = game_dict
            message['event'] = event

            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'game_message',
                    'message': message
                }
            )

        if event == 'PLAY_CARD':
            current_player_index = game.turn % 2
            current_player = game.players[current_player_index]
            card_id = message["card"]
            index = -1
            player = -1
            played_card = None

            if (message["username"] != current_player.username):
                print("can't play cards on opponent's turn")
                return
            for card in current_player.hand:
                if card.id == card_id:
                    played_card = card

            if (played_card.cost > current_player.mana):
                print("card costs too much")
                return

            current_player.play_card(played_card)
            game_dict = game.as_dict()

            with open(self.room_name, 'w') as outfile:
                json.dump(game_dict, outfile)

            message['event'] = event
            message['game'] = game_dict
            message["card"] = played_card.as_dict()
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'game_message',
                    'message': message
                }
            )

        if event == 'ATTACK_FACE':
            current_player_index = game.turn % 2
            current_player = game.players[current_player_index]
            opponent_index = (game.turn + 1) % 2
            opponent = game.players[opponent_index]
            card_id = message["card"]
            index = -1
            player = -1
            in_play_card = None

            if (message["username"] != current_player.username):
                print("can't attack on opponent's turn")
                return
            for card in current_player.in_play:
                if card.id == card_id:
                    in_play_card = card

            opponent.hit_points -= in_play_card.power

            game_dict = game.as_dict()

            with open(self.room_name, 'w') as outfile:
                json.dump(game_dict, outfile)

            message['event'] = event
            message['game'] = game_dict
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'game_message',
                    'message': message
                }
            )



        if event == 'NEXT_ROOM':
            message['event'] = event
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