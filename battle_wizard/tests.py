from django.test import TestCase
from battle_wizard.game_objects import Game
from battle_wizard.jsonDB import JsonDB
import os
import time

"""
    6 tested cards out of about 50:

    Stone Elemental - vanilla entity
    Unwind and Mana Shrub - Test return an entity to owner's hand, make sure Mana Shrub's effects trigger on leaving play.
    Training Master - Test target's power doubles and can still attack.
    Stiff Wind - 2 Effects - Prevent attack and draw as 2nd effect.
    Siz Pop - 2 Effects - Prevent attack and draw as 2nd effect.
"""

class GameObjectTests(TestCase):

    def setUp(self):
        self.testDBName = "testDB"

    def tearDown(self):
        if os.path.exists(f"database/games/{self.TEST_DB_NAME()}.json"):
            os.remove(f"database/games/{self.TEST_DB_NAME()}.json")

    def TEST_DB_NAME(self):
        # self.testDBName += "|"
        return self.testDBName
    
    def game_with_two_players(self):
        dbName = self.TEST_DB_NAME()
        game_dict = JsonDB().game_database(dbName)
        game = Game(None, dbName, "ingame", info=game_dict)        
        game.play_move({"username": "a", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "JOIN", "log_lines":[]})
        return game

    def test_new_ingame_game(self):
        game = self.game_with_two_players()
        self.assertEqual(game.turn, 0)
        os.remove(f"database/games/{game.db_name}.json")

    def test_two_players_join_ingame_game(self):
        game = self.game_with_two_players()
        self.assertEqual(len(game.players), 2)
        self.assertEqual(len(game.players[0].hand), 2)
        self.assertEqual(len(game.players[1].hand), 2)
        os.remove(f"database/games/{game.db_name}.json")

    def test_illegal_opponent_start_turn(self):
        game = self.game_with_two_players()
        game.play_move({"username": "b", "move_type": "START_TURN", "log_lines":[]})
        self.assertEqual(len(game.opponent().hand), 2)
        os.remove(f"database/games/{game.db_name}.json")

    def test_play_stone_elemental(self):
        dbName = self.TEST_DB_NAME()
        game_dict = JsonDB().game_database(dbName)
        player_decks = [["Stone Elemental"], []]
        game = Game(None, dbName, "test_stacked_deck", info=game_dict, player_decks=player_decks)
        game.play_move({"username": "a", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        self.assertEqual(len(game.current_player().in_play), 1)
        os.remove(f"database/games/{dbName}.json")

    def test_play_summoning_sickness(self):
        dbName = self.TEST_DB_NAME()
        game_dict = JsonDB().game_database(dbName)
        player_decks = [["Stone Elemental"], []]
        game = Game(None, dbName, "test_stacked_deck", info=game_dict, player_decks=player_decks)
        game.play_move({"username": "a", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 30)
        os.remove(f"database/games/{dbName}.json")

    def test_play_training_master_and_attack_with_buffed_target(self):
        dbName = self.TEST_DB_NAME()
        game_dict = JsonDB().game_database(dbName)
        player_decks = [["Stone Elemental", "Training Master"], []]
        game = Game(None, dbName, "test_stacked_deck", info=game_dict, player_decks=player_decks)
        game.play_move({"username": "a", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        self.assertEqual(game.current_player().in_play[0].power_with_tokens(), 4)
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 26)
        os.remove(f"database/games/{dbName}.json")

    def test_unwind_mana_shrub(self):
        dbName = self.TEST_DB_NAME()
        game_dict = JsonDB().game_database(dbName)
        player_decks = [["Mana Shrub", "Unwind"], []]
        game = Game(None, dbName, "test_stacked_deck", info=game_dict, player_decks=player_decks)
        game.play_move({"username": "a", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        self.assertEqual(game.current_player().max_mana, 5)
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        self.assertEqual(game.current_player().max_mana, 4)
        os.remove(f"database/games/{dbName}.json")

    def test_play_stiff_wind(self):
        """
            Tests Stiff Wind prevents attack, and that it draws a card.
        """
        dbName = self.TEST_DB_NAME()
        game_dict = JsonDB().game_database(dbName)
        player_decks = [["Stone Elemental", "Stiff Wind"], []]
        game = Game(None, dbName, "test_stacked_deck", info=game_dict, player_decks=player_decks)
        game.play_move({"username": "a", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        self.assertEqual(len(game.current_player().hand), 1)
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        self.assertEqual(len(game.current_player().hand), 1)
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 30)
        os.remove(f"database/games/{dbName}.json")

    def test_play_siz_pop(self):
        """
            Tests Siz Pop deals a damage and draws a card.
        """
        dbName = self.TEST_DB_NAME()
        game_dict = JsonDB().game_database(dbName)
        player_decks = [["Siz Pop", "Siz Pop"], []]
        game = Game(None, dbName, "test_stacked_deck", info=game_dict, player_decks=player_decks)
        game.play_move({"username": "a", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_SELF", "card": 0, "log_lines":[]})
        self.assertEqual(len(game.current_player().hand), 2)
        self.assertEqual(game.current_player().hit_points, 29)
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_OPPONENT", "card": 0, "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 29)
        os.remove(f"database/games/{dbName}.json")
