import datetime
import random
from battle_wizard.player import Player
from battle_wizard.card import Card


class PlayerAI(Player):

    def __init__(self, game, info, new=False):
        super().__init__(game, info, new)
        self.is_ai = True
        self.ai_running = False
        self.last_move_time = None

    def legal_moves_for_ai(self):
        """
            Returns a list of possible moves for an AI player.
        """
        if len(self.game.players) < 2:
            return [{"move_type": "JOIN", "username": self.username}]

        moves = []
        has_action_selected = self.selected_mob() or self.selected_artifact() or self.selected_spell()
        if self.card_info_to_target["effect_type"] in ["mob_activated", "mob_comes_into_play"]:
            moves = self.add_resolve_mob_effects_moves(moves)
        elif self.card_choice_info["choice_type"] in ["make", "make_with_option"]:
            moves = self.add_resolve_make_moves(moves)
            moves.append({"move_type": "CANCEL_MAKE", "username": self.username})              
        elif self.card_choice_info["choice_type"] == "make_from_deck":
            moves = self.add_resolve_make_from_deck_moves(moves)
        elif self.card_choice_info["choice_type"] == "fetch_artifact_into_hand":
            moves = self.add_resolve_fetch_card_moves(moves)
        elif self.card_choice_info["choice_type"] == "riffle":
            moves = self.add_resolve_riffle_moves(moves)
        elif self.card_choice_info["choice_type"] == "fetch_artifact_into_play":
            moves = self.add_resolve_fetch_artifact_into_play_moves(moves)
        elif self.card_choice_info["choice_type"] == "fetch_into_hand":
            moves = self.add_resolve_fetch_card_moves(moves)
        elif self.card_choice_info["choice_type"] == "fetch_into_hand_from_played_pile":
            moves = self.add_resolve_fetch_card_from_played_pile_moves(moves)
        elif len(self.game.stack) > 0 and not has_action_selected:
            moves = self.add_response_moves(moves)

        # can be zero here when there is a Make From Deck move with no targets in deck (at least)
        if len(moves) == 0:
            moves = self.add_attack_and_play_card_moves(moves)
            if not has_action_selected:
                moves.append({"move_type": "END_TURN", "username": self.username})
        return moves

    def add_response_moves(self, moves):
        moves = self.add_attack_and_play_card_moves(moves)
        moves.append({"move_type": "RESOLVE_NEXT_STACK", "username": self.username})              
        return moves 

    def add_effect_resolve_move(self, mob_to_target, effect_target, effect_type, moves):
        # todo handle cards with more than one effect that gets triggered at the same time
        moves.append({
                "card":mob_to_target.id, 
                "move_type": "RESOLVE_MOB_EFFECT", 
                "effect_index": 0, 
                "username": self.username,
                "effect_targets": [effect_target]})

        if len(mob_to_target.effects) == 2:
            if mob_to_target.effects[1].target_type == "mob" or mob_to_target.effects[1].target_type == "opponents_mob":
                # hack for animal trainer
                moves[-1]["effect_targets"].append({"id": effect_target["id"], "target_type":"mob"})            
            else:
                # hack for siz pop and stiff wind
                moves[-1]["effect_targets"].append({"id": self.username, "target_type":"player"})
        return moves

    def add_resolve_mob_effects_moves(self, moves):
        mob_to_target = self.selected_mob()
        effect_type = self.card_info_to_target["effect_type"]
        for card in self.game.opponent().in_play + self.in_play:
            if card.can_be_clicked and mob_to_target.id != card.id:
                effect_target = {"id": card.id, "target_type":"mob"}
                moves = self.add_effect_resolve_move(mob_to_target, effect_target, effect_type, moves)
        for p in self.game.players:
            if p.can_be_clicked:
                effect_target = {"id": p.username, "target_type":"player"}
                moves = self.add_effect_resolve_move(mob_to_target, effect_target, effect_type, moves)
        return moves 

    def add_resolve_make_moves(self, moves):
        move_type = "MAKE_CARD"
        if self.card_choice_info["cards"][0].card_type == "Effect":
            move_type = "MAKE_EFFECT"
        for x in range(0,3):
            moves.append({"card":self.card_choice_info["cards"][x].as_dict() , "move_type": move_type, "username": self.username})              
        return moves 

    def add_resolve_fetch_card_moves(self, moves):
        for c in self.card_choice_info["cards"]:
            moves.append({"card":c.id , "move_type": "FETCH_CARD", "username": self.username})              
        return moves 

    def add_resolve_fetch_card_from_played_pile_moves(self, moves):
        for c in self.card_choice_info["cards"]:
            moves.append({"card":c.id , "move_type": "FETCH_CARD_FROM_PLAYED_PILE", "username": self.username})              
        return moves 

    def add_resolve_make_from_deck_moves(self, moves):
        for c in self.card_choice_info["cards"]:
            moves.append({"card":c.id , "move_type": "FETCH_CARD", "username": self.username})              
        return moves 

    def add_resolve_riffle_moves(self, moves):
        for c in self.card_choice_info["cards"]:
            moves.append({"card":c.id, "move_type": "FINISH_RIFFLE", "username": self.username})              
        return moves 

    def add_resolve_fetch_artifact_into_play_moves(self, moves):
        for c in self.card_choice_info["cards"]:
            moves.append({"card":c.id , "move_type": "FETCH_CARD_INTO_PLAY", "username": self.username})              
        return moves 

    def add_attack_and_play_card_moves(self, moves):
        for spell in self.game.stack:
            card = Card(spell[1])
            if card.can_be_clicked:
                moves.append({"card":card.id, "move_type": "SELECT_STACK_SPELL", "username": self.username})
        for artifact in self.artifacts:
            if artifact.can_be_clicked:
                moves.append({"card":artifact.id, "move_type": "SELECT_ARTIFACT", "username": self.username, "effect_index": 0})
        for artifact in self.game.opponent().artifacts:
            if artifact.can_be_clicked:
                moves.append({"card":artifact.id, "move_type": "SELECT_ARTIFACT", "username": self.username, "effect_index": 0})
        for artifact in self.artifacts:
            for idx, e in enumerate(artifact.enabled_activated_effects()):                
                if len(artifact.effects_can_be_clicked) > idx and artifact.effects_can_be_clicked[idx]:
                    moves.append({"card":artifact.id , "move_type": "SELECT_ARTIFACT", "username": self.username, "effect_index": idx})
        for mob in self.in_play:
            if mob.can_be_clicked:
                moves.append({"card":mob.id , "move_type": "SELECT_MOB", "username": self.username})
            # todo: don't hardcode for Infernus
            if len(mob.effects_activated()) > 0 and \
                mob.effects_activated()[0].target_type == "this" and \
                mob.effects_activated()[0].cost <= self.current_mana():
                # todo maybe mobs will have multiple effects
                moves.append({"card":mob.id, "move_type": "ACTIVATE_MOB", "username": self.username, "effect_index": 0})
            elif len(mob.effects_activated()) > 0 and \
                mob.effects_activated()[0].cost <= self.current_mana():
                # todo maybe mobs will have multiple effects, only have Winding One right now
                moves.append({"card":mob.id, "move_type": "ACTIVATE_MOB", "username": self.username, "effect_index": 0})
        for mob in self.game.opponent().in_play:
            if mob.can_be_clicked:
                moves.append({"card":mob.id , "move_type": "SELECT_MOB", "username": self.username})
        for card in self.hand:
            if card.can_be_clicked:
                # todo: cleaner if/then for Duplication/Upgrade Chambers
                if self.card_info_to_target["effect_type"] == "artifact_activated":
                    moves.append({"card":card.id , "move_type": "SELECT_CARD_IN_HAND", "username": self.username})
                elif self.card_info_to_target["card_id"]:
                    moves.append({"card":card.id , "move_type": "PLAY_CARD_IN_HAND", "username": self.username})
                else:
                    moves.append({"card":card.id , "move_type": "SELECT_CARD_IN_HAND", "username": self.username})
        if self.can_be_clicked:
            moves.append({"move_type": "SELECT_SELF", "username": self.username})
        if self.game.opponent().can_be_clicked:
            moves.append({"move_type": "SELECT_OPPONENT", "username": self.username, "card": self.card_info_to_target["card_id"]})
        return moves

    def run_ai(self, moves, consumer):
        self.ai_running = True
        self.last_move_time = datetime.datetime.now()
        if self.username == "random_bot":
            chosen_move = random.choice(moves)
        elif self.username == "pass_bot":
            chosen_move = self.pass_move()
        elif self.username == "aggro_bot":
            chosen_move = self.aggro_bot_move(moves)
        else:
            print(f"Unknown AI bot: {self.username}")

        print("AI playing " + str(chosen_move))
        chosen_move["log_lines"] = []
        message = self.game.play_move(chosen_move, save=True)    
        consumer.send_game_message(self.game.as_dict(), message)
        self.ai_running = False

    def aggro_bot_move(self, moves):
        chosen_move = random.choice(moves)
        while len(moves) > 1 and chosen_move["move_type"] == "END_TURN":
            chosen_move = random.choice(moves) 

        good_moves = []
        for move in moves:
            if move["move_type"] == "SELECT_MOB":
                good_moves.insert(0, move)
        for move in moves:
            if move["move_type"] == "SELECT_CARD_IN_HAND":
                being_cast = self.game.current_player().in_hand_card(move["card"])
                if being_cast.card_type in ["mob", "artifact"]:                        
                    if len(being_cast.effects) > 0:
                        if "opponents_mob" in being_cast.effects[0].ai_target_types and self.game.opponent().has_mob_target():
                            good_moves.insert(0, move)
        for move in moves:
            if move["move_type"] == "PLAY_CARD":
                being_cast = self.game.current_player().in_hand_card(move["card"])
                target, _ = self.game.get_in_play_for_id(move["effect_targets"][0].id)
                if target in self.game.opponent().in_play: 
                    if len(being_cast.effects) > 0:
                        if "opponents_mob" in being_cast.effects[0].ai_target_types:
                            good_moves.insert(0, move)

                if target in self.game.current_player().in_play: 
                    if len(being_cast.effects) > 0:
                        if "self_mob" in being_cast.effects[0].ai_target_types:
                            good_moves.insert(0, move)
        for move in moves:
            if move["move_type"] == "RESOLVE_MOB_EFFECT":
                chosen_move = move
                coming_into_play, _ = self.game.get_in_play_for_id(move["card"])
                target, _ = self.game.get_in_play_for_id(move["effect_targets"][0]["id"])
                if target and target.id in [card.id for card in self.game.current_player().in_play]: 
                    pass
                elif target and target.id in [card.id for card in self.game.opponent().in_play]:
                    if len(coming_into_play.effects) > 0:
                        if "opponents_mob" in coming_into_play.effects[0].ai_target_types:
                            good_moves.insert(0, move)
        for move in moves:
            if move["move_type"] == "SELECT_OPPONENT":
                good_moves.insert(0, move)

        # don't let aggrobot select unfavorable spells to cast
        # instead, prefer to pass the turn
        if len(good_moves) > 0:
            chosen_move = good_moves[0]
        elif chosen_move["move_type"] == "SELECT_CARD_IN_HAND":
            being_cast = self.game.current_player().in_hand_card(chosen_move["card"])
            if len(being_cast.effects) > 0:
                if ("opponents_mob" in being_cast.effects[0].ai_target_types and not "opponent" in being_cast.effects[0].ai_target_types and not self.game.opponent().has_mob_target()) or \
                   ("self_mob" in being_cast.effects[0].ai_target_types and not self.game.current_player().has_mob_target()) or \
                   ("opponents_artifact" in being_cast.effects[0].ai_target_types and not self.game.opponent().has_artifact_target()):
                    chosen_move = self.pass_move()

        return chosen_move
            
    def pass_move(self):
        if len (self.game.stack) > 0:
            return {"move_type": "RESOLVE_NEXT_STACK", "username": self.username}                              
        else:
            return {"move_type": "END_TURN", "username": self.username}

    def maybe_run_ai(self, consumer):
        # run AI if it's the AI's move or if the other player just chose their discipline
        if (self.game.current_player() == self.game.players[1] or \
            (self.game.players[0].discipline != None and self.discipline == None)):                     
            time_for_next_move = False
            if not self.last_move_time or (datetime.datetime.now() - self.last_move_time).seconds >= 1:
                time_for_next_move = True
            self.game.set_clickables()
            moves = self.legal_moves_for_ai()
            if (time_for_next_move or len(moves) == 1) and not self.ai_running:
                if self.game.players[0].hit_points > 0 and self.hit_points > 0: 
                    print("running AI, choosing from moves: " + str(moves))
                    self.run_ai(moves, consumer)


