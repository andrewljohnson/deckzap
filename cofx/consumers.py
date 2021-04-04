import json
import math
import random
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
# from channels.generic.websocket import AsyncJsonWebsocketConsumer


class CoFXGame:

    def __init__(self, info=None):
        self.players = []
        self.cards = []
        self.turn = 0
        self.all_cards = [
            CoFXCard(0, "CatKin", 2, 2, 1, 0),
            CoFXCard(0, "CatKin", 2, 2, 1, 0),
            CoFXCard(0, "CatKin", 2, 2, 1, 0),
            CoFXCard(0, "CatKin", 2, 2, 1, 0),
            CoFXCard(0, "CatKin", 2, 2, 1, 0),
            CoFXCard(0, "CatKin", 2, 2, 1, 0),
            CoFXCard(0, "PantherKin", 3, 3, 2, 0),
            CoFXCard(0, "PantherKin", 3, 3, 2, 0),
            CoFXCard(0, "PantherKin", 3, 3, 2, 0),
            CoFXCard(0, "LionKin", 4, 4, 3, 0),
            CoFXCard(0, "LionKin", 4, 4, 3, 0),
            CoFXCard(0, "Beastmaster", 4, 5, 4, 0),
            CoFXCard(0, "Beastmaster", 4, 5, 4, 0),
            CoFXCard(0, "Ogre", 5, 6, 5, 0),
            CoFXCard(0, "Dragon", 6, 7, 6, 0),
            CoFXCard(0, "Kill", 0, 0, 3, 0, card_type="Spell", description="Kill an opponent's entity.", effects=[{"name": "kill", "id": 0}]),
            CoFXCard(0, "Zap", 3, 0, 2, 0, card_type="Spell", description="Deal 3 damage.", effects=[{"name": "damage", "amount": 3, "id": 0}]),
            CoFXCard(0, "Think", 2, 0, 0, 0, card_type="Spell", description="Draw 2 cards.", effects=[{"name": "draw", "amount": 2, "id": 0}]),
            CoFXCard(0, "Siz Pop", 1, 0, 1, 0, card_type="Spell", description="Deal 1 damage. Draw 1 card.", effects=[{"name": "draw", "amount": 1, "id": 0}, {"name": "damage", "amount": 1, "id": 1}]),
        ]

        if info:
            for u in info["players"]:
                self.players.append(CoFXPlayer(self, u))
            for c_info in info["cards"]:
                self.cards.append(CoFXCard(c_info["id"], c_info["name"], c_info["power"], c_info["toughness"], c_info["cost"], c_info["damage"], c_info["turn_played"], c_info["card_type"], c_info["description"], c_info["effects"]))
            self.turn = int(info["turn"])

    def as_dict(self):
        return {
            "players": [p.as_dict() for p in self.players], 
            "cards": [c.as_dict() for c in self.cards], 
            "turn": self.turn, 
        }

    def new_card(self):
        card = self.all_cards[random.randint(0, len(self.all_cards) - 1)]
        card.id = len(self.cards)
        self.cards.append(card)
        return card
    
    def get_in_play_for_id(self, card_id):
        target_card = None
        target_player = None

        for card in self.opponent().in_play:
            if card.id == card_id:
                target_card = card
                target_player = self.opponent()
        
        for card in self.current_player().in_play:
            if card.id == card_id:
                target_card = card
                target_player = self.current_player()

        return target_card, target_player

    def current_player(self):
        return self.players[self.turn % 2]

    def opponent(self):
        return self.players[(self.turn + 1) % 2]

    def resolve_combat(self, attacking_card, defending_card):
        attacking_card.damage += defending_card.power
        defending_card.damage += attacking_card.power
        if attacking_card.damage >= attacking_card.toughness:
            self.in_play.remove(attacking_card)
        if defending_card.damage >= defending_card.toughness:
            self.game.opponen().in_play.remove(defending_card)


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
            self.hand = [CoFXCard(c_info["id"], c_info["name"], c_info["power"], c_info["toughness"], c_info["cost"], c_info["damage"], c_info["turn_played"], c_info["card_type"], c_info["description"], c_info["effects"]) for c_info in info["hand"]]
            self.in_play = [CoFXCard(c_info["id"], c_info["name"], c_info["power"], c_info["toughness"], c_info["cost"], c_info["damage"], c_info["turn_played"], c_info["card_type"], c_info["description"], c_info["effects"]) for c_info in info["in_play"]]
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

    def do_draw_effect_on_player(self, card, target_player_username, amount):
        target_player = self.game.players[0]
        if target_player.username != target_player_username:
            target_player = self.game.players[1]
        target_player.draw(amount)

    def do_damage_effect_on_player(self, card, target_player_username, amount):
        target_player = self.game.players[0]
        if target_player.username != target_player_username:
            target_player = self.game.players[1]
        target_player.hit_points -= amount

    def do_damage_effect_on_entity(self, card, target_entity_id, amount):
        target_card, target_player = self.game.get_in_play_for_id(target_entity_id)
        target_card.damage += amount
        if target_card.damage >= target_card.toughness:
            target_player.in_play.remove(target_card) 

    def do_kill_effect_on_entity(self, card, target_entity_id, amount):
        target_card, target_player = self.game.get_in_play_for_id(target_entity_id)
        target_player.in_play.remove(target_card) 


    def in_play_card(self, card_id):
        for card in self.in_play:
            if card.id == card_id:
                return card

    def can_select(self, card_id):
        for card in current_player.in_play:
            if card.id == card_id:
                if card.turn_played == game.turn:
                    print("can't select entities that were just summoned")
                    return False
        return True

    def play_any_card_type(self, card_id, message):
        card = None
        for c in self.hand:
            if c.id == card_id:
                card = c
        if (card.cost > self.mana):
            print("card costs too much")
            return None
        self.hand.remove(card)
        self.mana -= card.cost
        card.turn_played = self.game.turn

        if card.card_type == "Entity":
            self.in_play.append(card)

        for e in card.effects:
            self.do_card_effect(card, CoFXCardEffect(e), message["effect_targets"])

        return card

    def do_card_effect(self, card, e, effect_targets):
        if e.name == "draw":
            played_card = self.do_draw_effect_on_player(card, effect_targets[str(e.id)], e.amount)
        if e.name == "damage":
            if e.target_type == "player":
                played_card = self.do_damage_effect_on_player(card, effect_targets[str(e.id)], e.amount)
            else:
                played_card = self.do_damage_effect_on_entity(card, effect_targets[str(e.id)], e.amount)
        if e.name == "kill":
            played_card = self.do_kill_effect_on_entity(card, effect_targets[str(e.id)])


class CoFXCard:

    def __init__(self, card_id, name, power, toughness, cost, damage, turn_played=-1, card_type="Entity", description=None, effects=[]):
        self.id = card_id
        self.name = name
        self.power = power
        self.toughness = toughness
        self.cost = cost
        self.damage = damage
        self.turn_played = turn_played
        self.card_type = card_type
        self.description = description
        self.effects = effects

    def __repr__(self):
        return f"{self.name} ({self.cost}) - {self.power}/{self.toughness}\n{self.description}\n{self.card_type}\n{self.effects}\n(damage: {self.damage}) (id: {self.id}, turn played: {self.turn_played})" 

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "power": self.power,
            "toughness": self.toughness,
            "cost": self.cost,
            "damage": self.damage,
            "turn_played": self.turn_played,
            "card_type": self.card_type,
            "description": self.description,
            "effects": self.effects,
        }


class CoFXCardEffect:
    def __init__(self, info):
        self.id = info["id"]
        self.name = info["name"]
        if "amount" in info:
            self.amount = info["amount"]


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

        if event == 'NEXT_ROOM':
            self.send_game_message(None, event, None, message)
            return

        game_dict = None
        try:
            json_data = open(self.room_name)
            game_dict = json.load(json_data) 
        except:
            print("making a new game")
        game = CoFXGame(info=game_dict)            

        if event == "PLAY_MOVE":
            event_type = message["event_type"]
            if event_type == 'JOIN':
                if len(game.players) <= 1:
                    game.players.append(CoFXPlayer(game, {"username":message["username"]}, new=True))
                else:
                    print(f"an extra player tried to join players {[p.username for p in game.players]}")
                if len(game.players) == 2:
                    for p in game.players:
                        p.draw(6)
            else:
                current_player = game.current_player()
                opponent = game.opponent()
                if (message["username"] != current_player.username):
                    print(f"can't {event} on opponent's turn")
                    return
            if event_type == 'START_TURN':
                if game.turn != 0:
                    game.current_player().draw(1)
                game.current_player().mana = math.floor(game.turn/2) + 1
            elif event_type == 'END_TURN':
                game.turn += 1
            elif event_type == 'SELECT_ENTITY':
                if not current_player.can_select(message["card"]):
                    # don't send the message to the clients to highlight the card
                    return
            elif event_type == 'ATTACK':
                if "defending_card" in message:
                    game.resolve_combat(
                        current_player.in_play_card(message["card"]), 
                        opponent.in_play_card(message["defending_card"])
                    )
                else:
                    opponent.hit_points -= current_player.in_play_card(message["card"]).power
            elif event_type == 'PLAY_CARD':
                played_card = current_player.play_any_card_type(message["card"], message)
                if played_card:
                    message["card"] = played_card.as_dict()

        game_dict = game.as_dict()
        with open(self.room_name, 'w') as outfile:
            json.dump(game_dict, outfile)

        self.send_game_message(game_dict, event, event_type, message)

    def send_game_message(self, game_dict, event, event_type, message):
        # send current-game-related message to players
        message["game"] = game_dict
        message['event'] = event
        message['event_type'] = event_type

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