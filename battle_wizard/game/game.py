import copy
import datetime
import random

from battle_wizard.game.card import Card
from battle_wizard.game.data import Constants
from battle_wizard.game.data import default_deck_genie_wizard 
from battle_wizard.game.data import default_deck_dwarf_tinkerer
from battle_wizard.game.data import default_deck_dwarf_bard
from battle_wizard.game.data import default_deck_vampire_lich
from battle_wizard.game.player import Player
from battle_wizard.game.player_ai import PlayerAI


class Game:
    def __init__(self, player_type, info=None, player_decks=None):

        # player 0 always acts on even turns, player 1 acts on odd turns
        self.actor_turn = int(info["actor_turn"]) if info and "actor_turn" in info else 0
        # the ID of the GameRecord in the DB.
        self.game_record_id = info["game_record_id"] if info and "game_record_id" in info else None
        # created by Make Effect
        self.global_effects = info["global_effects"] if info and "global_effects" in info else []
        # a list of all player-derived moves, sufficient to replay the game
        self.moves = info["moves"] if info and "moves" in info else []
        # the max number of cards a player can have
        self.max_hand_size = 10
        # the next id to give a card when doing make_card effects
        # each card gets the next unusued integer
        self.next_card_id = int(info["next_card_id"]) if info and "next_card_id" in info else 0
        # either pvp or pvai
        self.player_type = info["player_type"] if info and "player_type" in info else player_type
        # support 2 players
        self.players = []
        if info and "players" in info:
            for u in info["players"]:
                if u["is_ai"]:                    
                    self.players.append(PlayerAI(self, u))
                else:
                    self.players.append(Player(self, u))
        # stack decks for unit testing
        self.player_decks = player_decks
        # when True, a countdown timer starts for the active player
        self.show_rope = info["show_rope"] if info and "show_rope" in info else False
        # a stack of actions that need to be resolved in the game (spells, abilities, and attacks)
        self.stack = info["stack"] if info and "stack" in info else []
        # player 0 is the current player on even turns, player 1 is the current player on odd turns
        self.turn = int(info["turn"]) if info and "turn" in info else 0
        # the time the current turn started on
        self.turn_start_time = datetime.datetime.strptime(info["turn_start_time"], "%Y-%m-%d %H:%M:%S.%f") if (info and "turn_start_time" in info and info["turn_start_time"] != None) else datetime.datetime.now()        

    def __repr__(self):
        return f"{self.as_dict()}"

    def as_dict(self):
        return {
            "actor_turn": self.actor_turn, 
            "game_record_id": self.game_record_id, 
            "global_effects": self.global_effects, 
            "moves": self.moves, 
            "next_card_id": self.next_card_id, 
            "players": [p.as_dict() for p in self.players], 
            "player_type": self.player_type, 
            "show_rope": self.show_rope, 
            "stack": self.stack, 
            "turn": self.turn, 
            "turn_start_time": self.turn_start_time.__str__() if self.turn_start_time else None, 
        }

    def current_player(self):
        return self.players[self.actor_turn % 2]

    def opponent(self):
        return self.players[(self.actor_turn + 1) % 2]

    def play_move(self, message, save=False, is_reviewing=False):
        move_type = message["move_type"]
        
        if move_type == 'GET_TIME':
            max_turn_time = 60
            turn_time = datetime.datetime.now() - self.turn_start_time
            # if turn_time.seconds > max_turn_time:
            #     self.show_rope = True
            message["turn_time"] = turn_time.seconds
            message["max_turn_time"] = max_turn_time
            return message
        else:
            print(f"play_move: {move_type} {message['username']}")

        if save and (message["move_type"] != "JOIN" or len(self.moves) <= 2):
            move_copy = copy.deepcopy(message)
            if "game" in move_copy:
                del move_copy['game']
            if "log_lines" in move_copy:
                del move_copy['log_lines']
            if "show_spell" in move_copy:
                del move_copy['show_spell']
            if "game" in move_copy:
                del move_copy['game']
            self.moves.append(move_copy)
        
        if move_type == 'JOIN':
            message = self.join(message, is_reviewing)
        else:
            if (message["username"] != self.current_player().username):
                print(f"can't {move_type} on opponent's turn")
                return None
            self.unset_clickables(move_type)
        if move_type == 'START_FIRST_TURN':
            message = self.current_player().start_turn(message)            
        # moves sent by the game UX via buttons and card clicks
        elif move_type == 'END_TURN':
            message = self.end_turn(message)
        elif move_type == 'SELECT_CARD_IN_HAND':
            message = self.current_player().select_card_in_hand(message)
        elif move_type == 'PLAY_CARD_IN_HAND':
            message = self.play_card_in_hand(message)
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
            self.current_player().make_card(message)
        elif move_type == 'CANCEL_MAKE':
            self.current_player().cancel_make()
        elif move_type == 'MAKE_EFFECT':
            message["log_lines"].append(f"{message['username']} chose {message['card']['global_effect']}.")
            self.global_effects.append(message["card"]["global_effect"])
            self.current_player().reset_card_choice_info()
        elif move_type == 'FETCH_CARD_FROM_PLAYED_PILE':
            message = self.current_player().fetch_card_from_played_pile(message)        
        elif move_type == 'FETCH_CARD':
            message = self.current_player().fetch_card(message, Constants.artifactCardType)        
        elif move_type == 'FETCH_CARD_INTO_PLAY':
            message = self.current_player().fetch_card(message, Constants.artifactCardType, into_play=True)        
        elif move_type == 'FINISH_RIFFLE':
            message = self.current_player().finish_riffle(message)        
        # moves that get triggered indirectly from game UX actions (e.g. SELECT_MOB twice could be an ATTACK)
        elif move_type == 'ATTACK':
            message = self.initiate_attack(message)            
        elif move_type == 'RESOLVE_NEXT_STACK':
            if self.stack[-1][0]["move_type"] == "ATTACK":
                message = self.attack(message)          
            else:  
                self.actor_turn += 1
                message = self.current_player().play_card(self.stack[-1][0]["card"], message)
        elif move_type == 'ACTIVATE_ARTIFACT':
            message = self.activate_artifact(message)            
        elif move_type == 'ACTIVATE_MOB':
            message = self.activate_mob(message)            
        elif move_type == 'HIDE_REVEALED_CARDS':
            message = self.hide_revealed_cards(message)            
        elif move_type == 'PLAY_CARD':
            message = self.current_player().initiate_play_card(message["card"], message)
        elif move_type == 'RESOLVE_MOB_EFFECT':
            message = self.current_player().resolve_mob_effect(message["card"], message)
        elif move_type == 'UNSELECT':
             self.current_player().reset_card_info_to_target()

        # e.g. just pass if you bolt an attacker and you have nothing else to do
        if move_type in ['ACTIVATE_ARTIFACT', 'ACTIVATE_MOB', 'PLAY_CARD', 'ATTACK']:
            cp = self.current_player()
            opp = self.opponent()
            anything_clickable = False
            for card in cp.hand + cp.in_play + opp.in_play + cp.artifacts + opp.artifacts:
                if card.can_be_clicked:
                    anything_clickable = True
            for spell in self.stack:
                if Card(spell[1]).can_be_clicked:
                    anything_clickable = True
            if not anything_clickable and not "bot" in cp.username and len(self.stack) > 0:
                return self.play_move({"move_type": "RESOLVE_NEXT_STACK", "username": cp.username})

        if move_type != 'JOIN' or len(self.players) == 2:
            self.set_clickables()

        return message

    def unset_clickables(self, move_type, cancel_damage=True):
        """
            unselect everything before setting possible attacks/spells
        """

        if len(self.players) != 2:
            return
                       
        for card in self.current_player().played_pile + self.opponent().played_pile + self.current_player().hand + self.opponent().hand:
            card.show_level_up = False
        for card in self.current_player().in_play + self.opponent().in_play + self.current_player().artifacts + self.opponent().artifacts:
            for e in card.effects:
                e.show_effect_animation = False
            card.can_be_clicked = False
            card.effects_can_be_clicked = []
        for card in self.current_player().hand:
            card.can_be_clicked = False
            card.needs_targets = False
        for spell in self.stack:
            spell[1]["can_be_clicked"] = False
        self.opponent().can_be_clicked = False
        self.current_player().can_be_clicked = False
        if move_type != "UNSELECT" and cancel_damage:
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
                if len(selected_spell.effects) > 0:     
                    self.set_targets_for_target_type(selected_spell.effects[0].target_type, selected_spell.effects[0].target_restrictions)
        elif cp.card_info_to_target["effect_type"] in ["mob_at_ready"]:
            selected_mob = cp.selected_mob()
            for spell in self.stack:
                spell_card = spell[1]
                action = spell[0]
                if action["move_type"] == "ATTACK" and action["username"] != cp.username:
                    attacker, _ = self.get_in_play_for_id(action["card"])     
                    if attacker:
                        attacker.can_be_clicked = True
            if len(self.stack) == 0 or selected_mob.has_ability("Instant Attack"):
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

        if len(cp.card_choice_info["cards"]) > 0 and cp.card_choice_info["choice_type"] in ["select_mob_for_effect"]:
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
                if card.needs_hand_target_for_activated_effect(x):
                    effect_can_be_used = False if len(cp.hand) == 0 else True
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
            if cp.can_select_for_attack(card.id):
                card.can_be_clicked = True

        for card in cp.hand:               
            card.needs_targets = card.needs_targets_for_spell()
            if cp.current_mana() >= card.cost:
                card.can_be_clicked = True
                if card.card_type == Constants.artifactCardType:
                    card.can_be_clicked = len(cp.artifacts) != 3
                if card.card_type == Constants.spellCardType and card.needs_mob_or_artifact_target():
                    card.can_be_clicked = False
                    if len(cp.in_play + opp.in_play) > 0:
                        for mob in cp.in_play + opp.in_play:
                            if not mob.has_ability("Lurker"):
                                if len(card.effects[0].target_restrictions) > 0:
                                    if list(card.effects[0].target_restrictions[0].keys())[0] == "min_cost":
                                        if mob.cost >= list(card.effects[0].target_restrictions[0].values())[0]:
                                            card.can_be_clicked = True
                                else:
                                    card.can_be_clicked = True
                        for artifact in cp.artifacts + opp.artifacts:
                            if len(card.effects[0].target_restrictions) > 0:
                                if list(card.effects[0].target_restrictions[0].keys())[0] == "min_cost":
                                    if artifact.cost >= list(card.effects[0].target_restrictions[0].values())[0]:
                                        card.can_be_clicked = True
                            else:
                                card.can_be_clicked = True
                if card.card_type == Constants.spellCardType and card.needs_mob_target():
                    card.can_be_clicked = False
                    if len(cp.in_play + opp.in_play) > 0:
                        for mob in cp.in_play + opp.in_play:
                            if not mob.has_ability("Lurker"):
                                card.can_be_clicked = True
                if card.card_type == Constants.spellCardType and card.needs_artifact_target():
                    card.can_be_clicked = False if len(cp.artifacts) == 0 and len(opp.artifacts) == 0 else True
                if card.card_type == Constants.spellCardType and card.needs_stack_target():
                    card.can_be_clicked = card.has_stack_target(self)
                if card.card_type == Constants.mobCardType and not cp.can_summon():
                    card.can_be_clicked = False
                if card.card_type != Constants.spellCardType and len(self.stack) > 0:
                    card.can_be_clicked = False
                    if card.has_ability("Conjure"):
                        card.can_be_clicked = True
                if card.name == "Mind Manacles":
                    card.can_be_clicked = False
                    for e in opp.in_play:
                        if not e.has_ability("Lurker"):
                            card.can_be_clicked = True
                if card.has_ability("Instrument Required") and not cp.has_instrument():
                    card.can_be_clicked = False
                if card.card_type == Constants.spellCardType and len(self.stack) > 0 and card.card_subtype == "turn-only":
                    card.can_be_clicked = False    

    def get_in_play_for_id(self, card_id):
        """
            Returns a tuple of the mob and controlling player for a card_id of a card that is an in_play mob
        """
        for p in [self.opponent(), self.current_player()]:
            for card in p.in_play + p.artifacts:
                if card.id == card_id:
                    return card, p
        return None, None

    def set_targets_for_target_type(self, target_type, target_restrictions, effect=None):
        if target_type == "any_player":
            self.opponent().can_be_clicked = True
            self.current_player().can_be_clicked = True
        elif target_type == "any_enemy" and effect and effect.name == "attack":
            self.opponent().set_targets_for_attack_effect(effect)
        elif target_type == "any_enemy":
            self.opponent().set_targets_for_damage_effect()
        elif target_type == "any":
            self.current_player().set_targets_for_damage_effect()
            self.opponent().set_targets_for_damage_effect()
        elif target_type == "mob":
            self.current_player().set_targets_for_mob_effect(target_restrictions)
            self.opponent().set_targets_for_mob_effect(target_restrictions)
        elif target_type == "hand_card":
            self.current_player().set_targets_for_hand_card_effect()
        elif target_type == "artifact":
            self.current_player().set_targets_for_artifact_effect(target_restrictions)
            self.opponent().set_targets_for_artifact_effect(target_restrictions)
        elif target_type == "mob_or_artifact":
            self.current_player().set_targets_for_mob_effect(target_restrictions)
            self.opponent().set_targets_for_mob_effect(target_restrictions)
            self.current_player().set_targets_for_artifact_effect(target_restrictions)
            self.opponent().set_targets_for_artifact_effect(target_restrictions)
        elif target_type == "opponents_mob":
            self.opponent().set_targets_for_player_mob_effect(target_restrictions)
        elif target_type == "self_mob":
            self.current_player().set_targets_for_player_mob_effect(target_restrictions)
        elif target_type == "being_cast_mob":
            self.set_targets_for_being_cast_mob_effect()
        elif target_type == "being_cast_spell":
            self.set_targets_for_being_cast_spell_effect(target_restrictions)
        elif target_type == "opponent":
            self.opponent().can_be_clicked = True
        elif target_type == "self":
            self.current_player().can_be_clicked = True

    def set_targets_for_being_cast_spell_effect(self, target_restrictions):
        for spell in self.stack:
            card = spell[1]
            if card["card_type"] == Constants.spellCardType:
                if len(target_restrictions) > 0 and list(target_restrictions[0].keys())[0] == "target" and list(target_restrictions[0].values())[0] == "mob":
                    action = spell[0]
                    if "effect_targets" in action and action["effect_targets"][0]["target_type"] == Constants.mobCardType:
                        card["can_be_clicked"] = True
                else:
                    card["can_be_clicked"] = True

    def set_targets_for_being_cast_mob_effect(self):
        for spell in self.stack:
            card = spell[1]
            if card["card_type"] == Constants.mobCardType:
                card["can_be_clicked"] = True

    def join(self, message, is_reviewing=False):
        join_occured = True
        if len(self.players) == 0:
            self.players.append(Player(self, message, new=True))            
            self.players[len(self.players)-1].deck_id = int(message["deck_id"]) if "deck_id" in message and message["deck_id"] != "None" else None
            message["log_lines"].append(f"{message['username']} created the game.")
        elif len(self.players) == 1:
            message["log_lines"].append(f"{message['username']} joined the game.")
            if self.player_type == "pvai":                        
                self.players.append(PlayerAI(self, message, new=True))
                self.players[len(self.players)-1].deck_id = message["opponent_deck_id"] if "opponent_deck_id" in message else random.choice([default_deck_genie_wizard()["url"], default_deck_dwarf_tinkerer()["url"], default_deck_dwarf_bard()["url"], default_deck_vampire_lich()["url"]])
            else:
                self.players.append(Player(self, message, new=True))
                self.players[len(self.players)-1].deck_id = int(message["deck_id"]) if "deck_id" in message and message["deck_id"] != "None" else None
        elif len(self.players) >= 2:
            print(f"an extra player tried to join players {[p.username for p in self.players]}")
            join_occured = False

        if len(self.players) == 2 and join_occured:
            self.start_game(message, is_reviewing)
        return message

    def start_game(self, message, is_reviewing=False):
        if len(self.player_decks[0]) > 0 or len(self.player_decks[1]) > 0 :
            self.start_test_stacked_deck_game(message)
        else:
            self.start_constructed_game(message, is_reviewing)

    def start_test_stacked_deck_game(self, message):
        if self.players[0].max_mana == 0: 
            for x in range(0, 2):
                for card_name in self.player_decks[x]:
                    self.players[x].add_to_deck(card_name, 1)
                self.players[x].deck.reverse()
            self.current_player().get_starting_artifacts()
            self.opponent().get_starting_artifacts()
            self.current_player().get_starting_spells()
            self.opponent().get_starting_spells()
            for x in range(0, 2):
                self.players[x].draw(self.players[x].initial_hand_size())

            self.send_start_first_turn(message)

    def start_constructed_game(self, message, is_reviewing=False):
        if self.players[0].max_mana == 0: 
            deck_hashes = []
            for x in range(0, 2):
                deck_hashes.append(self.players[x].get_starting_deck())

            self.current_player().get_starting_artifacts()
            self.opponent().get_starting_artifacts()
            self.current_player().get_starting_spells()
            self.opponent().get_starting_spells()
            for x in range(0, 2):                
                self.players[x].draw(self.players[x].initial_hand_size())

            self.send_start_first_turn(message)

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
        if len(self.stack) > 0:
            print(f"can't end turn when there is a spell or attack on the stack")
            return message
        self.current_player().remove_temporary_tokens()
        self.opponent().remove_temporary_tokens()
        self.current_player().remove_temporary_abilities()
        self.remove_temporary_effects()
        self.current_player().clear_damage_this_turn()
        self.opponent().clear_damage_this_turn()
        self.current_player().clear_artifact_effects_targetted_this_turn()

        cards_to_discard = []
        cards_to_keep = []

        for card in self.current_player().hand:
            if card.has_ability("Keep"):
                cards_to_keep.append(card)
            else:
                cards_to_discard.append(card)

        if self.current_player().discipline == "tech":
            for card in cards_to_discard:
                self.current_player().hand.remove(card)
                self.current_player().played_pile.append(card)
        for card in cards_to_keep:
            for a in card.abilities:
                if a.name == "Keep":
                    if card.power:
                        old_power = card.power 
                        card.power += a.keep_power_increase
                        if card.power > old_power:
                            card.show_level_up = True
                    if card.toughness:
                        old_toughness = card.toughness 
                        card.toughness += a.keep_toughness_increase
                        if card.toughness > old_toughness:
                            card.show_level_up = True
                    if a.keep_evolve:
                         evolved_card = self.current_player().add_to_deck(a.keep_evolve, 1, add_to_hand=True)
                         self.current_player().hand.remove(evolved_card)
                         evolved_card.id = card.id
                         evolved_card.show_level_up = True
                         self.current_player().hand[self.current_player().hand.index(card)] = evolved_card

        for mob in self.current_player().in_play + self.current_player().artifacts:
            # this works because all end_turn triggered effects dont have targets to choose
            effect_targets = mob.unchosen_targets(self.current_player(), effect_type="triggered")            
            index = 0
            for effect in mob.effects_triggered():
                if effect.name == "spell_from_yard":
                    spells = []
                    for card in self.current_player().played_pile:
                        if card.card_type == Constants.spellCardType:
                            spells.append(card)
                    if len(spells) == 0:
                        continue
                    else:
                        if len(self.current_player().hand) < self.max_hand_size:
                            spell = random.choice(spells)
                            self.current_player().hand.append(spell)
                            self.current_player().played_pile.remove(spell)
                elif effect.name == "damage" and effect.trigger == "end_turn":
                    message["log_lines"] += mob.do_damage_effect(self.current_player(), effect, effect_targets[index])
                elif effect.name == "improve_damage_when_used":
                    # hax for Doomer, this would break if it didnt have two damage effects
                    mob.effects[0].amount += 1
                    mob.effects[1].amount += 1
                index += 1

        self.turn += 1
        self.actor_turn += 1
        message["log_lines"].append(f"{self.current_player().username}'s turn.")
        message = self.current_player().start_turn(message)
        return message

    def remove_temporary_effects(self):
        for p in [[self.current_player(), self.opponent()], [self.opponent(), self.current_player()]]:
            mobs_to_switch_sides = []
            for c in p[0].in_play:
                perm_effects = []
                for e in c.effects:
                    e.turns -= 1
                    if e.turns == 0:
                        if e.name == "take_control":
                            mobs_to_switch_sides.append(c)                        
                    else:
                        perm_effects.append(e)
                c.effects = perm_effects
            for c in mobs_to_switch_sides:
                p[0].in_play.remove(c)
                p[1].in_play.append(c)

    def play_card_in_hand(self, message):
        card = None
        for card_in_hand in self.current_player().hand:
            if card_in_hand.id == message["card"]:
                card = card_in_hand
                break
        if not card:
            print(f"can't play that Card, it's not in hand")
            return None

        self.current_player().reset_card_info_to_target()
        message["card_name"] = card.name
        message["move_type"] = "PLAY_CARD"
        message = self.play_move(message)
        return message

    def select_stack_spell(self, message):
        cp = self.current_player()
        if cp.card_info_to_target["effect_type"] != "spell_cast":
            print(f"can't select stack spell with non-counterspell")
            return None
        selected_spell = cp.selected_spell()
        stack_spell = None
        for spell in self.stack:
            if spell[1]["id"] == message["card"]:
                stack_spell = spell
        if selected_spell:
            effect = selected_spell.effects[0]
            stack_spell_card = Card(stack_spell[1])
            if effect.target_type == "being_cast_mob" and stack_spell_card.card_type != Constants.mobCardType:
                print(f"can't select non-mob with mob-counterspell")
                return None
            return self.select_stack_target(selected_spell, message, "PLAY_CARD")
        else:
            prin("shouldn't get here in select_stack_spell")

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
            if not selected_card.can_target_mobs():
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
                print(f"nothing selected to target mob {defending_card.name}")
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

    def activate_artifact_on_hand_card(self, message, artifact, hand_card, effect_index):
        message["move_type"] = "ACTIVATE_ARTIFACT"
        message["effect_index"] = effect_index
        message["card"] = self.current_player().selected_artifact().id
        message["card_name"] = self.current_player().selected_artifact().name
        message["hand_card"] = hand_card.id
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
                print(f"nothing selected to target artifact {defending_card.name}")
                return None
        else:
            print("Should never get here")                                
        return message

    def select_player(self, move_type, message):
        if self.current_player().selected_mob() and self.current_player().card_info_to_target["effect_type"] in ["mob_activated", "mob_comes_into_play"]:
            if move_type == 'SELECT_OPPONENT':
                message = self.select_player_target(self.opponent().username, self.current_player().selected_mob(), message, "RESOLVE_MOB_EFFECT")
            else:
                message = self.select_player_target(self.current_player().username, self.current_player().selected_mob(), message, "RESOLVE_MOB_EFFECT")
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
                message = self.select_player_target(target_player.username, self.current_player().selected_spell(), message, "PLAY_CARD")
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
                    print(f"can't attack {target_player.username} because a Mob has Guard")
                    return None                
            using_artifact = True
            message = self.select_player_target(target_player.username, self.current_player().selected_artifact(), message, "ACTIVATE_ARTIFACT")
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
        card_id = message["card"]
        attacking_card = self.current_player().in_play_card(card_id)
        self.stack.append([copy.deepcopy(message), attacking_card.as_dict()])
        self.current_player().reset_card_info_to_target()
        self.actor_turn += 1

        self.unset_clickables(message["move_type"])
        self.set_clickables()

        if not self.current_player().has_instants() and not self.current_player().has_defend():
            message = self.attack(message)
            self.unset_clickables(message["move_type"], cancel_damage=False)
            self.set_clickables()
            return message

        if "defending_card" in message:
            defending_card_id = message["defending_card"]
            defending_card = self.current_player().in_play_card(defending_card_id)
            message["log_lines"].append(f"{attacking_card.name} intends to attack {defending_card.name}")
        else:
            message["log_lines"].append(f"{attacking_card.name} intends to attack {self.opponent().username} for {attacking_card.power_with_tokens(self.opponent())}.")
        # todo rope

        return message

    def attack(self, message):
        to_resolve = self.stack.pop()
        move_to_complete = to_resolve[0]        
        move_to_complete["log_lines"] = []
        self.actor_turn += 1
        card_id = move_to_complete["card"]
        attacking_card = self.current_player().in_play_card(card_id)

        # an instant removed the attacker
        if not attacking_card:
            return message

        attacking_card.attacked = True
        self.unset_clickables(message["move_type"])
        self.set_clickables()
        
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
            move_to_complete["log_lines"].append(f"{attacking_card.name} attacks {self.opponent().username} for {attacking_card.power_with_tokens(self.current_player())}.")
            self.opponent().damage(attacking_card.power_with_tokens(self.current_player()))
        attacking_card.do_attack_abilities(self.current_player())
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
            artifact.resolve_effect(artifact.activated_effect_defs[0], self.current_player(), e, effect_targets[0])
            self.current_player().reset_card_info_to_target()
            if artifact.has_ability("multi_mob_attack"):
                e.targetted_this_turn.append(effect_targets[0])
        elif "hand_card" in message:
            hand_card = self.current_player().in_hand_card(message["hand_card"])
            message["log_lines"].append(f"{self.current_player().username} uses {artifact.name} on {hand_card.name}")
            artifact.resolve_effect(artifact.activated_effect_defs[0], self.current_player(), e, {"id": hand_card.id, "target_type": "hand_card"})
            self.current_player().reset_card_info_to_target()
        else:
            if e.target_type == "self":
                message["log_lines"].append(artifact.resolve_effect(artifact.activated_effect_defs[0], self.current_player(), e, {"id": message["username"], "target_type": "player"}))
            elif e.target_type == "opponent":
                message["log_lines"].append(artifact.resolve_effect(artifact.activated_effect_defs[0], self.current_player(), e, {"id": self.opponent().username, "target_type": "player"}))
            elif e.target_type == "all":  # Disk of Death only, maybe rename from all
                message["log_lines"].append(artifact.resolve_effect(artifact.activated_effect_defs[0], self.current_player(), e, {})) 
            elif e.target_type == "artifact_in_deck":
                message["log_lines"].append(artifact.resolve_effect(artifact.activated_effect_defs[0], self.current_player(), e, {"id": message["username"], "target_type": e.target_type})) 
            elif e.target_type == "self_mob":
                message = self.select_mob_target_for_artifact_activated_effect(artifact, message)
            else:
                target_player = self.players[0]
                if target_player.username != message["effect_targets"][0]["id"]:
                    target_player = self.players[1]
                message["log_lines"].append(f"{self.current_player().username} uses {artifact.name} on {target_player.username}")
                message["effect_targets"] = []
                message["effect_targets"].append({"id": target_player.username, "target_type": "player"})
                message["log_lines"].append(artifact.resolve_effect(artifact.activated_effect_defs[0], self.current_player(), e, message["effect_targets"][0])) 
                self.current_player().reset_card_info_to_target()
                if artifact.has_ability("multi_mob_attack"):
                    e.targetted_this_turn.append(message["effect_targets"][0])

        self.current_player().reset_card_info_to_target()
        # Wish Stone
        if len(artifact.enabled_activated_effects()) and artifact.enabled_activated_effects()[0].sacrifice_on_activate:
            self.current_player().send_card_to_played_pile(artifact, did_kill=True)
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
            message["log_lines"].append(mob.resolve_effect(artifact.activated_effect_defs[0], self.current_player(), e, {"id": mob.id, "target_type":e.target_type})) 
        elif e.name == "unwind":
            if "defending_card" in message:
                message["log_lines"].append(mob.resolve_effect(artifact.activated_effect_defs[0], self.current_player(), e, message["effect_targets"][0])) 
                self.current_player().reset_card_info_to_target()
                mob.can_activate_abilities = False
            else:
                message["log_lines"].append(f"{self.current_player().username} activates {mob.name}.")
                message = self.current_player().target_or_do_mob_effects(mob, message, self.current_player().username, is_activated_effect=True)
        else:
            print(f"unsupported mob effect {e}")
        return message

    def hide_revealed_cards(self, message):
        self.current_player().reset_card_choice_info()
        return message

    def resolve_combat(self, attacking_card, defending_card):
        if attacking_card.shielded:
            attacking_card.shielded = False
        else:
            attacking_card.damage += defending_card.power_with_tokens(self.opponent())
            attacking_card.damage_this_turn += defending_card.power_with_tokens(self.opponent())
            attacking_card.damage_to_show += defending_card.power_with_tokens(self.opponent())
            if attacking_card.damage < attacking_card.toughness_with_tokens() and defending_card.has_ability("DamageTakeControl"):
                self.current_player().in_play.remove(attacking_card)
                self.opponent().in_play.append(attacking_card)
                self.current_player().update_for_mob_changes_zones()
                self.opponent().update_for_mob_changes_zones()
        if defending_card.shielded:
            defending_card.shielded = False
        else:
            if attacking_card.has_ability("Stomp"):
                stomp_damage = attacking_card.power_with_tokens(self.current_player()) - (defending_card.toughness_with_tokens() - defending_card.damage)
                if stomp_damage > 0:
                    self.opponent().damage(stomp_damage)
            defending_card.damage += attacking_card.power_with_tokens(self.current_player())
            defending_card.damage_this_turn += attacking_card.power_with_tokens(self.current_player())
            defending_card.damage_to_show += attacking_card.power_with_tokens(self.opponent())
            if defending_card.damage < defending_card.toughness_with_tokens() and attacking_card.has_ability("DamageTakeControl"):
                self.opponent().in_play.remove(defending_card)
                self.current_player().in_play.append(defending_card)
                self.current_player().update_for_mob_changes_zones()
                self.opponent().update_for_mob_changes_zones()
        
        if attacking_card.damage >= attacking_card.toughness_with_tokens():
            self.current_player().send_card_to_played_pile(attacking_card, did_kill=True)

        if defending_card.damage >= defending_card.toughness_with_tokens():
            self.opponent().send_card_to_played_pile(defending_card, did_kill=True)

    def remove_attack_for_mob(self, mob):
        if len(self.stack) > 0:
            action = self.stack[-1][0]
            if action["move_type"] == "ATTACK" and action["username"] != self.current_player().username:
                if action["card"] == mob.id:    
                    self.stack.pop()
                    self.actor_turn += 1

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

    def select_mob_target(self, card_to_target, message, move_type, activated_effect=False):
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
        new_message["effect_targets"] = effect_targets
        new_message["card"] = card_to_target.id
        new_message["card_name"] = card_to_target.name
        self.current_player().reset_card_info_to_target()
        new_message = self.play_move(new_message)       
        return new_message             
    
    def select_stack_target(self, card_to_target, message, move_type):
        new_message = copy.deepcopy(message)
        new_message["move_type"] = move_type

        selected_card = None
        for spell in self.stack:
            if spell[1]["id"] == message["card"]:
                selected_card = Card(spell[1])
                break

        effect_targets = []
        effect_targets.append({"id": selected_card.id, "target_type": "stack_spell"})            
        new_message["effect_targets"] = effect_targets
        new_message["card"] = card_to_target.id
        new_message["card_name"] = card_to_target.name
        self.current_player().reset_card_info_to_target()
        new_message = self.play_move(new_message)       
        return new_message             

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
        return new_message             

    def defendable_attack_on_stack(self, defender):
        attack_to_defend = False
        attack_defender = None
        for spell in self.stack:
            spell_card = spell[1]
            action = spell[0]
            if action["move_type"] == "ATTACK" and action["username"] != self.current_player().username:
                attack_to_defend = True
                if "defending_card" in action:
                    attack_defender, _ = self.get_in_play_for_id(action["defending_card"])
        return attack_to_defend and defender != attack_defender
