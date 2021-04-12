from django.test import TestCase
from cofx.game_objects import CoFXGame
from cofx.jsonDB import JsonDB


class GameObjectTests(TestCase):
    def test_new_game(self):
        game_dict = JsonDB().game_database("testDB-1")
        game = CoFXGame("ingame", info=game_dict)        
        self.assertEqual(game.turn, 0)
