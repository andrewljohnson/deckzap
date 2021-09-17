from django.test import TestCase
from battle_wizard.game import Game
from battle_wizard.jsonDB import JsonDB
import os
import time


class GameObjectTests(TestCase):

    def setUp(self):

    def tearDown(self):
        pass

    def game_for_decks(self, player_decks):
        game_dict = {}
        game = Game("pvp", "test_stacked_deck", info=game_dict, player_decks=player_decks)
        game.play_move({"username": "a", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "JOIN", "log_lines":[]})
        return game

    def test_ten_card_hand_limit(self):
        """
            Test you can't draw more than 10 cards.
        """

        deck1 = ["Stone Elemental" for x in range(0,11)]
        deck2 = ["Stone Elemental" for x in range(0,11)]
        game = self.game_for_decks([deck1,deck2])
        for x in range(0,10):
            game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
            game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(len(game.current_player().hand), game.max_hand_size)

    def test_ten_mana_limit(self):
        """
            Test you can't have more than 10 mana
        """

        deck1 = []
        deck2 = []
        game = self.game_for_decks([deck1,deck2])
        for x in range(0,10):
            game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
            game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(game.current_player().max_mana, game.current_player().max_max_mana())

    def test_over_mana_mana_shrub(self):
        """
            Test you can't have more than 10 mana
        """

        deck1 = ["Mana Shrub", "Kill"]
        deck2 = []
        game = self.game_for_decks([deck1,deck2])
        for x in range(0,10):
            game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
            game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(game.current_player().max_mana, game.current_player().max_max_mana())
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        self.assertEqual(game.current_player().max_mana, game.current_player().max_max_mana())
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        self.assertEqual(game.current_player().max_mana, game.current_player().max_max_mana())

    def test_illegal_opponent_start_turn(self):
        game = self.game_for_decks([[], ["Zap","Zap","Zap","Zap","Zap"]])
        game.play_move({"username": "a", "move_type": "JOIN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "JOIN", "log_lines":[]})
        self.assertEqual(len(game.opponent().hand), 4)
        game.play_move({"username": "b", "move_type": "START_TURN", "log_lines":[]})
        self.assertEqual(len(game.opponent().hand), 4)

    def test_play_stone_elemental(self):
        """
            Vanilla mob.
        """
        game = self.game_for_decks([["Stone Elemental"], []])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        self.assertEqual(len(game.current_player().in_play), 1)

    def test_play_summoning_sickness(self):
        game = self.game_for_decks([["Stone Elemental"], []])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 30)

    def test_play_training_master_and_attack_with_buffed_target(self):
        """
            Test Training Master's target's power doubles and can still attack.
        """
        game = self.game_for_decks([["Stone Elemental", "Training Master"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 4)
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 26)

    def test_unwind_mana_shrub(self):
        """
            Test return a mob to owner's hand with Unwind.

            Make sure Mana Shrub's effects trigger on leaving play.
        """
        game = self.game_for_decks([["Mana Shrub", "Unwind"], []])
        turns_to_elapse = 2
        for x in range(0, turns_to_elapse):
            game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
            game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        self.assertEqual(game.current_player().max_mana, turns_to_elapse + 2)
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        self.assertEqual(game.current_player().max_mana, turns_to_elapse + 1)

    def test_play_stiff_wind(self):
        """
            Tests Stiff Wind prevents attack, and that it draws a card.

            2 effects card.
        """
        game = self.game_for_decks([["Stone Elemental", "Stiff Wind"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        self.assertEqual(len(game.current_player().hand), 1)
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 30)

    def test_play_siz_pop(self):
        """
            Tests Siz Pop deals a damage and draws a card.

            2 Effects card.
        """
        game = self.game_for_decks([["Siz Pop", "Siz Pop"], []])
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_SELF", "card": 0, "log_lines":[]})
        self.assertEqual(game.current_player().hit_points, 29)
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_OPPONENT", "card": 0, "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 29)

    def test_mind_manacles(self):
        """
            Tests Mind Manacles makes the mob switch sides.
        """
        game = self.game_for_decks([["Stone Elemental"], ["Mind Manacles"]])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        for x in range(0, 5):
            game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
            game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(len(game.current_player().in_play), 0)
        self.assertEqual(len(game.opponent().in_play), 1)
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})        
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        self.assertEqual(len(game.current_player().in_play), 1)
        self.assertEqual(len(game.opponent().in_play), 0)

    def test_mind_manacles_gains_fast(self):
        """
            Tests Mind Manacles mob gains Fast if the player has it from casting Master Time
        """
        game = self.game_for_decks([["Stone Elemental"], ["Mind Manacles", "Master Time"]])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        for x in range(0, 9):
            game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
            game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})        
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 2, "log_lines":[]})        
        self.assertEqual(game.opponent().hit_points, 30)
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 28)

    def test_removed_attacked_after_combat_death(self):
        """
            Tests if a mob that dies in combat gets the attacked flag reset properly.
        """
        game = self.game_for_decks([["Stone Elemental"], ["Stone Elemental"]])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 1, "log_lines":[]})
        self.assertEqual(game.current_player().played_pile[0].attacked, False)

    def test_gnomish_minstrel_takes_control(self):
        """
            Test Gnomish Minstrel takes control of a mob it damages.
        """
        game = self.game_for_decks([["Gnomish Minstrel"], ["Air Elemental"]])
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 1, "log_lines":[]})
        self.assertEqual(len(game.current_player().in_play), 1)
        self.assertEqual(len(game.opponent().in_play), 0)


    def test_town_ranger_guards(self):
        """
            Test Guard works on Town Ranger by checking if there are only two legal moves (attack ranger and end turn).
        """
        game = self.game_for_decks([["Familiar"], ["Town Ranger"]])
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        self.assertEqual(len(game.current_player().legal_moves_for_ai()), 1)

    def test_town_wizard_makes(self):
        """
            Test Town Wizard makes a card.
        """
        game = self.game_for_decks([["Town Wizard"], []])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "MAKE_CARD", "card": game.current_player().card_choice_info["cards"][0].as_dict(), "log_lines":[]})
        self.assertEqual(len(game.current_player().hand), 1)

    def test_town_shaman_makes(self):
        """
            Test Town Shaman makes a card.
        """
        game = self.game_for_decks([["Town Shaman"], []])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "MAKE_CARD", "card": game.current_player().card_choice_info["cards"][0].as_dict(), "log_lines":[]})
        self.assertEqual(len(game.current_player().hand), 1)

    def test_lute_transforms_and_makes(self):
        """
            Test Lute.
        """
        game = self.game_for_decks([["Lute"], []])
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(game.current_player().mana, 2)
        game.play_move({"username": "a", "move_type": "SELECT_ARTIFACT", "card": 0, "log_lines":[]})        
        self.assertEqual(game.current_player().mana, 1)
        game.play_move({"username": "a", "move_type": "SELECT_ARTIFACT", "card": 0, "log_lines":[]})        
        self.assertEqual(len(game.current_player().hand), 1)
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ARTIFACT", "card": 0, "log_lines":[]})        
        self.assertEqual(len(game.current_player().hand), 2)
        game.play_move({"username": "a", "move_type": "SELECT_ARTIFACT", "card": 0, "log_lines":[]})        
        self.assertEqual(game.current_player().artifacts[0].enabled_activated_effects()[0].counters, 2)

    def test_gnomish_mayor_summons(self):
        """
            Test Gnomish Mayor.
        """
        game = self.game_for_decks([["Gnomish Mayor"], []])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        self.assertEqual(len(game.current_player().in_play), 2)

    def test_gnomish_press_gang_makes(self):
        """
            Test Gnomish Press Gang.
        """
        game = self.game_for_decks([["Gnomish Press Gang"], []])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        self.assertEqual(len(game.current_player().hand), 1)


    def test_gnomish_soundsmith_makes(self):
        """
            Test Gnomish Soundsmith fetches an Instrument from deck.
        """
        deck = ["Gnomish Soundsmith", "LionKin", "LionKin", "LionKin", "LionKin", "Akbar's Pan Pipes"]
        game = self.game_for_decks([deck, []])
        game.players[0].mana = 3
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "FETCH_CARD", "card": game.current_player().card_choice_info["cards"][0].id, "log_lines":[]})
        self.assertEqual(game.current_player().hand[-1].name, "Akbar's Pan Pipes")

    def test_wishstone_makes(self):
        """
            Test Wishstone makes a Artifact from deck into in play.
        """
        deck = ["Wish Stone", "LionKin", "LionKin", "LionKin", "Scepter of Manipulation"]
        game = self.game_for_decks([deck, []])
        game.players[0].mana = 4
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ARTIFACT", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "FETCH_CARD_INTO_PLAY", "card": game.current_player().card_choice_info["cards"][0].id, "log_lines":[]})
        self.assertEqual(game.current_player().artifacts[-1].name, "Scepter of Manipulation")

    def test_bewitching_lights(self):
        """
            Test Bewitching Lights makes a Artifact from deck into in play.
        """
        game = self.game_for_decks([["Bewitching Lights"], ["LionKin"]])
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 28)
        self.assertEqual(len(game.opponent().hand), 0)
        self.assertEqual(len(game.opponent().played_pile), 1)

    def test_town_council(self):
        """
            Test Town Council.
        """
        game = self.game_for_decks([["Town Council", "Mana Shrub", "Mana Shrub", "Mana Shrub"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 3, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 2, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        self.assertEqual(len(game.current_player().in_play), 4)

    def test_taunted_bear_fade(self):
        """
            Test Taunted Bear Fade abilities.
        """
        game = self.game_for_decks([["Taunted Bear"], []])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 2)
        self.assertEqual(game.current_player().in_play[0].toughness_with_tokens(), 1)
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(len(game.current_player().in_play), 0)

    def test_taunted_bear_fast_stomp(self):
        """
            Test Taunted Bear Fast and Stomp abilities.
        """
        game = self.game_for_decks([["War Scorpion"], ["Taunted Bear"]])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 1, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 29)

    def test_war_scorpion(self):
        """
            Test War Scorpion.
        """
        game = self.game_for_decks([["War Scorpion", "Taunted Bear"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        self.assertTrue(not game.current_player().in_play[0].has_ability("Fast"))
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1, "log_lines":[]})
        self.assertEqual(len(game.current_player().in_play), 2)
        self.assertTrue(game.current_player().in_play[0].has_ability("Fast"))
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        self.assertTrue(not game.current_player().in_play[0].has_ability("Fast"))

    def test_berserk_monkey(self):
        """
            Test Berserk Monkey.
        """
        game = self.game_for_decks([["Berserk Monkey", "Berserk Monkey", "Berserk Monkey"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 2, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 1)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 2)
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[1], game.current_player()), 1)

    def test_frenzy_one_card(self):
        """
            Test Frenzy one card.
        """
        game = self.game_for_decks([["Frenzy", "Frenzy", "Frenzy", "Frenzy"], []])
        game.players[0].mana = 2
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        self.assertEqual(len(game.current_player().hand), 3)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1, "log_lines":[]})
        self.assertEqual(len(game.current_player().hand), 3)

    def test_frenzy_two_cards(self):
        """
            Test Frenzy two cards.
        """
        game = self.game_for_decks([["Taunted Bear", "Frenzy", "Frenzy", "Frenzy", "Frenzy", "Frenzy", "Frenzy", "Frenzy"], []])
        game.players[0].mana = 2
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        self.assertEqual(len(game.current_player().hand), 3)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 3, "log_lines":[]})
        self.assertEqual(len(game.current_player().hand), 4)

    def test_impale(self):
        """
            Test Impale.
        """
        game = self.game_for_decks([["War Scorpion", "Impale"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 27)



    def test_arsenal(self):
        """
            Test Arsenal and Kill Artifact.
        """
        game = self.game_for_decks([["War Scorpion", "Arsenal", "Kill Artifact"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 3)
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 2, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ARTIFACT", "card": 1, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 2)


    def test_arsenal_manacles(self):
        """
            Test Arsenal and Mind Manacles.
        """
        game = self.game_for_decks([["War Scorpion", "Arsenal"], ["Mind Manacles"]])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 3)
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        for card in game.players[1].hand:
            game.players[1].mana += card.cost
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 2, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 2)

    '''
    probably delete this card

    def test_arsenal_equipped_manacles(self):
        """
            Test Arsenal equipped and Mind Manacles.
        """
        game = self.game_for_decks([["War Scorpion", "Arsenal"], ["Mind Manacles"]])
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ARTIFACT", "effect_index": 1, "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 5)
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 2, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 2)
        self.assertEqual(game.opponent().artifacts[0].enabled_activated_effects()[0].cost, 2)
    '''

    def test_arsenal_two_artifacts(self):
        """
            Test Arsenal and Kill Artifact.
        """
        game = self.game_for_decks([["War Scorpion", "Akbar's Pan Pipes", "Arsenal", "War Scorpion"], ["Mind Manacles"]])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost    
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 3, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 2, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 3)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 4)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[1], game.current_player()), 4)
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.players[1].mana = game.players[1].hand[0].cost    
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 4, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 3, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 2)

    def test_arsenal_2x(self):
        """
            Test Arsenal and Kill Artifact.
        """
        game = self.game_for_decks([["War Scorpion", "Arsenal", "Arsenal"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 2, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 6)

    def test_arsenal_3x(self):
        """
            Test Arsenal and Kill Artifact.
        """
        game = self.game_for_decks([["Mana Shrub", "Arsenal", "Arsenal", "Arsenal"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost

        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 2, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 3, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 10)

    def test_arsenal_2x_reverse(self):
        """
            Test Arsenal and Kill Artifact.
        """
        game = self.game_for_decks([["Arsenal", "Arsenal", "War Scorpion"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost

        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 2, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 6)

    def test_arsenal_2x_middle(self):
        """
            Test Arsenal and Kill Artifact.
        """
        game = self.game_for_decks([["Arsenal", "Arsenal", "War Scorpion"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost

        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 2, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 6)


    '''
    probably delete this card

    def test_arsenal_attack_player(self):
        """
            Test Arsenal attacks a player as a weapon.
        """
        game = self.game_for_decks([["Arsenal"], []])
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ARTIFACT", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ARTIFACT", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_OPPONENT", "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 28)
    '''

    def test_dragonslayer_elf_no_targets(self):
        """
            Test you can End Turn after playing DragonSlayer with no targets.
        """
        game = self.game_for_decks([["Dragonslayer Elf", "Stone Elemental"], ["Stone Elemental"]])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 2, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(game.current_player().username, "b")

    def test_guard_lurker(self):
        """
            Test you can attack past a mob with Guard+Lurker.
        """
        game = self.game_for_decks([["Stone Elemental", "Hide"], ["Air Elemental"]])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.players[1].mana = game.players[1].hand[0].cost
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 2, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 2, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 28)

    def test_mana_storm(self):
        """
            Test Mana Storm.
        """

        deck1 = ["Mana Storm"]
        deck2 = []
        game = self.game_for_decks([deck1,deck2])
        for x in range(0,9):
            game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
            game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(game.current_player().max_mana, 10)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})        
        self.assertEqual(game.current_player().max_mana, 0)

    def test_riftwalker_djinn_syphon(self):
        """
            Test Syphon ability of Riftwalker Djinn
        """

        deck1 = ["Town Fighter"]
        deck2 = ["Riftwalker Djinn"]
        game = self.game_for_decks([deck1,deck2])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})        
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})        
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})        
        self.assertEqual(game.opponent().hit_points, 28)
        for x in range(0,4):
            game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
            game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 1, "log_lines":[]})        
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 1, "log_lines":[]})        
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 1, "log_lines":[]})        
        self.assertEqual(game.current_player().hit_points, 30)


    def test_animal_trainer(self):
        """
            Test Animal Trainer pumps and Fades a mob.
        """
        game = self.game_for_decks([["Stone Elemental", "Animal Trainer"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 4)
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 3)

    def test_multishot_bow(self):
        """
            Test Multishot Bow can attack multiple times, but not the same thing twice.
        """
        game = self.game_for_decks([["Multishot Bow"], ["Orc", "Orc"]])
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})        
        for card in game.players[1].hand:
            game.players[1].mana += card.cost
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 2, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ARTIFACT", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 1, "log_lines":[]})
        self.assertEqual(game.current_player().hit_points, 27)
        game.play_move({"username": "a", "move_type": "SELECT_ARTIFACT", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 2, "log_lines":[]})
        self.assertEqual(game.current_player().hit_points, 24)
        game.play_move({"username": "a", "move_type": "SELECT_ARTIFACT", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 1, "log_lines":[]})
        self.assertEqual(game.current_player().hit_points, 24)
        self.assertEqual(game.current_player().artifacts[0].effects[0].counters, 2)
        game.play_move({"username": "a", "move_type": "SELECT_OPPONENT", "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 27)
        self.assertEqual(game.current_player().artifacts[0].effects[0].counters, 1)
        game.play_move({"username": "a", "move_type": "SELECT_ARTIFACT", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_OPPONENT", "log_lines":[]})
        self.assertEqual(len(game.current_player().artifacts), 1)
        self.assertEqual(game.opponent().hit_points, 27)

    def test_multishot_guard(self):
        """
            Test Multishot Bow obeys Guard on mobs
        """
        game = self.game_for_decks([["Multishot Bow"], ["Air Elemental", "Orc"]])
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        for card in game.players[1].hand:
            game.players[1].mana += card.cost
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 2, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ARTIFACT", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 2, "log_lines":[]})
        self.assertEqual(game.current_player().hit_points, 30)
        game.play_move({"username": "a", "move_type": "SELECT_OPPONENT", "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 30)
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 1, "log_lines":[]})
        self.assertEqual(game.current_player().hit_points, 29)

    def test_enraged_stomper(self):
        """
            Test Enraged Stomper damages its controller.
        """
        game = self.game_for_decks([["Enraged Stomper"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})        
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(game.current_player().hit_points, 29)

    def test_gird_for_battle(self):
        """
            Test Gird for Battle.
        """
        game = self.game_for_decks([["Gird for Battle", "Arsenal", "Arsenal", "Arsenal", "Arsenal", "Arsenal", "Arsenal", "Arsenal"], []])
        game.players[0].mana = 5
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        self.assertEqual(len(game.current_player().in_play), 1)
        self.assertEqual(len(game.current_player().artifacts), 1)
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 4)
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})        
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 3)


    def test_spirit_of_the_stampede(self):
        """
            Spirit of the Stampede
        """
        game = self.game_for_decks([["Spirit of the Stampede", "Spirit of the Stampede", "Akbar's Pan Pipes"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 3)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 4)
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[1], game.current_player()), 4)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 2, "log_lines":[]})
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[0], game.current_player()), 5)
        self.assertEqual(game.power_with_tokens(game.current_player().in_play[1], game.current_player()), 5)


    def test_push_soul(self):
        """
            Test Push Soul.
        """

        deck1 = ["Stone Elemental", "Zap"]
        deck2 = ["Push Soul"]
        game = self.game_for_decks([deck1,deck2])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})        
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})        
        game.play_move({"username": "a", "move_type": "SELECT_SELF", "log_lines":[]})        
        game.play_move({"username": "b", "move_type": "RESOLVE_CARD", "card": 1, "log_lines":[]})        
        self.assertEqual(game.current_player().hit_points, 27)
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 2, "log_lines":[]})        
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})        
        self.assertEqual(game.opponent().hit_points, 29)
        self.assertEqual(len(game.opponent().in_play), 0)


    def test_riffle(self):
        """
            Test Riffle.
        """

        deck1 = ["Zap", "Zap", "Zap", "Riffle", "Riffle"]
        deck2 = []
        game = self.game_for_decks([deck1,deck2])
        self.assertEqual(len(game.current_player().hand), 2)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 4, "log_lines":[]})        
        game.play_move({"username": "a", "move_type": "FINISH_RIFFLE", "card": game.current_player().card_choice_info["cards"][0].id, "log_lines":[]})
        self.assertEqual(len(game.current_player().hand), 2)
        self.assertEqual(len(game.current_player().played_pile), 3)

    def test_disk_of_death(self):
        """
            Test Disk of Death.
        """

        deck1 = ["Stone Elemental", "Lute"]
        deck2 = ["Disk of Death"]
        game = self.game_for_decks([deck1,deck2])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})        
        self.assertEqual(len(game.current_player().in_play), 1)
        self.assertEqual(len(game.current_player().artifacts), 1)
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        for card in game.players[1].hand:
            game.players[1].mana += card.cost
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 2, "log_lines":[]})   
        game.play_move({"username": "b", "move_type": "SELECT_ARTIFACT", "card": 2, "log_lines":[]})        
        self.assertEqual(len(game.opponent().in_play), 1)
        self.assertEqual(len(game.opponent().artifacts), 1)
        self.assertEqual(len(game.current_player().artifacts), 1)
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_ARTIFACT", "card": 2, "log_lines":[]})        
        self.assertEqual(len(game.opponent().in_play), 0)
        self.assertEqual(len(game.opponent().artifacts), 0)
        self.assertEqual(len(game.current_player().artifacts), 0)

    def test_lightning_storm(self):
        """
            Test Lightning Storm.
        """
        game = self.game_for_decks([["Stone Elemental", "Stone Elemental"], ["Lightning Storm"]])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        for card in game.players[1].hand:
            game.players[1].mana += card.cost
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 2, "log_lines":[]})
        self.assertEqual(len(game.opponent().in_play), 0)

    def test_riffle(self):
        """
            Test Riffle.
        """
        game = self.game_for_decks([["Riffle", "Riffle", "Riffle", "Riffle", "Riffle", "Riffle"], []])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(game.current_player().username, "a")
        game.play_move({"username": "a", "move_type": "FINISH_RIFFLE", "card": 4, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(game.current_player().username, "b")

    def test_lurker_target(self):
        """
            Test Lurker prevents targetting.
        """
        game = self.game_for_decks([["Winding One"], ["Unwind"]])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        self.assertEqual(game.opponent().in_play[0].can_be_clicked, False)
        self.assertEqual(game.current_player().selected_spell(), None)

    def test_gnomish_piper(self):
        """
            Test Gnomish Piper lets you attack with the mob.
        """
        game = self.game_for_decks([["Stone Elemental", "Stone Elemental"], ["Gnomish Piper"]])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        for card in game.players[1].hand:
            game.players[1].mana += card.cost
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 2, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 1, "log_lines":[]})
        self.assertEqual(len(game.opponent().in_play), 0)

    def test_gnomish_piper_gives_back(self):
        """
            Test Gnomish Piper gives back the mob.
        """
        game = self.game_for_decks([["Stone Elemental"], ["Gnomish Piper"]])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        for card in game.players[1].hand:
            game.players[1].mana += card.cost
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 1, "log_lines":[]})
        self.assertEqual(len(game.opponent().in_play), 1)
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        self.assertEqual(len(game.opponent().in_play), 0)
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(game.current_player().in_play[0].name, "Stone Elemental")

    def test_akbars_pan_pipes(self):
        """
            Test Akbar's Pan Pipes makes a token,
        """
        game = self.game_for_decks([["Akbar's Pan Pipes"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ARTIFACT", "card": 0, "log_lines":[]})
        self.assertEqual(len(game.current_player().in_play), 1)

    def test_gnomish_militia(self):
        """
            Test Gnomish Militia
        """
        game = self.game_for_decks([["Gnomish Militia"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        self.assertEqual(len(game.current_player().hand), 2)

    def test_resonant_frequency(self):
        """
            Test Resonant Frequency
        """
        game = self.game_for_decks([["Stone Elemental", "LionKin", "Mirror of Fate", "Leyline Amulet", "Resonant Frequency", "Akbar's Pan Pipes"], []])
        for x in range(0,9):
            game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
            game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 2, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 3, "log_lines":[]})
        self.assertEqual(len(game.current_player().artifacts), 2)
        self.assertEqual(len(game.current_player().in_play), 2)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 4, "log_lines":[]})
        self.assertEqual(len(game.current_player().artifacts), 1)
        self.assertEqual(len(game.current_player().in_play), 1)
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 5, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(len(game.current_player().artifacts), 2)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 4, "log_lines":[]})
        self.assertEqual(len(game.current_player().artifacts), 2)
        self.assertEqual(len(game.current_player().in_play), 1)

    def test_song_dragon(self):
        """
            Test Song Dragon
        """
        game = self.game_for_decks([["Stone Elemental"], ["Lute", "Song Dragon"]])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        for card in game.players[1].hand:
            game.players[1].mana += card.cost
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 2, "log_lines":[]})
        self.assertEqual(len(game.current_player().in_play), 1)
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(len(game.current_player().in_play), 2)

    def test_jubilee(self):
        """
            Test Jubilee
        """
        deck1 = []
        for x in range(0, 2):
            deck1.append("Jubilee")
        deck1.append("Stone Elemental")
        deck1.append("Lute")
        game = self.game_for_decks([deck1, []])
        self.assertEqual(len(game.current_player().artifacts), 1)
        for x in range(0,13):
            game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
            game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(len(game.current_player().hand), 3)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1, "log_lines":[]})
        self.assertEqual(len(game.current_player().hand), 2)
        self.assertEqual(len(game.current_player().played_pile), 1)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 2, "log_lines":[]})
        self.assertEqual(len(game.current_player().hand), 1)
        self.assertEqual(len(game.current_player().in_play), 1)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        self.assertEqual(len(game.current_player().hand), 1)

    def test_avatar_of_song(self):
        """
            Test Avatar of Song
        """
        game = self.game_for_decks([["Avatar of Song", "Zap", "Kill", "Zap", "Lute"], []])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        for x in range(0,9):
            game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
            game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.current_player().hit_points = 3
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_SELF", "log_lines":[]})
        self.assertEqual(game.current_player().hit_points, 1)
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 2, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 3, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_SELF", "log_lines":[]})
        self.assertEqual(game.current_player().hit_points, 0)

    def test_ilra_lady_of_wind_and_music(self):
        """
            Test Ilra, Lady of Wind and Music
        """
        game = self.game_for_decks([["Stone Elemental", "Ilra, Lady of Wind and Music", "Lute"], []])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        for x in range(0,8):
            game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
            game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 28)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 23)

    def test_dazzling_solo(self):
        """
            Test Ilra, Lady of Wind and Music
        """
        game = self.game_for_decks([["Dazzling Solo", "Lute"], ["Stone Elemental", "Dagger"]])
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 2, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        for x in range(0,7):
            game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
            game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_ARTIFACT", "card": 3, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_ARTIFACT", "card": 3, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_OPPONENT", "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 29)
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(len(game.opponent().in_play), 1)
        self.assertEqual(len(game.opponent().artifacts), 1)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        self.assertEqual(len(game.opponent().in_play), 0)
        self.assertEqual(len(game.opponent().artifacts), 0)
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 2, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 2, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_ARTIFACT", "card": 3, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_OPPONENT", "log_lines":[]})
        self.assertEqual(game.opponent().hit_points, 27)

    def test_lightning_elemental(self):
        """
            Test Lightning Elemental.
        """
        game = self.game_for_decks([["Stone Elemental"], ["Lightning Elemental"]])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 1, "log_lines":[]})
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 0, "log_lines":[]})
        self.assertEqual(len(game.opponent().in_play), 0)

    def test_mana_battery(self):
        """
            Test Mana Battery.
        """
        game = self.game_for_decks([["Mana Battery", "Winding One", "Winding One"], []])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        self.assertEqual(len(game.current_player().artifacts), 1)
        self.assertEqual(game.current_player().artifacts[0].effects[0].counters, 0)
        for x in range(0,3):
            game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
            game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(game.current_player().mana, 4)
        self.assertEqual(game.current_player().artifacts[0].effects[0].counters, 3)
        self.assertEqual(game.current_player().current_mana(), 7)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1, "log_lines":[]})
        self.assertEqual(game.current_player().mana, 1)
        self.assertEqual(game.current_player().artifacts[0].effects[0].counters, 3)
        self.assertEqual(game.current_player().current_mana(), 4)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 2, "log_lines":[]})
        self.assertEqual(game.current_player().mana, 0)
        self.assertEqual(game.current_player().artifacts[0].effects[0].counters, 1)
        self.assertEqual(game.current_player().current_mana(), 1)

    def test_spell_archaeologist(self):
        """
            Test Spell Archaeologist
        """
        game = self.game_for_decks([["Spell Archaeologist", "Zap"], []])
        game.players[0].mana = 3
        game.players[0].played_pile.append(game.players[0].hand[1])
        game.players[0].hand.pop()
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        self.assertEqual(len(game.current_player().in_play), 1)
        self.assertEqual(len(game.current_player().hand), 0)
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(len(game.opponent().hand), 1)

    def test_orpheus_krustal(self):
        """
            Test Orpheus Krustal
        """
        game = self.game_for_decks([["Orpheus Krustal", "Zap", "Zap", "Zap", "Zap", "Zap", "Zap", "Zap", "Zap"], []])
        game.players[0].mana = 5
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        hand_count = len(game.players[0].hand)
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        self.assertEqual(hand_count, len(game.players[0].hand) - 3)

    def test_crazy_control(self):
        """
            Test Crazy Control
        """
        game = self.game_for_decks([["Crazy Control"], ["Game Maker"]])
        game.players[0].mana = 6
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        self.assertEqual(1, len(game.players[0].in_play))
        self.assertEqual(0, len(game.players[1].hand))

    def test_quasar_tap(self):
        """
            Test Quasar Tap
        """
        game = self.game_for_decks([["Quasar Tap", "Tame-ish Sabretooth"], []])
        game.players[0].mana = 18
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1, "log_lines":[]})
        self.assertEqual(game.players[0].mana, game.players[0].max_mana)

    def test_rolling_thunder(self):
        """
            Test Rolling Thunder
        """
        game = self.game_for_decks([["Rolling Thunder"], []])
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_OPPONENT", "log_lines":[]})
        self.assertEqual(28, game.players[1].hit_points)
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0, "log_lines":[]})
        game.play_move({"username": "a", "move_type": "SELECT_OPPONENT", "log_lines":[]})
        self.assertEqual(25, game.players[1].hit_points)


    def test_tame_shop_demon(self):
        """
            Test Tame Shop Demon
        """
        game = self.game_for_decks([["Tame Shop Demon"], []])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        self.assertEqual(1, len(game.players[0].in_play))
        game.play_move({"username": "a", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "b", "move_type": "END_TURN", "log_lines":[]})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0, "log_lines":[]})
        self.assertEqual(2, len(game.players[0].in_play))
        self.assertEqual("Leprechaun", game.players[0].in_play[0].name)
        self.assertEqual("Awesomerachaun", game.players[0].in_play[1].name)


