import copy
import datetime
import random

from battle_wizard.card import Card, CardEffect, CardAbility
from battle_wizard.data import default_deck_genie_wizard 
from battle_wizard.data import default_deck_dwarf_tinkerer
from battle_wizard.data import default_deck_dwarf_bard
from battle_wizard.data import default_deck_vampire_lich
from battle_wizard.data import hash_for_deck
from battle_wizard.models import Deck
from battle_wizard.models import GameRecord
from battle_wizard.models import GlobalDeck
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist


class Game:
    def __init__(self, player_type, info=None, player_decks=None, ai=None):

        self.game_record_id = info["game_record_id"] if info and "game_record_id" in info else None

        self.ai = ai
        self.player_type = info["player_type"] if info and "player_type" in info else player_type

        # support 2 players
        self.players = [Player(self, u) for u in info["players"]] if info and "players" in info else []
        self.turn = int(info["turn"]) if info and "turn" in info else 0

        # player 0 always acts on even turns, player 1 acts on odd turns
        self.actor_turn = int(info["actor_turn"]) if info and "actor_turn" in info else 0

        self.stack = info["stack"] if info and "stack" in info else []

        # the next id to give a card when doing make_card effects
        # each card gets the next unusued integer
        self.next_card_id = int(info["next_card_id"]) if info and "next_card_id" in info else 0
        # created by Make Effect
        self.global_effects = info["global_effects"] if info and "global_effects" in info else []

        # stack decks for unit testing
        self.player_decks = player_decks

        self.turn_start_time = datetime.datetime.strptime(info["turn_start_time"], "%Y-%m-%d %H:%M:%S.%f") if (info and "turn_start_time" in info and info["turn_start_time"] != None) else datetime.datetime.now()
        self.show_rope = info["show_rope"] if info and "show_rope" in info else False
        
        self.max_hand_size = 10

        # a list of all player-derived moves, sufficient to replay the game
        self.moves = info["moves"] if info and "moves" in info else []
        # when in review mode, the index of the move under review
        self.review_move_index = info["review_move_index"] if info and "review_move_index" in info else -1
        self.is_review_game = info["is_review_game"] if info and "is_review_game" in info else False
        if self.is_review_game:
            self.review_game = Game(self.player_type, info=info["review_game"], player_decks=player_decks, ai=ai) if info and "review_game" in info else None
        else:
            self.review_game = None
        self.is_reviewing = info["is_reviewing"] if info and "is_reviewing" in info else False

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
            "review_move_index": self.review_move_index, 
            "review_game": self.review_game.as_dict() if self.review_game else None, 
            "is_review_game": self.is_review_game, 
            "is_reviewing": self.is_reviewing, 
            "turn_start_time": self.turn_start_time.__str__() if self.turn_start_time else None, 
        }

    def player_for_username(self, username):
        if self.players[0].username == username:
            return self.players[0]
        return self.players[1]

    def current_player(self):
        return self.players[self.actor_turn % 2]

    def opponent(self):
        return self.players[(self.actor_turn + 1) % 2]

    def modify_new_card(self, card):
        if card.card_type == Card.spellCardType:            
            if 'spells_cost_more' in self.global_effects:
                card.cost += self.global_effects.count('spells_cost_more')
            if 'spells_cost_less' in self.global_effects:
                card.cost -= self.global_effects.count('spells_cost_less')
                card.cost = max(0, card.cost)
        elif card.card_type == Card.mobCardType:            
            if 'mobs_cost_more' in self.global_effects:
                card.cost += self.global_effects.count('mobs_cost_more')
            if 'mobs_cost_less' in self.global_effects:
                card.cost -= self.global_effects.count('mobs_cost_less')
                card.cost = max(0, card.cost)
            if 'mobs_get_more_toughness' in self.global_effects:
                card.toughness += self.global_effects.count('mobs_get_more_toughness')*2
            if 'mobs_get_less_toughness' in self.global_effects:
                card.toughness -= self.global_effects.count('mobs_get_less_toughness')*2
                card.toughness = max(0, card.toughness)
            if 'mobs_get_more_power' in self.global_effects:
                card.power += self.global_effects.count('mobs_get_more_power')*2
            if 'mobs_get_less_power' in self.global_effects:
                card.power -= self.global_effects.count('mobs_get_less_power')*2
                card.power = max(0, card.power)
        return card

    def legal_moves_for_ai(self, player):
        """
            Returns a list of possible moves for an AI player.
        """
        if len(self.players) < 2:
            return [{"move_type": "JOIN", "username": self.ai}]

        moves = []
        has_action_selected = player.selected_mob() or player.selected_artifact() or player.selected_spell()
        if player.card_info_to_target["effect_type"] in ["mob_activated", "mob_comes_into_play"]:
            moves = self.add_resolve_mob_effects_moves(player, moves)
        elif player.card_choice_info["choice_type"] in ["make", "make_with_option"]:
            moves = self.add_resolve_make_moves(player, moves)
            moves.append({"move_type": "CANCEL_MAKE", "username": self.ai})              
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
        elif player.card_choice_info["choice_type"] == "fetch_into_hand_from_played_pile":
            moves = self.add_resolve_fetch_card_from_played_pile_moves(player, moves)
        elif player.card_choice_info["choice_type"] == "select_mob_for_ice_prison":
            moves = self.add_select_mob_for_ice_prison_moves(moves)
            if len(moves) == 0:
                moves = self.add_attack_and_play_card_moves(moves)
                moves.append({"move_type": "END_TURN", "username": self.ai})                
        elif len(self.stack) > 0 and not has_action_selected:
            moves = self.add_response_moves(player, moves)

        # can be zero here when there is a Make From Deck move with no targets in deck (at least)
        if len(moves) == 0:
            moves = self.add_attack_and_play_card_moves(moves)
            if not has_action_selected:
                moves.append({"move_type": "END_TURN", "username": self.ai})
        return moves

    def add_response_moves(self, player, moves):
        moves = self.add_attack_and_play_card_moves(moves)
        moves.append({"move_type": "RESOLVE_NEXT_STACK", "username": self.ai})              
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

    def add_resolve_fetch_card_from_played_pile_moves(self, player, moves):
        for c in player.card_choice_info["cards"]:
            moves.append({"card":c.id , "move_type": "FETCH_CARD_FROM_PLAYED_PILE", "username": self.ai})              
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
        for spell in self.stack:
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
                # todo maybe mobs will have multiple effects
                moves.append({"card":mob.id, "move_type": "ACTIVATE_MOB", "username": self.ai, "effect_index": 0})
            elif len(mob.effects_activated()) > 0 and \
                mob.effects_activated()[0].cost <= self.current_player().current_mana():
                # todo maybe mobs will have multiple effects, only have Winding One right now
                moves.append({"card":mob.id, "move_type": "ACTIVATE_MOB", "username": self.ai, "effect_index": 0})
        for mob in self.opponent().in_play:
            if mob.can_be_clicked:
                moves.append({"card":mob.id , "move_type": "SELECT_MOB", "username": self.ai})
        for card in self.current_player().hand:
            if card.can_be_clicked:
                # todo: cleaner if/then for Duplication/Upgrade Chambers
                if self.current_player().card_info_to_target["effect_type"] == "artifact_activated":
                    moves.append({"card":card.id , "move_type": "SELECT_CARD_IN_HAND", "username": self.ai})
                elif self.current_player().card_info_to_target["card_id"]:
                    moves.append({"card":card.id , "move_type": "PLAY_CARD_IN_HAND", "username": self.ai})
                else:
                    moves.append({"card":card.id , "move_type": "SELECT_CARD_IN_HAND", "username": self.ai})
        if self.current_player().can_be_clicked:
            moves.append({"move_type": "SELECT_SELF", "username": self.ai})
        if self.opponent().can_be_clicked:
            moves.append({"move_type": "SELECT_OPPONENT", "username": self.ai, "card": self.current_player().card_info_to_target["card_id"]})
        return moves

    def navigate_game(self, original_message, consumer):
        
        self.review_game = Game("pvp", info={}, ai=consumer.ai, player_decks=consumer.decks)
        self.review_game.is_review_game = True
        self.is_reviewing = True;
        #print(f"navigate_game with total moves {len(self.moves)}")
        #for move in self.moves:
        #    print(move)
        self.moves[0]["discipline"] = self.players[0].discipline
        self.moves[1]["discipline"] = self.players[1].discipline
        self.moves[0]["initial_deck"] = [c.as_dict() for c in self.players[0].initial_deck]
        self.moves[1]["initial_deck"] = [c.as_dict() for c in self.players[1].initial_deck]
        index = 0
        log_lines = []
        for move in self.moves:
            if index > original_message["index"] - 1 and original_message["index"] > -1:
                break
            move["log_lines"] = []
            message = self.review_game.play_move(move)
            if message["log_lines"] != []:
                log_lines += message["log_lines"]
            index += 1
        original_message["log_lines"] = log_lines  
        username = original_message['username']
        if original_message["index"] == -1:
            self.review_game = None
            self.is_reviewing = False
            original_message["log_lines"].append(f"{username} resumed the game.")
        else:
            original_message["log_lines"].append(f"{username} navigated the game to move {original_message['index']}.")
        self.review_move_index = original_message["index"]
        return original_message


    def play_move(self, message, save=False):
        move_type = message["move_type"]
        if message["move_type"] != "GET_TIME":
            print(f"play_move: {move_type} {message['username']}")
        
        if move_type == 'GET_TIME':
            max_turn_time = 60
            turn_time = datetime.datetime.now() - self.turn_start_time
            # if turn_time.seconds > max_turn_time:
            #     self.show_rope = True
            message["turn_time"] = turn_time.seconds
            message["max_turn_time"] = max_turn_time
            return message

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
            #for move in self.moves:
            #    print(move)
        
        if move_type != 'JOIN':
            self.unset_clickables(move_type)

        # moves to join/configure/start a game
        if move_type == 'JOIN':
            message = self.join(message)
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
            self.make_card(message)
        elif move_type == 'CANCEL_MAKE':
            self.cancel_make(message)
        elif move_type == 'MAKE_EFFECT':
            message = self.make_effect(message)        
        elif move_type == 'FETCH_CARD_FROM_PLAYED_PILE':
            message = self.fetch_card_from_played_pile(message)        
        elif move_type == 'FETCH_CARD':
            message = self.fetch_card(message, Card.artifactCardType)        
        elif move_type == 'FETCH_CARD_INTO_PLAY':
            message = self.fetch_card(message, Card.artifactCardType, into_play=True)        
        elif move_type == 'FINISH_RIFFLE':
            message = self.finish_riffle(message)        
        # moves that get triggered indirectly from game UX actions (e.g. SELECT_MOB twice could be an ATTACK)
        elif move_type == 'ATTACK':
            message = self.initiate_attack(message)            
        elif move_type == 'RESOLVE_NEXT_STACK':
            if self.stack[-1][0]["move_type"] == "ATTACK":
                message = self.attack(message)          
            else:  
                self.actor_turn += 1
                self.current_player().play_card(self.stack[-1][0]["card"], message)
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

        if move_type == 'JOIN':
            if len(self.players) == 1 and self.player_type == "pvai":
                message["username"] = self.ai
                message = self.play_move(message, save=True)

        if message and len(self.players) == 2 and not self.is_review_game:
            game_object = GameRecord.objects.get(id=self.game_record_id)
            game_object.game_json = self.as_dict()
            if self.players[0].hit_points <= 0 or self.players[1].hit_points <= 0:
                game_object.date_finished = datetime.datetime.now()
                if self.players[0].hit_points <= 0 and self.players[1].hit_points >= 0:
                    game_object.winner = User.objects.get(username=self.players[1].username)
                elif self.players[1].hit_points <= 0 and self.players[0].hit_points >= 0:
                    game_object.winner = User.objects.get(username=self.players[0].username)
            game_object.save()
        else:
            # if message is None, the move was a no-op, like SELECT_CARD_IN_HAND on an uncastable card
            pass

        if move_type != 'JOIN' or len(self.players) == 2:
            self.set_clickables()

        return message

    def unset_clickables(self, move_type, cancel_damage=True):
        """
            unhighlight everything before highlighting possible attacks/spells
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

        # print(cp.username)
        # if cp.selected_mob():
        #    print(cp.selected_mob())
        #if cp.selected_artifact():
        #    print(cp.selected_artifact())
        #if cp.selected_spell():
        #    print(cp.selected_spell())

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
        
        if cp.card_info_to_target["effect_type"]:
            return

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
                if card.card_type == Card.artifactCardType:
                    card.can_be_clicked = len(cp.artifacts) != 3
                if card.card_type == Card.spellCardType and card.needs_mob_or_artifact_target():
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
                if card.card_type == Card.spellCardType and card.needs_mob_target():
                    card.can_be_clicked = False
                    if len(cp.in_play + opp.in_play) > 0:
                        for mob in cp.in_play + opp.in_play:
                            if not mob.has_ability("Lurker"):
                                card.can_be_clicked = True
                if card.card_type == Card.spellCardType and card.needs_artifact_target():
                    card.can_be_clicked = False if len(cp.artifacts) == 0 and len(opp.artifacts) == 0 else True
                if card.card_type == Card.spellCardType and card.needs_stack_target():
                    card.can_be_clicked = card.has_stack_target(self)
                if card.card_type == Card.mobCardType and not cp.can_summon():
                    card.can_be_clicked = False
                if card.card_type != Card.spellCardType and len(self.stack) > 0:
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
                if card.card_type == Card.spellCardType and len(self.stack) > 0 and card.card_subtype == "turn-only":
                    card.can_be_clicked = False    

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
        elif target_type == "hand_card":
            self.set_targets_for_hand_card_effect()
        elif target_type == "artifact":
            self.set_targets_for_artifact_effect(target_restrictions)
        elif target_type == "mob_or_artifact":
            self.set_targets_for_mob_effect(target_restrictions)
            self.set_targets_for_artifact_effect(target_restrictions)
        elif target_type == "opponents_mob":
            self.set_targets_for_opponents_mob_effect(target_restrictions)
        elif target_type == "self_mob":
            self.set_targets_for_self_mob_effect(target_restrictions)
        elif target_type == "being_cast_mob":
            self.set_targets_for_being_cast_mob_effect()
        elif target_type == "being_cast_spell":
            self.set_targets_for_being_cast_spell_effect(target_restrictions)
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
        guard_mobs_without_lurker = []
        clickable_ids = []
        for card in self.opponent().in_play:
            if card.has_ability("Guard") and not card.has_ability("Lurker"):
                guard_mobs_without_lurker.append(card)
        if len(guard_mobs_without_lurker) == 0:
            for card in self.opponent().in_play:
                if not card.has_ability("Lurker"):
                     clickable_ids.append(card.id)
            # todo this assumes card ids never clash with usernames
            clickable_ids.append(self.opponent().username)
        else:
            for card in guard_mobs_without_lurker:
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
        guard_mobs_without_lurker = []
        for card in self.opponent().in_play:
            if card.has_ability("Guard") and not card.has_ability("Lurker"):
                guard_mobs_without_lurker.append(card)
        if len(guard_mobs_without_lurker) == 0:
            for card in self.opponent().in_play:
                if not card.has_ability("Lurker"):
                    card.can_be_clicked = True
            self.opponent().can_be_clicked = True
        else:
            for card in guard_mobs_without_lurker:
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
                if card.power_with_tokens() >= list(target_restrictions[0].values())[0]:
                    if not card.has_ability("Lurker"):
                        card.can_be_clicked = True
                        did_target = True
            for card in self.current_player().in_play:
                if card.power_with_tokens() >= list(target_restrictions[0].values())[0]:
                    if not card.has_ability("Lurker"):
                        card.can_be_clicked = True
                        did_target = True
            return did_target

        if len(target_restrictions) > 0 and list(target_restrictions[0].keys())[0] == "min_cost":
            did_target = False
            for card in self.opponent().in_play:
                if card.cost >= list(target_restrictions[0].values())[0]:
                    card.can_be_clicked = True
                    did_target = True
            for card in self.current_player().in_play:
                if card.cost >= list(target_restrictions[0].values())[0]:
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

    def set_targets_for_artifact_effect(self, target_restrictions):
        if len(target_restrictions) > 0 and list(target_restrictions[0].keys())[0] == "min_cost":
            did_target = False
            for card in self.opponent().artifacts:
                if card.cost >= list(target_restrictions[0].values())[0]:
                    card.can_be_clicked = True
                    did_target = True
            for card in self.current_player().artifacts:
                if card.cost >= list(target_restrictions[0].values())[0]:
                    card.can_be_clicked = True
                    did_target = True
            return did_target

        did_target = False
        for card in self.opponent().artifacts:
            card.can_be_clicked = True
            did_target = True
        for card in self.current_player().artifacts:
            card.can_be_clicked = True
            did_target = True
        return did_target

    def set_targets_for_hand_card_effect(self):
        for card in self.current_player().hand:
            card.can_be_clicked = True

    def set_targets_for_being_cast_spell_effect(self, target_restrictions):
        for spell in self.stack:
            card = spell[1]
            if card["card_type"] == Card.spellCardType:
                if len(target_restrictions) > 0 and list(target_restrictions[0].keys())[0] == "target" and list(target_restrictions[0].values())[0] == "mob":
                    action = spell[0]
                    if "effect_targets" in action and action["effect_targets"][0]["target_type"] == Card.mobCardType:
                        card["can_be_clicked"] = True
                else:
                    card["can_be_clicked"] = True

    def set_targets_for_being_cast_mob_effect(self):
        for spell in self.stack:
            card = spell[1]
            if card["card_type"] == Card.mobCardType:
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
            self.players.append(Player(self, message, new=True))            
            self.players[len(self.players)-1].deck_id = int(message["deck_id"]) if "deck_id" in message and message["deck_id"] != "None" else None
            message["log_lines"].append(f"{message['username']} created the game.")
        elif len(self.players) == 1:
            message["log_lines"].append(f"{message['username']} joined the game.")
            if self.player_type == "pvai":                        
                self.players.append(Player(self, message, new=True, bot=self.ai))
                self.players[len(self.players)-1].deck_id = message["opponent_deck_id"] if "opponent_deck_id" in message else random.choice([default_deck_genie_wizard()["url"], default_deck_dwarf_tinkerer()["url"], default_deck_dwarf_bard()["url"], default_deck_vampire_lich()["url"]])
            else:
                self.players.append(Player(self, message, new=True))
                self.players[len(self.players)-1].deck_id = int(message["deck_id"]) if "deck_id" in message and message["deck_id"] != "None" else None
        elif len(self.players) >= 2:
            print(f"an extra player tried to join players {[p.username for p in self.players]}")
            join_occured = False

        if len(self.players) == 2 and join_occured:
            self.start_game(message)
        return message

    def start_game(self, message):
        if len(self.player_decks[0]) > 0 or len(self.player_decks[1]) > 0 :
            self.start_test_stacked_deck_game(message)
        else:
            self.start_constructed_game(message)

    def start_test_stacked_deck_game(self, message):
        if self.players[0].max_mana == 0: 
            for x in range(0, 2):
                for card_name in self.player_decks[x]:
                    self.players[x].add_to_deck(card_name, 1)
                self.players[x].deck.reverse()
            self.get_starting_artifacts()
            self.get_starting_spells()
            for x in range(0, 2):
                self.players[x].draw(self.players[x].initial_hand_size())

            self.send_start_first_turn(message)

    def start_constructed_game(self, message):
        if self.players[0].max_mana == 0: 
            deck_hashes = []
            for x in range(0, 2):
                if self.is_review_game:
                    self.players[x].deck = self.players[x].initial_deck
                else:
                    try:
                        decks = Deck.objects.filter(owner=User.objects.get(username=self.players[x].username))
                    except ObjectDoesNotExist:
                        decks = []
                    deck_to_use = None
                    for d in decks:
                        if d.id == self.players[x].deck_id:
                            deck_to_use = d.global_deck.deck_json
                    if self.players[x].deck_id == "the_coven":
                        deck_to_use = default_deck_vampire_lich()
                    elif self.players[x].deck_id == "keeper":
                        deck_to_use = default_deck_dwarf_tinkerer()
                    elif self.players[x].deck_id == "townies":
                        deck_to_use = default_deck_dwarf_bard()
                    elif self.players[x].deck_id == "draw_go":
                        deck_to_use = default_deck_genie_wizard()
                    else:
                        deck_to_use = deck_to_use if deck_to_use else random.choice([default_deck_genie_wizard(), default_deck_dwarf_tinkerer(), default_deck_dwarf_bard(), default_deck_vampire_lich()])
                    deck_hashes.append(hash_for_deck(deck_to_use))
                    card_names = []
                    for key in deck_to_use["cards"]:
                        for _ in range(0, deck_to_use["cards"][key]):
                            card_names.append(key)
                    for card_name in card_names:
                        self.players[x].add_to_deck(card_name, 1)
                    random.shuffle(self.players[x].deck)
                    self.players[x].initial_deck = copy.deepcopy(self.players[x].deck)
                    self.players[x].discipline = deck_to_use["discipline"]

            self.get_starting_artifacts()
            self.get_starting_spells()
            for x in range(0, 2):                
                self.players[x].draw(self.players[x].initial_hand_size())

            self.send_start_first_turn(message)
            if not self.is_review_game:
                game_record = GameRecord.objects.get(id=self.game_record_id)
                game_record.date_started = datetime.datetime.now()
                game_record.player_one = User.objects.get(username=self.players[0].username)
                try:
                    game_record.player_two = User.objects.get(username=self.players[1].username)
                except ObjectDoesNotExist:
                    game_record.player_two = User.objects.create(username=self.players[1].username)
                    game_record.player_two.save()
                game_record.player_one_deck = GlobalDeck.objects.get(cards_hash=deck_hashes[0])
                game_record.player_two_deck = GlobalDeck.objects.get(cards_hash=deck_hashes[1])
                game_record.save()

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
        if len(self.stack) > 0:
            print(f"can't end turn when there is a spell or attack on the stack")
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
            effect_targets = self.current_player().unchosen_targets_for_card(mob, self.current_player().username, effect_type="triggered")            
            index = 0
            for effect in mob.effects_triggered():
                if effect.name == "spell_from_yard":
                    spells = []
                    for card in self.current_player().played_pile:
                        if card.card_type == Card.spellCardType:
                            spells.append(card)
                    if len(spells) == 0:
                        continue
                    else:
                        if len(self.current_player().hand) < self.max_hand_size:
                            spell = random.choice(spells)
                            self.current_player().hand.append(spell)
                            self.current_player().played_pile.remove(spell)
                elif effect.name == "damage" and effect.trigger == "end_turn":
                    message = self.current_player().do_damage_effect(effect, effect_targets, index, message)
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

    def select_card_in_hand(self, message):
        card = None
        for card_in_hand in self.current_player().hand:
            if card_in_hand.id == message["card"]:
                card = card_in_hand
                break
        if not card:
            print(f"can't select that Card, it's not in hand")
            return None

        message["card_name"] = card.name
        has_mob_target = False

        if self.current_player().card_info_to_target["effect_type"] == "artifact_activated":
            artifact = self.current_player().selected_artifact()
            if artifact.effects[self.current_player().card_info_to_target["effect_index"]].name in ["duplicate_card_next_turn", "upgrade_card_next_turn", "decost_card_next_turn"]:
                message = self.activate_artifact_on_hand_card(message, self.current_player().selected_artifact(), card, self.current_player().card_info_to_target["effect_index"])
                self.unset_clickables(message["move_type"])
                self.set_clickables()
                # cards like Mana Coffin and Duplication Chamber
                artifact.effects[0].show_effect_animation = True
                return message

        if len(self.current_player().in_play + self.opponent().in_play) > 0:
            for mob in self.current_player().in_play + self.opponent().in_play:
                if not mob.has_ability("Lurker"):
                    has_mob_target = True

        if card.needs_artifact_target() and len(self.current_player().artifacts) == 0 and len(self.opponent().artifacts) == 0 :
            print(f"can't select artifact targetting spell with no artifacts in play")
            return None
        elif card.card_type == Card.spellCardType and card.needs_mob_target() and not has_mob_target:
            print(f"can't select mob targetting spell with no mobs without Lurker in play")
            return None
        elif card.has_ability("Instrument Required") and not self.current_player().has_instrument():
            print(f"can't cast {card.name} without having an Instument")
            return None
        elif card.card_type == Card.artifactCardType and not self.current_player().can_play_artifact():
            print(f"can't play artifact")
            return None
        elif card.card_type == Card.mobCardType and not self.current_player().can_summon():
            print(f"can't play Mob because can_summon is false")
            return None
        elif card.cost > self.current_player().current_mana():
            print(f"can't select, card costs too much - costs {card.cost}, mana available {self.current_player().current_mana()}")                        
            return None

        self.current_player().card_info_to_target["card_id"] = card.id
        self.current_player().card_info_to_target["effect_type"] = "spell_cast"
        # todo this is hardcoded, cant support multiple effects per card?
        self.current_player().card_info_to_target["effect_index"] = 0

        self.unset_clickables(message["move_type"])
        self.set_clickables()
        return message

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
            if effect.target_type == "being_cast_mob" and stack_spell_card.card_type != Card.mobCardType:
                print(f"can't select non-mob with mob-counterspell")
                return None
            return self.select_stack_target_for_spell(selected_spell, message)
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
                    print(f"can't attack {target_player.username} because a Mob has Guard")
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
            message["log_lines"].append(f"{attacking_card.name} intends to attack {self.current_player().username} for {self.power_with_tokens(attacking_card, self.opponent())}.")
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
            move_to_complete["log_lines"].append(f"{attacking_card.name} attacks {self.opponent().username} for {self.power_with_tokens(attacking_card, self.current_player())}.")
            self.opponent().damage(self.power_with_tokens(attacking_card, self.current_player()))
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
            message = artifact.do_effect(self.current_player(), e, message, effect_targets, 0)
            self.current_player().reset_card_info_to_target()
            if artifact.has_ability("multi_mob_attack"):
                e.targetted_this_turn.append(effect_targets[0])
        elif "hand_card" in message:
            hand_card = self.current_player().in_hand_card(message["hand_card"])
            message["log_lines"].append(f"{self.current_player().username} uses {artifact.name} on {hand_card.name}")
            effect_targets = []
            effect_targets.append({"id": hand_card.id, "target_type": "hand_card"})
            message = artifact.do_effect(self.current_player(), e, message, effect_targets, 0)
            self.current_player().reset_card_info_to_target()
        else:
            if e.target_type == "self":
                message = artifact.do_effect(self.current_player(), e, message, [{"id": message["username"], "target_type": "player"}], 0)
            elif e.target_type == "opponent":
                message = artifact.do_effect(self.current_player(), e, message, [{"id": self.opponent().username, "target_type": "player"}], 0)
            elif e.target_type == "all":
                message = artifact.do_effect(self.current_player(), e, message, [{"id": self.opponent().username, "target_type": "player"}], 0)
            elif e.target_type == "artifact_in_deck":
                message = artifact.do_effect(self.current_player(), e, message, [{"id": message["username"], "target_type": e.target_type}], 0)
            elif e.target_type == "self_mob":
                message = self.select_mob_target_for_artifact_activated_effect(artifact, message)
            else:
                target_player = self.players[0]
                if target_player.username != message["effect_targets"][0]["id"]:
                    target_player = self.players[1]
                message["log_lines"].append(f"{self.current_player().username} uses {artifact.name} on {target_player.username}")
                message["effect_targets"] = []
                message["effect_targets"].append({"id": target_player.username, "target_type": "player"})
                message = artifact.do_effect(self.current_player(), e, message, message["effect_targets"], 0)
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
            message = mob.do_effect(self.current_player(), e, message, effect_targets, 0)
        elif e.name == "unwind":
            if "defending_card" in message:
                message = mob.do_effect(self.current_player(), e, message, message["effect_targets"], 0)
                self.current_player().reset_card_info_to_target()
                mob.can_activate_abilities = False
            else:
                message["log_lines"].append(f"{self.current_player().username} activates {mob.name}.")
                message = self.current_player().target_or_do_mob_effects(mob, message, self.current_player().username, is_activated_effect=True)
        else:
            print(f"unsupported mob effect {e}")
        return message

    def make_card(self, message):
        if len(self.current_player().hand) < self.max_hand_size:
            self.current_player().add_to_deck(message["card"]["name"], 1, add_to_hand=True, card_cost=message["card"]["cost"])
        self.current_player().reset_card_choice_info()

    def cancel_make(self, message):
        for card in self.current_player().played_pile:
            if card.id == self.current_player().card_choice_info["effect_card_id"]:
                self.current_player().hand.append(card)
                self.current_player().played_pile.remove(card)
                break
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
        if card_type == Card.artifactCardType:
            if into_play:
                self.current_player().play_artifact(card)
            else:
                self.current_player().hand.append(card)
            self.current_player().deck.remove(card)
        if into_play:
            message["log_lines"].append(f"{message['username']} chose {card.name}.")

        self.current_player().reset_card_choice_info()
        return message

    def fetch_card_from_played_pile(self, message):
        """
            Fetch the selected card from current_player's deck
        """
        card = None
        for c in self.current_player().played_pile:
            if c.id == message['card']:
                card = c
                self.current_player().hand.append(card)
                self.current_player().played_pile.remove(card)
                break
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
            self.current_player().deck.remove(card_to_remove)
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

        # if card.id == player.card_info_to_target["card_id"]:
        #    player.reset_card_info_to_target()

        if player.username != card.owner_username:
            if player == self.current_player():
                player = self.opponent()
            else:
                player = self.current_player()

        # hax - Warty Evolver and maybe other cards that evolve on death
        did_evolve = card.has_effect("evolve")

        new_card = card
        if not did_evolve:
            new_card = self.factory_reset_card(card, player)
            # hax
            if new_card.name in ["Rolling Thunder", "Dwarf Council"]:
                new_card.effects[0].amount = card.effects[0].amount 
            elif new_card.name == "Fidget Spinner":
                new_card.power = card.power
                new_card.toughness = card.toughness
            # hax - does this more belong in factory_reset_card?
            new_card.level = card.level
        else:
            new_card.attacked = False
            new_card.damage = 0
            new_card.damage_to_show = 0
            new_card.damage_this_turn = 0
            new_card.turn_played = -1
            new_card.added_descriptions = ["Evolves."]


        if not card.is_token:
            player.played_pile.append(new_card)

        if did_kill and card.card_type == Card.mobCardType:
            self.remove_attack_for_mob(card)

        self.update_for_mob_changes_zones(player)

    def update_for_mob_changes_zones(self, player):

        # code for War Scorpion
        for e in player.in_play + player.artifacts:
            effect = e.effect_with_trigger("mob_changes_zones")
            if effect and effect.name == "toggle_symbiotic_fast":
                abilities_to_remove = []
                for ability in e.abilities:
                    if ability.name == "Fast":
                       abilities_to_remove.append(ability) 
                for ability in abilities_to_remove:
                    e.abilities.remove(ability)

            # code for Spirit of the Stampede and Vamp Leader
            if effect and effect.name == "set_token":
                tokens_to_remove = []
                for t in e.tokens:
                    if t.id == e.id:
                        tokens_to_remove.append(t)
                for t in tokens_to_remove:
                    e.tokens.remove(t)
                e.do_add_token_effect_on_mob(effect, player, e, player)

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
            if effect and effect.name == "set_token" and effect.target_type == "self_mobs":
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
                    e.do_add_token_effect_on_mob(effect, player, e, player)
                    
    def factory_reset_card(self, card, player):
        new_card = None
        # hax
        evolved = card.has_effect("evolve")
        for c in Card.all_card_objects():
            if c.name == card.name:
                new_card = copy.deepcopy(c)
        if evolved:
            card.attacked = False
            card.damage = 0
            card.damage_to_show = 0
            card.damage_this_turn = 0
            card.turn_played = -1
            return card
        else:
            new_card.id = card.id
            new_card.owner_username = player.username
            new_card = self.modify_new_card(new_card)
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
        
        if attacking_card.damage >= attacking_card.toughness_with_tokens():
            self.send_card_to_played_pile(attacking_card, self.current_player(), did_kill=True)

        if defending_card.damage >= defending_card.toughness_with_tokens():
            self.send_card_to_played_pile(defending_card, self.opponent(), did_kill=True)

    def remove_attack_for_mob(self, mob):
        if len(self.stack) > 0:
            action = self.stack[-1][0]
            if action["move_type"] == "ATTACK" and action["username"] != self.current_player().username:
                if action["card"] == mob.id:    
                    self.stack.pop()
                    self.actor_turn += 1

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
            elif t.multiplier == "self_mobs_and_artifacts":
                power += t.power_modifier * (len(player.artifacts) + len(player.in_play))
            else:
                power += t.power_modifier
        return power


class Player:

    def __init__(self, game, info, new=False, bot=None):
        self.username = info["username"]
        self.discipline = info["discipline"] if "discipline" in info else None
        self.deck_id = info["deck_id"] if "deck_id" in info else None
        self.initial_deck = [Card(c_info) for c_info in info["initial_deck"]] if "initial_deck" in info else []
        self.bot = bot

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
            self.card_choice_info = {"cards": [Card(c_info) for c_info in info["card_choice_info"]["cards"]], "choice_type": info["card_choice_info"]["choice_type"], "effect_card_id": info["card_choice_info"]["effect_card_id"] if "effect_card_id" in info["card_choice_info"] else None}

    def __repr__(self):
        return f"{self.as_dict()}"

    def as_dict(self):
        return {
            "username": self.username,
            "discipline": self.discipline,
            "hit_points": self.hit_points,
            "damage_this_turn": self.damage_this_turn,
            "damage_to_show": self.damage_to_show,
            "mana": self.mana,
            "max_mana": self.max_mana,
            "deck_id": self.deck_id,
            "card_info_to_target": self.card_info_to_target,
            "hand": [c.as_dict() for c in self.hand],
            "in_play": [c.as_dict() for c in self.in_play],
            "initial_deck": [c.as_dict() for c in self.initial_deck],
            "artifacts": [c.as_dict() for c in self.artifacts],
            "deck": [c.as_dict() for c in self.deck],
            "played_pile": [c.as_dict() for c in self.played_pile],
            "can_be_clicked": self.can_be_clicked,
            "abilities": [a.as_dict() for a in self.abilities],
            "card_choice_info": {"cards": [c.as_dict() for c in self.card_choice_info["cards"]], "choice_type": self.card_choice_info["choice_type"], "effect_card_id": self.card_choice_info["effect_card_id"] if "effect_card_id" in self.card_choice_info else None}
        }

    def max_max_mana(self):
        if self.discipline == "tech":
            return 99
        return 10

    def cards_each_turn(self):
        if self.discipline == "tech":
            return 5
        return 1

    def initial_hand_size(self):
        if self.discipline == "tech":
            return 5
        return 4

    def has_instants(self):
        for c in self.hand:
            if c.can_be_clicked:
                return True
        return False

    def has_mob_target(self):
        for mob in self.in_play:
            if not mob.has_ability("Lurker"):
                return True
        return False

    def has_artifact_target(self):
        for mob in self.artifacts:
            if not mob.has_ability("Lurker"):
                return True
        return False

    def has_defend(self):
        for c in self.in_play:
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

    def add_to_deck(self, card_name, count, add_to_hand=False, card_cost=None, reduce_cost=0):
        card = None
        for c in Card.all_card_objects():
            if c.name == card_name:
                card = c
        if not card:
            print("Error: couldn't add_to_deck " + card_name)
        for x in range(0, count):
            new_card = copy.deepcopy(card)
            if card_cost is not None:
                new_card.cost = card_cost
            new_card.cost = max(0, new_card.cost-reduce_cost)
            new_card.owner_username = self.username
            new_card.id = self.game.next_card_id
            self.game.next_card_id += 1
            new_card = self.game.modify_new_card(new_card)
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
            if len(self.deck) == 0 or len(self.hand) == self.game.max_hand_size:
                continue
            card = self.deck.pop()
            self.hand.append(card)
            for m in self.in_play + self.artifacts:
                for effect in m.effects_triggered():
                    effect.show_effect_animation = True
                    if effect.name == "hp_damage_random":
                        choice = random.choice(["hp", "damage"])
                        if choice == "hp":
                            return m.do_heal_effect_on_player(self, 1)
                        elif choice == "damage":
                            targets = [self.game.opponent()]
                            for m in self.game.opponent().in_play:
                                targets.append(m)
                            choice = random.choice(targets)
                            if choice == targets[0]:
                                m.do_damage_effect_on_player(self, choice, 1)
                            else:
                                self.do_damage_effect_on_mob(choice, self.game.opponent(), 1)

            for r in self.artifacts:
                for effect in r.effects_triggered():
                    if effect.name == "reduce_cost" and card.card_type == effect.target_type:
                        card.cost -= 1
                        card.cost = max(0, card.cost)
            for effect in card.effects_triggered():
                if effect.name == "reduce_cost":
                    card.cost -= 1
                    card.cost = max(0, card.cost)

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

    def do_mob_to_artifact_effect(self, effect_owner, target_mob, controller):
        self.game.send_card_to_played_pile(target_card, controller, did_kill=False)
        controller.played_pile.pop()
        if len(controller.artifacts) < 3:
            target_card.card_type = "artifact"
            controller.artifacts.append(target_mob)
        target_player.game.update_for_mob_changes_zones(target_player.game.players[0])
        target_player.game.update_for_mob_changes_zones(target_player.game.players[1])
        return [f"{effect_owner.username} turns {target_mob.name} into an artifact."]


    def do_kill_effect(self, e, effect_owner, target_mob):
        if e.target_type == "mob" or e.target_type == "artifact" or e.target_type == "mob_or_artifact":
            if target_mob:
                log_lines = [f"{self.name} kills {target_mob.name}."]
                effect_owner.do_kill_effect_on_mob(target_mob.id)
                return log_lines
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
            for card in effect_owner.in_play+effect_owner.artifacts+effect_owner.game.opponent().in_play+effect_owner.game.opponent().artifacts:
                if card.cost >= min_cost and card.cost <= max_cost and (instruments_ok or not card.has_ability("Instrument")):
                    card_ids_to_kill.append(card.id)
            for card_id in card_ids_to_kill: 
                effect_owner.do_kill_effect_on_mob(card_id)
            if len(card_ids_to_kill) > 0:
                return [f"{effect_owner.username} kills stuff ({len(card_ids_to_kill)})."]

    def do_kill_effect_on_mob(self, target_mob_id):
        target_card, target_player = self.game.get_in_play_for_id(target_mob_id)
        self.game.send_card_to_played_pile(target_card, target_player, did_kill=True)

    def do_remove_tokens_effect(self, card, e):
        if e.target_type == "self_mobs":
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
                if card.has_ability("Defend") and self.game.defendable_attack_on_stack(card):
                    return True
                if card.turn_played == self.game.turn:
                    if card.has_ability("Fast"):
                        return True
                    if card.has_ability("Ambush"):
                        for card in self.game.opponent().in_play:
                            if not card.has_ability("Lurker"):
                                return True
                    return False
        
                if len(self.game.stack) == 0 or card.has_ability("Instant Attack"):
                    return True
                return False

        print("should never happen, didnt find card in_play for can_select_for_attack")
        return False

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
        self.game.stack.append([copy.deepcopy(message), card.as_dict()])
        self.game.unset_clickables(message["move_type"])
        self.game.set_clickables()

        if not self.game.current_player().has_instants():
            self.game.actor_turn += 1
            message = self.play_card(card.id, message)
            self.game.unset_clickables(message["move_type"], cancel_damage=False)
            self.game.set_clickables()
            return message

        message["log_lines"].append(f"{self.username} starts to play {card.name}.")

        # todo rope
        return message

    def play_card(self, card_id, message):
        to_resolve = self.game.stack.pop()
        spell_to_resolve = to_resolve[0]
        spell_to_resolve["log_lines"] = []
        card = Card(to_resolve[1])

        for e in self.in_play + self.artifacts:
            for idx, effect in enumerate(e.effects_triggered()):
                if effect.trigger == "friendly_card_played" and effect.target_type == "this":
                    e.do_add_tokens_effect(e, effect, {idx: {"id": e.id, "target_type":"mob"}}, idx)

        spell_to_resolve["log_lines"].append(f"{self.username} plays {card.name}.")

        spell_to_resolve = self.play_mob_or_artifact(card, spell_to_resolve)

        if card.card_type == Card.mobCardType and card.has_ability("Shield"):
            card.shielded = True

        if len(card.effects) > 0 and card.card_type != Card.mobCardType:
            if not "effect_targets" in spell_to_resolve:
                spell_to_resolve["effect_targets"] = []

            for target in self.unchosen_targets_for_card(card, spell_to_resolve["username"]):
                spell_to_resolve["effect_targets"].append(target)

            for idx, target in enumerate(card.effects_spell() + card.effects_enter_play()):
                spell_to_resolve = card.do_effect(self, card.effects[idx], spell_to_resolve, spell_to_resolve["effect_targets"], idx)
           
            if len(spell_to_resolve["effect_targets"]) == 0:
                spell_to_resolve["effect_targets"] = None

            if len(card.effects) == 2:
                if card.effects[1].name == "improve_damage_when_used":
                    # hack for Rolling Thunder
                    card.effects[0].amount += 1
                    card.show_level_up = True
                if card.effects[1].name == "improve_effect_amount_when_cast":
                    # hack for Tech Crashhouse
                    card.effects[0].amount += 1
                    card.show_level_up = True
                if card.effects[1].name == "improve_effect_when_cast":
                    # hack for Tame Shop Demon
                    old_level = card.level
                    card.level += 1
                    card.level = min(card.level, len(card.effects[0].card_names)-1)
                    if card.level > old_level:
                        card.show_level_up = True

        if card.card_type == Card.spellCardType:
            if card.has_ability("Disappear"):
                card.show_level_up = True
            else:            
                self.played_pile.append(card)

        spell_to_resolve["card_name"] = card.name
        spell_to_resolve["show_spell"] = card.as_dict()

        return spell_to_resolve

    def unchosen_targets_for_card(self, card, username, effect_type="cast"):
        effect_targets = []
        effects = card.effects_spell() + card.effects_enter_play()
        if effect_type == "triggered":
            effects = card.effects_triggered()
        for idx, e in enumerate(effects):
            if e.target_type == "self":           
                effect_targets.append({"id": username, "target_type":"player"})
            elif e.target_type == "opponent":          
                effect_targets.append({"id": self.game.opponent().username, "target_type":"player"})
            elif e.target_type == "opponents_mobs":          
                effect_targets.append({"target_type":"opponents_mobs"})
            elif e.target_type == "all_players" or e.target_type == "all_mobs" or e.target_type == "self_mobs" or e.target_type == "all":          
                effect_targets.append({"target_type": e.target_type})
            elif e.target_type in ["all_cards_in_deck", "all_cards_in_played_pile"]:          
                effect_targets.append({"target_type": "player", "id": self.username})
        return effect_targets

    def play_mob_or_artifact(self, card, spell_to_resolve, do_effects=True):
        if card.card_type == Card.mobCardType:
            if len(card.effects) > 0 and do_effects:
                self.target_or_do_mob_effects(card, spell_to_resolve, spell_to_resolve["username"])
            for c in self.in_play + self.artifacts:
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
        elif card.card_type == Card.artifactCardType:
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
                        elif e.target_type == "all_players" or e.target_type == "all_mobs" or e.target_type == "self_mobs":           
                            effect_targets.append({"target_type": e.target_type})
                        elif e.target_type == "opponents_mob_random":           
                            effect_targets.append({"id": random.choice(self.game.opponent().in_play).id, "target_type":"mob"})
                        message["effect_targets"] = effect_targets
                    message = card.do_effect(self, e, message, message["effect_targets"], idx)
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
            message = card.do_effect(self, e, message, message["effect_targets"], idx)
        
        self.reset_card_info_to_target()
        return message

    # todo: make a has_effect method instead of checking name
    def has_brarium(self):
        for a in self.artifacts + self.in_play:
            if a.name == "Brarium" or a.name == "Enthralled Maker":
                return True
        return False

    def start_turn(self, message):
        self.game.turn_start_time = datetime.datetime.now()
        self.game.show_rope = False
        self.draw_for_turn()
        message = self.do_start_turn_card_effects_and_abilities(message)
        self.refresh_mana_for_turn()
        self.maybe_do_ice_prison()
        return message

    def draw_for_turn(self):
        if self.game.turn == 0:
            return

        draw_count = self.cards_each_turn() + self.game.global_effects.count("draw_extra_card")
        for m in self.in_play + self.artifacts:
            for e in m.effects_triggered():
                if e.name == "draw" and e.trigger == "start_turn":
                    # effects like Studious Child Vamp
                    e.show_effect_animation = True
                    draw_count += e.amount
        if self.has_brarium():
            draw_count -= 1
            if draw_count > 0:
                if self.discipline != "tech" or self.game.turn > 1:
                    self.draw(draw_count)
            if len(self.hand) < 10:                        
                Card({}).do_make_from_deck_effect(self)
        else:
            if self.discipline != "tech" or self.game.turn > 1:
                self.draw(draw_count)

    def do_start_turn_card_effects_and_abilities(self, message):
        for card in self.in_play + self.artifacts:
            if card.has_ability("Fade"):
                token = {
                    "turns": -1,
                    "power_modifier": -1,
                    "toughness_modifier": -1
                }
                effect = {
                    "tokens": [token],
                    "id": None
                }
                message["log_lines"] += card.do_add_token_effect_on_mob(CardEffect(effect), self, card, self)

            if not self.game.is_under_ice_prison():
                card.attacked = False

            card.can_activate_abilities = True

            for effect in card.effects_triggered():
                if effect.trigger == "start_turn" and effect.name != "draw":
                    message["log_lines"] += card.do_effect_start_turn(self, effect)

        for r in self.artifacts:
            r.can_activate_abilities = True
            r.effects_exhausted = {}
            message["log_lines"] += r.do_effect_artifact_only_start_turn(self)
        return message

    def refresh_mana_for_turn(self):
        if self.discipline == "tech":
            if self.game.turn <= 1:
                self.max_mana = 3
        else:
            self.max_mana += 1
            self.max_mana = min(self.max_max_mana(), self.max_mana)

        self.mana = 0
        self.mana += self.max_mana
        self.mana = min(self.max_max_mana(), self.mana)

    def maybe_do_ice_prison(self):
        if not self.game.is_under_ice_prison():
            return
        mobs_to_select_from = []
        for e in self.in_play:
            if e.attacked:
                mobs_to_select_from.append(e)
        if len(mobs_to_select_from) > 0:
            self.card_choice_info = {"cards": mobs_to_select_from, "choice_type": "select_mob_for_ice_prison"}

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
        #todo - we only support multi-effect artifacts, not mobs or spells yet
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
        self.card_choice_info = {"cards": [], "choice_type": None, "effect_card_id": None}

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
