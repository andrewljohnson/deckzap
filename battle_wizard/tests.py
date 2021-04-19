from django.test import TestCase
from battle_wizard.game_objects import Game
from battle_wizard.jsonDB import JsonDB
import os
import time

TEST_DB_NAME = "testDB"

class GameObjectTests(TestCase):

    def game_with_two_players(self):
        game_dict = JsonDB().game_database(TEST_DB_NAME)
        game = Game(None, TEST_DB_NAME, "ingame", info=game_dict)        
        game.play_move({"username": "a", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "JOIN", "log_lines":[]})
        return game

    def test_new_ingame_game(self):
        game = self.game_with_two_players()
        self.assertEqual(game.turn, 0)
        os.remove(f"database/games/{TEST_DB_NAME}.json")


    def test_two_players_join_ingame_game(self):
        game = self.game_with_two_players()
        self.assertEqual(len(game.players), 2)
        self.assertEqual(len(game.players[0].hand), 2)
        self.assertEqual(len(game.players[1].hand), 2)
        os.remove(f"database/games/{TEST_DB_NAME}.json")

    def test_illegal_opponent_start_turn(self):
        game = self.game_with_two_players()
        game.play_move({"username": "b", "move_type": "START_TURN", "log_lines":[]})
        self.assertEqual(len(game.opponent().hand), 2)
        os.remove(f"database/games/{TEST_DB_NAME}.json")

    def test_play_stone_elemental(self):
        game_dict = JsonDB().game_database(TEST_DB_NAME)
        player_decks = [["Stone Elemental"], []]
        game = Game(None, TEST_DB_NAME, "test_stacked_deck", info=game_dict, player_decks=player_decks)
        game.play_move({"username": "a", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "START_FIRST_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        self.assertEqual(len(game.current_player().in_play), 1)
        os.remove(f"database/games/{TEST_DB_NAME}.json")

    def test_play_summoning_sickness(self):
        game_dict = JsonDB().game_database(TEST_DB_NAME)
        player_decks = [["Stone Elemental"], []]
        game = Game(None, TEST_DB_NAME, "test_stacked_deck", info=game_dict, player_decks=player_decks)
        game.play_move({"username": "a", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "START_FIRST_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 30)
        os.remove(f"database/games/{TEST_DB_NAME}.json")

    def test_play_training_master_and_attack_with_buffed_target(self):
        game_dict = JsonDB().game_database(TEST_DB_NAME)
        player_decks = [["Stone Elemental", "Training Master"], []]
        game = Game(None, TEST_DB_NAME, "test_stacked_deck", info=game_dict, player_decks=player_decks)
        game.play_move({"username": "a", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "START_FIRST_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        self.assertEqual(game.current_player().in_play[0].power_with_tokens(), 4)
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 26)
        os.remove(f"database/games/{TEST_DB_NAME}.json")



