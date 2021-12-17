import copy
import datetime
import random

from battle_wizard.game.card import Card, CardEffect
from battle_wizard.game.data import Constants
from battle_wizard.game.data import default_deck 
from battle_wizard.game.data import default_deck_genie_wizard 
from battle_wizard.game.data import default_deck_dwarf_tinkerer
from battle_wizard.game.data import default_deck_dwarf_bard
from battle_wizard.game.data import default_deck_vampire_lich
from battle_wizard.models import Deck
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist


class Player:

    max_hit_points = 30

    def __init__(self, game, info={}, bot=None):
        self.game = game
        self.is_ai = False
        self.max_hit_points = 30
        self.card_mana = 0
        self.about_to_draw_count = info["about_to_draw_count"] if "about_to_draw_count" in info else 0
        self.artifacts = [Card(c_info) for c_info in info["artifacts"]] if "artifacts" in info else []
        self.can_be_clicked = info["can_be_clicked"] if "can_be_clicked" in info else 0
        self.damage_this_turn = info["damage_this_turn"] if "damage_this_turn" in info else 0
        self.damage_to_show = info["damage_to_show"] if "damage_to_show" in info else 0
        self.deck = [Card(c_info) for c_info in info["deck"]] if "deck" in info else []
        self.deck_id = info["deck_id"] if "deck_id" in info else None
        self.discipline = info["discipline"] if "discipline" in info else None
        self.deck_exhaustion = info["deck_exhaustion"] if "deck_exhaustion" in info else 0
        self.hand = [Card(c_info) for c_info in info["hand"]] if "hand" in info else []
        self.hit_points = info["hit_points"] if "hit_points" in info else Player.max_hit_points
        # used for replays, todo: use a random seed to make replays easier per @silberman
        self.initial_deck = [Card(c_info) for c_info in info["initial_deck"]] if "initial_deck" in info else []
        self.in_play = [Card(c_info) for c_info in info["in_play"]] if "in_play" in info else []
        self.mana = info["mana"] if "about_to_draw_count" in info else 0
        self.max_mana = info["max_mana"] if "max_mana" in info else 0
        self.played_pile = [Card(c_info) for c_info in info["played_pile"]] if "played_pile" in info else []
        self.username = info["username"]

        if "card_info_to_target" in info:
            self.card_info_to_target = info["card_info_to_target"]
        else:
            self.card_info_to_target = None
            self.reset_card_info_to_target()
        if "card_choice_info" in info:
            self.card_choice_info = {"cards": [Card(c_info) for c_info in info["card_choice_info"]["cards"]], "choice_type": info["card_choice_info"]["choice_type"], "effect_card_id": info["card_choice_info"]["effect_card_id"]}
        else:
            self.card_choice_info = None
            self.reset_card_choice_info()

    def __repr__(self):
        return f"{self.as_dict()}"

    def as_dict(self):
        return {
            "about_to_draw_count": self.about_to_draw_count,
            "artifacts": [c.as_dict() for c in self.artifacts],
            "can_be_clicked": self.can_be_clicked,
            "card_choice_info": {"cards": [c.as_dict() for c in self.card_choice_info["cards"]], "choice_type": self.card_choice_info["choice_type"], "effect_card_id": self.card_choice_info["effect_card_id"] if "effect_card_id" in self.card_choice_info else None},
            "card_info_to_target": self.card_info_to_target,
            "damage_this_turn": self.damage_this_turn,
            "damage_to_show": self.damage_to_show,
            "deck": [c.as_dict() for c in self.deck],
            "deck_exhaustion": self.deck_exhaustion,
            "deck_id": self.deck_id,
            "discipline": self.discipline,
            "hand": [c.as_dict() for c in self.hand],
            "hit_points": self.hit_points,
            "initial_deck": [c.as_dict() for c in self.initial_deck],
            "in_play": [c.as_dict() for c in self.in_play],
            "is_ai": self.is_ai,
            "mana": self.mana,
            "max_mana": self.max_mana,
            "played_pile": [c.as_dict() for c in self.played_pile],
            "username": self.username,
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
        # todo: delete instants code or re-add it back
        return False
        for c in self.hand + self.in_play:
            if c.can_be_clicked:
                return True
        return False

    def has_enemy_mob_target(self):
        return len(self.my_opponent().in_play) > 0

    def has_friendly_mob_target(self):
        return len(self.in_play) > 0

    def my_opponent(self):
        if self == self.game.players[0]:
            return self.game.players[1]
        return self.game.players[0]

    def has_mob_target(self):
        return len(self.my_opponent().in_play) + len(self.in_play) > 0

    def has_artifact_target(self):
        return len(self.my_opponent().artifacts) + len(self.artifacts) > 0

    def has_mob_or_artifact_target(self):
        return self.has_artifact_target() or self.has_mob_target()

    def current_mana(self):
        return self.mana + self.mana_from_cards()

    def mana_from_cards(self):
        for artifact in self.artifacts:
            for idx, effect in enumerate(artifact.effects_for_type("check_mana")):
                artifact.resolve_effect(artifact.check_mana_effect_defs[idx], self, effect, {})
        mana = self.card_mana
        self.card_mana = 0
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
            if add_to_hand:
                self.hand.append(new_card)
            else:
                self.deck.append(new_card)
        return new_card

    def damage(self, amount):
        while amount > 0 and self.hit_points > 0:
            amount -= 1
            self.hit_points -= 1
            self.damage_this_turn += 1
            self.damage_to_show += 1

    def draw(self, number_of_cards):
        log_lines = []
        if number_of_cards > 0:
            log_lines = [f"{self.username} drew {number_of_cards} card for their turn."]
        for i in range(0, number_of_cards):
            if len(self.deck) == 0:
                self.deck_exhaustion += 1
                self.hit_points -= self.deck_exhaustion
                continue
            drawn_card = self.deck.pop()
            if len(self.hand) != self.game.max_hand_size:            
                self.hand.append(drawn_card)
                for idx, effect in enumerate(drawn_card.effects_for_type("was_drawn")):
                    effect.show_effect_animation = True
                    log_lines.append(drawn_card.resolve_effect(drawn_card.was_drawn_effect_defs[idx], self, effect, {})) 
                for m in self.in_play + self.artifacts + [drawn_card]:
                    for idx, effect in enumerate(m.effects_for_type("draw")):
                        effect.show_effect_animation = True
                        log_lines.append(m.resolve_effect(m.draw_effect_defs[idx], self, effect, {})) 
        return log_lines if len(log_lines) > 0 else None

    def spend_mana(self, amount):
        amount_to_spend = amount 

        while self.mana > 0 and amount_to_spend > 0:
            self.mana -= 1
            amount_to_spend -= 1

        log_lines = None
        for artifact in self.artifacts:
            for idx, effect in enumerate(artifact.effects_for_type("spend_mana")):
                log_lines = artifact.resolve_effect(artifact.spend_mana_effect_defs[idx], self, effect, {"amount_to_spend": amount_to_spend, "amount_spent": amount})
                if log_lines:
                    effect.show_effect_animation = True
        return log_lines

    def artifact_in_play(self, card_id):
        for card in self.artifacts:
            if card.id == card_id:
                return card
        return None

    def can_activate_artifact(self, card_id):
        for card in self.artifacts:
            if card.id == card_id:
                if not card.can_activate_effects:
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
                if card.attacked or not (card.can_attack_mobs or card.can_attack_players):
                    return False
                if card.strength_with_tokens(self) <= 0:
                    return False
                for t in card.tokens:
                    if t.set_can_act == False:
                        return False                                                
                if len(self.game.stack) == 0:
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
        mana_log_lines = self.spend_mana(card.cost)
        if mana_log_lines:
            message["log_lines"] += mana_log_lines

        self.game.actor_turn += 1
        self.game.stack.append([copy.deepcopy(message), card.as_dict()])
        self.game.reset_clickables(message["move_type"])

        if not self.game.current_player().has_instants():
            self.game.actor_turn += 1
            message = self.play_card(card.id, message)
            self.game.reset_clickables(message["move_type"], cancel_damage=False)
            return message

        message["log_lines"].append(f"{self.username} starts to play {card.name}.")

        # todo rope
        return message

    def play_card(self, card_id, message):
        to_resolve = self.game.stack.pop()
        spell_to_resolve = to_resolve[0]
        spell_to_resolve["log_lines"] = []
        card = Card(to_resolve[1])
        return card.resolve(self, spell_to_resolve)

    def play_mob_or_artifact(self, card, spell_to_resolve, do_effects=True):
        if card.card_type == Constants.mobCardType:
            if len(card.effects) > 0 and do_effects:
                self.target_or_do_mob_effects(card, spell_to_resolve, spell_to_resolve["username"])
            for c in self.in_play + self.artifacts:
                for idx, effect in enumerate(c.effects_for_type("play_friendly_mob")):
                    effect.show_effect_animation = True
                    spell_to_resolve["log_lines"].append(c.resolve_effect(c.play_friendly_mob_effect_defs[idx], self, effect, {}))

            self.play_mob(card)
        elif card.card_type == Constants.artifactCardType:
            self.play_artifact(card)
        return spell_to_resolve

    def play_mob(self, card):
        self.in_play.append(card)
        self.update_for_mob_changes_zones()

        card.turn_played = self.game.turn

    def play_artifact(self, artifact):
        self.artifacts.append(artifact)
        artifact.turn_played = self.game.turn

    def target_or_do_mob_effects(self, card, message, username):
        effects = card.effects_for_type("enter_play")
        if len(effects) == 0:
            return message

        targeted_effect = None
        for e in effects:
            if e.target_type in ["any", "mob", "enemy_mob", "friendly_mob"]:
                targeted_effect = e

        if targeted_effect:
            self.card_info_to_target["effect_type"] = "mob_comes_into_play"
            if targeted_effect.target_type == "any":
                self.card_info_to_target["card_id"] = card.id
            elif targeted_effect.target_type in ["mob"]:
                if self.game.players[0].has_target_for_mob_effect() or self.game.players[1].has_target_for_mob_effect():
                    self.card_info_to_target["card_id"] = card.id
            elif targeted_effect.target_type in ["enemy_mob"]:
                if self.my_opponent().has_target_for_mob_effect():
                    self.card_info_to_target["card_id"] = card.id
            elif targeted_effect.target_type in ["friendly_mob"]:
                if self.game.current_player().has_target_for_mob_effect():
                    self.card_info_to_target["card_id"] = card.id
        else:
            effect_targets = card.unchosen_targets(self, "enter_play")
            message["effect_targets"] = effect_targets
            for idx, e in enumerate(effects):
                message["log_lines"].append(card.resolve_effect(card.enter_play_effect_defs[idx], self, e, effect_targets[idx])) 

        return message

    def resolve_mob_effect(self, card_id, message):
        card = None
        for c in self.in_play:
            if c.id == card_id:
                card = c
        if not "effect_targets" in message:
            message["effect_targets"] = []
        for idx, e in enumerate(card.effects_for_type("enter_play")):
            if len(message["effect_targets"]) <= idx:
                if e.target_type == "self":           
                    message["effect_targets"].append({"id": message["username"], "target_type":"player"})
                elif e.target_type == "opponent":           
                    message["effect_targets"].append({"id": self.my_opponent().username, "target_type":"player"})
            message["log_lines"].append(card.resolve_effect(card.enter_play_effect_defs[idx], self, e, message["effect_targets"][idx])) 
        
        self.reset_card_info_to_target()
        return message

    def start_turn(self, message):
        self.game.turn_start_time = datetime.datetime.now()
        self.game.show_rope = False
        log_lines = self.draw_for_turn()
        if log_lines:
            message["log_lines"] += log_lines
        message = self.do_start_turn_card_effects(message)
        self.refresh_mana_for_turn()
        self.game.reset_clickables(message["move_type"])
        return message

    def draw_for_turn(self):
        if self.game.turn == 0:
            return
        log_lines = []
        if self.discipline != "tech" or self.game.turn > 1:
            line = self.draw(self.draw_count())
            if line:
                log_lines.append(line)
        return log_lines if len(log_lines) > 0 else None

    def draw_count(self):
        self.about_to_draw_count = self.cards_each_turn()
        for card in self.in_play + self.artifacts:
            for idx, effect in enumerate(card.effects_for_type("before_draw")):
                card.resolve_effect(card.before_draw_effect_defs[idx], self, effect, {})
        return self.about_to_draw_count

    def do_start_turn_card_effects(self, message):
        for card in self.in_play + self.artifacts:
            card.attacked = False
            card.can_attack_mobs = True
            card.can_attack_players = True
            card.can_activate_effects = True
            for idx, effect in enumerate(card.effects_for_type("start_turn")):
                effect.show_effect_animation = True
                message["log_lines"].append(card.resolve_effect(card.start_turn_effect_defs[idx], self, effect, {}))

        for r in self.artifacts:
            r.can_activate_effects = True
            for effect in r.effects:
                effect.exhausted = False
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

    def can_summon(self):
        if len(self.in_play) == 7:
            return False
        return True

    def can_play_artifact(self):
        if len(self.artifacts) == 3:
            return False
        return True

    def set_targets_for_selected_mob(self):
        target_type = None
        card = self.selected_mob()
        targeted_effect = None
        for e in card.effects:
            if e.target_type in ["any", "mob", "enemy_mob", "friendly_mob"]:
                targeted_effect = e
        target_type = targeted_effect.target_type
        self.game.set_targets_for_target_type(target_type)

    def remove_temporary_tokens(self):
        for c in self.in_play:
            perm_tokens = []
            oldHitPoints = c.hit_points_with_tokens()
            for t in c.tokens:
                t.turns -= 1
                if t.turns != 0:
                    perm_tokens.append(t)
            c.tokens = perm_tokens
            newHitPoints = c.hit_points_with_tokens()
            hit_points_change_from_tokens = oldHitPoints - newHitPoints
            if hit_points_change_from_tokens > 0:
                c.damage -= min(hit_points_change_from_tokens, c.damage_this_turn)  

    def make_card(self, message):
        if len(self.hand) < self.game.max_hand_size:
            self.add_to_deck(message["card"]["name"], 1, add_to_hand=True, card_cost=message["card"]["cost"])
        self.reset_card_choice_info()

    def cancel_make(self):
        for card in self.played_pile:
            if card.id == self.card_choice_info["effect_card_id"]:
                self.hand.append(card)
                self.played_pile.remove(card)
                break
        self.reset_card_choice_info()

    def fetch_card_from_played_pile(self, message):
        """
            Fetch the selected card from current_player's deck
        """
        card = None
        for c in self.played_pile:
            if c.id == message['card']:
                card = c
                self.hand.append(card)
                self.played_pile.remove(card)
                break
        message["log_lines"].append(f"{self.username} chose {card.name}.")
        self.reset_card_choice_info()
        return message

    def fetch_card(self, message, card_type, into_play=False):
        """
            Fetch the selected card from current_player's deck
        """
        card = None
        for c in self.deck:
            if c.id == message['card']:
                card = c
        if card_type == Constants.artifactCardType:
            if into_play:
                self.play_artifact(card)
            else:
                self.hand.append(card)
            self.deck.remove(card)
        if into_play:
            message["log_lines"].append(f"{self.username} chose {card.name}.")

        self.reset_card_choice_info()
        return message

    def finish_riffle(self, message):
        """
            Fetch the selected card from current_player's deck
        """
        chosen_card = None
        for c in self.deck:
            if c.id == message['card']:
                chosen_card = c
        for card in self.card_choice_info["cards"]:
            card_to_remove = None
            for deck_card in self.deck:
                if card.id == deck_card.id:
                   card_to_remove = deck_card 
            self.deck.remove(card_to_remove)
            if card.id != chosen_card.id:
                self.send_card_to_played_pile(card, did_kill=False)
                message["log_lines"].append(f"{self.username} puts {card.name} into their played pile.")
        self.deck.append(chosen_card)
        self.draw(1)
        self.reset_card_choice_info()
        return message

    def select_card_in_hand(self, message):
        card = None
        for card_in_hand in self.hand:
            if card_in_hand.id == message["card"]:
                card = card_in_hand
                break
        if not card:
            print(f"can't select that Card, it's not in hand")
            return

        if "override_selection_for_lookahead" not in message and not card.can_be_clicked:
            print(f"can't select that Card, it can't be clicked maybe because there are no legal targets like with Lurker")
            return

        message["card_name"] = card.name
        has_mob_target = False

        if self.card_info_to_target["effect_type"] == "artifact_activated":
            artifact = self.selected_artifact()
            if artifact.effects[self.card_info_to_target["effect_index"]].target_type == "hand_card":
                message = self.game.activate_artifact_on_hand_card(message, self.selected_artifact(), card, self.card_info_to_target["effect_index"])
                self.game.reset_clickables(message["move_type"])
                # cards like Mana Coffin and Duplication Chamber
                artifact.effects[0].show_effect_animation = True
                return message

        if len(self.in_play + self.my_opponent().in_play) > 0:
            has_mob_target = True

        if card.needs_artifact_target() and len(self.artifacts) == 0 and len(self.my_opponent().artifacts) == 0 :
            print(f"can't select artifact targetting spell with no artifacts in play")
            return None
        elif card.card_type == Constants.spellCardType and card.needs_mob_target() and not has_mob_target:
            print(f"can't select mob targetting spell with no targettable mobs in play")
            return None
        elif card.card_type == Constants.artifactCardType and not self.can_play_artifact():
            print(f"can't play artifact")
            return None
        elif card.card_type == Constants.mobCardType and not self.can_summon():
            print(f"can't play Mob because can_summon is false")
            return None
        elif card.cost > self.current_mana():
            print(f"can't select, card costs too much - costs {card.cost}, mana available {self.current_mana()}")                        
            return None

        self.card_info_to_target["card_id"] = card.id
        self.card_info_to_target["effect_type"] = "spell_cast"
        # todo this is hardcoded, cant support multiple effects per card?
        self.card_info_to_target["effect_index"] = 0

        self.game.reset_clickables(message["move_type"])

        return message

    def set_targets_for_mob_effect(self):
        for card in self.in_play:
            card.can_be_clicked = True

    def set_targets_for_artifact_effect(self):
        for card in self.artifacts:
            card.can_be_clicked = True

    def set_targets_for_damage_effect(self):
        for card in self.in_play:
            card.can_be_clicked = True
        self.can_be_clicked = True

    def set_targets_for_any_enemy_effect(self, effect):
        for card in self.in_play:
            card.can_be_clicked = True
        self.can_be_clicked = True

    def set_targets_for_hand_card_effect(self):
        for card in self.hand:
            card.can_be_clicked = True

    def set_targets_for_player_mob_effect(self):
        for card in self.in_play:
            if card.id != self.card_info_to_target["card_id"]:
                card.can_be_clicked = True

    def has_target_for_mob_effect(self):
        return len(self.in_play) > 0

    def clear_damage_this_turn(self):
        for c in self.in_play:
            c.damage_this_turn = 0
        self.damage_this_turn = 0

    def send_card_to_played_pile(self, card, did_kill=True):
        """
            Send the card to the player's played_pile and reset any temporary effects on the card
        """
        if card in self.artifacts:
            self.artifacts.remove(card)
        if card in self.in_play:
            self.in_play.remove(card)
        card.do_leaves_play_effects(self, did_kill=did_kill)

        player = self
        if self.username != card.owner_username:
            if self == self.game.current_player():
                player = self.my_opponent()
            else:
                player = self.game.current_player()

        # these effects override the normal factory_reset
        if len(card.effects_for_type("sent_to_played_pile")) > 0:
            for idx, effect in enumerate(card.effects_for_type("sent_to_played_pile")):
                effect.show_effect_animation = True
                card.resolve_effect(card.sent_to_played_piled_effect_defs[idx], self, effect, {}) 
        else:
            card = Card.factory_reset_card(card, player)
        if not card.is_token:
            player.played_pile.append(card)

        if did_kill and card.card_type == Constants.mobCardType:
            self.game.remove_attack_for_mob(card)

        player.update_for_mob_changes_zones()

    def update_for_mob_changes_zones(self):
        for e in self.in_play + self.artifacts:
            for idx, effect in enumerate(e.effects_for_type("mob_changes_zones")):
                effect.show_effect_animation = True
                e.resolve_effect(e.mob_changes_zones_effect_defs[idx], self, effect, {})                     
    
    def get_starting_deck(self):
        if len(self.initial_deck):
            self.deck = self.initial_deck
        else:
            card_names = []
            deck_to_use = self.deck_for_id_or_url(self.deck_id)
            for key in deck_to_use["cards"]:
                for _ in range(0, deck_to_use["cards"][key]):
                    card_names.append(key)
            for card_name in card_names:
                self.add_to_deck(card_name, 1)
            random.shuffle(self.deck)
            self.initial_deck = copy.deepcopy(self.deck)
            self.discipline = deck_to_use["discipline"]

    def deck_for_id_or_url(self, id_or_url):
        try:
            decks = Deck.objects.filter(owner=User.objects.get(username=self.username))
        except ObjectDoesNotExist:
            decks = []
        deck_to_use = None
        for d in decks:
            if d.id == id_or_url:
                deck_to_use = d.global_deck.deck_json
        if id_or_url == "the_coven":
            deck_to_use = default_deck_vampire_lich()
        elif id_or_url == "keeper":
            deck_to_use = default_deck_dwarf_tinkerer()
        elif id_or_url == "townies":
            deck_to_use = default_deck_dwarf_bard()
        elif id_or_url == "draw_go":
            deck_to_use = default_deck_genie_wizard()
        elif id_or_url == "vanilla":
            deck_to_use = default_deck()
        else:
            deck_to_use = deck_to_use if deck_to_use else default_deck()
            # deck_to_use = deck_to_use if deck_to_use else random.choice([default_deck_genie_wizard(), default_deck_dwarf_tinkerer(), default_deck_dwarf_bard(), default_deck_vampire_lich()])

        return deck_to_use
