import copy
import math
import random

from battle_wizard.game.data import all_abilities
from battle_wizard.game.data import all_cards
from battle_wizard.game.data import Constants


class Card:
    
    def __init__(self, info):
        self.id = info["id"] if "id" in info else -1

        self.abilities = [CardAbility(a, idx) for idx, a in enumerate(info["abilities"])] if "abilities" in info and info["abilities"] else []
        self.added_descriptions = info["added_descriptions"] if "added_descriptions" in info else []
        self.attacked = info["attacked"] if "attacked" in info else False
        self.can_activate_abilities = info["can_activate_abilities"] if "can_activate_abilities" in info else True
        self.can_attack_mobs = info["can_attack_mobs"] if "can_attack_mobs" in info else False
        self.can_attack_players = info["can_attack_players"] if "can_attack_players" in info else False
        self.can_be_clicked = info["can_be_clicked"] if "can_be_clicked" in info else False
        self.card_for_effect = Card(info["card_for_effect"]) if "card_for_effect" in info and info["card_for_effect"] else None
        self.card_subtype = info["card_subtype"] if "card_subtype" in info else None
        self.card_type = info["card_type"] if "card_type" in info else Constants.mobCardType
        self.cost = info["cost"] if "cost" in info else 0
        self.damage = info["damage"] if "damage" in info else 0
        self.damage_this_turn = info["damage_this_turn"] if "damage_this_turn" in info else 0
        self.damage_to_show = info["damage_to_show"] if "damage_to_show" in info else 0
        self.discipline = info["discipline"] if "discipline" in info else None
        self.effects = [CardEffect(e, self.id) for _, e in enumerate(info["effects"])] if "effects" in info else []
        self.effects_can_be_clicked = info["effects_can_be_clicked"] if "effects_can_be_clicked" in info else []
        self.effects_exhausted = info["effects_exhausted"] if "effects_exhausted" in info else []
        self.description = info["description"] if "description" in info else None
        self.global_effect = info["global_effect"] if "global_effect" in info else None
        self.image = info["image"] if "image" in info else None
        self.is_token = info["is_token"] if "is_token" in info else False
        self.level = info["level"] if "level" in info else None
        self.name = info["name"] if "name" in info else None
        self.needs_targets = info["needs_targets"] if "needs_targets" in info else False
        self.original_description = info["original_description"] if "original_description" in info else None
        # probably bugs WRT Mind Manacles
        self.owner_username = info["owner_username"] if "owner_username" in info else None
        self.power = info["power"] if "power" in info else None
        self.show_level_up = info["show_level_up"] if "show_level_up" in info else False
        self.tokens = [CardToken(t) for t in info["tokens"]] if "tokens" in info else []
        self.toughness = info["toughness"] if "toughness" in info else None
        self.turn_played = info["turn_played"] if "turn_played" in info else -1

        # card.effects get mapped into these lists of defs defined on Card
        self.activated_effect_defs = []
        self.after_attack_effect_defs = []
        self.after_deals_damage_effect_defs = []
        self.before_is_damaged_effect_defs = []
        self.check_mana_effect_defs = []
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

        for effect in self.effects:
            self.create_effect_def(effect)

    def create_effect_def(self, effect):
        if effect.effect_type == "activated":
            self.activated_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "before_is_damaged":
            self.before_is_damaged_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "enter_play":
            self.enter_play_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "leave_play":
             self.leave_play_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "spell":
            self.spell_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "start_turn": 
            self.start_turn_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "end_turn": 
            self.end_turn_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "draw": 
            self.draw_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "play_friendly_mob": 
            self.play_friendly_mob_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "sent_to_played_pile": 
            self.sent_to_played_piled_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "mob_changes_zones": 
            self.mob_changes_zones_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "spend_mana": 
            self.spend_mana_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "check_mana": 
            self.check_mana_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "after_attack": 
            self.after_attack_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "select_mob_target": 
            self.select_mob_target_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "select_mob_target_override": 
            self.select_mob_target_override_effect_defs.append(self.effect_def_for_id(effect))
        if effect.effect_type == "after_deals_damage": 
            self.after_deals_damage_effect_defs.append(self.effect_def_for_id(effect))

    def __repr__(self):
        return f"{self.as_dict()}"

    def as_dict(self):
        return {
            "abilities": [a.as_dict() for a in self.abilities],
            "added_descriptions": self.added_descriptions,
            "attacked": self.attacked,
            "can_activate_abilities": self.can_activate_abilities,
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
            "show_level_up": self.show_level_up,
            "tokens": [t.as_dict() for t in self.tokens] if self.tokens else [],
            "toughness": self.toughness,
            "turn_played": self.turn_played,
        }


    def effect_def_for_id(self, effect):
        name = effect.name
        if name == "add_ambush":
            return self.do_add_ambush_effect          
        elif name == "add_fade":
            return self.do_add_fade_effect          
        elif name == "add_fast":
            return self.do_add_fast_effect          
        elif name == "add_mob_abilities" or name == "add_player_abilities":
            return self.do_add_abilities_effect          
        elif name == "add_mob_effects":
            return self.do_add_mob_effects_effect
        elif name == "add_random_mob_ability":
            return self.do_add_random_ability_effect_on_mobs
        elif name == "protect_with_shield":
            return self.do_protect_with_shield_effect
        elif name == "add_symbiotic_fast":
            return self.do_add_symbiotic_fast_effect
        elif name == "add_tokens":
            return self.do_add_tokens_effect
        elif name == "augment_mana":
            return self.do_augment_mana_effect
        elif name == "buff_power_toughness_from_mana":
            return self.do_buff_power_toughness_from_mana_effect
        elif name == "create_card":
            return self.do_create_card_effect
        elif name == "create_random_townie":
            return self.do_create_random_townie_effect
        elif name == "create_random_townie_cheap":
            return self.do_create_random_townie_effect_cheap
        elif name == "damage":
            return self.do_damage_effect
        elif name == "decost_card_next_turn":
            return self.do_decost_card_next_turn_effect
        elif name == "decrease_max_mana":
            return self.do_decrease_max_mana_effect
        elif name == "discard_random":
            return self.do_discard_random_effect_on_player
        elif name in ["decost_card_next_turn", "duplicate_card_next_turn", "upgrade_card_next_turn"]:
            return self.do_store_card_for_next_turn_effect
        elif name == "double_power":
            return self.do_double_power_effect_on_mob
        elif name == "drain_hp":
            return self.do_drain_hp_effect
        elif name == "draw":
            return self.do_draw_effect_on_player
        elif name == "draw_if_damaged_opponent":
            return self.do_draw_if_damaged_opponent_effect_on_player
        elif name == "draw_or_resurrect":
           return self.do_draw_or_resurrect_effect
        elif name == "duplicate_card_next_turn":
            return self.do_duplicate_card_next_turn_effect
        elif name == "enable_activated_effect":
            return self.do_enable_activated_effect_effect
        elif name == "entwine":
            return self.do_entwine_effect
        elif name == "evolve":
            return self.do_evolve_effect
        elif name == "fetch_card":
            return self.do_fetch_card_effect_on_player
        elif name == "fetch_card_into_play":
            return self.do_fetch_card_into_play_effect_on_player
        elif name == "force_attack_guard_first":
            return self.do_force_attack_guard_first_effect
        elif name == "gain_for_toughness":
            return self.do_gain_for_toughness_effect
        elif name == "hp_damage_random":
            return self.do_hp_damage_random_effect
        elif name == "heal":            
            return self.do_heal_effect
        elif name == "improve_damage_all_effects_when_used":
            return self.do_improve_damage_when_used_effect            
        elif name == "improve_damage_when_used":
            return self.do_improve_damage_when_used_effect            
        elif name == "improve_effect_amount_when_cast":
            return self.do_improve_effect_amount_when_cast_effect            
        elif name == "improve_effect_when_cast":
            return self.do_improve_effect_when_cast_effect            
        elif name == "kill":
            return self.do_kill_effect
        elif name == "lose_lurker":
            return self.do_lose_lurker_effect
        elif name == "make":
            return self.do_make_effect
        elif name == "make_cheap_with_option":
            return self.do_make_cheap_with_option_effect
        elif name == "make_from_deck":
            return self.do_make_from_deck_effect
        elif name == "make_token":
            return self.do_make_token_effect
        elif name == "make_untargettable":
            return self.do_make_untargettable_effect
        elif name == "mana":
            return self.do_mana_effect_on_player
        elif name == "mana_increase_max":
            return self.do_mana_increase_max_effect_on_player
        elif name == "mana_reduce":
            return self.do_mana_reduce_effect_on_player
        elif name == "mana_set_max":
            return self.do_mana_set_max_effect
        elif name == "mob_to_artifact":
            return self.do_mob_to_artifact_effect
        elif name == "preserve_stats":
            return self.do_preserve_stats_effect
        elif name == "preserve_effect_improvement":
            return self.do_preserve_effect_improvement_effect
        elif name == "pump_power":
            return self.do_pump_power_effect_on_mob
        elif name == "redirect_mob_spell":
           return self.do_redirect_mob_spell_effect
        elif name == "reduce_cost":
           return self.do_reduce_cost_effect
        elif name == "refresh_mana":
            return self.do_refresh_mana_effect
        elif name == "remove_symbiotic_fast":
            return self.do_remove_symbiotic_fast_effect
        elif name == "remove_tokens":
            return self.do_remove_tokens_effect
        elif name == "remove_player_abilities":
            return self.do_remove_player_abilities_effect
        elif name == "riffle":
            return self.do_riffle_effect
        elif name == "set_can_attack":
            return self.do_set_can_attack_effect           
        elif name == "set_token":
            return self.do_set_token_effect
        elif name == "spell_from_yard":
            return self.do_spell_from_yard_effect           
        elif name == "stack_counter":
           return  self.do_counter_card_effect
        elif name == "store_mana":
            return  self.do_store_mana_effect            
        elif name == "summon_from_deck":
            return self.do_summon_from_deck_effect_on_player
        elif name == "summon_from_deck_artifact":
            return self.do_summon_from_deck_artifact_effect_on_player
        elif name == "summon_from_hand":
            return self.do_summon_from_hand_effect
        elif name == "switch_hit_points":
            return self.do_switch_hit_points_effect
        elif name == "take_extra_turn":
            return self.do_take_extra_turn_effect_on_player
        elif name == "take_control":
            return self.do_take_control_effect
        elif name == "unwind":
            return self.do_unwind_effect
        elif name == "upgrade_card_next_turn":
            return self.do_upgrade_card_next_turn_effect
        elif name == "use_stored_mana":
            return self.do_use_stored_mana_effect
        else:
            print(f"UNSUPPORTED EFFECT NAME: {name}")

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
        evolved = card.has_effect("evolve")
        for c in Card.all_card_objects():
            if c.name == card.name:
                new_card = copy.deepcopy(c)
        if evolved:
            card.attacked = False
            card.can_attack_mobs = False
            card.can_attack_players = False
            card.damage = 0
            card.damage_to_show = 0
            card.damage_this_turn = 0
            card.turn_played = -1
            return card
        else:
            new_card.id = card.id
            new_card.owner_username = player.username
            new_card = Card.modify_new_card(new_card, player.game)
            return new_card

    @staticmethod
    def modify_new_card(card, game):
        if card.card_type == Constants.spellCardType:            
            if 'spells_cost_more' in game.global_effects:
                card.cost += game.global_effects.count('spells_cost_more')
            if 'spells_cost_less' in game.global_effects:
                card.cost -= game.global_effects.count('spells_cost_less')
                card.cost = max(0, card.cost)
        elif card.card_type == Constants.mobCardType:            
            if 'mobs_cost_more' in game.global_effects:
                card.cost += game.global_effects.count('mobs_cost_more')
            if 'mobs_cost_less' in game.global_effects:
                card.cost -= game.global_effects.count('mobs_cost_less')
                card.cost = max(0, card.cost)
            if 'mobs_get_more_toughness' in game.global_effects:
                card.toughness += game.global_effects.count('mobs_get_more_toughness')*2
            if 'mobs_get_less_toughness' in game.global_effects:
                card.toughness -= game.global_effects.count('mobs_get_less_toughness')*2
                card.toughness = max(0, card.toughness)
            if 'mobs_get_more_power' in game.global_effects:
                card.power += game.global_effects.count('mobs_get_more_power')*2
            if 'mobs_get_less_power' in game.global_effects:
                card.power -= game.global_effects.count('mobs_get_less_power')*2
                card.power = max(0, card.power)
        return card

    def resolve(self, player, spell_to_resolve):
        for e in player.in_play + player.artifacts:
            for idx, effect in enumerate(e.effects_for_type("friendly_card_played")):
                if effect.target_type == "this":
                    e.do_add_tokens_effect(player, effect, {"id": e.id, "target_type":"mob"})

        spell_to_resolve["log_lines"].append(f"{player.username} plays {self.name}.")

        if self.card_type != Constants.spellCardType:
            spell_to_resolve = player.play_mob_or_artifact(self, spell_to_resolve)

        if len(self.effects) > 0 and self.card_type != Constants.mobCardType:
            if not "effect_targets" in spell_to_resolve:
                spell_to_resolve["effect_targets"] = []

            for target in self.unchosen_targets(player):
                spell_to_resolve["effect_targets"].append(target)

            for idx, effect_def in enumerate(self.spell_effect_defs):
                spell_to_resolve["log_lines"].append(
                    self.resolve_effect(effect_def, player, self.effects[idx], spell_to_resolve["effect_targets"][idx])
                )

            for idx, effect_def in enumerate(self.enter_play_effect_defs):
                spell_to_resolve["log_lines"].append(
                    self.resolve_effect(effect_def, player, self.effects[idx], spell_to_resolve["effect_targets"][idx])
                )

            if len(spell_to_resolve["effect_targets"]) == 0:
                spell_to_resolve["effect_targets"] = None

        if self.card_type == Constants.spellCardType:
            if self.has_ability("Disappear"):
                self.show_level_up = True
            else:            
                player.played_pile.append(self)

        spell_to_resolve["card_name"] = self.name
        spell_to_resolve["show_spell"] = self.as_dict()
        return spell_to_resolve

    def unchosen_targets(self, player, effect_type=None):
        effect_targets = []
        effects = self.effects_spell() + self.effects_enter_play() 
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
        print(f"Resolve effect: {effect.name}");
        if effect.counters >= 1 and effect.name != "store_mana":
            effect.counters -= 1
        log_lines = effect_def(effect_owner, effect, target_info)
        if effect.cost > 0:
            effect_owner.spend_mana(effect.cost)
        if effect.cost_hp > 0:
            effect_owner.hit_points -= effect.cost_hp
        return log_lines

    def do_add_ambush_effect(self, effect_owner, effect, target_info):
        self.can_attack_mobs = True

    def do_add_fast_effect(self, effect_owner, effect, target_info):
        self.can_attack_players = True
        self.can_attack_mobs = True

    def do_add_fade_effect(self, effect_owner, effect, target_info):
        token = {
            "turns": -1,
            "power_modifier": -1,
            "toughness_modifier": -1
        }
        effect = {
            "tokens": [token],
            "id": None
        }
        return self.do_add_token_effect_on_mob(CardEffect(effect, 0), effect_owner, self, effect_owner)

    def do_add_abilities_effect(self, effect_owner, effect, target_info):
        ability = copy.deepcopy(effect.abilities[0])
        target_id = target_info["id"]
        if effect.target_type in ["mob", "opponents_mob", "self_mob"]:
            target_mob, controller = effect_owner.game.get_in_play_for_id(target_id)
            target_mob.abilities.append(ability)
            return [f"{self.name} adds {ability.name} to {target_mob.name}."]
        elif effect.target_type == "opponent" or effect.target_type == "self":
            target_player = Card.player_for_username(effect_owner.game, target_id)            
            target_player.abilities.append(ability)
            target_player.abilities[-1].id = self.id
            return [f"{target_player.username} gets {self.description}."]

    def do_add_mob_effects_effect(self, effect_owner, effect, target_info):
        target_id = target_info["id"]
        target_mob, controller = effect_owner.game.get_in_play_for_id(target_id)
        for e in effect.effects:
            existing_effect = False
            for ee in target_mob.effects:
                if ee.name == e.name:
                    existing_effect = ee
            if existing_effect:
                existing_effect.enabled = True
            else:
                target_mob.effects.append(e)
                target_mob.create_effect_def(e)
                if e.effect_type == "enter_play":
                    self.resolve_effect(target_mob.enter_play_effect_defs[-1], effect_owner, e, {}) 
        return [f"{target_mob.name} gets {effect.name}."]

    def do_add_random_ability_effect_on_mobs(self, effect_owner, effect, target_info):
        for card in effect_owner.in_play:
            self.do_add_random_ability_effect_on_mob(card)
        return [f"{effect_owner.username} added a random ability to their mobs with {self.name}."]

    def do_add_random_ability_effect_on_mob(self, mob):
        a = random.choice(all_abilities())
        mob.abilities.append(CardAbility(a, len(mob.abilities)))

    def do_add_tokens_effect(self, effect_owner, effect, target_info):
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
        token.id = effect.id
        if token.multiplier and token.multiplier == "half_self_mobs":
            for x in range(0, math.floor(len(effect_owner.in_play)/2)):
                target_mob.tokens.append(token)
        elif token.multiplier and token.multiplier == "self_mobs":
            for x in range(0, len(effect_owner.in_play)):
                target_mob.tokens.append(token)
        else:
            target_mob.tokens.append(token)
        if target_mob.toughness_with_tokens() - target_mob.damage <= 0:
            controller.send_card_to_played_pile(target_mob, did_kill=True)
        return [f"{target_mob.name} gets {token}."]

    def do_attack_abilities(self, effect_owner):
        if self.has_ability("DamageDraw"):
            ability = None
            for a in self.abilities:
                if a.descriptive_id == "DamageDraw":
                    ability = a
            if ability.target_type == "opponent":
                effect_owner.game.opponent().draw(ability.amount)
            else:
                effect_owner.draw(ability.amount)

        if self.has_ability("discard_random"):
            ability = None
            for a in self.abilities:
                if a.descriptive_id == "discard_random":
                    ability = a
            self.do_discard_random_effect_on_player(effect_owner.game.opponent(), CardEffect(              
                {
                    "name": "discard_random",
                    "descriptive_id": "discard_random",
                    "amount": 1
                }, 0), {"id": effect_owner.game.opponent().username })
 
    def do_augment_mana_effect(self, effect_owner, effect, target_info):
        store_effect = None
        for e in self.effects:
            if e.name == "store_mana":
                store_effect = e
        effect_owner.card_mana += store_effect.counters

    def do_buff_power_toughness_from_mana_effect(self, effect_owner, effect, target_info):
        mana_count = effect_owner.current_mana()
        effect_owner.spend_mana(effect_owner.current_mana())
        self.power += mana_count
        self.toughness += mana_count
        return [f"{self.name} is now {self.power}/{self.toughness}."]

    def do_counter_card_effect(self, effect_owner, effect, target_info):
        effect_owner.game.actor_turn += 1
        stack_spell = None
        for spell in effect_owner.game.stack:
            if spell[1]["id"] == card_id:
                stack_spell = spell
                break

        # the card was countered by a different counterspell
        if not stack_spell:
            return None

        effect_owner.game.stack.remove(stack_spell)
        #spell_to_resolve = message
        #spell_to_resolve["log_lines"] = []
        card = Card(stack_spell[1])
        effect_owner.game.current_player().send_card_to_played_pile(card, did_kill=False)
        return [f"{card.name} was countered by {effect_owner.game.opponent().username}."]
        # todo: figure if this matter
        # spell_to_resolve["card_name"] = card.name
        # return spell_to_resolve

    def do_create_card_effect(self, effect_owner, effect, target_info):
        if effect.target_type == "self":
            player = Card.player_for_username(effect_owner.game, target_info["id"])            

            for x in range(0, effect.amount):
                if len(player.hand) == player.game.max_hand_size:
                    return
                card_to_create = None
                for card in Card.all_card_objects():
                    if card.name == effect.card_name:
                        card_to_create = card
                player.hand.append(copy.deepcopy(card_to_create))
                player.hand[-1].id = player.game.next_card_id
                player.game.next_card_id += 1

            return [f"{self.name} creates {effect.amount} {effect.card_name}."]
        else:
            print(f"unsupported target_type {effect.target_type} for create_card effect")
            return None

    def do_create_random_townie_effect(self, effect_owner, effect, target_info):
        log_lines = self.do_create_random_townie_effect_with_reduce_cost(effect_owner, effect, target_info, 0)
        if effect.counters == 0:
            self.deactivate_instrument()
        return log_lines
        
    def do_create_random_townie_effect_cheap(self, effect_owner, effect, target_info):
        return self.do_create_random_townie_effect_with_reduce_cost(effect_owner, effect, target_info, 1)

    def do_create_random_townie_effect_with_reduce_cost(self, effect_owner, effect, target_info, reduce_cost):
        player = Card.player_for_username(effect_owner.game, target_info["id"])            
        if len(player.hand) >= player.game.max_hand_size:
            return
        townies = []
        for c in Card.all_card_objects():
            for a in c.abilities:
                if a.descriptive_id == "Townie":
                    townies.append(c)
        for x in range(0, effect.amount):
            t = random.choice(townies)
            player.add_to_deck(t.name, 1, add_to_hand=True, reduce_cost=reduce_cost)
        if effect.amount == 1:
            return [f"{player.username} makes {effect.amount} Townie."]
        return [f"{player.username} makes {effect.amount} Townies."]

    def deactivate_instrument(self):
        self.effects.pop(0)
        self.activated_effect_defs.pop(0)
        for a in self.effects:
            if a.effect_type == "activated":
                a.enabled = True
        self.description = self.original_description

    def do_damage_effect(self, effect_owner, effect, target_info):
        damage_amount = effect.amount 

        # todo this might need to come later in method, and/or make sure damage was dealt
        for idx, e in enumerate(self.effects_for_type("after_deals_damage")):
            self.resolve_effect(self.after_deals_damage_effect_defs[idx], effect_owner, e, {"damage": damage_amount}) 

        target_type = target_info["target_type"] if "target_type" in target_info else None
        target_id = target_info["id"] if "id" in target_info else None
        if effect.amount_id == "hand":            
            damage_amount = len(effect_owner.hand)
        elif effect.amount_id:
            print(f"unknown amount_id: {effect.amount_id}")
        if effect.target_type == "self":
            return self.do_damage_effect_on_player(effect_owner, effect_owner, effect.amount, effect.amount_id)
        elif target_type == "player":
            target_player = Card.player_for_username(effect_owner.game, target_id)
            return self.do_damage_effect_on_player(effect_owner, target_player, effect.amount, effect.amount_id)
        elif target_type == "opponents_mobs":
            return self.damage_mobs(effect_owner.game, effect_owner.game.opponent().in_play, damage_amount, effect_owner.username, f"{effect_owner.game.opponent().username}'s mobs")
        elif effect.target_type == "opponents_mob_random":
            if len(effect_owner.my_opponent().in_play) > 0:
                mob = random.choice(effect_owner.my_opponent().in_play)
                _, controller = effect_owner.game.get_in_play_for_id(mob.id)
                log_lines = [f"{effect_owner.username} deals {damage_amount} damage to {mob.name}."]
                self.do_damage_effect_on_mob(mob, controller, effect.amount, effect.amount_id)
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
            self.do_damage_effect_on_mob(target_mob, controller, effect.amount, effect.amount_id)
            return log_lines

    def damage_mobs(self, game, mobs, damage_amount, damage_dealer, damage_taker):
        dead_mobs = []
        for mob in mobs:
            mob.deal_damage_with_effects(damage_amount, game.opponent())
            if mob.damage >= mob.toughness_with_tokens():
                dead_mobs.append(mob)
        for mob in dead_mobs:
            game.opponent().send_card_to_played_pile(mob, did_kill=True)
        return [f"{damage_dealer} deals {damage_amount} damage to {damage_taker}."]

    def do_damage_effect_on_player(self, effect_owner, target_player, amount, amount_id=None):
        if amount_id == "hand":            
            target_player.damage(len(effect_owner.hand))
            return [f"{self.name} deals {len(effect_owner.hand)} damage to {target_player.username}."]            
        elif not amount_id:
            target_player.damage(amount)
            return [f"{self.name} deals {amount} damage to {target_player.username}."]            
        else:
            print(f"unknown amount_id: {amount_id}")

    def do_damage_effect_on_mob(self, target_card, controller, amount, amount_id=None):
        damage_amount = amount 
        if amount_id == "hand":            
            damage_amount = len(self.hand)
        elif amount_id:
            print(f"unknown amount_id: {amount_id}")

        target_card.deal_damage_with_effects(damage_amount, controller)
        if target_card.damage >= target_card.toughness_with_tokens():
            controller.send_card_to_played_pile(target_card, did_kill=True)

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
            previous_card.evolve(previous_card)
            effect_owner.hand.append(previous_card)
            self.card_for_effect = None

    def do_decrease_max_mana_effect(self, effect_owner, effect, target_info):
        # Mana Shrub leaves play
        if effect.enabled:
            effect_owner.max_mana -= effect.amount
            effect_owner.mana = min(effect_owner.max_mana, effect_owner.mana)

    def do_discard_random_effect_on_player(self, effect_owner, effect, target_info):
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

    def do_double_power_effect_on_mob(self, effect_owner, effect, target_info):
        target_mob, controller = effect_owner.game.get_in_play_for_id(target_info['id'])
        target_mob.power += target_mob.power_with_tokens(controller)
        return [f"{self.name} doubles the power of {target_mob.name}."]

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

    def do_draw_if_damaged_opponent_effect_on_player(self, effect_owner, effect, target_info):
        target_player = effect_owner
        if target_player.game.opponent().damage_this_turn > 0:
            target_player.draw(effect.amount)
            return [f"{target_player.username} draws {effect.amount} from {self.name}."]
        return None
    
    def do_draw_or_resurrect_effect(self, effect_owner, effect, target_info):
        # effect_owner
        amount = effect_owner.mana 
        effect_owner.spend_mana(amount)
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

        return [f"{effect_owner.username} did the RITUAL OF THE NIGHT."]
        return message

    def do_enable_activated_effect_effect(self, effect_owner, effect, target_info):
        # todo don't hardcode turning them all off, only needed for Arsenal, which doesn't even equip anymore
        for e in self.effects_activated():
            if e.effect_to_activate:
                e.enabled = False
        activated_effect = copy.deepcopy(effect.effect_to_activate)
        activated_effect.id = self.id
        activated_effect.enabled = True
        self.description = activated_effect.description
        self.effects.insert(0, activated_effect)
        self.activated_effect_defs.insert(0,self.effect_def_for_id(activated_effect))
        self.can_activate_abilities = True
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
 
    def do_evolve_effect(self, effect_owner, effect, target_info):
        if "did_kill" in target_info and target_info["did_kill"]:
            evolver_card = None
            previous_card = None
            for c in Card.all_card_objects():
                if c.name == effect.original_name:
                    evolver_card = c
                if self.name == c.name:
                    previous_card = c
            self.evolve(previous_card, evolver_card)

    def evolve(self, previous_card, evolver_card=None):
        evolve_cards = []
        for c in Card.all_card_objects():
            if not c.is_token and c.cost > previous_card.cost and c.cost < previous_card.cost + 2 and c.card_type == self.card_type:
                evolve_cards.append(c)
        if len(evolve_cards) > 0:
            evolved_card = random.choice(evolve_cards)
            self.name = evolved_card.name
            self.image = evolved_card.image
            self.description = evolved_card.description
            self.effects = evolved_card.effects
            if evolver_card:
                self.effects.append(evolver_card.effects[0])
            self.abilities = evolved_card.abilities
            self.power = evolved_card.power
            self.toughness = evolved_card.toughness

    def do_fetch_card_effect_on_player(self, effect_owner, effect, target_info):
        if Constants.artifactCardType in effect.target_type:
            self.display_deck_artifacts(effect_owner, effect.target_restrictions, "fetch_artifact_into_hand")
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
            self.display_deck_artifacts(effect_owner, effect.target_restrictions, "fetch_artifact_into_play")
        else:
            print("can't fetch unsupported type")
            return None
        return [f"{effect_owner.username} cracks {self.name} to fetch an artifact."]

    def display_deck_artifacts(self, target_player, target_restrictions, choice_type):
        artifacts = []
        for card in target_player.deck:
            if card.card_type == Constants.artifactCardType:
                if len(target_restrictions) == 0 or \
                    (list(target_restrictions[0].keys())[0] == "needs_instrument" and card.has_ability("Instrument")):
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

    def do_force_attack_guard_first_effect(self, effect_owner, effect, target_info):
        guard_mobs = []
        for mob in effect_owner.in_play:
            for effect in mob.effects:
                if effect.name == "force_attack_guard_first" and mob.can_be_clicked:
                    guard_mobs.append(mob)
        if len(guard_mobs) > 0:
            for mob in effect_owner.in_play:
                mob.can_be_clicked = mob in guard_mobs
            effect_owner.can_be_clicked = False

    def do_gain_for_toughness_effect(self, effect_owner, effect, target_info):
        target_mob, controller = effect_owner.game.get_in_play_for_id(target_info['id'])
        if target_mob:
            controller.hit_points += target_mob.toughness_with_tokens()
            controller.hit_points = min(controller.max_hit_points, controller.hit_points)

    def do_lose_lurker_effect(self, effect_owner, effect, target_info):
        for effect in self.effects:
            if effect.name == "make_untargettable":
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
            target_player.hit_points += amount
            target_player.hit_points = min(target_player.hit_points, target_player.max_hit_points)
            return [f"{target_player.username} heals {amount}."]

    def do_heal_effect_on_mob(self, target_mob, amount):
        target_mob.damage -= amount
        target_mob.damage = max(target_mob.damage, 0)
        target_mob.damage_this_turn -= amount
        target_mob.damage_this_turn = max(target_mob.damage_this_turn, 0)
        return [f"{target_mob.name} heals {amount}."]

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
                self.do_damage_effect_on_player(targets[0], choice, 1)
            else:
                self.do_damage_effect_on_mob(choice, effect_owner.my_opponent(), 1)

    def do_improve_damage_when_used_effect(self, effect_owner, effect, target_info):
        # Rolling Thunder
        self.effects[0].amount += 1
        self.show_level_up = True
        return [f"{self.name} gets improved to deal {self.effects[0].amount} damage."]

    def do_improve_damage_all_effects_when_used_effect(self, effect_owner, effect, target_info):
        # Doomer
        for e in self.effects:
            if e.name == "damage":
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

    def do_kill_effect(self, effect_owner, effect, target_info):
        if effect.target_type == "mob" or effect.target_type == "artifact" or effect.target_type == "mob_or_artifact":
            target_mob, controller = effect_owner.game.get_in_play_for_id(target_info['id'])
            if target_mob:
                log_lines = [f"{self.name} kills {target_mob.name}."]
                self.do_kill_effect_on_mob(target_mob, controller)
                return log_lines
        else:
            cards_to_kill = []
            min_cost = -1
            max_cost = 9999
            instruments_ok = True
            for r in effect.target_restrictions:
                if list(r.keys())[0] == "min_cost":
                    min_cost = list(r.values())[0]
                if list(r.keys())[0] == "max_cost":
                    max_cost = list(r.values())[0]
                if list(r.keys())[0] == "instruments":
                    instruments_ok = list(r.values())[0]
            for player in [effect_owner, effect_owner.game.opponent()]:
                for card in player.in_play+player.artifacts:
                    if card.cost >= min_cost and card.cost <= max_cost and (instruments_ok or not card.has_ability("Instrument")):
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
                "name": "Expensive mobs",
                "cost": 0,
                "card_type": "Effect",
                "description": "mobs cost 1 more",
                "global_effect": "mobs_cost_more"
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
                "name": "Cheap mobs",
                "cost": 0,
                "card_type": "Effect",
                "description": "mobs cost 1 less",
                "global_effect": "mobs_cost_less"
            }
            effects.append(Card(card_info))
            player.card_choice_info["cards"] = effects
            player.card_choice_info["choice_type"] = "make"
            return

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

        return [f"{self.name} made a card from their deck."]

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
            card_name = effect.card_name
            if len(effect.card_names) > 0:
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
            if card.card_type == "Spell" and card.can_be_clicked == True:
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
            if len(self.effects) == 2 and self.effects[1].name == "decrease_max_mana":
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
        old_power = self.power
        old_toughness = self.toughness
        old_level = self.level
        for a in dir(self):
            if not a.startswith('__') and not callable(getattr(self, a)):
                setattr(self, a, getattr(new_card, a))
        self.power = old_power
        self.toughness = old_toughness
        self.level = old_level

    def do_pump_power_effect_on_mob(self, effect_owner, effect, target_info):
        target_mob, _ = effect_owner.game.get_in_play_for_id(target_info['id'])
        target_mob.power += effect.amount
        return [f"{effect_owner.username} pumps the power of {target_mob.name} by {effect.amount}."]

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
        token_card_name = "Willing Villager"
        villager_card.do_make_token_effect(effect_owner, CardEffect({"amount":1, "card_name": token_card_name, "card_names":[]}, 0), {"id": effect_owner.username})

        # the card was countered by a different counterspell
        if not stack_spell:
            return None

        stack_spell[0]["effect_targets"][0]["id"] = effect_owner.game.next_card_id - 1
        return[f"{stack_spell[1]['name']} was redirected to a newly summoned {token_card_name}."]

    def do_remove_player_abilities_effect(self, effect_owner, effect, target_info):
        if "did_kill" in target_info and not target_info["did_kill"]:
            return
        ability_to_remove = None
        # todo this should loop over the abilities in e, in the future there could be more than 1 ability to remove
        for a in effect_owner.abilities:
            if a.id == self.id:
                ability_to_remove = a
        effect_owner.abilities.remove(ability_to_remove)

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

    def do_refresh_mana_effect(self, effect_owner, effect, target_info):
        if effect_owner.mana == 0:
            effect_owner.mana = effect_owner.max_mana

    def do_use_stored_mana_effect(self, effect_owner, effect, target_info):
        amount_to_spend = target_info["amount_to_spend"]
        store_effect = None
        for e in self.effects:
            if e.name == "store_mana":
                store_effect = e
        while amount_to_spend > 0 and store_effect.counters > 0:                        
            store_effect.counters -= 1
            amount_to_spend -= 1
    
    def do_riffle_effect(self, effect_owner, effect, target_info):
        player = effect_owner
        top_cards = []
        for card in player.deck:
            if len(top_cards) < effect.amount:
                top_cards.append(card)
        player.card_choice_info = {"cards": top_cards, "choice_type": "riffle"}
        return [f"{player.username} riffles for {effect.amount}."]

    def do_set_can_attack_effect(self, effect_owner, effect, target_info):
        if effect.target_type == "self_mobs":
            player = effect_owner
            for e in player.in_play:
                e.can_attack_mobs = True
                e.can_attack_players = True
                e.attacked = False
            return [f"{player.username} lets their mobs attack again this turn."]          
        else:
            print(f"e.target_type {target_type} not supported for set_can_attack")

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

    def do_protect_with_shield_effect(self, effect_owner, effect, target_info):
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
            "name": "add_fast",
            "description": "Fast",
            "description_expanded": "Fast mobs may attack the turn they come into play.",
            "effect_type": "enter_play"
        }        

    # todo fix that this doesn't check for an ID or something?
    def do_remove_symbiotic_fast_effect(self, effect_owner, effect, target_info):
        effects_to_remove = []
        for effect in self.effects:
            if effect.name == "add_fast":
               effects_to_remove.append(effect)
               break 
        for effect in effects_to_remove:
            self.effect.remove(effect)

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
        elif effect.target_type == "opponents_mob_random": # song dragon
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
        controller.in_play.remove(target_mob)
        effect_owner.in_play.append(target_mob)
        effect_owner.game.players[0].update_for_mob_changes_zones()
        effect_owner.game.players[1].update_for_mob_changes_zones()
        target_mob.turn_played = effect_owner.game.turn
        target_mob.attacked = False
        target_mob.can_attack_mobs = False
        target_mob.can_attack_players = False
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
        target_player.game.remove_temporary_effects()
        target_player.remove_temporary_abilities()
        target_player.clear_damage_this_turn()
        target_player.game.turn += 2
        log_lines = [f"{target_player.username} takes an extra turn."]
        message = target_player.start_turn({"log_lines":[]})
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
        for e in self.effects_activated():
            if e.enabled:
               enabled_effects.append(e)
        return enabled_effects

    def needs_targets_for_spell(self):
        if len(self.effects_spell()) == 0:
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
                if len(e.target_restrictions) > 0 and list(e.target_restrictions[0].keys())[0] == "target" and list(e.target_restrictions[0].values())[0] == "mob":
                    action = spell[0]
                    if "effect_targets" in action and action["effect_targets"][0]["target_type"] == Constants.mobCardType:
                        return True
                else:
                    return True
            if e.target_type == "being_cast_artifact" and card.card_type == Constants.artifactCardType:
                return True
        return False

    def needs_opponent_mob_target_for_spell(self):
        e = self.effects_spell()[0]
        if e.target_type in ["opponents_mob"]:
            return True
        return False

    def needs_opponent_mob_target_for_spell(self):
        e = self.effects_spell()[0]
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

    def power_with_tokens(self, player):
        power = self.power
        for t in self.tokens:
            if t.multiplier == "self_artifacts":
                power += t.power_modifier * len(player.artifacts)
            elif t.multiplier == "self_mobs_and_artifacts":
                power += t.power_modifier * (len(player.artifacts) + len(player.in_play))
            else:
                power += t.power_modifier
        return power

    def toughness_with_tokens(self):
        toughness = self.toughness
        for t in self.tokens:
            toughness += t.toughness_modifier
        return toughness

    def has_effect(self, effect_name):
        for e in self.effects:
            if e.name == effect_name:
                return True
        return False

    def has_ability(self, ability_name):
        for a in self.abilities:
            if a.descriptive_id == ability_name and a.enabled:
                return True
        return False

    def do_leaves_play_effects(self, player, did_kill=True):
        for idx, effect_def in enumerate(self.leave_play_effect_defs):
            target_info = {"id": player.username, "did_kill": did_kill}
            if self.effects_leave_play()[idx].target_type == "self":
                target_info = {"id": player.username, "target_type": "player", "did_kill": did_kill}
            elif self.effects_leave_play()[idx].target_type == "opponent":
                target_info = {"id": player.game.opponent().username, "target_type": "player", "did_kill": did_kill}
            self.resolve_effect(effect_def, player, self.effects_leave_play()[idx], target_info)

    def effects_leave_play(self):
        return [e for e in self.effects if e.effect_type == "leave_play"]

    def effects_enter_play(self):
        return [e for e in self.effects if e.effect_type == "enter_play"]

    def effects_activated(self):
        return [e for e in self.effects if e.effect_type == "activated"]

    def effects_for_type(self, effect_type):
        return [e for e in self.effects if e.effect_type == effect_type]

    def effects_spell(self):
        return [e for e in self.effects if e.effect_type == "spell"]

    def effects_enabled(self):
        return [e for e in self.effects if e.enabled == True]

    def effect_for_id(self, effect_id):
        for e in self.effects:
            if e.id == effect_id:
                return e

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
        self.id = effect_id

        self.abilities = [CardAbility(a, idx) for idx, a in enumerate(info["abilities"])] if "abilities" in info else []
        self.activate_on_add = info["activate_on_add"] if "activate_on_add" in info else False
        self.ai_target_types = info["ai_target_types"] if "ai_target_types" in info else []
        self.amount = info["amount"] if "amount" in info else None
        self.amount_id = info["amount_id"] if "amount_id" in info else None
        self.card_descriptions = info["card_descriptions"] if "card_descriptions" in info else []
        self.card_name = info["card_name"] if "card_name" in info else None
        self.card_names = info["card_names"] if "card_names" in info else []
        self.counters = info["counters"] if "counters" in info else -1
        self.cost = info["cost"] if "cost" in info else 0
        self.cost_hp = info["cost_hp"] if "cost_hp" in info else 0
        self.description = info["description"] if "description" in info else None
        self.description_expanded = info["description_expanded"] if "description_expanded" in info else None
        self.effects = [CardEffect(e, idx) for idx, e in enumerate(info["effects"])] if "effects" in info else []
        self.effect_to_activate = CardEffect(info["effect_to_activate"], info["effect_to_activate"]["id"] if "id" in info["effect_to_activate"] else 0) if "effect_to_activate" in info and info["effect_to_activate"] else None
        self.effect_type = info["effect_type"] if "effect_type" in info else None
        self.enabled = info["enabled"] if "enabled" in info else True
        self.image = info["image"] if "image" in info else None
        self.make_type = info["make_type"] if "make_type" in info else None
        self.multiplier = info["multiplier"] if "multiplier" in info else None
        self.name = info["name"] if "name" in info else None 
        self.original_name = info["original_name"] if "original_name" in info else None 
        self.power = info["power"] if "power" in info else None
        self.sacrifice_on_activate = info["sacrifice_on_activate"] if "sacrifice_on_activate" in info else False
        self.show_effect_animation = info["show_effect_animation"] if "show_effect_animation" in info else False
        self.targetted_this_turn = info["targetted_this_turn"] if "targetted_this_turn" in info else []
        self.target_restrictions = info["target_restrictions"] if "target_restrictions" in info else []
        self.target_type = info["target_type"] if "target_type" in info else None
        self.tokens = [CardToken(t) for t in info["tokens"]] if "tokens" in info else []
        self.toughness = info["toughness"] if "toughness" in info else None
        self.turns = info["turns"] if "turns" in info else 0
        self.ui_info = info["ui_info"] if "ui_info" in info else None
        self.was_added = info["was_added"] if "was_added" in info else False

    def __repr__(self):
        return f"{self.as_dict()}"

    def as_dict(self):
        return {
            "abilities": [a.as_dict() for a in self.abilities] if self.abilities else [],
            "activate_on_add": self.activate_on_add,
            "ai_target_types": self.ai_target_types,
            "amount": self.amount,
            "amount_id": self.amount_id,
            "card_descriptions": self.card_descriptions,
            "card_name": self.card_name,
            "card_names": self.card_names,
            "counters": self.counters,
            "cost": self.cost,
            "cost_hp": self.cost_hp,
            "description": self.description,
            "description_expanded": self.description_expanded,
            "effects": [e.as_dict() for e in self.effects] if self.effects else [],
            "effect_to_activate": self.effect_to_activate.as_dict() if self.effect_to_activate else None,
            "effect_type": self.effect_type,
            "enabled": self.enabled,
            "id": self.id,
            "image": self.image,
            "make_type": self.make_type,
            "multiplier": self.multiplier,
            "name": self.name,
            "original_name": self.original_name,
            "power": self.power,
            "sacrifice_on_activate": self.sacrifice_on_activate,
            "show_effect_animation": self.show_effect_animation,
            "targetted_this_turn": self.targetted_this_turn,
            "target_restrictions": self.target_restrictions,
            "target_type": self.target_type,
            "tokens": [t.as_dict() for t in self.tokens] if self.tokens else [],
            "toughness": self.toughness,
            "turns": self.turns,
            "ui_info": self.ui_info,
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
        return f"{self.as_dict()}"

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
