import datetime
import json
import copy 
import random
import time

from asgiref.sync import async_to_sync, sync_to_async
from channels.generic.websocket import WebsocketConsumer
from battle_wizard.game_objects import Game
from battle_wizard.jsonDB import JsonDB

DEBUG = True

class BattleWizardMatchFinderConsumer(WebsocketConsumer):

    def connect(self):
        print(f"Connected to Match Finder")
        self.room_group_name = 'match_finder'

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        queue_database = JsonDB().queue_database()
        queue_database["pvp"]["waiting_players"].remove(self.username)
        with open("database/queue_database.json", 'w') as outfile:
            json.dump(queue_database, outfile)
        print("Disconnected from Match Finder")
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        message = json.loads(text_data)
        print(message)

        self.username = message["username"]

        queue_database = JsonDB().queue_database()
        if not self.username in queue_database["pvp"]["waiting_players"]:
            queue_database["pvp"]["waiting_players"].append(self.username)

        if len(queue_database["pvp"]["waiting_players"]) == 2:
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'matchfinder_message',
                    'message': {"message_type": "start_match", "room_id": queue_database["pvp"]["starting_id"]}
                }
            )
            queue_database["pvp"]["starting_id"] += 1
            queue_database["pvp"]["waiting_players"] = []
        else:
            print("waiting for match")

        with open("database/queue_database.json", 'w') as outfile:
            json.dump(queue_database, outfile)

    def matchfinder_message(self, event):
        message = event['message']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'payload': message
        }))


class BattleWizardConsumer(WebsocketConsumer):

    def connect(self):
        self.player_type = self.scope['url_route']['kwargs']['player_type']
        self.ai = self.scope['url_route']['kwargs']['ai'] if 'ai' in self.scope['url_route']['kwargs'] else None
        self.room_name = self.scope['url_route']['kwargs']['room_code']
        self.room_group_name = 'room_%s' % self.room_name
        self.db_name = f"standard-{self.player_type}-{self.room_name}"
        self.moves = []
        self.ai_running = False
        self.last_move_time = None
        self.decks = [[], []]

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        print("Disconnected")
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        self.game = Game(self, self.player_type, self.db_name, info=JsonDB().game_database(self.db_name), ai=self.ai, player_decks=self.decks)        
        message = json.loads(text_data)

        if message["move_type"] == 'NEXT_ROOM':
            self.send_game_message(None, message)
            return

        message["log_lines"] = []
        message = self.game.play_move(message)    
        if message:
            self.send_game_message(self.game.as_dict(), message)

            if message["move_type"] == "GET_TIME":
                # run AI if it's the AI's move or if the other player just chose their discipline
                if self.player_type == "pvai" and (self.game.current_player() == self.game.players[1] or \
                    (self.game.players[0].discipline != None and self.game.players[1].discipline == None)):                     
                    time_for_next_move = False
                    if not self.last_move_time or (datetime.datetime.now() - self.last_move_time).seconds >= 1:
                        time_for_next_move = True
                    self.game.set_clickables()
                    moves = self.game.legal_moves_for_ai(self.game.players[1])
                    if (time_for_next_move or len(moves) == 1) and not self.ai_running:
                        if self.game.players[0].hit_points > 0 and self.game.players[1].hit_points > 0: 
                            # print(self.game.players[1].selected_mob().name if self.game.players[1].selected_mob() else None)
                            # print(self.game.players[1].selected_artifact().name if self.game.players[1].selected_artifact() else None)
                            # print(self.game.players[1].selected_spell().name if self.game.players[1].selected_spell() else None)
                            print("running AI, choosing from moves: " + str(moves))
                            self.run_ai(moves)

    def run_ai(self, moves):
        self.ai_running = True
        self.last_move_time = datetime.datetime.now()
        if self.ai == "random_bot":
            chosen_move = random.choice(moves)
        elif self.ai == "pass_bot":
            chosen_move = self.pass_move()
        elif self.ai == "aggro_bot":
            chosen_move = self.aggro_bot_move(moves)
        else:
            print(f"Unknown AI bot: {self.ai}")

        print("AI playing " + str(chosen_move))
        chosen_move["log_lines"] = []
        message = self.game.play_move(chosen_move)    
        self.send_game_message(self.game.as_dict(), message)
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
            return {"move_type": "RESOLVE_NEXT_STACK", "username": self.ai}                              
        else:
            return {"move_type": "END_TURN", "username": self.ai}

    def send_game_message(self, game_dict, message):
        # send current-game-related message to players
        if DEBUG and message and message["move_type"] != "GET_TIME":
            self.print_move(message)
        message["game"] = game_dict
        if message["move_type"] == "JOIN" and len(game_dict["players"]) == 1:
            message[ "all_cards"] = json.dumps(JsonDB().all_cards())

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'game_message',
                'message': message
            }
        )

    def print_move(self, message):
        move_copy = copy.deepcopy(message)
        if "game" in move_copy:
            del move_copy['game']
        if "log_lines" in move_copy:
            del move_copy['log_lines']
        if "show_spell" in move_copy:
            del move_copy['show_spell']
        if "defending_card" in move_copy:
            del move_copy['defending_card']

        self.moves.append(move_copy)
        print(f"send_game_message: {json.dumps(move_copy, indent=4)}")

    def game_message(self, event):
        '''
            Gets called once per recipient of a message.
        '''
        message = event['message']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'payload': message
        }))
