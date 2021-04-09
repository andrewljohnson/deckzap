import copy
import math
import random

from cofx.jsonDB import JsonDB


class CoFXGame:

    def __init__(self, game_type, info=None):
        self.players = []
        self.game_type = game_type
        self.turn = 0
        self.next_card_id = 0
        self.starting_effects = []

        self.all_cards = []
        for c_info in JsonDB().all_cards():
            if c_info["name"] != "Make Global Effect":
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

        attacking_card.attacked = True
        attacking_card.selected = False

        if attacking_card.damage >= attacking_card.toughness:
            self.current_player().in_play.remove(attacking_card)
            self.current_player().played_pile.append(attacking_card)  
            attacking_card.attacked = False
            attacking_card.selected = False
            attacking_card.damage = 0
        if defending_card.damage >= defending_card.toughness:
            self.opponent().in_play.remove(defending_card)
            self.opponent().played_pile.append(defending_card)  
            defending_card.attacked = False
            defending_card.selected = False
            defending_card.damage = 0


    def play_move(self, event, message, db_name):
        current_player = None
        if event == "PLAY_MOVE":
            move_type = message["move_type"]
            print(f"Move Type: {move_type}")

            if move_type == 'CHOOSE_STARTING_EFFECT':
                self.starting_effects.append(message["id"])
                player = self.players[0]
                if player.username != message["username"]:
                    player = self.players[1]

                player_db = JsonDB().update_deck_in_player_database(player.username, message["card_counts"], JsonDB().player_database())

                if len(self.starting_effects) == 2:
                    for p in self.players:
                        for card_name in player_db[p.username]["card_counts"].keys():
                            p.add_to_deck(card_name, int(player_db[p.username]["card_counts"][card_name]))
                        random.shuffle(p.deck)
                        p.draw(6)
            elif move_type == 'ENTER_FX_SELECTION':
                message["decks"] = {}
                player_db = JsonDB().player_database()
                for p in self.players:
                    if "card_counts" in player_db[p.username]:
                        message["decks"][p.username] = player_db[p.username]["card_counts"] 
                pass
            elif move_type == 'JOIN':
                if len(self.players) >= 2:
                    print(f"an extra player tried to join players {[p.username for p in self.players]}")
                elif len(self.players) <= 1:
                    if len(self.players) == 0 or len(self.players) == 1 and self.players[0].username != message["username"]:
                        self.players.append(CoFXPlayer(self, {"username":message["username"]}, new=True))
                if len(self.players) == 2 and len(self.players[0].hand) == 0 and self.game_type == "ingame":
                    for p in self.players:
                        for card_name in ["Make Entity", "Make Entity", "Make Spell",  "Make Spell"]: #"Make Global Effect"
                            p.add_to_deck(card_name, 1)
                        random.shuffle(p.deck)
                        p.draw(2)
            else:
                if (message["username"] != self.current_player().username):
                    print(f"can't {event} {move_type} on opponent's turn")
                    return None, None
            if move_type == 'START_TURN':
                if self.turn != 0:
                    self.current_player().draw(1 + self.starting_effects.count("draw_extra_card"))
                self.current_player().mana = math.floor(self.turn/2) + 2
                for card in self.current_player().in_play:
                    card.attacked = False
                    card.selected = False
            elif move_type == 'END_TURN':
                self.turn += 1
            elif move_type == 'SELECT_CARD_IN_HAND':
                notarget_spells = ["Think", "Make Entity", "Make Spell"]
                for card in self.current_player().hand:
                    if card.id == message["card"]:
                        if card.name == "Counterspell":
                            print(f"can't select counterspell on own turn")
                            return None, None
                        elif card.cost <= self.current_player().mana:
                            if card.selected and card.name in ["Kill", "Zap", "Siz Pop"]:
                                card.selected = False
                            elif card.selected:
                                message["move_type"] = "PLAY_CARD"
                                self.play_move('PLAY_MOVE', message, db_name)
                                # play card
                            elif card.card_type == "Entity" or card.name in notarget_spells:
                                message["move_type"] = "PLAY_CARD"
                                self.play_move('PLAY_MOVE', message, db_name)
                            else:
                                card.selected = True
                        else:
                            print(f"can't select, card costs too much - costs {card.cost}, mana available {self.current_player().mana}")
                            return None, None

            elif move_type == 'SELECT_ENTITY':
                casting_spell = False
                did_activate = False
                for card in self.current_player().hand:
                    if card.selected:
                        casting_spell = True
                        message["move_type"] = "PLAY_CARD"
                        my_card = self.current_player().in_play_card(message["card"])
                        effect_targets = {}
                        effect_targets[card.effects[0].id] = {"id": my_card.id, "target_type":"entity"}            
                        # hack for siz pop
                        if len(card.effects) == 2:
                            effect_targets[card.effects[1].id] = {"id": message["username"], "target_type":"player"}
                        message["effect_targets"] = effect_targets
                        message["card"] = card.id
                        card.selected = False
                        self.play_move('PLAY_MOVE', message, db_name)                    
                        did_activate = True

                if not casting_spell:
                    if not self.current_player().can_select(message["card"]):
                        # don't send the message to the clients to highlight the card
                        return None, None
                    in_play_card = self.current_player().in_play_card(message["card"])

                    if in_play_card.selected:
                        message["move_type"] = "ATTACK"
                        self.play_move('PLAY_MOVE', message, db_name)                    
                        did_activate = True
                    else:
                        for c in self.current_player().in_play:
                            c.selected = False
                        in_play_card.selected = True
                        for c in self.opponent().in_play:
                            c.can_be_targetted = True
                            print(f"Set can_be_targetted for {c.name}")
                        self.opponent().can_be_targetted = True

            elif move_type == 'SELECT_OPPONENT_ENTITY':
                defending_card = self.opponent().in_play_card(message["card"])
                selected_entity = None
                for entity in self.current_player().in_play:
                    if entity.selected:
                        selected_entity = entity
                selected_card = None
                for card in self.current_player().hand:
                    if card.selected:
                        selected_card = card
                if selected_entity:
                    message["move_type"] = "ATTACK"
                    message["card"] = selected_entity.id
                    message["defending_card"] = defending_card.id
                    self.play_move('PLAY_MOVE', message, db_name)                    
                elif selected_card:
                    message["move_type"] = "PLAY_CARD"
                    message["card"] = selected_card.id
                    effect_targets = {}
                    effect_targets[selected_card.effects[0].id] = {"id": defending_card.id, "target_type":"entity"}            
                    # hack for siz pop
                    if len(selected_card.effects) == 2:
                        effect_targets[selected_card.effects[1].id] = {"id": message["username"], "target_type":"player"}
                    message["effect_targets"] = effect_targets
                    self.play_move('PLAY_MOVE', message, db_name)                    
                else:
                    print(f"nothing selected to target {defending_card.name}")
                    return None, None
            elif move_type == 'SELECT_OPPONENT' or move_type == 'SELECT_SELF':
                casting_spell = False
                for card in self.current_player().hand:
                    if card.selected:
                        target_player = self.current_player() if move_type == 'SELECT_SELF' else self.opponent()
                        casting_spell = True
                        message["move_type"] = "PLAY_CARD"
                        effect_targets = {}
                        effect_targets[card.effects[0].id] = {"id": target_player.username, "target_type":"player"}            
                        # hack for siz pop
                        if len(card.effects) == 2:
                            effect_targets[card.effects[1].id] = {"id": message["username"], "target_type":"player"}
                        message["effect_targets"] = effect_targets
                        message["card"] = card.id
                        card.selected = False
                        self.play_move('PLAY_MOVE', message, db_name)                    

                if not casting_spell:
                    for card in self.current_player().in_play:
                        if card.selected:
                            message["card"] = card.id
                            message["move_type"] = "ATTACK"
                            self.play_move('PLAY_MOVE', message, db_name)                    
                            card.selected = False

            elif move_type == 'ATTACK':
                card_id = message["card"]
                attacking_card = self.current_player().in_play_card(card_id)
                if "defending_card" in message:
                    defending_card_id = message["defending_card"]
                    defending_card = self.opponent().in_play_card(defending_card_id)
                    self.resolve_combat(
                        attacking_card, 
                        defending_card
                    )
                    message["card"] = attacking_card.as_dict()
                    message["defending_card"] = defending_card.as_dict()
                else:
                    self.opponent().hit_points -= attacking_card.power
                    attacking_card.attacked = True
                    attacking_card.selected = False
            elif move_type == 'PLAY_CARD':
                played_card, was_countered = self.current_player().play_card(message["card"], message)
                if played_card:
                    message["was_countered"] = was_countered
                    message["counter_username"] = self.opponent().username
                    played_card.can_cast = False
                    message["card"] = played_card.as_dict()
                    message["played_card"] = True
                    if not was_countered and played_card.card_type == "Spell" and played_card.effects[0].name == "make":
                        message["is_make_effect"] = True
            elif move_type == 'MAKE_CARD':
                self.current_player().add_to_deck(message["card_name"], 1, add_to_hand=True)
                self.current_player().make_to_resolve = []
            elif move_type == 'MAKE_EFFECT':
                self.starting_effects.append(message["card"]["starting_effect"])
                self.current_player().make_to_resolve = []

            if len(self.players) == 2:
                for card in self.current_player().in_play:
                    card.can_be_targetted = False
                for card in self.current_player().hand:
                    card.can_cast = False
                
                if move_type != 'SELECT_ENTITY' or did_activate == True:
                    self.opponent().can_be_targetted = False
                    self.current_player().can_be_targetted = False
                    for card in self.opponent().in_play:
                        card.can_be_targetted = False

                if self.turn % 2 == 0 and self.current_player().username == self.players[0].username \
                    or self.turn % 2 == 1 and self.current_player().username == self.players[1].username:
                    for card in self.current_player().hand:
                        if self.current_player().mana >= card.cost:
                            card.can_cast = True
                            if card.name == "Kill":
                                card.can_cast = False if len(self.current_player().in_play) == 0 and len(self.opponent().in_play) == 0 else True
                            if card.name == "Counterspell":
                                card.can_cast = False
                        else:
                            card.can_cast = False

                    selected_card = None
                    for card in self.current_player().hand:
                        if card.selected:
                            selected_card = card
                    if selected_card:
                        if selected_card.name in ["Kill", "Zap", "Siz Pop"]:
                            for card in self.current_player().in_play:
                                card.can_be_targetted = True
                            for card in self.opponent().in_play:
                                card.can_be_targetted = True
                        if selected_card.name in ["Zap", "Siz Pop"]:
                            self.opponent().can_be_targetted = True
                            self.current_player().can_be_targetted = True

        JsonDB().save_game_database(self.as_dict(), db_name)
        return message, self.as_dict()


class CoFXPlayer:

    def __init__(self, game, info, new=False):
        self.username = info["username"]

        JsonDB().add_to_player_database(self.username, JsonDB().player_database())
        self.game = game
        if new:
            self.hit_points = 30
            self.mana = 0
            self.hand = []
            self.in_play = []
            self.deck = []
            self.played_pile = []
            self.make_to_resolve = []
            self.can_be_targetted = False
        else:
            self.hand = [CoFXCard(c_info) for c_info in info["hand"]]
            self.in_play = [CoFXCard(c_info) for c_info in info["in_play"]]
            self.hit_points = info["hit_points"]
            self.mana = info["mana"]
            self.deck = [CoFXCard(c_info) for c_info in info["deck"]]
            self.played_pile = [CoFXCard(c_info) for c_info in info["played_pile"]]
            self.make_to_resolve = [CoFXCard(c_info) for c_info in info["make_to_resolve"]]
            self.can_be_targetted = info["can_be_targetted"]

    def __repr__(self):
        return f"{self.username} - {self.hit_points} hp, {self.mana} mana, {len(self.hand)} cards, {len(self.in_play)} in play, {len(self.deck)} in deck, {len(self.played_pile)} in played_pile, {len(self.make_to_resolve)} in make_to_resolve, self.can_be_targetted {self.can_be_targetted}"

    def as_dict(self):
        return {
            "username": self.username,
            "hit_points": self.hit_points,
            "mana": self.mana,
            "hand": [c.as_dict() for c in self.hand],
            "in_play": [c.as_dict() for c in self.in_play],
            "deck": [c.as_dict() for c in self.deck],
            "played_pile": [c.as_dict() for c in self.played_pile],
            "make_to_resolve": [c.as_dict() for c in self.make_to_resolve],
            "can_be_targetted": self.can_be_targetted,
        }

    def draw(self, number_of_cards):
        for i in range(0,number_of_cards):
            if len(self.deck) == 0:
                for c in self.played_pile:
                    self.deck.append(c)
                self.played_pile = [] 
            if len(self.deck) == 0:
                continue
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
            target_card.damage = 0
            target_card.attacked = False
            target_card.selected = False

    def do_kill_effect_on_entity(self, card, target_entity_id):
        target_card, target_player = self.game.get_in_play_for_id(target_entity_id)
        target_player.in_play.remove(target_card) 
        target_player.played_pile.append(target_card)  
        target_card.damage = 0
        target_card.attacked = False
        target_card.selected = False
    
    def do_make_effect(self, card, target_player_username, make_type, amount):
        target_player = self.game.players[0]
        if target_player.username != target_player_username:
            target_player = self.game.players[1]
        return target_player.make(1, make_type)

    def make(self, amount, make_type):
        '''
            Make a spell or entity.
        '''
        if make_type == 'Global':
            effects = []
            card_info = {
                "name": "Expensive Spells",
                "cost": 0,
                "card_type": "Effect",
                "description": "New spells players make cost 1 more",
                "starting_effect": "spells_cost_more"
            }
            effects.append(CoFXCard(card_info))
            card_info = {
                "name": "Expensive Entities",
                "cost": 0,
                "card_type": "Effect",
                "description": "New entities players make cost 1 more",
                "starting_effect": "entities_cost_more"
            }
            effects.append(CoFXCard(card_info))
            card_info = {
                "name": "Draw More",
                "cost": 0,
                "card_type": "Effect",
                "description": "Players draw an extra card on their turn.",
                "starting_effect": "draw_extra_card"
            }
            effects.append(CoFXCard(card_info))
            self.make_to_resolve = effects
            return

        requiredEntityCost = None
        if self.game.turn <= 10 and make_type == "Entity":
            requiredEntityCost = math.floor(self.game.turn / 2) + 1

        card1 = None 
        while not card1 or card1.card_type != make_type or (requiredEntityCost and make_type == "Entity" and card1.cost != requiredEntityCost):
            card1 = random.choice(self.game.all_cards)
        card2 = None
        while not card2 or card2.card_type != make_type or card2 == card1:
            card2 = random.choice(self.game.all_cards)
        card3 = None
        while not card3 or card3.card_type != make_type or card3 in [card1, card2]:
            card3 = random.choice(self.game.all_cards)
        self.make_to_resolve = [card1, card2, card3]

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
                if card.attacked:
                    print("can't select entities that already attacked")
                    return False
        return True

    def play_card(self, card_id, message):
        card = None
        for c in self.hand:
            if c.id == card_id:
                card = c
        if card.cost > self.mana:
            print(f"card costs too much - costs {card.cost}, mana available {self.mana}")
            return None, False

        card.selected = False
        self.hand.remove(card)
        self.mana -= card.cost
        
        if card.card_type == "Entity":
            card.turn_played = self.game.turn

        for o_card in self.game.opponent().hand:
            for effect in o_card.effects:
                if effect.name == "counter" and self.game.opponent().mana >= o_card.cost:
                    self.game.opponent().hand.remove(o_card)
                    self.game.opponent().played_pile.append(o_card)
                    self.game.opponent().mana -= o_card.cost
                    return card, True

        if card.card_type == "Entity":
            self.in_play.append(card)
        else:
            self.played_pile.append(card)            

        if len(card.effects) > 0:
            for e in card.effects:
                if not "effect_targets" in message:
                    effect_targets = {}
                    if card.name == "Think":           
                            effect_targets[card.effects[0].id] = {"id": message["username"], "target_type":"player"};
                    elif card.name == "Make Entity" or card.name == "Make Spell" or card.name == "Make Global Effect":    
                            effect_targets[card.effects[0].id] = {"id": message["username"], "target_type":"player"};
                    message["effect_targets"] = effect_targets
                self.do_card_effect(card, e, message["effect_targets"])

        return card, False

    def do_card_effect(self, card, e, effect_targets):
        if e.name == "draw":
            self.do_draw_effect_on_player(card, effect_targets[e.id]["id"], e.amount)
        if e.name == "damage":
            if effect_targets[e.id]["target_type"] == "player":
                self.do_damage_effect_on_player(card, effect_targets[e.id]["id"], e.amount)
            else:
                self.do_damage_effect_on_entity(card, effect_targets[e.id]["id"], e.amount)
        if e.name == "kill":
            self.do_kill_effect_on_entity(card, effect_targets[e.id]["id"])
        if e.name == "make":
            self.do_make_effect(card, effect_targets[e.id]["id"], e.make_type, e.amount)

    def add_to_deck(self, card_name, count, add_to_hand=False):
        card = None
        for c in self.game.all_cards:
            if c.name == card_name:
                card = c
        for x in range(0, count):
            new_card = copy.deepcopy(card)
            new_card.owner_username = self.username
            new_card.id = self.game.next_card_id
            self.game.next_card_id += 1
            new_card = self.modify_new_card(self.game, new_card)
            if add_to_hand:
                self.hand.append(new_card)
            else:
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
        self.starting_effect = info["starting_effect"] if "starting_effect" in info else None
        self.attacked = info["attacked"] if "attacked" in info else False
        self.selected = info["selected"] if "selected" in info else False
        self.can_cast = info["can_cast"] if "can_cast" in info else False
        self.can_be_targetted = info["can_be_targetted"] if "can_be_targetted" in info else False
        self.owner_username = info["owner_username"] if "owner_username" in info else None

    def __repr__(self):
        return f"{self.name} ({self.cost}) - {self.power}/{self.toughness}\n{self.description}\n{self.card_type}\n{self.effects}\n(damage: {self.damage}) (id: {self.id}, turn played: {self.turn_played}, attacked: {self.attacked}, selected: {self.selected}, can_cast: {self.can_cast}, can_be_targetted: {self.can_be_targetted}, owner_username: {owner_username})" 

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
            "starting_effect": self.starting_effect,
            "attacked": self.attacked,
            "selected": self.selected,
            "can_cast": self.can_cast,
            "can_be_targetted": self.can_be_targetted,
            "owner_username": self.owner_username,
        }


class CoFXCardEffect:
    def __init__(self, info):
        self.id = info["id"]
        self.name = info["name"]
        self.amount = info["amount"] if "amount" in info else None
        self.make_type = info["make_type"] if "make_type" in info else None

    def __repr__(self):
        return f"{self.id} {self.name} {self.amount} {self.make_type}"

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "amount": self.amount,
            "make_type": self.make_type,
        }

