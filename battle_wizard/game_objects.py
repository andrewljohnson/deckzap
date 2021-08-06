import ast
import copy
import datetime
import math
import random
import time

from battle_wizard.data import default_deck_genie_wizard, default_deck_dwarf_tinkerer
from battle_wizard.jsonDB import JsonDB


class Game:
    def __init__(self, websocket_consumer, ai_type, db_name, game_type, info=None, player_decks=None, ai=None, hs_style=True):

        # constructed or test_stacked_deck
        self.game_type = game_type

        self.ai = ai
        self.ai_type = info["ai_type"] if info and "ai_type" in info else ai_type

        # support 2 players
        self.players = [Player(self, u) for u in info["players"]] if info else []
        self.turn = int(info["turn"]) if info else 0

        # player 0 always acts on even turns, player 1 acts on odd turns
        self.actor_turn = int(info["actor_turn"]) if info else 0

        self.defending_player = Player(self, info["defending_player"]) if info and info["defending_player"] else None
        self.move_to_complete = info["move_to_complete"] if info and "move_to_complete" in info else None
        self.spell_stack = info["spell_stack"] if info and "spell_stack" in info else []

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

        self.turn_start_time = datetime.datetime.strptime(info["turn_start_time"], "%Y-%m-%d %H:%M:%S.%f") if (info and "turn_start_time" in info and info["turn_start_time"] != None) else datetime.datetime.now()
        self.show_rope = info["show_rope"] if info else False

        self.max_max_mana = 5
        self.max_hand_size = 5
        self.cards_each_turn = 5
        self.initial_hand_size = 5
        self.discard_end_of_turn = True
        self.keep_excess_mana = True

        if hs_style:
            self.max_max_mana = 10
            self.max_hand_size = 10
            self.cards_each_turn = 1
            self.initial_hand_size = 4
            self.discard_end_of_turn = False
            self.keep_excess_mana = False

    def as_dict(self):
        return {
            "players": [p.as_dict() for p in self.players], 
            "defending_player": self.defending_player.as_dict() if self.defending_player else None, 
            "move_to_complete": self.move_to_complete, 
            "spell_stack": self.spell_stack, 
            "turn": self.turn, 
            "actor_turn": self.actor_turn, 
            "next_card_id": self.next_card_id, 
            "global_effects": self.global_effects, 
            "db_name": self.db_name, 
            "ai_type": self.ai_type, 
            "turn_start_time": self.turn_start_time.__str__() if self.turn_start_time else None, 
            "show_rope": self.show_rope, 
        }

    @staticmethod
    def all_cards():
        """
            Returns a list of all possible cards in the game. 
        """
        return [Card(c_info) for c_info in JsonDB().all_cards()]

    def current_player(self):
        return self.players[self.actor_turn % 2]

    def opponent(self):
        return self.players[(self.actor_turn + 1) % 2]

    def legal_moves_for_ai(self, player):
        """
            Returns a list of possible moves for an AI player.
        """
        if len(self.players) < 2:
            return [{"move_type": "JOIN", "username": self.ai}]
        moves = []
        if len(self.spell_stack) > 0:
            moves = self.add_spell_response_moves(player, moves)
        elif self.defending_player:
            moves = self.add_attack_response_moves(player, moves)
        elif player.card_info_to_target["effect_type"] in ["mob_activated", "mob_comes_into_play"]:
            moves = self.add_resolve_mob_effects_moves(player, moves)
        elif player.card_choice_info["choice_type"] == "make":
            moves = self.add_resolve_make_moves(player, moves)
        elif player.card_choice_info["choice_type"] == "make_from_deck":
            moves = self.add_resolve_make_from_deck_moves(player, moves)
        elif player.card_choice_info["choice_type"] == "fetch_artifact_into_hand":
            moves = self.add_resolve_fetch_card_moves(player, moves)
        elif player.card_choice_info["choice_type"] == "riffle":
            moves = self.add_resolve_riffle_moves(player, moves)
        elif player.card_choice_info["choice_type"] == "fetch_artifact_into_play":
            moves = self.add_resolve_fetch_artifact_into_play_moves(player, moves)
        elif player.card_choice_info["choice_type"] == "fetch_into_hand":
            moves = self.add_resolve_fetch_card_moves(player, moves)
        elif player.card_choice_info["choice_type"] == "select_mob_for_ice_prison":
            moves = self.add_select_mob_for_ice_prison_moves(moves)
            if len(moves) == 0:
                moves = self.add_attack_and_play_card_moves(moves)
                moves.append({"move_type": "END_TURN", "username": self.ai})                
        elif player.card_choice_info["choice_type"] == "view_hand":
            moves.append({
                "move_type": "HIDE_REVEALED_CARDS", 
                "username": self.ai})
        else:
            print("GETS TO ELSE - legal_moves_for_ai")
            print(player.selected_mob())
            print(player.selected_artifact())
            print(player.selected_spell())
            moves = self.add_attack_and_play_card_moves(moves)
            if not player.selected_mob() and not player.selected_artifact() and not player.selected_spell():
                moves.append({"move_type": "END_TURN", "username": self.ai})

        print("legal moves for AI: " + str(moves))
        return moves

    def add_spell_response_moves(self, player, moves):
        moves = self.add_attack_and_play_card_moves(moves)
        moves.append({"move_type": "RESOLVE_CARD", "username": self.ai})              
        return moves 

    def add_attack_response_moves(self, player, moves):
        moves = self.add_attack_and_play_card_moves(moves)
        moves.append({"move_type": "ALLOW_ATTACK", "username": self.ai})              
        return moves 

    def add_effect_resolve_move(self, mob_to_target, effect_target, effect_type, moves):
        # todo handle cards with more than one effect that gets triggered at the same time
        moves.append({
                "card":mob_to_target.id, 
                "move_type": "RESOLVE_MOB_EFFECT", 
                "effect_index": 0, 
                "username": self.ai,
                "effect_targets": [effect_target]})

        if len(mob_to_target.effects) == 2:
            if mob_to_target.effects[1].target_type == "mob" or mob_to_target.effects[1].target_type == "opponents_mob":
                # hack for animal trainer
                moves[-1]["effect_targets"].append({"id": effect_target["id"], "target_type":"mob"})            
            else:
                # hack for siz pop and stiff wind
                moves[-1]["effect_targets"].append({"id": self.ai, "target_type":"player"})
        return moves

    def add_select_mob_for_ice_prison_moves(self, moves):
        for card in self.current_player().in_play:
            if card.can_be_clicked:
                moves.append({"card":card.id , "move_type": "SELECT_MOB", "username": self.ai})
        return moves

    def add_resolve_mob_effects_moves(self, player, moves):
        mob_to_target = self.current_player().selected_mob()
        effect_type = self.current_player().card_info_to_target["effect_type"]
        for card in self.opponent().in_play + self.current_player().in_play:
            if card.can_be_clicked and mob_to_target.id != card.id:
                effect_target = {"id": card.id, "target_type":"mob"}
                moves = self.add_effect_resolve_move(mob_to_target, effect_target, effect_type, moves)
        for p in self.players:
            if p.can_be_clicked:
                effect_target = {"id": p.username, "target_type":"player"}
                moves = self.add_effect_resolve_move(mob_to_target, effect_target, effect_type, moves)
        return moves 

    def add_resolve_make_moves(self, player, moves):
        move_type = "MAKE_CARD"
        if player.card_choice_info["cards"][0].card_type == "Effect":
            move_type = "MAKE_EFFECT"
        for x in range(0,3):
            moves.append({"card":player.card_choice_info["cards"][x].as_dict() , "move_type": move_type, "username": self.ai})              
        return moves 

    def add_resolve_fetch_card_moves(self, player, moves):
        for c in player.card_choice_info["cards"]:
            moves.append({"card":c.id , "move_type": "FETCH_CARD", "username": self.ai})              
        return moves 

    def add_resolve_make_from_deck_moves(self, player, moves):
        for c in player.card_choice_info["cards"]:
            moves.append({"card":c.id , "move_type": "FETCH_CARD", "username": self.ai})              
        return moves 

    def add_resolve_riffle_moves(self, player, moves):
        for c in player.card_choice_info["cards"]:
            moves.append({"card":c.id, "move_type": "FINISH_RIFFLE", "username": self.ai})              
        return moves 

    def add_resolve_fetch_artifact_into_play_moves(self, player, moves):
        for c in player.card_choice_info["cards"]:
            moves.append({"card":c.id , "move_type": "FETCH_CARD_INTO_PLAY", "username": self.ai})              
        return moves 

    def add_attack_and_play_card_moves(self, moves):
        for spell in self.spell_stack:
            card = Card(spell[1])
            if card.can_be_clicked:
                moves.append({"card":card.id, "move_type": "SELECT_STACK_SPELL", "username": self.ai})
        for artifact in self.current_player().artifacts:
            if artifact.can_be_clicked:
                moves.append({"card":artifact.id, "move_type": "SELECT_ARTIFACT", "username": self.ai, "effect_index": 0})
        for artifact in self.opponent().artifacts:
            if artifact.can_be_clicked:
                moves.append({"card":artifact.id, "move_type": "SELECT_ARTIFACT", "username": self.ai, "effect_index": 0})
        for artifact in self.current_player().artifacts:
            for idx, e in enumerate(artifact.enabled_activated_effects()):                
                if len(artifact.effects_can_be_clicked) > idx and artifact.effects_can_be_clicked[idx]:
                    moves.append({"card":artifact.id , "move_type": "SELECT_ARTIFACT", "username": self.ai, "effect_index": idx})
        for mob in self.current_player().in_play:
            if mob.can_be_clicked:
                moves.append({"card":mob.id , "move_type": "SELECT_MOB", "username": self.ai})
            # todo: don't hardcode for Infernus
            if len(mob.effects_activated()) > 0 and \
                mob.effects_activated()[0].target_type == "this" and \
                mob.effects_activated()[0].cost <= self.current_player().current_mana():
                # todo maybe entities will have multiple effects
                moves.append({"card":mob.id, "move_type": "ACTIVATE_MOB", "username": self.ai, "effect_index": 0})
            elif len(mob.effects_activated()) > 0 and \
                mob.effects_activated()[0].cost <= self.current_player().current_mana():
                # todo maybe entities will have multiple effects, only have Winding One right now
                moves.append({"card":mob.id, "move_type": "ACTIVATE_MOB", "username": self.ai, "effect_index": 0})
        for mob in self.opponent().in_play:
            if mob.can_be_clicked:
                moves.append({"card":mob.id , "move_type": "SELECT_MOB", "username": self.ai})
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
        if message["move_type"] != "GET_TIME":
            print(f"MOVE: {move_type}")
        
        if move_type == 'GET_TIME':
            max_turn_time = 60
            turn_time = datetime.datetime.now() - self.turn_start_time
            
            message["turn_time"] = turn_time.seconds
            message["max_turn_time"] = max_turn_time
            return message

        if move_type != 'JOIN':
            self.unset_clickables(move_type)

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
        # moves sent by the game UX via buttons and card clicks
        elif move_type == 'END_TURN':
            message = self.end_turn(message)
        elif move_type == 'SELECT_CARD_IN_HAND':
            message = self.select_card_in_hand(message)
        elif move_type == 'SELECT_ARTIFACT':
            message = self.select_artifact(message)
        elif move_type == 'SELECT_STACK_SPELL':
            message = self.select_stack_spell(message)
        elif move_type == 'SELECT_MOB':
            message = self.select_mob(message)
        elif move_type == 'SELECT_OPPONENT' or move_type == 'SELECT_SELF':
            message = self.select_player(move_type, message)
        # moves where players choose from a list of cards
        elif move_type == 'MAKE_CARD':
            self.make_card(message)
        elif move_type == 'MAKE_EFFECT':
            message = self.make_effect(message)        
        elif move_type == 'FETCH_CARD':
            message = self.fetch_card(message, "Artifact")        
        elif move_type == 'FETCH_CARD_INTO_PLAY':
            message = self.fetch_card(message, "Artifact", into_play=True)        
        elif move_type == 'FINISH_RIFFLE':
            message = self.finish_riffle(message)        
        # moves that get triggered indirectly from game UX actions (e.g. SELECT_MOB twice could be an ATTACK)
        elif move_type == 'ATTACK':
            message = self.initiate_attack(message)            
        elif move_type == 'ALLOW_ATTACK':
            message = self.attack(message)            
        elif move_type == 'ACTIVATE_ARTIFACT':
            message = self.activate_artifact(message)            
        elif move_type == 'ACTIVATE_MOB':
            message = self.activate_mob(message)            
        elif move_type == 'HIDE_REVEALED_CARDS':
            message = self.hide_revealed_cards(message)            
        elif move_type == 'PLAY_CARD':
            message = self.current_player().initiate_play_card(message["card"], message)
        elif move_type == 'RESOLVE_CARD':
            message = self.opponent().play_card(self.spell_stack[-1][0]["card"], message)
        elif move_type == 'RESOLVE_MOB_EFFECT':
            message = self.current_player().resolve_mob_effect(message["card"], message)
        elif move_type == 'UNSELECT':
             self.current_player().reset_card_info_to_target()
    
        if message:
            JsonDB().save_game_database(self.as_dict(), self.db_name)
        else:
            # if message is None, the move was a no-op, like SELECT_CARD_IN_HAND on an uncastable card
            pass

        if move_type != 'JOIN' or len(self.players) == 2:
            self.set_clickables()

        return message

    def unset_clickables(self, move_type):
        """
            unhighlight everything before highlighting possible attacks/spells
        """

        if len(self.players) != 2:
            return
        for spell in self.spell_stack:
            spell[1]["can_be_clicked"] = False
        for card in self.opponent().in_play:
            card.can_be_clicked = False
        for card in self.current_player().in_play:
            card.can_be_clicked = False
            card.effects_can_be_clicked = []
        for card in self.current_player().hand:
            card.can_be_clicked = False
            card.needs_targets = False
        for card in self.current_player().artifacts:
            card.can_be_clicked = False
            card.effects_can_be_clicked = []
        self.opponent().can_be_clicked = False
        self.current_player().can_be_clicked = False
        if move_type != "UNSELECT":
            self.opponent().damage_to_show = 0
            self.current_player().damage_to_show = 0
            for card in self.opponent().in_play + self.current_player().in_play:
                card.damage_to_show = 0


    def set_clickables(self):
        """
            highlight selectable cards for possible attacks/spells
        """

        if len(self.players) != 2:
            return
        cp = self.current_player()
        opp = self.opponent()

        # these are only clickable if certain spells are the selected_spell
        for card in opp.artifacts:
            card.can_be_clicked = False

        if cp.selected_mob() and cp.card_info_to_target["effect_type"] != "mob_at_ready":
            cp.set_targets_for_selected_mob()
        elif cp.selected_artifact():
            selected_artifact = cp.selected_artifact()
            e = selected_artifact.enabled_activated_effects()[cp.card_info_to_target["effect_index"]]
            self.set_targets_for_target_type(e.target_type, e.target_restrictions, e)
        elif cp.selected_spell():
            selected_spell = cp.selected_spell()
            if not selected_spell.needs_targets_for_spell():
                selected_spell.can_be_clicked = True 
            else:           
                for e in selected_spell.effects:
                    if cp.current_mana() >= e.cost:
                        self.set_targets_for_target_type(e.target_type, e.target_restrictions)
                        # todo handle mutliple effects if we add cards like that
                        # without this break, this code breaks on Siz Pop
                        break
        elif cp.card_info_to_target["effect_type"] in ["mob_at_ready"]:
            selected_mob = cp.selected_mob()
            if len(self.spell_stack) == 0 or selected_mob.has_ability("Superfast"):
                only_has_ambush_attack = False
                if not selected_mob.has_ability("Fast"):
                    if selected_mob.has_ability("Ambush"):
                        if selected_mob.turn_played == self.turn:
                            only_has_ambush_attack = True
                if (selected_mob.has_ability("Evade Guard") or not opp.has_guard()) and not only_has_ambush_attack:
                    selected_mob.can_be_clicked = True
                    opp.can_be_clicked = True
                for card in opp.in_play:
                    if card.has_ability("Guard") or not opp.has_guard() or selected_mob.has_ability("Evade Guard"):
                        if not card.has_ability("Lurker"):
                            card.can_be_clicked = True
        if cp.card_info_to_target["effect_type"]:
            return

        if len(cp.card_choice_info["cards"]) > 0 and cp.card_choice_info["choice_type"] in ["select_mob_for_effect", "select_mob_for_ice_prison"]:
            for c in cp.card_choice_info["cards"]:
                c.can_be_clicked = True
            return

        for card in cp.artifacts:
            card.effects_can_be_clicked = []
            for x, effect in enumerate(card.enabled_activated_effects()):
                effect_can_be_used = True
                if card.needs_and_doesnt_have_legal_attack_targets(self):
                    effect_can_be_used = False
                if card.needs_mob_target_for_activated_effect(x):
                    effect_can_be_used = False if len(cp.in_play) == 0 and len(opp.in_play) == 0 else True
                if card.needs_self_mob_target_for_activated_effect(x):
                    effect_can_be_used = False if len(cp.in_play) == 0 else True
                if effect.cost > cp.current_mana():
                    effect_can_be_used = False
                if effect.name in card.effects_exhausted:
                    effect_can_be_used = False
                card.effects_can_be_clicked.append(effect_can_be_used)      
            if len(card.effects_can_be_clicked) and card.effects_can_be_clicked[0] and len(card.effects_can_be_clicked) == 1 and card.enabled_activated_effects()[0].name not in card.effects_exhausted:
                card.can_be_clicked = True               
            else: 
                card.can_be_clicked = False               

        for card in cp.in_play:
            card.effects_can_be_clicked = []
            for x, effect in enumerate(card.enabled_activated_effects()):
                effect_can_be_used = True
                if card.needs_mob_target_for_activated_effect(x):
                    effect_can_be_used = False if len(cp.in_play) == 0 and len(opp.in_play) == 0 else True
                if card.needs_self_mob_target_for_activated_effect(x):
                    effect_can_be_used = False
                    if len(cp.in_play) > 0:
                        for mob in cp.in_play:
                            if not card.has_ability("Lurker"):
                                card.effect_can_be_used = True
                if effect.cost > cp.current_mana():
                    effect_can_be_used = False
                if effect.name in card.effects_exhausted:
                    effect_can_be_used = False
                card.effects_can_be_clicked.append(effect_can_be_used)      
            if cp.can_select_for_attack(card.id) and (card.has_ability("Superfast") or (not self.defending_player and len(self.spell_stack) == 0)):
                card.can_be_clicked = True
        for card in cp.hand:               
            card.needs_targets = card.needs_targets_for_spell()
            if cp.current_mana() >= card.cost:
                card.can_be_clicked = True
                if card.card_type == "Artifact":
                    card.can_be_clicked = len(cp.artifacts) != 3
                if card.card_type == "Spell" and card.needs_mob_target():
                    card.can_be_clicked = False
                    if len(cp.in_play + opp.in_play) > 0:
                        for mob in cp.in_play + opp.in_play:
                            if not mob.has_ability("Lurker"):
                                card.can_be_clicked = True
                if card.card_type == "Spell" and card.needs_artifact_target():
                    card.can_be_clicked = False if len(cp.artifacts) == 0 and len(opp.artifacts) == 0 else True
                if card.card_type == "Spell" and card.needs_stack_target():
                    card.can_be_clicked = card.has_stack_target(self)
                if card.card_type == "Mob" and not cp.can_summon():
                    card.can_be_clicked = False
                if card.card_type != "Spell" and (self.defending_player or len(self.spell_stack) > 0):
                    card.can_be_clicked = False
                    if card.has_ability("Superfast"):
                        card.can_be_clicked = True
                if card.name == "Mind Manacles":
                    card.can_be_clicked = False
                    for e in opp.in_play:
                        if not e.has_ability("Lurker"):
                            card.can_be_clicked = True
                if card.has_ability("Instrument Required") and not cp.has_instrument():
                    card.can_be_clicked = False


    def set_targets_for_target_type(self, target_type, target_restrictions, effect=None):
        if target_type == "any_player":
            self.set_targets_for_player_effect()
        elif target_type == "any_enemy" and effect and effect.name == "attack":
            self.set_targets_for_attack_effect(effect)
        elif target_type == "any_enemy":
            self.set_targets_for_enemy_damage_effect()
        elif target_type == "any":
            self.set_targets_for_damage_effect()
        elif target_type == "mob":
            self.set_targets_for_mob_effect(target_restrictions)
        elif target_type == "artifact":
            self.set_targets_for_artifact_effect()
        elif target_type == "opponents_mob":
            self.set_targets_for_opponents_mob_effect(target_restrictions)
        elif target_type == "self_mob":
            self.set_targets_for_self_mob_effect(target_restrictions)
        elif target_type == "being_cast_mob":
            self.set_targets_for_being_cast_mob_effect()
        elif target_type == "being_cast_spell":
            self.set_targets_for_being_cast_spell_effect()
        elif target_type == "opponent":
            self.opponent().can_be_clicked = True
        elif target_type == "self":
            self.current_player().can_be_clicked = True

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
            if not card.has_ability("Lurker"):
                card.can_be_clicked = True
        self.opponent().can_be_clicked = True

    def has_targets_for_attack_effect(self, effect):
        # todo artifacts might eventually need evade guard
        guard_entities_without_lurker = []
        clickable_ids = []
        for card in self.opponent().in_play:
            if card.has_ability("Guard") and not card.has_ability("Lurker"):
                guard_entities_without_lurker.append(card)
        if len(guard_entities_without_lurker) == 0:
            for card in self.opponent().in_play:
                if not card.has_ability("Lurker"):
                     clickable_ids.append(card.id)
            # todo this assumes card ids never clash with usernames
            clickable_ids.append(self.opponent().username)
        else:
            for card in guard_entities_without_lurker:
                clickable_ids.append(card.id)

        for info in effect.targetted_this_turn:
            if info["target_type"] == "player" and info["id"] in clickable_ids:
                clickable_ids.remove(info["id"])
            else:
                card, _ = self.get_in_play_for_id(info["id"])
                if card and card.id in clickable_ids:
                    clickable_ids.remove(card.id)
        return len(clickable_ids) > 0

    def set_targets_for_attack_effect(self, effect):
        # todo artifacts might eventually need evade guard
        guard_entities_without_lurker = []
        for card in self.opponent().in_play:
            if card.has_ability("Guard") and not card.has_ability("Lurker"):
                guard_entities_without_lurker.append(card)
        if len(guard_entities_without_lurker) == 0:
            for card in self.opponent().in_play:
                if not card.has_ability("Lurker"):
                    card.can_be_clicked = True
            self.opponent().can_be_clicked = True
        else:
            for card in guard_entities_without_lurker:
                card.can_be_clicked = True

        if effect:
            for info in effect.targetted_this_turn:
                if info["target_type"] == "player":
                    self.opponent().can_be_clicked = False
                else:
                    card, _ = self.get_in_play_for_id(info["id"])
                    if card:
                        card.can_be_clicked = False

    def set_targets_for_player_effect(self):
        self.opponent().can_be_clicked = True
        self.current_player().can_be_clicked = True

    def set_targets_for_mob_effect(self, target_restrictions):
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

    def set_targets_for_artifact_effect(self):
        did_target = False
        for card in self.opponent().artifacts:
            card.can_be_clicked = True
            did_target = True
        for card in self.current_player().artifacts:
            card.can_be_clicked = True
            did_target = True
        return did_target

    def set_targets_for_being_cast_spell_effect(self):
        for spell in self.spell_stack:
            card = spell[1]
            if card["card_type"] == "Spell":
                card["can_be_clicked"] = True

    def set_targets_for_being_cast_mob_effect(self):
        for spell in self.spell_stack:
            card = spell[1]
            if card["card_type"] == "Mob":
                card["can_be_clicked"] = True

    def set_targets_for_opponents_mob_effect(self, target_restrictions):
        self.set_targets_for_player_mob_effect(target_restrictions, self.opponent())

    def set_targets_for_self_mob_effect(self, target_restrictions):
        self.set_targets_for_player_mob_effect(target_restrictions, self.current_player())

    def set_targets_for_player_mob_effect(self, target_restrictions, player):
        if len(target_restrictions) > 0 and list(target_restrictions[0].keys())[0] == "needs_guard":
            set_targets = False
            for e in player.in_play:
                if e.id != player.card_info_to_target["card_id"]:
                    if not e.has_ability("Lurker"):
                        if e.has_ability("Guard"):
                            set_targets = True
                            e.can_be_clicked = True
            return set_targets

        set_targets = False
        for card in player.in_play:
            if card.id != player.card_info_to_target["card_id"]:
                if not card.has_ability("Lurker"):
                    card.can_be_clicked = True
                    set_targets = True
        return set_targets

    def has_targets_for_mob_effect(self, target_restrictions):
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
        return self.has_targets_for_opponents_mob_effect(target_restrictions)

    def has_targets_for_opponents_mob_effect(self, target_restrictions):
        return self.has_target_for_self_or_opponent_mob_effect(target_restrictions, self.opponent())

    def has_targets_for_self_mob_effect(self, target_restrictions):
        return self.has_target_for_self_or_opponent_mob_effect(target_restrictions, self.current_player())

    def has_target_for_self_or_opponent_mob_effect(self, target_restrictions, player):
        if len(target_restrictions) > 0 and target_restrictions[0] == "needs_guard":
            for e in player.in_play:
                if e.id != player.card_info_to_target["card_id"]:
                    if e.has_ability("Guard"):
                        if not e.has_ability("Lurker"):
                            return True
            return False

        if len(target_restrictions) > 0 and list(target_restrictions[0].keys())[0] == "power":
            for e in player.in_play:
                if self.power_with_tokens(e, player) >= list(target_restrictions[0].values())[0]:
                    return True
            return False

        for e in player.in_play:
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

        if len(self.players) == 2 and join_occured:
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
        if game_type == "test_stacked_deck":
            self.start_test_stacked_deck_game(message)
        elif game_type == "constructed":
            self.start_constructed_game(message)
        else:
            print(f"unknown game type: {game_type}")

    def start_test_stacked_deck_game(self, message):
        if self.players[0].max_mana == 0: 
            for x in range(0, 2):
                for card_name in self.player_decks[x]:
                    self.players[x].add_to_deck(card_name, 1)
                self.players[x].deck.reverse()
            self.get_starting_artifacts()
            self.get_starting_spells()
            for x in range(0, 2):
                self.players[x].draw(self.initial_hand_size)

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

                deck_to_use = deck_to_use if deck_to_use else random.choice([default_deck_genie_wizard(), default_deck_dwarf_tinkerer()])
                card_names = []
                for key in deck_to_use["cards"]:
                    for _ in range(0, deck_to_use["cards"][key]):
                        card_names.append(key)
                for card_name in card_names:
                    self.players[x].add_to_deck(card_name, 1)
                random.shuffle(self.players[x].deck)
            self.get_starting_artifacts()
            self.get_starting_spells()
            for x in range(0, 2):                
                self.players[x].draw(self.initial_hand_size)

            self.send_start_first_turn(message)

    def get_starting_artifacts(self):
        found_artifact = None
        for c in self.current_player().deck:
            if len(c.abilities) > 0 and c.abilities[0].descriptive_id == "Starts in Play":
                found_artifact = c
                break
        if found_artifact:
            found_artifact.turn_played = self.turn
            self.current_player().play_artifact(found_artifact)
            self.current_player().deck.remove(found_artifact)
        
        found_artifact = None
        for c in self.opponent().deck:
            if len(c.abilities) > 0 and c.abilities[0].descriptive_id == "Starts in Play":
                found_artifact = c
                break
        if found_artifact:
            found_artifact.turn_played = self.turn
            self.opponent().play_artifact(found_artifact)
            self.opponent().deck.remove(found_artifact)

    def get_starting_spells(self):
        found_spell = None
        for c in self.current_player().deck:
            if len(c.abilities) > 0 and c.abilities[0].descriptive_id == "Starts in Hand":
                found_spell = c
                break
        if found_spell:
            self.current_player().hand.append(found_spell)
            self.current_player().deck.remove(found_spell)
        
        found_artifact = None
        for c in self.opponent().deck:
            if len(c.abilities) > 0 and c.abilities[0].descriptive_id == "Starts in Play":
                found_artifact = c
                break
        if found_artifact:
            found_artifact.turn_played = self.turn
            self.opponent().play_artifact(found_artifact)
            self.opponent().deck.remove(found_artifact)

    def send_start_first_turn(self, message):
        new_message = copy.deepcopy(message)
        new_message["move_type"] = "START_FIRST_TURN"
        new_message["username"] = self.players[0].username
        self.play_move(new_message)

    def end_turn(self, message):
        if len(self.current_player().card_choice_info["cards"]) > 0 or \
            self.current_player().card_info_to_target["card_id"]:
            print(f"can't end turn when there is an effect left to resolve {self.current_player().card_info_to_target['effect_type']} {self.current_player().card_choice_info}")
            return message
        if len(self.spell_stack) > 0:
            print(f"can't end turn when there is a spell on the stack")
            return message
        if self.defending_player:
            print(f"can't end turn when there is an ongoing attack")
            return message
        self.remove_temporary_tokens()
        self.remove_temporary_effects()
        self.remove_temporary_abilities()
        self.clear_damage_this_turn()
        # for Multishot Bow
        self.clear_artifact_effects_targetted_this_turn()

        cards_to_discard = []
        cards_to_keep = []

        for card in self.current_player().hand:
            if card.has_ability("Keep"):
                cards_to_keep.append(card)
            else:
                cards_to_discard.append(card)
        if self.discard_end_of_turn:
            for card in cards_to_discard:
                self.current_player().hand.remove(card)
                self.current_player().played_pile.append(card)
        for card in cards_to_keep:
            for a in card.abilities:
                if a.name == "Keep":
                    if card.power:
                        card.power += a.keep_power_increase
                    if card.toughness:
                        card.toughness += a.keep_toughness_increase
                    if a.keep_evolve:
                         evolved_card = self.current_player().add_to_deck(a.keep_evolve, 1, add_to_hand=True)
                         self.current_player().hand.remove(evolved_card)
                         self.current_player().hand[self.current_player().hand.index(card)] = evolved_card

        for mob in self.current_player().in_play:
            for effect in mob.effects_triggered():
                if effect.name == "spell_from_yard":
                    spells = []
                    for card in self.current_player().played_pile:
                        if card.card_type == "Spell":
                            spells.append(card)
                    if len(spells) == 0:
                        continue
                    else:
                        if len(self.current_player().hand) < 10:
                            spell = random.choice(spells)
                            self.current_player().hand.append(spell)
                            self.current_player().played_pile.remove(spell)

        self.turn += 1
        self.actor_turn += 1
        message["log_lines"].append(f"{self.current_player().username}'s turn.")
        message = self.current_player().start_turn(message)
        return message

    def select_card_in_hand(self, message):
        # todo: what happens if you select a card then another card?
        for card in self.current_player().hand:
            if card.id == message["card"]:
                message["card_name"] = card.name

                has_mob_target = False
                if len(self.current_player().in_play + self.opponent().in_play) > 0:
                    for mob in self.current_player().in_play + self.opponent().in_play:
                        if not mob.has_ability("Lurker"):
                            has_mob_target = True

                if card.needs_artifact_target() and len(self.current_player().artifacts) == 0 and len(self.opponent().artifacts) == 0 :
                    print(f"can't select artifact targetting spell with no artifacts in play")
                    return None
                elif card.card_type == "Spell" and card.needs_mob_target() and not has_mob_target:
                    print(f"can't select mob targetting spell with no entities without Lurker in play")
                    return None
                elif card.has_ability("Instrument Required") and not self.current_player().has_instrument():
                    print(f"can't cast {card.name} without having an Instument")
                    return None
                elif card.cost <= self.current_player().current_mana():
                    if self.current_player().selected_spell() and card.id == self.current_player().selected_spell().id and card.needs_targets_for_spell():
                        self.current_player().reset_card_info_to_target()
                    elif self.current_player().selected_spell() and card.id == self.current_player().selected_spell().id:
                        message["move_type"] = "PLAY_CARD"
                        message = self.play_move(message)
                        # play card
                    elif card.card_type == "Spell" and not card.needs_targets_for_spell():
                            message["move_type"] = "PLAY_CARD"
                            message = self.play_move(message)
                    elif card.card_type == "Mob":
                        if self.current_player().can_summon():
                            message["move_type"] = "PLAY_CARD"
                            message = self.play_move(message)
                        else:
                            print(f"can't summon because of {self.current_player().abilities}")
                    elif card.card_type == "Artifact":
                        if self.current_player().can_play_artifact():
                            message["move_type"] = "PLAY_CARD"
                            message = self.play_move(message)
                        else:
                            print(f"can't play artifact")
                    else:
                        self.current_player().card_info_to_target["card_id"] = card.id
                        self.current_player().card_info_to_target["effect_type"] = "spell_cast"
                        # todo this is hardcoded, cant support multiple effects per card?
                        self.current_player().card_info_to_target["effect_index"] = 0
                else:
                    print(f"can't select, card costs too much - costs {card.cost}, mana available {self.current_player().current_mana()}")                        
                    return None
                break
        return message

    def select_stack_spell(self, message):
        cp = self.current_player()
        if cp.card_info_to_target["effect_type"] != "spell_cast":
            print(f"can't select stack spell with non-counterspell")
            return None
        selected_spell = cp.selected_spell()
        effect = selected_spell.effects[0]
        stack_spell = self.spell_stack[0]
        stack_spell_card = Card(stack_spell[1])
        if effect.target_type == "being_cast_mob" and stack_spell_card.card_type != "Mob":
            print(f"can't select non-mob with mob-counterspell")
            return None

        return self.select_stack_target_for_spell(selected_spell, message)

    def select_mob(self, message):
        cp = self.current_player()
        if cp.card_info_to_target["effect_type"] in ["mob_comes_into_play", "mob_activated"]:
            defending_card, defending_player = self.get_in_play_for_id(message["card"])
            if defending_card.has_ability("Lurker"):
                print(f"can't target mob with Lurker")
                return None                
            message["defending_card"] = message["card"]
            card = cp.selected_mob()
            if cp.card_info_to_target["effect_type"] == "mob_comes_into_play":
                message = self.select_mob_target_for_mob_effect(card, message)
            elif cp.card_info_to_target["effect_type"] == "mob_activated": 
                message = self.select_mob_target_for_mob_activated_effect(card, message)
        elif cp.card_info_to_target["effect_type"] == "spell_cast":
            selected_card = cp.selected_spell()
            defending_card, defending_player = self.get_in_play_for_id(message["card"])
            if not selected_card.can_target_entities():
                print(f"can't target mob with {selected_card.name}")
                return None                                
            if defending_card.has_ability("Lurker"):
                print(f"can't target mob with Lurker")
                return None                
            # todo handle cards with multiple effects
            if cp.selected_spell().effects[0].target_type == "opponents_mob" and self.get_in_play_for_id(message["card"])[0] not in self.opponent().in_play:
                print(f"can't target own mob with opponents_mob effect from {cp.selected_spell().name}")
                return None
            message["defending_card"] = message["card"]
            message = self.select_mob_target_for_spell(cp.selected_spell(), message)
        elif len(cp.card_choice_info["cards"]) > 0 and cp.card_choice_info["choice_type"] == "select_mob_for_ice_prison":
             selected_card = cp.in_play_card(message["card"])
             chose_card = False
             if selected_card:
                for c in cp.card_choice_info["cards"]:
                    if c.id == selected_card.id:
                        selected_card.attacked = False
                        cp.reset_card_choice_info()
                        chose_card = True
             if not chose_card:
                print("can't select that mob to un-attack for ice prison")
        elif cp.controls_mob(message["card"]):
            card, _ = self.get_in_play_for_id(message["card"])
            if card == cp.selected_mob():                
                only_has_ambush_attack = False
                if not card.has_ability("Fast"):
                    if card.has_ability("Ambush"):
                        if card.turn_played == self.turn:
                            only_has_ambush_attack = True
                if only_has_ambush_attack:
                    print(f"can't attack opponent because a mob only has Ambush")
                elif self.opponent().has_guard() and not cp.in_play_card(message["card"]).has_ability("Evade Guard"):                        
                    self.current_player().reset_card_info_to_target()
                    print(f"can't attack opponent because a mob has Guard")
                else:                 
                    message["move_type"] = "ATTACK"
                    message["card_name"] = cp.in_play_card(message["card"]).name
                    message = self.play_move(message)   
            elif cp.selected_artifact():
                defending_card, defending_player = self.get_in_play_for_id(message["card"])
                return self.activate_artifact_on_mob(message, defending_card, defending_player, cp.card_info_to_target["effect_index"])
            elif cp.can_select_for_attack(message["card"]):
                cp.select_in_play(message["card"])
            else:
                print("can't select that mob")
                return None
        elif not cp.controls_mob(message["card"]):
            defending_card, defending_player = self.get_in_play_for_id(message["card"])
            selected_mob = cp.selected_mob()
            if selected_mob:
                if not defending_card.has_ability("Lurker") and (not self.opponent().has_guard() or defending_card.has_ability("Guard") or selected_mob.has_ability("Evade Guard")):                        
                    message["move_type"] = "ATTACK"
                    message["card"] = selected_mob.id
                    message["card_name"] = selected_mob.name
                    message["defending_card"] = defending_card.id
                    message = self.play_move(message)
                else:
                    if defending_card.has_ability("Lurker"):
                        print(f"can't attack {defending_card.name} because it has Lurker")
                    else:
                        print(f"can't attack {defending_card.name} because another mob has Guard")
                    return None                                            
            elif cp.selected_artifact():
                effect_can_be_used = True
                if cp.selected_artifact().needs_self_mob_target_for_activated_effect(cp.card_info_to_target["effect_index"]):
                    effect_can_be_used = False if defending_card in self.opponent().in_play else True
                if effect_can_be_used:
                    return self.activate_artifact_on_mob(message, defending_card, defending_player, cp.card_info_to_target["effect_index"])
                else:
                    print(f"that artifact effect can't target {defending_card.name}")
                    return None
            elif defending_card:
                print(f"nothing selected to target {defending_card.name}")
                return None
            else:
                print(f"taking back a mob?")
                return None
        else:
            print("Should never get here")                                
        return message

    def activate_artifact_on_mob(self, message, defending_card, defending_player, effect_index):
        if defending_card.has_ability("Lurker"):
            print(f"can't target mob with Lurker")
            return None                
        effect = self.current_player().selected_artifact().effects[effect_index]
        if effect.name == "attack":
            if defending_player.has_guard() and not defending_card.has_ability("Guard"):
                return None                

            for info in effect.targetted_this_turn:
                if info["target_type"] == "mob":
                    card, _ = self.get_in_play_for_id(info["id"])
                    if info["id"] == defending_card.id:
                        print(f"already attacked {defending_card.name} with {self.current_player().selected_artifact().name}")
                        return None                

        message["move_type"] = "ACTIVATE_ARTIFACT"
        message["effect_index"] = effect_index
        message["card"] = self.current_player().selected_artifact().id
        message["card_name"] = self.current_player().selected_artifact().name
        message["defending_card"] = defending_card.id
        message = self.play_move(message)      
        return message      

    def select_artifact(self, message):
        cp = self.current_player()
        artifact = cp.artifact_in_play(message["card"])
        if not artifact and not cp.selected_spell() and not cp.selected_mob():
            print("can't activate opponent's artifacts")
            return None
        effect_index = message["effect_index"] if "effect_index" in message else 0
        message["effect_index"] = effect_index
        if cp.card_info_to_target["effect_type"] in ["mob_comes_into_play"]:
            message = self.select_artifact_target_for_mob_effect(cp.selected_mob(), message)
        elif cp.card_info_to_target["effect_type"] in ["mob_activated"]:
            message = self.select_artifact_target_for_artifact_effect(cp.selected_mob(), message)
        elif cp.selected_spell():  
            # todo handle cards with multiple effects
            if cp.selected_spell().effects[effect_index].target_type == "opponents_artifact" and self.get_in_play_for_id(message["card"])[0] not in self.opponent().artifacts:
                print(f"can't target own artifact with opponents_artifact effect from {cp.selected_spell().name}")
                return None
            message = self.select_artifact_target_for_spell(cp.selected_spell(), message)
        elif cp.controls_artifact(message["card"]):
            artifact = cp.artifact_in_play(message["card"])
            effect = artifact.effects_enabled()[effect_index]
            if cp.selected_artifact() and artifact.id == cp.selected_artifact().id and artifact.needs_target_for_activated_effect(effect_index):
                cp.reset_card_info_to_target()
            elif not effect.name in artifact.effects_exhausted and effect.cost <= cp.current_mana():
                if not artifact.needs_target_for_activated_effect(effect_index):
                    message["move_type"] = "ACTIVATE_ARTIFACT"
                    message = self.play_move(message)
                elif artifact.needs_mob_target_for_activated_effect() and (len(cp.in_play) > 0 or len(self.opponent().in_play) > 0):
                    cp.select_artifact(message["card"], effect_index)
                elif not artifact.needs_mob_target_for_activated_effect(): # player targets
                    cp.select_artifact(message["card"], effect_index)
                else:
                    cp.reset_card_info_to_target()
            else:
                print(f"can't activate artifact")
                return None
        elif not cp.controls_artifact(message["card"]):
            defending_card = self.get_in_play_for_id(message["card"])
            selected_artifact = cp.selected_artifact()
            if selected_artifact:
                message["move_type"] = "ACTIVATE_ARTIFACT"
                message["card"] = selected_artifact.id
                message["card_name"] = selected_artifact.name
                message["defending_artifact"] = defending_artifact.id
                message = self.play_move(message)
            else:
                print(f"nothing selected to target {defending_card.name}")
                return None
        else:
            print("Should never get here")                                
        return message

    def select_player(self, move_type, message):
        if self.current_player().selected_mob() and self.current_player().card_info_to_target["effect_type"] in ["mob_activated", "mob_comes_into_play"]:
            if move_type == 'SELECT_OPPONENT':
                message = self.select_player_target_for_mob_effect(self.opponent().username, self.current_player().selected_mob(), message)
            else:
                message = self.select_player_target_for_mob_effect(self.current_player().username, self.current_player().selected_mob(), message)
        elif self.current_player().selected_spell():
            target_player = self.current_player() if move_type == 'SELECT_SELF' else self.opponent()
            if move_type == 'SELECT_SELF' and not self.current_player().selected_spell().can_target_self():
                print(f"can't target self because the target_type is {self.current_player().selected_spell().effects[0].target_type}")
                return None                
            elif move_type == 'SELECT_OPPONENT' and not self.current_player().selected_spell().can_target_opponent():
                print(f"can't target opponent {target_player.username} because the target_type is {self.current_player().selected_spell().effects[0].target_type}")
                return None                
            else:
                casting_spell = True
                message = self.select_player_target_for_spell(target_player.username, self.current_player().selected_spell(), message)
        elif self.current_player().selected_artifact():
            target_player = self.current_player() if move_type == 'SELECT_SELF' else self.opponent()
            # todo hardcoded 0 index
            effect = self.current_player().selected_artifact().effects[0]
            for info in effect.targetted_this_turn:
                if info["target_type"] == "player":
                    print(f"already attacked {target_player.username} with {self.current_player().selected_artifact().name}")
                    return None                
            if effect.name == "attack":
                if target_player.has_guard():
                    print(f"can't attack {target_player.username} because an Mob has Guard")
                    return None                
            using_artifact = True
            message = self.select_player_target_for_artifact_effect(target_player.username, self.current_player().selected_artifact(), message)
        else:
            if self.current_player().selected_mob():
                card = self.current_player().selected_mob()
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
                    self.current_player().reset_card_info_to_target()
                elif only_has_ambush_attack:
                    print(f"can't attack opponent because the mob only has ambush")
                    return None
                else:
                    print(f"can't attack opponent because a mob has Guard")
                    return None
        return message

    def initiate_attack(self, message):
        self.actor_turn += 1
        self.move_to_complete = copy.deepcopy(message)
        self.defending_player = self.current_player()
        self.unset_clickables(message["move_type"])
        self.set_clickables()
        if not self.current_player().has_instants():
            return self.attack(message)

        card_id = message["card"]
        attacking_card = self.opponent().in_play_card(card_id)
        if "defending_card" in message:
            defending_card_id = message["defending_card"]
            defending_card = self.current_player().in_play_card(defending_card_id)
            message["log_lines"].append(f"{attacking_card.name} intends to attack {defending_card.name}")
        else:
            message["log_lines"].append(f"{attacking_card.name} intends to attack {self.current_player().username} for {self.power_with_tokens(attacking_card, self.opponent())}.")
        # todo rope

        return message

    def attack(self, message):
        move_to_complete = copy.deepcopy(self.move_to_complete)
        move_to_complete["log_lines"] = []
        self.move_to_complete = None
        self.actor_turn += 1
        self.defending_player = None
        card_id = move_to_complete["card"]
        attacking_card = self.current_player().in_play_card(card_id)
        attacking_card.attacked = True
        self.current_player().reset_card_info_to_target()
        self.unset_clickables(message["move_type"])
        self.set_clickables()
        
        # if the mob is removed from play by a spell or effect
        if not attacking_card:
            return move_to_complete
        
        for a in attacking_card.abilities:
            if a.descriptive_id == "Lurker":
                a.enabled = False
        if "defending_card" in move_to_complete:
            defending_card_id = move_to_complete["defending_card"]
            defending_card = self.opponent().in_play_card(defending_card_id)
            # if the defending mob is removed from play by a spell or effect
            if not defending_card:
                return move_to_complete
            self.resolve_combat(
                attacking_card, 
                defending_card
            )
            move_to_complete["defending_card"] = defending_card.as_dict()
            move_to_complete["log_lines"].append(f"{attacking_card.name} attacks {defending_card.name}")
        else:
            move_to_complete["log_lines"].append(f"{attacking_card.name} attacks {self.opponent().username} for {self.power_with_tokens(attacking_card, self.current_player())}.")
            self.opponent().damage(self.power_with_tokens(attacking_card, self.current_player()))
        self.current_player().do_attack_abilities(attacking_card)
        return move_to_complete

    def activate_artifact(self, message):
        card_id = message["card"]
        activated_effect_index = message["effect_index"] if "effect_index" in message else 0
        artifact = self.current_player().artifact_in_play(card_id)            
        if not artifact:
            print("can't activate opponent's artifacts")
            return None
        e = artifact.enabled_activated_effects()[activated_effect_index]
        if not artifact.has_ability("multi_mob_attack"):
            artifact.can_activate_abilities = False
            # todo support multi-use abilities on artifacts
            artifact.effects_exhausted = {e.name: True}
        
        if "defending_card" in message:
            defending_card, _  = self.get_in_play_for_id(message["defending_card"])
            message["log_lines"].append(f"{self.current_player().username} uses {artifact.name} on {defending_card.name}")
            effect_targets = []
            effect_targets.append({"id": defending_card.id, "target_type": "mob"})
            message = self.current_player().do_card_effect(artifact, e, message, effect_targets, 0)
            self.current_player().reset_card_info_to_target()
            if artifact.has_ability("multi_mob_attack"):
                e.targetted_this_turn.append(effect_targets[0])
        else:
            if e.target_type == "self":
                message = self.current_player().do_card_effect(artifact, e, message, [{"id": message["username"], "target_type": "player"}], 0)
            elif e.target_type == "opponent":
                message = self.current_player().do_card_effect(artifact, e, message, [{"id": self.opponent().username, "target_type": "player"}], 0)
            elif e.target_type == "all":
                message = self.current_player().do_card_effect(artifact, e, message, [{"id": self.opponent().username, "target_type": "player"}], 0)
            # todo unhardcode for other fetch types if we can fetch more than Artifacts
            elif e.target_type == "Artifact":
                message = self.current_player().do_card_effect(artifact, e, message, [{"id": message["username"], "target_type": e.target_type}], 0)
            elif e.target_type == "self_mob":
                message = self.select_mob_target_for_artifact_activated_effect(artifact, message)
            else:
                target_player = self.players[0]
                if target_player.username != message["effect_targets"][0]["id"]:
                    target_player = self.players[1]
                message["log_lines"].append(f"{self.current_player().username} uses {artifact.name} on {target_player.username}")
                message["effect_targets"] = []
                message["effect_targets"].append({"id": target_player.username, "target_type": "player"})
                message = self.current_player().do_card_effect(artifact, e, message, message["effect_targets"], 0)
                self.current_player().reset_card_info_to_target()
                if artifact.has_ability("multi_mob_attack"):
                    e.targetted_this_turn.append(message["effect_targets"][0])

        self.current_player().reset_card_info_to_target()
        # Wish Stone
        if len(artifact.enabled_activated_effects()) and artifact.enabled_activated_effects()[0].sacrifice_on_activate:
            self.send_card_to_played_pile(artifact, self.current_player(), did_kill=True)
        return message

    def activate_mob(self, message):
        card_id = message["card"]
        mob, _ = self.get_in_play_for_id(card_id)
        if not mob.can_activate_abilities:
            print(f"can't activate, already used {mob}")
            return None

        activated_effect_index = message["effect_index"]
        e = mob.enabled_activated_effects()[activated_effect_index]

        for a in mob.abilities:
            if a.descriptive_id == "Lurker":
                a.enabled = False

        if e.name == "pump_power":
            # todo don't hardcode for Infernus
            message["log_lines"].append(f"{self.current_player().username} pumps {mob.name} +1/+0.")
            effect_targets = []
            effect_targets.append({"id": mob.id, "target_type":e.target_type})
            message = self.current_player().do_card_effect(mob, e, message, effect_targets, 0)
        elif e.name == "unwind":
            if "defending_card" in message:
                message = self.current_player().do_card_effect(mob, e, message, message["effect_targets"], 0)
                self.current_player().reset_card_info_to_target()
                mob.can_activate_abilities = False
            else:
                message["log_lines"].append(f"{self.current_player().username} activates {mob.name}.")
                message = self.current_player().target_or_do_mob_effects(mob, message, self.current_player().username, is_activated_effect=True)
        else:
            print(f"unsupported mob effect {e}")
        return message

    def make_card(self, message):
        if len(self.current_player().hand) < 10:
            self.current_player().add_to_deck(message["card"]["name"], 1, add_to_hand=True, card_cost=message["card"]["cost"])
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
        if card_type == "Artifact":
            if into_play:
                self.current_player().play_artifact(card)
            else:
                self.current_player().hand.append(card)
            self.current_player().deck.remove(card)
        message["log_lines"].append(f"{message['username']} chose {card.name}.")

        self.current_player().reset_card_choice_info()
        return message

    def finish_riffle(self, message):
        """
            Fetch the selected card from current_player's deck
        """
        chosen_card = None
        for c in self.current_player().deck:
            if c.id == message['card']:
                chosen_card = c
        for card in self.current_player().card_choice_info["cards"]:
            card_to_remove = None
            for deck_card in self.current_player().deck:
                if card.id == deck_card.id:
                   card_to_remove = deck_card 
            self.current_player().deck.remove(deck_card)
            if card.id != chosen_card.id:
                self.send_card_to_played_pile(card, self.current_player(), did_kill=False)
                message["log_lines"].append(f"{message['username']} puts {card.name} into their played pile.")
        self.current_player().deck.append(chosen_card)
        self.current_player().draw(1)
        self.current_player().reset_card_choice_info()
        return message

    def get_in_play_for_id(self, card_id):
        """
            Returns a tuple of the mob and controlling player for a card_id of a card that is an in_play mob
        """
        for p in [self.opponent(), self.current_player()]:
            for card in p.in_play + p.artifacts:
                if card.id == card_id:
                    return card, p
        return None, None

    def send_card_to_played_pile(self, card, player, did_kill=True):
        """
            Send the card to the player's played_pile and reset any temporary effects on the card
        """
        if card in player.artifacts:
            player.artifacts.remove(card)
        if card in player.in_play:
            player.in_play.remove(card)
        card.do_leaves_play_effects(player, did_kill=did_kill)

        if card.id == player.card_info_to_target["card_id"]:
            player.reset_card_info_to_target()

        if player.username != card.owner_username:
            if player == self.current_player():
                player = self.opponent()
            else:
                player = self.current_player()
        new_card = self.factory_reset_card(card, player)
        # hax
        if new_card.name == "Rolling Thunder":
            new_card.effects[0].amount = card.effects[0].amount 
        if new_card.name == "Fidget Spinner":
            new_card.power = card.power
            new_card.toughness = card.toughness
        # hax - does this more belong in factory_reset_card?
        new_card.level = card.level

        player.played_pile.append(new_card)

        self.update_for_mob_changes_zones(player)

    def update_for_mob_changes_zones(self, player):

        # code for War Scorpion
        for e in player.in_play:
            effect = e.effect_with_trigger("mob_changes_zones")
            if effect and effect.name == "toggle_symbiotic_fast":
                abilities_to_remove = []
                for ability in e.abilities:
                    if ability.name == "Fast":
                       abilities_to_remove.append(ability) 
                for ability in abilities_to_remove:
                    e.abilities.remove(ability)

            # code for Spirit of the Stampede
            if effect and effect.name == "set_token":
                tokens_to_remove = []
                for t in e.tokens:
                    if t.id == e.id:
                        tokens_to_remove.append(t)
                for t in tokens_to_remove:
                    e.tokens.remove(t)
                token = copy.deepcopy(effect.tokens[0])
                # todo: maybe support IDs for removal for more than Spirit of the Stampede
                token.id = e.id
                player.do_add_token_effect_on_mob(
                    token, 
                    e.id
                )

        anything_friendly_has_fast = False
        for e in player.in_play:
            if e.has_ability("Fast"):
                anything_friendly_has_fast = True

        for e in player.in_play:
            effect = e.effect_with_trigger("mob_changes_zones")
            if effect and effect.name == "toggle_symbiotic_fast":
                if anything_friendly_has_fast:
                    e.abilities.append(CardAbility({
                        "name": "Fast",
                        "descriptive_id": "Fast"
                    }, len(e.abilities)))


        # code for Arsenal artifact
        for r in player.artifacts:
            effect = r.effect_with_trigger("mob_changes_zones")
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
                    # todo move this copy and id code into do_add_token_effect_on_mob
                    new_token = copy.deepcopy(effect.tokens[0])
                    new_token.id = r.id
                    player.do_add_token_effect_on_mob(
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
            attacking_card.damage_to_show += self.power_with_tokens(defending_card, self.opponent())
            if attacking_card.damage < attacking_card.toughness_with_tokens() and defending_card.has_ability("DamageTakeControl"):
                self.current_player().in_play.remove(attacking_card)
                self.opponent().in_play.append(attacking_card)
                self.update_for_mob_changes_zones(self.current_player())
                self.update_for_mob_changes_zones(self.opponent())
        if defending_card.shielded:
            defending_card.shielded = False
        else:
            if attacking_card.has_ability("Stomp"):
                stomp_damage = self.power_with_tokens(attacking_card, self.current_player()) - (defending_card.toughness_with_tokens() - defending_card.damage)
                if stomp_damage > 0:
                    self.opponent().damage(stomp_damage)
            defending_card.damage += self.power_with_tokens(attacking_card, self.current_player())
            defending_card.damage_this_turn += self.power_with_tokens(attacking_card, self.current_player())
            defending_card.damage_to_show += self.power_with_tokens(attacking_card, self.opponent())
            if defending_card.damage < defending_card.toughness_with_tokens() and attacking_card.has_ability("DamageTakeControl"):
                self.opponent().in_play.remove(defending_card)
                self.current_player().in_play.append(defending_card)
                self.update_for_mob_changes_zones(self.current_player())
                self.update_for_mob_changes_zones(self.opponent())
        
        if defending_card.damage >= defending_card.toughness_with_tokens():
            self.send_card_to_played_pile(defending_card, self.opponent(), did_kill=True)
        if attacking_card.damage >= attacking_card.toughness_with_tokens():
            self.send_card_to_played_pile(attacking_card, self.current_player(), did_kill=True)


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

    def remove_temporary_effects(self):
        for p in [[self.current_player(), self.opponent()], [self.opponent(), self.current_player()]]:
            entities_to_switch_sides = []
            for c in p[0].in_play:
                perm_effects = []
                for e in c.effects:
                    e.turns -= 1
                    if e.turns == 0:
                        if e.name == "take_control":
                            entities_to_switch_sides.append(c)                        
                    else:
                        perm_effects.append(e)
                c.effects = perm_effects
            for c in entities_to_switch_sides:
                p[0].in_play.remove(c)
                p[1].in_play.append(c)

    def remove_temporary_abilities(self):
        perm_abilities = []
        for a in self.current_player().abilities:
            if a.turns > 0:
                a.turns -= 1
                if a.turns != 0:
                    perm_abilities.append(a)
            else:
                perm_abilities.append(a)
        self.current_player().abilities = perm_abilities

    def clear_artifact_effects_targetted_this_turn(self):
        for r in self.current_player().artifacts:
            for e in r.effects:
                e.targetted_this_turn = []

    def clear_damage_this_turn(self):
        for c in self.current_player().in_play + self.opponent().in_play:
            c.damage_this_turn = 0
        self.current_player().damage_this_turn = 0
        self.opponent().damage_this_turn = 0

    def select_artifact_target(self, card_to_target, message, move_type):
        new_message = copy.deepcopy(message)
        new_message["move_type"] = move_type
        selected_card = self.current_player().artifact_in_play(message["card"])
        if not selected_card:
            selected_card = self.opponent().artifact_in_play(message["card"])
        effect_targets = []
        #todo multiple effects
        effect_targets.append({"id": selected_card.id, "target_type":"artifact"})            
        new_message["effect_targets"] = effect_targets
        new_message["card"] = card_to_target.id
        new_message["card_name"] = card_to_target.name

        self.current_player().reset_card_info_to_target()
        new_message = self.play_move(new_message)       
        return new_message             

    def select_artifact_target_for_spell(self, card_to_target, message):
        return self.select_artifact_target(card_to_target, message, "PLAY_CARD")

    def select_artifact_target_for_mob_effect(self, mob_with_effect_to_target, message):
        return self.select_artifact_target(mob_with_effect_to_target, message, "RESOLVE_MOB_EFFECT")

    def select_artifact_target_for_artifact_effect(self, artifact_with_effect_to_target, message):
        return self.select_artifact_target(artifact_with_effect_to_target, message, "RESOLVE_MOB_EFFECT")

    def select_mob_target(self, card_to_target, message, move_type, activated_effect=False, mob_activated_effect=False):
        new_message = copy.deepcopy(message)
        new_message["move_type"] = move_type
        selected_card = self.current_player().in_play_card(message["defending_card"])
        if not selected_card:
            selected_card = self.opponent().in_play_card(message["defending_card"])
        effect_targets = []
        effect_targets.append({"id": selected_card.id, "target_type":"mob"})            
        if not activated_effect:
                if len(card_to_target.effects) == 2:
                    if card_to_target.effects[1].target_type == "mob" or card_to_target.effects[1].target_type == "opponents_mob":
                        # hack for animal trainer
                        effect_targets.append({"id": selected_card.id, "target_type":"mob"})            
                    elif card_to_target.effects[1].target_type == "opponent":
                        pass
                        # hack for impale
                        # skip it, because it will be assigned in play_card because it has an opponent type
                        # effect_targets.append({"id": self.opponent().username, "target_type":"player"})            
                    else:
                        # hack for siz pop and stiff wind
                        effect_targets.append({"id": message["username"], "target_type":"player"})
        new_message["effect_targets"] = effect_targets
        new_message["card"] = card_to_target.id
        new_message["card_name"] = card_to_target.name
        self.current_player().reset_card_info_to_target()
        new_message = self.play_move(new_message)       
        return new_message             
    
    def select_stack_target(self, card_to_target, message, move_type, activated_effect=False, mob_activated_effect=False):
        new_message = copy.deepcopy(message)
        new_message["move_type"] = move_type

        selected_card = None
        for spell in self.spell_stack:
            if spell[1]["id"] == message["card"]:
                selected_card = Card(spell[1])
                break

        effect_targets = []
        effect_targets.append({"id": selected_card.id, "target_type":"being_cast_mob"})            
        new_message["effect_targets"] = effect_targets
        new_message["card"] = card_to_target.id
        new_message["card_name"] = card_to_target.name
        self.current_player().reset_card_info_to_target()
        new_message = self.play_move(new_message)       
        return new_message             

    def select_stack_target_for_spell(self, card_to_target, message):
        return self.select_stack_target(card_to_target, message, "PLAY_CARD")

    def select_mob_target_for_spell(self, card_to_target, message):
        return self.select_mob_target(card_to_target, message, "PLAY_CARD")

    def select_mob_target_for_mob_effect(self, mob_with_effect_to_target, message):
        return self.select_mob_target(mob_with_effect_to_target, message, "RESOLVE_MOB_EFFECT")

    def select_mob_target_for_artifact_activated_effect(self, artifact_with_effect_to_target, message):
        return self.select_mob_target(artifact_with_effect_to_target, message, "ACTIVATE_ARTIFACT", activated_effect=True)

    def select_mob_target_for_mob_activated_effect(self, artifact_with_effect_to_target, message):
        return self.select_mob_target(artifact_with_effect_to_target, message, "ACTIVATE_MOB", activated_effect=True)

    def select_player_target(self, username, card_with_effect_to_target, message, move_type):
        new_message = copy.deepcopy(message)
        new_message["move_type"] = move_type
        effect_targets = []
        effect_targets.append({"id": username, "target_type":"player"})            
        new_message["effect_targets"] = effect_targets
        new_message["card"] = card_with_effect_to_target.id
        new_message["card_name"] = card_with_effect_to_target.name
        new_message = self.play_move(new_message)    
        print ("doing play_move in select_player_target")   
        return new_message             

    def select_player_target_for_spell(self, username, card, message):
        return self.select_player_target(username, card, message, "PLAY_CARD")

    def select_player_target_for_mob_effect(self, username, mob_with_effect_to_target, message):
        return self.select_player_target(username, mob_with_effect_to_target, message, "RESOLVE_MOB_EFFECT")

    def select_player_target_for_artifact_effect(self, username, artifact_with_effect_to_target, message):
        return self.select_player_target(username, artifact_with_effect_to_target, message, "ACTIVATE_ARTIFACT")

    def is_under_ice_prison(self):
        for c in self.current_player().artifacts + self.opponent().artifacts:
            if len(c.effects_triggered()) > 0 and c.effects_triggered()[0].name ==  "stop_mob_renew":
                return True
        return False

    def power_with_tokens(self, card, player):
        power = card.power
        for t in card.tokens:
            if t.multiplier == "self_artifacts":
                power += t.power_modifier * len(player.artifacts)
            elif t.multiplier == "self_entities_and_artifacts":
                power += t.power_modifier * (len(player.artifacts) + len(player.in_play))
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
            self.damage_to_show = 0
            self.mana = 0
            self.max_mana = 0
            self.hand = []
            self.in_play = []
            self.artifacts = []
            self.deck = []
            self.played_pile = []
            self.can_be_clicked = False
            self.abilities = []
            self.reset_card_info_to_target()
            self.reset_card_choice_info()
        else:
            self.hand = [Card(c_info) for c_info in info["hand"]]
            self.in_play = [Card(c_info) for c_info in info["in_play"]]
            self.artifacts = [Card(c_info) for c_info in info["artifacts"]]
            self.hit_points = info["hit_points"]
            self.damage_this_turn = info["damage_this_turn"]
            self.damage_to_show = info["damage_to_show"]
            self.mana = info["mana"]
            self.max_mana = info["max_mana"]
            self.deck = [Card(c_info) for c_info in info["deck"]]
            self.played_pile = [Card(c_info) for c_info in info["played_pile"]]
            self.can_be_clicked = info["can_be_clicked"]
            self.abilities = [CardAbility(a, idx) for idx, a in enumerate(info["abilities"])] if "abilities" in info and info["abilities"] else []
            self.card_info_to_target = info["card_info_to_target"]
            self.card_choice_info = {"cards": [Card(c_info) for c_info in info["card_choice_info"]["cards"]], "choice_type": info["card_choice_info"]["choice_type"]}

    def __repr__(self):
        return f"{self.username} ({self.race}, deck_id: {self.deck_id}) - \
                {self.hit_points} hp - {self.damage_this_turn} damage_this_turn - {self.damage_to_show} damage_to_show - {self.mana} mana, self.card_info_to_target {self.card_info_to_target} \
                {self.max_mana} max_mana, {len(self.hand)} cards, {len(self.in_play)} in play, \
                {len(self.deck)} in deck, {len(self.played_pile)} in played_pile, \
                self.can_be_clicked {self.can_be_clicked}, \
                {self.card_choice_info} \
                {self.abilities}, self.artifacts {self.artifacts}"

    def as_dict(self):
        return {
            "username": self.username,
            "race": self.race,
            "hit_points": self.hit_points,
            "damage_this_turn": self.damage_this_turn,
            "damage_to_show": self.damage_to_show,
            "mana": self.mana,
            "max_mana": self.max_mana,
            "deck_id": self.deck_id,
            "card_info_to_target": self.card_info_to_target,
            "hand": [c.as_dict() for c in self.hand],
            "in_play": [c.as_dict() for c in self.in_play],
            "artifacts": [c.as_dict() for c in self.artifacts],
            "deck": [c.as_dict() for c in self.deck],
            "played_pile": [c.as_dict() for c in self.played_pile],
            "can_be_clicked": self.can_be_clicked,
            "abilities": [a.as_dict() for a in self.abilities],
            "card_choice_info": {"cards": [c.as_dict() for c in self.card_choice_info["cards"]], "choice_type": self.card_choice_info["choice_type"]}
        }

    def has_instants(self):
        for c in self.hand:
            if c.can_be_clicked:
                return True
        return False

    def current_mana(self):
        return self.mana + self.mana_from_artifacts()

    def mana_from_artifacts(self):
        mana = 0
        for artifact in self.artifacts:
            for effect in artifact.effects:
                if effect.name == "store_mana":
                    mana += effect.counters
        return mana

    def add_to_deck(self, card_name, count, add_to_hand=False, card_cost=None):
        card = None
        print(card_name)
        for c in Game.all_cards():
            if c.name == card_name:
                card = c
        for x in range(0, count):
            new_card = copy.deepcopy(card)
            if card_cost:
                new_card.cost = card_cost
            new_card.owner_username = self.username
            new_card.id = self.game.next_card_id
            self.game.next_card_id += 1
            new_card = self.modify_new_card(self.game, new_card)
            if add_to_hand:
                self.hand.append(new_card)
            else:
                self.deck.append(new_card)
        return new_card

    def damage(self, amount):
        while amount > 0 and self.hit_points > 0:
            amount -= 1
            if self.hit_points == 1 and self.cant_die_ability():
                continue
            self.hit_points -= 1
            self.damage_this_turn += 1
            self.damage_to_show += 1

    def draw(self, number_of_cards):
        for i in range(0,number_of_cards):
            if len(self.deck) == 0:
                for c in self.played_pile:
                    self.deck.append(c)
                self.played_pile = [] 
            if len(self.deck) == 0 or len(self.hand) == 10:
                continue
            card = self.deck.pop()
            self.hand.append(card)
            for r in self.artifacts:
                for effect in r.effects_triggered():
                    if effect.name == "reduce_cost" and card.card_type == effect.target_type:
                        card.cost -= 1
                        card.cost = max(0, card.cost)

    def do_card_effect(self, card, e, message, effect_targets, target_index):
        # weapons and instruments
        if e.counters >= 1:
            e.counters -= 1

        print(f"Do card effect: {e.name}");
        if e.name == "increase_max_mana":
            self.do_increase_max_mana_effect_on_player(play_[target_index]["id"], e.amount, card)
            message["log_lines"].append(f"{self.username} increases max mana by {e.amount}.")
        elif e.name == "set_max_mana":
            self.do_set_max_mana_effect(e.amount)
            message["log_lines"].append(f"{self.username} resets everyone's max mana to {e.amount} with {card.name}.")
        elif e.name == "reduce_mana":
            self.do_reduce_mana_effect_on_player(card, effect_targets[target_index]["id"], e.amount)
            message["log_lines"].append(f"{self.username} draws {e.amount} from {card.name}.")
        elif e.name == "draw":
            self.do_draw_effect_on_player(card, effect_targets[target_index]["id"], e.amount, e.multiplier)
            message["log_lines"].append(f"{self.username} draws {e.amount} from {card.name}.")
        elif e.name == "draw_if_damaged_opponent":
            drawn_count = self.do_draw_if_damaged_opponent_effect_on_player(card, effect_targets[target_index]["id"], e.amount)
            if drawn_count > 0:
                message["log_lines"].append(f"{self.username} draws {e.amount} from {card.name}.")
        elif e.name == "make_token":
            if e.target_type == "self":
                self.do_make_token_effect(e, card)
                message["log_lines"].append(f"{card.name} makes {e.amount} tokens.")
            else:
                self.game.opponent().do_make_token_effect(e, card)
                message["log_lines"].append(f"{card.name} makes {e.amount} tokens for {self.game.opponent().username}.")
        elif e.name == "create_card":
            if e.target_type == "self":
                self.do_create_card_effect(e)
                message["log_lines"].append(f"{card.name} creates {e.amount} {e.card_name}.")
            else:
                print(f"unsupported target_type {e.target_type} for create_card effect")
        elif e.name == "fetch_card":
            self.do_fetch_card_effect_on_player(card, effect_targets[target_index]["id"], e.target_type, e.target_restrictions, choice_type="fetch_artifact_into_hand")
            message["log_lines"].append(f"{self.username} fetches a card with {card.name}.")
        elif e.name == "fetch_card_into_play":
            self.do_fetch_card_effect_on_player(card, effect_targets[target_index]["id"], e.target_type, e.target_restrictions, choice_type="fetch_artifact_into_play")
            message["log_lines"].append(f"{self.username} cracks {card.name} to fetch a artifact.")
        elif e.name == "take_extra_turn":
            message["log_lines"].append(f"{self.username} takes an extra turn.")
            message = self.do_take_extra_turn_effect_on_player(effect_targets[target_index]["id"], message)
        elif e.name == "summon_from_deck":
            if e.target_type == "self":
                message["log_lines"].append(f"{self.username} summons something from their deck.")
            else:
                message["log_lines"].append(f"Both players fill their boards.")
            self.do_summon_from_deck_effect_on_player(e, effect_targets, target_index)
        elif e.name == "summon_from_deck_artifact":
            if e.target_type == "self":
                message["log_lines"].append(f"{self.username} summons something from their deck.")
                self.do_summon_from_deck_artifact_effect_on_player(e, effect_targets, target_index)
            else:
                print(f"unsupported target_type {e.target_type} for summon_from_deck_artifact effect for {card.name}")
        elif e.name == "discard_random":
                self.do_discard_random_effect_on_player(card, effect_targets[target_index]["id"], e.amount)
        elif e.name == "damage":
            if effect_targets[target_index]["target_type"] == "player":
                self.do_damage_effect_on_player(card, effect_targets[target_index]["id"], e.amount)
                message["log_lines"].append(f"{self.username} deals {e.amount} damage to {effect_targets[target_index]['id']}.")
            elif effect_targets[target_index]["target_type"] == "all_entities" or effect_targets[target_index]["target_type"] == "all":
                dead_entities = []
                for mob in self.in_play:
                    mob.damage += e.amount
                    mob.damage_this_turn += e.amount
                    mob.damage_to_show += e.amount
                    if mob.damage >= mob.toughness_with_tokens():
                        dead_entities.append(mob)
                for mob in dead_entities:
                    self.game.send_card_to_played_pile(mob, self, did_kill=True)
                dead_entities = []
                for mob in self.game.opponent().in_play:
                    mob.damage += e.amount
                    mob.damage_this_turn += e.amount
                    mob.damage_to_show += e.amount
                    if mob.damage >= mob.toughness_with_tokens():
                        dead_entities.append(mob)
                for mob in dead_entities:
                    self.game.send_card_to_played_pile(mob, self.game.opponent(), did_kill=True)
                if effect_targets[target_index]["target_type"] == "all":
                    self.damage(e.amount)
                    self.game.opponent().damage(e.amount)
                    message["log_lines"].append(f"{self.username} deals {e.amount} damage to all entities and players.")
                else:
                    message["log_lines"].append(f"{self.username} deals {e.amount} damage to all entities.")
            else:
                message["log_lines"].append(f"{self.username} deals {e.amount} damage to {self.game.get_in_play_for_id(effect_targets[target_index]['id'])[0].name}.")
                self.do_damage_effect_on_mob(card, effect_targets[target_index]["id"], e.amount)
        elif e.name == "heal":
            if effect_targets[target_index]["target_type"] == "player":
                self.do_heal_effect_on_player(card, effect_targets[target_index]["id"], e.amount)
                message["log_lines"].append(f"{self.username} heals {e.amount} on {effect_targets[target_index]['id']}.")
            else:
                message["log_lines"].append(f"{self.username} heals {e.amount} on {self.game.get_in_play_for_id(effect_targets[target_index]['id'])[0].name}.")
                self.do_heal_effect_on_mob(card, effect_targets[target_index]["id"], e.amount)
        elif e.name == "attack":
            if effect_targets[target_index]["target_type"] == "player":
                self.do_damage_effect_on_player(card, effect_targets[target_index]["id"], e.power)
                self.do_attack_abilities(card)
                message["log_lines"].append(f"{self.username} attacks {effect_targets[target_index]['id']} for {e.power} damage.")
            else:
                message["log_lines"].append(f"{self.username} attacks {self.game.get_in_play_for_id(effect_targets[target_index]['id'])[0].name} for {e.power} damage.")
                self.do_attack_effect_on_mob(card, effect_targets[target_index]["id"], e.power)

            #todo fix hardcoding, is every attack effect from a weapon?
            if e.counters == 0:
                if e.was_added:
                    card.deactivate_weapon()
                else:
                    self.game.send_card_to_played_pile(card, self, did_kill=True)
        elif e.name == "double_power":
            self.do_double_power_effect_on_mob(card, effect_targets[target_index]["id"])
            message["log_lines"].append(f"{self.username} doubles the power of {self.game.get_in_play_for_id(effect_targets[target_index]['id'])[0].name}.")
        elif e.name == "pump_power":
            self.do_pump_power_effect_on_mob(card, effect_targets[target_index]["id"], e.amount, e.cost)
            message["log_lines"].append(f"{self.username} pumps the power of {self.game.get_in_play_for_id(effect_targets[target_index]['id'])[0].name} by {e.amount}.")
        elif e.name == "kill":
            if e.target_type == "mob" or e.target_type == "artifact":
                message["log_lines"].append(f"{self.username} kills {self.game.get_in_play_for_id(effect_targets[target_index]['id'])[0].name}.")
                self.do_kill_effect_on_mob(effect_targets[target_index]["id"])
            else:
                card_ids_to_kill = []
                min_cost = -1
                max_cost = 9999
                instruments_ok = True
                for r in e.target_restrictions:
                    if list(r.keys())[0] == "min_cost":
                        min_cost = list(r.values())[0]
                    if list(r.keys())[0] == "max_cost":
                        max_cost = list(r.values())[0]
                    if list(r.keys())[0] == "instruments":
                        instruments_ok = list(r.values())[0]
                for card in self.in_play+self.artifacts+self.game.opponent().in_play+self.game.opponent().artifacts:
                    if card.cost >= min_cost and card.cost <= max_cost and (instruments_ok or not card.has_ability("Instrument")):
                        card_ids_to_kill.append(card.id)
                for card_id in card_ids_to_kill: 
                    self.do_kill_effect_on_mob(card_id)
        elif e.name == "take_control":
            if e.target_type == "all":
                while len(self.game.opponent().in_play) > 0 and len(self.in_play) < 7:
                    if len(e.abilities) and e.abilities[0].descriptive_id == "Fast":
                        self.game.opponent().in_play[0].abilities.append(copy.deepcopy(e.abilities[0]))
                    self.do_take_control_effect_on_mob(self.game.opponent().in_play[0].id)
                while len(self.game.opponent().artifacts) > 0 and len(self.artifacts) < 3:
                    if len(e.abilities) and e.abilities[0].descriptive_id == "Fast":
                        self.game.opponent().artifacts[0].effects_exhausted = {}
                    self.do_take_control_effect_on_artifact(self.game.opponent().artifacts[0].id)
                message["log_lines"].append(f"{self.username} takes control everything.")
            else:
                message["log_lines"].append(f"{self.username} takes control of {self.game.get_in_play_for_id(effect_targets[target_index]['id'])[0].name}.")
                self.do_take_control_effect_on_mob(effect_targets[target_index]["id"])
        elif e.name == "unwind":
            if e.target_type == "all_entities":
                message["log_lines"].append(f"{card.name} returns all entities to their owners' hands.")
                entities_to_unwind = []
                for mob in self.in_play:
                    if mob.id != card.id:
                        entities_to_unwind.append(mob.id)
                for mob in self.game.opponent().in_play:
                    if mob.id != card.id:
                        entities_to_unwind.append(mob.id)
                for eid in entities_to_unwind:
                    self.do_unwind_effect_on_mob(eid)
            else:
                target_card, target_player = self.game.get_in_play_for_id(effect_targets[target_index]['id'])
                message["log_lines"].append(f"{self.username} uses {card.name} to return {target_card.name} to {target_card.owner_username}'s hand.")
                self.do_unwind_effect_on_mob(effect_targets[target_index]["id"])
        elif e.name == "entwine":
            self.do_entwine_effect()
        elif e.name == "switch_hit_points":
            self.do_switch_hit_points_effect()
            message["log_lines"].append(f"{self.username} uses {card.name} to switch hit points with {effect_targets[target_index]['id']}.")
        elif e.name == "enable_activated_effect":
            self.do_enable_activated_effect_effect(card)
        elif e.name == "equip_to_mob":
            self.do_enable_equip_to_mob_effect(card, effect_targets[target_index]['id'])
        elif e.name == "unequip_from_mob":
            equipped_mob = None
            for mob in self.in_play:
                for token in mob.tokens:
                    if token.id == card.id:
                        equipped_mob = mob
            self.deactivate_equipment(card, equipped_mob)
        elif e.name == "view_hand":
            self.do_view_hand_effect()
        elif e.name == "gain_for_toughness":
            self.do_gain_for_toughness_effect(effect_targets[target_index]["id"])
        elif e.name == "make":
            self.do_make_effect(card, effect_targets[target_index]["id"], e.make_type)
        elif e.name == "make_from_deck":
            self.do_make_from_deck_effect(effect_targets[target_index]["id"])
        elif e.name == "riffle":
            self.do_riffle_effect(effect_targets[target_index]["id"], e.amount)
        elif e.name == "make_random_townie":
            self.do_make_random_townie_effect(e.amount)
            #todo fix hardcoding
            if e.counters == 0 and card.name == "Lute":
                card.deactivate_instrument()
        elif e.name == "mana":
            message["log_lines"].append(f"{effect_targets[target_index]['id']} gets {e.amount} mana.")
            self.do_mana_effect_on_player(card, effect_targets[target_index]["id"], e.amount)
        elif e.name == "add_tokens":
            if e.target_type == 'self_entities':
                message["log_lines"].append(f"{self.username} adds {str(e.tokens[0])} to their own entities.")
            else:
                message["log_lines"].append(f"{self.username} adds {str(e.tokens[0])} to {self.game.get_in_play_for_id(effect_targets[target_index]['id'])[0].name}.")
            self.do_add_tokens_effect(card, e, effect_targets, target_index)
        elif e.name == "add_tokens":
            if e.target_type == 'self_entities':
                message["log_lines"].append(f"{self.username} adds {str(e.tokens[0])} to their own entities.")
            else:
                message["log_lines"].append(f"{self.username} adds {str(e.tokens[0])} to {self.game.get_in_play_for_id(effect_targets[target_index]['id'])[0].name}.")
            self.do_add_tokens_effect(card, e, effect_targets, target_index)
        elif e.name == "set_can_attack":
            if e.target_type == "self_entities":
                message["log_lines"].append(f"{self.username} kets their entities attack again this turn.")
                self.do_set_can_attack_effect()           
            else:
                print(f"e.target_type {e.target_type} not supported for set_can_attack")
        elif e.name == "add_player_abilities":
            if e.target_type == "opponent":
                message["log_lines"].append(f"{self.game.opponent().username} gets {card.description}.")
            else:
                message["log_lines"].append(f"{self.username} gains {card.description}.")
            self.do_add_abilities_effect(e, card)           
        elif e.name == "add_mob_abilities":
            message["log_lines"].append(f"{self.username} adds {e.abilities[0].name} to {effect_targets[target_index]['id']} with {card.name}.")
            self.do_add_abilities_effect(e, self.game.get_in_play_for_id(effect_targets[target_index]['id'])[0])           
        elif e.name == "add_effects":
            message = self.do_add_effects_effect(card, e, effect_targets, message)           
        elif e.name == "stack_counter":
           message =  self.do_counter_card_effect(effect_targets[target_index]['id'], message)
        elif e.name == "summon_from_hand":
            message = self.do_summon_from_hand_effect(effect_targets[target_index]["id"], message)
        elif e.name == "buff_power_toughness_from_mana":
            message = self.do_buff_power_toughness_from_mana_effect(card, message)

        self.spend_mana(e.cost)
        self.hit_points -= e.cost_hp
        
        return message 

    def spend_mana(self, amount):
        amount_to_spend = amount        
        
        while self.mana > 0 and amount_to_spend > 0:
            self.mana -= 1
            amount_to_spend -= 1

        for artifact in self.artifacts:
            for effect in artifact.effects:
                if effect.name == "refresh_mana":
                    if self.mana == 0:
                        self.mana = self.max_mana
                elif effect.name == "store_mana":
                    while amount_to_spend > 0 and effect.counters > 0:                        
                        effect.counters -= 1
                        amount_to_spend -= 1

    def do_summon_from_deck_effect_on_player(self, e, effect_targets, target_index):
        if e.target_type == "self" and e.amount == 1:
            target_player = self.game.players[0]
            if target_player.username != effect_targets[target_index]["id"]:
                target_player = self.game.players[1]

            entities = []
            for c in target_player.deck:
                if c.card_type == "Mob":
                    entities.append(c)

            if len(entities) > 0:
                mob_to_summon = random.choice(entities)
                target_player.deck.remove(mob_to_summon)
                target_player.in_play.append(mob_to_summon)
                self.game.update_for_mob_changes_zones(target_player)
                mob_to_summon.turn_played = self.game.turn   
                if target_player.fast_ability():
                    mob_to_summon.abilities.append(target_player.fast_ability())          
                # todo: maybe support comes into play effects
                # target_player.target_or_do_mob_effects(mob_to_summon, {}, target_player.username)     
        elif e.target_type == "all_players" and e.amount == -1:
            entities = []
            for c in Game.all_cards():
                if c.card_type == "Mob":
                    entities.append(c)
            for p in self.game.players:
                while len(p.in_play) < 7:
                    mob_to_summon = copy.deepcopy(random.choice(entities))
                    mob_to_summon.id = self.game.next_card_id
                    self.game.next_card_id += 1
                    p.in_play.append(mob_to_summon)
                    self.game.update_for_mob_changes_zones(p)
                    mob_to_summon.turn_played = self.game.turn     
                    if p.fast_ability():
                        mob_to_summon.abilities.append(p.fast_ability())                            
                    # todo: maybe support comes into play effects
                    # p.target_or_do_mob_effects(mob_to_summon, {}, p.username)     

    def do_summon_from_deck_artifact_effect_on_player(self, e, effect_targets, target_index):
        if e.target_type == "self" and e.amount == 1:
            target_player = self.game.players[0]
            if target_player.username != effect_targets[target_index]["id"]:
                target_player = self.game.players[1]

            artifacts = []
            for c in target_player.deck:
                if c.card_type == "Artifact":
                    artifacts.append(c)

            if len(artifacts) > 0:
                artifact_to_summon = random.choice(artifacts)
                target_player.deck.remove(artifact_to_summon)
                target_player.play_artifact(artifact_to_summon)
                self.game.update_for_mob_changes_zones(target_player)
                # todo: maybe support comes into play effects for artifacts?

    def do_draw_effect_on_player(self, card, target_player_username, amount, multiplier):
        target_player = self.game.players[0]
        if target_player.username != target_player_username:
            target_player = self.game.players[1]
        if multiplier == "self_entities":
            target_player.draw(amount *len(target_player.in_play))
        else:
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
            p.max_mana = min(self.game.max_max_mana, p.max_mana)
            p.mana = min(p.mana, p.max_mana)

    def do_take_extra_turn_effect_on_player(self, target_player_username, message):
        target_player = self.game.players[0]
        if target_player.username != target_player_username:
            target_player = self.game.players[1]
        self.game.remove_temporary_tokens()
        self.game.remove_temporary_effects()
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
            for pile in [p.hand, p.played_pile]:
                pile_cards = []
                for c in pile:
                    p.deck.append(c)
                    pile_cards.append(c)
                for c in pile_cards:
                    pile.remove(c)
            random.shuffle(p.deck)
            p.draw(3)

    def do_enable_activated_effect_effect(self, card):
        # todo don't hardcode turning them all off, only needed for Arsenal because it has two equip effects
        for e in card.effects:
            if e.effect_to_activate:
                e.enabled = False
        e = copy.deepcopy(card.effects[0].effect_to_activate)
        e.id = card.id
        e.enabled = True
        card.description = e.description
        card.effects.append(e)
        card.can_activate_abilities = True

    def do_enable_equip_to_mob_effect(self, artifact_to_equip, target_mob_id):
        # todo don't hardcode turning them all off, only needed for Arsenal because it has two equip effects
        for e in artifact_to_equip.effects:
            if e.effect_to_activate:
                e.enabled = False
        e = artifact_to_equip.effects[self.card_info_to_target["effect_index"]].effect_to_activate
        new_token = copy.deepcopy(e.tokens[0])
        new_token.id = artifact_to_equip.id
        self.do_add_token_effect_on_mob(
            new_token, 
            target_mob_id
        )
        effect = CardEffect({
                    "name": "unequip_from_mob",
                    "effect_type": "activated",
                    "target_type": "self",
                    "was_added": True
                }, artifact_to_equip.id)
        artifact_to_equip.effects.append(effect)
        artifact_to_equip.description = e.description

    def do_view_hand_effect(self):
        self.card_choice_info["cards"] = copy.deepcopy(self.game.opponent().hand)
        self.card_choice_info["choice_type"] = "view_hand"

    def do_mana_effect_on_player(self, card, target_player_username, amount):
        target_player = self.game.players[0]
        if target_player.username != target_player_username:
            target_player = self.game.players[1]
        target_player.mana += amount

    def do_increase_max_mana_effect_on_player(self, target_player_username, amount, card):
        target_player = self.game.players[0]
        if target_player.username != target_player_username:
            target_player = self.game.players[1]
        old_max_mana = target_player.max_mana
        target_player.max_mana += 1
        target_player.max_mana = min(self.game.max_max_mana, target_player.max_mana)
        # in case something like Mana Shrub doesn't increase the mana
        if old_max_mana == target_player.max_mana:
            if len(card.effects) == 2 and card.effects[1].name == "decrease_max_mana":
                card.effects[1].enabled = False

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
            # dont use send_card_to_played_pile, this triggers effects
            self.game.send_card_to_played_pile(card, target_player, did_kill=False)
            if to_deck:
                for c in target_player.played_pile:
                    if c.id == card.id:
                        break
                if c:
                    target_player.played_pile.remove(c)
                    target_player.deck.append(c)
                    random.shuffle(target_player.deck)

    def do_damage_effect_on_mob(self, card, target_mob_id, amount):
        target_card, target_player = self.game.get_in_play_for_id(target_mob_id)
        if target_card.shielded:
            target_card.shielded = False
        else:
            target_card.damage += amount
            target_card.damage_to_show += amount
            if target_card.damage >= target_card.toughness_with_tokens():
                self.game.send_card_to_played_pile(target_card, target_player, did_kill=True)
                if card.has_ability("die_to_top_deck"):
                    card = None
                    for c in target_player.played_pile:
                        if c.id == target_card.id:
                            card = c
                    target_player.played_pile.remove(card)
                    target_player.deck.append(card)

    def do_heal_effect_on_mob(self, card, target_mob_id, amount):
        target_card, target_player = self.game.get_in_play_for_id(target_mob_id)
        target_card.damage -= amount
        target_card.damage = max(target_card.damage, 0)
        target_card.damage_this_turn -= amount
        target_card.damage_this_turn = max(target_card.damage_this_turn, 0)

    def do_attack_effect_on_mob(self, card, target_mob_id, amount):
        target_card, target_player = self.game.get_in_play_for_id(target_mob_id)
        self.damage(self.game.power_with_tokens(target_card, target_player))
        self.do_damage_effect_on_mob(card, target_mob_id, amount)

    def do_double_power_effect_on_mob(self, card, target_mob_id):
        target_card, target_player = self.game.get_in_play_for_id(target_mob_id)
        target_card.power += self.game.power_with_tokens(target_card, target_player)

    def do_pump_power_effect_on_mob(self, card, target_mob_id, amount, cost):
        target_card, target_player = self.game.get_in_play_for_id(target_mob_id)
        target_card.power += amount

    def do_kill_effect_on_mob(self, target_mob_id):
        target_card, target_player = self.game.get_in_play_for_id(target_mob_id)
        self.game.send_card_to_played_pile(target_card, target_player, did_kill=True)

    def do_gain_for_toughness_effect(self, target_mob_id):
        target_card, target_player = self.game.get_in_play_for_id(target_mob_id)
        target_player.hit_points += target_card.toughness_with_tokens()
        target_player.hit_points = min (30, target_player.hit_points)

    def do_take_control_effect_on_mob(self, target_mob_id):
        target_card, target_player = self.game.get_in_play_for_id(target_mob_id)
        target_player.in_play.remove(target_card)
        self.in_play.append(target_card)
        self.game.update_for_mob_changes_zones(target_player)
        self.game.update_for_mob_changes_zones(self)
        target_card.turn_played = self.game.turn
        if self.fast_ability():
            target_card.abilities.append(self.fast_ability())       
        if target_card.has_ability("Fast") or target_card.has_ability("Ambush"):
            target_card.attacked = False
        target_card.do_leaves_play_effects(target_player, did_kill=False)

    def do_take_control_effect_on_artifact(self, target_artifact_id):
        target_card, target_player = self.game.get_in_play_for_id(target_artifact_id)
        target_player.artifacts.remove(target_card)
        self.artifacts.append(target_card)
        self.game.update_for_mob_changes_zones(target_player)
        self.game.update_for_mob_changes_zones(self)
        target_card.turn_played = self.game.turn
        target_card.do_leaves_play_effects(target_player, did_kill=False)
    
    def do_unwind_effect_on_mob(self, target_mob_id):
        target_card, target_player = self.game.get_in_play_for_id(target_mob_id)
        target_player.in_play.remove(target_card)  
        target_card.do_leaves_play_effects(target_player, did_kill=False)
        if target_player.username != target_card.owner_username:
            if target_player == self:
                target_player = self.game.opponent()
            else:
                target_player = self
        new_card = self.game.factory_reset_card(target_card, target_player)
        target_player.hand.append(new_card)  

    def do_make_effect(self, card, target_player_username, make_type):
        target_player = self.game.players[0]
        if target_player.username != target_player_username:
            target_player = self.game.players[1]
        return target_player.make(1, make_type)

    def do_make_from_deck_effect(self, target_player_username):
        target_player = self.game.players[0]
        if target_player.username != target_player_username:
            target_player = self.game.players[1]
        return target_player.make_from_deck()

    def do_riffle_effect(self, target_player_username, amount):
        target_player = self.game.players[0]
        if target_player.username != target_player_username:
            target_player = self.game.players[1]
        return target_player.riffle(amount)

    def do_fetch_card_effect_on_player(self, card, target_player_username, card_type, target_restrictions, choice_type=None):
        if card_type == "Artifact":
            target_player = self.game.players[0]
            if target_player.username != target_player_username:
                target_player = self.game.players[1]
            return target_player.display_deck_artifacts(target_restrictions, choice_type)
        elif card_type == "all_cards_in_deck":
            target_player = self.game.players[0]
            if target_player.username != target_player_username:
                target_player = self.game.players[1]
            return target_player.display_deck_for_fetch()
        else:
            print("can't fetch unsupported type")
            return None

    def do_add_token_effect_on_mob(self, token, target_mob_id):
        target_card, target_player = self.game.get_in_play_for_id(target_mob_id)
        if token.multiplier and token.multiplier == "half_self_entities":
            for x in range(0, math.floor(len(self.in_play)/2)):
                target_card.tokens.append(token)
        elif token.multiplier and token.multiplier == "self_entities":
            for x in range(0, len(self.in_play)):
                target_card.tokens.append(token)
        else:
            target_card.tokens.append(token)
        if target_card.toughness_with_tokens() - target_card.damage <= 0:
            self.game.send_card_to_played_pile(target_card, target_player, did_kill=True)

    def do_set_can_attack_effect(self):
        for e in self.in_play:
            e.attacked = False

    def do_add_effect_effect_on_mob(self, effect, target_mob_id):
        target_card, target_player = self.game.get_in_play_for_id(target_mob_id)  
        target_card.effects.insert(0, effect)
        target_card.added_descriptions.append(effect.description)
        if effect.activate_on_add:
            # todo: make this generic if we add other added
            if effect.name == "increase_max_mana":
                self.do_increase_max_mana_effect_on_player(target_player.username, effect.amount)

    def do_add_abilities_effect_on_player(self, effect, player, card_id):
        player.abilities.append(effect.abilities[0])
        player.abilities[-1].id = card_id

    def do_add_abilities_effect_on_mob(self, effect, mob):
        a = copy.deepcopy(effect.abilities[0])
        mob.abilities.append(a)

    def do_add_tokens_effect(self, card, e, effect_targets, target_index):
        if effect_targets[target_index]["target_type"] == "mob":
            for token in e.tokens:
                new_token = copy.deepcopy(token)
                new_token.id = card.id
                self.do_add_token_effect_on_mob(
                    new_token, 
                    effect_targets[target_index]["id"]
                )
        else:  # e.target_type == "self_entities"
            for token in e.tokens:
                new_token = copy.deepcopy(token)
                new_token.id = card.id
                for mob in self.in_play:
                    self.do_add_token_effect_on_mob(
                        new_token, 
                        mob.id
                    )

    def do_remove_tokens_effect(self, card, e):
        if e.target_type == "self_entities":
            for mob in self.in_play:
                tokens_to_keep = []
                for token in mob.tokens:
                    if token.id != card.id:
                        tokens_to_keep.append(token)
                mob.tokens = tokens_to_keep

    def remove_abilities(self, card, e):
        ability_to_remove = None
        # todo this should  loop over the abilities in e, in the future there could be more than 1 ability to remove
        for a in self.abilities:
            if a.id == card.id:
                ability_to_remove = a
        self.abilities.remove(a)

    def do_add_effects_effect(self, card, e, effect_targets, message):
        if e.target_type == "self_entities":
            for c in self.in_play:
                for effect_effect in e.effects:
                    effect_effect.enabled = False
                    self.do_add_effect_effect_on_mob(
                        effect_effect, 
                        c.id
                    )
        elif e.target_type == "opponents_mob":
                for idx, effect_effect in enumerate(e.effects):
                    target_card = self.game.get_in_play_for_id(effect_targets[idx]['id'])[0]            
                    if effect_effect.name == "take_control":
                        message["log_lines"].append(f"{self.username} takes control of {target_card.name} with {card.name}.")
                        self.do_add_effect_effect_on_mob(
                            effect_effect, 
                            target_card.id
                        )
                        self.do_take_control_effect_on_mob(target_card.id)
        return message

    def do_add_abilities_effect(self, e, card):
        if e.target_type == "new_self_entities":
            for card in self.in_play:
                for a in e.abilities:
                    if a.descriptive_id == "Fast":
                        card.abilities.append(a) 
            self.do_add_abilities_effect_on_player(
                e, 
                self,
                card.id                
            )
        elif e.target_type in ["mob", "opponents_mob", "self_mob"]:
            self.do_add_abilities_effect_on_mob(
                e, 
                card
            )
        elif e.target_type == "opponent":
            self.do_add_abilities_effect_on_player(
                e, 
                self.game.opponent(),
                card.id
            )
        elif e.target_type == "self":
            self.do_add_abilities_effect_on_player(
                e, 
                self,
                card.id
            )

    def do_make_token_effect(self, e, card):
        for x in range(0, e.amount):
            if len(self.in_play) == 7:
                return
            card_to_create = None
            card_name = e.card_name
            if len(e.card_names) > 0:
                card_name = e.card_names[card.level]
            for card in Game.all_cards():
                if card.name == card_name:
                    card_to_create = card
            new_card = copy.deepcopy(card_to_create)
            self.in_play.append(new_card)
            self.game.update_for_mob_changes_zones(self)
            new_card.id = self.game.next_card_id
            new_card.turn_played = self.game.turn
            new_card.owner_username = self.username
            self.game.next_card_id += 1

    def do_create_card_effect(self, e):
        for x in range(0, e.amount):
            if len(self.hand) == 10:
                return
            card_to_create = None
            for card in Game.all_cards():
                if card.name == e.card_name:
                    card_to_create = card
            self.hand.append(copy.deepcopy(card_to_create))
            self.hand[-1].id = self.game.next_card_id
            self.game.next_card_id += 1

    def do_make_random_townie_effect(self, amount):
        if len(self.hand) >= 10:
            return
        townies = []
        for c in Game.all_cards():
            for a in c.abilities:
                if a.descriptive_id == "Townie":
                    townies.append(c)
        t = random.choice(townies)
        self.add_to_deck(t.name, 1, add_to_hand=True)


    def make(self, amount, make_type):
        '''
            Make a spell or mob.
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

        requiredMobCost = None
        if self.game.turn <= 10 and make_type == "Mob":
            requiredMobCost = math.floor(self.game.turn / 2) + 1

        all_cards = Game.all_cards()
        banned_cards = ["Make Spell", "Make Spell+", "Make Mob", "Make Mob+"]
        card1 = None 
        while not card1 or card1.name in banned_cards or card1.card_type != make_type or (requiredMobCost and make_type == "Mob" and card1.cost != requiredMobCost) or (self.race != None and card1.race != None and self.race not in [card1.race, f"{card1.race}_{card1.card_class}"]):
            card1 = random.choice(all_cards)
        card2 = None
        while not card2 or card2.name in banned_cards or card2.card_type != make_type or card2 == card1 or (self.race != None and card2.race != None and self.race not in [card2.race, f"{card2.race}_{card2.card_class}"]):
            card2 = random.choice(all_cards)
        card3 = None
        while not card3 or card3.name in banned_cards or card3.card_type != make_type or card3 in [card1, card2] or (self.race != None and card3.race != None and self.race not in [card3.race, f"{card3.race}_{card3.card_class}"]):
            card3 = random.choice(all_cards)
        self.card_choice_info = {"cards": [card1, card2, card3], "choice_type": "make"}
        
        # todo: hax for Make Artifact
        if make_type == "Artifact":
            for c in self.card_choice_info["cards"]:
                c.cost = 3

    def make_from_deck(self):
        '''
            Make a spell or mob from the player's deck.
        '''
        card1 = None 
        if len(self.deck) > 0:
            while not card1:
                card1 = random.choice(self.deck)
        if len(self.deck) > 1:
            card2 = None
            while not card2 or card2 == card1:
                card2 = random.choice(self.deck)
        if len(self.deck) > 2:
            card3 = None
            while not card3 or card3 in [card1, card2]:
                card3 = random.choice(self.deck)
        self.card_choice_info = {"cards": [card1, card2, card3], "choice_type": "make_from_deck"}

    def riffle(self, amount):
        all_cards = Game.all_cards()
        top_cards = []
        for card in self.deck:
            if len(top_cards) < amount:
                top_cards.append(card)
        self.card_choice_info = {"cards": top_cards, "choice_type": "riffle"}

    def display_deck_artifacts(self, target_restrictions, choice_type):
        all_cards = Game.all_cards()
        artifacts = []
        for card in self.deck:
            if card.card_type == "Artifact":
                if len(target_restrictions) == 0 or \
                    (list(target_restrictions[0].keys())[0] == "needs_weapon" and card.has_ability("Weapon")) or \
                    (list(target_restrictions[0].keys())[0] == "needs_instrument" and card.has_ability("Instrument")):
                    artifacts.append(card)
        if len(artifacts) > 0:
            self.card_choice_info = {"cards": artifacts, "choice_type": choice_type}
        else:
            self.reset_card_choice_info()

    def display_deck_for_fetch(self):
        all_cards = Game.all_cards()
        self.card_choice_info = {"cards": self.deck, "choice_type": "fetch_into_hand"}

    def artifact_in_play(self, card_id):
        for card in self.artifacts:
            if card.id == card_id:
                return card
        return None

    def can_activate_artifact(self, card_id):
        for card in self.artifacts:
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

    def in_play_mob_is_selected(self, card_id):
        for c in self.in_play:
            if c.id == card_id and c.id == self.card_info_to_target["card_id"]:
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

    def initiate_play_card(self, card_id, message):
        card = None
        for c in self.hand:
            if c.id == card_id:
                card = c
        if card.cost > self.current_mana():
            print(f"card costs too much - costs {card.cost}, mana available {self.current_mana()}")
            return None
        self.reset_card_info_to_target()
        self.hand.remove(card)
        self.spend_mana(card.cost)

        self.game.actor_turn += 1
        self.game.spell_stack.append([copy.deepcopy(message), card.as_dict()])
        self.game.unset_clickables(message["move_type"])
        self.game.set_clickables()

        if not self.game.current_player().has_instants():
            return self.play_card(card.id, message)

        message["log_lines"].append(f"{self.username} starts to play {card.name}.")

        # todo rope
        return message

    def do_summon_from_hand_effect(self, target_username, message):
        target = self.game.players[0]
        caster = self.game.players[1]
        if target.username != target_username:
            target = self.game.players[1]
            caster = self.game.players[0]
        nonspells = []
        for card in target.hand:
            if card.card_type != "Spell":
                nonspells.append(card)
        if len(nonspells) > 0:
            to_summon = random.choice(nonspells)
            target.hand.remove(to_summon)
            message = self.play_mob_or_artifact(to_summon, message, False)
            message["log_lines"].append(f"{to_summon.name} was summoned for {caster.username}.")
        return message

    def do_buff_power_toughness_from_mana_effect(self, card, message):
        mana_count = self.current_mana()
        self.spend_mana(self.current_mana())
        card.power += mana_count
        card.toughness += mana_count
        message["log_lines"].append(f"{card.name} is now {card.power}/{card.toughness}.")
        return message

    def play_card(self, card_id, message):
        self.game.actor_turn += 1
        to_resolve = self.game.spell_stack.pop()
        spell_to_resolve = to_resolve[0]
        spell_to_resolve["log_lines"] = []
        card = Card(to_resolve[1])

        for e in self.in_play:
            for idx, effect in enumerate(e.effects_triggered()):
                if effect.trigger == "friendly_card_played" and effect.target_type == "this":
                    self.do_add_tokens_effect(e, effect, {idx: {"id": e.id, "target_type":"mob"}}, idx)

        spell_to_resolve["log_lines"].append(f"{self.username} plays {card.name}.")

        spell_to_resolve = self.play_mob_or_artifact(card, spell_to_resolve)

        if card.card_type == "Mob" and card.has_ability("Shield"):
            card.shielded = True

        if len(card.effects) > 0 and card.card_type != "Mob":
            if not "effect_targets" in spell_to_resolve:
                spell_to_resolve["effect_targets"] = []
           
            for idx, e in enumerate(card.effects_spell() + card.effects_enter_play()):
                if e.target_type == "self":           
                    spell_to_resolve["effect_targets"].append({"id": spell_to_resolve["username"], "target_type":"player"})
                elif e.target_type == "opponent":          
                    spell_to_resolve["effect_targets"].append({"id": self.game.opponent().username, "target_type":"player"})
                elif e.target_type == "all_players" or e.target_type == "all_entities" or e.target_type == "self_entities" or e.target_type == "all":          
                    spell_to_resolve["effect_targets"].append({"target_type": e.target_type})
                elif e.target_type == "all_cards_in_deck":           
                    spell_to_resolve["effect_targets"].append({"target_type": "player", "id": self.username})
                spell_to_resolve = self.do_card_effect(card, e, spell_to_resolve, spell_to_resolve["effect_targets"], idx)
            if len(spell_to_resolve["effect_targets"]) == 0:
                spell_to_resolve["effect_targets"] = None

            if len(card.effects) == 2:
                if card.effects[1].name == "improve_damage_when_cast":
                    # hack for Rolling Thunder
                    card.effects[0].amount += 1
                if card.effects[1].name == "improve_effect_when_cast":
                    # hack for Tame Shop Demon"
                    card.level += 1
                    card.level = min(card.level, len(card.effects[0].card_names)-1)

        if card.card_type == "Spell":
            self.played_pile.append(card)            

        spell_to_resolve["card_name"] = card.name
        spell_to_resolve["played_card"] = True
        spell_to_resolve["was_countered"] = False
        spell_to_resolve["show_spell"] = card.as_dict()

        return spell_to_resolve

    def play_mob_or_artifact(self, card, spell_to_resolve, do_effects=True):
        if card.card_type == "Mob":
            if len(card.effects) > 0 and do_effects:
                self.target_or_do_mob_effects(card, spell_to_resolve, spell_to_resolve["username"])
            for c in self.in_play:
                if len(c.effects_triggered()) > 0:
                    # Spouty Gas Ball code
                    if c.effects_triggered()[0].trigger == "play_friendly_mob":
                        if c.effects_triggered()[0].name == "damage" and c.effects_triggered()[0].target_type == "opponents_mob_random":
                            if len(self.game.opponent().in_play) > 0:
                                mob = random.choice(self.game.opponent().in_play)
                                if mob.shielded:
                                    mob.shielded = False
                                else:
                                    mob.damage += c.effects_triggered()[0].amount
                                    mob.damage_this_turn += c.effects_triggered()[0].amount
                                    mob.damage_to_show += c.effects_triggered()[0].amount
                                    if mob.damage >= mob.toughness_with_tokens():
                                        self.game.send_card_to_played_pile(mob, self.game.opponent(), did_kill=True)
                                spell_to_resolve["log_lines"].append(f"{c.name} deal {c.effects_triggered()[0].amount} damage to {mob.name}.")
            self.play_mob(card)
        elif card.card_type == "Artifact":
            self.play_artifact(card)
            if card.has_ability("Slow Artifact"):
                card.effects_exhausted.append(card.effects[0].name)
        return spell_to_resolve

    def play_mob(self, card):
        self.in_play.append(card)
        self.game.update_for_mob_changes_zones(self)

        if self.fast_ability():
            card.abilities.append(self.fast_ability())          
        card.turn_played = self.game.turn

    def play_artifact(self, artifact):
        self.artifacts.append(artifact)
        artifact.turn_played = self.game.turn
        # self.game.update_for_mob_changes_zones(self)
        # self.update_for_mob_changes_zones(self.game.opponent())        

    def fast_ability(self):
        for a in self.abilities:
            if a.descriptive_id == "Fast":
                new_a = copy.deepcopy(a)
                return a
        return None 

    def cant_die_ability(self):
        for a in self.abilities:
            if a.descriptive_id == "Can't Die":
                return a
        return None 

    def target_or_do_mob_effects(self, card, message, username, is_activated_effect=False):
        effects = card.effects_enter_play()
        if is_activated_effect:
            effects = card.effects_activated()
        if len(effects) > 0:
            if effects[0].target_type == "any":
                self.card_info_to_target["card_id"] = card.id
                if is_activated_effect:
                    self.card_info_to_target["effect_type"] = "mob_activated"
                else:
                    self.card_info_to_target["effect_type"] = "mob_comes_into_play"
            elif effects[0].target_type in ["mob"]:
                if self.game.has_targets_for_mob_effect(effects[0].target_restrictions):
                    self.card_info_to_target["card_id"] = card.id
                    if is_activated_effect:
                        self.card_info_to_target["effect_type"] = "mob_activated"
                    else:
                        self.card_info_to_target["effect_type"] = "mob_comes_into_play"
            elif effects[0].target_type in ["opponents_mob"]:
                if self.game.has_targets_for_opponents_mob_effect(effects[0].target_restrictions):
                    self.card_info_to_target["card_id"] = card.id
                    if is_activated_effect:
                        self.card_info_to_target["effect_type"] = "mob_activated"
                    else:
                        self.card_info_to_target["effect_type"] = "mob_comes_into_play"
            elif effects[0].target_type in ["self_mob"]:
                if self.game.has_targets_for_self_mob_effect(effects[0].target_restrictions):
                    self.card_info_to_target["card_id"] = card.id
                    if is_activated_effect:
                        self.card_info_to_target["effect_type"] = "mob_activated"
                    else:
                        self.card_info_to_target["effect_type"] = "mob_comes_into_play"
            else:
                for idx, e in enumerate(effects):
                    if e.target_type == "opponents_mob_random" and len(self.game.opponent().in_play) == 0:
                        continue
                    # todo think about this weird rpeated setting of effect_targets in message
                    if not "effect_targets" in message:
                        effect_targets = []
                        if e.target_type == "self" or e.name == "fetch_card":  
                            effect_targets.append({"id": username, "target_type":"player"})
                        elif e.target_type == "this":           
                            effect_targets.append({"id": card.id, "target_type":"mob"})
                        elif e.target_type == "all_players" or e.target_type == "all_entities" or e.target_type == "self_entities":           
                            effect_targets.append({"target_type": e.target_type})
                        elif e.target_type == "opponents_mob_random":           
                            effect_targets.append({"id": random.choice(self.game.opponent().in_play).id, "target_type":"mob"})
                        message["effect_targets"] = effect_targets
                    message = self.do_card_effect(card, e, message, message["effect_targets"], idx)
        return message

    def resolve_mob_effect(self, card_id, message):
        card = None
        for c in self.in_play:
            if c.id == card_id:
                card = c
        for idx, e in enumerate(card.effects):
            if not "effect_targets" in message:
                effect_targets = []
                if e.target_type == "self":           
                    effect_targets.append({"id": message["username"], "target_type":"player"})
                message["effect_targets"] = effect_targets
            message = self.do_card_effect(card, e, message, message["effect_targets"], idx)
        
        self.reset_card_info_to_target()
        return message

    def do_counter_card_effect(self, card_id, message):
        self.game.actor_turn += 1
        stack_spell = None
        for spell in self.game.spell_stack:
            if spell[1]["id"] == card_id:
                stack_spell = spell
                break

        self.game.spell_stack.remove(stack_spell)
        spell_to_resolve = message
        spell_to_resolve["log_lines"] = []
        card = Card(stack_spell[1])
        self.game.send_card_to_played_pile(card, self.game.current_player(), did_kill=False)
        spell_to_resolve["log_lines"].append(f"{card.name} was countered by {self.game.opponent().username}.")
        spell_to_resolve["card_name"] = card.name
        return spell_to_resolve

    def modify_new_card(self, game, card):
        if card.card_type == "Spell":            
            if 'spells_cost_more' in game.global_effects:
                card.cost += game.global_effects.count('spells_cost_more')
            if 'spells_cost_less' in game.global_effects:
                card.cost -= game.global_effects.count('spells_cost_less')
                card.cost = max(0, card.cost)
        elif card.card_type == "Mob":            
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

    def has_brarium(self):
        for a in self.artifacts:
            if a.name == "Brarium":
                return True
        return False

    def start_turn(self, message):
        self.game.turn_start_time = datetime.datetime.now()
        self.game.show_rope = False

        if self.game.turn != 0:
            draw_count = self.game.cards_each_turn + self.game.global_effects.count("draw_extra_card")
            for a in self.artifacts:
                for e in a.effects_triggered():
                    if e.name == "draw" and e.trigger == "start_turn":
                        draw_count += e.amount
            if self.has_brarium():
                self.do_make_from_deck_effect(self.username)
                draw_count -= 1
            if draw_count > 0:
                self.draw(draw_count)
        self.max_mana += 1
        self.max_mana = min(self.game.max_max_mana, self.max_mana)
        if not self.game.keep_excess_mana:
            for r in self.artifacts:
                for effect in r.effects_triggered():
                    if effect.name == "store_mana" and self.mana > 0:
                        counters = effect.counters or 0
                        counters += self.mana
                        effect.counters = min(3, counters)
            self.mana = 0
        self.mana += self.max_mana
        self.mana = min(self.game.max_max_mana, self.mana)

        for card in self.in_play:
            if card.has_ability("Fade"):
                token = {
                    "turns": -1,
                    "power_modifier": -1,
                    "toughness_modifier": -1
                }
                self.do_add_token_effect_on_mob(CardToken(token), card.id)

            if not self.game.is_under_ice_prison():
                card.attacked = False
            card.can_activate_abilities = True

            for effect in card.effects_triggered():
                if effect.trigger == "start_turn":
                    if effect.name == "damage" and effect.target_type == "self":
                        self.game.current_player().damage(effect.amount)
                        message["log_lines"].append(f"{self.game.current_player().username} takes {effect.amount} damage from {card.name}.")
                    elif effect.name == "take_control" and effect.target_type == "opponents_mob_random":
                        if len(self.game.opponent().in_play) > 0:
                            mob_to_target = random.choice(self.game.opponent().in_play)
                            self.game.current_player().do_take_control_effect_on_mob(mob_to_target.id)
                            message["log_lines"].append(f"{self.game.current_player().username} takes control of {mob_to_target.name}.")
                    elif effect.name == "rebirth":
                        # this is handled at top of def
                        pass
                    else:
                        print(f"unsupported start_turn triggered effect {effect}")

        for r in self.artifacts:
            r.can_activate_abilities = True
            r.effects_exhausted = {}
            for effect in r.effects_triggered():
                if effect.trigger == "start_turn":
                    if effect.name == "gain_hp_for_hand":
                        gained = 0
                        to_apply = max(len(self.hand) - 5, 0)
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
                self.card_choice_info = {"cards": entities_to_select_from, "choice_type": "select_mob_for_ice_prison"}
        return message

    def controls_artifact(self, card_id):
        for c in self.artifacts:
            if c.id == card_id:
                return True
        return False

    def controls_mob(self, card_id):
        for c in self.in_play:
            if c.id == card_id:
                return True
        return False

    def select_artifact(self, card_id, effect_index):
        #todo - we only support multi-effect artifacts, not entities or spells yet
        self.card_info_to_target["effect_index"] = effect_index
        for c in self.artifacts:
            if c.id == card_id:
                self.card_info_to_target["card_id"] = c.id
                self.card_info_to_target["effect_type"] = "artifact_activated"

    def selected_artifact(self):
        for artifact in self.artifacts:
            if artifact.id == self.card_info_to_target["card_id"]:
                return artifact

    def selected_mob(self):
        for mob in self.in_play:
            if mob.id == self.card_info_to_target["card_id"]:
                return mob

    def selected_spell(self):
        for card in self.hand:
            if card.id == self.card_info_to_target["card_id"]:
                return card

    def select_in_play(self, card_id):
        for c in self.in_play:
            if c.id == card_id:
                self.card_info_to_target["card_id"] = c.id
                self.card_info_to_target["effect_type"] = "mob_at_ready"

    def reset_card_info_to_target(self):
        self.card_info_to_target = {"card_id": None, "effect_type": None, "effect_index": None}

    def reset_card_choice_info(self):
        self.card_choice_info = {"cards": [], "choice_type": None}

    def has_guard(self):
        for c in self.in_play:
            if c.has_ability("Guard") and not c.has_ability("Lurker"):
                return True
        return False

    def has_instrument(self):
        for c in self.artifacts:
            if c.has_ability("Instrument"):
                return True
        return False

    def can_summon(self):
        for a in self.abilities:
            if a.descriptive_id == "Can't Summon":
                return False
        if len(self.in_play) == 7:
            return False
        return True

    def can_play_artifact(self):
        if len(self.artifacts) == 3:
            return False
        return True

    def set_targets_for_selected_mob(self):
        # todo artifacts?
        target_type = None
        target_restrictions = None
        card = self.selected_mob()
        if self.card_info_to_target["effect_type"] == "mob_comes_into_play":
                target_type = card.effects[0].target_type
                target_restrictions = card.effects[0].target_restrictions
        elif self.card_info_to_target["effect_type"] == "mob_activated":
            target_type = card.effects_activated()[0].target_type
            target_restrictions = card.effects_activated()[0].target_restrictions
        self.game.set_targets_for_target_type(target_type, target_restrictions)

    def do_attack_abilities(self, attacking_card):
        if attacking_card.has_ability("DamageDraw"):
            ability = None
            for a in attacking_card.abilities:
                if a.descriptive_id == "DamageDraw":
                    ability = a
            if ability.target_type == "opponent":
                self.game.opponent().draw(ability.amount)
            else:
                self.draw(ability.amount)

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

    def deactivate_equipment(self, card, equipped_mob):
        token_to_remove = None
        for t in equipped_mob.tokens:
            if t.id == card.id:
                token_to_remove = t
        oldToughness = equipped_mob.toughness_with_tokens() - equipped_mob.damage
        equipped_mob.tokens.remove(token_to_remove)
        newToughness = equipped_mob.toughness_with_tokens() - equipped_mob.damage
        if newToughness <= 0:
            toughness_change_from_tokens = oldToughness - newToughness
            equipped_mob.damage -= toughness_change_from_tokens
            equipped_mob.damage_this_turn = max(0, equipped_mob.damage_this_turn-toughness_change_from_tokens)

        idx_to_replace = None
        for idx, r in enumerate(self.artifacts):
            if r.id == card.id:
                idx_to_replace = idx

        old_turn_played = card.turn_played
        new_card = self.game.factory_reset_card(card, self)
        new_card.turn_played = old_turn_played
        self.artifacts[idx_to_replace] = new_card

class Card:

    def __init__(self, info):
        self.id = info["id"] if "id" in info else -1

        self.abilities = [CardAbility(a, idx) for idx, a in enumerate(info["abilities"])] if "abilities" in info and info["abilities"] else []
        self.added_descriptions = info["added_descriptions"] if "added_descriptions" in info else []
        self.attacked = info["attacked"] if "attacked" in info else False
        self.can_activate_abilities = info["can_activate_abilities"] if "can_activate_abilities" in info else True
        self.can_be_clicked = info["can_be_clicked"] if "can_be_clicked" in info else False
        self.card_type = info["card_type"] if "card_type" in info else "Mob"
        self.card_class = info["class"] if "class" in info else None
        self.cost = info["cost"] if "cost" in info else 0
        self.damage = info["damage"] if "damage" in info else 0
        self.damage_this_turn = info["damage_this_turn"] if "damage_this_turn" in info else 0
        self.damage_to_show = info["damage_to_show"] if "damage_to_show" in info else 0
        self.effects = [CardEffect(e, self.id) for _, e in enumerate(info["effects"])] if "effects" in info else []
        self.effects_can_be_clicked = info["effects_can_be_clicked"] if "effects_can_be_clicked" in info else []
        self.effects_exhausted = info["effects_exhausted"] if "effects_exhausted" in info else []
        self.description = info["description"] if "description" in info else None
        self.global_effect = info["global_effect"] if "global_effect" in info else None
        self.image = info["image"] if "image" in info else None
        self.is_token = info["is_token"] if "is_token" in info else False
        self.level = info["level"] if "level" in info else None
        self.name = info["name"]
        self.needs_targets = info["needs_targets"] if "needs_targets" in info else False
        self.original_description = info["original_description"] if "original_description" in info else None
        # probably bugs WRT Mind Manacles
        self.owner_username = info["owner_username"] if "owner_username" in info else None
        self.power = info["power"] if "power" in info else None
        self.race = info["race"] if "race" in info else None
        self.shielded = info["shielded"] if "shielded" in info else False
        self.tokens = [CardToken(t) for t in info["tokens"]] if "tokens" in info else []
        self.toughness = info["toughness"] if "toughness" in info else None
        self.turn_played = info["turn_played"] if "turn_played" in info else -1

    def __repr__(self):
        return f"{self.name} ({self.race}, {self.cost}) - {self.power}/{self.toughness}\n \
                 abilities: {self.abilities}, tokens: {self.tokens}\n \
                 added_descriptions: {self.added_descriptions}\n \
                 attacked: {self.attacked} card_class: {self.card_class}\n \
                 can_activate_abilities: {self.can_activate_abilities})\n \
                 can_be_clicked: {self.can_be_clicked}\n \
                 card_type: {self.card_type}\n \
                 damage: {self.damage}\n \
                 damage_this_turn: {self.damage_this_turn}\n \
                 damage_to_show: {self.damage_to_show}\n \
                 description: {self.description}\n \
                 effects: {self.effects}\n \
                 effects_can_be_clicked: {self.effects_can_be_clicked}\n \
                 effects_exhausted: {self.effects_exhausted}\n \
                 id: {self.id}, turn played: {self.turn_played}\n \
                 image: {self.image}\n \
                 level: {self.level}\n \
                 needs_targets: {self.needs_targets} is_token: {self.is_token} shielded: {self.shielded}\n \
                 original_description: {self.original_description}\n \
                 owner_username: {self.owner_username}"
 

    def as_dict(self):
        return {
            "abilities": [a.as_dict() for a in self.abilities],
            "added_descriptions": self.added_descriptions,
            "attacked": self.attacked,
            "can_activate_abilities": self.can_activate_abilities,
            "can_be_clicked": self.can_be_clicked,
            "card_class": self.card_class,
            "card_type": self.card_type,
            "cost": self.cost,
            "damage": self.damage,
            "damage_this_turn": self.damage_this_turn,
            "damage_to_show": self.damage_to_show,
            "description": self.description,
            "effects": [e.as_dict() for e in self.effects],
            "effects_can_be_clicked": self.effects_can_be_clicked,
            "effects_exhausted": self.effects_exhausted,
            "global_effect": self.global_effect,
            "id": self.id,
            "image": self.image,
            "is_token": self.is_token,
            "level": self.level,
            "name": self.name,
            "needs_targets": self.needs_targets,
            "original_description": self.original_description,
            "owner_username": self.owner_username,
            "power": self.power,
            "race": self.race,
            "shielded": self.shielded,
            "tokens": [t.as_dict() for t in self.tokens] if self.tokens else [],
            "toughness": self.toughness,
            "turn_played": self.turn_played,
        }

    def enabled_activated_effects(self):
        enabled_effects = []
        for e in self.effects_activated():
            if e.enabled:
               enabled_effects.append(e)
        return enabled_effects

    def deactivate_weapon(self):
        # todo: don't hardcode for dagger
        ability_to_remove = None
        for a in self.effects:
            if a.effect_type == "activated" and a.id == self.id:
                ability_to_remove = a
        self.effects.remove(ability_to_remove)
        for a in self.effects:
            if a.effect_type == "activated":
                a.enabled = True
        self.description = self.original_description
        # self.can_activate_abilities = True        

    def deactivate_instrument(self):
        # todo: don't hardcode for Lute
        ability_to_remove = None
        for a in self.effects:
            if a.effect_type == "activated" and a.id == self.id:
                ability_to_remove = a
        self.effects.remove(ability_to_remove)
        for a in self.effects:
            if a.effect_type == "activated":
                a.enabled = True
                break
        self.description = self.original_description
        # self.can_activate_abilities = True        

    def needs_activated_effect_targets(self):
        for e in self.enabled_activated_effects():
            if e.target_type in ["any", "any_enemy", "mob", "opponents_mob", "self_mob", "artifact", "any_player"]:
                return True
        return False 

    def needs_targets_for_spell(self):
        if len(self.effects) == 0:
            return False
        e = self.effects[0]
        if e.target_type in ["any", "any_enemy", "mob", "opponents_mob", "self_mob", "artifact", "any_player", "being_cast", "being_cast_artifact", "being_cast_spell", "being_cast_mob"]:
            return True
        return False 

    def needs_mob_target(self):
        if len(self.effects) == 0:
            return False
        e = self.effects[0]
        if e.target_type  in ["mob", "opponents_mob", "self_mob"]:
            return True
        return False

    def can_target_entities(self):
        if len(self.effects) == 0:
            return False
        e = self.effects[0]
        if e.target_type  in ["mob", "opponents_mob", "any_enemy", "any", "self_mob"]:
            return True
        return False

    def can_target_opponent(self):
        if len(self.effects) == 0:
            return False
        e = self.effects[0]
        if e.target_type in ["any_player", "any_enemy", "opponent", "any"]:
            return True
        return False

    def can_target_self(self):
        if len(self.effects) == 0:
            return False
        e = self.effects[0]
        if e.target_type in ["any_player", "any_self", "self", "any"]:
            return True
        return False

    def needs_artifact_target(self):
        if len(self.effects) == 0:
            return False
        e = self.effects[0]
        if e.target_type == "artifact":
            return True
        return False

    def needs_stack_target(self):
        if len(self.effects) == 0:
            return False
        e = self.effects[0]
        if e.target_type == "being_cast_mob" or e.target_type == "being_cast_artifact" or e.target_type == "being_cast_spell" or e.target_type == "being_cast":
            return True
        return False

    def has_stack_target(self, game):
        e = self.effects[0]
        for spell in game.spell_stack:
            card = Card(spell[1])
            if e.target_type == "being_cast":
                return True
            if e.target_type == "being_cast_mob" and card.card_type == "Mob":
                return True
            if e.target_type == "being_cast_spell" and card.card_type == "Spell":
                return True
            if e.target_type == "being_cast_artifact" and card.card_type == "Artifact":
                return True
        return False

    def needs_mob_target_for_activated_effect(self, index=0):
        e = self.enabled_activated_effects()[index]
        if e.target_type in ["mob", "opponents_mob", "self_mob"]:
            return True
        return False

    def needs_and_doesnt_have_legal_attack_targets(self, game):
        if not self.has_ability("multi_mob_attack"):  
            return False                  
        return not game.has_targets_for_attack_effect(self.effects[0])

    def needs_self_mob_target_for_activated_effect(self, index=0):
        e = self.enabled_activated_effects()[index]
        if e.target_type in ["self_mob"]:
            return True
        return False

    def needs_target_for_activated_effect(self, effect_index):
        e = self.enabled_activated_effects()[effect_index]
        # todo: Artifact target_type because of fetch_card, maybe refactor:
        if e.target_type in ["self", "opponent", "Artifact", "all"]: 
            return False
        return True

    def toughness_with_tokens(self):
        toughness = self.toughness
        for t in self.tokens:
            toughness += t.toughness_modifier
        return toughness

    def has_ability(self, ability_name):
        for a in self.abilities:
            if a.descriptive_id == ability_name and a.enabled:
                return True
        return False

    def effect_with_trigger(self, trigger_name):
        for e in self.effects_triggered():
            if e.trigger == trigger_name:
                return e
        return None

    def do_changes_sides_effects(self, player):
        equip_effect_id = None
        artifact_ids = [r.id for r in player.artifacts]
        for token in self.tokens:
            if token.id in artifact_ids:                
                for r in player.artifacts:
                    if token.id == r.id:
                        player.deactivate_equipment(r, self)

        for e in self.effects_leave_play():
            if e.name == "decrease_max_mana" and e.enabled:
                player.max_mana -= e.amount
                player.mana = min(player.max_mana, player.mana)

    def do_leaves_play_effects(self, player, did_kill=True):
        equip_effect_id = None
        artifact_ids = [r.id for r in player.artifacts]
        for token in self.tokens:
            if token.id in artifact_ids:                
                for r in player.artifacts:
                    if token.id == r.id:
                        player.deactivate_equipment(r, self)

        for e in self.effects_leave_play():
            if e.name == "decrease_max_mana" and e.enabled:
                player.max_mana -= e.amount
                player.mana = min(player.max_mana, player.mana)
            if e.name == "damage" and e.target_type == "opponent":
                player.game.opponent().damage(e.amount)                                
            if e.name == "damage" and e.target_type == "self":
                player.damage(e.amount)                
            if e.name == "make_token" and did_kill:
                player.do_make_token_effect(e, self)
            if e.name == "remove_tokens":
                player.do_remove_tokens_effect(self, e)
            if e.name == "remove_player_abilities":
                player.remove_abilities(self, e)

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

    def effects_enabled(self):
        return [e for e in self.effects if e.enabled == True]

    def effect_for_id(self, effect_id):
        for e in self.effects:
            if e.id == effect_id:
                return e


class CardEffect:
    def __init__(self, info, effect_id):
        self.id = effect_id

        self.abilities = [CardAbility(a, idx) for idx, a in enumerate(info["abilities"])] if "abilities" in info else []
        self.activate_on_add = info["activate_on_add"] if "activate_on_add" in info else False
        self.amount = info["amount"] if "amount" in info else None
        self.card_name = info["card_name"] if "card_name" in info else None
        self.card_names = info["card_names"] if "card_names" in info else []
        self.counters = info["counters"] if "counters" in info else 0
        self.cost = info["cost"] if "cost" in info else 0
        self.cost_hp = info["cost_hp"] if "cost_hp" in info else 0
        self.description = info["description"] if "description" in info else None
        self.effects = [CardEffect(e, idx) for idx, e in enumerate(info["effects"])] if "effects" in info else []
        self.effect_to_activate = CardEffect(info["effect_to_activate"], info["effect_to_activate"]["id"] if "id" in info["effect_to_activate"] else 0) if "effect_to_activate" in info and info["effect_to_activate"] else None
        self.effect_type = info["effect_type"] if "effect_type" in info else None
        self.enabled = info["enabled"] if "enabled" in info else True
        self.image = info["image"] if "image" in info else None
        self.make_type = info["make_type"] if "make_type" in info else None
        self.multiplier = info["multiplier"] if "multiplier" in info else None
        self.name = info["name"] if "name" in info else None 
        self.power = info["power"] if "power" in info else None
        self.sacrifice_on_activate = info["sacrifice_on_activate"] if "sacrifice_on_activate" in info else False
        self.targetted_this_turn = info["targetted_this_turn"] if "targetted_this_turn" in info else []
        self.target_restrictions = info["target_restrictions"] if "target_restrictions" in info else []
        self.target_type = info["target_type"] if "target_type" in info else None
        self.tokens = [CardToken(t) for t in info["tokens"]] if "tokens" in info else []
        self.toughness = info["toughness"] if "toughness" in info else None
        self.trigger = info["trigger"] if "trigger" in info else None
        self.turns = info["turns"] if "turns" in info else 0
        self.was_added = info["was_added"] if "was_added" in info else False

    def __repr__(self):
        return f"\
            id: {self.id} name: {self.name} power: {self.power} target_restrictions: {self.target_restrictions}]n \
            trigger: {self.trigger} toughness: {self.toughness} multiplier: {self.multiplier}\n \
            amount: {self.amount} cost: {self.cost} targetted_this_turn: {self.targetted_this_turn}\n \
            description: {self.description} cost_hp: {self.cost_hp}\n \
            target_type: {self.target_type} name: {self.card_name} image: {self.image} card_names: {self.card_names} \n \
            make_type: {self.make_type} tokens: {self.tokens} turns: {self.turns}\n \
            sacrifice_on_activate: {self.sacrifice_on_activate} abilities: {self.abilities}\n \
            effect_type: {self.effect_type} effects: {self.effects} activate_on_add: {self.activate_on_add} \
            effect_to_activate: {self.effect_to_activate} enabled: {self.enabled} counters: {self.counters} was_added: {self.was_added}"

    def as_dict(self):
        return {
            "abilities": [a.as_dict() for a in self.abilities] if self.abilities else [],
            "activate_on_add": self.activate_on_add,
            "amount": self.amount,
            "card_name": self.card_name,
            "card_names": self.card_names,
            "counters": self.counters,
            "cost": self.cost,
            "cost_hp": self.cost_hp,
            "description": self.description,
            "effects": [e.as_dict() for e in self.effects] if self.effects else [],
            "effect_to_activate": self.effect_to_activate.as_dict() if self.effect_to_activate else None,
            "effect_type": self.effect_type,
            "enabled": self.enabled,
            "id": self.id,
            "image": self.image,
            "make_type": self.make_type,
            "multiplier": self.multiplier,
            "name": self.name,
            "power": self.power,
            "sacrifice_on_activate": self.sacrifice_on_activate,
            "targetted_this_turn": self.targetted_this_turn,
            "target_restrictions": self.target_restrictions,
            "target_type": self.target_type,
            "tokens": [t.as_dict() for t in self.tokens] if self.tokens else [],
            "toughness": self.toughness,
            "trigger": self.trigger,
            "turns": self.turns,
            "was_added": self.was_added
        }


class CardAbility:
    def __init__(self, info, ability_id):
        self.amount = info["amount"] if "amount" in info else None
        self.description = info["description"] if "description" in info else None
        self.descriptive_id = info["descriptive_id"] if "descriptive_id" in info else None
        self.enabled = info["enabled"] if "enabled" in info else True
        self.id = ability_id
        self.keep_evolve = info["keep_evolve"] if "keep_evolve" in info else None
        self.keep_power_increase = info["keep_power_increase"] if "keep_power_increase" in info else 0
        self.keep_toughness_increase = info["keep_toughness_increase"] if "keep_toughness_increase" in info else 0
        self.name = info["name"] if "name" in info else None
        self.target_type = info["target_type"] if "target_type" in info else None
        self.turns = info["turns"] if "turns" in info else -1

    def __repr__(self):
        return f"self.id: {self.id}\n\
                self.name: {self.name}\n\
                self.amount: {self.amount}\n\
                self.target_type: {self.target_type}\n\
                self.description: {self.description}\n\
                self.descriptive_id: {self.descriptive_id}\n\
                self.keep_evolve: {self.keep_evolve}\n\
                self.keep_power_increase: {self.keep_power_increase}\n\
                self.keep_toughness_increase: {self.keep_toughness_increase}\n\
                self.turns: {self.turns}\n\
                self.enabled: {self.enabled}"

    def as_dict(self):
        return {
            "amount": self.amount,
            "description": self.description,
            "descriptive_id": self.descriptive_id,
            "enabled": self.enabled,
            "id": self.id,
            "keep_evolve": self.keep_evolve,
            "keep_power_increase": self.keep_power_increase,
            "keep_toughness_increase": self.keep_toughness_increase,
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
        if self.id != None:
            return f"id: {self.id} - +{self.power_modifier}/+{self.toughness_modifier}"
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
