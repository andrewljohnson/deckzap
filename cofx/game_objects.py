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
        self.decks_to_set = None

        self.all_cards = []
        for c_info in JsonDB().all_cards():
            self.all_cards.append(CoFXCard(c_info))

        if info:
            for u in info["players"]:
                self.players.append(CoFXPlayer(self, u))
            self.turn = int(info["turn"])
            self.next_card_id = int(info["next_card_id"])
            self.starting_effects = info["starting_effects"] if "starting_effects" in info else []
            self.decks_to_set = info["decks_to_set"]

    def as_dict(self):
        return {
            "players": [p.as_dict() for p in self.players], 
            "turn": self.turn, 
            "next_card_id": self.next_card_id, 
            "starting_effects": self.starting_effects, 
            "all_cards": [c.as_dict() for c in self.all_cards], 
            "decks_to_set": self.decks_to_set, 
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

    def send_card_to_played_pile(self, card, player):
        player.in_play.remove(card)
        player.played_pile.append(card)  
        card.attacked = False
        card.selected = False
        card.damage = 0
        card.turn_played = -1
        card.tokens = []
        for e in card.effects_leave_play:
            if e.name == "decrease_max_mana":
                player.max_mana -= e.amount

    def resolve_combat(self, attacking_card, defending_card):
        attacking_card.damage += defending_card.power_with_tokens()
        defending_card.damage += attacking_card.power_with_tokens()
        attacking_card.attacked = True
        attacking_card.selected = False
        if attacking_card.damage >= attacking_card.toughness_with_tokens():
            self.send_card_to_played_pile(attacking_card,self.current_player())
        if defending_card.damage >= defending_card.toughness_with_tokens():
            self.send_card_to_played_pile(defending_card,self.opponent())

    def play_move(self, event, message, db_name):

        if event == "PLAY_MOVE":
            move_type = message["move_type"]
            print(f"Move Type: {move_type}")

            if len(self.players) == 2:
                self.unhighlight_everything()

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
                        p.max_mana = 0
                        p.draw(6)
                    self.send_start_first_turn(message, db_name)
            elif move_type == 'JOIN':
                if len(self.players) >= 2:
                    print(f"an extra player tried to join players {[p.username for p in self.players]}")
                elif len(self.players) <= 1:
                    if len(self.players) == 0 or len(self.players) == 1 and self.players[0].username != message["username"]:
                        self.players.append(CoFXPlayer(self, {"username":message["username"]}, new=True))
                if len(self.players) == 2 and len(self.players[0].hand) == 0:
                    if self.game_type == "ingame":
                        for p in self.players:
                            for card_name in ["Make Entity", "Make Entity", "Make Spell",  "Make Spell"]:
                                p.add_to_deck(card_name, 1)
                            random.shuffle(p.deck)
                            p.max_mana = 1
                            p.draw(2)
                    else:
                        self.decks_to_set = {}
                if len(self.players) == 2 and self.players[0].max_mana == 1 and self.turn == 0:
                    # configure for game start after 2 joins if not configured yet
                    if self.game_type == "ingame":
                        self.send_start_first_turn(message, db_name)
                    elif self.game_type == "ingame":
                        if game.starting_effects.length == 2:
                            self.send_start_first_turn(message, db_name)
                        else:
                            player_db = JsonDB().player_database()
                            for p in self.players:
                                if "card_counts" in player_db[p.username]:
                                    self.decks_to_set[p.username] = player_db[p.username]["card_counts"]
                    else:  # no other game types implemented
                        pass 
            else:
                if (message["username"] != self.current_player().username):
                    print(f"can't {event} {move_type} on opponent's turn")
                    return None, None
            if move_type == 'START_TURN':
                self.current_player().start_turn()
            elif move_type == 'END_TURN':
                for c in self.current_player().in_play + self.opponent().in_play:
                    perm_tokens = []
                    for t in c.tokens:
                        if t.is_permanent:
                            perm_tokens.append(t)
                    c.tokens = perm_tokens
                self.turn += 1
                self.current_player().start_turn()
            elif move_type == 'SELECT_CARD_IN_HAND':
                for card in self.current_player().hand:
                    if card.id == message["card"]:
                        if card.is_counter_spell():
                            print(f"can't select counterspell on own turn")
                            return None, None
                        elif card.cost <= self.current_player().mana:
                            if card.selected and card.needs_targets():
                                card.selected = False
                            elif card.selected:
                                message["move_type"] = "PLAY_CARD"
                                self.play_move('PLAY_MOVE', message, db_name)
                                # play card
                            elif card.card_type == "Entity" or not card.needs_targets():
                                message["move_type"] = "PLAY_CARD"
                                self.play_move('PLAY_MOVE', message, db_name)
                            else:
                                selection = True
                                card.select_and_set_targets(self)
                        else:
                            print(f"can't select, card costs too much - costs {card.cost}, mana available {self.current_player().mana}")
                            return None, None
            elif move_type == 'SELECT_ENTITY':
                if self.current_player().entity_with_effect_to_target:
                    message = self.select_entity_target_for_entity_effect(self.current_player().entity_with_effect_to_target, message, db_name)
                elif self.current_player().has_selected_card():  
                    message = self.select_entity_target_for_spell(self.current_player().selected_spell(), message, db_name)
                elif self.current_player().controls_entity(message["card"]):
                    if self.current_player().in_play_entity_is_selected(message["card"]):                
                        has_guard = False
                        for c in self.opponent().in_play:
                            if c.abilities and c.abilities[0].name == "Guard":
                                has_guard = True
                        if has_guard:                        
                            self.current_player().in_play_card(message["card"]).selected = False
                            print(f"can't attack opponent because an entity has Guard")
                        else:                 
                            message["move_type"] = "ATTACK"
                            self.play_move('PLAY_MOVE', message, db_name)   
                    elif self.current_player().can_select(message["card"]):
                        self.current_player().select_in_play(message["card"])
                    else:
                        return None, None
                elif not self.current_player().controls_entity(message["card"]):
                    defending_card = self.opponent().in_play_card(message["card"])
                    selected_entity = self.current_player().selected_entity()
                    if selected_entity:
                        has_guard = False
                        for c in self.opponent().in_play:
                            if c.abilities and c.abilities[0].name == "Guard":
                                has_guard = True
                        if not has_guard or (defending_card.abilities and defending_card.abilities[0].name == "Guard"):                        
                            message["move_type"] = "ATTACK"
                            message["card"] = selected_entity.id
                            message["defending_card"] = defending_card.id
                            self.play_move('PLAY_MOVE', message, db_name)
                        else:
                            print(f"can't attack {defending_card.name} because another entity has Guard")
                            return None, None                                            
                    else:
                        print(f"nothing selected to target {defending_card.name}")
                        return None, None



                else:
                    print("Should never get here")                                
            elif move_type == 'SELECT_OPPONENT' or move_type == 'SELECT_SELF':
                if self.current_player().entity_with_effect_to_target:
                    if move_type == 'SELECT_OPPONENT':
                        message = self.select_player_target_for_entity_effect(self.opponent().username, self.current_player().entity_with_effect_to_target, message, db_name)
                    else:
                        message = self.select_player_target_for_entity_effect(self.current_player().username, self.current_player().entity_with_effect_to_target, message, db_name)
                else:
                    casting_spell = False
                    for card in self.current_player().hand:
                        if card.selected:
                            target_player = self.current_player() if move_type == 'SELECT_SELF' else self.opponent()
                            casting_spell = True
                            message = self.select_player_target_for_spell(target_player.username, card, message, db_name)

                    if not casting_spell:
                        for card in self.current_player().in_play:
                            if card.selected:
                                has_guard = False
                                for c in self.opponent().in_play:
                                    if c.abilities and c.abilities[0].name == "Guard":
                                        has_guard = True
                                if not has_guard:
                                    message["card"] = card.id
                                    message["move_type"] = "ATTACK"
                                    self.play_move('PLAY_MOVE', message, db_name)                    
                                    card.selected = False
                                else:
                                    print(f"can't attack opponent because an entity has Guard")
                                    return None, None
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
            elif move_type == 'RESOLVE_ENTITY_EFFECT':
                self.current_player().resolve_entity_effect(message["card"], message)
                self.current_player().entity_with_effect_to_target = None
            elif move_type == 'MAKE_CARD':
                self.current_player().add_to_deck(message["card_name"], 1, add_to_hand=True)
                self.current_player().make_to_resolve = []
            elif move_type == 'MAKE_EFFECT':
                self.starting_effects.append(message["card"]["starting_effect"])
                self.current_player().make_to_resolve = []

            self.highlight_can_cast()

        JsonDB().save_game_database(self.as_dict(), db_name)
        return message, self.as_dict()

    def send_start_first_turn(self, message, db_name):
        # TODO: send a new message instead of reconfiguring
        #old_move_type = message["move_type"]
        message["move_type"] = "START_TURN"
        #old_username = message["username"]
        message["username"] = self.players[0].username
        self.play_move("PLAY_MOVE", message, db_name)
        #message["move_type"] = old_move_type
        #message["username"] = old_username

    def unhighlight_everything(self):
        for card in self.opponent().in_play:
            card.can_be_targetted = False
        for card in self.current_player().in_play:
            card.can_be_targetted = False
        for card in self.current_player().hand:
            card.can_cast = False
        self.opponent().can_be_targetted = False
        self.current_player().can_be_targetted = False
    
    def set_targets_for_damage_effect(self):
        for card in self.opponent().in_play:
            card.can_be_targetted = True
        for card in self.current_player().in_play:
            card.can_be_targetted = True
        self.opponent().can_be_targetted = True
        self.current_player().can_be_targetted = True        

    def set_targets_for_creature_effect(self):
        for card in self.opponent().in_play:
            card.can_be_targetted = True
        for card in self.current_player().in_play:
            card.can_be_targetted = True

    def highlight_can_cast(self):
        for card in self.current_player().hand:
            if self.current_player().mana >= card.cost:
                card.can_cast = True
                if card.name == "Kill" or card.name == "Unwind" or card.name == "Faerie War Chant":
                    card.can_cast = False if len(self.current_player().in_play) == 0 and len(self.opponent().in_play) == 0 else True
                if card.name == "Counterspell":
                    card.can_cast = False
            else:
                card.can_cast = False

    def select_entity_target(self, card_to_target, message, db_name, move_type):
        # TODO: send a new message instead of reconfiguring
        old_move_type = message["move_type"]
        message["move_type"] = move_type
        selected_card = self.current_player().in_play_card(message["card"])
        if not selected_card:
            selected_card = self.opponent().in_play_card(message["card"])
        effect_targets = {}
        effect_targets[card_to_target.effects[0].id] = {"id": selected_card.id, "target_type":"entity"}            
        # hack for siz pop
        if len(card_to_target.effects) == 2:
            effect_targets[card_to_target.effects[1].id] = {"id": message["username"], "target_type":"player"}
        message["effect_targets"] = effect_targets
        message["card"] = card_to_target.id
        card_to_target.selected = False
        self.play_move('PLAY_MOVE', message, db_name)       
        message["move_type"] = old_move_type
        return message             

    def select_entity_target_for_spell(self, card_to_target, message, db_name):
        return self.select_entity_target(card_to_target, message, db_name, "PLAY_CARD")

    def select_entity_target_for_entity_effect(self, entity_with_effect_to_target, message, db_name):
        return self.select_entity_target(entity_with_effect_to_target, message, db_name, "RESOLVE_ENTITY_EFFECT")

    def select_player_target(self, username, entity_with_effect_to_target, message, db_name, move_type):
        # TODO: send a new message instead of reconfiguring
        old_move_type = message["move_type"]
        message["move_type"] = move_type
        effect_targets = {}
        effect_targets[entity_with_effect_to_target.effects[0].id] = {"id": username, "target_type":"player"}            
        message["effect_targets"] = effect_targets
        message["card"] = entity_with_effect_to_target.id
        self.play_move('PLAY_MOVE', message, db_name)       
        message["move_type"] = old_move_type
        return message             

    def select_player_target_for_spell(self, username, card, message, db_name):
        return self.select_player_target(username, card, message, db_name, "PLAY_CARD")

    def select_player_target_for_entity_effect(self, username, entity_with_effect_to_target, message, db_name):
        return self.select_player_target(username, entity_with_effect_to_target, message, db_name, "RESOLVE_ENTITY_EFFECT")


class CoFXPlayer:

    def __init__(self, game, info, new=False):
        self.username = info["username"]

        JsonDB().add_to_player_database(self.username, JsonDB().player_database())
        self.game = game
        if new:
            self.hit_points = 30
            self.mana = 0
            self.max_mana = 0
            self.hand = []
            self.in_play = []
            self.deck = []
            self.played_pile = []
            self.make_to_resolve = []
            self.can_be_targetted = False
            self.entity_with_effect_to_target = None
        else:
            self.hand = [CoFXCard(c_info) for c_info in info["hand"]]
            self.in_play = [CoFXCard(c_info) for c_info in info["in_play"]]
            self.hit_points = info["hit_points"]
            self.mana = info["mana"]
            self.max_mana = info["max_mana"]
            self.deck = [CoFXCard(c_info) for c_info in info["deck"]]
            self.played_pile = [CoFXCard(c_info) for c_info in info["played_pile"]]
            self.make_to_resolve = [CoFXCard(c_info) for c_info in info["make_to_resolve"]]
            self.can_be_targetted = info["can_be_targetted"]
            self.entity_with_effect_to_target = CoFXCard(info["entity_with_effect_to_target"]) if info["entity_with_effect_to_target"] else None

    def __repr__(self):
        return f"{self.username} - {self.hit_points} hp, {self.mana} mana, {self.max_mana} max_mana, {len(self.hand)} cards, {len(self.in_play)} in play, {len(self.deck)} in deck, {len(self.played_pile)} in played_pile, {len(self.make_to_resolve)} in make_to_resolve, self.can_be_targetted {self.can_be_targetted}, self.entity_with_effect_to_target {self.entity_with_effect_to_target}"

    def as_dict(self):
        return {
            "username": self.username,
            "hit_points": self.hit_points,
            "mana": self.mana,
            "max_mana": self.max_mana,
            "hand": [c.as_dict() for c in self.hand],
            "in_play": [c.as_dict() for c in self.in_play],
            "deck": [c.as_dict() for c in self.deck],
            "played_pile": [c.as_dict() for c in self.played_pile],
            "make_to_resolve": [c.as_dict() for c in self.make_to_resolve],
            "can_be_targetted": self.can_be_targetted,
            "entity_with_effect_to_target": self.entity_with_effect_to_target.as_dict() if self.entity_with_effect_to_target else None,
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

    def do_mana_effect_on_player(self, card, target_player_username, amount):
        target_player = self.game.players[0]
        if target_player.username != target_player_username:
            target_player = self.game.players[1]
        target_player.mana += amount

    def do_increase_max_mana_effect_on_player(self, card, target_player_username, amount):
        target_player = self.game.players[0]
        if target_player.username != target_player_username:
            target_player = self.game.players[1]
        target_player.max_mana += 1

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
            target_card.turn_played = -1

    def do_double_power_effect_on_entity(self, card, target_entity_id):
        target_card, target_player = self.game.get_in_play_for_id(target_entity_id)
        target_card.power *= 2

    def do_kill_effect_on_entity(self, card, target_entity_id):
        target_card, target_player = self.game.get_in_play_for_id(target_entity_id)
        self.game.send_card_to_played_pile(target_card, target_player)

    def do_unwind_effect_on_entity(self, card, target_entity_id):
        target_card, target_player = self.game.get_in_play_for_id(target_entity_id)
        target_player.in_play.remove(target_card) 
        target_player.hand.append(target_card)  
        target_card.damage = 0
        target_card.attacked = False
        target_card.selected = False
        target_card.turn_played = -1
    
    def do_make_effect(self, card, target_player_username, make_type, amount):
        target_player = self.game.players[0]
        if target_player.username != target_player_username:
            target_player = self.game.players[1]
        return target_player.make(1, make_type)

    def do_add_tokens_effect_on_entity(self, token, target_entity_id):
        target_card, target_player = self.game.get_in_play_for_id(target_entity_id)
        target_card.tokens.append(token)

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
        
        if card.cost >= 2:
            for o_card in self.game.opponent().hand:
                for effect in o_card.effects:
                    if effect.name == "counter" and self.game.opponent().mana >= o_card.cost:
                        self.game.opponent().hand.remove(o_card)
                        self.game.opponent().played_pile.append(o_card)
                        self.game.opponent().mana -= o_card.cost
                        return card, True

        card.can_cast = False
        if card.card_type == "Entity":
            self.in_play.append(card)
            card.turn_played = self.game.turn
        else:
            self.played_pile.append(card)            

        if len(card.effects) > 0:
            if card.card_type == "Entity":
                if len(card.effects) > 0:
                    # tell client to select targets
                    if card.name in ["Angry PantherKin"]:
                        self.entity_with_effect_to_target = card
                        self.game.set_targets_for_damage_effect()
                    elif card.name in ["Scary LionKin", "Training Master"]:
                        self.entity_with_effect_to_target = card
                        self.game.set_targets_for_creature_effect()
                    else:
                        for e in card.effects:
                            if not "effect_targets" in message:
                                effect_targets = {}
                                if e.name == "draw" or e.name == "increase_max_mana" or e.name == "make" or e.name == "mana":           
                                    effect_targets[card.effects[0].id] = {"id": message["username"], "target_type":"player"};
                                message["effect_targets"] = effect_targets
                            self.do_card_effect(card, e, message["effect_targets"])
            else:
                if not "effect_targets" in message:
                    message["effect_targets"]  = {}
                for e in card.effects:
                    if card.name == "Think" or "Make" in card.name or card.name == "Forest Ritual":           
                        message["effect_targets"][e.id] = {"id": message["username"], "target_type":"player"};
                    self.do_card_effect(card, e, message["effect_targets"])

        return card, False

    def resolve_entity_effect(self, card_id, message):
        card = None
        for c in self.in_play:
            if c.id == card_id:
                card = c
        for e in card.effects:
            if not "effect_targets" in message:
                effect_targets = {}
                if card.name == "Think":           
                        effect_targets[card.effects[0].id] = {"id": message["username"], "target_type":"player"};
                elif card.name == "Make Entity" or card.name == "Make Spell" or card.name == "Make Global Effect":    
                        effect_targets[card.effects[0].id] = {"id": message["username"], "target_type":"player"};
                message["effect_targets"] = effect_targets
            self.do_card_effect(card, e, message["effect_targets"])

    def do_card_effect(self, card, e, effect_targets):
        if e.name == "increase_max_mana":
            self.do_increase_max_mana_effect_on_player(card, effect_targets[e.id]["id"], e.amount)
        elif e.name == "draw":
            self.do_draw_effect_on_player(card, effect_targets[e.id]["id"], e.amount)
        elif e.name == "damage":
            if effect_targets[e.id]["target_type"] == "player":
                self.do_damage_effect_on_player(card, effect_targets[e.id]["id"], e.amount)
            else:
                self.do_damage_effect_on_entity(card, effect_targets[e.id]["id"], e.amount)
        elif e.name == "double_power":
            self.do_double_power_effect_on_entity(card, effect_targets[e.id]["id"])
        elif e.name == "kill":
            self.do_kill_effect_on_entity(card, effect_targets[e.id]["id"])
        elif e.name == "unwind":
            self.do_unwind_effect_on_entity(card, effect_targets[e.id]["id"])
        elif e.name == "make":
            self.do_make_effect(card, effect_targets[e.id]["id"], e.make_type, e.amount)
        elif e.name == "mana":
            self.do_mana_effect_on_player(card, effect_targets[e.id]["id"], e.amount)
        elif e.name == "add_tokens":
            self.do_add_tokens_effect_on_entity(
                e.tokens[0], 
                effect_targets[e.id]["id"]
            )

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

    def start_turn(self):
        if self.game.turn != 0:
            self.draw(1 + self.game.starting_effects.count("draw_extra_card"))
        self.max_mana += 1
        self.mana = self.max_mana
        for card in self.in_play:
            card.attacked = False
            card.selected = False

    def has_selected_card(self):
        for c in self.hand:
            if c.selected:
                return True
        return False

    def controls_entity(self, card_id):
        for c in self.in_play:
            if c.id == card_id:
                return True
        return False

    def select_in_play(self, card_id):
        for c in self.in_play:
            c.selected = False
            if c.id == card_id:
                in_play_card = c  
        in_play_card.selected = True
        
        has_guard = False
        for c in self.game.opponent().in_play:
            if c.abilities and c.abilities[0].name == "Guard":
                c.can_be_targetted = True
                has_guard = True

        if not has_guard:
            for c in self.game.opponent().in_play:
                c.can_be_targetted = True
            self.game.opponent().can_be_targetted = True

    def has_selected_entity(self):
        for c in self.in_play:
            if c.selected:
                return True
        return False

    def in_play_entity_is_selected(self, card_id):
        for c in self.in_play:
            if c.id == card_id and c.selected:
                return True
        return False

    def selected_entity(self):
        for entity in self.in_play:
            if entity.selected:
                return entity

    def selected_spell(self):
        for card in self.hand:
            if card.selected:
                return card


class CoFXCard:

    def __init__(self, info):
        self.id = info["id"] if "id" in info else -1
        self.name = info["name"]
        self.power = info["power"] if "power" in info else None
        self.toughness = info["toughness"] if "toughness" in info else None
        self.tokens = [CoFXCardToken(t) for t in info["tokens"]] if "tokens" in info else []
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
        self.effects_leave_play = [CoFXCardEffect(e) for e in info["effects_leave_play"]] if "effects_leave_play" in info else []
        self.abilities = [CoFXCardAbility(a) for a in info["abilities"]] if "abilities" in info and info["abilities"] else None
        self.added_effects = [CoFXCardEffect(e) for e in info["added_effects"]] if "added_effects" in info else {}

    def __repr__(self):
        return f"{self.name} ({self.cost}) - {self.power}/{self.toughness}\n{self.description}\n{self.card_type}\n{self.effects}\n(damage: {self.damage}) (id: {self.id}, turn played: {self.turn_played}, attacked: {self.attacked}, selected: {self.selected}, can_cast: {self.can_cast}, can_be_targetted: {self.can_be_targetted}, owner_username: {self.owner_username}, effects_leave_play: {self.effects_leave_play}, abilities: {self.abilities}, tokens: {self.tokens} added_effects: {self.added_effects})" 

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
            "effects_leave_play": [e.as_dict() for e in self.effects_leave_play],
            "abilities": [a.as_dict() for a in self.abilities] if self.abilities else None,
            "tokens": [t.as_dict() for t in self.tokens] if self.tokens else [],
            "added_effects": [e.as_dict() for e in self.added_effects]
        }

    def needs_targets(self):
        for e in self.effects:
            if e.name == "damage" or e.name == "kill" or e.name == "unwind" or e.name == "double_power" or e.name == "add_tokens":
                return True
        return False # draw, make, increase_max_mana

    def select_and_set_targets(self, game):
        self.selected = True
        for e in self.effects:
            if e.name == "damage":
                game.set_targets_for_damage_effect()
            if e.name == "kill" or e.name == "unwind" or e.name == "double_power" or e.name == "add_tokens":
                game.set_targets_for_creature_effect()


    def is_counter_spell(self):
        for e in self.effects:
            if e.name == "counter":
                return True
        return False  

    def power_with_tokens(self):
        power = self.power
        for t in self.tokens:
            power += t.power_modifier
        return power

    def toughness_with_tokens(self):
        toughness = self.toughness
        for t in self.tokens:
            toughness += t.toughness_modifier
        return toughness


class CoFXCardEffect:
    def __init__(self, info):
        self.id = info["id"]
        self.name = info["name"]
        self.amount = info["amount"] if "amount" in info else None
        self.make_type = info["make_type"] if "make_type" in info else None
        self.tokens = [CoFXCardToken(t) for t in info["tokens"]] if "tokens" in info else []

    def __repr__(self):
        return f"{self.id} {self.name} {self.amount} {self.make_type} {self.tokens}"

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "amount": self.amount,
            "make_type": self.make_type,
            "tokens": [t.as_dict() for t in self.tokens] if self.tokens else [],
        }

class CoFXCardAbility:
    def __init__(self, info):
        self.id = info["id"]
        self.name = info["name"]

    def __repr__(self):
        return f"{self.id} {self.name}"

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
        }

class CoFXCardToken:
    def __init__(self, info):
        self.is_permanent = info["is_permanent"]
        self.power_modifier = info["power_modifier"] if "power_modifier" in info else 0
        self.toughness_modifier = info["toughness_modifier"] if "toughness_modifier" in info else 0

    def __repr__(self):
        return f"{self.is_permanent} {self.power_modifier} {self.toughness_modifier}"

    def as_dict(self):
        return {
            "is_permanent": self.is_permanent,
            "power_modifier": self.power_modifier,
            "toughness_modifier": self.toughness_modifier,
        }
