import copy
import json
import math
import random

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer


class CoFXGame:

    def __init__(self, info=None):
        self.players = []
        self.turn = 0
        self.next_card_id = 0
        self.starting_effects = []

        self.all_cards = []
        json_data = open('cofx/cofx_cards.json')
        card_json = json.load(json_data)  
        for c_info in card_json:
            self.all_cards.append(CoFXCard(c_info))

        if info:
            for u in info["players"]:
                self.players.append(CoFXPlayer(self, u))
            self.turn = int(info["turn"])
            self.next_card_id = int(info["next_card_id"])
            self.starting_effects = info["starting_effects"] if "starting_effects" in info else []

    def as_dict(self):
        return {
            "players": [p.as_dict() for p in self.players], 
            "turn": self.turn, 
            "next_card_id": self.next_card_id, 
            "starting_effects": self.starting_effects, 
            "all_cards": [c.as_dict() for c in self.all_cards], 
        }

    def current_player(self):
        return self.players[self.turn % 2]

    def opponent(self):
        return self.players[(self.turn + 1) % 2]

    def get_in_play_for_id(self, card_id):
        for p in [self.opponent(), self.current_player()]:
            for card in p.in_play:
                if card.id == card_id:
                    return card, p

    def resolve_combat(self, attacking_card, defending_card):
        attacking_card.damage += defending_card.power
        defending_card.damage += attacking_card.power
        if attacking_card.damage >= attacking_card.toughness:
            self.current_player().in_play.remove(attacking_card)
            self.current_player().played_pile.append(attacking_card)  
        if defending_card.damage >= defending_card.toughness:
            self.opponent().in_play.remove(defending_card)
            self.opponent().played_pile.append(defending_card)  


class CoFXPlayer:

    def __init__(self, game, info, new=False):
        self.username = info["username"]

        try:
            json_data = open("player_database.json")
            player_db = json.load(json_data) 
        except:
            player_db = {}

        if self.username not in player_db:
            player_db[self.username] = {}
        with open("player_database.json", 'w') as outfile:
            json.dump(player_db, outfile)

        self.game = game
        if new:
            self.hit_points = 30
            self.mana = 0
            self.hand = []
            self.in_play = []
            self.deck = []
            self.played_pile = []
        else:
            self.hand = [CoFXCard(c_info) for c_info in info["hand"]]
            self.in_play = [CoFXCard(c_info) for c_info in info["in_play"]]
            self.hit_points = info["hit_points"]
            self.mana = info["mana"]
            self.deck = [CoFXCard(c_info) for c_info in info["deck"]]
            self.played_pile = [CoFXCard(c_info) for c_info in info["played_pile"]]

    def __repr__(self):
        return f"{self.username} - {self.hit_points} hp, {self.mana} mana, {len(self.hand)} cards, {len(self.in_play)} in play, {len(self.deck)} in deck, {len(self.played_pile)} in played_pile"

    def as_dict(self):
        return {
            "username": self.username,
            "hit_points": self.hit_points,
            "mana": self.mana,
            "hand": [c.as_dict() for c in self.hand],
            "in_play": [c.as_dict() for c in self.in_play],
            "deck": [c.as_dict() for c in self.deck],
            "played_pile": [c.as_dict() for c in self.played_pile],
        }

    def draw(self, number_of_cards):
        for i in range(0,number_of_cards):
            if len(self.deck) == 0:
                for c in self.played_pile:
                    self.deck.append(c)
                self.played_pile = [] 
            self.hand.append(self.deck.pop())

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
            target_player.played_pile.append(target_card)  

    def do_kill_effect_on_entity(self, card, target_entity_id):
        target_card, target_player = self.game.get_in_play_for_id(target_entity_id)
        target_player.in_play.remove(target_card) 
        target_player.played_pile.append(target_card)  
    
    def in_play_card(self, card_id):
        for card in self.in_play:
            if card.id == card_id:
                return card

    def can_select(self, card_id):
        for card in self.in_play:
            if card.id == card_id:
                if card.turn_played == self.game.turn:
                    print("can't select entities that were just summoned")
                    return False
        return True

    def play_card(self, card_id, message):
        card = None
        for c in self.hand:
            if c.id == card_id:
                card = c
        if card.cost > self.mana:
            print(f"card costs too much - costs {card.cost}, mana available {self.mana}")
            return None

        self.hand.remove(card)
        self.mana -= card.cost
        card.turn_played = self.game.turn

        for o_card in self.game.opponent().hand:
            for effect in o_card.effects:
                if effect.name == "counter" and self.game.opponent().mana >= o_card.cost:
                    self.game.opponent().hand.remove(o_card)
                    self.game.opponent().mana -= o_card.cost
                    return card

        if card.card_type == "Entity":
            self.in_play.append(card)
        else:
            self.played_pile.append(card)            

        if len(card.effects) > 0:
            for e in card.effects:
                self.do_card_effect(card, e, message["effect_targets"])

        return card

    def do_card_effect(self, card, e, effect_targets):
        if e.name == "draw":
            played_card = self.do_draw_effect_on_player(card, effect_targets[str(e.id)]["id"], e.amount)
        if e.name == "damage":
            if effect_targets[str(e.id)]["target_type"] == "player":
                played_card = self.do_damage_effect_on_player(card, effect_targets[str(e.id)]["id"], e.amount)
            else:
                played_card = self.do_damage_effect_on_entity(card, effect_targets[str(e.id)]["id"], e.amount)
        if e.name == "kill":
            played_card = self.do_kill_effect_on_entity(card, effect_targets[str(e.id)]["id"])

    def add_to_deck(self, card_name, count):
        card = None
        for c in self.game.all_cards:
            if c.name == card_name:
                card = c
        for x in range(0, count):
            new_card = copy.deepcopy(card)
            new_card.id = self.game.next_card_id
            self.game.next_card_id += 1
            new_card = self.modify_new_card(self.game, new_card)
            self.deck.append(new_card)
        print(f"added {count} {card_name}, deck has size {len(self.deck)}")

    def modify_new_card(self, game, card):
        if card.card_type == "Spell":            
            if 'spells_cost_more' in game.starting_effects:
                card.cost += game.starting_effects.count('spells_cost_more')
            if 'spells_cost_less' in game.starting_effects:
                card.cost -= game.starting_effects.count('spells_cost_less')
                card.cost = max(0, card.cost)
        elif card.card_type == "Entity":            
            if 'entities_cost_more' in game.starting_effects:
                card.cost += game.starting_effects.count('entities_cost_more')
            if 'entities_cost_less' in game.starting_effects:
                card.cost -= game.starting_effects.count('entities_cost_less')
                card.cost = max(0, card.cost)
            if 'entities_get_more_toughness' in game.starting_effects:
                card.toughness += game.starting_effects.count('entities_get_more_toughness')*2
            if 'entities_get_less_toughness' in game.starting_effects:
                card.toughness -= game.starting_effects.count('entities_get_less_toughness')*2
                card.toughness = max(0, card.toughness)
            if 'entities_get_more_power' in game.starting_effects:
                card.power += game.starting_effects.count('entities_get_more_power')*2
            if 'entities_get_less_power' in game.starting_effects:
                card.power -= game.starting_effects.count('entities_get_less_power')*2
                card.power = max(0, card.power)
        return card


class CoFXCard:

    def __init__(self, info):
        self.id = info["id"] if "id" in info else -1
        self.name = info["name"]
        self.power = info["power"] if "power" in info else None
        self.toughness = info["toughness"] if "toughness" in info else None
        self.cost = info["cost"]
        self.damage = info["damage"] if "damage" in info else 0
        self.turn_played = info["turn_played"] if "turn_played" in info else -1
        self.card_type = info["card_type"] if "card_type" in info else "Entity"
        self.description = info["description"] if "description" in info else None
        self.effects = [CoFXCardEffect(e) for e in info["effects"]] if "effects" in info else []

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
            "effects": [e.as_dict() for e in self.effects],
        }


class CoFXCardEffect:
    def __init__(self, info):
        self.id = info["id"]
        self.name = info["name"]
        self.amount = info["amount"] if "amount" in info else None

    def __repr__(self):
        return f"{self.id} {self.name} {self.amount}"

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "amount": self.amount,
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
            move_type = message["move_type"]
            print(f"Move Type: {move_type}")

            if move_type == 'CHOOSE_STARTING_EFFECT':
                game.starting_effects.append(message["id"])
                player = game.players[0]
                if player.username != message["username"]:
                    player = game.players[1]

                json_data = open("player_database.json")
                player_db = json.load(json_data) 
                player_db[player.username]["card_counts"] = message["card_counts"]
                with open("player_database.json", 'w') as outfile:
                    json.dump(player_db, outfile)

                if len(game.starting_effects) == 2:
                    for p in game.players:
                        for card_name in player_db[p.username]["card_counts"].keys():
                            p.add_to_deck(card_name, int(player_db[p.username]["card_counts"][card_name]))
                        random.shuffle(p.deck)
                        p.draw(6)

            elif move_type == 'ENTER_FX_SELECTION':
                # just tell the UX to show the FX selection view
                message["decks"] = {}
                json_data = open("player_database.json")
                player_db = json.load(json_data) 
                for p in game.players:
                    if "card_counts" in player_db[p.username]:
                        message["decks"][p.username] = player_db[p.username]["card_counts"] 
                pass
            elif move_type == 'JOIN':
                if len(game.players) <= 1:
                    game.players.append(CoFXPlayer(game, {"username":message["username"]}, new=True))
                else:
                    print(f"an extra player tried to join players {[p.username for p in game.players]}")
            else:
                current_player = game.current_player()
                opponent = game.opponent()
                if (message["username"] != current_player.username):
                    print(f"can't {event} {move_type} on opponent's turn")
                    return
            if move_type == 'START_TURN':
                if game.turn != 0:
                    game.current_player().draw(1 + game.starting_effects.count("draw_extra_card"))
                game.current_player().mana = math.floor(game.turn/2) + 1
            elif move_type == 'END_TURN':
                game.turn += 1
            elif move_type == 'SELECT_ENTITY':
                if not current_player.can_select(message["card"]):
                    # don't send the message to the clients to highlight the card
                    return
            elif move_type == 'ATTACK':
                if "defending_card" in message:
                    game.resolve_combat(
                        current_player.in_play_card(message["card"]), 
                        opponent.in_play_card(message["defending_card"])
                    )
                else:
                    opponent.hit_points -= current_player.in_play_card(message["card"]).power
            elif move_type == 'PLAY_CARD':
                played_card = current_player.play_card(message["card"], message)
                if played_card:
                    message["card"] = played_card.as_dict()

        game_dict = game.as_dict()
        with open(self.room_name, 'w') as outfile:
            json.dump(game_dict, outfile)

        self.send_game_message(game_dict, event, move_type, message)

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