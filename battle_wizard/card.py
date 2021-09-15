import copy
import math
import random

from battle_wizard.data import all_cards

class Card:
    
    spellCardType = "spell"
    mobCardType = "mob"
    artifactCardType = "artifact"

    def __init__(self, info):
        self.id = info["id"] if "id" in info else -1

        self.abilities = [CardAbility(a, idx) for idx, a in enumerate(info["abilities"])] if "abilities" in info and info["abilities"] else []
        self.added_descriptions = info["added_descriptions"] if "added_descriptions" in info else []
        self.attacked = info["attacked"] if "attacked" in info else False
        self.can_activate_abilities = info["can_activate_abilities"] if "can_activate_abilities" in info else True
        self.can_be_clicked = info["can_be_clicked"] if "can_be_clicked" in info else False
        self.card_for_effect = Card(info["card_for_effect"]) if "card_for_effect" in info and info["card_for_effect"] else None
        self.card_subtype = info["card_subtype"] if "card_subtype" in info else None
        self.card_type = info["card_type"] if "card_type" in info else Card.mobCardType
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
        self.shielded = info["shielded"] if "shielded" in info else False
        self.show_level_up = info["show_level_up"] if "show_level_up" in info else False
        self.tokens = [CardToken(t) for t in info["tokens"]] if "tokens" in info else []
        self.toughness = info["toughness"] if "toughness" in info else None
        self.turn_played = info["turn_played"] if "turn_played" in info else -1

    def __repr__(self):
        return f"{self.as_dict()}"

    def as_dict(self):
        return {
            "abilities": [a.as_dict() for a in self.abilities],
            "added_descriptions": self.added_descriptions,
            "attacked": self.attacked,
            "can_activate_abilities": self.can_activate_abilities,
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
            "shielded": self.shielded,
            "show_level_up": self.show_level_up,
            "tokens": [t.as_dict() for t in self.tokens] if self.tokens else [],
            "toughness": self.toughness,
            "turn_played": self.turn_played,
        }

    @staticmethod
    def all_card_objects(require_images=False, include_tokens=True):
        return [Card(c_info) for c_info in all_cards(require_images, include_tokens)]
    
    @staticmethod  
    def player_for_username(game, username):
        if game.players[0].username == username:
            return game.players[0]
        return game.players[1]

    @staticmethod
    def is_under_ice_prison(game):
        for c in game.current_player().artifacts + game.opponent().artifacts:
            if len(c.effects_triggered()) > 0 and c.effects_triggered()[0].name ==  "stop_mob_renew":
                return True
        return False

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
        if card.card_type == Card.spellCardType:            
            if 'spells_cost_more' in game.global_effects:
                card.cost += game.global_effects.count('spells_cost_more')
            if 'spells_cost_less' in game.global_effects:
                card.cost -= game.global_effects.count('spells_cost_less')
                card.cost = max(0, card.cost)
        elif card.card_type == Card.mobCardType:            
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
            for idx, effect in enumerate(e.effects_triggered()):
                if effect.trigger == "friendly_card_played" and effect.target_type == "this":
                    e.do_add_tokens_effect(e, effect, {idx: {"id": e.id, "target_type":"mob"}}, idx)

        spell_to_resolve["log_lines"].append(f"{player.username} plays {self.name}.")

        if self.card_type != Card.spellCardType:
            spell_to_resolve = player.play_mob_or_artifact(self, spell_to_resolve)

        if self.card_type == Card.mobCardType and self.has_ability("Shield"):
            self.shielded = True

        if len(self.effects) > 0 and self.card_type != Card.mobCardType:
            if not "effect_targets" in spell_to_resolve:
                spell_to_resolve["effect_targets"] = []

            for target in self.unchosen_targets(player):
                spell_to_resolve["effect_targets"].append(target)

            for idx, target in enumerate(self.effects_spell() + self.effects_enter_play()):
                spell_to_resolve = self.do_effect(player, self.effects[idx], spell_to_resolve, spell_to_resolve["effect_targets"], idx)
           
            if len(spell_to_resolve["effect_targets"]) == 0:
                spell_to_resolve["effect_targets"] = None

            if len(self.effects) == 2:
                if self.effects[1].name == "improve_damage_when_used":
                    # hack for Rolling Thunder
                    self.effects[0].amount += 1
                    self.show_level_up = True
                if self.effects[1].name == "improve_effect_amount_when_cast":
                    # hack for Tech Crashhouse
                    self.effects[0].amount += 1
                    self.show_level_up = True
                if self.effects[1].name == "improve_effect_when_cast":
                    # hack for Tame Shop Demon
                    old_level = self.level
                    self.level += 1
                    self.level = min(self.level, len(self.effects[0].self_names)-1)
                    if self.level > old_level:
                        self.show_level_up = True

        if self.card_type == Card.spellCardType:
            if self.has_ability("Disappear"):
                self.show_level_up = True
            else:            
                player.played_pile.append(self)

        spell_to_resolve["card_name"] = self.name
        spell_to_resolve["show_spell"] = self.as_dict()
        return spell_to_resolve

    def unchosen_targets(self, player, effect_type="cast"):
        effect_targets = []
        effects = self.effects_spell() + self.effects_enter_play()
        if effect_type == "triggered":
            effects = self.effects_triggered()
        for idx, e in enumerate(effects):
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
        return effect_targets

    def do_effect(self, effect_owner, e, message, effect_targets, target_index):
        print(f"Do card effect: {e.name}");

        # weapons and instruments
        if e.counters >= 1:
            e.counters -= 1

        target_id = effect_targets[target_index]["id"] if target_index < len(effect_targets) and "id" in effect_targets[target_index] else None
        target_player = Card.player_for_username(effect_owner.game, target_id) if target_id and effect_targets[target_index]["target_type"] == "player" else None
        target_mob = None
        controller = None
        if target_id and e.target_type in ["mob", "artifact", "mob_or_artifact"]:
            target_mob, controller = effect_owner.game.get_in_play_for_id(target_id)

        log_lines = None
        if e.name == "add_effects":
            log_lines = self.do_add_effects_effect(effect_owner, e, target_mob, controller, target_player)           
        elif e.name == "add_mob_abilities" or e.name == "add_player_abilities":
            log_lines = self.do_add_abilities_effect(effect_owner, e, target_mob, controller, target_player)           
        elif e.name == "add_random_mob_ability":
            log_lines = self.do_add_random_ability_effect_on_mobs(effect_owner, e, target_mob, controller, target_player)
        elif e.name == "add_tokens":
            log_lines = self.do_add_tokens_effect(e, effect_owner, target_mob, controller)
        elif e.name == "attack":
            log_lines = self.do_attack_effect(effect_owner, e, target_mob, controller, target_player)
        elif e.name == "buff_power_toughness_from_mana":
            log_lines = self.do_buff_power_toughness_from_mana_effect(effect_owner, self)
        elif e.name == "create_card":
            log_lines = self.do_create_card_effect(effect_owner, e, message)
        elif e.name == "create_random_townie":
            log_lines = self.do_create_random_townie_effect(target_player, e)
        elif e.name == "create_random_townie_cheap":
            log_lines = self.do_create_random_townie_effect(target_player, e, reduce_cost=1)
        elif e.name == "discard_random":
            log_lines = self.do_discard_random_effect_on_player(self, target_player, e.amount, e.amount_id)
        elif e.name == "damage":
            log_lines = self.do_damage_effect(effect_owner, e, effect_targets, target_index)
        elif e.name in ["decost_card_next_turn", "duplicate_card_next_turn", "upgrade_card_next_turn"]:
            # todo no log lines returned
            log_lines = self.do_store_card_for_next_turn_effect(effect_owner, target_id)
        elif e.name == "double_power":
            log_lines = self.do_double_power_effect_on_mob(effect_owner, target_mob, controller)
        elif e.name == "draw":
            log_lines = self.do_draw_effect_on_player(target_player, e.amount, e.multiplier)
        elif e.name == "draw_if_damaged_opponent":
            log_lines = self.do_draw_if_damaged_opponent_effect_on_player(effect_owner,  e.amount)
        elif e.name == "draw_or_resurrect":
           log_lines = self.do_draw_or_resurrect_effect(effect_owner)
        elif e.name == "enable_activated_effect":
            log_lines = self.do_enable_activated_effect_effect(effect_owner)
        elif e.name == "entwine":
            log_lines = self.do_entwine_effect(effect_owner)
        elif e.name == "equip_to_mob":
            log_lines = self.do_enable_equip_to_mob_effect(effect_owner, target_mob, controller)
        elif e.name == "fetch_card":
            log_lines = self.do_fetch_card_effect_on_player(effect_owner, e.target_type, e.target_restrictions, choice_type="fetch_artifact_into_hand")
        elif e.name == "fetch_card_into_play":
            log_lines = self.do_fetch_card_effect_on_player(effect_owner, e.target_type, e.target_restrictions, choice_type="fetch_artifact_into_play")
        elif e.name == "gain_for_toughness":
            log_lines = self.do_gain_for_toughness_effect(target_mob, controller)
        elif e.name == "heal":
            log_lines = self.do_heal_effect(effect_targets[target_index]["target_type"], target_player, target_mob, amount)
        elif e.name == "kill":
            log_lines = self.do_kill_effect(e, effect_owner, target_mob, controller)
        elif e.name == "make":
            log_lines = self.do_make_effect(target_player, e.make_type)
        elif e.name == "make_cheap_with_option":
            log_lines = self.do_make_effect(effect_owner, e.make_type, reduce_cost=1, option=True)
        elif e.name == "make_from_deck":
            log_lines = self.do_make_from_deck_effect(effect_owner)
        elif e.name == "make_token":
            log_lines = self.do_make_token_effect(target_player, e, self)
        elif e.name == "mana":
            log_lines = self.do_mana_effect_on_player(target_player, e.amount)
        elif e.name == "mana_increase_max":
            log_lines = self.do_mana_increase_max_effect_on_player(target_player, e.amount)
        elif e.name == "mana_reduce":
            log_lines = self.do_mana_reduce_effect_on_player(target_player, e.amount)
        elif e.name == "mana_set_max":
            log_lines = self.do_mana_set_max_effect(effect_owner.game, e.amount)
        elif e.name == "mob_to_artifact":
            log_lines = self.do_mob_to_artifact_effect(effect_owner, target_mob, controller)
        elif e.name == "pump_power":
            log_lines = self.do_pump_power_effect_on_mob(effect_owner, target_mob, e.amount)
        elif e.name == "redirect_mob_spell":
           log_lines = self.do_redirect_mob_spell_effect(target_id, effect_owner)
        elif e.name == "riffle":
            log_lines = self.do_riffle_effect(target_player, e.amount)
        elif e.name == "set_can_attack":
            log_lines = self.do_set_can_attack_effect(e.target_type, effect_owner)           
        elif e.name == "stack_counter":
           log_lines =  self.do_counter_card_effect(effect_owner, target_id)
        elif e.name == "summon_from_deck":
            log_lines = self.do_summon_from_deck_effect_on_player(e, effect_owner, target_player, effect_targets, target_index)
        elif e.name == "summon_from_deck_artifact":
            log_lines = self.do_summon_from_deck_artifact_effect_on_player(effect_owner, e)
        elif e.name == "summon_from_hand":
            log_lines = self.do_summon_from_hand_effect(effect_owner, target_player)
        elif e.name == "switch_hit_points":
            log_lines = self.do_switch_hit_points_effect(effect_owner)
        elif e.name == "take_extra_turn":
            log_lines = self.do_take_extra_turn_effect_on_player(target_player, message)
        elif e.name == "take_control":
            log_lines = self.do_take_control_effect(e, effect_owner, target_mob)
        elif e.name == "unwind":
            log_lines = self.do_unwind_effect(e, effect_owner, target_mob, controller)
        elif e.name == "unequip_from_mob":
            log_lines = self.do_unequip_from_mob_effect(effect_owner)

        if log_lines:
            message["log_lines"] = log_lines
        effect_owner.spend_mana(e.cost)
        effect_owner.hit_points -= e.cost_hp
        
        return message 

    def do_add_abilities_effect(self, effect_owner, effect, target_mob, controller, target_player):
        # effect_owner, controller are unused
        ability = copy.deepcopy(effect.abilities[0])
        if effect.target_type in ["mob", "opponents_mob", "self_mob"]:
            target_mob.abilities.append(ability)
            return [f"{self.name} adds {ability.name} to {target_mob.name}."]
        elif e.target_type == "opponent" or e.target_type == "self":
            target_player.abilities.append(ability)
            target_player.abilities[-1].id = self.id
            return [f"{target_player.username} gets {self.description}."]

    def do_add_effects_effect(self, effect_owner, effect, target_mob, controller, target_player):
        # target_player is unused
        log_lines = []
        if effect.target_type == "self_mobs":
            for c in effect_owner.in_play:
                for effect_effect in effect.effects:
                    effect_effect.enabled = False
                    self.do_add_effect_effect_on_mob(effect_effect, target_mob, controller)
        elif effect.target_type == "opponents_mob":
                for idx, effect_effect in enumerate(effect.effects):
                    if effect_effect.name == "take_control":
                        log_lines.append(f"{self.username} takes control of {target_mob.name} with {self.name}.")
                        self.do_add_effect_effect_on_mob(effect_effect, target_mob, controller)
                        self.do_take_control_effect_on_mob(effect_owner, target_mob, controller)
        # todo better log message
        return log_lines

    def do_add_effect_effect_on_mob(self, effect, target_mob, controller):
        target_mob.effects.insert(0, effect)
        target_mob.added_descriptions.append(effect.description)
        if effect.activate_on_add:
            # todo: make this generic if we add other added
            if effect.name == "mana_increase_max":
                target_mob.do_mana_increase_max_effect_on_player(controller, effect.amount)

    def do_add_random_ability_effect_on_mobs(self, effect_owner, e, target_mob, controller, target_player):
        for card in effect_owner.in_play:
            self.do_add_random_ability_effect_on_mob(card)
        return [f"{effect_owner.username} added a random ability to their mobs with {self.name}."]

    def do_add_random_ability_effect_on_mob(self, mob):
        abilities = [
            {
                "name": "Fast",
                "descriptive_id": "Fast"
            },
            {
                "name": "Syphon",
                "descriptive_id": "Syphon"
            },
            {
                "name": "Lurker",
                "descriptive_id": "Lurker"
            },
            {
                "name": "Shield",
                "descriptive_id": "Shield"
            },
            {
                "name": "Conjure",
                "descriptive_id": "Conjure"
            },
            {
                "name": "Guard",
                "descriptive_id": "Guard"
            },
            {
                "name": "Defend",
                "descriptive_id": "Defend"
            },
            {
                "name": "Fade",
                "descriptive_id": "Fade"
            },
            {
                "name": "Ambush",
                "descriptive_id": "Ambush"
            },
        ]
        a = random.choice(abilities)
        mob.abilities.append(CardAbility(a, len(mob.abilities)))

    def do_add_tokens_effect(self, e, effect_owner, target_mob, controller):
        if target_mob:
            for token in e.tokens:
                self.do_add_token_effect_on_mob(e, effect_owner, target_mob, controller)
        else:  # e.target_type == "self_mobs"
            for token in e.tokens:
                for mob in effect_owner.in_play:
                    self.do_add_token_effect_on_mob(e, effect_owner, mob, effect_owner)
        if e.target_type == 'self_mobs':
            return [f"{effect_owner.username} adds {str(e.tokens[0])} to their own mobs."]
        else:
            return [f"{effect_owner.username} adds {str(e.tokens[0])} to {target_mob.name}."]

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

    def do_attack_effect(self, effect_owner, e, target_mob, controller, target_player):
        #todo fix hardcoding attack effect, is every attack effect from a weapon?
        if target_player:
            log_lines = self.do_attack_effect_on_player(effect_owner, target_player, e.power, e.amount_id)
        else:
            log_lines = self.do_attack_effect_on_mob(effect_owner, target_mob, controller, e.power)
        if e.counters == 0:
            if e.was_added:
                self.deactivate_weapon()
            else:
                controller.send_card_to_played_pile(self, did_kill=True)
        return log_lines

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

    def do_attack_effect_on_player(self, effect_owner, target_player, power, amount_id):
        self.do_damage_effect_on_player(effect_owner, target_player, power, amount_id)
        self.do_attack_abilities(effect_owner)
        return [f"{effect_owner.username} attacks {target_id} for {power} damage."]

    def do_attack_effect_on_mob(self, effect_owner, target_mob, controller, amount):
        target_mob.damage(amount)
        self.do_damage_effect_on_mob(target_mob, controller, amount)
        return [f"{effect_owner.username} attacks {target_mob.name} for {amount} damage."]

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

        if self.has_ability("Syphon"):
            effect_owner.hit_points += self.power_with_tokens(effect_owner)
            effect_owner.hit_points = min(30, effect_owner.hit_points)
        if self.has_ability("discard_random"):
            ability = None
            for a in self.abilities:
                if a.descriptive_id == "discard_random":
                    ability = a
            self.do_discard_random_effect_on_player(effect_owner, effect_owner.game.opponent(), ability.amount)
 
    def do_buff_power_toughness_from_mana_effect(self, effect_owner, target_mob):
        mana_count = effect_owner.current_mana()
        effect_owner.spend_mana(effect_owner.current_mana())
        target_mob.power += mana_count
        target_mob.toughness += mana_count
        return [f"{target_mob.name} is now {target_mob.power}/{target_mob.toughness}."]

    def do_counter_card_effect(self, effect_owner, card_id):
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

    def do_create_card_effect(self, player, e):
        for x in range(0, e.amount):
            if len(player.hand) == player.game.max_hand_size:
                return
            card_to_create = None
            for card in Card.all_card_objects():
                if card.name == e.card_name:
                    card_to_create = card
            player.hand.append(copy.deepcopy(card_to_create))
            player.hand[-1].id = player.game.next_card_id
            player.game.next_card_id += 1

        if e.target_type == "self":
            return [f"{self.name} creates {e.amount} {e.card_name}."]
        else:
            print(f"unsupported target_type {e.target_type} for create_card effect")
            return None

    def do_create_random_townie_effect(self, player, effect, reduce_cost=0):
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
        #todo fix hardcoding
        if effect.counters == 0 and self.name == "Lute":
            self.deactivate_instrument()
        if effect.amount == 1:
            return [f"{player.username} makes {effect.amount} Townie."]
        return [f"{player.username} makes {effect.amount} Townies."]

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

    def do_damage_effect(self, effect_owner, e, effect_targets, target_index):
        damage_amount = e.amount 
        target_type = effect_targets[target_index]["target_type"]
        if e.amount_id == "hand":            
            damage_amount = len(self.hand)
        elif e.amount_id:
            print(f"unknown amount_id: {e.amount_id}")
        if target_type == "player":
            target_player = effect_owner.game.players[0]
            if target_player.username != effect_targets[target_index]["id"]:
                target_player = effect_owner.game.players[1]
            return self.do_damage_effect_on_player(effect_owner, target_player, e.amount, e.amount_id)
        elif target_type == "opponents_mobs":
            return self.damage_mobs(effect_owner.game, effect_owner.game.opponent().in_play, damage_amount, effect_owner.username, f"{effect_owner.game.opponent().username}'s mobs", message)
        elif target_type == "all_mobs" or target_type == "all":
            damage_taker = "all mobs"
            if target_type == "all":
                damage_taker = "all mobs and players"
            log_lines = self.damage_mobs(effect_owner.game.opponent().in_play + effect_owner.in_play, damage_amount, effect_owner.username, damage_taker, message)
            if target_type == "all":
                effect_owner.damage(damage_amount)
                effect_owner.game.opponent().damage(damage_amount)
        else:
            target_mob, controller = effect_owner.game.get_in_play_for_id(effect_targets[target_index]['id'])
            log_lines = [f"{effect_owner.username} deals {damage_amount} damage to {target_mob.name}."]
            self.do_damage_effect_on_mob(target_mob, controller, e.amount, e.amount_id)
            return log_lines

    def damage_mobs(self, game, mobs, damage_amount, damage_dealer, damage_taker):
        dead_mobs = []
        for mob in mobs:
            mob.damage += damage_amount
            mob.damage_this_turn += damage_amount
            mob.damage_to_show += damage_amount
            if mob.damage >= mob.toughness_with_tokens():
                dead_mobs.append(mob)
        for mob in dead_mobs:
            game.opponent().send_card_to_played_pile(mob, did_kill=True)
        return [f"{damage_dealer} deals {damage_amount} damage to {damage_taker}."]
        return message

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

        if target_card.shielded:
            if damage_amount > 0:
                target_card.shielded = False
        else:
            target_card.damage += damage_amount
            target_card.damage_to_show += damage_amount
            if target_card.damage >= target_card.toughness_with_tokens():
                controller.send_card_to_played_pile(target_card, did_kill=True)

    def do_discard_random_effect_on_player(self, target_player, amount, amount_id=None, to_deck=False):
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
            # dont use send_card_to_played_pile, this triggers effects
            target_player.send_card_to_played_pile(card, did_kill=False)
            if to_deck:
                for c in target_player.played_pile:
                    if c.id == card.id:
                        break
                if c:
                    target_player.played_pile.remove(c)
                    target_player.deck.append(c)
                    random.shuffle(target_player.deck)

        if amount_to_log == 1:
            return [f"{target_player.username} discards {amount_to_log} card from {self.name}."]
        elif amount_to_log > 0:
            return [f"{target_player.username} discards {amount_to_log} cards from {self.name}."]

    def do_double_power_effect_on_mob(self, effect_owner, target_mob, target_player):
        target_mob.power += target_mob.power_with_tokens(target_player)
        return [f"{self.name} doubles the power of {target_mob.name}."]

    def do_draw_effect_on_player(self, target_player, amount, multiplier):
        amount_to_draw = amount
        if multiplier == "self_mobs":
            amount_to_draw = amount *len(target_player.in_play)
        target_player.draw(amount_to_draw)
        return [f"{target_player.username} draws {amount_to_draw} from {self.name}."]

    def do_draw_if_damaged_opponent_effect_on_player(self, target_player, amount):
        if target_player.game.opponent().damage_this_turn > 0:
            target_player.draw(amount)
            return [f"{player.username} draws {e.amount} from {self.name}."]
        return None
    
    def do_draw_or_resurrect_effect(self, effect_owner):
        amount = effect_owner.mana 
        effect_owner.spend_mana(amount)
        dead_mobs = []
        for card in effect_owner.played_pile:
            if card.card_type == Card.mobCardType:
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

    def do_enable_activated_effect_effect(self, effect_owner):
        # todo don't hardcode turning them all off, only needed for Arsenal because it has two equip effects
        for e in self.effects:
            if e.effect_to_activate:
                e.enabled = False
        e = copy.deepcopy(self.effects[0].effect_to_activate)
        e.id = self.id
        e.enabled = True
        self.description = e.description
        self.effects.append(e)
        self.can_activate_abilities = True
        return [f"{effect_owner.username} activates {self.name}."]

    def do_enable_equip_to_mob_effect(self, effect_owner, target_mob, controller):
        # todo don't hardcode turning them all off, only needed for Arsenal because it has two equip effects
        for e in self.effects:
            if e.effect_to_activate:
                e.enabled = False
        e = self.effects[effect_owner.card_info_to_target["effect_index"]].effect_to_activate
        e["id"] = self.id
        log_lines = self.do_add_token_effect_on_mob(e, effect_owner, target_mob, controller)
        effect = CardEffect({
                    "name": "unequip_from_mob",
                    "effect_type": "activated",
                    "target_type": "self",
                    "was_added": True
                }, self.id)
        self.effects.append(effect)
        self.description = e.description
        return log_lines

    def do_entwine_effect(self, effect_owner):
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
 
    def do_fetch_card_effect_on_player(self, target_player, card_type, target_restrictions, choice_type=None):
        if Card.artifactCardType in card_type:
            self.display_deck_artifacts(target_player, target_restrictions, choice_type)
        elif card_type == "all_cards_in_deck":
            self.display_deck_for_fetch(target_player)
        elif card_type == "all_cards_in_played_pile":
            self.display_played_pile_for_fetch(target_player, self.id)
        else:
            print("can't fetch unsupported type")
            return None

        if choice_type == "fetch_artifact_into_play":
            return [f"{target_player.username} cracks {self.name} to fetch an artifact."]
        return [f"{target_player.username} fetches a card with {self.name}."]

    def display_deck_artifacts(self, target_player, target_restrictions, choice_type):
        artifacts = []
        for card in target_player.deck:
            if card.card_type == Card.artifactCardType:
                if len(target_restrictions) == 0 or \
                    (list(target_restrictions[0].keys())[0] == "needs_weapon" and card.has_ability("Weapon")) or \
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

    def do_gain_for_toughness_effect(self, target_mob, controller):
        if target_mob:
            controller.hit_points += target_mob.toughness_with_tokens()
            controller.hit_points = min (30, controller.hit_points)

    def do_heal_effect(self, target_type, target_player, target_mob, amount):
        if target_type == "player":
            return self.do_heal_effect_on_player(target_player, amount)
        else:
            return self.do_heal_effect_on_mob(target_mob, amount)

    def do_heal_effect_on_player(self, target_player, amount):
        target_player.hit_points += amount
        target_player.hit_points = min(target_player.hit_points, 30)
        return [f"{effect_owner.username} heals {e.amount} on {target_player.username}."]

    def do_heal_effect_on_mob(self, target_mob, amount):
        target_mob.damage -= amount
        target_mob.damage = max(target_mob.damage, 0)
        target_mob.damage_this_turn -= amount
        target_mob.damage_this_turn = max(target_mob.damage_this_turn, 0)
        return [f"{effect_owner.username} heals {e.amount} on {target_mob.name}."]

    def do_kill_effect(self, e, effect_owner, target_mob, controller):
        if e.target_type == "mob" or e.target_type == "artifact" or e.target_type == "mob_or_artifact":
            if target_mob:
                log_lines = [f"{self.name} kills {target_mob.name}."]
                self.do_kill_effect_on_mob(target_mob, controller)
                return log_lines
        else:
            cards_to_kill = []
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
            for player in [effect_owner, effect_owner.game.opponent()]:
                for card in player.in_play+player.artifacts:
                    if card.cost >= min_cost and card.cost <= max_cost and (instruments_ok or not card.has_ability("Instrument")):
                        cards_to_kill.append((card, player))
            for card_tuple in cards_to_kill: 
                self.do_kill_effect_on_mob(card_tuple[0], card_tuple[1])
            if len(card_ids_to_kill) > 0:
                return [f"{effect_owner.username} kills stuff ({len(card_ids_to_kill)})."]

    def do_kill_effect_on_mob(self, target_mob, controller):
        controller.send_card_to_played_pile(target_mob, did_kill=True)

    def do_mob_to_artifact_effect(self, effect_owner, target_mob, controller):
        controller.send_card_to_played_pile(target_mob, did_kill=False)
        controller.played_pile.pop()
        if len(controller.artifacts) < 3:
            target_card.card_type = "artifact"
            controller.artifacts.append(target_mob)
        effect_owner.game.update_for_mob_changes_zones(effect_owner.game.players[0])
        effect_owner.game.update_for_mob_changes_zones(effect_owner.game.players[1])
        return [f"{effect_owner.username} turns {target_mob.name} into an artifact."]

    def do_make_effect(self, target_player, make_type, reduce_cost=0, option=False):
        return self.make(1, make_type, target_player, reduce_cost=reduce_cost, option=option)

    def do_make_from_deck_effect(self, target_player):
        return self.make_from_deck(target_player)

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
        if player.game.turn <= 10 and make_type == Card.mobCardType:
            requiredMobCost = math.floor(player.game.turn / 2) + 1

        all_game_cards = Card.all_card_objects(require_images=True, include_tokens=False)
        banned_cards = ["Make Spell", "Make Spell+", "Make Mob", "Make Mob+"]
        card1 = None 
        while not card1 or card1.name in banned_cards or (make_type != "any" and card1.card_type != make_type) or (requiredMobCost and make_type == Card.mobCardType and card1.cost != requiredMobCost): 
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
        if make_type == Card.artifactCardType:
            for c in player.card_choice_info["cards"]:
                c.cost = min(3, c.cost)
        
        for c in player.card_choice_info["cards"]:
            c.cost = max(0, c.cost-reduce_cost)
    
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

    def do_mana_effect_on_player(self, target_player, amount):
        target_player.mana += amount
        return [f"{target_player.username} gets {amount} mana."]

    def do_make_token_effect(self, player, e, card_for_level):
        for x in range(0, e.amount):
            if len(player.in_play) == 7:
                return
            card_to_create = None
            card_name = e.card_name
            if len(e.card_names) > 0:
                card_name = e.card_names[card_for_level.level]
            for card in Card.all_card_objects():
                if card.name == card_name:
                    card_to_create = card
            new_card = copy.deepcopy(card_to_create)
            player.in_play.append(new_card)
            player.game.update_for_mob_changes_zones(player)
            new_card.id = player.game.next_card_id
            new_card.turn_played = player.game.turn
            new_card.owner_username = player.username
            player.game.next_card_id += 1
        
        if e.target_type == "self":
            return [f"{self.name} makes {e.amount} tokens."]
        else:
            return [f"{self.name} makes {e.amount} tokens for {player.game.opponent().username}."]

    def do_mana_increase_max_effect_on_player(self, target_player, amount):
        old_max_mana = target_player.max_mana
        target_player.max_mana += 1
        target_player.max_mana = min(target_player.max_max_mana(), target_player.max_mana)
        # in case something like Mana Shrub doesn't increase the mana
        if old_max_mana == target_player.max_mana:
            if len(self.effects) == 2 and self.effects[1].name == "decrease_max_mana":
                self.effects[1].enabled = False
        return [f"{target_player.username} increases max mana by {amount}."]

    def do_mana_set_max_effect(self, game, amount):
        for p in game.players:
            p.max_mana = amount
            p.max_mana = min(p.max_max_mana(), p.max_mana)
            p.mana = min(p.mana, p.max_mana)
        return [f"{player.username} draws {e.amount} from {self.name}."]

    def do_mana_reduce_effect_on_player(self, target_player, amount):
        target_player.max_mana -= max(amount, 0)
        target_player.mana = min(target_player.mana, target_player.max_mana)
        return [f"{target_player.username} decreases max mana by {e.amount}."]

    def do_pump_power_effect_on_mob(self, target_mob, amount):
        target_mob.power += amount
        return [f"{effect_owner.username} pumps the power of {target_mob.name} by {e.amount}."]

    def do_redirect_mob_spell_effect(self, card_id, effect_owner):
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
        villager_card.do_make_token_effect(effect_owner, CardEffect({"amount":1, "card_name": token_card_name, "card_names":[]}, 0))

        # the card was countered by a different counterspell
        if not stack_spell:
            return None

        stack_spell[0]["effect_targets"][0]["id"] = effect_owner.game.next_card_id - 1
        return[f"{stack_spell[1]['name']} was redirected to a newly summoned {token_card_name}."]

    def do_riffle_effect(self, player, amount):
        top_cards = []
        for card in player.deck:
            if len(top_cards) < amount:
                top_cards.append(card)
        player.card_choice_info = {"cards": top_cards, "choice_type": "riffle"}
        return [f"{player.username} riffles for {amount}."]

    def do_set_can_attack_effect(self, target_type, player):
        if e.target_type == "self_mobs":
            for e in player.in_play:
                e.attacked = False
            return [f"{player.username} lets their mobs attack again this turn."]          
        else:
            print(f"e.target_type {target_type} not supported for set_can_attack")

    def do_store_card_for_next_turn_effect(self, player, target_card_id):
        for c in player.hand:
            if c.id == target_card_id:
                self.card_for_effect = c
                player.hand.remove(c)
                break

    def do_summon_from_deck_effect_on_player(self, effect_owner, target_player, e, effect_targets, target_index):
        if e.target_type == "self" and e.amount == 1:
            mobs = []
            for c in target_player.deck:
                if c.card_type == Card.mobCardType:
                    mobs.append(c)

            if len(mobs) > 0:
                mob_to_summon = random.choice(mobs)
                target_player.deck.remove(mob_to_summon)
                target_player.in_play.append(mob_to_summon)
                target_player.game.update_for_mob_changes_zones(target_player)
                mob_to_summon.turn_played = target_player.game.turn   
                if target_player.fast_ability():
                    mob_to_summon.abilities.append(target_player.fast_ability())          
                # todo: maybe support comes into play effects
                # target_player.target_or_do_mob_effects(mob_to_summon, {}, target_player.username)     
        elif e.target_type == "all_players" and e.amount == -1:
            mobs = []
            for c in Card.all_card_objects():
                if c.card_type == Card.mobCardType:
                    mobs.append(c)
            for p in effect_owner.game.players:
                while len(p.in_play) < 7:
                    mob_to_summon = copy.deepcopy(random.choice(mobs))
                    mob_to_summon.id = self.game.next_card_id
                    effect_owner.game.next_card_id += 1
                    p.in_play.append(mob_to_summon)
                    effect_owner.game.update_for_mob_changes_zones(p)
                    mob_to_summon.turn_played = effect_owner.game.turn     
                    if p.fast_ability():
                        mob_to_summon.abilities.append(p.fast_ability())                            
                    # todo: maybe support comes into play effects
                    # p.target_or_do_mob_effects(mob_to_summon, {}, p.username)     
        if e.target_type == "self":
            return [f"{effect_owner.username} summons something from their deck."]
        else:
            return [f"Both players fill their boards."]

    def do_summon_from_deck_artifact_effect_on_player(self, effect_owner, e):
        if e.target_type == "self" and e.amount == 1:
            artifacts = []
            for c in target_player.deck:
                if c.card_type == Card.artifactCardType:
                    artifacts.append(c)

            if len(artifacts) > 0:
                artifact_to_summon = random.choice(artifacts)
                target_player.deck.remove(artifact_to_summon)
                target_player.play_artifact(artifact_to_summon)
                target_player.game.update_for_mob_changes_zones(target_player)
                # todo: maybe support comes into play effects for artifacts?

            return [f"{effect_owner.username} summons something from their deck."]
        
        print(f"unsupported target_type {e.target_type} for summon_from_deck_artifact effect for {self.name}")

    def do_summon_from_hand_effect(self, effect_owner, target_player):
        nonspells = []
        for card in target_player.hand:
            if card.card_type != Card.spellCardType:
                nonspells.append(card)
        if len(nonspells) > 0:
            to_summon = random.choice(nonspells)
            target_player.hand.remove(to_summon)
            message = target_player.play_mob_or_artifact(to_summon, {"log_lines":[]}, do_effects=False)
            message["log_lines"].append(f"{to_summon.name} was summoned for {effect_owner.username}.")
            return message["log_lines"]

    def do_switch_hit_points_effect(self, effect_owner):
        cp_hp = effect_owner.hit_points
        effect_owner.hit_points = effect_owner.game.opponent().hit_points
        effect_owner.game.opponent().hit_points = cp_hp
        return [f"{effect_owner.username} uses {self.name} to switch hit points with {effect_owner.game.opponent().username}."]

    def do_take_control_effect(self, e, effect_owner, target_mob):
        opponent = effect_owner.game.opponent()
        if e.target_type == "all":
            while len(opponent.in_play) > 0 and len(effect_owner.in_play) < 7:
                if len(e.abilities) and e.abilities[0].descriptive_id == "Fast":
                    opponent.in_play[0].abilities.append(copy.deepcopy(e.abilities[0]))
                self.do_take_control_effect_on_mob(effect_owner, opponent.in_play[0], opponent)
            while len(opponent.artifacts) > 0 and len(effect_owner.artifacts) < 3:
                if len(e.abilities) and e.abilities[0].descriptive_id == "Fast":
                    opponent.artifacts[0].effects_exhausted = {}
                self.do_take_control_effect_on_artifact(effect_owner, opponent.artifacts[0], opponent)
            log_lines = [f"{effect_owner.username} takes control everything."]
        else:
            log_lines = [f"{effect_owner.username} takes control of {target_mob.name}."]
            self.do_take_control_effect_on_mob(effect_owner, target_mob, opponent)
        return log_lines

    def do_take_control_effect_on_mob(self, effect_owner, target_mob, controller):
        controller.in_play.remove(target_mob)
        effect_owner.in_play.append(target_card)
        effect_owner.game.update_for_mob_changes_zones(controller)
        effect_owner.game.update_for_mob_changes_zones(effect_owner)
        target_mob.turn_played = effect_owner.game.turn
        if effect_owner.fast_ability():
            target_mob.abilities.append(effect_owner.fast_ability())       
        if target_mob.has_ability("Fast") or target_mob.has_ability("Ambush"):
            target_mob.attacked = False
        target_mob.do_leaves_play_effects(controller, did_kill=False)

    def do_take_control_effect_on_artifact(self, effect_owner, target_artifact, controller):
        controller.artifacts.remove(target_artifact)
        effect_owner.artifacts.append(target_artifact)
        effect_owner.game.update_for_mob_changes_zones(controller)
        effect_owner.game.update_for_mob_changes_zones(effect_owner)
        target_artifact.turn_played = effect_owner.game.turn
        target_artifact.do_leaves_play_effects(controller, did_kill=False)
    
    def do_take_extra_turn_effect_on_player(self, target_player, message):
        target_player.game.remove_temporary_tokens()
        target_player.game.remove_temporary_effects()
        target_player.game.remove_temporary_abilities()
        target_player.game.clear_damage_this_turn()
        target_player.game.turn += 2
        log_lines = [f"{target_player.username} takes an extra turn."]
        message = target_player.start_turn(message)
        log_lines += message["log_lines"]
        return log_lines

    def do_unequip_from_mob_effect(self, effect_owner):
        equipped_mob = None
        for mob in effect_owner.in_play:
            for token in mob.tokens:
                if token.id == self.id:
                    equipped_mob = mob

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
        for idx, r in enumerate(artifact_controller.artifacts):
            if r.id == self.id:
                idx_to_replace = idx

        old_turn_played = self.turn_played
        new_card = Card.factory_reset_card(self, artifact_controller)
        new_card.turn_played = old_turn_played
        artifact_controller.artifacts[idx_to_replace] = new_card

    def do_unwind_effect(self, e, effect_owner, target_mob, controller):
        if e.target_type == "all_mobs":
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
            self.do_unwind_effect_on_mob(target_mob, controller)
            return [f"{self.name} returns {target_mob.name} to {target_mob.owner_username}'s hand."]

    def do_unwind_effect_on_mob(self, target_mob, controller):
        controller.in_play.remove(target_mob)  
        target_mob.do_leaves_play_effects(controller, did_kill=False)
        controller.game.remove_attack_for_mob(target_mob)
        new_card = Card.factory_reset_card(target_mob, controller)
        player = controller.game.players[0]
        if new_card.owner_username != player.username:
            player = controller.game.players[1]
        player.hand.append(new_card)  

    def do_effect_start_turn(self, player, effect):
        if effect.name == "damage" and effect.target_type == "self":
            player.damage(effect.amount)
            effect.show_effect_animation = True
            message["log_lines"].append(f"{player.username} takes {effect.amount} damage from {self.name}.")
        elif effect.name == "take_control" and effect.target_type == "opponents_mob_random": # song dragon
            if len(player.game.opponent().in_play) > 0:
                mob_to_target = random.choice(player.game.opponent().in_play)
                self.do_take_control_effect_on_mob(player, mob_to_target, player.game.opponent())
                effect.show_effect_animation = True
                message["log_lines"].append(f"{player.username} takes control of {mob_to_target.name}.")
        elif effect.name == "gain_hp":
            # cards like bright child vamp
            effect.show_effect_animation = True
            return self.do_heal_effect_on_player(player, effect.amount)
        else:
            print(f"unsupported start_turn triggered effect {effect}")

    def do_effect_artifact_only_start_turn(self, player):
        log_lines = []
        for effect in self.effects_triggered():
            if effect.trigger == "start_turn":
                # cards like Mana Battery
                effect.show_effect_animation = True
                if effect.name == "gain_hp_for_hand":
                    gained = 0
                    to_apply = max(len(player.hand) - 5, 0)
                    while player.hit_points < 30 and to_apply > 0:
                        player.hit_points += 1
                        to_apply -= 1
                        gained += 1  
                    log_lines.append(f"{player.username} gains {gained} hit points from {self.name}.")
                elif effect.name == "lose_hp_for_hand":
                    player.game.opponent().damage(len(player.game.opponent().hand))
                    log_lines.append(f"{player.game.opponent().username} takes {len(player.game.opponent().hand)} damage from {self.name}.")
                elif effect.name == "store_mana" and player.mana > 0:
                        counters = effect.counters or 0
                        counters += player.mana
                        effect.counters = min(3, counters)
            elif effect.name == "duplicate_card_next_turn" and self.card_for_effect:
                new_card = player.add_to_deck(self.card_for_effect.name, 1, add_to_hand=True)
                player.hand.append(self.card_for_effect)
                new_card.cost = self.card_for_effect.cost
                self.card_for_effect = None
            elif effect.name == "upgrade_card_next_turn" and self.card_for_effect:
                previous_card = None
                for c in Card.all_card_objects():
                    if self.card_for_effect.name == c.name:
                        previous_card = c
                previous_card.evolve(previous_card)
                player.hand.append(previous_card)
                self.card_for_effect = None
            elif effect.name == "decost_card_next_turn" and self.card_for_effect:                    
                self.card_for_effect.cost = max(0, self.card_for_effect.cost - 1)
                player.hand.append(self.card_for_effect)
                self.card_for_effect = None
            else:
                print(f"unsupported start_turn triggered effect for artifact, {effect}")
        return log_lines

    def enabled_activated_effects(self):
        enabled_effects = []
        for e in self.effects_activated():
            if e.enabled:
               enabled_effects.append(e)
        return enabled_effects

    def needs_activated_effect_targets(self):
        for e in self.enabled_activated_effects():
            if e.target_type in ["any", "any_enemy", "mob", "opponents_mob", "self_mob", "artifact", "any_player", "mob_or_artifact"]:
                return True
        return False 

    def needs_targets_for_spell(self):
        if len(self.effects_spell()) == 0:
            return False
        e = self.effects[0]
        if e.target_type in ["any", "any_enemy", "mob", "opponents_mob", "self_mob", "artifact", "any_player", "being_cast", "being_cast_artifact", "being_cast_spell", "being_cast_mob", "mob_or_artifact"]:
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
            if e.target_type == "being_cast_mob" and card.card_type == Card.mobCardType:
                return True
            if e.target_type == "being_cast_spell" and card.card_type == Card.spellCardType:
                if len(e.target_restrictions) > 0 and list(e.target_restrictions[0].keys())[0] == "target" and list(e.target_restrictions[0].values())[0] == "mob":
                    action = spell[0]
                    if "effect_targets" in action and action["effect_targets"][0]["target_type"] == Card.mobCardType:
                        return True
                else:
                    return True
            if e.target_type == "being_cast_artifact" and card.card_type == Card.artifactCardType:
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
        return not self.has_targets_for_attack_effect(game, self.effects[0])

    def has_targets_for_attack_effect(self, game, effect):
        # todo artifacts might eventually need evade guard
        guard_mobs_without_lurker = []
        clickable_ids = []
        for card in game.opponent().in_play:
            if card.has_ability("Guard") and not card.has_ability("Lurker"):
                guard_mobs_without_lurker.append(card)
        if len(guard_mobs_without_lurker) == 0:
            for card in game.opponent().in_play:
                if not card.has_ability("Lurker"):
                     clickable_ids.append(card.id)
            # todo this assumes card ids never clash with usernames
            clickable_ids.append(game.opponent().username)
        else:
            for card in guard_mobs_without_lurker:
                clickable_ids.append(card.id)

        for info in effect.targetted_this_turn:
            if info["target_type"] == "player" and info["id"] in clickable_ids:
                clickable_ids.remove(info["id"])
            else:
                card, _ = game.get_in_play_for_id(info["id"])
                if card and card.id in clickable_ids:
                    clickable_ids.remove(card.id)
        return len(clickable_ids) > 0

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
                        r.do_unequip_from_mob_effect(player)

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
                        r.do_unequip_from_mob_effect(player)

        for e in self.effects_leave_play():
            if e.name == "decrease_max_mana" and e.enabled:
                player.max_mana -= e.amount
                player.mana = min(player.max_mana, player.mana)
            if e.name == "damage" and e.target_type == "opponent":
                player.game.opponent().damage(e.amount)                                
            if e.name == "damage" and e.target_type == "self":
                player.damage(e.amount)                
            if e.name == "make_token" and did_kill:
                self.do_make_token_effect(player, e, self)
            if e.name == "remove_tokens":
                player.do_remove_tokens_effect(self, e)
            if e.name == "remove_player_abilities":
                player.remove_abilities(self, e)
            if e.name == "evolve" and did_kill:
                evolver_card = None
                previous_card = None
                for c in Card.all_card_objects():
                    if c.name == "Warty Evolver":
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

    def deal_damage(self, amount, target_player, game):
        if self.shielded:
            if damage_amount > 0:
                self.shielded = False
        else:
            self.damage += damage_amount
            self.damage_to_show += damage_amount
            if self.damage >= self.toughness_with_tokens():
                target_player.send_card_to_played_pile(self, did_kill=True)


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
        self.show_effect_animation = info["show_effect_animation"] if "show_effect_animation" in info else False
        self.targetted_this_turn = info["targetted_this_turn"] if "targetted_this_turn" in info else []
        self.target_restrictions = info["target_restrictions"] if "target_restrictions" in info else []
        self.target_type = info["target_type"] if "target_type" in info else None
        self.tokens = [CardToken(t) for t in info["tokens"]] if "tokens" in info else []
        self.toughness = info["toughness"] if "toughness" in info else None
        self.trigger = info["trigger"] if "trigger" in info else None
        self.turns = info["turns"] if "turns" in info else 0
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
            "show_effect_animation": self.show_effect_animation,
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
