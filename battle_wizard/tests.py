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
    
    def game_for_decks(self, player_decks):
        dbName = self.TEST_DB_NAME()
        game_dict = JsonDB().game_database(dbName)
        game = Game(None, "pvp", dbName, "test_stacked_deck", info=game_dict, player_decks=player_decks)
        game.play_move({"username": "a", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "JOIN", "log_lines":[]})
        return dbName, game

    def game_with_two_players(self):
        dbName = self.TEST_DB_NAME()
        game_dict = JsonDB().game_database(dbName)
        game = Game(None, "pvp", dbName, "ingame", info=game_dict)        
        game.play_move({"username": "a", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "JOIN", "log_lines":[]})
        return game

    def test_ten_card_hand_limit(self):
        """
            Test you can't draw more than 10 cards.
        """

        deck1 = ["Stone Elemental" for x in range(0,11)]
        deck2 = ["Stone Elemental" for x in range(0,11)]
        dbName, game = self.game_for_decks([deck1,deck2])
        for x in range(0,10):
            game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
            game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(len(game.current_player().hand), 10)
        os.remove(f"database/games/{dbName}.json")

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
        dbName, game = self.game_for_decks([["Stone Elemental"], []])
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        self.assertEqual(len(game.current_player().in_play), 1)
        os.remove(f"database/games/{dbName}.json")

    def test_play_summoning_sickness(self):
        dbName, game = self.game_for_decks([["Stone Elemental"], []])
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
        dbName, game = self.game_for_decks([["Stone Elemental", "Training Master"], []])
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 4)
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 26)
        os.remove(f"database/games/{dbName}.json")

    def test_unwind_mana_shrub(self):
        """
            Test return an entity to owner's hand with Unwind.

            Make sure Mana Shrub's effects trigger on leaving play.
        """
        dbName, game = self.game_for_decks([["Mana Shrub", "Unwind"], []])
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
        dbName, game = self.game_for_decks([["Stone Elemental", "Stiff Wind"], []])
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
        dbName, game = self.game_for_decks([["Siz Pop", "Siz Pop"], []])
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
        dbName, game = self.game_for_decks([["Counterspell"], ["LionKin"]])
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})        
        self.assertEqual(len(game.current_player().played_pile), 1)
        self.assertEqual(len(game.opponent().played_pile), 1)
        os.remove(f"database/games/{dbName}.json")

    def test_big_counterspell(self):
        """
            Tests Counterspell sends card to opponent's played_pile and Counterspell to current_player's played_pile.
        """
        dbName, game = self.game_for_decks([["Big Counterspell"], ["LionKin", "Mana Tree"]])
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})        
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 2, "log_lines":[]})        
        self.assertEqual(len(game.current_player().played_pile), 1)
        self.assertEqual(len(game.opponent().played_pile), 1)
        os.remove(f"database/games/{dbName}.json")

    def test_mind_manacles(self):
        """
            Tests Mind Manacles makes the entity switch sides.
        """
        dbName, game = self.game_for_decks([["Stone Elemental"], ["Mind Manacles"]])
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
        dbName, game = self.game_for_decks([["Stone Elemental"], ["Mind Manacles", "Master Time"]])
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
        dbName, game = self.game_for_decks([["Stone Elemental"], ["Stone Elemental"]])
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
        dbName, game = self.game_for_decks([["Gnomish Minstrel"], ["Air Elemental"]])
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
        dbName, game = self.game_for_decks([["Familiar"], ["Town Ranger"]])
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        self.assertEqual(len(game.legal_moves_for_ai(game.current_player())), 1)
        os.remove(f"database/games/{dbName}.json")

    def test_town_wizard_makes(self):
        """
            Test Town Wizard makes a card.
        """
        dbName, game = self.game_for_decks([["Town Wizard"], []])
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "MAKE_CARD", "card": game.current_player().card_choice_info["cards"][0].as_dict(), "log_lines":[]})
        self.assertEqual(len(game.current_player().hand), 1)
        os.remove(f"database/games/{dbName}.json")

    def test_town_shaman_makes(self):
        """
            Test Town Shaman makes a card.
        """
        dbName, game = self.game_for_decks([["Town Shaman"], []])
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "MAKE_CARD", "card": game.current_player().card_choice_info["cards"][0].as_dict(), "log_lines":[]})
        self.assertEqual(len(game.current_player().hand), 1)
        os.remove(f"database/games/{dbName}.json")

    def test_lute_transforms_and_makes(self):
        """
            Test Lute.
        """
        dbName, game = self.game_for_decks([["Lute"], []])
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
            Test Gnomish Mayor.
        """
        dbName, game = self.game_for_decks([["Gnomish Mayor"], []])
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        self.assertEqual(len(game.current_player().in_play), 2)
        os.remove(f"database/games/{dbName}.json")

    def test_gnomish_press_gang_makes(self):
        """
            Test Gnomish Press Gang.
        """
        dbName, game = self.game_for_decks([["Gnomish Press Gang"], []])
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        self.assertEqual(len(game.current_player().hand), 1)
        os.remove(f"database/games/{dbName}.json")


    def test_gnomish_soundsmith_makes(self):
        """
            Test Gnomish Soundsmith fetches an Instrument from deck.
        """
        deck = ["Gnomish Soundsmith", "LionKin", "LionKin", "LionKin", "Lute", "Lute"]
        deck.reverse()
        dbName, game = self.game_for_decks([deck, []])
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
        deck = ["Wish Stone", "LionKin", "LionKin", "LionKin", "Scepter of Manipulation"]
        deck.reverse()
        player_decks = [deck, []]
        dbName, game = self.game_for_decks(player_decks)
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 4, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_RELIC", "card": 4, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "FETCH_CARD_INTO_PLAY", "card": game.current_player().card_choice_info["cards"][0].id, "log_lines":[]})
        self.assertEqual(game.current_player().relics[-1].name, "Scepter of Manipulation")
        os.remove(f"database/games/{dbName}.json")

    def test_bewitching_lights(self):
        """
            Test Bewitching Lights makes a Relic from deck into in play.
        """
        dbName, game = self.game_for_decks([["Bewitching Lights"], ["LionKin"]])
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 28)
        self.assertEqual(len(game.opponent().hand), 0)
        self.assertEqual(len(game.opponent().played_pile), 1)
        os.remove(f"database/games/{dbName}.json")

    def test_befuddling_guitar_attack_player(self):
        """
            Test Befuddling Guitar.
        """
        dbName, game = self.game_for_decks([["Befuddling Guitar"], ["LionKin"]])
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_RELIC", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_OPPONENT", "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 27)
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_RELIC", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_OPPONENT", "log_lines":[]})
        self.assertEqual(len(game.current_player().relics), 0)
        os.remove(f"database/games/{dbName}.json")

    def test_befuddling_guitar_attack_entity(self):
        """
            Test Befuddling Guitar.
        """
        dbName, game = self.game_for_decks([["Befuddling Guitar"], ["LionKin"]])
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_RELIC", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 1, "log_lines":[]})
        self.assertEqual(game.current_player().hit_points, 27)
        self.assertEqual(game.opponent().deck[-1].name, "LionKin")
        os.remove(f"database/games/{dbName}.json")


    def test_town_council(self):
        """
            Test Town Council.
        """
        dbName, game = self.game_for_decks([["Town Council", "Mana Shrub", "Mana Shrub", "Mana Shrub"], []])
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 3, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 2, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        self.assertEqual(len(game.current_player().in_play), 4)
        os.remove(f"database/games/{dbName}.json")

    def test_taunted_bear_fade(self):
        """
            Test Taunted Bear Fade abilities.
        """
        dbName, game = self.game_for_decks([["Taunted Bear"], ["Totem Cat"]])
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 2)
        self.assertEqual(game.current_player().in_play[0].toughness_with_tokens(), 1)
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(len(game.current_player().in_play), 0)
        os.remove(f"database/games/{dbName}.json")

    def test_taunted_bear_fast_stomp(self):
        """
            Test Taunted Bear Fast and Stomp abilities.
        """
        dbName, game = self.game_for_decks([["War Scorpion"], ["Taunted Bear"]])
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_ENTITY", "card": 1, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 29)
        os.remove(f"database/games/{dbName}.json")

    def test_war_scorpion(self):
        """
            Test War Scorpion.
        """
        dbName, game = self.game_for_decks([["War Scorpion", "Taunted Bear"], []])
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        self.assertTrue(not game.current_player().in_play[0].has_ability("Fast"))
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        self.assertEqual(len(game.current_player().in_play), 2)
        self.assertTrue(game.current_player().in_play[0].has_ability("Fast"))
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        self.assertTrue(not game.current_player().in_play[0].has_ability("Fast"))
        os.remove(f"database/games/{dbName}.json")

    def test_berserk_monkey(self):
        """
            Test Berserk Monkey.
        """
        dbName, game = self.game_for_decks([["Berserk Monkey", "Berserk Monkey", "Berserk Monkey"], []])
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 2, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 2)
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 3)
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[1], game.current_player()), 2)
        os.remove(f"database/games/{dbName}.json")

    def test_frenzy_one_card(self):
        """
            Test Frenzy one card.
        """
        dbName, game = self.game_for_decks([["Frenzy", "Frenzy", "Frenzy", "Taunted Bear"], []])
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 3, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 2, "log_lines":[]})
        self.assertEqual(len(game.current_player().hand), 1)
        os.remove(f"database/games/{dbName}.json")

    def test_frenzy_two_cards(self):
        """
            Test Frenzy two cards.
        """
        dbName, game = self.game_for_decks([["Frenzy", "Frenzy", "Frenzy", "Taunted Bear"], []])
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 3, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 3, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 3, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 2, "log_lines":[]})
        self.assertEqual(len(game.current_player().hand), 2)
        os.remove(f"database/games/{dbName}.json")

    def test_impale(self):
        """
            Test Impale.
        """
        dbName, game = self.game_for_decks([["War Scorpion", "Impale"], []])
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 27)
        os.remove(f"database/games/{dbName}.json")

    def test_arsenal(self):
        """
            Test Arsenal and Kill Relic.
        """
        dbName, game = self.game_for_decks([["War Scorpion", "Arsenal", "Kill Relic"], []])
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 3)
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 2, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_RELIC", "card": 1, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 2)
        os.remove(f"database/games/{dbName}.json")


    def test_arsenal_manacles(self):
        """
            Test Arsenal and Mind Manacles.
        """
        dbName, game = self.game_for_decks([["War Scorpion", "Arsenal"], ["Mind Manacles"]])
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 3)
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 2, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 2)
        os.remove(f"database/games/{dbName}.json")

    def test_arsenal_equipped_manacles(self):
        """
            Test Arsenal equipped and Mind Manacles.
        """
        dbName, game = self.game_for_decks([["War Scorpion", "Arsenal"], ["Mind Manacles"]])
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_RELIC", "effect_index": 1, "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 5)
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 2, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 2)
        self.assertEqual(game.opponent().relics[0].enabled_activated_effects()[0].cost, 2)
        os.remove(f"database/games/{dbName}.json")

    def test_arsenal_two_relics(self):
        """
            Test Arsenal and Kill Relic.
        """
        dbName, game = self.game_for_decks([["War Scorpion", "Befuddling Guitar", "Arsenal", "War Scorpion"], ["Mind Manacles"]])
        print(game.as_dict())
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 3, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 2, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 3)
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 4)
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[1], game.current_player()), 4)
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 4, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_ENTITY", "card": 3, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 2)
        os.remove(f"database/games/{dbName}.json")

    def test_arsenal_2x(self):
        """
            Test Arsenal and Kill Relic.
        """
        dbName, game = self.game_for_decks([["War Scorpion", "Arsenal", "Arsenal"], []])
        print(game.as_dict())
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})

        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 2, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 6)
        os.remove(f"database/games/{dbName}.json")

    def test_arsenal_3x(self):
        """
            Test Arsenal and Kill Relic.
        """
        dbName, game = self.game_for_decks([["Mana Shrub", "Arsenal", "Arsenal", "Arsenal"], []])
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})

        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 2, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 3, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 9)
        os.remove(f"database/games/{dbName}.json")

    def test_arsenal_2x_reverse(self):
        """
            Test Arsenal and Kill Relic.
        """
        dbName, game = self.game_for_decks([["Arsenal", "Arsenal", "War Scorpion"], []])
        print(game.as_dict())
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})

        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 2, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 6)
        os.remove(f"database/games/{dbName}.json")

    def test_arsenal_2x_middle(self):
        """
            Test Arsenal and Kill Relic.
        """
        dbName, game = self.game_for_decks([["Arsenal", "Arsenal", "War Scorpion"], []])
        print(game.as_dict())
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})

        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 2, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 6)
        os.remove(f"database/games/{dbName}.json")



    def test_arsenal_attack_player(self):
        """
            Test Arsenal attacks a player as a weapon.
        """
        dbName, game = self.game_for_decks([["Arsenal"], []])
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_RELIC", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_RELIC", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_OPPONENT", "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 28)
        os.remove(f"database/games/{dbName}.json")

    def test_dragonslayer_elf_no_targets(self):
        """
            Test you can End Turn after playing DragonSlayer with no targets.
        """
        dbName, game = self.game_for_decks([["Dragonslayer Elf", "Stone Elemental"], ["Stone Elemental"]])
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 2, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(game.current_player().username, "b")
        os.remove(f"database/games/{dbName}.json")

    def test_guard_lurker(self):
        """
            Test you can attack past an entity with Guard+Lurker.
        """
        dbName, game = self.game_for_decks([["Stone Elemental", "Hide"], ["Air Elemental"]])
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 2, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 2, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 28)
        os.remove(f"database/games/{dbName}.json")

    def test_mana_storm(self):
        """
            Test Mana Storm.
        """

        deck1 = ["Mana Storm"]
        deck2 = []
        dbName, game = self.game_for_decks([deck1,deck2])
        for x in range(0,8):
            game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
            game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(game.current_player().max_mana, 10)
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})        
        self.assertEqual(game.current_player().max_mana, 0)
        os.remove(f"database/games/{dbName}.json")

    def test_riftwalker_djinn_syphon(self):
        """
            Test Syphon ability of Riftwalker Djinn
        """

        deck1 = ["Town Fighter"]
        deck2 = ["Riftwalker Djinn"]
        dbName, game = self.game_for_decks([deck1,deck2])
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})        
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})        
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})        
        self.assertEqual(game.opponent().hit_points, 28)
        for x in range(0,3):
            game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
            game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})        
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_ENTITY", "card": 1, "log_lines":[]})        
        game.play_move({"username": "b", "move_type": "SELECT_ENTITY", "card": 1, "log_lines":[]})        
        self.assertEqual(game.current_player().hit_points, 30)

        os.remove(f"database/games/{dbName}.json")

    def test_animal_trainer(self):
        """
            Test Animal Trainer pumps and Fades an entity.
        """
        dbName, game = self.game_for_decks([["Stone Elemental", "Animal Trainer"], []])
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 0, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 4)
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 3)
        os.remove(f"database/games/{dbName}.json")

    def test_multishot_bow(self):
        """
            Test Multishot Bow can attack multiple times, but not the same thing twice.
        """
        dbName, game = self.game_for_decks([["Multishot Bow"], ["Orc", "Orc"]])
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})        

        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})        
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 2, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_RELIC", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 1, "log_lines":[]})
        self.assertEqual(game.current_player().hit_points, 27)
        game.play_move({"username": "a", "move_type": "SELECT_RELIC", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 2, "log_lines":[]})
        self.assertEqual(game.current_player().hit_points, 24)
        game.play_move({"username": "a", "move_type": "SELECT_RELIC", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 1, "log_lines":[]})
        self.assertEqual(game.current_player().hit_points, 24)
        self.assertEqual(game.current_player().relics[0].effects[0].counters, 2)
        game.play_move({"username": "a", "move_type": "SELECT_OPPONENT", "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 27)
        self.assertEqual(game.current_player().relics[0].effects[0].counters, 1)
        game.play_move({"username": "a", "move_type": "SELECT_RELIC", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_OPPONENT", "log_lines":[]})
        self.assertEqual(len(game.current_player().relics), 1)
        self.assertEqual(game.opponent().hit_points, 27)
        os.remove(f"database/games/{dbName}.json")

    def test_multishot_guard(self):
        """
            Test Multishot Bow obeys Guard on entities
        """
        dbName, game = self.game_for_decks([["Multishot Bow"], ["Air Elemental", "Orc"]])
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})        
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 2, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_RELIC", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 2, "log_lines":[]})
        self.assertEqual(game.current_player().hit_points, 30)
        game.play_move({"username": "a", "move_type": "SELECT_OPPONENT", "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 30)
        game.play_move({"username": "a", "move_type": "SELECT_ENTITY", "card": 1, "log_lines":[]})
        self.assertEqual(game.current_player().hit_points, 29)
        os.remove(f"database/games/{dbName}.json")

    def test_enraged_stomper(self):
        """
            Test Enraged Stomper damages its controller.
        """
        dbName, game = self.game_for_decks([["Enraged Stomper"], []])
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})        
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})        
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})        
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(game.current_player().hit_points, 29)
        os.remove(f"database/games/{dbName}.json")

    def test_gird_for_battle(self):
        """
            Test Gird for Battle.
        """
        dbName, game = self.game_for_decks([["Arsenal", "Arsenal", "Arsenal", "Arsenal", "Arsenal", "Arsenal", "Arsenal", "Gird for Battle"], []])
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})        
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})        
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})        
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 7, "log_lines":[]})
        self.assertEqual(len(game.current_player().in_play), 1)
        self.assertEqual(len(game.current_player().relics), 1)
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 4)
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})        
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 3)
        os.remove(f"database/games/{dbName}.json")
