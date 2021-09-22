import copy
import datetime
import random

from battle_wizard.game.card import Card, CardEffect, CardAbility
from battle_wizard.game.data import Constants
from battle_wizard.game.data import default_deck_genie_wizard 
from battle_wizard.game.data import default_deck_dwarf_tinkerer
from battle_wizard.game.data import default_deck_dwarf_bard
from battle_wizard.game.data import default_deck_vampire_lich
from battle_wizard.models import Deck
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist


class Player:

    max_hit_points = 30

    def __init__(self, game, info, new=False, bot=None):
        self.is_ai = False
        self.max_hit_points = 30
        self.username = info["username"]
        self.discipline = info["discipline"] if "discipline" in info else None
        self.deck_id = info["deck_id"] if "deck_id" in info else None
        self.card_mana = 0

        # used for replays, todo: use a random seed to make replays easier per @silberman
        self.initial_deck = [Card(c_info) for c_info in info["initial_deck"]] if "initial_deck" in info else []

        self.game = game
        if new:
            self.hit_points = Player.max_hit_points
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
            "is_ai": self.is_ai,
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

    def has_opponents_mob_target(self):
        return len(self.my_opponent().in_play) > 0

    def my_opponent(self):
        if self == self.game.players[0]:
            return self.game.players[1]
        return self.game.players[0]

    def has_mob_target(self):
        return len(self.my_opponent().in_play) + len(self.in_play) > 0

    def has_artifact_target(self):
        return len(self.my_opponent().artifacts) + len(self.artifacts) > 0

    def has_defend(self):
        for c in self.in_play:
            if c.can_be_clicked:
                return True
        return False

    def current_mana(self):
        return self.mana + self.mana_from_cards()

    def mana_from_cards(self):
        for artifact in self.artifacts:
            for idx, effect in enumerate(artifact.effects_for_type("check_mana")):
                effect.show_effect_animation = True
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
            new_card = Card.modify_new_card(new_card, self.game)
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
        log_lines = []
        for i in range(0, number_of_cards):
            if len(self.deck) == 0:
                for c in self.played_pile:
                    self.deck.append(c)
                self.played_pile = [] 
            if len(self.deck) == 0 or len(self.hand) == self.game.max_hand_size:
                continue
            drawn_card = self.deck.pop()
            self.hand.append(drawn_card)
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

        for artifact in self.artifacts:
            for idx, effect in enumerate(artifact.effects_for_type("spend_mana")):
                effect.show_effect_animation = True
                artifact.resolve_effect(artifact.spend_mana_effect_defs[idx], self, effect, {"amount_to_spend": amount_to_spend})

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
                if card.attacked or not (card.can_attack_mobs or card.can_attack_players):
                    return False
                if card.power_with_tokens(self) <= 0:
                    return False
                for t in card.tokens:
                    if t.set_can_act == False:
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
            if card.has_ability("Slow Artifact"):
                card.effects_exhausted.append(card.effects[0].name)
        return spell_to_resolve

    def play_mob(self, card):
        self.in_play.append(card)
        self.update_for_mob_changes_zones()

        card.turn_played = self.game.turn

    def play_artifact(self, artifact):
        self.artifacts.append(artifact)
        artifact.turn_played = self.game.turn
        # self.update_for_mob_changes_zones(self)
        # self.my_opponent().update_for_mob_changes_zones()        

    def cant_die_ability(self):
        for a in self.abilities:
            if a.descriptive_id == "Can't Die":
                return a
        return None 

    def reduce_draw_ability(self):
        for a in self.abilities:
            if a.descriptive_id == "Reduce Draw":
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
                if self.game.players[0].has_target_for_mob_effect(effects[0].target_restrictions) or self.game.players[1].has_target_for_mob_effect(effects[0].target_restrictions):
                    self.card_info_to_target["card_id"] = card.id
                    if is_activated_effect:
                        self.card_info_to_target["effect_type"] = "mob_activated"
                    else:
                        self.card_info_to_target["effect_type"] = "mob_comes_into_play"
            elif effects[0].target_type in ["opponents_mob"]:
                if self.my_opponent().has_target_for_mob_effect(effects[0].target_restrictions):
                    self.card_info_to_target["card_id"] = card.id
                    if is_activated_effect:
                        self.card_info_to_target["effect_type"] = "mob_activated"
                    else:
                        self.card_info_to_target["effect_type"] = "mob_comes_into_play"
            elif effects[0].target_type in ["self_mob"]:
                if self.game.current_player().has_target_for_mob_effect(effects[0].target_restrictions):
                    self.card_info_to_target["card_id"] = card.id
                    if is_activated_effect:
                        self.card_info_to_target["effect_type"] = "mob_activated"
                    else:
                        self.card_info_to_target["effect_type"] = "mob_comes_into_play"
            else:
                effect_targets = []
                has_targets = "effect_targets" in message
                for idx, e in enumerate(effects):
                    if e.target_type == "opponents_mob_random" and len(self.my_opponent().in_play) == 0:
                        continue
                    # todo think about this weird repeated setting of effect_targets in message
                    if not has_targets:
                        if e.target_type in ["self", "all_cards_in_deck", "artifact", "all_cards_in_played_pile"]:  
                            effect_targets.append({"id": username, "target_type":"player"})
                        elif e.target_type == "this":           
                            effect_targets.append({"id": card.id, "target_type":"mob"})
                        elif e.target_type == "all_players" or e.target_type == "all_mobs" or e.target_type == "self_mobs":           
                            effect_targets.append({"target_type": e.target_type})
                        elif e.target_type == "opponents_mob_random":           
                            effect_targets.append({"id": random.choice(self.my_opponent().in_play).id, "target_type":"mob"})
                        elif e.target_type == None:           
                            effect_targets.append({})
                        message["effect_targets"] = effect_targets
                    message["log_lines"].append(card.resolve_effect(card.enter_play_effect_defs[idx], self, e, effect_targets[idx])) 

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
            message["log_lines"].append(card.resolve_effect(card.enter_play_effect_defs[idx], self, e, message["effect_targets"][idx])) 
        
        self.reset_card_info_to_target()
        return message

    def start_turn(self, message):
        self.game.turn_start_time = datetime.datetime.now()
        self.game.show_rope = False
        log_lines = self.draw_for_turn()
        if log_lines:
            message["log_lines"] += log_lines
        message = self.do_start_turn_card_effects_and_abilities(message)
        self.refresh_mana_for_turn()
        return message

    def draw_for_turn(self):
        if self.game.turn == 0:
            return

        draw_count = self.cards_each_turn() + self.game.global_effects.count("draw_extra_card")

        if self.reduce_draw_ability():
            draw_count -= 1            

        log_lines = []
        if self.discipline != "tech" or self.game.turn > 1:
            log_lines.append(self.draw(draw_count))
        return log_lines if len(log_lines) > 0 else None

    def do_start_turn_card_effects_and_abilities(self, message):
        for card in self.in_play + self.artifacts:
            card.attacked = False
            card.can_attack_mobs = True
            card.can_attack_players = True

            card.can_activate_abilities = True

            for idx, effect in enumerate(card.effects_for_type("start_turn")):
                effect.show_effect_animation = True
                message["log_lines"].append(card.resolve_effect(card.start_turn_effect_defs[idx], self, effect, {}))

        for r in self.artifacts:
            r.can_activate_abilities = True
            r.effects_exhausted = {}
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

    def remove_temporary_abilities(self):
        perm_abilities = []
        for a in self.abilities:
            if a.turns > 0:
                a.turns -= 1
                if a.turns != 0:
                    perm_abilities.append(a)
            else:
                perm_abilities.append(a)
        self.abilities = perm_abilities

    def remove_temporary_tokens(self):
        for c in self.in_play:
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

    def get_starting_artifacts(self):
        found_artifact = None
        for c in self.deck:
            if len(c.abilities) > 0 and c.abilities[0].descriptive_id == "Starts in Play":
                found_artifact = c
                break
        if found_artifact:
            found_artifact.turn_played = self.game.turn
            self.play_artifact(found_artifact)
            self.deck.remove(found_artifact)
        
    def get_starting_spells(self):
        found_spell = None
        for c in self.deck:
            if len(c.abilities) > 0 and c.abilities[0].descriptive_id == "Starts in Hand":
                found_spell = c
                break
        if found_spell:
            self.hand.append(found_spell)
            self.deck.remove(found_spell)
        
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
            return None

        message["card_name"] = card.name
        has_mob_target = False

        if self.card_info_to_target["effect_type"] == "artifact_activated":
            artifact = self.selected_artifact()
            if artifact.effects[self.card_info_to_target["effect_index"]].name in ["duplicate_card_next_turn", "upgrade_card_next_turn", "decost_card_next_turn"]:
                message = self.game.activate_artifact_on_hand_card(message, self.selected_artifact(), card, self.card_info_to_target["effect_index"])
                self.game.unset_clickables(message["move_type"])
                self.game.set_clickables()
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
        elif card.has_ability("Instrument Required") and not self.has_instrument():
            print(f"can't cast {card.name} without having an Instument")
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

        self.game.unset_clickables(message["move_type"])
        self.game.set_clickables()
        return message

    def set_targets_for_mob_effect(self, target_restrictions):
        if len(target_restrictions) > 0 and list(target_restrictions[0].keys())[0] == "power":
            for card in self.in_play:
                if card.power_with_tokens(self.opponent()) >= list(target_restrictions[0].values())[0]:
                    card.can_be_clicked = True
            return

        if len(target_restrictions) > 0 and list(target_restrictions[0].keys())[0] == "min_cost":
            for card in self.in_play:
                if card.cost >= list(target_restrictions[0].values())[0]:
                    card.can_be_clicked = True
            return

        for card in self.in_play:
            card.can_be_clicked = True

    def set_targets_for_artifact_effect(self, target_restrictions):
        if len(target_restrictions) > 0 and list(target_restrictions[0].keys())[0] == "min_cost":
            did_target = False
            for card in self.artifacts:
                if card.cost >= list(target_restrictions[0].values())[0]:
                    card.can_be_clicked = True
                    did_target = True
            return

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

        if effect:
            for info in effect.targetted_this_turn:
                if info["target_type"] == "player":
                    self.can_be_clicked = False
                else:
                    card, _ = self.game.get_in_play_for_id(info["id"])
                    if card:
                        card.can_be_clicked = False

    def set_targets_for_hand_card_effect(self):
        for card in self.hand:
            card.can_be_clicked = True

    def set_targets_for_player_mob_effect(self, target_restrictions):
        if len(target_restrictions) > 0 and list(target_restrictions[0].keys())[0] == "needs_guard":
            set_targets = False
            for e in self.in_play:
                if e.id != self.card_info_to_target["card_id"]:
                    if e.has_effect("force_attack_guard_first"):
                        set_targets = True
                        e.can_be_clicked = True
            return

        set_targets = False
        for card in self.in_play:
            if card.id != self.card_info_to_target["card_id"]:
                card.can_be_clicked = True
                set_targets = True

    def has_target_for_mob_effect(self, target_restrictions):
        if len(target_restrictions) > 0 and target_restrictions[0] == "needs_guard":
            for e in self.in_play:
                if e.id != self.card_info_to_target["card_id"]:
                    if e.has_effect("force_attack_guard_first"):
                        return True
            return False

        if len(target_restrictions) > 0 and list(target_restrictions[0].keys())[0] == "power":
            for e in self.in_play:
                if e.power_with_tokens(self) >= list(target_restrictions[0].values())[0]:
                    return True
            return False

        return len(self.in_play) > 0

    def clear_artifact_effects_targetted_this_turn(self):
        # for Multishot Bow
        for r in self.artifacts:
            for e in r.effects:
                e.targetted_this_turn = []

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

        # hax - Warty Evolver and maybe other cards that evolve on death
        did_evolve = card.has_effect("evolve")

        if did_evolve:
            card.attacked = False
            card.damage = 0
            card.damage_to_show = 0
            card.damage_this_turn = 0
            card.turn_played = -1
            card.added_descriptions = ["Evolves."]
        else:
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
        else:
            deck_to_use = deck_to_use if deck_to_use else random.choice([default_deck_genie_wizard(), default_deck_dwarf_tinkerer(), default_deck_dwarf_bard(), default_deck_vampire_lich()])

        return deck_to_use
