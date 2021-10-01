from django.test import TestCase
from battle_wizard.game.game import Game
from battle_wizard.game.player import Player
from battle_wizard.game.player_ai import PlayerAI
import os
import time


class GameObjectTests(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def game_for_decks(self, player_decks):
        game_dict = {}
        game = Game("pvp", info=game_dict, player_decks=player_decks)
        game.play_move({"username": "a", "move_type": "JOIN"})
        game.play_move({"username": "b", "move_type": "JOIN"})
        return game

    def test_ten_card_hand_limit(self):
        """
            Test you can't draw more than 10 cards.
        """

        deck1 = ["Stone Elemental" for x in range(0,11)]
        deck2 = ["Stone Elemental" for x in range(0,11)]
        game = self.game_for_decks([deck1,deck2])
        for x in range(0,10):
            game.play_move({"username": "a", "move_type": "END_TURN"})
            game.play_move({"username": "b", "move_type": "END_TURN"})
        self.assertEqual(len(game.current_player().hand), game.max_hand_size)

    def test_ten_mana_limit(self):
        """
            Test you can't have more than 10 mana
        """

        deck1 = ["Stone Elemental"]
        deck2 = ["Stone Elemental"]
        game = self.game_for_decks([deck1,deck2])
        for x in range(0,10):
            game.play_move({"username": "a", "move_type": "END_TURN"})
            game.play_move({"username": "b", "move_type": "END_TURN"})
        self.assertEqual(game.current_player().max_mana, game.current_player().max_max_mana())

    def test_over_mana_mana_shrub(self):
        """
            Test you can't have more than 10 mana
        """

        deck1 = ["Mana Shrub", "Kill"]
        deck2 = []
        game = self.game_for_decks([deck1,deck2])
        for x in range(0,10):
            game.play_move({"username": "a", "move_type": "END_TURN"})
            game.play_move({"username": "b", "move_type": "END_TURN"})
        self.assertEqual(game.current_player().max_mana, game.current_player().max_max_mana())
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0})
        self.assertEqual(game.current_player().max_mana, game.current_player().max_max_mana())
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0})
        self.assertEqual(game.current_player().max_mana, game.current_player().max_max_mana())

    def test_illegal_opponent_start_turn(self):
        game = self.game_for_decks([[], ["Zap","Zap","Zap","Zap","Zap"]])
        game.play_move({"username": "a", "move_type": "JOIN"})
        game.play_move({"username": "b", "move_type": "JOIN"})
        self.assertEqual(len(game.opponent().hand), 4)
        game.play_move({"username": "b", "move_type": "START_TURN"})
        self.assertEqual(len(game.opponent().hand), 4)

    def test_play_stone_elemental(self):
        """
            Vanilla mob.
        """
        game = self.game_for_decks([["Stone Elemental"], []])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        self.assertEqual(len(game.current_player().in_play), 1)

    def test_play_summoning_sickness(self):
        game = self.game_for_decks([["Stone Elemental"], []])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0})
        self.assertEqual(game.opponent().hit_points, game.opponent().max_hit_points)

    def test_play_training_master_and_attack_with_buffed_target(self):
        """
            Test Training Master's target's power doubles and can still attack.
        """
        game = self.game_for_decks([["Stone Elemental", "Training Master"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0})
        self.assertEqual(game.current_player().in_play[0].power_with_tokens(game.current_player()), 4)
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0})
        game.play_move({"username": "a", "move_type": "SELECT_OPPONENT"})
        self.assertEqual(game.opponent().hit_points, 26)

    def test_unwind_mana_shrub(self):
        """
            Test return a mob to owner's hand with Unwind.

            Make sure Mana Shrub's effects trigger on leaving play.
        """
        game = self.game_for_decks([["Mana Shrub", "Unwind"], []])
        turns_to_elapse = 2
        for x in range(0, turns_to_elapse):
            game.play_move({"username": "a", "move_type": "END_TURN"})
            game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1})
        self.assertEqual(game.current_player().max_mana, turns_to_elapse + 2)
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0})
        self.assertEqual(game.current_player().max_mana, turns_to_elapse + 1)

    def test_play_stiff_wind(self):
        """
            Tests Stiff Wind prevents attack, and that it draws a card.

            2 effects card.
        """
        game = self.game_for_decks([["Stone Elemental", "Stiff Wind"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        self.assertEqual(len(game.current_player().hand), 1)
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0})
        self.assertEqual(game.opponent().hit_points, game.opponent().max_hit_points)

    def test_play_siz_pop(self):
        """
            Tests Siz Pop deals a damage and draws a card.

            2 Effects card.
        """
        game = self.game_for_decks([["Siz Pop", "Siz Pop"], []])
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "SELECT_SELF", "card": 0})
        self.assertEqual(game.current_player().hit_points, 29)
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1})
        game.play_move({"username": "a", "move_type": "SELECT_OPPONENT"})
        self.assertEqual(game.opponent().hit_points, 29)

    def test_mind_manacles(self):
        """
            Tests Mind Manacles makes the mob switch sides.
        """
        game = self.game_for_decks([["Stone Elemental"], ["Mind Manacles"]])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "END_TURN"})
        for x in range(0, 5):
            game.play_move({"username": "b", "move_type": "END_TURN"})
            game.play_move({"username": "a", "move_type": "END_TURN"})
        self.assertEqual(len(game.current_player().in_play), 0)
        self.assertEqual(len(game.opponent().in_play), 1)
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 1})        
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 0})
        self.assertEqual(len(game.current_player().in_play), 1)
        self.assertEqual(len(game.opponent().in_play), 0)

    def test_mind_manacles_fast_target(self):
        """
            Test take_control effect lets caster attack with a mob that has the add_fast effect.
        """
        game = self.game_for_decks([["OG Vamp"], ["Mind Manacles"]])
        for x in range(0,5):
            game.play_move({"username": "a", "move_type": "END_TURN"})
            game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "b", "move_type": "RESOLVE_NEXT_STACK"})        
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 1})        
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 0})
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 0})
        game.play_move({"username": "b", "move_type": "SELECT_OPPONENT"})
        og_vamp = game.players[1].in_play[0]
        end_hit_points = game.opponent().max_hit_points - og_vamp.power_with_tokens(game.players[1])
        self.assertEqual(game.opponent().hit_points, end_hit_points)

    def test_mind_manacles_ambush_target(self):
        """
            Test take_control effect lets caster attack with a mob that has the add_ambush effect.
        """
        game = self.game_for_decks([["Stone Elemental", "Tame-ish Sabretooth"], ["Mind Manacles"]])
        for x in range(0,8):
            game.play_move({"username": "a", "move_type": "END_TURN"})
            game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "b", "move_type": "RESOLVE_NEXT_STACK"})        
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1})
        game.play_move({"username": "b", "move_type": "RESOLVE_NEXT_STACK"})        
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 2})        
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 1})
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 1})
        self.assertEqual(len(game.opponent().in_play), 1)
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 0})
        self.assertEqual(len(game.opponent().in_play), 0)

    def test_removed_attacked_after_combat_death(self):
        """
            Tests if a mob that dies in combat gets the attacked flag reset properly.
        """
        game = self.game_for_decks([["Stone Elemental"], ["Stone Elemental"]])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 1})
        game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 1})
        self.assertEqual(game.current_player().played_pile[0].attacked, False)

    def test_town_ranger_guards(self):
        """
            Test Guard works on Town Ranger by checking if there are only two legal moves (attack ranger and end turn).
        """
        game = self.game_for_decks([["Familiar"], ["Town Ranger"]])
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 1})
        game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0})
        legal_moves = PlayerAI(game, game.current_player().as_dict()).legal_moves_for_ai()
        self.assertEqual(len(legal_moves), 1)
        self.assertEqual(game.opponent().in_play[0].can_be_clicked, True)
        self.assertEqual(game.opponent().can_be_clicked, False)


    def test_town_wizard_makes(self):
        """
            Test Town Wizard makes a card.
        """
        game = self.game_for_decks([["Town Wizard"], []])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "MAKE_CARD", "card": game.current_player().card_choice_info["cards"][0].as_dict()})
        self.assertEqual(len(game.current_player().hand), 1)

    def test_town_shaman_makes(self):
        """
            Test Town Shaman makes a card.
        """
        game = self.game_for_decks([["Town Shaman"], []])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "MAKE_CARD", "card": game.current_player().card_choice_info["cards"][0].as_dict()})
        self.assertEqual(len(game.current_player().hand), 1)

    def test_lute_transforms_and_makes(self):
        """
            Test Lute.
        """
        game = self.game_for_decks([["Lute"], []])
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "END_TURN"})
        self.assertEqual(game.current_player().mana, 2)
        game.play_move({"username": "a", "move_type": "SELECT_ARTIFACT", "card": 0})        
        self.assertEqual(game.current_player().mana, 1)
        game.play_move({"username": "a", "move_type": "SELECT_ARTIFACT", "card": 0})        
        self.assertEqual(len(game.current_player().hand), 1)
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "SELECT_ARTIFACT", "card": 0})        
        self.assertEqual(len(game.current_player().hand), 2)
        game.play_move({"username": "a", "move_type": "SELECT_ARTIFACT", "card": 0})        
        self.assertEqual(game.current_player().artifacts[0].enabled_activated_effects()[0].counters, 2)

    def test_gnomish_mayor_summons(self):
        """
            Test Gnomish Mayor.
        """
        game = self.game_for_decks([["Gnomish Mayor"], []])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        self.assertEqual(len(game.current_player().in_play), 2)

    def test_gnomish_press_gang_makes(self):
        """
            Test Gnomish Press Gang.
        """
        game = self.game_for_decks([["Gnomish Press Gang"], []])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        self.assertEqual(len(game.current_player().hand), 1)

    def test_wishstone_makes(self):
        """
            Test Wishstone makes a Artifact from deck into in play.
        """
        deck = ["Wish Stone", "LionKin", "LionKin", "LionKin", "Scepter of Manipulation"]
        game = self.game_for_decks([deck, []])
        game.players[0].mana = 4
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "SELECT_ARTIFACT", "card": 0})
        game.play_move({"username": "a", "move_type": "FETCH_CARD_INTO_PLAY", "card": game.current_player().card_choice_info["cards"][0].id})
        self.assertEqual(game.current_player().artifacts[-1].name, "Scepter of Manipulation")

    def test_bewitching_lights(self):
        """
            Test Bewitching Lights makes a Artifact from deck into in play.
        """
        game = self.game_for_decks([["Bewitching Lights"], ["LionKin"]])
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0})
        game.play_move({"username": "a", "move_type": "SELECT_OPPONENT"})
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
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 3})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 2})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        self.assertEqual(len(game.current_player().in_play), 4)

    def test_taunted_bear_fade(self):
        """
            Test Taunted Bear Fade effects.
        """
        game = self.game_for_decks([["Taunted Bear"], []])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "END_TURN"})
        self.assertEqual(game.current_player().in_play[0].power_with_tokens(game.current_player()), 2)
        self.assertEqual(game.current_player().in_play[0].toughness_with_tokens(), 1)
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "END_TURN"})
        self.assertEqual(len(game.current_player().in_play), 0)

    def test_taunted_bear_fast_stomp(self):
        """
            Test Taunted Bear Fast and Stomp effects.
        """
        game = self.game_for_decks([["War Scorpion"], ["Taunted Bear"]])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 1})
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 1})
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 0})
        self.assertEqual(game.opponent().hit_points, 29)

    def test_war_scorpion_gain_symbiotic_fast_effect(self):
        """
            Test War Scorpion.
        """
        game = self.game_for_decks([["War Scorpion", "Taunted Bear"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1})
        self.assertEqual(len(game.current_player().in_play), 2)
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0})
        game.play_move({"username": "a", "move_type": "SELECT_OPPONENT"})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 1})
        game.play_move({"username": "a", "move_type": "SELECT_OPPONENT"})
        self.assertEqual(game.opponent().hit_points, game.opponent().max_hit_points - game.players[0].in_play[0].power_with_tokens(game.players[0]) - game.players[0].in_play[1].power_with_tokens(game.players[0]))

    def test_war_scorpion_remove_symbiotic_fast_effect(self):
        """
            Test War Scorpion stps being Fast if the only Fast guy dies
        """
        game = self.game_for_decks([["War Scorpion", "Taunted Bear", "Zap"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 2})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 1})
        self.assertEqual(len(game.current_player().in_play), 1)
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0})
        game.play_move({"username": "a", "move_type": "SELECT_OPPONENT"})
        self.assertEqual(game.opponent().hit_points, game.opponent().max_hit_points)

    def test_berserk_monkey(self):
        """
            Test Berserk Monkey.
        """
        game = self.game_for_decks([["Berserk Monkey", "Berserk Monkey", "Berserk Monkey"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 2})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1})
        self.assertEqual(game.current_player().in_play[0].power_with_tokens(game.current_player()), 1)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        self.assertEqual(game.current_player().in_play[0].power_with_tokens(game.current_player()), 2)
        self.assertEqual(game.current_player().in_play[1].power_with_tokens(game.current_player()), 1)

    def test_frenzy_one_card(self):
        """
            Test Frenzy one card.
        """
        game = self.game_for_decks([["Frenzy", "Frenzy", "Frenzy", "Frenzy"], []])
        game.players[0].mana = 2
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        self.assertEqual(len(game.current_player().hand), 3)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1})
        self.assertEqual(len(game.current_player().hand), 3)

    def test_frenzy_two_cards(self):
        """
            Test Frenzy two cards.
        """
        game = self.game_for_decks([["Taunted Bear", "Frenzy", "Frenzy", "Frenzy", "Frenzy", "Frenzy", "Frenzy", "Frenzy"], []])
        game.players[0].mana = 2
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0})
        game.play_move({"username": "a", "move_type": "SELECT_OPPONENT"})
        self.assertEqual(len(game.current_player().hand), 3)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 3})
        self.assertEqual(len(game.current_player().hand), 4)

    def test_impale(self):
        """
            Test Impale.
        """
        game = self.game_for_decks([["War Scorpion", "Impale"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0})
        self.assertEqual(game.opponent().hit_points, 27)



    def test_arsenal(self):
        """
            Test Arsenal and Kill Artifact.
        """
        game = self.game_for_decks([["War Scorpion", "Arsenal", "Kill Artifact"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1})
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "END_TURN"})
        self.assertEqual(game.current_player().in_play[0].power_with_tokens(game.current_player()), 3)
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 2})
        game.play_move({"username": "a", "move_type": "SELECT_ARTIFACT", "card": 1})
        self.assertEqual(game.current_player().in_play[0].power_with_tokens(game.current_player()), 2)


    def test_arsenal_manacles(self):
        """
            Test Arsenal and Mind Manacles.
        """
        game = self.game_for_decks([["War Scorpion", "Arsenal"], ["Mind Manacles"]])
        for x in range(0,5):
            game.play_move({"username": "a", "move_type": "END_TURN"})
            game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "b", "move_type": "RESOLVE_NEXT_STACK"})        
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1})
        game.play_move({"username": "b", "move_type": "RESOLVE_NEXT_STACK"})        
        self.assertEqual(game.current_player().in_play[0].power_with_tokens(game.current_player()), 3)
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 2})
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 0})
        self.assertEqual(game.current_player().in_play[0].power_with_tokens(game.current_player()), 2)

    def test_arsenal_manacles_two_scorpions(self):
        """
            Test Arsenal and and Mind Manacles
        """
        game = self.game_for_decks([["War Scorpion", "Akbar's Pan Pipes", "Arsenal", "War Scorpion"], ["Mind Manacles"]])
        for x in range(0,5):
            game.play_move({"username": "a", "move_type": "END_TURN"})
            game.play_move({"username": "b", "move_type": "END_TURN"})
        for card in game.players[0].hand:
            game.players[0].mana += card.cost    
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 3})
        game.play_move({"username": "b", "move_type": "RESOLVE_NEXT_STACK"})        
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 2})
        game.play_move({"username": "b", "move_type": "RESOLVE_NEXT_STACK"})        
        self.assertEqual(game.current_player().in_play[0].power_with_tokens(game.current_player()), 3)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1})
        game.play_move({"username": "b", "move_type": "RESOLVE_NEXT_STACK"})        
        self.assertEqual(game.current_player().in_play[0].power_with_tokens(game.current_player()), 4)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "b", "move_type": "RESOLVE_NEXT_STACK"})        
        self.assertEqual(game.current_player().in_play[0].power_with_tokens(game.current_player()), 4)
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.players[1].mana = game.players[1].hand[0].cost    
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 4})
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 3})
        self.assertEqual(game.current_player().in_play[0].power_with_tokens(game.current_player()), 2)

    def test_arsenal_2x(self):
        """
            Test Arsenal and Kill Artifact.
        """
        game = self.game_for_decks([["War Scorpion", "Arsenal", "Arsenal"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 2})
        self.assertEqual(game.current_player().in_play[0].power_with_tokens(game.current_player()), 6)

    def test_arsenal_3x(self):
        """
            Test Arsenal and Kill Artifact.
        """
        game = self.game_for_decks([["Mana Shrub", "Arsenal", "Arsenal", "Arsenal"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost

        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 2})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 3})
        self.assertEqual(game.current_player().in_play[0].power_with_tokens(game.current_player()), 10)

    def test_arsenal_2x_reverse(self):
        """
            Test Arsenal and Kill Artifact.
        """
        game = self.game_for_decks([["Arsenal", "Arsenal", "War Scorpion"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost

        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 2})
        self.assertEqual(game.current_player().in_play[0].power_with_tokens(game.current_player()), 6)

    def test_arsenal_2x_middle(self):
        """
            Test Arsenal and Kill Artifact.
        """
        game = self.game_for_decks([["Arsenal", "Arsenal", "War Scorpion"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost

        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 2})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1})
        self.assertEqual(game.current_player().in_play[0].power_with_tokens(game.current_player()), 6)

    def test_dragonslayer_elf_no_targets(self):
        """
            Test you can End Turn after playing DragonSlayer with no targets.
        """
        game = self.game_for_decks([["Dragonslayer Elf", "Stone Elemental"], ["Stone Elemental"]])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1})
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 2})
        game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "END_TURN"})
        self.assertEqual(game.current_player().username, "b")

    def test_lurker_guard(self):
        """
            Test you can attack past a mob with Guard+Lurker.
        """
        game = self.game_for_decks([["Stone Elemental"], ["Air Elemental", "Hide"]])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "END_TURN"})
        for card in game.players[1].hand:
            game.players[1].mana += card.cost
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 1})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 2})
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 1})
        game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0})
        game.play_move({"username": "a", "move_type": "SELECT_OPPONENT"})
        self.assertEqual(game.opponent().hit_points, 28)

    def test_lurker_spell_selection(self):
        """
            Test you can't select a spell that targets mobs if the only mob has lurker
        """
        game = self.game_for_decks([["Winding One", "Kill"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0})
        self.assertEqual(game.players[0].selected_spell(), None)

    def test_mana_storm(self):
        """
            Test Mana Storm.
        """

        deck1 = ["Mana Storm"]
        deck2 = []
        game = self.game_for_decks([deck1,deck2])
        for x in range(0,9):
            game.play_move({"username": "a", "move_type": "END_TURN"})
            game.play_move({"username": "b", "move_type": "END_TURN"})
        self.assertEqual(game.current_player().max_mana, 10)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})        
        self.assertEqual(game.current_player().max_mana, 0)

    def test_riftwalker_djinn_drain(self):
        """
            Test Drain effect of Riftwalker Djinn
        """

        deck1 = ["Town Fighter"]
        deck2 = ["Riftwalker Djinn"]
        game = self.game_for_decks([deck1,deck2])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})        
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0})        
        game.play_move({"username": "a", "move_type": "SELECT_OPPONENT"})        
        self.assertEqual(game.opponent().hit_points, game.opponent().max_hit_points - 2)
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.players[1].mana += game.players[1].hand[0].cost
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 1})        
        game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 1})        
        game.play_move({"username": "b", "move_type": "SELECT_OPPONENT"})        
        self.assertEqual(game.current_player().hit_points, game.current_player().max_hit_points)

    def test_riftwalker_djinn_shield_spell(self):
        """
            Test Shield effect of Riftwalker Djinn with a damage spell
        """

        deck1 = ["Riftwalker Djinn"]
        deck2 = ["Zap", "Zap"]
        game = self.game_for_decks([deck1,deck2])
        for x in range(0,4):
            game.play_move({"username": "a", "move_type": "END_TURN"})
            game.play_move({"username": "b", "move_type": "END_TURN"})

        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})        
        game.play_move({"username": "b", "move_type": "RESOLVE_NEXT_STACK"})        
        game.play_move({"username": "a", "move_type": "END_TURN"})

        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 1})        
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 0})        
        self.assertEqual(game.opponent().in_play[0].damage, 0)
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 2})        
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 0})        
        self.assertEqual(len(game.opponent().in_play), 0)

    def test_riftwalker_djinn_shield_combat(self):
        """
            Test Shield effect of Riftwalker Djinn with combat
        """

        deck1 = ["Riftwalker Djinn"]
        deck2 = ["Riftwalker Djinn"]
        game = self.game_for_decks([deck1,deck2])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})        
        game.play_move({"username": "a", "move_type": "END_TURN"})
        for card in game.players[1].hand:
            game.players[1].mana += card.cost
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 1})        
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 1})        
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 0})        
        self.assertEqual(game.current_player().in_play[0].damage, 0)
        self.assertEqual(game.opponent().in_play[0].damage, 0)
        game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0})        
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 1})        
        self.assertEqual(len(game.current_player().in_play), 0)
        self.assertEqual(len(game.opponent().in_play), 0)

    def test_animal_trainer(self):
        """
            Test Animal Trainer pumps and Fades a mob.
        """
        game = self.game_for_decks([["Stone Elemental", "Animal Trainer"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0})
        self.assertEqual(game.current_player().in_play[0].power_with_tokens(game.current_player()), 4)
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "END_TURN"})
        self.assertEqual(game.current_player().in_play[0].power_with_tokens(game.current_player()), 3)

    def test_enraged_stomper(self):
        """
            Test Enraged Stomper damages its controller.
        """
        game = self.game_for_decks([["Enraged Stomper"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "END_TURN"})        
        game.play_move({"username": "b", "move_type": "END_TURN"})
        self.assertEqual(game.current_player().hit_points, 29)

    def test_gird_for_battle(self):
        """
            Test Gird for Battle.
        """
        game = self.game_for_decks([["Gird for Battle", "Arsenal", "Arsenal", "Arsenal", "Arsenal", "Arsenal", "Arsenal", "Arsenal"], []])
        game.players[0].mana = game.players[0].hand[0].cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        self.assertEqual(len(game.current_player().in_play), 1)
        self.assertEqual(len(game.current_player().artifacts), 1)
        self.assertEqual(game.current_player().in_play[0].power_with_tokens(game.current_player()), 4)
        game.play_move({"username": "a", "move_type": "END_TURN"})        
        game.play_move({"username": "b", "move_type": "END_TURN"})
        self.assertEqual(game.current_player().in_play[0].power_with_tokens(game.current_player()), 3)


    def test_spirit_of_the_stampede(self):
        """
            Spirit of the Stampede
        """
        game = self.game_for_decks([["Spirit of the Stampede", "Spirit of the Stampede", "Akbar's Pan Pipes"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        self.assertEqual(game.current_player().in_play[0].power_with_tokens(game.current_player()), 3)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1})
        self.assertEqual(game.current_player().in_play[0].power_with_tokens(game.current_player()), 4)
        self.assertEqual(game.current_player().in_play[1].power_with_tokens(game.current_player()), 4)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 2})
        self.assertEqual(game.current_player().in_play[0].power_with_tokens(game.current_player()), 5)
        self.assertEqual(game.current_player().in_play[1].power_with_tokens(game.current_player()), 5)


    def test_push_soul(self):
        """
            Test Push Soul.
        """

        deck1 = ["Stone Elemental", "Zap"]
        deck2 = ["Push Soul"]
        game = self.game_for_decks([deck1,deck2])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})        
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1})        
        game.play_move({"username": "a", "move_type": "SELECT_SELF"})        
        game.play_move({"username": "b", "move_type": "RESOLVE_NEXT_STACK", "card": 1})        
        self.assertEqual(game.current_player().hit_points, 27)
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 2})        
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 0})        
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
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 4})        
        game.play_move({"username": "a", "move_type": "FINISH_RIFFLE", "card": game.current_player().card_choice_info["cards"][0].id})
        self.assertEqual(len(game.current_player().hand), 2)
        self.assertEqual(len(game.current_player().played_pile), 3)

    def test_disk_of_death(self):
        """
            Test Disk of Death.
        """

        deck1 = ["Stone Elemental", "Lute"]
        deck2 = ["Disk of Death"]
        game = self.game_for_decks([deck1,deck2])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})        
        self.assertEqual(len(game.current_player().in_play), 1)
        self.assertEqual(len(game.current_player().artifacts), 1)
        game.play_move({"username": "a", "move_type": "END_TURN"})
        for card in game.players[1].hand:
            game.players[1].mana += card.cost
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 2})   
        game.play_move({"username": "b", "move_type": "SELECT_ARTIFACT", "card": 2})        
        self.assertEqual(len(game.current_player().artifacts), 1)
        self.assertEqual(len(game.opponent().artifacts), 1)
        self.assertEqual(len(game.opponent().in_play), 1)
        game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "SELECT_ARTIFACT", "card": 2})        
        self.assertEqual(len(game.opponent().in_play), 0)
        self.assertEqual(len(game.opponent().artifacts), 0)
        self.assertEqual(len(game.current_player().artifacts), 0)

    def test_lightning_storm(self):
        """
            Test Lightning Storm.
        """
        game = self.game_for_decks([["Stone Elemental", "Stone Elemental"], ["Lightning Storm"]])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1})
        game.play_move({"username": "a", "move_type": "END_TURN"})
        for card in game.players[1].hand:
            game.players[1].mana += card.cost
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 2})
        self.assertEqual(len(game.opponent().in_play), 0)

    def test_riffle(self):
        """
            Test Riffle.
        """
        game = self.game_for_decks([["Riffle", "Riffle", "Riffle", "Riffle", "Riffle", "Riffle"], []])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "END_TURN"})
        self.assertEqual(game.current_player().username, "a")
        game.play_move({"username": "a", "move_type": "FINISH_RIFFLE", "card": 4})
        game.play_move({"username": "a", "move_type": "END_TURN"})
        self.assertEqual(game.current_player().username, "b")

    def test_lurker_target(self):
        """
            Test Lurker prevents targetting.
        """
        game = self.game_for_decks([["Winding One"], ["Unwind"]])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "END_TURN"})
        for card in game.players[1].hand:
            game.players[1].mana += card.cost
        self.assertEqual(game.current_player().hand[0].can_be_clicked, False)

    def test_akbars_pan_pipes(self):
        """
            Test Akbar's Pan Pipes makes a token,
        """
        game = self.game_for_decks([["Akbar's Pan Pipes"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "SELECT_ARTIFACT", "card": 0})
        self.assertEqual(len(game.current_player().in_play), 1)

    def test_gnomish_militia(self):
        """
            Test Gnomish Militia
        """
        game = self.game_for_decks([["Gnomish Militia"], []])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        self.assertEqual(len(game.current_player().hand), 2)

    def test_resonant_frequency(self):
        """
            Test Resonant Frequency
        """
        game = self.game_for_decks([["Stone Elemental", "LionKin", "Mirror of Fate", "Leyline Amulet", "Resonant Frequency", "Akbar's Pan Pipes"], []])
        for x in range(0,9):
            game.play_move({"username": "a", "move_type": "END_TURN"})
            game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 2})
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 3})
        self.assertEqual(len(game.current_player().artifacts), 2)
        self.assertEqual(len(game.current_player().in_play), 2)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 4})
        self.assertEqual(len(game.current_player().artifacts), 1)
        self.assertEqual(len(game.current_player().in_play), 1)
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 5})
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "END_TURN"})
        self.assertEqual(len(game.current_player().artifacts), 2)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 4})
        self.assertEqual(len(game.current_player().artifacts), 1)
        self.assertEqual(len(game.current_player().in_play), 1)

    def test_song_dragon(self):
        """
            Test Song Dragon
        """
        game = self.game_for_decks([["Stone Elemental"], ["Lute", "Song Dragon"]])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "END_TURN"})
        for card in game.players[1].hand:
            game.players[1].mana += card.cost
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 2})
        self.assertEqual(len(game.current_player().in_play), 1)
        game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "END_TURN"})
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
            game.play_move({"username": "a", "move_type": "END_TURN"})
            game.play_move({"username": "b", "move_type": "END_TURN"})
        self.assertEqual(len(game.current_player().hand), 3)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1})
        self.assertEqual(len(game.current_player().hand), 2)
        self.assertEqual(len(game.current_player().played_pile), 1)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 2})
        self.assertEqual(len(game.current_player().hand), 1)
        self.assertEqual(len(game.current_player().in_play), 1)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        self.assertEqual(len(game.current_player().hand), 1)

    def test_ilra_lady_of_wind_and_music(self):
        """
            Test Ilra, Lady of Wind and Music
        """
        game = self.game_for_decks([["Stone Elemental", "Ilra, Lady of Wind and Music", "Lute"], []])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        for x in range(0,8):
            game.play_move({"username": "a", "move_type": "END_TURN"})
            game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0})
        game.play_move({"username": "a", "move_type": "SELECT_OPPONENT"})
        self.assertEqual(game.opponent().hit_points, 28)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0})
        game.play_move({"username": "a", "move_type": "SELECT_OPPONENT"})
        self.assertEqual(game.opponent().hit_points, 23)

    def test_lightning_elemental(self):
        """
            Test Lightning Elemental.
        """
        game = self.game_for_decks([["Stone Elemental"], ["Lightning Elemental"]])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 1})
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 0})
        self.assertEqual(len(game.opponent().in_play), 0)

    def test_mana_battery(self):
        """
            Test Mana Battery.
        """
        game = self.game_for_decks([["Mana Battery", "Winding One", "Winding One"], []])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        self.assertEqual(len(game.current_player().artifacts), 1)
        self.assertEqual(game.current_player().artifacts[0].effects[0].counters, -1)
        for x in range(0,3):
            game.play_move({"username": "a", "move_type": "END_TURN"})
            game.play_move({"username": "b", "move_type": "END_TURN"})
        self.assertEqual(game.current_player().mana, 4)
        self.assertEqual(game.current_player().current_mana(), 7)
        self.assertEqual(game.current_player().artifacts[0].effects[0].counters, 3)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1})
        self.assertEqual(game.current_player().mana, 1)
        self.assertEqual(game.current_player().current_mana(), 4)
        self.assertEqual(game.current_player().artifacts[0].effects[0].counters, 3)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 2})
        self.assertEqual(game.current_player().mana, 0)
        self.assertEqual(game.current_player().current_mana(), 1)
        self.assertEqual(game.current_player().artifacts[0].effects[0].counters, 1)

    def test_spell_archaeologist(self):
        """
            Test Spell Archaeologist
        """
        game = self.game_for_decks([["Spell Archaeologist", "Zap"], []])
        game.players[0].mana = 3
        game.players[0].played_pile.append(game.players[0].hand[1])
        game.players[0].hand.pop()
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        self.assertEqual(len(game.current_player().in_play), 1)
        self.assertEqual(len(game.current_player().hand), 0)
        game.play_move({"username": "a", "move_type": "END_TURN"})
        self.assertEqual(len(game.opponent().hand), 1)

    def test_orpheus_krustal(self):
        """
            Test Orpheus Krustal
        """
        game = self.game_for_decks([["Orpheus Krustal", "Zap", "Zap", "Zap", "Zap", "Zap", "Zap", "Zap", "Zap"], []])
        game.players[0].mana = 5
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "END_TURN"})
        hand_count = len(game.players[0].hand)
        game.play_move({"username": "b", "move_type": "END_TURN"})
        self.assertEqual(hand_count, len(game.players[0].hand) - 3)

    def test_crazy_control(self):
        """
            Test Crazy Control
        """
        game = self.game_for_decks([["Crazy Control"], ["Game Maker"]])
        game.players[0].mana = 6
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        self.assertEqual(1, len(game.players[0].in_play))
        self.assertEqual(0, len(game.players[1].hand))

    def test_quasar_tap(self):
        """
            Test Quasar Tap
        """
        game = self.game_for_decks([["Quasar Tap", "Tame-ish Sabretooth"], []])
        game.players[0].mana = 18
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1})
        self.assertEqual(game.players[0].mana, game.players[0].max_mana)

    def test_rolling_thunder(self):
        """
            Test Rolling Thunder
        """
        game = self.game_for_decks([["Rolling Thunder"], []])
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "SELECT_OPPONENT"})
        self.assertEqual(28, game.players[1].hit_points)
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "SELECT_OPPONENT"})
        self.assertEqual(25, game.players[1].hit_points)

    def test_tame_shop_demon(self):
        """
            Test Tame Shop Demon
        """
        game = self.game_for_decks([["Tame Shop Demon"], []])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        self.assertEqual(1, len(game.players[0].in_play))
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        self.assertEqual(2, len(game.players[0].in_play))
        self.assertEqual("Leprechaun", game.players[0].in_play[0].name)
        self.assertEqual("Awesomerachaun", game.players[0].in_play[1].name)

    def test_spouty_gas_ball(self):
        """
            Test Spouty Gas Ball pings.
        """
        game = self.game_for_decks([["Spouty Gas Ball", "Stone Elemental"], ["Stone Elemental"]])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 2})
        game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 1})
        self.assertEqual(game.opponent().in_play[0].damage, 1)

    def test_doomer_drain(self):
        """
            Test Drain effect of Doomer
        """

        deck1 = ["Doomer"]
        deck2 = ["Stone Elemental"]
        game = self.game_for_decks([deck1, deck2])
        game.players[0].hit_points = 29
        game.players[0].mana = game.players[0].hand[0].cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})        
        game.play_move({"username": "a", "move_type": "END_TURN"})
        self.assertEqual(game.opponent().hit_points, game.opponent().max_hit_points)

    def test_inferno_element_fast(self):
        """
            Test add_fast effect of Inferno Elemental
        """

        deck1 = ["Inferno Elemental"]
        deck2 = []
        game = self.game_for_decks([deck1, deck2])
        game.players[0].mana = game.players[0].hand[0].cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})        
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0})
        game.play_move({"username": "a", "move_type": "SELECT_OPPONENT"})
        self.assertEqual(game.opponent().hit_points, game.opponent().max_hit_points - game.players[0].in_play[0].power_with_tokens(game.players[0]))

    def test_wind_of_mercury(self):
        """
            Test add_fast to a mob with Wind of Mercury
        """

        deck1 = ["Stone Elemental", "Wind of Mercury"]
        deck2 = []
        game = self.game_for_decks([deck1, deck2])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})    
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0})
        game.play_move({"username": "a", "move_type": "SELECT_OPPONENT"})
        self.assertEqual(game.opponent().hit_points, game.opponent().max_hit_points)            
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0})
        game.play_move({"username": "a", "move_type": "SELECT_OPPONENT"})
        self.assertEqual(game.opponent().hit_points, game.opponent().max_hit_points - game.players[0].in_play[0].power_with_tokens(game.players[0]))

    def test_ambush_cant_select(self):
        """
            Test mob can't be selected if it has Ambush but not mobs to attack
        """

        deck1 = ["Tame-ish Sabretooth"]
        deck2 = []
        game = self.game_for_decks([deck1, deck2])
        game.players[0].mana += game.players[0].hand[0].cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})    
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0})
        self.assertEqual(game.players[0].selected_mob(), None)

    def test_tameish_sabretooth(self):
        """
            Test add_ambush effect of Tame-ish Sabretooth
        """

        deck1 = ["Stone Elemental"]
        deck2 = ["Tame-ish Sabretooth"]
        game = self.game_for_decks([deck1, deck2])
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})    
        game.play_move({"username": "a", "move_type": "END_TURN"})
        for card in game.players[1].hand:
            game.players[1].mana += card.cost
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 1})    
        print("doing test select")
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 1})    
        self.assertEqual(game.opponent().can_be_clicked, False)
        self.assertEqual(game.opponent().in_play[0].can_be_clicked, True)

    def test_flock_of_bats(self):
        """
            Test allow_defend_response effect of Flock of Bats
        """

        deck1 = ["Flock of Bats"]
        deck2 = ["OG Vamp"]
        game = self.game_for_decks([deck1, deck2])
        for card in game.players[0].hand:
            game.players[0].mana += card.cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})    
        game.play_move({"username": "a", "move_type": "END_TURN"})
        for card in game.players[1].hand:
            game.players[1].mana += card.cost
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 1})    
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 1})
        game.play_move({"username": "b", "move_type": "SELECT_OPPONENT"})
        self.assertEqual(game.players[0].username, game.current_player().username)

    def test_trickster(self):
        """
            Test draw_on_deal_damage effect of Trickster
        """

        deck1 = ["Trickster", "Trickster", "Trickster", "Trickster", "Trickster", "Trickster"]
        deck2 = []
        game = self.game_for_decks([deck1, deck2])
        game.players[0].mana += game.players[0].hand[0].cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})    
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 0})
        hand_size = len(game.players[0].hand)
        game.play_move({"username": "a", "move_type": "SELECT_OPPONENT"})
        self.assertEqual(hand_size + 1, len(game.players[0].hand))

    def test_stomp_shield(self):
        """
            Test Taunted Bear Fast and Stomp effects.
        """
        game = self.game_for_decks([["Riftwalker Djinn"], ["Taunted Bear"]])
        game.players[0].mana += game.players[0].hand[0].cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 1})
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 1})
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 0})
        self.assertEqual(game.opponent().hit_points, 30)

    def test_quickster_conjure_vs_attack(self):
        """
            Test Quickster can use Conjure effect to be cast as an instant
        """
        game = self.game_for_decks([["Quickster"], ["Taunted Bear"]])
        game.players[0].mana += game.players[0].hand[0].cost
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.players[1].mana += game.players[1].hand[0].cost
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 1})
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 1})
        game.play_move({"username": "b", "move_type": "SELECT_OPPONENT"})
        self.assertEqual(game.current_player().username, game.players[0].username)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        self.assertEqual(len(game.players[0].in_play), 1)

    def test_disappear_effect(self):
        """
            Test Tame Time is removed from the game when cast because of disappear 
        """
        game = self.game_for_decks([["Tame Time"], []])
        game.players[0].mana += game.players[0].hand[0].cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        self.assertEqual(len(game.current_player().in_play), 0)
        self.assertEqual(len(game.current_player().hand), 0)

    def test_bow_starts_in_play(self):
        """
            Test one Bow gets put into play on game starts
        """
        game = self.game_for_decks([["Bow", "Bow", "Bow", "Bow", "Bow", "Bow", "Bow"], ["Bow", "Bow", "Bow", "Bow", "Bow", "Bow", "Bow"]])
        self.assertEqual(len(game.current_player().artifacts), 1)
        self.assertEqual(len(game.opponent().artifacts), 1)

    def test_brarium_reduces_draw_and_makes(self):
        """
            Test one Bow gets put into play on game starts
        """
        game = self.game_for_decks([["Brarium", "Stone Elemental", "Stone Elemental", "Stone Elemental", "Stone Elemental", "Stone Elemental", "Stone Elemental"], []])
        game.players[0].mana += game.players[0].hand[0].cost
        self.assertEqual(len(game.current_player().hand), 4)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        self.assertEqual(len(game.current_player().hand), 3)
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "END_TURN"})
        self.assertEqual(len(game.current_player().hand), 3)
        self.assertEqual(len(game.current_player().card_choice_info["cards"]), 3)

    def test_mana_coffin_store_and_decost_effects(self):
        """
            Test one Mana Coffin reduces the cost of a card
        """
        game = self.game_for_decks([["Mana Coffin", "Stone Elemental"], []])
        self.assertEqual(game.players[0].hand[1].cost, 1)
        game.players[0].mana += game.players[0].hand[0].cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "SELECT_ARTIFACT", "card": 0})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1})
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "END_TURN"})
        self.assertEqual(len(game.current_player().hand), 1)
        self.assertEqual(game.players[0].hand[0].cost, 0)

    def test_restrict_effect_targets_min_cost_effect(self):
        """
            Test a spell with restrict_effect_targets_min_cost can't be selected without a valid target, but can with a valid one.
        """
        game = self.game_for_decks([["Stone Elemental", "Sabotage", "Riftwalker Djinn"], []])
        game.players[0].mana += game.players[0].hand[0].cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.players[0].mana += game.players[0].hand[0].cost
        game.players[0].mana += game.players[0].hand[1].cost
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1})
        self.assertEqual(game.players[0].selected_spell(), None)
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 2})
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1})
        self.assertEqual(game.players[0].selected_spell(), game.players[0].hand[0])
        self.assertEqual(len(game.current_player().in_play), 2)
        game.play_move({"username": "a", "move_type": "SELECT_MOB", "card": 2})
        self.assertEqual(len(game.current_player().in_play), 1)

    def test_restrict_effect_targets_mob_with_guard_effect(self):
        """
        """
        game = self.game_for_decks([["Air Elemental"], ["Sniper Elf"]])
        for x in range(0,6):
            game.play_move({"username": "a", "move_type": "END_TURN"})
            game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 1})
        self.assertEqual(game.players[1].selected_spell(), game.players[1].hand[0])

    def test_restrict_effect_targets_mob_with_guard_effect_no_target(self):
        """
        """
        game = self.game_for_decks([["Stone Elemental"], ["Sniper Elf"]])
        for x in range(0,5):
            game.play_move({"username": "a", "move_type": "END_TURN"})
            game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 1})
        self.assertEqual(game.players[1].selected_spell(), None)

    def test_restrict_effect_targets_mob_with_power_effect(self):
        """
        """
        game = self.game_for_decks([["Ultrachaun"], ["Dragonslayer Elf"]])
        for x in range(0,6):
            game.play_move({"username": "a", "move_type": "END_TURN"})
            game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 1})
        self.assertEqual(game.players[1].selected_spell(), game.players[1].hand[0])
        game.play_move({"username": "b", "move_type": "PLAY_CARD_IN_HAND", "card": 1})
        self.assertEqual(len(game.players[0].in_play), 1)
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 0})
        self.assertEqual(len(game.players[0].in_play), 0)

    def test_restrict_effect_targets_mob_with_power_effect_no_target(self):
        """
        """
        game = self.game_for_decks([["Stone Elemental"], ["Dragonslayer Elf"]])
        for x in range(0,6):
            game.play_move({"username": "a", "move_type": "END_TURN"})
            game.play_move({"username": "b", "move_type": "END_TURN"})
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 1})
        self.assertEqual(game.players[1].selected_spell(), None)

    def test_redirect_mob_spell_effect(self):
        game = self.game_for_decks([["Stone Elemental", "Send Minion"], ["Mayor's Brandy"]])
        game.players[0].mana += game.players[0].hand[1].cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 2})
        game.play_move({"username": "b", "move_type": "SELECT_MOB", "card": 0})
        self.assertEqual(len(game.stack), 1)
        game.play_move({"username": "a", "move_type": "SELECT_CARD_IN_HAND", "card": 1})
        game.play_move({"username": "a", "move_type": "SELECT_STACK_SPELL", "card": 2})
        self.assertEqual(len(game.opponent().in_play), 2)
        self.assertEqual(game.opponent().in_play[1].power_with_tokens(game.opponent()), 4)

    def test_redirect_mob_spell_effect_restricted(self):
        game = self.game_for_decks([["Stone Elemental", "Send Minion"], ["Zap"]])
        game.players[0].mana += game.players[0].hand[1].cost
        game.play_move({"username": "a", "move_type": "PLAY_CARD_IN_HAND", "card": 0})
        game.play_move({"username": "a", "move_type": "END_TURN"})
        game.play_move({"username": "b", "move_type": "SELECT_CARD_IN_HAND", "card": 2})
        game.play_move({"username": "b", "move_type": "SELECT_OPPONENT"})
        self.assertEqual(len(game.stack), 0)
