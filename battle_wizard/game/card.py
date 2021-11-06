import copy
import json
import math
import random

from battle_wizard.game.data import Constants
from create_cards.models import CustomCard

class Card:
    
    def __init__(self, info):
        self.id = info["id"] if "id" in info else -1
        self.attacked = info["attacked"] if "attacked" in info else False
        # use by artifacts with activated abilities
        self.can_activate_effects = info["can_activate_effects"] if "can_activate_effects" in info else True
        self.can_attack_mobs = info["can_attack_mobs"] if "can_attack_mobs" in info else False
        self.can_attack_players = info["can_attack_players"] if "can_attack_players" in info else False
        self.can_be_clicked = info["can_be_clicked"] if "can_be_clicked" in info else False
        # used by artifacts such as Upgrade Chanber and Mana Coffin
        self.card_for_effect = Card(info["card_for_effect"]) if "card_for_effect" in info and info["card_for_effect"] else None
        self.card_subtype = info["card_subtype"] if "card_subtype" in info else None
        # the only current subtype in use is "tun-only" for spells that can't be cast as instants
        self.card_type = info["card_type"] if "card_type" in info else Constants.mobCardType
        self.cost = info["cost"] if "cost" in info else 0
        self.damage = info["damage"] if "damage" in info else 0
        self.damage_this_turn = info["damage_this_turn"] if "damage_this_turn" in info else 0
        self.damage_to_show = info["damage_to_show"] if "damage_to_show" in info else 0
        self.discipline = info["discipline"] if "discipline" in info else None
        self.effects = [CardEffect(e, self.id) for _, e in enumerate(info["effects"])] if "effects" in info else []
        # used by artifacts to say which effects are useable
        self.effects_can_be_clicked = info["effects_can_be_clicked"] if "effects_can_be_clicked" in info else []
        # used by artifacts to say which effects are un-useable
        self.description = info["description"] if "description" in info else None
        self.image = info["image"] if "image" in info else None
        self.is_custom = info["is_custom"] if "is_custom" in info else False
        self.is_token = info["is_token"] if "is_token" in info else False
        self.level = info["level"] if "level" in info else None
        self.name = info["name"] if "name" in info else None
        # used by artifacts with activated effects
        self.original_description = info["original_description"] if "original_description" in info else None
        self.owner_username = info["owner_username"] if "owner_username" in info else None
        self.strength = info["strength"] if "strength" in info else None
        self.show_level_up = info["show_level_up"] if "show_level_up" in info else False
        self.tokens = [CardToken(t) for t in info["tokens"]] if "tokens" in info else []
        self.hit_points = info["hit_points"] if "hit_points" in info else None
        self.turn_played = info["turn_played"] if "turn_played" in info else -1

        self.power_points = info["power_points"] if "power_points" in info else self.power_points_value()

        # card.effects get mapped into these lists of defs defined on Card
        self.action_added_to_stack_effect_defs = []
        self.activated_effect_defs = []        
        self.after_attack_effect_defs = []
        self.after_card_resolves_effect_defs = []
        self.after_deals_damage_effect_defs = []
        self.after_deals_damage_opponent_effect_defs = []
        self.after_declared_attack_effect_defs = []
        self.after_shuffle_effect_defs = []
        self.before_draw_effect_defs = []
        self.before_is_damaged_effect_defs = []
        self.check_mana_effect_defs = []
        self.discarded_end_of_turn_effect_defs = []
        self.draw_effect_defs = []
        self.enter_play_effect_defs = []
        self.end_turn_effect_defs = []
        self.leave_play_effect_defs = []
        self.mob_changes_zones_effect_defs = []
        self.play_friendly_mob_effect_defs = []
        self.select_mob_target_effect_defs = []
        self.select_mob_target_override_effect_defs = []
        self.sent_to_played_piled_effect_defs = []
        self.spell_effect_defs = []
        self.spend_mana_effect_defs = []
        self.start_turn_effect_defs = []
        self.was_drawn_effect_defs = []

        for effect in self.effects:
            self.create_effect_def(effect)

    def power_points_value(self):
        power_points = 0
        for e in self.effects:
            power_points += e.power_points
        power_points -= self.cost * 2
        if self.strength:
            power_points += self.strength
        if self.hit_points:
            power_points += self.hit_points
        return power_points

    def create_effect_def(self, effect):
        if effect.effect_type == "action_added_to_stack":
            self.action_added_to_stack_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "activated":
            self.activated_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "after_attack": 
            self.after_attack_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "after_deals_damage": 
            self.after_deals_damage_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "after_deals_damage_opponent": 
            self.after_deals_damage_opponent_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "after_declared_attack":
            self.after_declared_attack_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "after_card_resolves": 
            self.after_card_resolves_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "after_shuffle": 
            self.after_shuffle_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "before_draw":
            self.before_draw_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "before_is_damaged":
            self.before_is_damaged_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "check_mana": 
            self.check_mana_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "discarded_end_of_turn": 
            self.discarded_end_of_turn_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "draw": 
            self.draw_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "end_turn": 
            self.end_turn_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "enter_play":
            self.enter_play_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "leave_play":
             self.leave_play_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "mob_changes_zones": 
            self.mob_changes_zones_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "play_friendly_mob": 
            self.play_friendly_mob_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "select_mob_target": 
            self.select_mob_target_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "select_mob_target_override": 
            self.select_mob_target_override_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "sent_to_played_pile": 
            self.sent_to_played_piled_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "spell":
            self.spell_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "spend_mana": 
            self.spend_mana_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "start_turn": 
            self.start_turn_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "was_drawn": 
            self.was_drawn_effect_defs.append(self.effect_def_for_id(effect))

    def __repr__(self):
        return f"{self.as_dict()}"

    def as_dict(self):
        return {
            "attacked": self.attacked,
            "can_activate_effects": self.can_activate_effects,
            "can_attack_mobs": self.can_attack_mobs,
            "can_attack_players": self.can_attack_players,
            "can_be_clicked": self.can_be_clicked,
            "card_for_effect": self.card_for_effect.as_dict() if self.card_for_effect else None,
            "card_subtype": self.card_subtype,
            "card_type": self.card_type,
            "cost": self.cost,
            "damage": self.damage,
            "damage_this_turn": self.damage_this_turn,
            "damage_to_show": self.damage_to_show,
            "discipline": self.discipline,
            "description": self.description,
            "effects": [e.as_dict() for e in self.effects],
            "effects_can_be_clicked": self.effects_can_be_clicked,
            "id": self.id,
            "image": self.image,
            "is_custom": self.is_custom,
            "is_token": self.is_token,
            "level": self.level,
            "name": self.name,
            "original_description": self.original_description,
            "owner_username": self.owner_username,
            "power_points": self.power_points,
            "strength": self.strength,
            "show_level_up": self.show_level_up,
            "tokens": [t.as_dict() for t in self.tokens] if self.tokens else [],
            "hit_points": self.hit_points,
            "turn_played": self.turn_played,
        }


    def effect_def_for_id(self, effect):
        eid = effect.id
        if eid == "ambush":
            return self.do_ambush_effect          
        elif eid == "add_fade":
            return self.do_add_fade_effect          
        elif eid == "add_fast":
            return self.do_add_fast_effect          
        elif eid == "add_mob_effects":
            return self.do_add_mob_effects_effect
        elif eid == "add_symbiotic_fast":
            return self.do_add_symbiotic_fast_effect
        elif eid == "add_tokens":
            return self.do_add_tokens_effect
        elif eid == "allow_instant_cast":
            return self.do_allow_instant_cast_effect
        elif eid == "allow_defend_response":
            return self.do_allow_defend_response_effect
        elif eid == "augment_mana":
            return self.do_augment_mana_effect
        elif eid == "buff_strength_hit_points_from_mana":
            return self.do_buff_strength_hit_points_from_mana_effect
        elif eid == "create_card":
            return self.do_create_card_effect
        elif eid == "create_random_townie":
            return self.do_create_random_townie_effect
        elif eid == "create_random_townie_cheap":
            return self.do_create_random_townie_effect_cheap
        elif eid == "damage":
            return self.do_damage_effect
        elif eid == "deal_excess_damage_to_controller":
            return self.do_deal_excess_damage_to_controller_effect
        elif eid == "decost_card_next_turn":
            return self.do_decost_card_next_turn_effect
        elif eid == "decrease_max_mana":
            return self.do_decrease_max_mana_effect
        elif eid == "discard_random":
            return self.do_discard_random_effect_on_player
        elif eid == "disappear":
            return self.do_disappear_effect
        elif eid in ["duplicate_card_next_turn", "store_for_decosting", "upgrade_card_next_turn"]:
            return self.do_store_card_for_next_turn_effect
        elif eid == "double_strength":
            return self.do_double_strength_effect_on_mob
        elif eid == "drain":
            return self.do_drain_hp_effect
        elif eid == "draw":
            return self.do_draw_effect_on_player
        elif eid == "draw_on_deal_damage":
            return self.do_draw_on_deal_damage_effect            
        elif eid == "draw_if_damaged_opponent":
            return self.do_draw_if_damaged_opponent_effect_on_player
        elif eid == "draw_or_resurrect":
           return self.do_draw_or_resurrect_effect
        elif eid == "duplicate_card_next_turn":
            return self.do_duplicate_card_next_turn_effect
        elif eid == "enable_activated_effect":
            return self.do_enable_activated_effect_effect
        elif eid == "entwine":
            return self.do_entwine_effect
        elif eid == "fetch_card":
            return self.do_fetch_card_effect_on_player
        elif eid == "fetch_card_into_play":
            return self.do_fetch_card_into_play_effect_on_player
        elif eid == "guard":
            return self.do_guard_effect
        elif eid == "gain_for_hit_points":
            return self.do_gain_for_hit_points_effect
        elif eid == "hp_damage_random":
            return self.do_hp_damage_random_effect
        elif eid == "heal":            
            return self.do_heal_effect
        elif eid == "improve_damage_all_effects_when_used":
            return self.do_improve_damage_when_used_effect            
        elif eid == "improve_damage_when_used":
            return self.do_improve_damage_when_used_effect            
        elif eid == "improve_effect_amount_when_cast":
            return self.do_improve_effect_amount_when_cast_effect            
        elif eid == "improve_effect_when_cast":
            return self.do_improve_effect_when_cast_effect            
        elif eid == "keep":
            return self.do_keep_effect
        elif eid == "kill":
            return self.do_kill_effect
        elif eid == "lose_lurker":
            return self.do_lose_lurker_effect
        elif eid == "make":
            return self.do_make_effect
        elif eid == "make_cheap_with_option":
            return self.do_make_cheap_with_option_effect
        elif eid == "make_from_deck":
            return self.do_make_from_deck_effect
        elif eid == "make_token":
            return self.do_make_token_effect
        elif eid == "make_untargettable":
            return self.do_make_untargettable_effect
        elif eid == "mana":
            return self.do_mana_effect_on_player
        elif eid == "mana_increase_max":
            return self.do_mana_increase_max_effect_on_player
        elif eid == "mana_reduce":
            return self.do_mana_reduce_effect_on_player
        elif eid == "mana_set_max":
            return self.do_mana_set_max_effect
        elif eid == "mob_to_artifact":
            return self.do_mob_to_artifact_effect
        elif eid == "preserve_stats":
            return self.do_preserve_stats_effect
        elif eid == "preserve_effect_improvement":
            return self.do_preserve_effect_improvement_effect
        elif eid == "pump_strength":
            return self.do_pump_strength_effect_on_mob
        elif eid == "redirect_mob_spell":
           return self.do_redirect_mob_spell_effect
        elif eid == "reduce_cost":
           return self.do_reduce_cost_effect
        elif eid == "reduce_draw":
           return self.do_reduce_draw_effect
        elif eid == "refresh_mana":
            return self.do_refresh_mana_effect
        elif eid == "remove_symbiotic_fast":
            return self.do_remove_symbiotic_fast_effect
        elif eid == "remove_tokens":
            return self.do_remove_tokens_effect
        elif eid == "restrict_effect_targets_min_cost":
            return self.do_restrict_effect_targets_min_cost_effect
        elif eid == "restrict_effect_targets_mob_targetter":
            return self.do_restrict_effect_targets_mob_targetter_effect
        elif eid == "restrict_effect_targets_mob_with_guard":
            return self.do_restrict_effect_targets_mob_with_guard_effect
        elif eid == "restrict_effect_targets_mob_with_strength":
            return self.do_restrict_effect_targets_mob_with_strength_effect            
        elif eid == "riffle":
            return self.do_riffle_effect
        elif eid == "set_can_attack":
            return self.do_set_can_attack_effect           
        elif eid == "set_token":
            return self.do_set_token_effect
        elif eid == "shield":
            return self.do_shield_effect
        elif eid == "slow_artifact":
            return self.do_slow_artifact_effect           
        elif eid == "spell_from_yard":
            return self.do_spell_from_yard_effect           
        elif eid == "stack_counter":
           return  self.do_counter_card_effect
        elif eid == "start_in_hand":
           return  self.do_start_in_hand_effect
        elif eid == "start_in_play":
           return  self.do_start_in_play_effect
        elif eid == "store_mana":
            return  self.do_store_mana_effect            
        elif eid == "summon_from_deck":
            return self.do_summon_from_deck_effect_on_player
        elif eid == "summon_from_deck_artifact":
            return self.do_summon_from_deck_artifact_effect_on_player
        elif eid == "summon_from_hand":
            return self.do_summon_from_hand_effect
        elif eid == "switch_hit_points":
            return self.do_switch_hit_points_effect
        elif eid == "take_extra_turn":
            return self.do_take_extra_turn_effect_on_player
        elif eid == "take_control":
            return self.do_take_control_effect
        elif eid == "unwind":
            return self.do_unwind_effect
        elif eid == "upgrade_card_next_turn":
            return self.do_upgrade_card_next_turn_effect
        elif eid == "use_stored_mana":
            return self.do_use_stored_mana_effect
        else:
            print(f"UNSUPPORTED EFFECT ID: {eid}")

    @staticmethod
    def all_card_objects(require_images=False, include_tokens=True):
        return [Card(c_info) for c_info in all_cards(require_images, include_tokens)]
    
    @staticmethod  
    def player_for_username(game, username):
        if game.players[0].username == username:
            return game.players[0]
        return game.players[1]

    @staticmethod
    def factory_reset_card(card, player):
        new_card = None
        # hax
        for c in Card.all_card_objects():
            if c.name == card.name:
                new_card = copy.deepcopy(c)
        new_card.id = card.id
        new_card.owner_username = player.username
        return new_card

    def resolve(self, player, spell_to_resolve):
        print(f"resolving {self.name}")
        for m in player.in_play + player.artifacts:
            for idx, effect in enumerate(m.effects_for_type("friendly_card_played")):
                if effect.target_type == "this":
                    m.do_add_tokens_effect(player, effect, {"id": m.id, "target_type":"mob"})

        spell_to_resolve["log_lines"].append(f"{player.username} plays {self.name}.")

        if self.card_type != Constants.spellCardType:
            spell_to_resolve = player.play_mob_or_artifact(self, spell_to_resolve)

        if len(self.effects) > 0 and self.card_type != Constants.mobCardType:
            if not "effect_targets" in spell_to_resolve:
                spell_to_resolve["effect_targets"] = []

            for target in self.unchosen_targets(player):
                spell_to_resolve["effect_targets"].append(target)

            for idx, effect_def in enumerate(self.spell_effect_defs):
                target_info = spell_to_resolve["effect_targets"][idx]
                if "target_type" in target_info and target_info["target_type"] == "mob":
                    target_mob, _ = player.game.get_in_play_for_id(target_info["id"])
                    if not target_mob:
                        # mob was removed from play by a different effect
                        continue
                log_lines = self.resolve_effect(effect_def, player, self.effects_for_type("spell")[idx], spell_to_resolve["effect_targets"][idx])
                if log_lines:
                    [spell_to_resolve["log_lines"].append(line) for line in log_lines]

            for idx, effect_def in enumerate(self.enter_play_effect_defs):
                target_info = spell_to_resolve["effect_targets"][idx]
                if "target_type" in target_info and target_info["target_type"] == "mob":
                    target_mob, _ = player.game.get_in_play_for_id(target_info["id"])
                    if not target_mob:
                        # mob was removed from play by a different effect
                        continue
                spell_to_resolve["log_lines"].append(
                    self.resolve_effect(effect_def, player, self.effects_for_type("enter_play")[idx], spell_to_resolve["effect_targets"][idx])
                )

            if len(spell_to_resolve["effect_targets"]) == 0:
                spell_to_resolve["effect_targets"] = None

        if self.card_type == Constants.spellCardType:
            player.played_pile.append(self)

        for idx, effect_def in enumerate(self.after_card_resolves_effect_defs):
            spell_to_resolve["log_lines"].append(
                self.resolve_effect(effect_def, player, self.effects_for_type("after_card_resolves")[idx], spell_to_resolve["effect_targets"][idx])
            )

        spell_to_resolve["card_names"] = [self.name]
        spell_to_resolve["show_spell"] = self.as_dict()

        return spell_to_resolve

    def unchosen_targets(self, player, effect_type=None):
        effect_targets = []
        effects = self.effects_for_type("spell")  + self.effects_for_type("enter_play") 
        if effect_type:
            effects = self.effects_for_type(effect_type)
        for e in effects:
            if e.target_type == "self":           
                effect_targets.append({"id": player.username, "target_type":"player"})
            elif e.target_type == "opponent":          
                effect_targets.append({"id": player.game.opponent().username, "target_type":"player"})
            elif e.target_type == "opponents_mobs":          
                effect_targets.append({"target_type":"opponents_mobs"})
            elif e.target_type == "all_players" or e.target_type == "all_mobs" or e.target_type == "self_mobs" or e.target_type == "all":          
                effect_targets.append({"target_type": e.target_type})
            elif e.target_type in ["all_cards_in_deck", "all_cards_in_played_pile"]:          
                effect_targets.append({"target_type": "player", "id": player.username})
            elif e.target_type == None: # improve_damage_when_used has no target_type     
                effect_targets.append({})
        return effect_targets

    def resolve_effect(self, effect_def, effect_owner, effect, target_info):
        # print(f"Resolve effect: {effect.name}");
        if effect.counters >= 1 and effect.id != "store_mana":
            effect.counters -= 1
        log_lines = effect_def(effect_owner, effect, target_info)
        mana_log_lines = None
        if effect.cost > 0:
            mana_log_lines = effect_owner.spend_mana(effect.cost)
        if effect.cost_hp > 0:
            effect_owner.hit_points -= effect.cost_hp

        all_log_lines = None
        if log_lines or mana_log_lines: 
            all_log_lines = []
            if log_lines:
                all_log_lines += log_lines
            if mana_log_lines:
                all_log_lines += mana_log_lines
        return all_log_lines

    def do_ambush_effect(self, effect_owner, effect, target_info):
        self.can_attack_mobs = True
        # clone the game so we can do a move in the cloned game to select the mob with Ambush
        # then, check if there are any mobs that can be attacked in the cloned game (e.g. mob.can_be_clicked == True)
        game_copy = copy.deepcopy(effect_owner.game)
        for mob in game_copy.current_player().in_play:
            if mob.id == self.id:
                game_copy.play_move({"username": effect_owner.username, "move_type": "SELECT_MOB", "card": self.id})        
        found_attackable_mob = False
        for m in game_copy.opponent().in_play:
            if m.can_be_clicked:                
                found_attackable_mob = True
        self.can_attack_mobs = found_attackable_mob

    def do_add_fast_effect(self, effect_owner, effect, target_info):
        self.can_attack_players = True
        self.can_attack_mobs = True

    def do_add_fade_effect(self, effect_owner, effect, target_info):
        token = {
            "turns": -1,
            "strength_modifier": -1,
            "hit_points_modifier": -1
        }
        effect = {
            "tokens": [token],
            "id": None
        }
        return self.do_add_token_effect_on_mob(CardEffect(effect, 0), effect_owner, self, effect_owner)

    def do_add_mob_effects_effect(self, effect_owner, effect, target_info):
        target_id = target_info["id"]
        target_mob, controller = effect_owner.game.get_in_play_for_id(target_id)
        for e in effect.effects:
            existing_effect = False
            for ee in target_mob.effects:
                if ee.id == e.id:
                    existing_effect = ee
            if existing_effect:
                existing_effect.enabled = True
            else:
                target_mob.effects.append(e)
                target_mob.create_effect_def(e)
                if e.effect_type == "enter_play":
                    self.resolve_effect(target_mob.enter_play_effect_defs[-1], effect_owner, e, {}) 
        return [f"{target_mob.name} gets {effect.name}."]

    def do_add_tokens_effect(self, effect_owner, effect, target_info):
        print("do_add_tokens_effect")
        if effect.target_type == 'self_mobs':
            for token in effect.tokens:
                for mob in effect_owner.in_play:
                    self.do_add_token_effect_on_mob(effect, effect_owner, mob, effect_owner)
            return [f"{effect_owner.username} adds {str(effect.tokens[0])} to their own mobs."]
        else:
            target_mob, controller = effect_owner.game.get_in_play_for_id(target_info["id"])
            for token in effect.tokens:
                self.do_add_token_effect_on_mob(effect, effect_owner, target_mob, controller)
            return [f"{effect_owner.username} adds {str(effect.tokens[0])} to {target_mob.name}."]

    def do_add_token_effect_on_mob(self, effect, effect_owner, target_mob, controller):
        token = copy.deepcopy(effect.tokens[0])
        token.id = effect.id_for_game
        if token.multiplier and token.multiplier == "half_self_mobs":
            for x in range(0, math.floor(len(effect_owner.in_play)/2)):
                target_mob.tokens.append(token)
        elif token.multiplier and token.multiplier == "self_mobs":
            for x in range(0, len(effect_owner.in_play)):
                target_mob.tokens.append(token)
        else:
            target_mob.tokens.append(token)
        if target_mob.hit_points_with_tokens() - target_mob.damage <= 0:
            controller.send_card_to_played_pile(target_mob, did_kill=True)
        return [f"{target_mob.name} gets {token}."]


    def do_allow_defend_response_effect(self, effect_owner, effect, target_info):
        self.can_be_clicked = True

    def do_allow_instant_cast_effect(self, effect_owner, effect, target_info):
        if effect_owner.current_mana() >= self.cost:
                self.can_be_clicked = True
 
    def do_augment_mana_effect(self, effect_owner, effect, target_info):
        store_effect = None
        for e in self.effects:
            if e.id == "store_mana":
                store_effect = e
        effect_owner.card_mana += store_effect.counters

    def do_buff_strength_hit_points_from_mana_effect(self, effect_owner, effect, target_info):
        mana_count = effect_owner.current_mana()

        log_lines = [f"{self.name} is now {self.strength}/{self.hit_points}."]
        mana_log_lines = effect_owner.spend_mana(effect_owner.current_mana())
        if mana_log_lines:
            log_lines += mana_log_lines
        self.strength += mana_count
        self.hit_points += mana_count
        return log_lines

    def do_counter_card_effect(self, effect_owner, effect, target_info):
        effect_owner.game.actor_turn += 1
        stack_spell = None
        for spell in effect_owner.game.stack:
            if spell[1]["id"] == target_info["id"]:
                stack_spell = spell
                break

        # the card was countered by a different counterspell
        if not stack_spell:
            return None

        effect_owner.game.stack.remove(stack_spell)
        card = Card(stack_spell[1])
        effect_owner.game.current_player().send_card_to_played_pile(card, did_kill=False)
        return [f"{card.name} was countered by {effect_owner.game.opponent().username}."]

    def do_create_card_effect(self, effect_owner, effect, target_info):
        if effect.target_type == "self":
            player = Card.player_for_username(effect_owner.game, target_info["id"])            

            for x in range(0, effect.amount):
                if len(player.hand) == player.game.max_hand_size:
                    return
                card_to_create = None
                for card in Card.all_card_objects():
                    if card.name == effect.card_names[0]:
                        card_to_create = card
                player.hand.append(copy.deepcopy(card_to_create))
                player.hand[-1].id = player.game.next_card_id
                player.game.next_card_id += 1

            return [f"{self.name} creates {effect.amount} {effect.card_names[0]}."]
        else:
            print(f"unsupported target_type {effect.target_type} for create_card effect")
            return None

    def do_create_random_townie_effect(self, effect_owner, effect, target_info):
        log_lines = self.do_create_random_townie_effect_with_reduce_cost(effect_owner, effect, target_info, 0)
        if effect.counters == 0:
            self.effects.pop(0)
            self.activated_effect_defs.pop(0)
            for a in self.effects:
                if a.effect_type == "activated":
                    a.enabled = True
            self.description = self.original_description
        return log_lines
        
    def do_create_random_townie_effect_cheap(self, effect_owner, effect, target_info):
        return self.do_create_random_townie_effect_with_reduce_cost(effect_owner, effect, target_info, 1)

    def do_create_random_townie_effect_with_reduce_cost(self, effect_owner, effect, target_info, reduce_cost):
        player = Card.player_for_username(effect_owner.game, target_info["id"])            
        if len(player.hand) >= player.game.max_hand_size:
            return
        townies = []
        for c in Card.all_card_objects():
            for e in c.effects:
                if e.id == "is_townie":
                    townies.append(c)
        for x in range(0, effect.amount):
            t = random.choice(townies)
            player.add_to_deck(t.name, 1, add_to_hand=True, reduce_cost=reduce_cost)
        if effect.amount == 1:
            return [f"{player.username} makes {effect.amount} Townie."]
        return [f"{player.username} makes {effect.amount} Townies."]

    def do_damage_effect(self, effect_owner, effect, target_info):
        damage_amount = effect.amount 

        target_type = target_info["target_type"] if "target_type" in target_info else None
        target_id = target_info["id"] if "id" in target_info else None
        if effect.amount_id == "hand":            
            damage_amount = len(effect_owner.hand)
        elif effect.amount_id:
            print(f"unknown amount_id: {effect.amount_id}")
        if effect.target_type == "self":
            return self.do_damage_effect_on_player(effect, effect_owner, effect_owner, effect.amount, effect.amount_id)
        elif target_type == "player":
            target_player = Card.player_for_username(effect_owner.game, target_id)
            return self.do_damage_effect_on_player(effect, effect_owner, target_player, effect.amount, effect.amount_id)
        elif target_type == "opponents_mobs":
            return self.damage_mobs(effect_owner.game, effect_owner.game.opponent().in_play, damage_amount, effect_owner.username, f"{effect_owner.game.opponent().username}'s mobs")
        elif effect.target_type == "enemy_mob_random":
            if len(effect_owner.my_opponent().in_play) > 0:
                mob = random.choice(effect_owner.my_opponent().in_play)
                _, controller = effect_owner.game.get_in_play_for_id(mob.id)
                log_lines = [f"{effect_owner.username} deals {damage_amount} damage to {mob.name}."]
                self.do_damage_effect_on_mob(effect, mob, controller, effect.amount, effect.amount_id)
                return log_lines
        elif target_type == "all_mobs" or target_type == "all":
            damage_taker = "all mobs"
            if target_type == "all":
                damage_taker = "all mobs and players"
            log_lines = self.damage_mobs(effect_owner.game, effect_owner.game.players[0].in_play + effect_owner.game.players[1].in_play, damage_amount, effect_owner.username, damage_taker)
            if target_type == "all":
                effect_owner.game.players[0].damage(damage_amount)
                effect_owner.game.players[1].damage(damage_amount)
            return log_lines
        else:
            target_mob, controller = effect_owner.game.get_in_play_for_id(target_info['id'])
            log_lines = [f"{effect_owner.username} deals {damage_amount} damage to {target_mob.name}."]
            self.do_damage_effect_on_mob(effect, target_mob, controller, effect.amount, effect.amount_id)
            return log_lines

    def damage_mobs(self, game, mobs, damage_amount, damage_dealer, damage_taker):
        dead_mobs = []
        for mob in mobs:
            mob.deal_damage_with_effects(damage_amount, game.opponent())
            if mob.damage >= mob.hit_points_with_tokens():
                dead_mobs.append(mob)
        for mob in dead_mobs:
            game.opponent().send_card_to_played_pile(mob, did_kill=True)
        return [f"{damage_dealer} deals {damage_amount} damage to {damage_taker}."]

    def do_damage_effect_on_player(self, effect, effect_owner, target_player, amount, amount_id=None):
        actual_amount = None
        if amount_id == "hand":    
            actual_amount = len(effect_owner.hand)       
        elif not amount_id:
            actual_amount = amount    
        else:
            print(f"unknown amount_id: {amount_id}")

        target_player.damage(actual_amount)
        for idx, e in enumerate(self.effects_for_type("after_deals_damage_opponent")):
            self.resolve_effect(self.after_deals_damage_opponent_effect_defs[idx], effect_owner, e, {"damage": actual_amount}) 
        return [f"{self.name} deals {actual_amount} damage to {target_player.username}."]            

    def do_damage_effect_on_mob(self, effect, target_card, controller, amount, amount_id=None):
        damage_amount = amount 
        if amount_id == "hand":            
            damage_amount = len(self.hand)
        elif amount_id:
            print(f"unknown amount_id: {amount_id}")

        target_card.deal_damage_with_effects(damage_amount, controller)
        for idx, e in enumerate(self.effects_for_type("after_deals_damage")):
            self.resolve_effect(self.after_deals_damage_effect_defs[idx], effect_owner, e, {"damage": actual_amount}) 

        if target_card.damage >= target_card.hit_points_with_tokens():
            controller.send_card_to_played_pile(target_card, did_kill=True)

    def do_deal_excess_damage_to_controller_effect(self, effect_owner, effect, target_info):
        if effect_owner.username != effect_owner.game.current_player().username:
            return
        if "damage_possible" not in target_info:
            return
        if target_info["damage"] == 0:
            # this can happen when a Shield gets popped
            return
        excess_damage = target_info["damage_possible"] - target_info["damage"]
        effect_owner.my_opponent().damage(excess_damage)

    def do_decost_card_next_turn_effect(self, effect_owner, effect, target_info):
        if self.card_for_effect:                     
            self.card_for_effect.cost = max(0, self.card_for_effect.cost - 1)
            effect_owner.hand.append(self.card_for_effect)
            self.card_for_effect = None
    
    def do_duplicate_card_next_turn_effect(self, effect_owner, effect, target_info):
        if self.card_for_effect:
            new_card = effect_owner.add_to_deck(self.card_for_effect.name, 1, add_to_hand=True)
            effect_owner.hand.append(self.card_for_effect)
            new_card.cost = self.card_for_effect.cost
            self.card_for_effect = None

    def do_upgrade_card_next_turn_effect(self, effect_owner, effect, target_info):
        if self.card_for_effect:
            previous_card = None
            for c in Card.all_card_objects():
                if self.card_for_effect.name == c.name:
                    previous_card = c
            previous_card.upgrade(previous_card)
            effect_owner.hand.append(previous_card)
            self.card_for_effect = None

    def do_decrease_max_mana_effect(self, effect_owner, effect, target_info):
        # Mana Shrub leaves play
        if effect.enabled:
            effect_owner.max_mana -= effect.amount
            effect_owner.mana = min(effect_owner.max_mana, effect_owner.mana)

    def do_discard_random_effect_on_player(self, effect_owner, effect, target_info):
        if effect.target_type == "opponent":
            target_player = effect_owner.my_opponent()
        else:
            target_player = Card.player_for_username(effect_owner.game, target_info["id"])
        amount = effect.amount
        amount_id = effect.amount_id
        discard_amount = amount 
        if amount_id == "hand":            
            discard_amount = len(target_player.hand)
        elif amount_id:
            print(f"unknown amount_id: {amount_id}")

        amount_to_log = max(discard_amount, len(target_player.hand))

        while discard_amount > 0 and len(target_player.hand) > 0:
            discard_amount -= 1
            card = random.choice(target_player.hand)
            target_player.hand.remove(card)
            target_player.send_card_to_played_pile(card, did_kill=False)

        if amount_to_log == 1:
            return [f"{target_player.username} discards {amount_to_log} card from {self.name}."]
        elif amount_to_log > 0:
            return [f"{target_player.username} discards {amount_to_log} cards from {self.name}."]

    def do_disappear_effect(self, effect_owner, effect, target_info):
        print("do_disappear_effect")
        if self in effect_owner.hand:
            effect_owner.hand.remove(self)        
        if self in effect_owner.played_pile:
            effect_owner.played_pile.remove(self)
        self.show_level_up = True
        return [f"{self.name} disappears from the game instead of going to {effect_owner.username}'s yard."]

    def do_double_strength_effect_on_mob(self, effect_owner, effect, target_info):
        target_mob, controller = effect_owner.game.get_in_play_for_id(target_info['id'])
        target_mob.strength += target_mob.strength_with_tokens(controller)
        return [f"{self.name} doubles the strength of {target_mob.name}."]

    def do_drain_hp_effect(self, effect_owner, effect, target_info):
        effect_owner.hit_points += target_info["damage"]
        effect_owner.hit_points = min(effect_owner.max_hit_points, effect_owner.hit_points)
    
    def do_draw_effect_on_player(self, effect_owner, effect, target_info):
        if effect.target_type == "self":
            target_id = effect_owner.username
        else:
            target_id = target_info["id"]
        target_player = Card.player_for_username(effect_owner.game, target_id)
        amount_to_draw = effect.amount
        if effect.multiplier == "self_mobs":
            amount_to_draw = amount_to_draw * len(effect_owner.in_play)
        target_player.draw(amount_to_draw)
        return [f"{target_player.username} draws {amount_to_draw} from {self.name}."]

    def do_draw_on_deal_damage_effect(self, effect_owner, effect, target_info):
        effect_owner.draw(effect.amount)

    def do_draw_if_damaged_opponent_effect_on_player(self, effect_owner, effect, target_info):
        target_player = effect_owner
        if target_player.game.opponent().damage_this_turn > 0:
            target_player.draw(effect.amount)
            return [f"{target_player.username} draws {effect.amount} from {self.name}."]
        return None
    
    def do_draw_or_resurrect_effect(self, effect_owner, effect, target_info):
        # effect_owner
        amount = effect_owner.mana 
        log_lines = effect_owner.spend_mana(amount)
        dead_mobs = []
        for card in effect_owner.played_pile:
            if card.card_type == Constants.mobCardType:
                dead_mobs.append(card)
        random.shuffle(dead_mobs)
        choices = ["draw", "resurrect"]
        for x in range(0, amount):
            if len(dead_mobs) == 0 or random.choice(choices) == 'draw' or len(effect_owner.in_play) == 7:
                effect_owner.draw(1)
            else:
                mob = dead_mobs.pop()
                effect_owner.played_pile.remove(mob)
                effect_owner.play_mob(mob)
        ritual_line = f"{effect_owner.username} did the RITUAL OF THE NIGHT."
        if log_lines:
            log_lines.append(ritual_line)
        else:
            log_lines = [ritual_line]
        return log_lines

    def do_enable_activated_effect_effect(self, effect_owner, effect, target_info):
        # todo don't hardcode turning them all off, only needed for Arsenal, which doesn't even equip anymore
        for e in self.effects_for_type("activated"):
            if e.effect_to_activate:
                e.enabled = False
        activated_effect = copy.deepcopy(effect.effect_to_activate)
        activated_effect.id_for_game = self.id
        activated_effect.enabled = True
        self.description = activated_effect.description
        self.effects.insert(0, activated_effect)
        self.activated_effect_defs.insert(0,self.effect_def_for_id(activated_effect))
        self.can_activate_effects = True
        return [f"{effect_owner.username} activates {self.name}."]

    def do_entwine_effect(self, effect_owner, effect, target_info):
        for p in effect_owner.game.players:
            for pile in [p.hand, p.played_pile]:
                pile_cards = []
                for c in pile:
                    p.deck.append(c)
                    pile_cards.append(c)
                for c in pile_cards:
                    pile.remove(c)
            random.shuffle(p.deck)
            p.draw(3)
        return [f"{effect_owner.username} casts {self.name}."]
 
    def upgrade(self, previous_card, upgrader_card=None):
        upgrade_cards = []
        for c in Card.all_card_objects():
            if not c.is_token and c.cost > previous_card.cost and c.cost < previous_card.cost + 2 and c.card_type == self.card_type:
                upgrade_cards.append(c)
        if len(upgrade_cards) > 0:
            upgraded_card = random.choice(upgrade_cards)
            self.name = upgraded_card.name
            self.image = upgraded_card.image
            self.description = upgraded_card.description
            self.effects = upgraded_card.effects
            if upgrader_card:
                self.effects.append(upgrader_card.effects[0])
            self.strength = upgraded_card.strength
            self.hit_points = upgraded_card.hit_points

    def do_fetch_card_effect_on_player(self, effect_owner, effect, target_info):
        if Constants.artifactCardType in effect.target_type:
            self.display_deck_artifacts(effect_owner, "fetch_artifact_into_hand")
        elif effect.target_type == "all_cards_in_deck":
            self.display_deck_for_fetch(effect_owner)
        elif effect.target_type == "all_cards_in_played_pile":
            self.display_played_pile_for_fetch(effect_owner, self.id)
        else:
            print("can't fetch unsupported type")
            return None

        return [f"{effect_owner.username} fetches a card with {self.name}."]

    def do_fetch_card_into_play_effect_on_player(self, effect_owner, effect, target_info):
        if Constants.artifactCardType in effect.target_type:
            self.display_deck_artifacts(effect_owner, "fetch_artifact_into_play")
        else:
            print("can't fetch unsupported type")
            return None
        return [f"{effect_owner.username} cracks {self.name} to fetch an artifact."]

    def display_deck_artifacts(self, target_player, choice_type):
        artifacts = []
        for card in target_player.deck:
            if card.card_type == Constants.artifactCardType:
                artifacts.append(card)
        if len(artifacts) > 0:
            target_player.card_choice_info = {"cards": artifacts, "choice_type": choice_type}
        else:
            target_player.reset_card_choice_info()

    def display_deck_for_fetch(self, target_player):
        if len(target_player.deck) > 0:
            target_player.card_choice_info = {"cards": target_player.deck, "choice_type": "fetch_into_hand", "effect_card_id": None}
        else:
            return None

    def display_played_pile_for_fetch(self, target_player, card_id):
        if len(target_player.played_pile) > 0:
            target_player.card_choice_info = {"cards": target_player.played_pile, "choice_type": "fetch_into_hand_from_played_pile", "effect_card_id": card_id}
        else:
            return None

    def do_guard_effect(self, effect_owner, effect, target_info):
        guard_mobs = []
        for mob in effect_owner.in_play:
            for e in mob.effects:
                if e.id == "guard" and mob.can_be_clicked:
                    guard_mobs.append(mob)
        if len(guard_mobs) > 0:
            for mob in effect_owner.in_play:
                mob.can_be_clicked = mob in guard_mobs
            effect_owner.can_be_clicked = False

    def do_gain_for_hit_points_effect(self, effect_owner, effect, target_info):
        target_mob, controller = effect_owner.game.get_in_play_for_id(target_info['id'])
        if target_mob:
            old_hp = controller.hit_points
            controller.hit_points += target_mob.hit_points_with_tokens()
            controller.hit_points = min(controller.max_hit_points, controller.hit_points)
            if controller.hit_points > old_hp:
                return [f"{controller.username} gained {controller.hit_points - old_hp} from {self.name}."]

    def do_lose_lurker_effect(self, effect_owner, effect, target_info):
        for effect in self.effects:
            if effect.id == "make_untargettable":
                effect.enabled = False

    def do_heal_effect(self, effect_owner, effect, target_info):
        if effect.target_type == "self":
            return self.do_heal_effect_on_player(effect_owner, effect)
        elif target_info["target_type"] == "player":
            target_player = Card.player_for_username(effect_owner.game, target_info["id"])
            return self.do_heal_effect_on_player(target_player, effect)
        else:
            target_mob, _ = effect_owner.game.get_in_play_for_id(target_info["id"])
            return self.do_heal_effect_on_mob(target_mob, amount)

    def do_heal_effect_on_player(self, target_player, effect):
        """
                            gained = 0
                    to_apply = max(len(player.hand) - 5, 0)
                    while player.hit_points < player.max_hit_points and to_apply > 0:
                        player.hit_points += 1
                        to_apply -= 1
                        gained += 1  
        """
        amount = effect.amount
        if effect.amount_id == "hand_less_amount":
            amount = max(len(target_player.hand) - effect.amount, 0)
        if amount > 0:
            old_hp = target_player.hit_points
            target_player.hit_points += amount
            target_player.hit_points = min(target_player.hit_points, target_player.max_hit_points)
            if target_player.hit_points > old_hp:
                return [f"{self.name} healed {target_player.username} for {target_player.hit_points - old_hp}."]

    def do_heal_effect_on_mob(self, target_mob, amount):
        target_mob.damage -= amount
        target_mob.damage = max(target_mob.damage, 0)
        target_mob.damage_this_turn -= amount
        target_mob.damage_this_turn = max(target_mob.damage_this_turn, 0)
        return [f"{self.name} healed {target_mob.name} for {amount}."]

    def do_hp_damage_random_effect(self, effect_owner, effect, target_info):
        choice = random.choice(["hp", "damage"])
        if choice == "hp":
            return self.do_heal_effect_on_player(effect_owner, CardEffect({"amount": 1}, self.id))
        elif choice == "damage":
            targets = [effect_owner.my_opponent()]
            for m in effect_owner.my_opponent().in_play:
                targets.append(m)
            choice = random.choice(targets)
            if choice == targets[0]:
                self.do_damage_effect_on_player(effect, targets[0], choice, 1)
            else:
                self.do_damage_effect_on_mob(effect, choice, effect_owner.my_opponent(), 1)

    def do_improve_damage_when_used_effect(self, effect_owner, effect, target_info):
        # Rolling Thunder
        self.effects[0].amount += 1
        self.show_level_up = True
        return [f"{self.name} gets improved to deal {self.effects[0].amount} damage."]

    def do_improve_damage_all_effects_when_used_effect(self, effect_owner, effect, target_info):
        # Doomer
        for e in self.effects:
            if e.id == "damage":
                effect.amount += 1
        self.show_level_up = True
        return [f"{self.name} gets improved to deal {self.effects[0].amount} damage."]

    def do_improve_effect_amount_when_cast_effect(self, effect_owner, effect, target_info):
        # Tech Crashhouse
        self.effects[0].amount += 1
        self.show_level_up = True
        return [f"{self.name} gets improved to {self.effects[0].amount} Townies made."]

    def do_improve_effect_when_cast_effect(self, effect_owner, effect, target_info):
        # Tame Shop Demon
        old_level = self.level
        self.level += 1
        self.level = min(self.level, len(self.effects[0].card_names)-1)
        if self.level > old_level:
            self.show_level_up = True
        return [f"{self.name} levels up."]

    def do_keep_effect(self, effect_owner, effect, target_info):
        log_lines = [f"{effect_owner.username} kept a card."]
        if effect.amount and not effect.amount_id:
            old_strength = self.strength 
            self.strength += effect.amount
            old_hit_points = self.hit_points 
            self.hit_points += effect.amount
            if self.strength > old_strength or self.hit_points > old_hit_points:
                self.show_level_up = True
        if effect.amount_id == "upgrade":
             upgraded_card = effect_owner.add_to_deck(effect.card_names[0], 1, add_to_hand=True)
             effect_owner.hand.remove(upgraded_card)
             upgraded_card.id = self.id
             upgraded_card.show_level_up = True
             effect_owner.hand.append(upgraded_card)
        else:
            effect_owner.hand.append(self)
        card_to_remove = None
        for c in effect_owner.played_pile:
            if c.id == self.id:
                card_to_remove = c
        effect_owner.played_pile.remove(c)
        return log_lines

    def do_kill_effect(self, effect_owner, effect, target_info):
        if effect.target_type == "mob" or effect.target_type == "artifact" or effect.target_type == "mob_or_artifact":
            target_mob, controller = effect_owner.game.get_in_play_for_id(target_info['id'])
            log_lines = [f"{self.name} kills {target_mob.name}."]
            self.do_kill_effect_on_mob(target_mob, controller)
            return log_lines
        else:
            cards_to_kill = []
            min_cost = -1
            max_cost = 9999
            if "min_cost" in effect.other_info:
                min_cost = effect.other_info["min_cost"]
            if "max_cost" in effect.other_info:
                max_cost = effect.other_info["max_cost"]
            for player in [effect_owner, effect_owner.game.opponent()]:
                for card in player.in_play+player.artifacts:
                    if card.cost >= min_cost and card.cost <= max_cost:
                        cards_to_kill.append((card, player))
            for card_tuple in cards_to_kill: 
                self.do_kill_effect_on_mob(card_tuple[0], card_tuple[1])
            if len(cards_to_kill) > 0:
                return [f"{effect_owner.username} kills stuff ({len(cards_to_kill)})."]

    def do_kill_effect_on_mob(self, target_mob, controller):
        controller.send_card_to_played_pile(target_mob, did_kill=True)

    def do_mob_to_artifact_effect(self, effect_owner, effect, target_info):
        target_mob, controller = effect_owner.game.get_in_play_for_id(target_info['id'])
        if not target_mob:
            return
        controller.send_card_to_played_pile(target_mob, did_kill=False)
        controller.played_pile.pop()
        if len(controller.artifacts) < 3:
            target_mob.card_type = "artifact"
            controller.artifacts.append(target_mob)
        effect_owner.game.players[0].update_for_mob_changes_zones()
        effect_owner.game.players[1].update_for_mob_changes_zones()
        return [f"{effect_owner.username} turns {target_mob.name} into an artifact."]

    def do_make_effect(self, effect_owner, effect, target_info):
        return self.make(1, effect.make_type, effect_owner)

    def do_make_cheap_with_option_effect(self, effect_owner, effect, target_info):
        return self.make(1, effect.make_type, effect_owner, reduce_cost=1, option=True)

    def do_make_from_deck_effect(self, effect_owner, effect, target_info):
        return self.make_from_deck(effect_owner)

    def make(self, amount, make_type, player, reduce_cost=0, option=False):
        '''
            Make a spell or mob.
        '''
        requiredMobCost = None
        if player.game.turn <= 10 and make_type == Constants.mobCardType:
            requiredMobCost = math.floor(player.game.turn / 2) + 1

        all_game_cards = Card.all_card_objects(require_images=True, include_tokens=False)
        banned_cards = ["Make Spell", "Make Spell+", "Make Mob", "Make Mob+"]
        card1 = None 
        while not card1 or card1.name in banned_cards or (make_type != "any" and card1.card_type != make_type) or (requiredMobCost and make_type == Constants.mobCardType and card1.cost != requiredMobCost): 
            card1 = random.choice(all_game_cards)
        card2 = None
        while not card2 or card2.name in banned_cards or (make_type != "any" and card2.card_type != make_type) or card2 == card1:
            card2 = random.choice(all_game_cards)
        card3 = None
        while not card3 or card3.name in banned_cards or (make_type != "any" and card3.card_type != make_type) or card3 in [card1, card2]:
            card3 = random.choice(all_game_cards)
        player.card_choice_info = {"cards": [card1, card2, card3], "choice_type": "make"}
        
        if option:
            player.card_choice_info["choice_type"] = "make_with_option"

        player.card_choice_info["effect_card_id"] = self.id
       
        # todo: hax for Find Artifact
        if make_type == Constants.artifactCardType:
            for c in player.card_choice_info["cards"]:
                c.cost = min(3, c.cost)
        
        for c in player.card_choice_info["cards"]:
            c.cost = max(0, c.cost-reduce_cost)

        return [f"{self.name} made a card."]
    
    def make_from_deck(self, player):
        '''
            Make a spell or mob from the player's deck.
        '''
        card1 = None 
        if len(player.deck) > 0:
            while not card1:
                card1 = random.choice(player.deck)
        card2 = None
        if len(player.deck) > 1:
            while not card2 or card2 == card1:
                card2 = random.choice(player.deck)
        card3 = None
        if len(player.deck) > 2:
            while not card3 or card3 in [card1, card2]:
                card3 = random.choice(player.deck)
        
        if card3:
            player.card_choice_info = {"cards": [card1, card2, card3], "choice_type": "make_from_deck"}
        elif card2:
            player.card_choice_info = {"cards": [card1, card2], "choice_type": "make_from_deck"}
        else:
            player.card_choice_info = {"cards": [card1], "choice_type": "make_from_deck"}

        return [f"{player.username} made a card from their deck with {self.name}."]

    def do_mana_effect_on_player(self, effect_owner, effect, target_info):
        target_player = Card.player_for_username(effect_owner.game, target_info["id"])
        target_player.mana += effect.amount
        return [f"{target_player.username} gets {effect.amount} mana."]

    def do_make_token_effect(self, effect_owner, effect, target_info):
        if "did_kill" in target_info and not target_info["did_kill"]:
            return
        player = Card.player_for_username(effect_owner.game, target_info["id"])
        for x in range(0, effect.amount):
            if len(player.in_play) == 7:
                return
            card_to_create = None
            card_name = effect.card_names[0]
            if self.level != None:
                card_name = effect.card_names[self.level]
            for card in Card.all_card_objects():
                if card.name == card_name:
                    card_to_create = card
            new_card = copy.deepcopy(card_to_create)
            player.in_play.append(new_card)
            player.update_for_mob_changes_zones()
            new_card.id = player.game.next_card_id
            new_card.turn_played = player.game.turn
            new_card.owner_username = player.username
            player.game.next_card_id += 1
        
        if effect.target_type == "self":
            return [f"{self.name} makes {effect.amount} tokens."]
        else:
            return [f"{self.name} makes {effect.amount} tokens for {player.username}."]

    def do_make_untargettable_effect(self, effect_owner, effect, target_info):
        if effect.enabled:
            if effect_owner.card_info_to_target["card_id"] != None or effect_owner.username != effect_owner.game.current_player().username:
                self.can_be_clicked = False
            if effect_owner.my_opponent().selected_mob():
                effect_owner.game.set_attack_clicks(omit_mobs=[self])

        for card in effect_owner.game.current_player().hand:
            if card.card_type == Constants.spellCardType and card.can_be_clicked == True and card.needs_mob_target():
                card.can_be_clicked = False
                for mob in effect_owner.in_play + effect_owner.my_opponent().in_play:
                    if mob.can_be_clicked:
                        card.can_be_clicked = True
                        break
    
    def do_mana_increase_max_effect_on_player(self, effect_owner, effect, target_info):
        target_player = Card.player_for_username(effect_owner.game, target_info["id"])
        old_max_mana = target_player.max_mana
        target_player.max_mana += 1
        target_player.max_mana = min(target_player.max_max_mana(), target_player.max_mana)
        # in case something like Mana Shrub doesn't increase the mana
        if old_max_mana == target_player.max_mana:
            if len(self.effects) == 2 and self.effects[1].id == "decrease_max_mana":
                self.effects[1].enabled = False
        return [f"{target_player.username} increases their max mana by {effect.amount}."]

    def do_mana_set_max_effect(self, effect_owner, effect, target_info):
        for p in effect_owner.game.players:
            p.max_mana = effect.amount
            p.max_mana = min(p.max_max_mana(), p.max_mana)
            p.mana = min(p.mana, p.max_mana)
        return [f"{self.name} sets max mana to {effect.amount}."]

    def do_mana_reduce_effect_on_player(self, effect_owner, effect, target_info):
        target_player = Card.player_for_username(effect_owner.game, target_info["id"])
        target_player.max_mana -= max(effect.amount, 0)
        target_player.mana = min(target_player.mana, target_player.max_mana)
        return [f"{target_player.username} decreases max mana by {effect.amount}."]

    def do_preserve_effect_improvement_effect(self, effect_owner, effect, target_info):
        new_card = Card.factory_reset_card(self, effect_owner)
        old_effect_amount = self.effects[0].amount 
        old_level = self.level
        for a in dir(self):
            if not a.startswith('__') and not callable(getattr(self, a)):
                setattr(self, a, getattr(new_card, a))
        self.effects[0].amount = old_effect_amount
        # hax - does this more belong in factory_reset_card?
        self.level = old_level

    def do_preserve_stats_effect(self, effect_owner, effect, target_info):
        new_card = Card.factory_reset_card(self, effect_owner)
        old_strength = self.strength
        old_hit_points = self.hit_points
        old_level = self.level
        for a in dir(self):
            if not a.startswith('__') and not callable(getattr(self, a)):
                setattr(self, a, getattr(new_card, a))
        self.strength = old_strength
        self.hit_points = old_hit_points
        self.level = old_level

    def do_pump_strength_effect_on_mob(self, effect_owner, effect, target_info):
        target_mob, _ = effect_owner.game.get_in_play_for_id(target_info['id'])
        target_mob.strength += effect.amount
        return [f"{effect_owner.username} pumps the strength of {target_mob.name} by {effect.amount}."]

    def do_redirect_mob_spell_effect(self, effect_owner, effect, target_info):
        card_id = target_info["id"]
        if len(effect_owner.in_play) >= 7:
            # can't summon the 2/3 to redirect the spell to
            return None

        stack_spell = None
        for spell in effect_owner.game.stack:
            if spell[1]["id"] == card_id:
                stack_spell = spell
                break

        villager_card = Card({})
        villager_card.id = effect_owner.game.next_card_id

        token_card_name = "Willing Villager"
        villager_card.do_make_token_effect(effect_owner, CardEffect({"amount":1, "card_names": [token_card_name]}, 0), {"id": effect_owner.username})
        effect_owner.game.next_card_id += 1

        # the card was countered by a different counterspell
        if not stack_spell:
            return None

        stack_spell[0]["effect_targets"][0]["id"] = villager_card.id
        return[f"{stack_spell[1]['name']} was redirected to a newly summoned {villager_card.name}."]


    def do_restrict_effect_targets_min_cost_effect(self, effect_owner, effect, target_info):
        if self == effect_owner.selected_spell():
            for player in effect_owner.game.players:
                for pile in [player.in_play, player.artifacts]:
                    for card in pile:
                        if card.can_be_clicked and card.cost < effect.amount:
                            card.can_be_clicked = False
        elif target_info["move_type"] != "SELECT_CARD_IN_HAND" and effect_owner.current_mana() >= self.cost:
            # clone the game so we can do a move in the cloned game to select the card with target restrictions
            # then, check if there are any targets in the cloned game (e.g. card.can_be_clicked == True)
            game_copy = copy.deepcopy(effect_owner.game)
            game_copy.play_move({"username": effect_owner.username, "move_type": "SELECT_CARD_IN_HAND", "card": self.id, "override_selection_for_lookahead": True})        
            has_targets = False
            for player in game_copy.players:
                for pile in [player.in_play, player.artifacts]:
                    for card in pile:
                        if card.can_be_clicked:
                            has_targets = True
            self.can_be_clicked = has_targets

    def do_restrict_effect_targets_mob_targetter_effect(self, effect_owner, effect, target_info):
        if self == effect_owner.selected_spell():
            for spell in effect_owner.game.stack:
                card = Card(spell[1])
                if card.card_type == Constants.spellCardType:
                    action = spell[0]
                    if "effect_targets" in action and action["effect_targets"][0]["target_type"] == Constants.mobCardType:
                        card.can_be_clicked = True
        elif target_info["move_type"] != "SELECT_CARD_IN_HAND" and effect_owner.current_mana() >= self.cost:
            game_copy = copy.deepcopy(effect_owner.game)
            game_copy.play_move({"username": effect_owner.username, "move_type": "SELECT_CARD_IN_HAND", "card": self.id, "override_selection_for_lookahead": True})        
            has_targets = False
            for spell in game_copy.stack:
                card = spell[1]
                if card["card_type"] == Constants.spellCardType:
                    action = spell[0]
                    if "effect_targets" in action and action["effect_targets"][0]["target_type"] == Constants.mobCardType:
                        has_targets = True
            self.can_be_clicked = has_targets

    def do_restrict_effect_targets_mob_with_guard_effect(self, effect_owner, effect, target_info):
        if self.id == effect_owner.selected_mob():
            for player in effect_owner.game.players:
                for card in player.in_play:
                    if card.can_be_clicked and not card.has_effect("guard"):
                        card.can_be_clicked = False
        elif target_info["move_type"] not in ["PLAY_CARD", "PLAY_CARD_IN_HAND"] and effect_owner.current_mana() >= self.cost:
            game_copy = copy.deepcopy(effect_owner.game)
            game_copy.play_move({"username": effect_owner.username, "move_type": "PLAY_CARD_IN_HAND", "card": self.id, "override_selection_for_lookahead": True})        
            has_targets = False
            for player in game_copy.players:
                for card in player.in_play:
                    if card.can_be_clicked and card.has_effect("guard"):
                        has_targets = True
            self.can_be_clicked = has_targets

    def do_restrict_effect_targets_mob_with_strength_effect(self, effect_owner, effect, target_info):
        if self.id == effect_owner.selected_mob():
            for player in effect_owner.game.players:
                for card in player.in_play:
                    if card.can_be_clicked and card.strength_with_tokens(player) < effect.amount:
                        card.can_be_clicked = False
        elif target_info["move_type"] not in ["PLAY_CARD", "PLAY_CARD_IN_HAND"] and effect_owner.current_mana() >= self.cost:
            game_copy = copy.deepcopy(effect_owner.game)
            game_copy.play_move({"username": effect_owner.username, "move_type": "PLAY_CARD_IN_HAND", "card": self.id, "override_selection_for_lookahead": True})        
            has_targets = False
            for player in game_copy.players:
                for card in player.in_play:
                    if card.can_be_clicked and card.strength_with_tokens(player) >= effect.amount:
                        has_targets = True
            self.can_be_clicked = has_targets

    def do_remove_tokens_effect(self, effect_owner, effect, target_info):
        if effect.target_type == "self_mobs":
            for mob in effect_owner.in_play:
                tokens_to_keep = []
                for token in mob.tokens:
                    if token.id != self.id:
                        tokens_to_keep.append(token)
                mob.tokens = tokens_to_keep

    def do_reduce_cost_effect(self, effect_owner, effect, target_info):
        if not effect.target_type or self.card_type == effect.target_type:
            self.cost -= 1
            self.cost = max(0, self.cost)

    def do_reduce_draw_effect(self, effect_owner, effect, target_info):
        effect_owner.about_to_draw_count -= effect.amount

    def do_refresh_mana_effect(self, effect_owner, effect, target_info):
        if effect_owner.mana == 0 and target_info["amount_spent"] > 0:
            effect_owner.mana = effect_owner.max_mana

    def do_use_stored_mana_effect(self, effect_owner, effect, target_info):
        amount_to_spend = target_info["amount_to_spend"]
        store_effect = None
        log_lines = None
        if amount_to_spend > 0:
            log_lines = [f"{self.name} used {amount_to_spend} mana."]            
        for e in self.effects:
            if e.id == "store_mana":
                store_effect = e
        while amount_to_spend > 0 and store_effect.counters > 0:                        
            store_effect.counters -= 1
            amount_to_spend -= 1
        return log_lines

    
    def do_riffle_effect(self, effect_owner, effect, target_info):
        player = effect_owner
        top_cards = []
        for card in player.deck:
            if len(top_cards) < effect.amount:
                top_cards.append(card)
        player.card_choice_info = {"cards": top_cards, "choice_type": "riffle"}
        return [f"{player.username} riffled for {effect.amount} and chose a card."]

    def do_set_can_attack_effect(self, effect_owner, effect, target_info):
        if effect.target_type == "self_mobs":
            player = effect_owner
            for e in player.in_play:
                e.can_attack_mobs = True
                e.can_attack_players = True
                e.attacked = False
            return [f"{player.username} let their mobs attack again this turn."]          
        else:
            print(f"e.target_type {target_type} not supported for set_can_attack")

    def do_slow_artifact_effect(self, effect_owner, effect, target_info):
        for effect in self.effects:
            effect.exhausted = True

    def do_spell_from_yard_effect(self, effect_owner, effect, target_info):
        spells = []
        for card in effect_owner.played_pile:
            if card.card_type == Constants.spellCardType:
                spells.append(card)
        if len(spells) == 0:
            return
        else:
            if len(effect_owner.hand) < effect_owner.game.max_hand_size:
                spell = random.choice(spells)
                effect_owner.hand.append(spell)
                effect_owner.played_pile.remove(spell)
                return [f"{self.name} returns {spell.name} to {effect_owner.username}'s hand."]

    def do_start_in_hand_effect(self, effect_owner, effect, target_info):
        effect_owner.hand.append(self)
        effect_owner.deck.remove(self)   

    def do_start_in_play_effect(self, effect_owner, effect, target_info):
        if len(effect_owner.artifacts) == 0:
            effect_owner.artifacts.append(self)
            effect_owner.deck.remove(self)   
            self.turn_played = 0

    def do_store_card_for_next_turn_effect(self, effect_owner, effect, target_info):
        for c in effect_owner.hand:
            if "id" in target_info and c.id == target_info["id"]:
                self.card_for_effect = c
                effect_owner.hand.remove(c)
                break

    def do_store_mana_effect(self, effect_owner, effect, target_info):
        counters = max(effect.counters, 0)
        new_counters = min(3 - counters, effect_owner.mana)
        log_lines =  None
        if new_counters > 0:
            log_lines = [f"{self.name} stores {new_counters} mana."]   
            if  effect.counters == -1:
                effect.counters = 0
            effect.counters += new_counters
            effect.counters = min(effect.counters, 3)
        return log_lines

    def do_summon_from_deck_effect_on_player(self, effect_owner, effect, target_info):
        if effect.target_type == "self" and effect.amount == 1:
            mobs = []
            target_player = effect_owner
            for c in target_player.deck:
                if c.card_type == Constants.mobCardType:
                    mobs.append(c)

            if len(mobs) > 0:
                mob_to_summon = random.choice(mobs)
                target_player.deck.remove(mob_to_summon)
                target_player.in_play.append(mob_to_summon)
                target_player.update_for_mob_changes_zones()
                mob_to_summon.turn_played = target_player.game.turn   
        elif effect.target_type == "all_players" and effect.amount == -1:
            mobs = []
            for c in Card.all_card_objects():
                if c.card_type == Constants.mobCardType:
                    mobs.append(c)
            for p in effect_owner.game.players:
                while len(p.in_play) < 7:
                    mob_to_summon = copy.deepcopy(random.choice(mobs))
                    mob_to_summon.id = self.game.next_card_id
                    effect_owner.game.next_card_id += 1
                    p.in_play.append(mob_to_summon)
                    p.update_for_mob_changes_zones()
                    mob_to_summon.turn_played = effect_owner.game.turn     
        if effect.target_type == "self":
            return [f"{effect_owner.username} summons something from their deck."]
        else:
            return [f"Both players fill their boards."]

    def do_summon_from_deck_artifact_effect_on_player(self, effect_owner, effect, target_info):
        target_player = effect_owner
        if effect.target_type == "self" and effect.amount == 1:
            artifacts = []
            for c in target_player.deck:
                if c.card_type == Constants.artifactCardType:
                    artifacts.append(c)

            if len(artifacts) > 0:
                target_player = effect_owner
                artifact_to_summon = random.choice(artifacts)
                target_player.deck.remove(artifact_to_summon)
                target_player.play_artifact(artifact_to_summon)
                target_player.update_for_mob_changes_zones()
                # todo: maybe support comes into play effects for artifacts?

            return [f"{effect_owner.username} summons something from their deck."]
        
        print(f"unsupported target_type {effect.target_type} for summon_from_deck_artifact effect for {self.name}")

    def do_summon_from_hand_effect(self, effect_owner, effect, target_info):
        target_player = Card.player_for_username(effect_owner.game, target_info["id"])
        nonspells = []
        for card in target_player.hand:
            if card.card_type != Constants.spellCardType:
                nonspells.append(card)
        if len(nonspells) > 0:
            to_summon = random.choice(nonspells)
            target_player.hand.remove(to_summon)
            message = effect_owner.play_mob_or_artifact(to_summon, {"log_lines":[]}, do_effects=False)
            message["log_lines"].append(f"{to_summon.name} was summoned for {effect_owner.username}.")
            return message["log_lines"]

    def do_switch_hit_points_effect(self, effect_owner, effect, target_info):
        # effect_owner
        cp_hp = effect_owner.hit_points
        effect_owner.hit_points = effect_owner.game.opponent().hit_points
        effect_owner.game.opponent().hit_points = cp_hp
        return [f"{effect_owner.username} uses {self.name} to switch hit points with {effect_owner.game.opponent().username}."]

    def do_shield_effect(self, effect_owner, effect, target_info):
        if not effect.enabled:
            return
        effect.enabled = False
        damage = target_info["damage"]
        self.deal_damage(-damage)

    def do_add_symbiotic_fast_effect(self, effect_owner, effect, target_info):
        anything_friendly_has_fast = False
        for e in effect_owner.in_play:
            if e.has_effect("add_fast"):
                anything_friendly_has_fast = True

        if anything_friendly_has_fast:
            self.do_add_mob_effects_effect(
                effect_owner, 
                CardEffect(
                    {
                        "effects": [self.add_fast_effect_info()]
                    }, 
                    self.id
                ), 
                {"id": self.id}
            )
            self.can_attack_mobs = True
            self.can_attack_players = True

    def add_fast_effect_info(self):
        return {
            "id": "add_fast",
            "name": "Add Fast",
            "description": "Fast",
            "description_expanded": "Fast mobs may attack the turn they come into play.",
            "effect_type": "enter_play"
        }        

    # todo fix that this doesn't check for an ID or something?
    def do_remove_symbiotic_fast_effect(self, effect_owner, effect, target_info):
        effects_to_remove = []
        for effect in self.effects:
            if effect.id == "add_fast":
                effects_to_remove.append(effect)
                if not self.has_effect("ambush"):
                    self.can_attack_mobs = False
                self.can_attack_players = False
                break 
        for effect in effects_to_remove:
            self.effects.remove(effect)

    def do_set_token_effect(self, effect_owner, effect, target_info):
        tokens_to_remove = []
        for t in self.tokens:
            if t.id == self.id:
                tokens_to_remove.append(t)
        for t in tokens_to_remove:
            self.tokens.remove(t)
        
        if self.card_type == "mob": # code for Spirit of the Stampede and Vamp Leader
            self.do_add_token_effect_on_mob(effect, effect_owner, self, effect_owner)
        elif effect.target_type == "self_mobs": # Arsenal
            for e in effect_owner.my_opponent().in_play:
                for token in e.tokens:
                    if token.id == self.id:
                        e.tokens.remove(token)
                        break

            for e in effect_owner.in_play:
                for token in e.tokens:
                    if token.id == self.id:
                        e.tokens.remove(token)
                        break
            for mob in effect_owner.in_play:
                mob.do_add_token_effect_on_mob(effect, effect_owner, mob, effect_owner)

    def do_take_control_effect(self, effect_owner, effect, target_info):
        # e, effect_owner, target_mob
        opponent = effect_owner.game.opponent()
        if effect.target_type == "all":
            while len(opponent.in_play) > 0 and len(effect_owner.in_play) < 7:
                self.do_take_control_effect_on_mob(effect_owner, opponent.in_play[0], opponent)
            while len(opponent.artifacts) > 0 and len(effect_owner.artifacts) < 3:
                self.do_take_control_effect_on_artifact(effect_owner, opponent.artifacts[0], opponent)
            log_lines = [f"{effect_owner.username} takes control everything."]
        elif effect.target_type == "enemy_mob_random": # song dragon
            if len(opponent.in_play) > 0:
                mob_to_target = random.choice(opponent.in_play)
                self.do_take_control_effect_on_mob(effect_owner, mob_to_target, opponent)
                log_lines = [f"{effect_owner.username} takes control of {mob_to_target.name}."]
        else:
            target_mob, controller = effect_owner.game.get_in_play_for_id(target_info["id"])
            log_lines = [f"{effect_owner.username} takes control of {target_mob.name}."]
            self.do_take_control_effect_on_mob(effect_owner, target_mob, controller)
        return log_lines

    def do_take_control_effect_on_mob(self, effect_owner, target_mob, controller):
        target_mob.turn_played = effect_owner.game.turn
        target_mob.attacked = False
        target_mob.can_attack_mobs = False
        target_mob.can_attack_players = False
        controller.in_play.remove(target_mob)
        effect_owner.in_play.append(target_mob)
        effect_owner.game.players[0].update_for_mob_changes_zones()
        effect_owner.game.players[1].update_for_mob_changes_zones()
        target_mob.do_leaves_play_effects(controller, did_kill=False)

        def_index = 0
        for e in target_mob.effects:
            if e.effect_type == "enter_play" and e.target_type == None:
                self.resolve_effect(target_mob.enter_play_effect_defs[def_index], effect_owner, e, {}) 
                def_index += 1

    def do_take_control_effect_on_artifact(self, effect_owner, target_artifact, controller):
        controller.artifacts.remove(target_artifact)
        effect_owner.artifacts.append(target_artifact)
        effect_owner.game.players[0].update_for_mob_changes_zones()
        effect_owner.game.players[1].update_for_mob_changes_zones()
        target_artifact.turn_played = effect_owner.game.turn
        target_artifact.do_leaves_play_effects(controller, did_kill=False)
    
    def do_take_extra_turn_effect_on_player(self, effect_owner, effect, target_info):
        target_player = Card.player_for_username(effect_owner.game, target_info["id"])
        target_player.remove_temporary_tokens()
        target_player.clear_damage_this_turn()
        target_player.game.turn += 2
        log_lines = [f"{target_player.username} takes an extra turn."]
        message = target_player.start_turn({"log_lines":[], "move_type": "START_TURN"})
        log_lines += message["log_lines"]
        return log_lines

    def do_unwind_effect(self, effect_owner, effect, target_info):
        if effect.target_type == "all_mobs":
            mobs_to_unwind = []
            for mob in effect_owner.in_play:
                if mob.id != self.id:
                    mobs_to_unwind.append((mob, effect_owner))
            for mob in effect_owner.game.opponent().in_play:
                if mob.id != self.id:
                    mobs_to_unwind.append((mob, effect_owner.game.opponent()))
            for mob_tuple in mobs_to_unwind:
                self.do_unwind_effect_on_mob(mob_tuple[0], mob_tuple[1])
            return [f"{self.name} returns all mobs to their owners' hands."]
        else:
            target_mob, controller = effect_owner.game.get_in_play_for_id(target_info["id"])
            self.do_unwind_effect_on_mob(target_mob, controller)
            return [f"{self.name} returns {target_mob.name} to {target_mob.owner_username}'s hand."]

    def do_unwind_effect_on_mob(self, target_mob, controller):
        controller.in_play.remove(target_mob)  
        target_mob.do_leaves_play_effects(controller, did_kill=False)
        controller.game.remove_attack_for_mob(target_mob)
        new_card = Card.factory_reset_card(target_mob, controller)
        player = controller.game.players[0]
        if target_mob.owner_username != player.username:
            player = controller.game.players[1]
        player.hand.append(new_card)  

    def enabled_activated_effects(self):
        enabled_effects = []
        for e in self.effects_for_type("activated"):
            if e.enabled:
               enabled_effects.append(e)
        return enabled_effects

    def needs_targets_for_spell(self):
        if len(self.effects_for_type("spell")) == 0:
            return False
        e = self.effects[0]
        if e.target_type in [
            "any", 
            "any_enemy", 
            "any_player", 
            "artifact", 
            "being_cast", 
            "being_cast_artifact", 
            "being_cast_spell", 
            "being_cast_mob", 
            "mob", 
            "mob_or_artifact",
            "opponents_mob", 
            "self_mob", 
        ]:
            return True
        return False 

    def needs_mob_or_artifact_target(self):
        if len(self.effects) == 0:
            return False
        e = self.effects[0]
        if e.target_type  in ["mob_or_artifact"]:
            return True
        return False

    def needs_mob_target(self):
        if len(self.effects) == 0:
            return False
        e = self.effects[0]
        if e.target_type  in ["mob", "opponents_mob", "self_mob"]:
            return True
        return False

    def can_target_mobs(self):
        if len(self.effects) == 0:
            return False
        e = self.effects[0]
        if e.target_type  in ["mob", "opponents_mob", "any_enemy", "any", "self_mob", "mob_or_artifact"]:
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
        for spell in game.stack:
            card = Card(spell[1])
            if spell[0]["move_type"] == "ATTACK":
                continue
            if e.target_type == "being_cast":
                return True
            if e.target_type == "being_cast_mob" and card.card_type == Constants.mobCardType:
                return True
            if e.target_type == "being_cast_spell" and card.card_type == Constants.spellCardType:
                return True
            if e.target_type == "being_cast_artifact" and card.card_type == Constants.artifactCardType:
                return True
        return False

    def needs_opponent_mob_target_for_spell(self):
        e = self.effects_for_type("spell")[0]
        if e.target_type in ["opponents_mob"]:
            return True
        return False

    def needs_opponent_mob_target_for_spell(self):
        e = self.effects_for_type("spell")[0]
        if e.target_type in ["opponents_mob"]:
            return True
        return False

    def needs_mob_target_for_activated_effect(self, index=0):
        e = self.enabled_activated_effects()[index]
        if e.target_type in ["mob", "opponents_mob", "self_mob"]:
            return True
        return False

    def needs_self_mob_target_for_activated_effect(self, index=0):
        e = self.enabled_activated_effects()[index]
        if e.target_type in ["self_mob"]:
            return True
        return False

    def needs_hand_target_for_activated_effect(self, index=0):
        e = self.enabled_activated_effects()[index]
        if e.target_type in ["hand_card"]:
            return True
        return False

    def needs_target_for_activated_effect(self, effect_index):
        e = self.enabled_activated_effects()[effect_index]
        if e.target_type in ["self", "opponent", "artifact_in_deck", "all"]: 
            return False
        return True

    def strength_with_tokens(self, player):
        strength = self.strength
        for t in self.tokens:
            if t.multiplier == "self_artifacts":
                strength += t.strength_modifier * len(player.artifacts)
            elif t.multiplier == "self_mobs_and_artifacts":
                strength += t.strength_modifier * (len(player.artifacts) + len(player.in_play))
            else:
                strength += t.strength_modifier
        return strength

    def hit_points_with_tokens(self):
        hit_points = self.hit_points
        for t in self.tokens:
            hit_points += t.hit_points_modifier
        return hit_points

    def has_effect(self, effect_id):
        for e in self.effects:
            if e.id == effect_id:
                return True
        return False

    def do_leaves_play_effects(self, player, did_kill=True):
        for idx, effect_def in enumerate(self.leave_play_effect_defs):
            target_info = {"id": player.username, "did_kill": did_kill}
            if self.effects_for_type("leave_play")[idx].target_type == "self":
                target_info = {"id": player.username, "target_type": "player", "did_kill": did_kill}
            elif self.effects_for_type("leave_play")[idx].target_type == "opponent":
                target_info = {"id": player.game.opponent().username, "target_type": "player", "did_kill": did_kill}
            self.resolve_effect(effect_def, player, self.effects_for_type("leave_play")[idx], target_info)

    def effects_for_type(self, effect_type):
        return [e for e in self.effects if e.effect_type == effect_type]

    def deal_damage_with_effects(self, amount, controller):
        for idx, effect in enumerate(self.effects_for_type("before_is_damaged")):
            self.resolve_effect(self.before_is_damaged_effect_defs[idx], controller, effect, {"damage": amount})         
        self.deal_damage(amount)

    def deal_damage(self, amount):
        self.damage += amount
        self.damage_to_show += amount
        self.damage_this_turn += amount


class CardEffect:
    def __init__(self, info, effect_id):
        self.id_for_game = effect_id
        # an integer to be used to size the effect
        self.amount = info["amount"] if "amount" in info else None
        # a string to be used to size the effect
        self.amount_id = info["amount_id"] if "amount_id" in info else None
        # the cost in mana of the effect
        self.cost = info["cost"] if "cost" in info else 0
        # a one word description to maybe show on the card, but definitely show on hover
        self.description = info["description"] if "description" in info else None
        # a sentence description to show on hover
        self.description_expanded = info["description_expanded"] if "description_expanded" in info else None
        # whether or not to show self.description as text on the card, or just on hover if False
        self.description_on_card = info["description_on_card"] if "description_on_card" in info else True
        # used to determine when the effect triggers, such as on draw or after target selection
        self.effect_type = info["effect_type"] if "effect_type" in info else None
        # whether or not the effect is enabled and will trigger or can be activated
        self.enabled = info["enabled"] if "enabled" in info else True
        # this is set after an effect is used, so it can't be used again this turn
        self.exhausted = info["exhausted"] if "exhausted" in info else False
        # the id of the effect, which gets mapped to a def
        self.id = info["id"] if "id" in info else None         
        # the name of the effect
        self.name = info["name"] if "name" in info else None         
        # the calculated strength of the effect
        self.power_points = info["power_points"] if "power_points" in info else 0         
        # a flag to set on the effect to trigger an animation on the next repaint
        self.show_effect_animation = info["show_effect_animation"] if "show_effect_animation" in info else False
        # the target type for the effect, such as mob, enemy, artifact, self, etc
        self.target_type = info["target_type"] if "target_type" in info else None
        # tokens that the effect adds
        self.tokens = [CardToken(t) for t in info["tokens"]] if "tokens" in info else []
        # info the UI needs to display or animate the effect
        self.ui_info = info["ui_info"] if "ui_info" in info else None

        # currently, only used for Resonant Frequency to set min_cost and max_cost for what gets killed
        self.other_info = info["other_info"] if "other_info" in info else {}

        # todo: move all of these below to other_info? only used sparsely
        # the type of target the AI should prefer to play
        self.ai_target_types = info["ai_target_types"] if "ai_target_types" in info else []
        # only used for Tame Shop Demon
        self.card_descriptions = info["card_descriptions"] if "card_descriptions" in info else []
        # used for make_token and upgrade effects
        self.card_names = info["card_names"] if "card_names" in info else []
        # this gets used in resolve_effect so maybe leave to level
        self.cost_hp = info["cost_hp"] if "cost_hp" in info else 0
        # used for Lute and Akbar's Pan Pipes
        self.counters = info["counters"] if "counters" in info else -1
        # a list of affects added by the effect, use for cards like Hide and WInd of Mercury
        self.effects = [CardEffect(e, idx) for idx, e in enumerate(info["effects"])] if "effects" in info else []
        # only used for Lute
        self.effect_to_activate = CardEffect(info["effect_to_activate"], info["effect_to_activate"]["id"] if "id" in info["effect_to_activate"] else 0) if "effect_to_activate" in info and info["effect_to_activate"] else None
        # seems a little specific to make cards
        self.make_type = info["make_type"] if "make_type" in info else None
        # todo: move to other_info?
        self.multiplier = info["multiplier"] if "multiplier" in info else None
        # used for Mirror of Fate, Wish Stone, and Disk of Death
        self.sacrifice_on_activate = info["sacrifice_on_activate"] if "sacrifice_on_activate" in info else False

    def __repr__(self):
        return f"{self.as_dict()}"

    def as_dict(self):
        return {
            "ai_target_types": self.ai_target_types,
            "amount": self.amount,
            "amount_id": self.amount_id,
            "card_descriptions": self.card_descriptions,
            "card_names": self.card_names,
            "counters": self.counters,
            "cost": self.cost,
            "cost_hp": self.cost_hp,
            "description": self.description,
            "description_expanded": self.description_expanded,
            "description_on_card": self.description_on_card,
            "effects": [e.as_dict() for e in self.effects] if self.effects else [],
            "effect_to_activate": self.effect_to_activate.as_dict() if self.effect_to_activate else None,
            "effect_type": self.effect_type,
            "enabled": self.enabled,
            "exhausted": self.exhausted,
            "id": self.id,
            "make_type": self.make_type,
            "multiplier": self.multiplier,
            "name": self.name,
            "id_for_game": self.id_for_game,
            "other_info": self.other_info,
            "power_points": self.power_points,
            "sacrifice_on_activate": self.sacrifice_on_activate,
            "show_effect_animation": self.show_effect_animation,
            "target_type": self.target_type,
            "tokens": [t.as_dict() for t in self.tokens] if self.tokens else [],
            "ui_info": self.ui_info,
        }


class CardToken:
    def __init__(self, info):
        self.strength_modifier = info["strength_modifier"] if "strength_modifier" in info else 0
        self.set_can_act = info["set_can_act"] if "set_can_act" in info else None
        self.hit_points_modifier = info["hit_points_modifier"] if "hit_points_modifier" in info else 0
        self.turns = info["turns"] if "turns" in info else -1
        self.multiplier = info["multiplier"] if "multiplier" in info else 0
        self.id = info["id"] if "id" in info else None

    def __repr__(self):
        if self.set_can_act is not None:
            return "Can't Attack"
        if self.id != None:
            return f"id: {self.id} - +{self.strength_modifier}/+{self.hit_points_modifier}"
        return f"+{self.strength_modifier}/+{self.hit_points_modifier}"

    def as_dict(self):
        return {
            "strength_modifier": self.strength_modifier,
            "set_can_act": self.set_can_act,
            "hit_points_modifier": self.hit_points_modifier,
            "turns": self.turns,
            "multiplier": self.multiplier,
            "id": self.id,
        }

def all_cards(require_images=False, include_tokens=True, include_old_cards=True):
    """
        Returns a list of all possible cards in the game. 
    """
    subset = []

    if include_old_cards:
        json_data = open('battle_wizard/game/battle_wizard_cards.json')
        all_cards = json.load(json_data)
        for c in all_cards:
            if include_tokens or ("is_token" not in c or c["is_token"] == False):
                if "image" in c or not require_images:
                    subset.append(Card(c).as_dict())

        json_data = open('battle_wizard/game/old_cards.json')
        all_cards = json.load(json_data)
        for c in all_cards:
            if include_tokens or ("is_token" not in c or c["is_token"] == False):
                if "image" in c or not require_images:
                    subset.append(Card(c).as_dict())

    json_data = open('create_cards/cards_and_effects.json')
    cards_and_effects = json.load(json_data)
    for c in cards_and_effects["cards"]:
        if include_tokens or ("is_token" not in c or c["is_token"] == False):
            if "image" in c or not require_images:
                c["discipline"] = "magic"
                subset.append(Card(c).as_dict())

    custom_cards = CustomCard.objects.all().exclude(card_json__name="Unnamed Card")
    for card in custom_cards:
        card.card_json["discipline"] = "magic"
        subset.append(Card(card.card_json).as_dict())

    return subset

