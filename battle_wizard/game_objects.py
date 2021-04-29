import copy
import math
import random
import time

from battle_wizard.jsonDB import JsonDB


class Game:
    def __init__(self, websocket_consumer, ai_type, db_name, game_type, info=None, player_decks=None, ai=None):

        # can be ingame or choose_race
        # there is also a test_stacked_deck variant for tests
        self.game_type = game_type

        self.ai = ai
        self.ai_type = info["ai_type"] if info and "ai_type" in info else ai_type

        # support 2 players
        self.players = [Player(self, u) for u in info["players"]] if info else []
        # player 0 always acts on even turns, player 1 acts on odd turns
        self.turn = int(info["turn"]) if info else 0
        # the next id to give a card when doing make_card effects
        # each card gets the next unusued integer
        self.next_card_id = int(info["next_card_id"]) if info else 0
        # created by Make Effect
        self.global_effects = info["global_effects"] if info and "global_effects" in info else []

        # the name of the json database on disk
        self.db_name = db_name
        # the websocket consumer instance the game gets updated by
        self.websocket_consumer = websocket_consumer

        # use for test_stacked_deck game_type (for unit testing)
        self.player_decks = player_decks

    def as_dict(self):
        return {
            "players": [p.as_dict() for p in self.players], 
            "turn": self.turn, 
            "next_card_id": self.next_card_id, 
            "global_effects": self.global_effects, 
            "db_name": self.db_name, 
            "ai_type": self.ai_type, 
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
            return [{"move_type": "JOIN", "username": self.ai}]
        if not player.race and self.game_type in ["choose_race", "choose_race_prebuilt"]:
            return [
                {"move_type": "CHOOSE_RACE", "username": self.ai, "race": "elf"},
                {"move_type": "CHOOSE_RACE", "username": self.ai, "race": "genie"},
            ]

        moves = []
        if player.card_info_to_resolve["effect_type"] in ["entity_activated", "entity_comes_into_play"]:
            moves = self.add_resolve_entity_effects_moves(player, moves)
        elif player.card_choice_info["choice_type"] == "make":
            moves = self.add_resolve_make_moves(player, moves)
        elif player.card_choice_info["choice_type"] == "fetch_relic":
            moves = self.add_resolve_fetch_relic_moves(player, moves)
        elif player.card_choice_info["choice_type"] == "fetch_relic_into_play":
            moves = self.add_resolve_fetch_relic_into_play_moves(player, moves)
        elif player.card_choice_info["choice_type"] == "select_entity_for_ice_prison":
            moves = self.add_select_entity_for_ice_prison_moves(moves)
            if len(moves) == 0:
                moves = self.add_attack_and_play_card_moves(moves)
                moves.append({"move_type": "END_TURN", "username": self.ai})                
        elif player.card_choice_info["choice_type"] == "view_hand":
            moves.append({
                "move_type": "HIDE_REVEALED_CARDS", 
                "username": self.ai})
        else:
            moves = self.add_attack_and_play_card_moves(moves)
            if not player.selected_entity() and not player.selected_relic() and not player.selected_spell():
                moves.append({"move_type": "END_TURN", "username": self.ai})

        return moves

    def add_effect_resolve_move(self, entity_to_target, effect_target, effect_type, moves):
        # todo handle cards with more than one effect that gets triggered at the same time
        effect_id = None
        if effect_type == "entity_comes_into_play": 
            effect_id = entity_to_target.effects[0].id
        elif effect_type == "entity_activated": 
            effect_id = entity_to_target.effects_activated()[0].id
        moves.append({
                "card":entity_to_target.id, 
                "move_type": "RESOLVE_ENTITY_EFFECT", 
                "username": self.ai,
                "effect_targets": {effect_id: effect_target}})
        return moves

    def add_select_entity_for_ice_prison_moves(self, moves):
        for card in self.current_player().in_play:
            if card.can_be_clicked:
                moves.append({"card":card.id , "move_type": "SELECT_ENTITY", "username": self.ai})
        return moves

    def add_resolve_entity_effects_moves(self, player, moves):
        entity_to_target = self.current_player().selected_entity()
        effect_type = self.current_player().card_info_to_resolve["effect_type"]
        for card in self.opponent().in_play + self.current_player().in_play:
            if card.can_be_clicked:
                effect_target = {"id": card.id, "target_type":"entity"}
                moves = self.add_effect_resolve_move(entity_to_target, effect_target, effect_type, moves)
        for p in self.players:
            if p.can_be_clicked:
                # todo don't hardcode index
                effect_target = {"id": p.username, "target_type":"player"}
                moves = self.add_effect_resolve_move(entity_to_target, effect_target, effect_type, moves)
        return moves 

    def add_resolve_make_moves(self, player, moves):
        move_type = "MAKE_CARD"
        if player.card_choice_info["cards"][0].card_type == "Effect":
            move_type = "MAKE_EFFECT"
        for x in range(0,3):
            # todo don't hardcode index
            moves.append({"card":player.card_choice_info["cards"][0].as_dict() , "move_type": move_type, "username": self.ai})              
            moves.append({"card":player.card_choice_info["cards"][1].as_dict() , "move_type": move_type, "username": self.ai})              
            moves.append({"card":player.card_choice_info["cards"][2].as_dict() , "move_type": move_type, "username": self.ai})              
        return moves 

    def add_resolve_fetch_relic_moves(self, player, moves):
        for c in player.card_choice_info["cards"]:
            moves.append({"card":c.as_dict() , "move_type": "FETCH_CARD", "username": self.ai})              
        return moves 

    def add_resolve_fetch_relic_into_play_moves(self, player, moves):
        for c in player.card_choice_info["cards"]:
            moves.append({"card":c.as_dict() , "move_type": "FETCH_CARD_INTO_PLAY", "username": self.ai})              
        return moves 

    def add_attack_and_play_card_moves(self, moves):
        for relic in self.current_player().relics:
            if relic.can_be_clicked:
                moves.append({"card":relic.id , "move_type": "SELECT_RELIC", "username": self.ai})
        for entity in self.current_player().in_play:
            if entity.can_be_clicked:
                moves.append({"card":entity.id , "move_type": "SELECT_ENTITY", "username": self.ai})
            # todo: don't hardcode for Infernus
            if len(entity.effects_activated()) > 0 and \
                entity.effects_activated()[0].target_type == "this" and \
                entity.effects_activated()[0].cost <= self.current_player().mana:
                moves.append({"card":entity.id, "move_type": "ACTIVATE_ENTITY", "username": self.ai})
            elif len(entity.effects_activated()) > 0 and \
                entity.effects_activated()[0].cost <= self.current_player().mana:
                # todo: don't hardcode for Winding One
                moves.append({"card":entity.id, "move_type": "ACTIVATE_ENTITY", "username": self.ai})
        for entity in self.opponent().in_play:
            if entity.can_be_clicked:
                moves.append({"card":entity.id , "move_type": "SELECT_ENTITY", "username": self.ai})
        for card in self.current_player().hand:
            if card.can_be_clicked:
                moves.append({"card":card.id , "move_type": "SELECT_CARD_IN_HAND", "username": self.ai})
        if self.current_player().can_be_clicked:
            moves.append({"move_type": "SELECT_SELF", "username": self.ai})
        if self.opponent().can_be_clicked:
            moves.append({"move_type": "SELECT_OPPONENT", "username": self.ai})
        return moves

    def play_move(self, message):
        move_type = message["move_type"]
        print(f"MOVE: {move_type}")
        
        self.unset_clickables()

        # moves to join/configure/start a game
        if move_type == 'JOIN':
            message = self.join(message)
        elif move_type == 'CHOOSE_RACE':
            message = self.choose_race(message)
        else:
            if (message["username"] != self.current_player().username):
                print(f"can't {move_type} on opponent's turn")
                return None
        # move sent after initial game config
        if move_type == 'START_FIRST_TURN':
            message = self.current_player().start_turn(message)
            found_relic = None
            
            for c in self.current_player().deck:
                if len(c.abilities) > 0 and c.abilities[0].descriptive_id == "Starts in Play":
                    found_relic = c
                    break
            if found_relic:
                self.current_player().relics.append(found_relic)
                self.current_player().deck.remove(found_relic)
            
            found_relic = None
            for c in self.opponent().deck:
                if len(c.abilities) > 0 and c.abilities[0].descriptive_id == "Starts in Play":
                    found_relic = c
                    break
            if found_relic:
                self.opponent().relics.append(found_relic)
                self.opponent().deck.remove(found_relic)


        # moves sent by the game UX via buttons and card clicks
        elif move_type == 'END_TURN':
            message = self.end_turn(message)
        elif move_type == 'SELECT_CARD_IN_HAND':
            message = self.select_card_in_hand(message)
        elif move_type == 'SELECT_RELIC':
            message = self.select_relic(message)
        elif move_type == 'SELECT_ENTITY':
            message = self.select_entity(message)
        elif move_type == 'SELECT_OPPONENT' or move_type == 'SELECT_SELF':
            message = self.select_player(move_type, message)
        elif move_type == 'MAKE_CARD':
            self.make_card(message)
        elif move_type == 'MAKE_EFFECT':
            message = self.make_effect(message)        
        elif move_type == 'FETCH_CARD':
            message = self.fetch_card(message, "Relic")        
        elif move_type == 'FETCH_CARD_INTO_PLAY':
            message = self.fetch_card(message, "Relic", into_play=True)        
        # moves that get triggered indirectly from game UX actions (e.g. SELECT_ENTITY twice could be an ATTACK)
        elif move_type == 'ATTACK':
            message = self.attack(message)            
        elif move_type == 'ACTIVATE_RELIC':
            message = self.activate_relic(message)            
        elif move_type == 'ACTIVATE_ENTITY':
            message = self.activate_entity(message)            
        elif move_type == 'HIDE_REVEALED_CARDS':
            message = self.hide_revealed_cards(message)            
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
        for card in self.current_player().relics:
            card.can_be_clicked = False
        self.opponent().can_be_clicked = False
        self.current_player().can_be_clicked = False


    def set_clickables(self):
        """
            highlight selectable cards for possible attacks/spells
        """
        if len(self.players) != 2:
            return

        cp = self.current_player()
        opp = self.opponent()
        if cp.selected_entity() and cp.card_info_to_resolve["effect_type"] != "entity_at_ready":
            cp.set_targets_for_selected_entity()
        elif cp.selected_relic():
            selected_relic = cp.selected_relic()
            if not selected_relic.needs_activated_effect_targets():
                selected_relic.can_be_clicked = True 
            else:           
                for e in selected_relic.enabled_activated_effects():
                    if cp.mana >= e.cost:
                        self.set_targets_for_target_type(e.target_type, e.target_restrictions)
        elif cp.selected_spell():
            selected_spell = cp.selected_spell()
            if not selected_spell.needs_targets():
                selected_spell.can_be_clicked = True 
            else:           
                for e in selected_spell.effects:
                    if cp.mana >= e.cost:
                        self.set_targets_for_target_type(e.target_type, e.target_restrictions)
                        # todo handle mutliple effects if we add cards like that
                        # without this break, this code breaks on Siz Pop
                        break
        elif cp.card_info_to_resolve["effect_type"] in ["entity_at_ready"]:
            selected_entity = cp.selected_entity()
            only_has_ambush_attack = False
            if not selected_entity.has_ability("Fast"):
                if selected_entity.has_ability("Ambush"):
                    if selected_entity.turn_played == self.turn:
                        only_has_ambush_attack = True
            if (selected_entity.has_ability("Evade Guard") or not opp.has_guard()) and not only_has_ambush_attack:
                selected_entity.can_be_clicked = True
                opp.can_be_clicked = True
            for card in opp.in_play:
                if card.has_ability("Guard") or not opp.has_guard() or selected_entity.has_ability("Evade Guard"):
                    if not card.has_ability("Lurker"):
                        card.can_be_clicked = True
        if cp.card_info_to_resolve["effect_type"]:
            return

        if len(cp.card_choice_info["cards"]) > 0 and cp.card_choice_info["choice_type"] in ["select_entity_for_effect", "select_entity_for_ice_prison"]:
            for c in cp.card_choice_info["cards"]:
                c.can_be_clicked = True
            return

        for card in cp.relics:
            if card.can_activate_abilities:
                card.can_be_clicked = True                
            if card.needs_entity_target_for_activated_effect():
                card.can_be_clicked = False if len(cp.in_play) == 0 and len(opp.in_play) == 0 else True
            if len(card.enabled_activated_effects()) == 0 or card.enabled_activated_effects()[0].cost > cp.mana:
                card.can_be_clicked = False
            if not card.can_activate_abilities:
                card.can_be_clicked = False                
        for card in cp.in_play:
            if cp.can_select_for_attack(card.id):
                card.can_be_clicked = True
        for card in cp.hand:               
            if cp.mana >= card.cost:
                card.can_be_clicked = True
                if card.needs_card_being_cast_target():
                    card.can_be_clicked = False
                if card.card_type == "Relic":
                    card.can_be_clicked = len(cp.relics) != 3
                if card.card_type == "Spell" and card.needs_entity_target():
                    card.can_be_clicked = False if len(cp.in_play) == 0 and len(opp.in_play) == 0 else True
                if card.card_type == "Spell" and card.needs_relic_target():
                    card.can_be_clicked = False if len(cp.relics) == 0 and len(opp.relics) == 0 else True
                if card.card_type == "Entity" and not cp.can_summon():
                    card.can_be_clicked = False
                if card.name == "Mind Manacles":
                    if len(opp.in_play) == 0:
                        card.can_be_clicked = False
                    card.can_be_clicked = False
                    for e in opp.in_play:
                        if not e.has_ability("Lurker"):
                            card.can_be_clicked = True

    def set_targets_for_target_type(self, target_type, target_restrictions):
        if target_type == "any_player":
            self.set_targets_for_player_effect()
        if target_type == "any_enemy":
            self.set_targets_for_enemy_damage_effect()
        if target_type == "any":
            self.set_targets_for_damage_effect()
        elif target_type == "entity":
            self.set_targets_for_entity_effect(target_restrictions)
        elif target_type == "relic":
            self.set_targets_for_relic_effect()
        elif target_type == "opponents_entity":
            self.set_targets_for_opponents_entity_effect(target_restrictions)

    def set_targets_for_damage_effect(self):
        for card in self.opponent().in_play:
            if not card.has_ability("Lurker"):
                card.can_be_clicked = True
        for card in self.current_player().in_play:
            if not card.has_ability("Lurker"):
                card.can_be_clicked = True
        self.opponent().can_be_clicked = True
        self.current_player().can_be_clicked = True        

    def set_targets_for_enemy_damage_effect(self):
        for card in self.opponent().in_play:
            card.can_be_clicked = True
        self.opponent().can_be_clicked = True

    def set_targets_for_player_effect(self):
        self.opponent().can_be_clicked = True
        self.current_player().can_be_clicked = True

    def set_targets_for_entity_effect(self, target_restrictions):
        if len(target_restrictions) > 0 and list(target_restrictions[0].keys())[0] == "power":
            did_target = False
            for card in self.opponent().in_play:
                if card.power >= list(target_restrictions[0].values())[0]:
                    if not card.has_ability("Lurker"):
                        card.can_be_clicked = True
                        did_target = True
            for card in self.current_player().in_play:
                if card.power >= list(target_restrictions[0].values())[0]:
                    if not card.has_ability("Lurker"):
                        card.can_be_clicked = True
                        did_target = True
            return did_target

        did_target = False
        for card in self.opponent().in_play:
            if not card.has_ability("Lurker"):
                card.can_be_clicked = True
                did_target = True
        for card in self.current_player().in_play:
            if not card.has_ability("Lurker"):
                card.can_be_clicked = True
                did_target = True
        return did_target

    def set_targets_for_relic_effect(self):
        did_target = False
        for card in self.opponent().relics:
            card.can_be_clicked = True
            did_target = True
        for card in self.current_player().relics:
            card.can_be_clicked = True
            did_target = True
        return did_target

    def set_targets_for_opponents_entity_effect(self, target_restrictions):
        if len(target_restrictions) > 0 and list(target_restrictions[0].keys())[0] == "needs_guard":
            set_targets = False
            for e in self.opponent().in_play:
                if not e.has_ability("Lurker"):
                    if e.has_ability("Guard"):
                        set_targets = True
                        e.can_be_clicked = True
            return set_targets

        set_targets = False
        for card in self.opponent().in_play:
            if not card.has_ability("Lurker"):
                card.can_be_clicked = True
                set_targets = True
        return set_targets

    def has_targets_for_entity_effect(self, target_restrictions):
        if len(target_restrictions) > 0 and list(target_restrictions[0].keys())[0] == "needs_guard":
            for e in self.current_player().in_play:
                if e.has_ability("Guard"):
                    if not e.has_ability("Lurker"):
                        return True
            return False

        if len(target_restrictions) > 0 and list(target_restrictions[0].keys())[0] == "power":
            for e in self.current_player().in_play:
                if self.power_with_tokens(e, self.current_player()) >= list(target_restrictions[0].values())[0]:
                    return True
            return False

        for e in self.current_player().in_play:
            if not e.has_ability("Lurker"):
                return True
        return self.has_targets_for_opponents_entity_effect(target_restrictions)

    def has_targets_for_opponents_entity_effect(self, target_restrictions):
        if len(target_restrictions) > 0 and target_restrictions[0] == "needs_guard":
            for e in self.opponent().in_play:
                if e.has_ability("Guard"):
                    if not e.has_ability("Lurker"):
                        return True
            return False

        if len(target_restrictions) > 0 and list(target_restrictions[0].keys())[0] == "power":
            for e in self.opponent().in_play:
                if self.power_with_tokens(e, self.opponent()) >= list(target_restrictions[0].values())[0]:
                    return True
            return False

        for e in self.opponent().in_play:
            if not e.has_ability("Lurker"):
                return True
        return False

    def hide_revealed_cards(self, message):
        self.current_player().reset_card_choice_info()
        return message

    def join(self, message):
        join_occured = True
        if len(self.players) == 0:
            self.players.append(Player(self, {"username":message["username"]}, new=True))            
            self.players[len(self.players)-1].deck_id = int(message["deck_id"]) if "deck_id" in message and message["deck_id"] != "None" else None
            message["log_lines"].append(f"{message['username']} created the game.")
            if self.ai_type == "pvai":
                message["log_lines"].append(f"{self.ai} joined the game.")
                self.players.append(Player(self, {"username":self.ai}, new=True, bot=self.ai))
                self.players[len(self.players)-1].deck_id = int(message["deck_id"]) if "deck_id" in message and message["deck_id"] != "None" else None
        elif len(self.players) == 1:
            message["log_lines"].append(f"{message['username']} joined the game.")
            self.players.append(Player(self, {"username":message["username"]}, new=True))
            self.players[len(self.players)-1].deck_id = int(message["deck_id"]) if "deck_id" in message and message["deck_id"] != "None" else None
        elif len(self.players) >= 2:
            print(f"an extra player tried to join players {[p.username for p in self.players]}")
            join_occured = False

        if len(self.players) == 2 and join_occured and self.game_type in ["ingame", "test_stacked_deck", "constructed"]:
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
        elif game_type == "choose_race":
            self.start_choose_race_game(message)
        elif game_type == "choose_race_prebuilt":
            self.start_choose_race_prebuilt_game(message)
        elif game_type == "test_stacked_deck":
            self.start_test_stacked_deck_game(message)
        elif game_type == "constructed":
            self.start_constructed_game(message)
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
        self.send_start_first_turn(message)

    def start_choose_race_prebuilt_game(self, message):
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

    def start_constructed_game(self, message):
        if self.players[0].max_mana == 0: 
            for x in range(0, 2):
                decks_db = JsonDB().decks_database()
                decks = decks_db[self.players[x].username]["decks"] if self.players[x].username in decks_db else []
                deck_to_use = None
                for d in decks:
                    if d["id"] == self.players[x].deck_id:
                        deck_to_use = d

                default_deck = {"cards": {"Riftwalker Djinn": 2, "Mana Shrub": 2, "Thought Sprite": 2, "Think": 2, "LionKin": 2, "Faerie Queen": 2, "Lightning Elemental": 2, "Tame Tempest": 2, "Kill": 2, "Zap": 2, "Fire Elemental": 2, "Siz Pop": 2, "Counterspell": 2, "Familiar": 2, "Mind Manacles": 2, "Inferno Elemental": 2}, "id": 0}
                deck_to_use = deck_to_use if deck_to_use else default_deck
                card_names = []
                for key in deck_to_use["cards"]:
                    for _ in range(0, deck_to_use["cards"][key]):
                        card_names.append(key)
                for card_name in card_names:
                    self.players[x].add_to_deck(card_name, 1)
                random.shuffle(self.players[x].deck)
                self.players[x].max_mana = 1
                self.players[x].draw(5)

            self.send_start_first_turn(message)

    def send_start_first_turn(self, message):
        new_message = copy.deepcopy(message)
        new_message["move_type"] = "START_FIRST_TURN"
        new_message["username"] = self.players[0].username
        self.play_move(new_message)

    def end_turn(self, message):
        if len(self.current_player().card_choice_info["cards"]) > 0 or \
            self.current_player().card_info_to_resolve["card_id"]:
            print(f"can't end turn when there is an effect left to resolve {self.current_player().card_info_to_resolve['effect_type']} {self.current_player().card_choice_info}")
            return message
        self.remove_temporary_tokens()
        self.remove_temporary_abilities()
        self.clear_damage_this_turn()
        self.turn += 1
        message["log_lines"].append(f"{self.current_player().username}'s turn.")
        message = self.current_player().start_turn(message)
        return message

    def select_card_in_hand(self, message):
        # todo: what happens if you select a card then another card?
        for card in self.current_player().hand:
            if card.id == message["card"]:
                message["card_name"] = card.name
                if card.needs_card_being_cast_target():
                    print(f"can't select counterspell on own turn")
                    return None
                elif card.needs_relic_target() and len(self.current_player().relics) == 0 and len(self.opponent().relics) == 0 :
                    print(f"can't select relic targetting spell with no relics in play")
                    return None
                elif card.cost <= self.current_player().mana:
                    if self.current_player().selected_spell() and card.id == self.current_player().selected_spell().id and card.needs_targets():
                        self.current_player().reset_card_info_to_resolve()
                    elif self.current_player().selected_spell() and card.id == self.current_player().selected_spell().id:
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
                    elif card.card_type == "Relic":
                        if self.current_player().can_play_relic():
                            message["move_type"] = "PLAY_CARD"
                            message = self.play_move(message)
                        else:
                            print(f"can't play relic")
                    else:
                        self.current_player().card_info_to_resolve["card_id"] = card.id
                        self.current_player().card_info_to_resolve["effect_type"] = "spell_cast"

                else:
                    print(f"can't select, card costs too much - costs {card.cost}, mana available {self.current_player().mana}")                        
                    return None
                break
        return message

    def select_entity(self, message):
        cp = self.current_player()
        if cp.card_info_to_resolve["effect_type"] in ["entity_comes_into_play", "entity_activated"]:
            defending_card, defending_player = self.get_in_play_for_id(message["card"])
            if defending_card.has_ability("Lurker"):
                print(f"can't target entity with Lurker")
                return None                
            message["defending_card"] = message["card"]
            card = cp.selected_entity()
            if cp.card_info_to_resolve["effect_type"] == "entity_comes_into_play":
                message = self.select_entity_target_for_entity_effect(card, message)
            elif cp.card_info_to_resolve["effect_type"] == "entity_activated": 
                message = self.select_entity_target_for_entity_activated_effect(card, message)
        elif cp.card_info_to_resolve["effect_type"] == "spell_cast":
            selected_card = cp.selected_spell()
            defending_card, defending_player = self.get_in_play_for_id(message["card"])
            if not selected_card.can_target_entities():
                print(f"can't target entity with {selected_card.name}")
                return None                                
            if defending_card.has_ability("Lurker"):
                print(f"can't target entity with Lurker")
                return None                
            # todo handle cards with multiple effects
            if cp.selected_spell().effects[0].target_type == "opponents_entity" and self.get_in_play_for_id(message["card"])[0] not in self.opponent().in_play:
                print(f"can't target own entity with opponents_entity effect from {cp.selected_spell().name}")
                return None
            message["defending_card"] = message["card"]
            message = self.select_entity_target_for_spell(cp.selected_spell(), message)
        elif len(cp.card_choice_info["cards"]) > 0 and cp.card_choice_info["choice_type"] == "select_entity_for_ice_prison":
             selected_card = cp.in_play_card(message["card"])
             chose_card = False
             if selected_card:
                for c in cp.card_choice_info["cards"]:
                    if c.id == selected_card.id:
                        selected_card.attacked = False
                        cp.reset_card_choice_info()
                        chose_card = True
             if not chose_card:
                print("can't select that entity to un-attack for ice prison")
        elif cp.controls_entity(message["card"]):
            card, _ = self.get_in_play_for_id(message["card"])
            if card == cp.selected_entity():                
                only_has_ambush_attack = False
                if not card.has_ability("Fast"):
                    if card.has_ability("Ambush"):
                        if card.turn_played == self.turn:
                            only_has_ambush_attack = True
                if only_has_ambush_attack:
                    print(f"can't attack opponent because an entity only has Ambush")
                elif self.opponent().has_guard() and not cp.in_play_card(message["card"]).has_ability("Evade Guard"):                        
                    self.current_player().reset_card_info_to_resolve()
                    print(f"can't attack opponent because an entity has Guard")
                else:                 
                    message["move_type"] = "ATTACK"
                    message["card_name"] = cp.in_play_card(message["card"]).name
                    message = self.play_move(message)   
            elif cp.selected_relic():
                defending_card, defending_player = self.get_in_play_for_id(message["card"])
                return self.activate_relic_on_entity(message, defending_card, defending_player)
            elif cp.can_select_for_attack(message["card"]):
                cp.select_in_play(message["card"])
            else:
                print("can't select that entity")
                return None
        elif not cp.controls_entity(message["card"]):
            defending_card, defending_player = self.get_in_play_for_id(message["card"])
            selected_entity = cp.selected_entity()
            if selected_entity:
                if not defending_card.has_ability("Lurker") and (not self.opponent().has_guard() or defending_card.has_ability("Guard") or selected_entity.has_ability("Evade Guard")):                        
                    message["move_type"] = "ATTACK"
                    message["card"] = selected_entity.id
                    message["card_name"] = selected_entity.name
                    message["defending_card"] = defending_card.id
                    message = self.play_move(message)
                else:
                    if defending_card.has_ability("Lurker"):
                        print(f"can't attack {defending_card.name} because it has Lurker")
                    else:
                        print(f"can't attack {defending_card.name} because another entity has Guard")
                    return None                                            
            elif cp.selected_relic():
                return self.activate_relic_on_entity(message, defending_card, defending_player)
            else:
                print(f"nothing selected to target {defending_card.name}")
                return None
        else:
            print("Should never get here")                                
        return message

    def activate_relic_on_entity(self, message, defending_card, defending_player):
        if defending_card.has_ability("Lurker"):
            print(f"can't target entity with Lurker")
            return None                
        message["move_type"] = "ACTIVATE_RELIC"
        message["card"] = self.current_player().selected_relic().id
        message["card_name"] = self.current_player().selected_relic().name
        message["defending_card"] = defending_card.id
        message = self.play_move(message)      
        return message      

    def select_relic(self, message):
        cp = self.current_player()
        if cp.card_info_to_resolve["effect_type"] in ["entity_comes_into_play"]:
            message = self.select_relic_target_for_entity_effect(cp.selected_entity(), message)
        elif cp.card_info_to_resolve["effect_type"] in ["entity_activated"]:
            message = self.select_relic_target_for_relic_effect(cp.selected_entity(), message)
        elif cp.selected_spell():  
            # todo handle cards with multiple effects
            if cp.selected_spell().effects[0].target_type == "opponents_relic" and self.get_in_play_for_id(message["card"])[0] not in self.opponent().relics:
                print(f"can't target own relic with opponents_relic effect from {cp.selected_spell().name}")
                return None
            message = self.select_relic_target_for_spell(cp.selected_spell(), message)
        elif cp.controls_relic(message["card"]):            
            relic = cp.relic_in_play(message["card"])
            if cp.selected_relic() and relic.id == cp.selected_relic().id and relic.needs_target_for_activated_effect():
                cp.reset_card_info_to_resolve()
            elif relic.can_activate_abilities and relic.effects_enabled()[0].cost <= cp.mana:
                if not relic.needs_target_for_activated_effect():
                        message["move_type"] = "ACTIVATE_RELIC"
                        message = self.play_move(message)
                elif relic.needs_entity_target_for_activated_effect() and (len(cp.in_play) > 0 or len(self.opponent().in_play) > 0):
                    cp.select_relic(message["card"])
                elif not relic.needs_entity_target_for_activated_effect(): # player targets
                    cp.select_relic(message["card"])
                else:
                    cp.reset_card_info_to_resolve()
            else:
                print(f"can't activate relic")
                return None
        elif not cp.controls_relic(message["card"]):
            defending_card = self.get_in_play_for_id(message["card"])
            selected_relic = cp.selected_relic()
            if selected_relic:
                message["move_type"] = "ACTIVATE_RELIC"
                message["card"] = selected_relic.id
                message["card_name"] = selected_relic.name
                message["defending_relic"] = defending_relic.id
                message = self.play_move(message)
            else:
                print(f"nothing selected to target {defending_card.name}")
                return None
        else:
            print("Should never get here")                                
        return message

    def select_player(self, move_type, message):
        if self.current_player().selected_entity() and self.current_player().card_info_to_resolve["effect_type"] in ["entity_activated", "entity_comes_into_play"]:
            if move_type == 'SELECT_OPPONENT':
                message = self.select_player_target_for_entity_effect(self.opponent().username, self.current_player().selected_entity(), message)
            else:
                message = self.select_player_target_for_entity_effect(self.current_player().username, self.current_player().selected_entity(), message)
        elif self.current_player().selected_spell():
            target_player = self.current_player() if move_type == 'SELECT_SELF' else self.opponent()
            casting_spell = True
            message = self.select_player_target_for_spell(target_player.username, self.current_player().selected_spell(), message)
        elif self.current_player().selected_relic():
            target_player = self.current_player() if move_type == 'SELECT_SELF' else self.opponent()
            using_relic = True
            message = self.select_player_target_for_relic_effect(target_player.username, self.current_player().selected_relic(), message)
        else:
            if self.current_player().selected_entity():
                card = self.current_player().selected_entity()
                only_has_ambush_attack = False
                if not card.has_ability("Fast"):
                    if card.has_ability("Ambush"):
                        if card.turn_played == self.turn:
                            only_has_ambush_attack = True
                if (card.has_ability("Evade Guard") or not self.opponent().has_guard()) and not only_has_ambush_attack:
                    message["card"] = card.id
                    message["card_name"] = card.name
                    message["move_type"] = "ATTACK"
                    message = self.play_move(message)                    
                    self.current_player().reset_card_info_to_resolve()
                elif only_has_ambush_attack:
                    print(f"can't attack opponent because the entity only has ambush")
                    return None
                else:
                    print(f"can't attack opponent because an entity has Guard")
                    return None
        return message

    def attack(self, message):
        card_id = message["card"]
        attacking_card = self.current_player().in_play_card(card_id)
        attacking_card.attacked = True
        self.current_player().reset_card_info_to_resolve()
        for a in attacking_card.abilities:
            if a.descriptive_id == "Lurker":
                a.enabled = False
        for a in attacking_card.added_abilities:
            if a.descriptive_id == "Lurker":
                a.enabled = False
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
            message["log_lines"].append(f"{attacking_card.name} attacks {self.opponent().username} for {self.power_with_tokens(attacking_card, self.current_player())}.")
            self.opponent().damage(self.power_with_tokens(attacking_card, self.current_player()))
            self.current_player().do_attack_abilities(attacking_card)
        return message

    def activate_relic(self, message):
        card_id = message["card"]
        relic = self.current_player().relic_in_play(card_id)
        relic.can_activate_abilities = False
        self.current_player().reset_card_info_to_resolve()
        if "defending_card" in message:
            defending_card, _  = self.get_in_play_for_id(message["defending_card"])
            message["log_lines"].append(f"{self.current_player().username} uses {relic.name} on {defending_card.name}")
            effect_targets = {}
            e = relic.enabled_activated_effects()[0]
            effect_targets[e.id] = {"id": defending_card.id, "target_type":e.target_type};
            message = self.current_player().do_card_effect(relic, e, message, effect_targets)
            self.current_player().reset_card_info_to_resolve()
        else:
            e = relic.enabled_activated_effects()[0]
            if e.target_type == "self":
                message = self.current_player().do_card_effect(relic, e, message, [{"id": message["username"], "target_type": "player"}])
            elif e.target_type == "opponent":
                message = self.current_player().do_card_effect(relic, e, message, [{"id": self.opponent().username, "target_type": "player"}])
            # todo unhardcode for other fetch types if we can fetch more than Relics
            elif e.target_type == "Relic":
                message = self.current_player().do_card_effect(relic, e, message, [{"id": message["username"], "target_type": e.target_type}])
            else:
                target_player = self.players[0]
                if target_player.username != message["effect_targets"][e.id]["id"]:
                    target_player = self.players[1]
                message["log_lines"].append(f"{self.current_player().username} uses {relic.name} on {target_player.username}")
                message["effect_targets"] = {}
                message["effect_targets"][e.id] = {"id": target_player.username, "target_type": "player"};
                message = self.current_player().do_card_effect(relic, e, message, message["effect_targets"])
                self.current_player().reset_card_info_to_resolve()

        if relic.enabled_activated_effects()[0].sacrifice_on_activate:
            self.send_card_to_played_pile(relic, self.current_player())
        return message

    def activate_entity(self, message):
        card_id = message["card"]
        entity, _ = self.get_in_play_for_id(card_id)
        if not entity.can_activate_abilities:
            print(f"can't activate, already used {entity}")
            return None

        e = entity.enabled_activated_effects()[0]

        for a in entity.abilities:
            if a.descriptive_id == "Lurker":
                a.enabled = False
        for a in entity.added_abilities:
            if a.descriptive_id == "Lurker":
                a.enabled = False

        if e.name == "pump_power":
            # todo don't hardcode for Infernus
            message["log_lines"].append(f"{self.current_player().username} pumps {entity.name} +1/+0.")
            effect_targets = {}
            effect_targets[e.id] = {"id": entity.id, "target_type":e.target_type};
            message = self.current_player().do_card_effect(entity, e, message, effect_targets)
        elif e.name == "unwind":
            if "defending_card" in message:
                message = self.current_player().do_card_effect(entity, e, message, message["effect_targets"])
                self.current_player().reset_card_info_to_resolve()
                entity.can_activate_abilities = False
            else:
                message["log_lines"].append(f"{self.current_player().username} activates {entity.name}.")
                message = self.current_player().target_or_do_entity_effects(entity, message, self.current_player().username, is_activated_effect=True)
        else:
            print(f"unsupported entity effect {e}")
        return message

    def make_card(self, message):
        self.current_player().add_to_deck(message["card"]["name"], 1, add_to_hand=True)
        self.current_player().reset_card_choice_info()

    def make_effect(self, message):
        message["log_lines"].append(f"{message['username']} chose {message['card']['global_effect']}.")
        self.global_effects.append(message["card"]["global_effect"])
        self.current_player().reset_card_choice_info()
        return message

    def fetch_card(self, message, card_type, into_play=False):
        """
            Fetch the selected card from current_player's deck
        """
        card = None
        for c in self.current_player().deck:
            if c.id == message['card']:
                card = c
        if card_type == "Relic":
            if into_play:
                self.current_player().relics.append(card)
            else:
                self.current_player().hand.append(card)
            self.current_player().deck.remove(card)
        message["log_lines"].append(f"{message['username']} chose {card.name}.")

        self.current_player().reset_card_choice_info()
        return message

    def get_in_play_for_id(self, card_id):
        """
            Returns a tuple of the entity and controlling player for a card_id of a card that is an in_play entity
        """
        for p in [self.opponent(), self.current_player()]:
            for card in p.in_play + p.relics:
                if card.id == card_id:
                    return card, p
        return None, None

    def send_card_to_played_pile(self, card, player):
        """
            Send the card to the player's played_pile and reset any temporary effects on the card
        """
        if card in player.relics:
            player.relics.remove(card)
        if card in player.in_play:
            player.in_play.remove(card)
        card.do_leaves_play_effects(player)

        if card.id == player.card_info_to_resolve["card_id"]:
            player.reset_card_info_to_resolve()

        if not card.is_token:
            new_card = self.factory_reset_card(card, player)
            player.played_pile.append(new_card)

        self.update_for_entity_changes_zones(player)

    def update_for_entity_changes_zones(self, player):

        # code for War Scorpion
        for e in player.in_play:
            effect = e.effect_with_trigger("entity_changes_zones")
            if effect and effect.name == "toggle_symbiotic_fast":
                abilities_to_remove = []
                for ability in e.added_abilities:
                    if ability.name == "Fast":
                       abilities_to_remove.append(ability) 
                for ability in abilities_to_remove:
                    e.added_abilities.remove(ability)


        anything_friendly_has_fast = False
        for e in player.in_play:
            if e.has_ability("Fast"):
                anything_friendly_has_fast = True

        for e in player.in_play:
            effect = e.effect_with_trigger("entity_changes_zones")
            if effect and effect.name == "toggle_symbiotic_fast":
                if anything_friendly_has_fast:
                    e.added_abilities.append(CardAbility({
                        "name": "Fast",
                        "descriptive_id": "Fast"
                    }, len(e.added_abilities)))


        # code for Arsenal relic
        for r in player.relics:
            effect = r.effect_with_trigger("entity_changes_zones")
            if effect:
            if effect and effect.name == "set_token" and effect.target_type == "self_entities":
                for e in self.opponent().in_play:
                    for token in e.tokens:
                        if token.id == r.id:
                            e.tokens.remove(token)
                            break

                for e in self.current_player().in_play:
                    for token in e.tokens:
                        if token.id == r.id:
                            e.tokens.remove(token)
                            break

                for e in player.in_play:
                    new_token = copy.deepcopy(effect.tokens[0])
                    new_token.id = r.id
                    player.do_add_token_effect_on_entity(
                        new_token, 
                        e.id
                    )

    def factory_reset_card(self, card, player):
        new_card = None
        for c in Game.all_cards():
            if c.name == card.name:
                new_card = copy.deepcopy(c)
        new_card.id = card.id
        new_card.owner_username = player.username
        new_card = player.modify_new_card(self, new_card)

        return new_card

    def resolve_combat(self, attacking_card, defending_card):
        if attacking_card.shielded:
            attacking_card.shielded = False
        else:
            attacking_card.damage += self.power_with_tokens(defending_card, self.opponent())
            attacking_card.damage_this_turn += self.power_with_tokens(defending_card, self.opponent())
            if attacking_card.damage >= attacking_card.toughness_with_tokens():
                self.send_card_to_played_pile(attacking_card, self.current_player())
            elif defending_card.has_ability("DamageTakeControl"):
                self.current_player().in_play.remove(attacking_card)
                self.opponent().in_play.append(attacking_card)
                self.update_for_entity_changes_zones(self.current_player())
                self.update_for_entity_changes_zones(self.opponent())
        if defending_card.shielded:
            defending_card.shielded = False
        else:
            if attacking_card.has_ability("Stomp"):
                stomp_damage = self.power_with_tokens(attacking_card, self.current_player()) - (defending_card.toughness_with_tokens() - defending_card.damage)
                if stomp_damage > 0:
                    self.opponent().damage(stomp_damage)
            defending_card.damage += self.power_with_tokens(attacking_card, self.current_player())
            defending_card.damage_this_turn += self.power_with_tokens(attacking_card, self.current_player())
            if defending_card.damage >= defending_card.toughness_with_tokens():
                self.send_card_to_played_pile(defending_card, self.opponent())
            elif attacking_card.has_ability("DamageTakeControl"):
                self.opponent().in_play.remove(defending_card)
                self.current_player().in_play.append(defending_card)
                self.update_for_entity_changes_zones(self.current_player())
                self.update_for_entity_changes_zones(self.opponent())


    def remove_temporary_tokens(self):
        for c in self.current_player().in_play + self.opponent().in_play:
            perm_tokens = []
            oldToughness = c.toughness_with_tokens()
            for t in c.tokens:
                t.turns -= 1
                if t.turns != 0:
                    perm_tokens.append(t)
            c.tokens = perm_tokens
            newToughness = c.toughness_with_tokens()
            toughness_change_from_tokens = oldToughness - newToughness
            if toughness_change_from_tokens > 0:
                c.damage -= min(toughness_change_from_tokens, c.damage_this_turn)  

    def remove_temporary_abilities(self):
        perm_abilities = []
        for a in self.current_player().added_abilities:
            a.turns -= 1
            if a.turns != 0:
                perm_abilities.append(a)
        self.current_player().added_abilities = perm_abilities

    def clear_damage_this_turn(self):
        for c in self.current_player().in_play + self.opponent().in_play:
            c.damage_this_turn = 0
        self.current_player().damage_this_turn = 0
        self.opponent().damage_this_turn = 0

    def select_relic_target(self, card_to_target, message, move_type):
        new_message = copy.deepcopy(message)
        new_message["move_type"] = move_type
        selected_card = self.current_player().relic_in_play(message["card"])
        if not selected_card:
            selected_card = self.opponent().relic_in_play(message["card"])
        effect_targets = {}
        #todo multiple effects
        effect_targets[card_to_target.effects[0].id] = {"id": selected_card.id, "target_type":"relic"}            
        new_message["effect_targets"] = effect_targets
        new_message["card"] = card_to_target.id
        new_message["card_name"] = card_to_target.name

        self.current_player().reset_card_info_to_resolve()
        new_message = self.play_move(new_message)       
        return new_message             

    def select_relic_target_for_spell(self, card_to_target, message):
        return self.select_relic_target(card_to_target, message, "PLAY_CARD")

    def select_relic_target_for_entity_effect(self, entity_with_effect_to_target, message):
        return self.select_relic_target(entity_with_effect_to_target, message, "RESOLVE_ENTITY_EFFECT")

    def select_relic_target_for_relic_effect(self, relic_with_effect_to_target, message):
        return self.select_relic_target(relic_with_effect_to_target, message, "RESOLVE_ENTITY_EFFECT")

    def select_entity_target(self, card_to_target, message, move_type, activated_effect=False, entity_activated_effect=False):
        new_message = copy.deepcopy(message)
        new_message["move_type"] = move_type
        selected_card = self.current_player().in_play_card(message["defending_card"])
        if not selected_card:
            selected_card = self.opponent().in_play_card(message["defending_card"])
        effect_targets = {}
        if activated_effect:
            effect_targets[card_to_target.enabled_activated_effects()[0].id] = {"id": selected_card.id, "target_type":"entity"}            
        else:
            effect_targets[card_to_target.effects[0].id] = {"id": selected_card.id, "target_type":"entity"}            
            # hack for siz pop and stiff wind
            if len(card_to_target.effects) == 2:
                effect_targets[card_to_target.effects[1].id] = {"id": message["username"], "target_type":"player"}
        new_message["effect_targets"] = effect_targets
        new_message["card"] = card_to_target.id
        new_message["card_name"] = card_to_target.name
        self.current_player().reset_card_info_to_resolve()
        new_message = self.play_move(new_message)       
        return new_message             

    def select_entity_target_for_spell(self, card_to_target, message):
        return self.select_entity_target(card_to_target, message, "PLAY_CARD")

    def select_entity_target_for_entity_effect(self, entity_with_effect_to_target, message):
        return self.select_entity_target(entity_with_effect_to_target, message, "RESOLVE_ENTITY_EFFECT")

    def select_entity_target_for_relic_effect(self, relic_with_effect_to_target, message):
        return self.select_entity_target(relic_with_effect_to_target, message, "ACTIVATE_RELIC", activated_effect=True)

    def select_entity_target_for_entity_activated_effect(self, relic_with_effect_to_target, message):
        return self.select_entity_target(relic_with_effect_to_target, message, "ACTIVATE_ENTITY", activated_effect=True)

    def select_player_target(self, username, entity_with_effect_to_target, message, move_type):
        new_message = copy.deepcopy(message)
        new_message["move_type"] = move_type
        effect_targets = {}
        if entity_with_effect_to_target.card_type == "Relic" or (entity_with_effect_to_target.card_type == "Entity" and entity_with_effect_to_target.turn_played > self.turn):
            effect_targets[entity_with_effect_to_target.enabled_activated_effects()[0].id] = {"id": username, "target_type":"player"}            
        else:
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

    def select_player_target_for_relic_effect(self, username, relic_with_effect_to_target, message):
        return self.select_player_target(username, relic_with_effect_to_target, message, "ACTIVATE_RELIC")

    def is_under_ice_prison(self):
        for c in self.current_player().relics + self.opponent().relics:
            if len(c.effects_triggered()) > 0 and c.effects_triggered()[0].name ==  "stop_entity_renew":
                return True
        return False

    def power_with_tokens(self, card, player):
        power = card.power
        for t in card.tokens:
            if t.multiplier == "self_relics":
                power += t.power_modifier * len(player.relics)
            else:
                power += t.power_modifier
        return power


class Player:

    def __init__(self, game, info, new=False, bot=None):
        self.username = info["username"]
        self.race = info["race"] if "race" in info else None
        self.deck_id = info["deck_id"] if "deck_id" in info else None
        self.bot = bot

        JsonDB().add_to_player_database(self.username, JsonDB().player_database())
        self.game = game
        if new:
            self.hit_points = 30
            self.damage_this_turn = 0
            self.armor = 0
            self.mana = 0
            self.max_mana = 0
            self.hand = []
            self.in_play = []
            self.relics = []
            self.deck = []
            self.played_pile = []
            self.can_be_clicked = False
            self.added_abilities = []
            self.reset_card_info_to_resolve()
            self.reset_card_choice_info()
        else:
            self.hand = [Card(c_info) for c_info in info["hand"]]
            self.in_play = [Card(c_info) for c_info in info["in_play"]]
            self.relics = [Card(c_info) for c_info in info["relics"]]
            self.hit_points = info["hit_points"]
            self.damage_this_turn = info["damage_this_turn"]
            self.armor = info["armor"]
            self.mana = info["mana"]
            self.max_mana = info["max_mana"]
            self.deck = [Card(c_info) for c_info in info["deck"]]
            self.played_pile = [Card(c_info) for c_info in info["played_pile"]]
            self.can_be_clicked = info["can_be_clicked"]
            self.added_abilities = [CardAbility(a, idx) for idx, a in enumerate(info["added_abilities"])] if "added_abilities" in info and info["added_abilities"] else []
            self.card_info_to_resolve = info["card_info_to_resolve"]
            self.card_choice_info = {"cards": [Card(c_info) for c_info in info["card_choice_info"]["cards"]], "choice_type": info["card_choice_info"]["choice_type"]}

    def __repr__(self):
        return f"{self.username} ({self.race}, deck_id: {self.deck_id}) - \
                {self.hit_points} hp - {self.damage_this_turn} damage_this_turn - {self.armor} armor, {self.mana} mana, self.card_info_to_resolve {self.card_info_to_resolve} \
                {self.max_mana} max_mana, {len(self.hand)} cards, {len(self.in_play)} in play, \
                {len(self.deck)} in deck, {len(self.played_pile)} in played_pile, \
                self.can_be_clicked {self.can_be_clicked}, \
                self.added_abilities self.card_choice_info \
                {self.added_abilities}, self.relics {self.relics}"

    def as_dict(self):
        return {
            "username": self.username,
            "race": self.race,
            "hit_points": self.hit_points,
            "damage_this_turn": self.damage_this_turn,
            "armor": self.armor,
            "mana": self.mana,
            "max_mana": self.max_mana,
            "deck_id": self.deck_id,
            "card_info_to_resolve": self.card_info_to_resolve,
            "hand": [c.as_dict() for c in self.hand],
            "in_play": [c.as_dict() for c in self.in_play],
            "relics": [c.as_dict() for c in self.relics],
            "deck": [c.as_dict() for c in self.deck],
            "played_pile": [c.as_dict() for c in self.played_pile],
            "can_be_clicked": self.can_be_clicked,
            "added_abilities": [a.as_dict() for a in self.added_abilities],
            "card_choice_info": {"cards": [c.as_dict() for c in self.card_choice_info["cards"]], "choice_type": self.card_choice_info["choice_type"]}
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

    def damage(self, amount):
        while amount > 0 and self.armor > 0:
            amount -= 1
            self.armor -= 1

        while amount > 0 and self.hit_points > 0:
            amount -= 1
            if self.hit_points == 1 and self.cant_die_ability():
                continue
            self.hit_points -= 1
            self.damage_this_turn += 1

    def draw(self, number_of_cards):
        for i in range(0,number_of_cards):
            if len(self.deck) == 0:
                for c in self.played_pile:
                    self.deck.append(c)
                self.played_pile = [] 
            if len(self.deck) == 0 or len(self.hand) == 11:
                continue
            card = self.deck.pop()
            self.hand.append(card)
            for r in self.relics:
                for effect in r.effects_triggered():
                    if effect.name == "reduce_cost" and card.card_type == effect.target_type:
                        card.cost -= 1
                        card.cost = max(0, card.cost)

    def do_card_effect(self, card, e, message, effect_targets):
        # weapons and instruments
        if e.counters >= 1:
            e.counters -= 1

        print(f"Do card effect: {e.name}");
        if e.name == "increase_max_mana":
            self.do_increase_max_mana_effect_on_player(effect_targets[e.id]["id"], e.amount)
            message["log_lines"].append(f"{self.username} increases max mana by {e.amount}.")
        elif e.name == "set_max_mana":
            self.do_set_max_mana_effect(e.amount)
            message["log_lines"].append(f"{self.username} resets everyone's max mana to {e.amount} with {card.name}.")
        elif e.name == "reduce_mana":
            self.do_reduce_mana_effect_on_player(card, effect_targets[e.id]["id"], e.amount)
            message["log_lines"].append(f"{self.username} draws {e.amount} from {card.name}.")
        elif e.name == "draw":
            self.do_draw_effect_on_player(card, effect_targets[e.id]["id"], e.amount)
            message["log_lines"].append(f"{self.username} draws {e.amount} from {card.name}.")
        elif e.name == "draw_if_damaged_opponent":
            drawn_count = self.do_draw_if_damaged_opponent_effect_on_player(card, effect_targets[e.id]["id"], e.amount)
            if drawn_count > 0:
                message["log_lines"].append(f"{self.username} draws {e.amount} from {card.name}.")
        elif e.name == "make_token":
            if e.target_type == "self":
                self.do_make_token_effect(e)
                message["log_lines"].append(f"{card.name} makes {e.amount} tokens.")
            else:
                self.game.opponent().do_make_token_effect(e)
                message["log_lines"].append(f"{card.name} makes {e.amount} tokens for {self.game.opponent().username}.")
        elif e.name == "fetch_card":
            self.do_fetch_card_effect_on_player(card, effect_targets[e.id]["id"], e.target_type, e.target_restrictions, choice_type="fetch_relic_into_hand")
            message["log_lines"].append(f"{self.username} cracks {card.name} to fetch a relic.")
        elif e.name == "fetch_card_into_play":
            self.do_fetch_card_effect_on_player(card, effect_targets[e.id]["id"], e.target_type, e.target_restrictions, choice_type="fetch_relic_into_play")
            message["log_lines"].append(f"{self.username} cracks {card.name} to fetch a relic.")
        elif e.name == "gain_armor":
            self.do_gain_armor_effect_on_player(card, effect_targets[e.id]["id"], e.amount)
            message["log_lines"].append(f"{self.username} gains {e.amount} armor from {card.name}.")
        elif e.name == "take_extra_turn":
            message["log_lines"].append(f"{self.username} takes an extra turn.")
            message = self.do_take_extra_turn_effect_on_player(effect_targets[e.id]["id"], message)
        elif e.name == "summon_from_deck":
            if e.target_type == "self":
                message["log_lines"].append(f"{self.username} summons something from their deck.")
            else:
                message["log_lines"].append(f"Both players fill their boards.")
            self.do_summon_from_deck_effect_on_player(e, effect_targets)
        elif e.name == "discard_random":
                self.do_discard_random_effect_on_player(card, effect_targets[e.id]["id"], e.amount)
        elif e.name == "damage":
            if effect_targets[e.id]["target_type"] == "player":
                self.do_damage_effect_on_player(card, effect_targets[e.id]["id"], e.amount)
                message["log_lines"].append(f"{self.username} deals {e.amount} damage to {effect_targets[e.id]['id']}.")
            elif effect_targets[e.id]["target_type"] == "all_entities":
                dead_entities = []
                for entity in self.in_play:
                    entity.damage += e.amount
                    entity.damage_this_turn += e.amount
                    if entity.damage >= entity.toughness_with_tokens():
                        dead_entities.append(entity)
                for entity in dead_entities:
                    self.game.send_card_to_played_pile(entity, self)
                dead_entities = []
                for entity in self.game.opponent().in_play:
                    entity.damage += e.amount
                    entity.damage_this_turn += e.amount
                    if entity.damage >= entity.toughness_with_tokens():
                        dead_entities.append(entity)
                for entity in dead_entities:
                    self.game.send_card_to_played_pile(entity, self.game.opponent())
                message["log_lines"].append(f"{self.username} deals {e.amount} damage to all entities.")
            else:
                message["log_lines"].append(f"{self.username} deals {e.amount} damage to {self.game.get_in_play_for_id(effect_targets[e.id]['id'])[0].name}.")
                self.do_damage_effect_on_entity(card, effect_targets[e.id]["id"], e.amount)
        elif e.name == "heal":
            if effect_targets[e.id]["target_type"] == "player":
                self.do_heal_effect_on_player(card, effect_targets[e.id]["id"], e.amount)
                message["log_lines"].append(f"{self.username} heals {e.amount} on {effect_targets[e.id]['id']}.")
            else:
                message["log_lines"].append(f"{self.username} heals {e.amount} on {self.game.get_in_play_for_id(effect_targets[e.id]['id'])[0].name}.")
                self.do_heal_effect_on_entity(card, effect_targets[e.id]["id"], e.amount)
        elif e.name == "attack":
            if effect_targets[e.id]["target_type"] == "player":
                self.do_damage_effect_on_player(card, effect_targets[e.id]["id"], e.power)
                self.do_attack_abilities(card)
                message["log_lines"].append(f"{self.username} attacks {effect_targets[e.id]['id']} for {e.power} damage.")
            else:
                message["log_lines"].append(f"{self.username} attacks {self.game.get_in_play_for_id(effect_targets[e.id]['id'])[0].name} for {e.power} damage.")
                self.do_attack_effect_on_entity(card, effect_targets[e.id]["id"], e.power)

            #todo fix hardcoding
            if e.counters == 0 and card.name == "Dagger":
                card.deactivate_weapon()
        elif e.name == "double_power":
            self.do_double_power_effect_on_entity(card, effect_targets[e.id]["id"])
            message["log_lines"].append(f"{self.username} doubles the power of {self.game.get_in_play_for_id(effect_targets[e.id]['id'])[0].name}.")
        elif e.name == "pump_power":
            self.do_pump_power_effect_on_entity(card, effect_targets[e.id]["id"], e.amount, e.cost)
            message["log_lines"].append(f"{self.username} pumps the power of {self.game.get_in_play_for_id(effect_targets[e.id]['id'])[0].name} by {e.amount}.")
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
        elif e.name == "switch_hit_points":
            self.do_switch_hit_points_effect()
            message["log_lines"].append(f"{self.username} uses {card.name} to switch hit points with {effect_targets[e.id]['id']}.")
        elif e.name == "enable_activated_effect":
            self.do_enable_activated_effect_effect(card)
        elif e.name == "view_hand":
            self.do_view_hand_effect()
        elif e.name == "make":
            self.do_make_effect(card, effect_targets[e.id]["id"], e.make_type, e.amount)
        elif e.name == "make_random_townie":
            self.do_make_random_townie_effect(e.amount)
            #todo fix hardcoding
            if e.counters == 0 and card.name == "Lute":
                card.deactivate_instrument()
        elif e.name == "mana":
            message["log_lines"].append(f"{effect_targets[e.id]['id']} gets {e.amount} mana.")
            self.do_mana_effect_on_player(card, effect_targets[e.id]["id"], e.amount)
        elif e.name == "add_tokens":
            if e.target_type == 'self_entities':
                message["log_lines"].append(f"{self.username} adds {str(e.tokens[0])} to their own entities.")
            else:
                message["log_lines"].append(f"{self.username} adds {str(e.tokens[0])} to {self.game.get_in_play_for_id(effect_targets[e.id]['id'])[0].name}.")
            self.do_add_tokens_effect(card, e, effect_targets)
        elif e.name == "add_effects":
            if e.target_type == "self_entities":
                message["log_lines"].append(f"{self.username} adds effects to their entities.")
            else:
                message["log_lines"].append(f"{self.username} adds effects {self.game.get_in_play_for_id(effect_targets[e.id]['id'])[0].name}.")
            self.do_add_effects_effect(e, card)           
        elif e.name == "add_player_abilities":
            if e.target_type == "opponent":
                message["log_lines"].append(f"{self.game.opponent().username} gets {card.description}.")
            else:
                message["log_lines"].append(f"{self.username} gains {card.description}.")
            self.do_add_abilities_effect(e, card)           
        elif e.name == "add_entity_abilities":
            message["log_lines"].append(f"{self.username} adds {e.abilities[0].name} to {effect_targets[e.id]['id']} with {card.name}.")
            self.do_add_abilities_effect(e, self.game.get_in_play_for_id(effect_targets[e.id]['id'])[0])           

        self.mana -= e.cost
        self.hit_points -= e.cost_hp
        
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
                self.game.update_for_entity_changes_zones(target_player)
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
                    self.game.update_for_entity_changes_zones(p)
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

    def do_draw_if_damaged_opponent_effect_on_player(self, card, target_player_username, amount):
        target_player = self.game.players[0]
        if target_player.username != target_player_username:
            target_player = self.game.players[1]
        if target_player.game.opponent().damage_this_turn > 0:
            target_player.draw(amount)
            return amount
        return 0
    
    def do_reduce_mana_effect_on_player(self, card, target_player_username, amount):
        target_player = self.game.players[0]
        if target_player.username != target_player_username:
            target_player = self.game.players[1]
        target_player.max_mana -= max(amount, 0)
        target_player.mana = min(target_player.mana, target_player.max_mana)

    def do_set_max_mana_effect(self, amount):
        for p in self.game.players:
            p.max_mana = amount
            p.mana = min(p.mana, p.max_mana)

    def do_gain_armor_effect_on_player(self, card, target_player_username, amount):
        target_player = self.game.players[0]
        if target_player.username != target_player_username:
            target_player = self.game.players[1]
        target_player.armor += amount

    def do_take_extra_turn_effect_on_player(self, target_player_username, message):
        target_player = self.game.players[0]
        if target_player.username != target_player_username:
            target_player = self.game.players[1]
        self.game.remove_temporary_tokens()
        self.game.remove_temporary_abilities()
        self.game.clear_damage_this_turn()
        self.game.turn += 2
        message = self.start_turn(message)
        return message

    def do_switch_hit_points_effect(self):
        cp_hp = self.hit_points
        self.hit_points = self.game.opponent().hit_points
        self.game.opponent().hit_points = cp_hp

    def do_entwine_effect(self):
        for p in self.game.players:
            for pile in [self.hand, self.played_pile]:
                pile_cards = []
                for c in pile:
                    p.deck.append(c)
                    pile_cards.append(c)
                for c in pile_cards:
                    pile.remove(c)
            random.shuffle(p.deck)
            p.draw(3)

    def do_enable_activated_effect_effect(self, card):
        # todo don't hardcode first effect
        card.effects[0].enabled = False
        card.effects.append(copy.deepcopy(card.effects[0].effect_to_activate))
        card.effects[len(card.effects) - 1].enabled = True
        card.description = card.effects[len(card.effects) - 1].description
        card.can_activate_abilities = True

    def do_view_hand_effect(self):
        self.card_choice_info["cards"] = copy.deepcopy(self.game.opponent().hand)
        self.card_choice_info["choice_type"] = "view_hand"

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
        target_player.damage(amount)

    def do_heal_effect_on_player(self, card, target_player_username, amount):
        target_player = self.game.players[0]
        if target_player.username != target_player_username:
            target_player = self.game.players[1]
        target_player.hit_points += amount
        target_player.hit_points = min(target_player.hit_points, 30)

    def do_discard_random_effect_on_player(self, card, target_player_username, amount, to_deck=False):
        target_player = self.game.players[0]
        if target_player.username != target_player_username:
            target_player = self.game.players[1]
        while amount > 0 and len(target_player.hand) > 0:
            amount -= 1
            card = random.choice(target_player.hand)
            target_player.hand.remove(card)
            self.game.send_card_to_played_pile(card, target_player)
            if to_deck:
                for c in target_player.played_pile:
                    if c.id == card.id:
                        break
                target_player.played_pile.remove(c)
                target_player.deck.append(c)
                random.shuffle(target_player.deck)

    def do_damage_effect_on_entity(self, card, target_entity_id, amount):
        target_card, target_player = self.game.get_in_play_for_id(target_entity_id)
        if target_card.shielded:
            target_card.shielded = False
        else:
            target_card.damage += amount
            if target_card.damage >= target_card.toughness_with_tokens():
                self.game.send_card_to_played_pile(target_card, target_player)
                if card.has_ability("die_to_top_deck"):
                    card = None
                    for c in target_player.played_pile:
                        if c.id == target_card.id:
                            card = c
                    target_player.played_pile.remove(card)
                    target_player.deck.append(card)

    def do_heal_effect_on_entity(self, card, target_entity_id, amount):
        target_card, target_player = self.game.get_in_play_for_id(target_entity_id)
        target_card.damage -= amount
        target_card.damage = max(target_card.damage, 0)

    def do_attack_effect_on_entity(self, card, target_entity_id, amount):
        target_card, target_player = self.game.get_in_play_for_id(target_entity_id)
        self.damage(self.game.power_with_tokens(target_card, target_player))
        self.do_damage_effect_on_entity(card, target_entity_id, amount)

    def do_double_power_effect_on_entity(self, card, target_entity_id):
        target_card, target_player = self.game.get_in_play_for_id(target_entity_id)
        target_card.power += self.game.power_with_tokens(target_card, target_player)

    def do_pump_power_effect_on_entity(self, card, target_entity_id, amount, cost):
        target_card, target_player = self.game.get_in_play_for_id(target_entity_id)
        target_card.power += amount

    def do_kill_effect_on_entity(self, target_entity_id):
        target_card, target_player = self.game.get_in_play_for_id(target_entity_id)
        self.game.send_card_to_played_pile(target_card, target_player)

    def do_take_control_effect_on_entity(self, target_entity_id):
        target_card, target_player = self.game.get_in_play_for_id(target_entity_id)
        target_player.in_play.remove(target_card)
        self.in_play.append(target_card)
        self.game.update_for_entity_changes_zones(target_player)
        self.game.update_for_entity_changes_zones(self)
        target_card.turn_played = self.game.turn
        if self.fast_ability():
            target_card.added_abilities.append(self.fast_ability())       
        if target_card.has_ability("Fast") or target_card.has_ability("Ambush"):
            target_card.attacked = False
    
    def do_unwind_effect_on_entity(self, target_entity_id):
        target_card, target_player = self.game.get_in_play_for_id(target_entity_id)
        target_player.in_play.remove(target_card)  

        for e in target_card.effects_leave_play():
            if e.name == "decrease_max_mana":
                target_player.max_mana -= e.amount
            target_player.mana = min(target_player.max_mana, target_player.mana)

        new_card = self.game.factory_reset_card(target_card, target_player)
        target_player.hand.append(new_card)  

    def do_make_effect(self, card, target_player_username, make_type, amount):
        target_player = self.game.players[0]
        if target_player.username != target_player_username:
            target_player = self.game.players[1]
        return target_player.make(1, make_type)

    def do_fetch_card_effect_on_player(self, card, target_player_username, card_type, target_restrictions, choice_type=None):
        if card_type == "Relic":
            target_player = self.game.players[0]
            if target_player.username != target_player_username:
                target_player = self.game.players[1]
            return target_player.display_deck_relics(target_restrictions, choice_type)
        else:
            print("can't fetch unsupported type")
            return None

    def do_add_token_effect_on_entity(self, token, target_entity_id):
        target_card, target_player = self.game.get_in_play_for_id(target_entity_id)
        if token.multiplier and token.multiplier == "half_self_entities":
            for x in range(0, math.floor(len(self.in_play)/2)):
                target_card.tokens.append(token)
        else:
            target_card.tokens.append(token)
        if target_card.toughness_with_tokens() <= 0:
            self.game.send_card_to_played_pile(target_card, target_player)

    def do_add_effect_effect_on_entity(self, effect, target_entity_id):
        target_card, target_player = self.game.get_in_play_for_id(target_entity_id)  
        effect.was_added = True
        target_card.effects.append(effect)
        target_card.added_descriptions.append([effect.description])
        if effect.activate_on_add:
            # todo: make this generic if we add other added
            if effect.name == "increase_max_mana":
                self.do_increase_max_mana_effect_on_player(target_player.username, effect.amount)

    def do_add_abilities_effect_on_player(self, effect, player):
        player.added_abilities.append(effect.abilities[0])

    def do_add_abilities_effect_on_entity(self, effect, entity):
        entity.added_abilities.append(effect.abilities[0])

    def do_add_tokens_effect(self, card, e, effect_targets):
        if effect_targets[e.id]["target_type"] == "entity":
            for token in e.tokens:
                new_token = copy.deepcopy(token)
                new_token.id = card.id
                self.do_add_token_effect_on_entity(
                    new_token, 
                    effect_targets[e.id]["id"]
                )
        else:  # e.target_type == "self_entities"
            for token in e.tokens:
                new_token = copy.deepcopy(token)
                new_token.id = card.id
                for entity in self.in_play:
                    self.do_add_token_effect_on_entity(
                        new_token, 
                        entity.id
                    )

    def do_remove_tokens_effect(self, card, e):
        if e.target_type == "self_entities":
            for entity in self.in_play:
                tokens_to_keep = []
                for token in entity.tokens:
                    if token.id != card.id:
                        tokens_to_keep.append(token)
                entity.tokens = tokens_to_keep

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
        elif e.target_type == "entity":
            self.do_add_abilities_effect_on_entity(
                e, 
                card
            )
        elif e.target_type == "opponent":
            self.do_add_abilities_effect_on_player(
                e, 
                self.game.opponent()
            )
        elif e.target_type == "self":
            self.do_add_abilities_effect_on_player(
                e, 
                self
            )

    def do_make_token_effect(self, e):
        for x in range(0, e.amount):
            if len(self.in_play) == 7:
                return
            token_card = {
                "id": self.game.next_card_id,
                "power": e.power,
                "toughness": e.toughness,
                "name": e.card_name,
                "abilities": [a.as_dict() for a in e.abilities],
                "turn_played": self.game.turn,
                "is_token": True
            }
            self.in_play.append(Card(token_card))
            self.game.update_for_entity_changes_zones(self)
            self.game.next_card_id += 1

    def do_make_random_townie_effect(self, amount):
        townies = []
        for c in Game.all_cards():
            for a in c.abilities:
                if a.descriptive_id == "Townie":
                    townies.append(c)
        t = random.choice(townies)
        self.add_to_deck(t.name, 1, add_to_hand=True)


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
                "description": "Spells cost 1 more",
                "global_effect": "spells_cost_more"
            }
            effects.append(Card(card_info))
            card_info = {
                "name": "Expensive Entities",
                "cost": 0,
                "card_type": "Effect",
                "description": "Entities cost 1 more",
                "global_effect": "entities_cost_more"
            }
            effects.append(Card(card_info))
            card_info = {
                "name": "Draw More",
                "cost": 0,
                "card_type": "Effect",
                "description": "Players draw an extra card on their turn.",
                "global_effect": "draw_extra_card"
            }
            effects.append(Card(card_info))
            card_info = {
                "name": "Cheap Spells",
                "cost": 0,
                "card_type": "Effect",
                "description": "Spells cost 1 less",
                "global_effect": "spells_cost_less"
            }
            effects.append(Card(card_info))
            card_info = {
                "name": "Cheap Entities",
                "cost": 0,
                "card_type": "Effect",
                "description": "Entities cost 1 less",
                "global_effect": "entities_cost_less"
            }
            effects.append(Card(card_info))
            self.card_choice_info["cards"] = effects
            self.card_choice_info["choice_type"] = "make"
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
        self.card_choice_info = {"cards": [card1, card2, card3], "choice_type": "make"}

    def display_deck_relics(self, target_restrictions, choice_type):
        all_cards = Game.all_cards()
        relics = []
        for card in self.deck:
            if card.card_type == "Relic":
                if len(target_restrictions) == 0 or \
                    (list(target_restrictions[0].keys())[0] == "needs_weapon" and card.has_ability("Weapon")) or \
                    (list(target_restrictions[0].keys())[0] == "needs_instrument" and card.has_ability("Instrument")):
                    relics.append(card)
        self.card_choice_info = {"cards": relics, "choice_type": choice_type}

    def relic_in_play(self, card_id):
        for card in self.relics:
            if card.id == card_id:
                return card
        return None

    def can_activate_relic(self, card_id):
        for card in self.relics:
            if card.id == card_id:
                if not card.can_activate_abilities:
                    return False
        return True

    def in_play_card(self, card_id):
        for card in self.in_play:
            if card.id == card_id:
                return card
        return None

    def in_hand_card(self, card_id):
        for card in self.hand:
            if card.id == card_id:
                return card
        return None

    def in_play_entity_is_selected(self, card_id):
        for c in self.in_play:
            if c.id == card_id and c.id == self.card_info_to_resolve["card_id"]:
                return True
        return False

    def can_select_for_attack(self, card_id):
        for card in self.in_play:
            if card.id == card_id:
                if card.attacked:
                    return False
                if self.game.power_with_tokens(card, self) <= 0:
                    return False
                for t in card.tokens:
                    if t.set_can_act == False:
                        return False                        
                if card.turn_played == self.game.turn:
                    if card.has_ability("Fast"):
                        return True
                    if card.has_ability("Ambush"):
                        for card in self.game.opponent().in_play:
                            if not card.has_ability("Lurker"):
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

        self.reset_card_info_to_resolve()
        self.hand.remove(card)
        self.mana -= card.cost

        for e in self.in_play:
            for effect in e.effects_triggered():
                if effect.trigger == "friendly_card_played" and effect.target_type == "self":
                    self.do_add_tokens_effect(e, effect, {effect.id: {"id": e.id, "target_type":"entity"}})

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
            for c in self.in_play:
                if len(c.effects_triggered()) > 0:
                    if c.effects_triggered()[0].trigger == "play_friendly_entity":
                        if c.effects_triggered()[0].name == "damage" and c.effects_triggered()[0].target_type == "opponents_entity_random":
                            if len(self.game.opponent().in_play) > 0:
                                entity = random.choice(self.game.opponent().in_play)
                                if entity.shielded:
                                    entity.shielded = False
                                else:
                                    entity.damage += c.effects_triggered()[0].amount
                                    entity.damage_this_turn += c.effects_triggered()[0].amount
                                    if entity.damage >= entity.toughness_with_tokens():
                                        self.game.send_card_to_played_pile(entity, self.game.opponent())
                                message["log_lines"].append(f"{c.name} deal {c.effects_triggered()[0].amount} damage to {entity.name}.")

            self.in_play.append(card)
            print(f"update_for_entity_changes_zones {card.name}")
            self.game.update_for_entity_changes_zones(self)

            if self.fast_ability():
                card.added_abilities.append(self.fast_ability())          
            card.turn_played = self.game.turn

        elif card.card_type == "Relic":
            self.relics.append(card)
            card.turn_played = self.game.turn
        else:
            self.played_pile.append(card)            

        if card.card_type == "Entity" and card.has_ability("Shield"):
            card.shielded = True

        if len(card.effects) > 0:
            if card.card_type == "Entity":
                self.target_or_do_entity_effects(card, message, message["username"])
            else:
                if not "effect_targets" in message:
                    message["effect_targets"]  = {}
                for e in card.effects_spell() + card.effects_enter_play():
                    if e.target_type == "self":           
                        message["effect_targets"][e.id] = {"id": message["username"], "target_type":"player"}
                    elif e.target_type == "opponent":           
                        message["effect_targets"][e.id] = {"id": self.game.opponent().username, "target_type":"player"}
                    elif e.target_type == "all_players" or e.target_type == "all_entities" or e.target_type == "self_entities":           
                        message["effect_targets"][e.id] = {"target_type": e.target_type};
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

    def cant_die_ability(self):
        for a in self.added_abilities:
            if a.descriptive_id == "Can't Die":
                return a
        return None 

    def target_or_do_entity_effects(self, card, message, username, is_activated_effect=False):
        effects = card.effects_enter_play()
        if is_activated_effect:
            effects = card.effects_activated()

        if len(effects) > 0:
            if effects[0].target_type == "any":
                self.card_info_to_resolve["card_id"] = card.id
                if is_activated_effect:
                    self.card_info_to_resolve["effect_type"] = "entity_activated"
                else:
                    self.card_info_to_resolve["effect_type"] = "entity_comes_into_play"
            elif effects[0].target_type in ["entity", "opponents_entity"]:
                if self.game.has_targets_for_entity_effect(effects[0].target_restrictions):
                    self.card_info_to_resolve["card_id"] = card.id
                    if is_activated_effect:
                        self.card_info_to_resolve["effect_type"] = "entity_activated"
                    else:
                        self.card_info_to_resolve["effect_type"] = "entity_comes_into_play"
            else:
                for e in effects:
                    if not "effect_targets" in message:
                        effect_targets = {}
                        if e.target_type == "self" or e.name == "fetch_card":           
                            effect_targets[effects[0].id] = {"id": username, "target_type":"player"};
                        message["effect_targets"] = effect_targets
                    message = self.do_card_effect(card, e, message, message["effect_targets"])
        return message

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
        
        self.reset_card_info_to_resolve()
        return message

    def modify_new_card(self, game, card):
        if card.card_type == "Spell":            
            if 'spells_cost_more' in game.global_effects:
                card.cost += game.global_effects.count('spells_cost_more')
            if 'spells_cost_less' in game.global_effects:
                card.cost -= game.global_effects.count('spells_cost_less')
                card.cost = max(0, card.cost)
        elif card.card_type == "Entity":            
            if 'entities_cost_more' in game.global_effects:
                card.cost += game.global_effects.count('entities_cost_more')
            if 'entities_cost_less' in game.global_effects:
                card.cost -= game.global_effects.count('entities_cost_less')
                card.cost = max(0, card.cost)
            if 'entities_get_more_toughness' in game.global_effects:
                card.toughness += game.global_effects.count('entities_get_more_toughness')*2
            if 'entities_get_less_toughness' in game.global_effects:
                card.toughness -= game.global_effects.count('entities_get_less_toughness')*2
                card.toughness = max(0, card.toughness)
            if 'entities_get_more_power' in game.global_effects:
                card.power += game.global_effects.count('entities_get_more_power')*2
            if 'entities_get_less_power' in game.global_effects:
                card.power -= game.global_effects.count('entities_get_less_power')*2
                card.power = max(0, card.power)
        return card

    def start_turn(self, message):
        if self.game.turn != 0:
            self.draw(1 + self.game.global_effects.count("draw_extra_card"))
        self.max_mana += 1
        self.mana = self.max_mana

        if self.card_info_to_resolve["card_id"]:
            self.reset_card_info_to_resolve()

        for card in self.in_play:
            if card.has_ability("Fade"):
                token = {
                    "turns": -1,
                    "power_modifier": -1,
                    "toughness_modifier": -1
                }
                self.do_add_token_effect_on_entity(CardToken(token), card.id)

            if not self.game.is_under_ice_prison():
                card.attacked = False
            card.can_activate_abilities = True
        for r in self.relics:
            r.can_activate_abilities = True
            for effect in r.effects_triggered():
                if effect.name == "gain_hp_for_hand":
                    gained = 0
                    to_apply = len(self.hand)
                    while self.hit_points < 30 and to_apply > 0:
                        self.hit_points += 1
                        to_apply -= 1
                        gained += 1  
                    message["log_lines"].append(f"{message['username']} gains {gained} hit points from {r.name}.")
                elif effect.name == "lose_hp_for_hand":
                    self.game.opponent().damage(len(self.game.opponent().hand))
                    message["log_lines"].append(f"{self.game.opponent().username} takes {len(self.game.opponent().hand)} damage from {r.name}.")

        if self.game.is_under_ice_prison():
            entities_to_select_from = []
            for e in self.in_play:
                if e.attacked:
                    entities_to_select_from.append(e)
            if len(entities_to_select_from) > 0:
                self.card_choice_info = {"cards": entities_to_select_from, "choice_type": "select_entity_for_ice_prison"}
        return message

    def controls_relic(self, card_id):
        for c in self.relics:
            if c.id == card_id:
                return True
        return False

    def controls_entity(self, card_id):
        for c in self.in_play:
            if c.id == card_id:
                return True
        return False

    def select_relic(self, card_id):
        for c in self.relics:
            if c.id == card_id:
                self.card_info_to_resolve["card_id"] = c.id
                self.card_info_to_resolve["effect_type"] = "relic_activated"

    def selected_relic(self):
        for relic in self.relics:
            if relic.id == self.card_info_to_resolve["card_id"]:
                return relic

    def selected_entity(self):
        for entity in self.in_play:
            if entity.id == self.card_info_to_resolve["card_id"]:
                return entity

    def selected_spell(self):
        for card in self.hand:
            if card.id == self.card_info_to_resolve["card_id"]:
                return card

    def select_in_play(self, card_id):
        for c in self.in_play:
            if c.id == card_id:
                self.card_info_to_resolve["card_id"] = c.id
                self.card_info_to_resolve["effect_type"] = "entity_at_ready"

    def has_guard(self):
        for c in self.in_play:
            if c.has_ability("Guard"):
                return True
        return False

    def can_summon(self):
        for a in self.added_abilities:
            if a.descriptive_id == "Can't Summon":
                return False
        if len(self.in_play) == 7:
            return False
        return True

    def can_play_relic(self):
        if len(self.relics) == 3:
            return False
        return True

    def set_targets_for_selected_entity(self):
        # todo relics?
        target_type = None
        target_restrictions = None
        card = self.selected_entity()
        if self.card_info_to_resolve["effect_type"] == "entity_comes_into_play":
                target_type = card.effects[0].target_type
                target_restrictions = card.effects[0].target_restrictions
        elif self.card_info_to_resolve["effect_type"] == "entity_activated":
            target_type = card.effects_activated()[0].target_type
            target_restrictions = card.effects_activated()[0].target_restrictions
        self.game.set_targets_for_target_type(target_type, target_restrictions)

    def reset_card_info_to_resolve(self):
        self.card_info_to_resolve = {"card_id": None, "effect_type": None}

    def reset_card_choice_info(self):
        self.card_choice_info = {"cards": [], "choice_type": None}

    def do_attack_abilities(self, attacking_card):
        if attacking_card.has_ability("Syphon"):
            ability = None
            for a in attacking_card.abilities:
                if a.descriptive_id == "DamageDraw":
                    ability = a
            if ability.target_type == "opponent":
                self.game.opponent().draw(ability.amount)
            else:
                self.draw(ability.amount)
        #todo syphon ignores Shield and Armor
        if attacking_card.has_ability("Syphon"):
            self.hit_points += self.game.power_with_tokens(attacking_card, self)
            self.hit_points = min(30, self.hit_points)
        if attacking_card.has_ability("discard_random"):
            ability = None
            for a in attacking_card.abilities:
                if a.descriptive_id == "discard_random":
                    ability = a
            self.do_discard_random_effect_on_player(attacking_card, self.game.opponent().username, ability.amount)
        if attacking_card.has_ability("discard_random_to_deck"):
            ability = None
            for a in attacking_card.abilities:
                if a.descriptive_id == "discard_random_to_deck":
                    ability = a
            self.do_discard_random_effect_on_player(attacking_card, self.game.opponent().username, ability.amount, to_deck=True)


class Card:

    def __init__(self, info):
        self.added_descriptions = info["added_descriptions"] if "added_descriptions" in info else []
        self.attacked = info["attacked"] if "attacked" in info else False
        self.can_activate_abilities = info["can_activate_abilities"] if "can_activate_abilities" in info else True
        self.can_be_clicked = info["can_be_clicked"] if "can_be_clicked" in info else False
        self.card_type = info["card_type"] if "card_type" in info else "Entity"
        self.cost = info["cost"] if "cost" in info else 0
        self.damage = info["damage"] if "damage" in info else 0
        self.damage_this_turn = info["damage_this_turn"] if "damage_this_turn" in info else 0
        self.description = info["description"] if "description" in info else None
        self.global_effect = info["global_effect"] if "global_effect" in info else None
        self.id = info["id"] if "id" in info else -1
        self.is_token = info["is_token"] if "is_token" in info else False
        self.name = info["name"]
        # probably bugs WRT Mind Manacles
        self.owner_username = info["owner_username"] if "owner_username" in info else None
        self.power = info["power"] if "power" in info else None
        self.race = info["race"] if "race" in info else None
        self.shielded = info["shielded"] if "shielded" in info else False
        self.toughness = info["toughness"] if "toughness" in info else None
        self.turn_played = info["turn_played"] if "turn_played" in info else -1

        self.abilities = [CardAbility(a, idx) for idx, a in enumerate(info["abilities"])] if "abilities" in info and info["abilities"] else []
        self.added_abilities = [CardAbility(a, idx) for idx, a in enumerate(info["added_abilities"])] if "added_abilities" in info and info["added_abilities"] else []
        self.effects = [CardEffect(e, idx) for idx, e in enumerate(info["effects"])] if "effects" in info else []
        self.tokens = [CardToken(t) for t in info["tokens"]] if "tokens" in info else []

    def __repr__(self):
        return f"{self.name} ({self.race}, {self.cost}) - {self.power}/{self.toughness}\n \
                 description: {self.description}\n \
                 added_descriptions: {self.added_descriptions}\n \
                 card_type: {self.card_type}\n \
                 effects: {self.effects}\n \
                 damage: {self.damage}\n \
                 damage_this_turn: {self.damage_this_turn}\n \
                 can_be_clicked: {self.can_be_clicked}\n \
                 id: {self.id}, turn played: {self.turn_played}\n \
                 attacked: {self.attacked}\n \
                 owner_username: {self.owner_username} \n \
                 abilities: {self.abilities}, tokens: {self.tokens}\n \
                 can_activate_abilities: {self.can_activate_abilities})\n \
                 is_token: {self.is_token} shielded: {self.shielded}"
 

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "race": self.race,
            "power": self.power,
            "toughness": self.toughness,
            "cost": self.cost,
            "damage_this_turn": self.damage_this_turn,
            "damage": self.damage,
            "turn_played": self.turn_played,
            "card_type": self.card_type,
            "description": self.description,
            "added_descriptions": self.added_descriptions,
            "effects": [e.as_dict() for e in self.effects],
            "global_effect": self.global_effect,
            "attacked": self.attacked,
            "can_be_clicked": self.can_be_clicked,
            "can_activate_abilities": self.can_activate_abilities,
            "owner_username": self.owner_username,
            "is_token": self.is_token,
            "shielded": self.shielded,
            "abilities": [a.as_dict() for a in self.abilities],
            "added_abilities": [a.as_dict() for a in self.added_abilities],
            "tokens": [t.as_dict() for t in self.tokens] if self.tokens else []
        }

    def enabled_activated_effects(self):
        enabled_effects = []
        for e in self.effects_activated():
            if e.enabled:
               enabled_effects.append(e)
        return enabled_effects

    def deactivate_weapon(self):
        # todo: don't hardcode for dagger
        first_activated_effect = None
        for a in self.effects:
            if a.effect_type == "activated" and a.was_added == True:
                self.effects.remove(a)
                break
        for a in self.effects:
            if a.effect_type == "activated":
                a.enabled = True
                break
        self.description = "✦✦: Make this a 1 power weapon with 2 charges."
        self.can_activate_abilities = True        

    def deactivate_instrument(self):
        # todo: don't hardcode for Lute
        first_activated_effect = None
        for a in self.effects:
            if a.effect_type == "activated" and a.was_added == True:
                self.effects.remove(a)
                break
        for a in self.effects:
            if a.effect_type == "activated":
                a.enabled = True
                break
        self.description = "✦✦: Make this an instrument with 2 charges that fetches Townies."
        self.can_activate_abilities = True        

    def needs_activated_effect_targets(self):
        for e in self.enabled_activated_effects():
            if e.target_type == "any" or e.target_type == "any_enemy" or e.target_type == "entity" or e.target_type == "opponents_entity":
                return True
        return False 

    def needs_targets(self):
        for e in self.effects:
            if e.target_type == "any" or e.target_type == "any_enemy" or e.target_type == "entity" or e.target_type == "opponents_entity" or e.target_type == "relic" or e.target_type == "any_player":
                return True
        return False 

    def needs_entity_target(self):
        for e in self.effects:
            if e.target_type == "entity" or e.target_type == "opponents_entity":
                return True
        return False

    def can_target_entities(self):
        for e in self.effects:
            if e.target_type == "entity" or e.target_type == "opponents_entity" or e.target_type == "any_enemy" or e.target_type == "any":
                return True
        return False

    def needs_relic_target(self):
        for e in self.effects:
            if e.target_type == "relic":
                return True
        return False

    def needs_entity_target_for_activated_effect(self):
        for e in self.enabled_activated_effects():
            if e.target_type == "entity" or e.target_type == "opponents_entity":
                return True
        return False

    def needs_target_for_activated_effect(self):
        for e in self.enabled_activated_effects():
            # todo: Relic target_type because of fetch_card, maybe refactor:
            if e.target_type == "self" or e.target_type == "opponent" or e.target_type == "Relic": 
                return False
        return True

    def needs_card_being_cast_target(self):
        for e in self.effects:
            if e.target_type == "card_being_cast":
                return True
        return False

    def toughness_with_tokens(self):
        toughness = self.toughness
        for t in self.tokens:
            toughness += t.toughness_modifier
        return toughness

    def has_ability(self, ability_name):
        for a in self.abilities:
            if a.descriptive_id == ability_name and a.enabled:
                return True
        for a in self.added_abilities:
            if a.descriptive_id == ability_name and a.enabled:
                return True
        return False

    def effect_with_trigger(self, trigger_name):
        for e in self.effects_triggered():
            if e.trigger == trigger_name:
                return e
        return None

    def do_leaves_play_effects(self, player):
        for e in self.effects_leave_play():
            if e.name == "decrease_max_mana":
                player.max_mana -= e.amount
                player.mana = min(player.max_mana, player.mana)
            if e.name == "damage" and e.target_type == "opponent":
                player.game.opponent().damage(e.amount)                                
            if e.name == "damage" and e.target_type == "self":
                player.damage(e.amount)                
            if e.name == "make_token":
                player.do_make_token_effect(e)
            if e.name == "remove_tokens":
                player.do_remove_tokens_effect(self, e)

    def effects_leave_play(self):
        return [e for e in self.effects if e.effect_type == "leave_play"]

    def effects_enter_play(self):
        return [e for e in self.effects if e.effect_type == "enter_play"]

    def effects_activated(self):
        return [e for e in self.effects if e.effect_type == "activated"]

    def effects_triggered(self):
        return [e for e in self.effects if e.effect_type == "triggered"]

    def effects_spell(self):
        return [e for e in self.effects if e.effect_type == "spell"]

    def effects_added(self):
        return [e for e in self.effects if e.was_added == True]

    def effects_enabled(self):
        return [e for e in self.effects if e.enabled == True]

    def effect_for_id(self, effect_id):
        for e in self.effects:
            if e.id == effect_id:
                return e


class CardEffect:
    def __init__(self, info, effect_id):
        self.abilities = [CardAbility(a, idx) for idx, a in enumerate(info["abilities"])] if "abilities" in info else []
        self.activate_on_add = info["activate_on_add"] if "activate_on_add" in info else False
        self.amount = info["amount"] if "amount" in info else None
        self.card_name = info["card_name"] if "card_name" in info else None
        self.counters = info["counters"] if "counters" in info else 0
        self.cost = info["cost"] if "cost" in info else 0
        self.cost_hp = info["cost_hp"] if "cost_hp" in info else 0
        self.description = info["description"] if "description" in info else None
        self.effects = [CardEffect(e, idx) for idx, e in enumerate(info["effects"])] if "effects" in info else []
        self.effect_to_activate = CardEffect(info["effect_to_activate"], 0) if "effect_to_activate" in info and info["effect_to_activate"] else None
        self.effect_type = info["effect_type"] if "effect_type" in info else None
        self.enabled = info["enabled"] if "enabled" in info else True
        self.id = effect_id
        self.make_type = info["make_type"] if "make_type" in info else None
        self.name = info["name"]
        self.power = info["power"] if "power" in info else None
        self.sacrifice_on_activate = info["sacrifice_on_activate"] if "sacrifice_on_activate" in info else False
        self.target_restrictions = info["target_restrictions"] if "target_restrictions" in info else []
        self.target_type = info["target_type"] if "target_type" in info else None
        self.tokens = [CardToken(t) for t in info["tokens"]] if "tokens" in info else []
        self.toughness = info["toughness"] if "toughness" in info else None
        self.trigger = info["trigger"] if "trigger" in info else None
        self.was_added = info["was_added"] if "was_added" in info else False

    def __repr__(self):
        return f"\
            id: {self.id} name: {self.name} power: {self.power} target_restrictions: \
            {self.target_restrictions} trigger: {self.trigger} toughness: {self.toughness} \
            amount: {self.amount} cost: {self.cost}\n \
            description: {self.description} cost_hp: {self.cost_hp} \
            target_type: {self.target_type} name: {self.card_name} \n \
            make_type: {self.make_type} tokens: {self.tokens} was_added: {self.was_added} \
            sacrifice_on_activate: {self.sacrifice_on_activate} abilities: {self.abilities}\n \
            effect_type: {self.effect_type} effects: {self.effects} activate_on_add: {self.activate_on_add} \
            effect_to_activate: {self.effect_to_activate} enabled: {self.enabled} counters: {self.counters}"

    def as_dict(self):
        return {
            "abilities": [a.as_dict() for a in self.abilities] if self.abilities else [],
            "activate_on_add": self.activate_on_add,
            "amount": self.amount,
            "card_name": self.card_name,
            "counters": self.counters,
            "cost": self.cost,
            "cost_hp": self.cost_hp,
            "description": self.description,
            "effects": [e.as_dict() for e in self.effects] if self.effects else [],
            "effect_to_activate": self.effect_to_activate.as_dict() if self.effect_to_activate else None,
            "effect_type": self.effect_type,
            "enabled": self.enabled,
            "id": self.id,
            "make_type": self.make_type,
            "name": self.name,
            "power": self.power,
            "sacrifice_on_activate": self.sacrifice_on_activate,
            "target_restrictions": self.target_restrictions,
            "target_type": self.target_type,
            "tokens": [t.as_dict() for t in self.tokens] if self.tokens else [],
            "toughness": self.toughness,
            "trigger": self.trigger,
            "was_added": self.was_added
        }


class CardAbility:
    def __init__(self, info, ability_id):
        self.amount = info["amount"] if "amount" in info else None
        self.descriptive_id = info["descriptive_id"] if "descriptive_id" in info else None
        self.enabled = info["enabled"] if "enabled" in info else True
        self.id = ability_id
        self.name = info["name"] if "name" in info else None
        self.target_type = info["target_type"] if "target_type" in info else None
        self.turns = info["turns"] if "turns" in info else -1

    def __repr__(self):
        return f"self.id: {self.id} self.name: {self.name} self.amount: {self.amount} self.target_type: {self.target_type}\n\
                self.descriptive_id: {self.descriptive_id} self.turns: {self.turns} self.enabled: {self.enabled}"

    def as_dict(self):
        return {
            "amount": self.amount,
            "descriptive_id": self.descriptive_id,
            "enabled": self.enabled,
            "id": self.id,
            "name": self.name,
            "target_type": self.target_type,
            "turns": self.turns,
        }


class CardToken:
    def __init__(self, info):
        self.power_modifier = info["power_modifier"] if "power_modifier" in info else 0
        self.set_can_act = info["set_can_act"] if "set_can_act" in info else None
        self.toughness_modifier = info["toughness_modifier"] if "toughness_modifier" in info else 0
        self.turns = info["turns"] if "turns" in info else -1
        self.multiplier = info["multiplier"] if "multiplier" in info else 0
        self.id = info["id"] if "id" in info else None

    def __repr__(self):
        if self.set_can_act is not None:
            return "Can't Attack"
        return f"+{self.power_modifier}/+{self.toughness_modifier}"

    def as_dict(self):
        return {
            "power_modifier": self.power_modifier,
            "set_can_act": self.set_can_act,
            "toughness_modifier": self.toughness_modifier,
            "turns": self.turns,
            "multiplier": self.multiplier,
            "id": self.id,
        }
