from django.test import TestCase
from battle_wizard.game_objects import Game
from battle_wizard.jsonDB import JsonDB
import os
import time

"""
    10 tested cards out of about 50:

    Stone Elemental
    Unwind
    Mana Shrub
    Training Master
    Stiff Wind
    Siz Pop
    Counterspell
    Big Counterspell 
    Mind Manacles
    Master Time
"""

class GameObjectTests(TestCase):

    def setUp(self):
        self.testDBName = "testDB"

    def tearDown(self):
        if os.path.exists(f"database/games/{self.TEST_DB_NAME()}.json"):
            os.remove(f"database/games/{self.TEST_DB_NAME()}.json")

    def TEST_DB_NAME(self):
        return self.testDBName
    
    def game_with_two_players(self):
        dbName = self.TEST_DB_NAME()
        game_dict = JsonDB().game_database(dbName)
        game = Game(None, "pvp", dbName, "ingame", info=game_dict)        
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
        """
            Vanilla entity.
        """
        dbName = self.TEST_DB_NAME()
        game_dict = JsonDB().game_database(dbName)
        player_decks = [["Stone Elemental"], []]
        game = Game(None, "pvp", dbName, "test_stacked_deck", info=game_dict, player_decks=player_decks)
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
        game = Game(None, "pvp", dbName, "test_stacked_deck", info=game_dict, player_decks=player_decks)
        game.play_move({"username": "a", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 30)
        os.remove(f"database/games/{dbName}.json")

    def test_play_training_master_and_attack_with_buffed_target(self):
        """
            Test Training Master's target's power doubles and can still attack.
        """
        dbName = self.TEST_DB_NAME()
        game_dict = JsonDB().game_database(dbName)
        player_decks = [["Stone Elemental", "Training Master"], []]
        game = Game(None, "pvp", dbName, "test_stacked_deck", info=game_dict, player_decks=player_decks)
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
        """
            Test return an entity to owner's hand with Unwind.

            Make sure Mana Shrub's effects trigger on leaving play.
        """

        dbName = self.TEST_DB_NAME()
        game_dict = JsonDB().game_database(dbName)
        player_decks = [["Mana Shrub", "Unwind"], []]
        game = Game(None, "pvp", dbName, "test_stacked_deck", info=game_dict, player_decks=player_decks)
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

            2 effects card.
        """
        dbName = self.TEST_DB_NAME()
        game_dict = JsonDB().game_database(dbName)
        player_decks = [["Stone Elemental", "Stiff Wind"], []]
        game = Game(None, "pvp", dbName, "test_stacked_deck", info=game_dict, player_decks=player_decks)
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

            2 Effects card.
        """
        dbName = self.TEST_DB_NAME()
        game_dict = JsonDB().game_database(dbName)
        player_decks = [["Siz Pop", "Siz Pop"], []]
        game = Game(None, "pvp", dbName, "test_stacked_deck", info=game_dict, player_decks=player_decks)
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

    def test_counterspell(self):
        """
            Tests Counterspell sends card to opponent's played_pile and Counterspell to current_player's played_pile.
        """
        dbName = self.TEST_DB_NAME()
        game_dict = JsonDB().game_database(dbName)
        player_decks = [["Counterspell"], ["LionKin"]]
        game = Game(None, "pvp", dbName, "test_stacked_deck", info=game_dict, player_decks=player_decks)
        game.play_move({"username": "a", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})        
        self.assertEqual(len(game.current_player().played_pile), 1)
        self.assertEqual(len(game.opponent().played_pile), 1)
        os.remove(f"database/games/{dbName}.json")

    def test_big_counterspell(self):
        """
            Tests Counterspell sends card to opponent's played_pile and Counterspell to current_player's played_pile.
        """
        dbName = self.TEST_DB_NAME()
        game_dict = JsonDB().game_database(dbName)
        player_decks = [["Big Counterspell"], ["LionKin", "Mana Tree"]]
        game = Game(None, "pvp", dbName, "test_stacked_deck", info=game_dict, player_decks=player_decks)
        game.play_move({"username": "a", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})        
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 2, "log_lines":[]})        
        print(game.as_dict())
        self.assertEqual(len(game.current_player().played_pile), 1)
        self.assertEqual(len(game.opponent().played_pile), 1)
        os.remove(f"database/games/{dbName}.json")

    def test_mind_manacles(self):
        """
            Tests Mind Manacles makes the entity switch sides.
        """
        dbName = self.TEST_DB_NAME()
        game_dict = JsonDB().game_database(dbName)
        player_decks = [["Stone Elemental"], ["Mind Manacles"]]
        game = Game(None, "pvp", dbName, "test_stacked_deck", info=game_dict, player_decks=player_decks)
        game.play_move({"username": "a", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        for x in range(0, 4):
            game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
            game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(len(game.current_player().in_play), 0)
        self.assertEqual(len(game.opponent().in_play), 1)
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})        
        game.play_move({"username": "b", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        self.assertEqual(len(game.current_player().in_play), 1)
        self.assertEqual(len(game.opponent().in_play), 0)
        os.remove(f"database/games/{dbName}.json")

    def test_mind_manacles_gains_fast(self):
        """
            Tests Mind Manacles entity gains Fast if the player has it from casting Master Time
        """
        dbName = self.TEST_DB_NAME()
        game_dict = JsonDB().game_database(dbName)
        player_decks = [["Stone Elemental"], ["Mind Manacles", "Master Time"]]
        game = Game(None, "pvp", dbName, "test_stacked_deck", info=game_dict, player_decks=player_decks)
        game.play_move({"username": "a", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        for x in range(0, 8):
            game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
            game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})        
        game.play_move({"username": "b", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 2, "log_lines":[]})        
        self.assertEqual(game.opponent().hit_points, 30)
        game.play_move({"username": "b", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 28)
        os.remove(f"database/games/{dbName}.json")

    def test_removed_attacked_after_combat_death(self):
        """
            Tests if an entity that dies in combat gets the attacked flag reset properly.
        """
        dbName = self.TEST_DB_NAME()
        game_dict = JsonDB().game_database(dbName)
        player_decks = [["Stone Elemental"], ["Stone Elemental"]]
        game = Game(None, "pvp", dbName, "test_stacked_deck", info=game_dict, player_decks=player_decks)
        game.play_move({"username": "a", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 1, "log_lines":[]})
        self.assertEqual(game.current_player().played_pile[0].attacked, False)
        os.remove(f"database/games/{dbName}.json")

    def test_gnomish_minstrel_takes_control(self):
        """
            Test Gnomish Minstrel takes control of an entity it damages.
        """
        dbName = self.TEST_DB_NAME()
        game_dict = JsonDB().game_database(dbName)
        player_decks = [["Gnomish Minstrel"], ["Air Elemental"]]
        game = Game(None, "pvp", dbName, "test_stacked_deck", info=game_dict, player_decks=player_decks)
        game.play_move({"username": "a", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 1, "log_lines":[]})
        self.assertEqual(len(game.current_player().in_play), 1)
        self.assertEqual(len(game.opponent().in_play), 0)
        os.remove(f"database/games/{dbName}.json")


    def test_town_ranger_guards(self):
        """
            Test Guard works on Town Ranger by checking if there are only two legal moves (attack ranger and end turn).
        """
        dbName = self.TEST_DB_NAME()
        game_dict = JsonDB().game_database(dbName)
        player_decks = [["Familiar"], ["Town Ranger"]]
        game = Game(None, "pvp", dbName, "test_stacked_deck", info=game_dict, player_decks=player_decks)
        game.play_move({"username": "a", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        print(game.legal_moves_for_ai(game.current_player()))
        self.assertEqual(len(game.legal_moves_for_ai(game.current_player())), 1)
        os.remove(f"database/games/{dbName}.json")

    def test_town_wizard_makes(self):
        """
            Test Town Wizard makes a card.
        """
        dbName = self.TEST_DB_NAME()
        game_dict = JsonDB().game_database(dbName)
        player_decks = [["Town Wizard"], []]
        game = Game(None, "pvp", dbName, "test_stacked_deck", info=game_dict, player_decks=player_decks)
        game.play_move({"username": "a", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "MAKE_CARD", "card": game.current_player().card_choice_info["cards"][0].as_dict(), "log_lines":[]})
        self.assertEqual(len(game.current_player().hand), 1)
        os.remove(f"database/games/{dbName}.json")

    def test_town_shaman_makes(self):
        """
            Test Town Shaman makes a card.
        """
        dbName = self.TEST_DB_NAME()
        game_dict = JsonDB().game_database(dbName)
        player_decks = [["Town Shaman"], []]
        game = Game(None, "pvp", dbName, "test_stacked_deck", info=game_dict, player_decks=player_decks)
        game.play_move({"username": "a", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "MAKE_CARD", "card": game.current_player().card_choice_info["cards"][0].as_dict(), "log_lines":[]})
        self.assertEqual(len(game.current_player().hand), 1)
        os.remove(f"database/games/{dbName}.json")

    def test_lute_transforms_and_makes(self):
        """
            Test Town Shaman makes a card.
        """
        dbName = self.TEST_DB_NAME()
        game_dict = JsonDB().game_database(dbName)
        player_decks = [["Lute"], []]
        game = Game(None, "pvp", dbName, "test_stacked_deck", info=game_dict, player_decks=player_decks)
        game.play_move({"username": "a", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(game.current_player().mana, 3)
        game.play_move({"username": "a", "move_type": "SELECT_RELIC", "card": 0, "log_lines":[]})        
        self.assertEqual(game.current_player().mana, 1)
        game.play_move({"username": "a", "move_type": "SELECT_RELIC", "card": 0, "log_lines":[]})        
        self.assertEqual(len(game.current_player().hand), 1)
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_RELIC", "card": 0, "log_lines":[]})        
        self.assertEqual(len(game.current_player().hand), 2)
        game.play_move({"username": "a", "move_type": "SELECT_RELIC", "card": 0, "log_lines":[]})        
        self.assertEqual(game.current_player().relics[0].enabled_activated_effects()[0].counters, 2)
        os.remove(f"database/games/{dbName}.json")

    def test_gnomish_mayor_summons(self):
        """
            Test Town Shaman makes a card.
        """
        dbName = self.TEST_DB_NAME()
        game_dict = JsonDB().game_database(dbName)
        player_decks = [["Gnomish Mayor"], []]
        game = Game(None, "pvp", dbName, "test_stacked_deck", info=game_dict, player_decks=player_decks)
        game.play_move({"username": "a", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        self.assertEqual(len(game.current_player().in_play), 2)
        os.remove(f"database/games/{dbName}.json")

    def test_gnomish_press_gang_makes(self):
        """
            Test Town Shaman makes a card.
        """
        dbName = self.TEST_DB_NAME()
        game_dict = JsonDB().game_database(dbName)
        player_decks = [["Gnomish Press Gang"], []]
        game = Game(None, "pvp", dbName, "test_stacked_deck", info=game_dict, player_decks=player_decks)
        game.play_move({"username": "a", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        self.assertEqual(len(game.current_player().hand), 1)
        os.remove(f"database/games/{dbName}.json")


    def test_gnomish_soundsmith_makes(self):
        """
            Test Gnomish Soundsmith fetches an Instrument from deck.
        """
        dbName = self.TEST_DB_NAME()
        game_dict = JsonDB().game_database(dbName)
        deck = ["Gnomish Soundsmith", "LionKin", "LionKin", "LionKin", "Lute", "Lute"]
        deck.reverse()
        player_decks = [deck, []]
        game = Game(None, "pvp", dbName, "test_stacked_deck", info=game_dict, player_decks=player_decks)
        game.play_move({"username": "a", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 5, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "FETCH_CARD", "card": game.current_player().card_choice_info["cards"][0].id, "log_lines":[]})
        self.assertEqual(game.current_player().hand[-1].name, "Lute")
        os.remove(f"database/games/{dbName}.json")

    def test_wishstone_makes(self):
        """
            Test Wishstone makes a Relic from deck into in play.
        """
        dbName = self.TEST_DB_NAME()
        game_dict = JsonDB().game_database(dbName)
        deck = ["Wish Stone", "LionKin", "LionKin", "LionKin", "Scepter of Manipulation"]
        deck.reverse()
        player_decks = [deck, []]
        game = Game(None, "pvp", dbName, "test_stacked_deck", info=game_dict, player_decks=player_decks)
        game.play_move({"username": "a", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 4, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_RELIC", "card": 4, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "FETCH_CARD_INTO_PLAY", "card": game.current_player().card_choice_info["cards"][0].id, "log_lines":[]})
        self.assertEqual(game.current_player().relics[-1].name, "Scepter of Manipulation")
        os.remove(f"database/games/{dbName}.json")
