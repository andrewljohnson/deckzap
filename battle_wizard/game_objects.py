import copy
import math
import random
import time

from battle_wizard.jsonDB import JsonDB


class Game:
    def __init__(self, websocket_consumer, db_name, game_type, info=None, player_decks=None):

        # can be ingame, pregame, or choose_race
        # there is also a test_stacked_deck variant for tests
        self.game_type = game_type
        # support 2 players
        self.players = [Player(self, u) for u in info["players"]] if info else []
        # player 0 always acts on even turns, player 1 acts on odd turns
        self.turn = int(info["turn"]) if info else 0
        # the next id to give a card when doing make_card effects
        # each card gets the next unusued integer
        self.next_card_id = int(info["next_card_id"]) if info else 0
        # only used for game_type=pregame
        self.starting_effects = info["starting_effects"] if info and "starting_effects" in info else []
        self.decks_to_set = info["decks_to_set"] if info and "decks_to_set" in info else None

        # the name of the json database on disk
        self.db_name = db_name
        # the websocket consumer instance the game gets updated by
        self.websocket_consumer = websocket_consumer

        self.player_decks = player_decks

    def as_dict(self):
        return {
            "players": [p.as_dict() for p in self.players], 
            "turn": self.turn, 
            "next_card_id": self.next_card_id, 
            "starting_effects": self.starting_effects, 
            "decks_to_set": self.decks_to_set, 
            "db_name": self.db_name, 
        }

    @staticmethod
    def all_cards():
        """
            Returns a list of all possible cards in the game. 
        """
        return [Card(c_info) for c_info in JsonDB().all_cards()]

    def current_player(self):
        return self.players[self.turn % 2]

    def opponent(self):
        return self.players[(self.turn + 1) % 2]

    def legal_moves_for_ai(self, player):
        """
            Returns a list of possible moves for an AI player.
        """
        if len(self.players) < 2:
            return [{"move_type": "JOIN", "username": "random_bot"}]
        if not player.race:
            return [
                {"move_type": "CHOOSE_RACE", "username": "random_bot", "race": "elf"},
                {"move_type": "CHOOSE_RACE", "username": "random_bot", "race": "genie"},
            ]

        moves = []
        if player.entity_with_effect_to_target:
            moves = self.add_resolve_entities_moves(player, moves)
        elif player.make_to_resolve:
            moves = self.add_resolve_make_moves(player, moves)
        else:
            moves = self.add_attack_and_play_card_moves(moves)
        moves.append({"move_type": "END_TURN", "username": "random_bot"})

        return moves

    def add_resolve_entities_moves(self, player, moves):
        for card in self.opponent().in_play + self.current_player().in_play:
            if card.can_be_clicked:
                effect_targets = {} 
                effect_targets[player.entity_with_effect_to_target.effects[0].id] = {"id": card.id, "target_type":"entity"}            
                # hack for siz pop and stiff wind
                if len(player.entity_with_effect_to_target.effects) == 2:
                    effect_targets[player.entity_with_effect_to_target.effects[1].id] = {"id": self.username, "target_type":"player"}
                moves.append({
                        "card":player.entity_with_effect_to_target.id, 
                        "move_type": "RESOLVE_ENTITY_EFFECT", 
                        "username": "random_bot",
                        "effect_targets": effect_targets})
        for p in self.players:
            if p.can_be_clicked:
                effect_targets = {}
                # todo don't hardcode index
                effect_targets[player.entity_with_effect_to_target.effects[0].id] = {"id": self.opponent().username, "target_type":"player"}            
                moves.append({"card":player.entity_with_effect_to_target.id , "move_type": "RESOLVE_ENTITY_EFFECT", "username": "random_bot", "effect_targets": effect_targets})
        return moves 

    def add_resolve_make_moves(self, player, moves):
        if player.make_to_resolve[0].card_type == "Effect":
            # todo don't hardcode index
            moves.append({"card":player.make_to_resolve[0].as_dict() , "move_type": "MAKE_EFFECT", "username": "random_bot"})              
            moves.append({"card":player.make_to_resolve[1].as_dict() , "move_type": "MAKE_EFFECT", "username": "random_bot"})              
            moves.append({"card":player.make_to_resolve[2].as_dict() , "move_type": "MAKE_EFFECT", "username": "random_bot"})              
        else:
            # todo don't hardcode index
            moves.append({"card_name":player.make_to_resolve[0].name , "move_type": "MAKE_CARD", "username": "random_bot"})             
            moves.append({"card_name":player.make_to_resolve[1].name , "move_type": "MAKE_CARD", "username": "random_bot"})             
            moves.append({"card_name":player.make_to_resolve[2].name , "move_type": "MAKE_CARD", "username": "random_bot"})             
        return moves 

    def add_attack_and_play_card_moves(self, moves):
        for entity in self.current_player().in_play:
            if entity.can_be_clicked:
                moves.append({"card":entity.id , "move_type": "SELECT_ENTITY", "username": "random_bot"})
        for entity in self.opponent().in_play:
            if entity.can_be_clicked:
                moves.append({"card":entity.id , "move_type": "SELECT_ENTITY", "username": "random_bot"})
        for card in self.current_player().hand:
            if card.can_be_clicked:
                moves.append({"card":card.id , "move_type": "SELECT_CARD_IN_HAND", "username": "random_bot"})
        if self.current_player().can_be_clicked:
            moves.append({"move_type": "SELECT_SELF", "username": "random_bot"})
        if self.opponent().can_be_clicked:
            moves.append({"move_type": "SELECT_OPPONENT", "username": "random_bot"})
        return moves

    def play_move(self, message):
        move_type = message["move_type"]
        print(f"MOVE: {move_type}")
        
        self.unset_clickables()

        # moves to join/configure/start a game
        if move_type == 'JOIN':
            message = self.join(message)
        elif move_type == 'CHOOSE_STARTING_EFFECT':
            message = self.choose_starting_effect_and_deck(message)
        elif move_type == 'CHOOSE_RACE':
            message = self.choose_race(message)
        else:
            if (message["username"] != self.current_player().username):
                print(f"can't {move_type} on opponent's turn")
                return None
        # move sent after initial game config
        if move_type == 'START_FIRST_TURN':
            self.current_player().start_turn()
        # moves sent by the game UX via buttons and card clicks
        elif move_type == 'END_TURN':
            message = self.end_turn(message)
        elif move_type == 'SELECT_CARD_IN_HAND':
            message = self.select_card_in_hand(message)
        elif move_type == 'SELECT_ENTITY':
            message = self.select_entity(message)
        elif move_type == 'SELECT_OPPONENT' or move_type == 'SELECT_SELF':
            message = self.select_player(move_type, message)
        elif move_type == 'MAKE_CARD':
            self.make_card(message)
        elif move_type == 'MAKE_EFFECT':
            message = self.make_effect(message)        
        # moves that get triggered indirectly from game UX actions (e.g. SELECT_ENTITY twice could be an ATTACK)
        elif move_type == 'ATTACK':
            message = self.attack(message)            
        elif move_type == 'PLAY_CARD':
            message = self.current_player().play_card(message["card"], message)
        elif move_type == 'RESOLVE_ENTITY_EFFECT':
            message = self.current_player().resolve_entity_effect(message["card"], message)
    
        if message:
            JsonDB().save_game_database(self.as_dict(), self.db_name)
        else:
            # if message is None, the move was a no-op, like SELECT_CARD_IN_HAND on an uncastable card
            pass

        self.set_clickables()

        return message

    def unset_clickables(self):
        """
            unhighlight everything before highlighting possible attacks/spells
        """
        if len(self.players) != 2:
            return
        for card in self.opponent().in_play:
            card.can_be_clicked = False
        for card in self.current_player().in_play:
            card.can_be_clicked = False
        for card in self.current_player().hand:
            card.can_be_clicked = False
        self.opponent().can_be_clicked = False
        self.current_player().can_be_clicked = False

    def set_clickables(self):
        if len(self.players) != 2:
            return

        card = self.current_player().entity_with_effect_to_target
        if card:
            if card.effects[0].target_type == "any":
                self.set_targets_for_damage_effect()
            elif card.effects[0].target_type == "entity":
                self.set_targets_for_entity_effect()
            elif card.effects[0].target_type == "opponents_entity":
                self.set_targets_for_opponents_entity_effect()
            return

        selected_entity = None
        for entity in self.current_player().in_play:
            if entity.selected:
                selected_entity = entity
        selected_card = None
        for card in self.current_player().hand:
            if card.selected:
                selected_card = card

        if selected_entity:
            if not self.opponent().has_guard():
                selected_entity.can_be_clicked = True
                self.opponent().can_be_clicked = True
            for card in self.opponent().in_play:
                if self.opponent().entity_has_guard(card) or not self.opponent().has_guard():
                    card.can_be_clicked = True
        elif selected_card:
            if not selected_card.needs_targets():
                selected_card.can_be_clicked = True 
            else:           
                for e in selected_card.effects:
                    if e.target_type == "any":
                        self.set_targets_for_damage_effect()
                    if e.target_type == "entity":
                        self.set_targets_for_entity_effect()
                    if e.target_type == "opponents_entity":
                        self.set_targets_for_opponents_entity_effect()
        elif not selected_card and not selected_entity:
            for card in self.current_player().in_play:
                if self.current_player().can_select_for_attack(card.id):
                    card.can_be_clicked = True
            for card in self.current_player().hand:               
                if self.current_player().mana >= card.cost:
                    card.can_be_clicked = True
                    if card.needs_card_being_cast_target():
                        card.can_be_clicked = False
                    if card.needs_entity_target():
                        card.can_be_clicked = False if len(self.current_player().in_play) == 0 and len(self.opponent().in_play) == 0 else True
                    if card.card_type == "Entity" and not self.current_player().can_summon():
                        card.can_be_clicked = False
                    if card.name == "Mind Manacles" and len(self.opponent().in_play) == 0:
                        card.can_be_clicked = False

    def set_targets_for_damage_effect(self):
        for card in self.opponent().in_play:
            card.can_be_clicked = True
        for card in self.current_player().in_play:
            card.can_be_clicked = True
        self.opponent().can_be_clicked = True
        self.current_player().can_be_clicked = True        


    def set_targets_for_entity_effect(self):
        did_target = False
        for card in self.opponent().in_play:
            card.can_be_clicked = True
            did_target = True
        for card in self.current_player().in_play:
            card.can_be_clicked = True
            did_target = True
        return did_target

    def set_targets_for_opponents_entity_effect(self):
        set_targets = False
        for card in self.opponent().in_play:
            card.can_be_clicked = True
            set_targets = True
        return set_targets

    def has_targets_for_entity_effect(self):
        return len(self.opponent().in_play) > 0 or len(self.current_player().in_play) > 0

    def has_targets_for_opponents_entity_effect(self):
        return len(self.opponent().in_play) > 0

    def join(self, message):
        join_occured = True
        if len(self.players) == 0:
            self.players.append(Player(self, {"username":message["username"]}, new=True))            
            message["log_lines"].append(f"{message['username']} created the game.")
            if self.game_type in ["p_vs_ai", "p_vs_ai_prebuilt"]:
                message["log_lines"].append(f"random_bot joined the game.")
                self.players.append(Player(self, {"username":"random_bot"}, new=True, bot="random_bot"))
        elif len(self.players) == 1:
            message["log_lines"].append(f"{message['username']} joined the game.")
            self.players.append(Player(self, {"username":message["username"]}, new=True))
        elif len(self.players) >= 2:
            print(f"an extra player tried to join players {[p.username for p in self.players]}")
            join_occured = False

        if self.game_type == "pregame":
            if len(self.players) == 2 and self.turn == 0 and len(self.players[0].hand) == 0:
                self.decks_to_set = {}
                player_db = JsonDB().player_database()
                for p in self.players:
                    if "card_counts" in player_db[p.username]:
                        self.decks_to_set[p.username] = player_db[p.username]["card_counts"]
        
        if len(self.players) == 2 and join_occured and self.game_type in ["ingame", "test_stacked_deck"]:
            self.start_game(message, self.game_type)
        return message

    def choose_starting_effect_and_deck(self, message):
        message["log_lines"].append(f"{message['username']} chose {message['id']}.")
        self.starting_effects.append(message["id"])
        player = self.players[0]
        if player.username != message["username"]:
            player = self.players[1]
        player_db = JsonDB().update_deck_in_player_database(player.username, message["card_counts"], JsonDB().player_database())

        if len(self.starting_effects) == 2:
            self.start_game(message, self.game_type)
        return message

    def choose_race(self, message):
        message["log_lines"].append(f"{message['username']} chose {message['race']}.")
        player = self.players[0]
        if player.username != message["username"]:
            player = self.players[1]
        player.race = message["race"]

        if self.players[0].race and len(self.players) == 2 and self.players[1].race:
            self.start_game(message, self.game_type)
        return message

    def start_game(self, message, game_type):
        print(f"START GAME FOR {game_type}")
        if game_type == "ingame":
            self.start_ingame_deckbuilder_game(message)
        elif game_type == "pregame":
            self.start_pregame_deckbuilder_game(message)
        elif game_type == "choose_race" or game_type == "p_vs_ai":
            self.start_choose_race_game(message)
        elif game_type == "choose_race_prebuilt" or game_type == "p_vs_ai_prebuilt":
            self.start_choose_race_prebuilt_game(message)
        elif game_type == "test_stacked_deck":
            self.start_test_stacked_deck_game(message)
        else:
            print(f"unknown game type: {game_type}")

    def start_ingame_deckbuilder_game(self, message):
        for p in self.players:
            for card_name in ["Make Entity", "Make Spell"]:
                p.add_to_deck(card_name, 1)
            random.shuffle(p.deck)
            p.max_mana = 1
            p.draw(2)
        if self.players[0].max_mana == 1: 
           self.send_start_first_turn(message)
        
    def start_pregame_deckbuilder_game(self, message):
        player_db = JsonDB().player_database()
        for p in self.players:
            for card_name in player_db[p.username]["card_counts"].keys():
                p.add_to_deck(card_name, int(player_db[p.username]["card_counts"][card_name]))
            random.shuffle(p.deck)
            p.max_mana = 0
            p.draw(6)
        self.send_start_first_turn(message)

    def start_choose_race_game(self, message):
        use_test = False
        test = ["Stiff Wind", "Stiff Wind", "Stone Elemental", "Stone Elemental"]
        elf_deck = ["Make Spell", "Make Entity"]
        genie_deck = ["Make Spell", "Make Entity"]
        for p in self.players:
            if use_test:
                for card_name in test:
                    p.add_to_deck(card_name, 1)
            elif p.race == "elf":
                for card_name in elf_deck:
                    p.add_to_deck(card_name, 1)
            else:
                for card_name in genie_deck:
                    p.add_to_deck(card_name, 1)
            random.shuffle(p.deck)
            p.max_mana = 1
            p.draw(2)
            print(p.deck)
        self.send_start_first_turn(message)

    def start_choose_race_prebuilt_game(self, message):
        print("start_choose_race_prebuilt_gamestart_choose_race_prebuilt_gamestart_choose_race_prebuilt_game")
        elf_deck = []
        for card in Game.all_cards():
            if card.race == "elf" or not card.race:
                elf_deck.append(card.name)
        genie_deck = []
        for card in Game.all_cards():
            if card.race == "genie" or not card.race:
                genie_deck.append(card.name)

        for p in self.players:
            if p.race == "elf":
                for card_name in elf_deck:
                    p.add_to_deck(card_name, 1)
            else:
                for card_name in genie_deck:
                    p.add_to_deck(card_name, 1)
            random.shuffle(p.deck)
            p.max_mana = 0
            p.draw(6)
        self.send_start_first_turn(message)

    def start_test_stacked_deck_game(self, message):
        if self.players[0].max_mana == 0: 
            for x in range(0, 2):
                for card_name in self.player_decks[x]:
                    self.players[x].add_to_deck(card_name, 1)
                self.players[x].max_mana = 1
                self.players[x].draw(2)

            self.send_start_first_turn(message)

    def send_start_first_turn(self, message):
        new_message = copy.deepcopy(message)
        new_message["move_type"] = "START_FIRST_TURN"
        new_message["username"] = self.players[0].username
        self.play_move(new_message)

    def end_turn(self, message):
        self.remove_temporary_tokens()
        self.remove_temporary_abilities()
        self.turn += 1
        message["log_lines"].append(f"{self.current_player().username}'s turn.")
        self.current_player().start_turn()
        return message

    def select_card_in_hand(self, message):
        for card in self.current_player().hand:
            if card.id == message["card"]:
                message["card_name"] = card.name
                if card.needs_card_being_cast_target():
                    print(f"can't select counterspell on own turn")
                    return None
                elif card.cost <= self.current_player().mana:
                    if card.selected and card.needs_targets():
                        card.selected = False
                    elif card.selected:
                        message["move_type"] = "PLAY_CARD"
                        message = self.play_move(message)
                        # play card
                    elif card.card_type == "Spell" and not card.needs_targets():
                            message["move_type"] = "PLAY_CARD"
                            message = self.play_move(message)
                    elif card.card_type == "Entity":
                        if self.current_player().can_summon():
                            message["move_type"] = "PLAY_CARD"
                            message = self.play_move(message)
                        else:
                            print(f"can't summon because of {self.current_player().added_abilities}")
                    else:
                        card.selected = True
                else:
                    print(f"can't select, card costs too much - costs {card.cost}, mana available {self.current_player().mana}")                        
                    return None
                break
        return message

    def select_entity(self, message):
        if self.current_player().entity_with_effect_to_target:
            message = self.select_entity_target_for_entity_effect(self.current_player().entity_with_effect_to_target, message)
        elif self.current_player().selected_card():  
            # todo handle cards with multiple effects
            if self.current_player().selected_card().effects[0].target_type == "opponents_entity" and self.get_in_play_for_id(message["card"])[0] not in self.opponent().in_play:
                print(f"can't target own entity with opponents_entity effect from {self.current_player().selected_card().name}")
                return None
            message = self.select_entity_target_for_spell(self.current_player().selected_spell(), message)
        elif self.current_player().controls_entity(message["card"]):
            if self.current_player().in_play_entity_is_selected(message["card"]):                
                if self.opponent().has_guard():                        
                    self.current_player().in_play_card(message["card"]).selected = False
                    print(f"can't attack opponent because an entity has Guard")
                else:                 
                    message["move_type"] = "ATTACK"
                    message["card_name"] = self.current_player().in_play_card(message["card"]).name
                    message = self.play_move(message)   
            elif self.current_player().can_select_for_attack(message["card"]):
                self.current_player().select_in_play(message["card"])
            else:
                print("can't select that entity")
                return None
        elif not self.current_player().controls_entity(message["card"]):
            defending_card = self.opponent().in_play_card(message["card"])
            selected_entity = self.current_player().selected_entity()
            if selected_entity:
                if not self.opponent().has_guard() or self.opponent().entity_has_guard(defending_card):                        
                    message["move_type"] = "ATTACK"
                    message["card"] = selected_entity.id
                    message["card_name"] = selected_entity.name
                    message["defending_card"] = defending_card.id
                    message = self.play_move(message)
                else:
                    print(f"can't attack {defending_card.name} because another entity has Guard")
                    return None                                            
            else:
                print(f"nothing selected to target {defending_card.name}")
                return None
        else:
            print("Should never get here")                                
        return message

    def select_player(self, move_type, message):
        if self.current_player().entity_with_effect_to_target:
            if move_type == 'SELECT_OPPONENT':
                message = self.select_player_target_for_entity_effect(self.opponent().username, self.current_player().entity_with_effect_to_target, message)
            else:
                message = self.select_player_target_for_entity_effect(self.current_player().username, self.current_player().entity_with_effect_to_target, message)
        else:
            casting_spell = False
            for card in self.current_player().hand:
                if card.selected:
                    target_player = self.current_player() if move_type == 'SELECT_SELF' else self.opponent()
                    casting_spell = True
                    message = self.select_player_target_for_spell(target_player.username, card, message)

            if not casting_spell:
                for card in self.current_player().in_play:
                    if card.selected:
                        if not self.opponent().has_guard():
                            message["card"] = card.id
                            message["card_name"] = card.name
                            message["move_type"] = "ATTACK"
                            message = self.play_move(message)                    
                            card.selected = False
                        else:
                            print(f"can't attack opponent because an entity has Guard")
                            return None
        return message

    def attack(self, message):
        card_id = message["card"]
        attacking_card = self.current_player().in_play_card(card_id)
        if "defending_card" in message:
            defending_card_id = message["defending_card"]
            defending_card = self.opponent().in_play_card(defending_card_id)
            self.resolve_combat(
                attacking_card, 
                defending_card
            )
            message["defending_card"] = defending_card.as_dict()
            message["log_lines"].append(f"{attacking_card.name} attacks {defending_card.name}")
        else:
            message["log_lines"].append(f"{attacking_card.name} attacks {self.opponent().username} for {attacking_card.power_with_tokens()}.")
            self.opponent().hit_points -= attacking_card.power_with_tokens()
            if attacking_card.abilities:
                if attacking_card.abilities[0].name == "DamageDraw":
                    self.current_player().draw(attacking_card.abilities[0].amount)
        attacking_card.attacked = True
        attacking_card.selected = False
        return message

    def make_card(self, message):
        self.current_player().add_to_deck(message["card_name"], 1, add_to_hand=True)
        self.current_player().make_to_resolve = []

    def make_effect(self, message):
        message["log_lines"].append(f"{message['username']} chose {message['card']['starting_effect']}.")
        self.starting_effects.append(message["card"]["starting_effect"])
        self.current_player().make_to_resolve = []
        return message

    def get_in_play_for_id(self, card_id):
        """
            Returns a tuple of the entity and controlling player for a card_id of a card that is an in_play entity
        """
        for p in [self.opponent(), self.current_player()]:
            for card in p.in_play:
                if card.id == card_id:
                    return card, p

    def send_card_to_played_pile(self, card, player):
        """
            Send the card to the player's played_pile and reset any temporary effects on the card
        """
        if card in player.in_play:
            player.in_play.remove(card)
        player.played_pile.append(card)  
        card.attacked = False
        card.selected = False
        card.damage = 0
        card.turn_played = -1
        card.tokens = []
        # todo: make this generic if we add other added effects
        for e in card.effects_leave_play:
            if e.name == "decrease_max_mana":
                player.max_mana -= e.amount
        for e in card.added_effects["effects_leave_play"]:
            if e.name == "decrease_max_mana":
                player.max_mana -= e.amount
        player.mana = min(player.max_mana, player.mana)
        card.reset_added_effects()
        card.added_abilities = []
        card.added_descriptions = []

    def resolve_combat(self, attacking_card, defending_card):
        attacking_card.damage += defending_card.power_with_tokens()
        defending_card.damage += attacking_card.power_with_tokens()
        attacking_card.attacked = True
        attacking_card.selected = False
        if attacking_card.damage >= attacking_card.toughness_with_tokens():
            self.send_card_to_played_pile(attacking_card,self.current_player())
        if defending_card.damage >= defending_card.toughness_with_tokens():
            self.send_card_to_played_pile(defending_card,self.opponent())

    def remove_temporary_tokens(self):
        for c in self.current_player().in_play + self.opponent().in_play:
            perm_tokens = []
            for t in c.tokens:
                t.turns -= 1
                if t.turns != 0:
                    perm_tokens.append(t)
            c.tokens = perm_tokens

    def remove_temporary_abilities(self):
        perm_abilities = []
        for a in self.current_player().added_abilities:
            a.turns -= 1
            if a.turns != 0:
                perm_abilities.append(a)
        self.current_player().added_abilities = perm_abilities

    def select_entity_target(self, card_to_target, message, move_type):
        new_message = copy.deepcopy(message)
        new_message["move_type"] = move_type
        selected_card = self.current_player().in_play_card(message["card"])
        if not selected_card:
            selected_card = self.opponent().in_play_card(message["card"])
        effect_targets = {}
        effect_targets[card_to_target.effects[0].id] = {"id": selected_card.id, "target_type":"entity"}            
        # hack for siz pop and stiff wind
        if len(card_to_target.effects) == 2:
            effect_targets[card_to_target.effects[1].id] = {"id": message["username"], "target_type":"player"}
        new_message["effect_targets"] = effect_targets
        new_message["card"] = card_to_target.id
        new_message["card_name"] = card_to_target.name
        card_to_target.selected = False
        new_message = self.play_move(new_message)       
        return new_message             

    def select_entity_target_for_spell(self, card_to_target, message):
        return self.select_entity_target(card_to_target, message, "PLAY_CARD")

    def select_entity_target_for_entity_effect(self, entity_with_effect_to_target, message):
        return self.select_entity_target(entity_with_effect_to_target, message, "RESOLVE_ENTITY_EFFECT")

    def select_player_target(self, username, entity_with_effect_to_target, message, move_type):
        new_message = copy.deepcopy(message)
        new_message["move_type"] = move_type
        effect_targets = {}
        effect_targets[entity_with_effect_to_target.effects[0].id] = {"id": username, "target_type":"player"}            
        new_message["effect_targets"] = effect_targets
        new_message["card"] = entity_with_effect_to_target.id
        new_message["card_name"] = entity_with_effect_to_target.name
        new_message = self.play_move(new_message)       
        return new_message             

    def select_player_target_for_spell(self, username, card, message):
        return self.select_player_target(username, card, message, "PLAY_CARD")

    def select_player_target_for_entity_effect(self, username, entity_with_effect_to_target, message):
        return self.select_player_target(username, entity_with_effect_to_target, message, "RESOLVE_ENTITY_EFFECT")


class Player:

    def __init__(self, game, info, new=False, bot=None):
        self.username = info["username"]
        self.race = info["race"] if "race" in info else None
        self.bot = bot

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
            self.can_be_clicked = False
            self.entity_with_effect_to_target = None
            self.added_abilities = []
        else:
            self.hand = [Card(c_info) for c_info in info["hand"]]
            self.in_play = [Card(c_info) for c_info in info["in_play"]]
            self.hit_points = info["hit_points"]
            self.mana = info["mana"]
            self.max_mana = info["max_mana"]
            self.deck = [Card(c_info) for c_info in info["deck"]]
            self.played_pile = [Card(c_info) for c_info in info["played_pile"]]
            self.make_to_resolve = [Card(c_info) for c_info in info["make_to_resolve"]]
            self.can_be_clicked = info["can_be_clicked"]
            self.entity_with_effect_to_target = Card(info["entity_with_effect_to_target"]) if info["entity_with_effect_to_target"] else None
            self.added_abilities = [CardAbility(a, idx) for idx, a in enumerate(info["added_abilities"])] if "added_abilities" in info and info["added_abilities"] else []

    def __repr__(self):
        return f"{self.username} ({self.race}) - {self.hit_points} hp, {self.mana} mana, {self.max_mana} max_mana, {len(self.hand)} cards, {len(self.in_play)} in play, {len(self.deck)} in deck, {len(self.played_pile)} in played_pile, {len(self.make_to_resolve)} in make_to_resolve, self.can_be_clicked {self.can_be_clicked}, self.entity_with_effect_to_target {self.entity_with_effect_to_target}, self.added_abilities {self.added_abilities}"

    def as_dict(self):
        return {
            "username": self.username,
            "race": self.race,
            "hit_points": self.hit_points,
            "mana": self.mana,
            "max_mana": self.max_mana,
            "hand": [c.as_dict() for c in self.hand],
            "in_play": [c.as_dict() for c in self.in_play],
            "deck": [c.as_dict() for c in self.deck],
            "played_pile": [c.as_dict() for c in self.played_pile],
            "make_to_resolve": [c.as_dict() for c in self.make_to_resolve],
            "can_be_clicked": self.can_be_clicked,
            "entity_with_effect_to_target": self.entity_with_effect_to_target.as_dict() if self.entity_with_effect_to_target else None,
            "added_abilities": [a.as_dict() for a in self.added_abilities]
        }

    def add_to_deck(self, card_name, count, add_to_hand=False):
        card = None
        for c in Game.all_cards():
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

    def draw(self, number_of_cards):
        for i in range(0,number_of_cards):
            if len(self.deck) == 0:
                for c in self.played_pile:
                    self.deck.append(c)
                self.played_pile = [] 
            if len(self.deck) == 0:
                continue
            self.hand.append(self.deck.pop())

    def do_card_effect(self, card, e, message, effect_targets):
        print(f"Do card effect: {e.name}");
        if e.name == "increase_max_mana":
            self.do_increase_max_mana_effect_on_player(effect_targets[e.id]["id"], e.amount)
            message["log_lines"].append(f"{self.username} increases max mana by {e.amount}.")
        elif e.name == "draw":
            self.do_draw_effect_on_player(card, effect_targets[e.id]["id"], e.amount)
            message["log_lines"].append(f"{self.username} draws {e.amount} from {card.name}.")
        elif e.name == "take_extra_turn":
            self.do_take_extra_turn_effect_on_player(effect_targets[e.id]["id"])
            message["log_lines"].append(f"{self.username} takes an extra turn.")
        elif e.name == "summon_from_deck":
            if e.target_type == "self":
                message["log_lines"].append(f"{self.username} summons something from their deck.")
            else:
                message["log_lines"].append(f"Both players fill their boards.")
            self.do_summon_from_deck_effect_on_player(e, effect_targets)
        elif e.name == "damage":
            if effect_targets[e.id]["target_type"] == "player":
                self.do_damage_effect_on_player(card, effect_targets[e.id]["id"], e.amount)
                message["log_lines"].append(f"{self.username} deals {e.amount} damage to {effect_targets[e.id]['id']}.")
            else:
                message["log_lines"].append(f"{self.username} deals {e.amount} damage to {self.game.get_in_play_for_id(effect_targets[e.id]['id'])[0].name}.")
                self.do_damage_effect_on_entity(card, effect_targets[e.id]["id"], e.amount)
        elif e.name == "double_power":
            self.do_double_power_effect_on_entity(card, effect_targets[e.id]["id"])
            message["log_lines"].append(f"{self.username} doubles the power of {self.game.get_in_play_for_id(effect_targets[e.id]['id'])[0].name}.")
        elif e.name == "kill":
            message["log_lines"].append(f"{self.username} kills {self.game.get_in_play_for_id(effect_targets[e.id]['id'])[0].name}.")
            self.do_kill_effect_on_entity(effect_targets[e.id]["id"])
        elif e.name == "take_control":
            message["log_lines"].append(f"{self.username} takes control of {self.game.get_in_play_for_id(effect_targets[e.id]['id'])[0].name}.")
            self.do_take_control_effect_on_entity(effect_targets[e.id]["id"])
        elif e.name == "unwind":
            if e.target_type == "all_entities":
                message["log_lines"].append(f"{card.name} returns all entities to their owners' hands.")
                entities_to_unwind = []
                for entity in self.in_play:
                    if entity.id != card.id:
                        entities_to_unwind.append(entity.id)
                for entity in self.game.opponent().in_play:
                    if entity.id != card.id:
                        entities_to_unwind.append(entity.id)
                for eid in entities_to_unwind:
                    self.do_unwind_effect_on_entity(eid)
            else:
                target_card, target_player = self.game.get_in_play_for_id(effect_targets[e.id]['id'])
                message["log_lines"].append(f"{self.username} uses {card.name} to return {target_card.name} to {target_player.username}'s hand.")
                self.do_unwind_effect_on_entity(effect_targets[e.id]["id"])
        elif e.name == "entwine":
            self.do_entwine_effect()
        elif e.name == "make":
            self.do_make_effect(card, effect_targets[e.id]["id"], e.make_type, e.amount)
        elif e.name == "mana":
            message["log_lines"].append(f"{effect_targets[e.id]['id']} gets {e.amount} mana.")
            self.do_mana_effect_on_player(card, effect_targets[e.id]["id"], e.amount)
        elif e.name == "add_tokens":
            if e.target_type == 'self_entities':
                message["log_lines"].append(f"{self.username} adds {str(e.tokens[0])} to their own entities.")
            else:
                message["log_lines"].append(f"{self.username} adds {str(e.tokens[0])} to {self.game.get_in_play_for_id(effect_targets[e.id]['id'])[0].name}.")
            self.do_add_tokens_effect(e, effect_targets)
        elif e.name == "add_effects":
            if e.target_type == "self_entities":
                message["log_lines"].append(f"{self.username} adds effects to their entities.")
            else:
                message["log_lines"].append(f"{self.username} adds effects {self.game.get_in_play_for_id(effect_targets[e.id]['id'])[0].name}.")
            self.do_add_effects_effect(e, card)           
        elif e.name == "add_player_abilities":
            if e.target_type == "opponent":
                message["log_lines"].append(f"{self.game.opponent()} gets {card.description}.")
            else:
                message["log_lines"].append(f"{self.username} gains {card.description}.")
            self.do_add_abilities_effect(e, card)           
        return message 

    def do_summon_from_deck_effect_on_player(self, e, effect_targets):
        if e.target_type == "self" and e.amount == 1:
            target_player = self.game.players[0]
            if target_player.username != effect_targets[e.id]["id"]:
                target_player = self.game.players[1]

            entities = []
            for c in target_player.deck:
                if c.card_type == "Entity":
                    entities.append(c)

            if len(entities) > 0:
                entity_to_summon = random.choice(entities)
                target_player.deck.remove(entity_to_summon)
                target_player.in_play.append(entity_to_summon)
                entity_to_summon.turn_played = self.game.turn   
                if target_player.fast_ability():
                    entity_to_summon.added_abilities.append(target_player.fast_ability())          
                # todo: maybe support comes into play effects
                # target_player.target_or_do_entity_effects(entity_to_summon, {}, target_player.username)     
        elif e.target_type == "all_players" and e.amount == -1:
            entities = []
            for c in Game.all_cards():
                if c.card_type == "Entity":
                    entities.append(c)
            for p in self.game.players:
                while len(p.in_play) < 7:
                    entity_to_summon = copy.deepcopy(random.choice(entities))
                    entity_to_summon.id = self.game.next_card_id
                    self.game.next_card_id += 1
                    p.in_play.append(entity_to_summon)
                    entity_to_summon.turn_played = self.game.turn     
                    if p.fast_ability():
                        entity_to_summon.added_abilities.append(p.fast_ability())                            
                    # todo: maybe support comes into play effects
                    # p.target_or_do_entity_effects(entity_to_summon, {}, p.username)     

    def do_draw_effect_on_player(self, card, target_player_username, amount):
        target_player = self.game.players[0]
        if target_player.username != target_player_username:
            target_player = self.game.players[1]
        target_player.draw(amount)

    def do_take_extra_turn_effect_on_player(self, target_player_username):
        target_player = self.game.players[0]
        if target_player.username != target_player_username:
            target_player = self.game.players[1]
        self.game.remove_temporary_tokens()
        self.game.remove_temporary_abilities()
        self.game.turn += 2
        self.start_turn()

    def do_entwine_effect(self):
        for p in self.game.players:
            all_hand_cards = []
            for c in p.hand:
                p.deck.append(c)
                all_hand_cards.append(c)
            for c in all_hand_cards:
                p.hand.remove(c)

            all_played_cards = []
            for c in p.played_pile:
                p.deck.append(c)
                all_played_cards.append(c)
            for c in all_played_cards:
                p.played_pile.remove(c)
            random.shuffle(p.deck)
            p.draw(3)

    def do_mana_effect_on_player(self, card, target_player_username, amount):
        target_player = self.game.players[0]
        if target_player.username != target_player_username:
            target_player = self.game.players[1]
        target_player.mana += amount

    def do_increase_max_mana_effect_on_player(self, target_player_username, amount):
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
            self.game.send_card_to_played_pile(target_card, target_player)

    def do_double_power_effect_on_entity(self, card, target_entity_id):
        target_card, target_player = self.game.get_in_play_for_id(target_entity_id)
        target_card.power += target_card.power_with_tokens()

    def do_kill_effect_on_entity(self, target_entity_id):
        target_card, target_player = self.game.get_in_play_for_id(target_entity_id)
        self.game.send_card_to_played_pile(target_card, target_player)

    def do_take_control_effect_on_entity(self, target_entity_id):
        target_card, target_player = self.game.get_in_play_for_id(target_entity_id)
        target_player.in_play.remove(target_card)
        self.game.current_player().in_play.append(target_card)
        if self.game.current_player().fast_ability():
            target_card.attacked = False
            target_card.added_abilities.append(self.game.current_player().fast_ability())         
    
    def do_unwind_effect_on_entity(self, target_entity_id):
        target_card, target_player = self.game.get_in_play_for_id(target_entity_id)
        self.game.send_card_to_played_pile(target_card, target_player)
        target_player.hand.append(target_card)  
        target_player.played_pile.remove(target_card)
    
    def do_make_effect(self, card, target_player_username, make_type, amount):
        target_player = self.game.players[0]
        if target_player.username != target_player_username:
            target_player = self.game.players[1]
        return target_player.make(1, make_type)

    def do_add_token_effect_on_entity(self, token, target_entity_id):
        target_card, _ = self.game.get_in_play_for_id(target_entity_id)
        target_card.tokens.append(token)

    def do_add_effect_effect_on_entity(self, effect, target_entity_id):
        target_card, target_player = self.game.get_in_play_for_id(target_entity_id)  
        target_card.added_effects[effect.effect_type].append(effect)
        target_card.added_descriptions.append([effect.description])
        if effect.activate_on_add:
            # todo: make this generic if we add other added
            if effect.name == "increase_max_mana":
                self.do_increase_max_mana_effect_on_player(target_player.username, effect.amount)

    def do_add_abilities_effect_on_player(self, effect, player):
        player.added_abilities.append(effect.abilities[0])

    def do_add_tokens_effect(self, e, effect_targets):
        if e.target_type == "entity":
            for token in e.tokens:
                self.do_add_token_effect_on_entity(
                    token, 
                    effect_targets[e.id]["id"]
                )
        else:  # e.target_type == "self_entities"
            for token in e.tokens:
                for entity in self.in_play:
                    self.do_add_token_effect_on_entity(
                        copy.deepcopy(token), 
                        entity.id
                    )

    def do_add_effects_effect(self, e, card):
        if e.target_type == "self_entities":
            for card in self.in_play:
                for effect_effect in e.effects:
                    self.do_add_effect_effect_on_entity(
                        effect_effect, 
                        card.id
                    )

    def do_add_abilities_effect(self, e, card):
        if e.target_type == "new_self_entities":
            for card in self.in_play:
                for a in e.abilities:
                    if a.descriptive_id == "Fast":
                        card.added_abilities.append(a) 
            self.do_add_abilities_effect_on_player(
                e, 
                self
            )
        elif e.target_type == "opponent":
            self.do_add_abilities_effect_on_player(
                e, 
                self.game.opponent()
            )

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
            effects.append(Card(card_info))
            card_info = {
                "name": "Expensive Entities",
                "cost": 0,
                "card_type": "Effect",
                "description": "New entities players make cost 1 more",
                "starting_effect": "entities_cost_more"
            }
            effects.append(Card(card_info))
            card_info = {
                "name": "Draw More",
                "cost": 0,
                "card_type": "Effect",
                "description": "Players draw an extra card on their turn.",
                "starting_effect": "draw_extra_card"
            }
            effects.append(Card(card_info))
            self.make_to_resolve = effects
            return

        requiredEntityCost = None
        if self.game.turn <= 10 and make_type == "Entity":
            requiredEntityCost = math.floor(self.game.turn / 2) + 1

        all_cards = Game.all_cards()
        banned_cards = ["Make Spell", "Make Spell+", "Make Entity", "Make Entity+"]
        card1 = None 
        while not card1 or card1.name in banned_cards or card1.card_type != make_type or (requiredEntityCost and make_type == "Entity" and card1.cost != requiredEntityCost) or (self.race != None and card1.race != None and self.race != card1.race):
            card1 = random.choice(all_cards)
        card2 = None
        while not card2 or card2.name in banned_cards or card2.card_type != make_type or card2 == card1 or (self.race != None and card2.race != None and self.race != card2.race):
            card2 = random.choice(all_cards)
        card3 = None
        while not card3 or card3.name in banned_cards or card3.card_type != make_type or card3 in [card1, card2] or (self.race != None and card3.race != None and self.race != card3.race):
            card3 = random.choice(all_cards)
        self.make_to_resolve = [card1, card2, card3]

    def in_play_card(self, card_id):
        for card in self.in_play:
            if card.id == card_id:
                return card
        return None

    def in_play_entity_is_selected(self, card_id):
        for c in self.in_play:
            if c.id == card_id and c.selected:
                return True
        return False

    def can_select_for_attack(self, card_id):
        for card in self.in_play:
            if card.id == card_id:
                if card.attacked:
                    return False
                if card.power_with_tokens() <= 0:
                    return False
                for t in card.tokens:
                    if t.set_can_act == False:
                        return False                        
                if card.turn_played == self.game.turn:
                    if self.entity_has_fast(card):
                        return True
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

        card.selected = False
        self.hand.remove(card)
        self.mana -= card.cost
        
        # todo: wrap this into a counterspell method
        for o_card in self.game.opponent().hand:
            for effect in o_card.effects:
                if effect.target_type == "card_being_cast" and card.cost >= effect.amount and self.game.opponent().mana >= o_card.cost:
                    self.game.send_card_to_played_pile(card, self.game.current_player())
                    self.game.opponent().hand.remove(o_card)
                    self.game.opponent().played_pile.append(o_card)
                    self.game.opponent().mana -= o_card.cost
                    message["log_lines"].append(f"{card.name} was countered by {self.game.opponent().username}.")
                    message["was_countered"] = True
                    message["counter_username"] = self.game.opponent().username
                    message["card_name"] = card.name
                    return message

        message["log_lines"].append(f"{self.username} plays {card.name}.")
        if card.card_type == "Entity":
            self.in_play.append(card)
            if self.fast_ability():
                card.added_abilities.append(self.fast_ability())          
            card.turn_played = self.game.turn
        else:
            self.played_pile.append(card)            

        if len(card.effects) > 0:
            if card.card_type == "Entity":
                self.target_or_do_entity_effects(card, message, message["username"])
            else:
                if not "effect_targets" in message:
                    message["effect_targets"]  = {}
                for e in card.effects:
                    if e.target_type == "self":           
                        message["effect_targets"][e.id] = {"id": message["username"], "target_type":"player"}
                    elif e.target_type == "all_players":           
                        message["effect_targets"][e.id] = {"target_type":"all_players"};

                    message = self.do_card_effect(card, e, message, message["effect_targets"])

        message["card_name"] = card.name
        message["played_card"] = True
        message["was_countered"] = False
        return message

    def fast_ability(self):
        for a in self.added_abilities:
            if a.descriptive_id == "Fast":
                return a
        return None 

    def target_or_do_entity_effects(self, card, message, username):
        if len(card.effects) > 0:
            # tell client to select targets
            if card.effects[0].target_type == "any":
                self.entity_with_effect_to_target = card
            elif card.effects[0].target_type == "entity":
                if self.game.has_targets_for_entity_effect():
                    self.entity_with_effect_to_target = card
            elif card.effects[0].target_type == "opponents_entity":
                if self.game.has_targets_for_opponents_entity_effect():
                    self.entity_with_effect_to_target = card
            else:
                for e in card.effects:
                    if not "effect_targets" in message:
                        effect_targets = {}
                        if e.target_type == "self":           
                            effect_targets[card.effects[0].id] = {"id": username, "target_type":"player"};
                        message["effect_targets"] = effect_targets
                    message = self.do_card_effect(card, e, message, message["effect_targets"])

    def resolve_entity_effect(self, card_id, message):
        card = None
        for c in self.in_play:
            if c.id == card_id:
                card = c
        for e in card.effects:
            if not "effect_targets" in message:
                effect_targets = {}
                if e.target_type == "self":           
                    effect_targets[card.effects[0].id] = {"id": message["username"], "target_type":"player"};
                message["effect_targets"] = effect_targets
            message = self.do_card_effect(card, e, message, message["effect_targets"])
        
        self.entity_with_effect_to_target = None
        return message

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

    def selected_card(self):
        for c in self.hand:
            if c.selected:
                return c

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

    def selected_entity(self):
        for entity in self.in_play:
            if entity.selected:
                return entity

    def selected_spell(self):
        for card in self.hand:
            if card.selected:
                return card

    def has_guard(self):
        for c in self.in_play:
            if self.entity_has_guard(c):
                return True
        return False

    def entity_has_guard(self, entity):
        if entity.abilities and entity.abilities[0].name == "Guard":
            return True
        return False

    def entity_has_damage_draw(self, entity):
        if entity.abilities and entity.abilities[0].name == "DamageDraw":
            return True
        return False

    def entity_has_fast(self, entity):
        if entity.abilities and entity.abilities[0].descriptive_id == "Fast":
            return True
        if entity.added_abilities and entity.added_abilities[0].descriptive_id == "Fast":
            return True
        return False

    def can_summon(self):
        for a in self.added_abilities:
            if a.descriptive_id == "Can't Summon":
                return False
        if len(self.in_play) == 7:
            return False
        return True


class Card:

    def __init__(self, info):
        self.id = info["id"] if "id" in info else -1
        self.name = info["name"]
        self.race = info["race"] if "race" in info else None
        self.power = info["power"] if "power" in info else None
        self.toughness = info["toughness"] if "toughness" in info else None
        self.tokens = [CardToken(t) for t in info["tokens"]] if "tokens" in info else []
        self.cost = info["cost"]
        self.damage = info["damage"] if "damage" in info else 0
        self.turn_played = info["turn_played"] if "turn_played" in info else -1
        self.card_type = info["card_type"] if "card_type" in info else "Entity"
        self.description = info["description"] if "description" in info else None
        self.added_descriptions = info["added_descriptions"] if "added_descriptions" in info else []
        self.effects = [CardEffect(e, idx) for idx, e in enumerate(info["effects"])] if "effects" in info else []
        self.starting_effect = info["starting_effect"] if "starting_effect" in info else None
        self.attacked = info["attacked"] if "attacked" in info else False
        self.selected = info["selected"] if "selected" in info else False
        self.owner_username = info["owner_username"] if "owner_username" in info else None
        self.effects_leave_play = [CardEffect(e, idx) for idx, e in enumerate(info["effects_leave_play"])] if "effects_leave_play" in info else []
        self.abilities = [CardAbility(a, idx) for idx, a in enumerate(info["abilities"])] if "abilities" in info and info["abilities"] else []
        self.added_abilities = [CardAbility(a, idx) for idx, a in enumerate(info["added_abilities"])] if "added_abilities" in info and info["added_abilities"] else []
        self.added_effects = {"effects":[], "effects_leave_play":[]}
        self.can_act = info["can_act"] if "can_act" in info else False
        self.can_be_clicked = info["can_be_clicked"] if "can_be_clicked" in info else False

        if "added_effects" in info:
            for idx, e in enumerate(info["added_effects"]["effects"]):
                self.added_effects["effects"].append(CardEffect(e, idx))
            for idx, e in enumerate(info["added_effects"]["effects_leave_play"]):
                self.added_effects["effects_leave_play"].append(CardEffect(e, idx))

    def __repr__(self):
        return f"{self.name} ({self.race}, {self.cost}) - {self.power}/{self.toughness}\n \
                 description: {self.description}\n \
                 added_descriptions: {self.added_descriptions}\n \
                 card_type: {self.card_type}\n \
                 effects: {self.effects}\n \
                 damage: {self.damage}\n \
                 can_be_clicked: {self.can_be_clicked}\n \
                 id: {self.id}, turn played: {self.turn_played}\n \
                 attacked: {self.attacked}, selected: {self.selected}\n \
                 owner_username: {self.owner_username}, effects_leave_play: {self.effects_leave_play}\n \
                 abilities: {self.abilities}, tokens: {self.tokens}\n \
                 added_effects: {self.added_effects} can_act: {self.can_act})" 

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "race": self.race,
            "power": self.power,
            "toughness": self.toughness,
            "cost": self.cost,
            "damage": self.damage,
            "turn_played": self.turn_played,
            "card_type": self.card_type,
            "description": self.description,
            "added_descriptions": self.added_descriptions,
            "effects": [e.as_dict() for e in self.effects],
            "starting_effect": self.starting_effect,
            "attacked": self.attacked,
            "selected": self.selected,
            "can_be_clicked": self.can_be_clicked,
            "can_act": self.can_act,
            "owner_username": self.owner_username,
            "effects_leave_play": [e.as_dict() for e in self.effects_leave_play],
            "abilities": [a.as_dict() for a in self.abilities],
            "added_abilities": [a.as_dict() for a in self.added_abilities],
            "tokens": [t.as_dict() for t in self.tokens] if self.tokens else [],
            "added_effects": {
                "effects": [e.as_dict() for e in self.added_effects["effects"]],
                "effects_leave_play": [e.as_dict() for e in self.added_effects["effects_leave_play"]]
            }
        }

    def reset_added_effects(self):
        self.added_effects = {"effects":[], "effects_leave_play":[]}

    def needs_targets(self):
        for e in self.effects:
            if e.target_type == "any" or e.target_type == "entity" or e.target_type == "opponents_entity":
                return True
        return False 

    def needs_entity_target(self):
        for e in self.effects:
            if e.target_type == "entity" or e.target_type == "opponents_entity":
                return True
        return False

    def needs_card_being_cast_target(self):
        for e in self.effects:
            if e.target_type == "card_being_cast":
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


class CardEffect:
    def __init__(self, info, effect_id):
        self.id = effect_id
        self.name = info["name"]
        self.description = info["description"] if "description" in info else None
        self.amount = info["amount"] if "amount" in info else None
        self.activate_on_add = info["activate_on_add"] if "activate_on_add" in info else False
        self.make_type = info["make_type"] if "make_type" in info else None
        self.effect_type = info["effect_type"] if "effect_type" in info else None
        self.target_type = info["target_type"] if "target_type" in info else None
        self.tokens = [CardToken(t) for t in info["tokens"]] if "tokens" in info else []
        self.effects = [CardEffect(e, idx) for idx, e in enumerate(info["effects"])] if "effects" in info else []
        self.abilities = [CardAbility(a, idx) for idx, a in enumerate(info["abilities"])] if "abilities" in info else []

    def __repr__(self):
        return f"id: {self.id} name: {self.name} amount: {self.amount}\n \
                 description: {self.description} target_type: {self.target_type}\n \
                 make_type: {self.make_type} tokens: {self.tokens} abilities: {self.abilities}\n \
                 effect_type; {self.effect_type} effects: {self.effects} activate_on_add: {self.activate_on_add}"

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "amount": self.amount,
            "description": self.description,
            "activate_on_add": self.activate_on_add,
            "make_type": self.make_type,
            "effect_type": self.effect_type,
            "target_type": self.target_type,
            "tokens": [t.as_dict() for t in self.tokens] if self.tokens else [],
            "effects": [e.as_dict() for e in self.effects] if self.effects else [],
            "abilities": [a.as_dict() for a in self.abilities] if self.abilities else [],
        }


class CardAbility:
    def __init__(self, info, ability_id):
        self.id = ability_id
        self.descriptive_id = info["descriptive_id"] if "descriptive_id" in info else None
        self.name = info["name"]
        self.amount = info["amount"] if "amount" in info else None
        self.turns = info["turns"] if "turns" in info else -1

    def __repr__(self):
        return f"{self.id} {self.name} {self.amount} {self.descriptive_id} {self.turns}"

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "descriptive_id": self.descriptive_id,
            "amount": self.amount,
            "turns": self.turns,
        }


class CardToken:
    def __init__(self, info):
        self.turns = info["turns"] if "turns" in info else -1
        self.power_modifier = info["power_modifier"] if "power_modifier" in info else 0
        self.toughness_modifier = info["toughness_modifier"] if "toughness_modifier" in info else 0
        self.set_can_act = info["set_can_act"] if "set_can_act" in info else None

    def __repr__(self):
        if self.set_can_act is not None:
            return "Can't Attack"
        return f"+{self.power_modifier}/+{self.toughness_modifier}"

    def as_dict(self):
        return {
            "turns": self.turns,
            "power_modifier": self.power_modifier,
            "toughness_modifier": self.toughness_modifier,
            "set_can_act": self.set_can_act,
        }
