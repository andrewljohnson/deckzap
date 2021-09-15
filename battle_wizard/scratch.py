    self.effect_defs = [self.effect_def_for_id(effect.name) for effect in info["effects"]]

    def effect_def_for_id(name):
        if name == "add_effects":
            return self.do_add_effects_effect         
        elif name == "add_mob_abilities" or name == "add_player_abilities":
            return self.do_add_abilities_effect          
        elif name == "add_random_mob_ability":
            return self.do_add_random_ability_effect_on_mobs
        elif name == "add_tokens":
            return self.do_add_tokens_effect
        elif name == "attack":
            return self.do_attack_effect
        elif name == "buff_power_toughness_from_mana":
            return self.do_buff_power_toughness_from_mana_effect
        elif name == "create_card":
            return self.do_create_card_effect
        elif name == "create_random_townie":
            return self.do_create_random_townie_effect
        elif name == "create_random_townie_cheap":
            return self.do_create_random_townie_effect
        elif name == "discard_random":
            return self.do_discard_random_effect_on_player
        elif name == "damage":
            return self.do_damage_effect
        elif name in ["decost_card_next_turn", "duplicate_card_next_turn", "upgrade_card_next_turn"]:
            # todo no log lines returned
            return self.do_store_card_for_next_turn_effect
        elif name == "double_power":
            return self.do_double_power_effect_on_mob
        elif name == "draw":
            return self.do_draw_effect_on_player
        elif name == "draw_if_damaged_opponent":
            return self.do_draw_if_damaged_opponent_effect_on_player
        elif name == "draw_or_resurrect":
           return self.do_draw_or_resurrect_effect
        elif name == "enable_activated_effect":
            return self.do_enable_activated_effect_effect
        elif name == "entwine":
            return self.do_entwine_effect
        elif name == "equip_to_mob":
            return self.do_enable_equip_to_mob_effect
        elif name == "fetch_card":
            return self.do_fetch_card_effect_on_player
        elif name == "fetch_card_into_play":
            return self.do_fetch_card_effect_on_player
        elif name == "gain_for_toughness":
            return self.do_gain_for_toughness_effect
        elif name == "heal":
            return self.do_heal_effect
        elif name == "kill":
            return self.do_kill_effect
        elif name == "make":
            return self.do_make_effect
        elif name == "make_cheap_with_option":
            return self.do_make_effect
        elif name == "make_from_deck":
            return self.do_make_from_deck_effect
        elif name == "make_token":
            return self.do_make_token_effect
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
        elif name == "pump_power":
            return self.do_pump_power_effect_on_mob
        elif name == "redirect_mob_spell":
           return self.do_redirect_mob_spell_effect
        elif name == "riffle":
            return self.do_riffle_effect
        elif name == "set_can_attack":
            return self.do_set_can_attack_effect         
        elif name == "stack_counter":
           return  self.do_counter_card_effect
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
        elif name == "unequip_from_mob":
            return self.do_unequip_from_mob_effect

