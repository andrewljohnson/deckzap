from django.test import TestCase
from cofx.game_objects import CoFXGame
from cofx.jsonDB import JsonDB
import os

TEST_DB_NAME = "testDB-1"

class GameObjectTests(TestCase):
    def test_new_ingame_game(self):
        game_dict = JsonDB().game_database(TEST_DB_NAME)
        game = CoFXGame("ingame", info=game_dict)        
        self.assertEqual(game.turn, 0)

    def game_with_two_players(self):
        game_dict = JsonDB().game_database(TEST_DB_NAME)
        game = CoFXGame("ingame", info=game_dict)        
        game.play_move("PLAY_MOVE", {"username": "a", "move_type": "JOIN"}, TEST_DB_NAME)
        game.play_move("PLAY_MOVE", {"username": "b", "move_type": "JOIN"}, TEST_DB_NAME)
        return game

    def test_two_players_join_ingame_game(self):
        game = self.game_with_two_players()
        self.assertEqual(len(game.players), 2)
        os.remove(f"database/games/{TEST_DB_NAME}.json")
        
    def test_start_turn(self):
        game = self.game_with_two_players()
        game.play_move("PLAY_MOVE", {"username": "b", "move_type": "START_TURN"}, TEST_DB_NAME)
        os.remove(f"database/games/{TEST_DB_NAME}.json")