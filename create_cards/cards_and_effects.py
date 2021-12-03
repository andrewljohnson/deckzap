import json
import math
import os
import sys


class CardInfo:
   def __init__(self, name, image, cost, card_type, effects):
      self.name = name
      self.image = image
      self.cost = cost
      self.card_type = card_type.id
      self.effects = effects

   def as_dict(self):
      return {
         "name": self.name,
         "image": self.image,
         "cost": self.cost,
         "card_type": self.card_type,
         "effects": self.effects,
      }


class CardInfoMob(CardInfo):
   def __init__(self, name, image, cost, card_type, strength, hit_points, effects):
      super().__init__(name, image, cost, card_type, effects)
      self.strength = strength
      self.hit_points = hit_points

   def as_dict(self):
      info = super().as_dict()
      info["strength"] = self.strength
      info["hit_points"] = self.hit_points
      return info


class CardType:
   def __init__(self, card_type_id, name):
      self.id = card_type_id
      self.name = name

   def as_dict(self):
      return {
         "id": self.id,
         "name": self.name
      }


class EffectType:
   def __init__(self, effect_type_id, name, description):
      self.id = effect_type_id
      self.name = name
      self.description = description

   def as_dict(self):
      return {
         "description": self.description,
         "id": self.id,
         "name": self.name,
      }

class TargetType:
   def __init__(self, target_type_id, name, description):
      self.id = target_type_id
      self.name = name
      self.description = description

   def as_dict(self):
      return {
         "description": self.description,
         "id": self.id,
         "name": self.name
      }


def card_types(as_dicts=False):
   all_card_types = {
      "mob": CardType("mob", "Mob"),
      "spell": CardType("spell", "Spell")
   }
   if as_dicts:
      return dictify(all_card_types)
   return all_card_types

 
def effect_types(as_dicts=False):
   all_effect_types = {
      "after_deals_damage": EffectType("after_deals_damage", "After This Deals Damage", "after it deals damage"),
      "before_is_damaged": EffectType("before_is_damaged", "Before This is Damaged", None),
      "enters_play": EffectType("enters_play", "Enters Play", "When this enters play"),
      "select_mob_target": EffectType("select_mob_target", "When Selecting a Target", None), 
      "mob_changes_zones": EffectType("mob_changes_zones", "Mob Changes Zones", None),
      "spell": EffectType("spell", "Spell", None),
      "play_friendly_mob": EffectType("play_friendly_mob", "Play Friendly Mob", "When you play a mob")
   }
   if as_dicts:
      return dictify(all_effect_types)
   return all_effect_types


def target_types(as_dicts=False): 
   all_target_types = {
      "any": TargetType("any", "Any Player or Mob", "any target"),
      "enemy_mobs": TargetType("enemy_mobs", "All Enemy Mobs", "all enemy mobs"),
      "enemy_mob": TargetType("enemy_mob", "Enemy Mob", "an enemy mob"),
      "friendly_mob": TargetType("friendly_mob", "Friendly Mob", "a friendly mob"),
      "mob": TargetType("mob", "Mob", "a mob"),
      "opponent": TargetType("opponent", "Opponent", "your opponent"),
      "friendly_mob_random": TargetType("friendly_mob_random", "Friendly Mob (random)", "a random friendly mob"),
      "enemy_mob_random": TargetType("enemy_mob_random", "Enemy Mob (random)", "a random enemy mob"),
      "player": TargetType("player", "Player", "Target player"),
      "self": TargetType("self", "Self", "yourself")
   }
   if as_dicts:
      return dictify(all_target_types)
   return all_target_types


def dictify(dict_of_objects):
   dict_of_dicts = {}
   for i, k in dict_of_objects.items():
      dict_of_dicts[i] = k.as_dict()
   return dict_of_dicts


class Effects:
   """
      Each Effects def returns a dict, except the all def which returns a list of them all.
   """

   @staticmethod
   def ambush():
      return {
         "id": "ambush",
         "name": "Ambush",
         "description": "Ambush",
         "description_expanded": "Ambush mobs may attack other mobs the turn they come into play (or switch sides).",
         "effect_type": effect_types()["mob_changes_zones"].id,
         "legal_card_type_ids": [card_types()["mob"].id],
         "power_points": 1,
      }      

   @staticmethod
   def damage(card_type_id, amount, effect_type, target_type, ai_target_type_ids=None):
      if effect_type.description != None:
         description = f"{effect_type.description}, deal {amount} damage to {target_type.description}."
      else:
         description = f"Deal {amount} damage to {target_type.description}."

      return {
         "ai_target_types": ai_target_type_ids,
         "amount": amount,
         "effect_type": effect_type.id,
         "description": description,
         "legal_card_type_ids": [key for key, value in card_types().items()],
         "legal_effect_types": Effects.effect_types_for_card_type_id(card_type_id),
         "legal_target_types": [{"id": value.id, "name": value.name} for key, value in target_types().items()],
         "id": "damage",
         "name": "Damage",
         "power_points": Effects.damage_power_points(amount, target_type), 
         "target_type": target_type.id
      }

   def damage_power_points(amount, target_type):
      points = None
      if target_type.id == "opponent":
         points = amount / 2
      elif target_type.id == "self":
         points = -amount / 2
      elif target_type.id == "player":
         points = amount / 2 + 1
      elif target_type.id == "friendly_mob":
         points = -amount / 2 * 2
      elif target_type.id == "any":
         points = amount + 1
      elif target_type.id == "enemy_mob":
         points = amount
      elif target_type.id == "friendly_mob_random":
         points = -amount
      elif target_type.id == "enemy_mob_random":
         points = amount
      elif target_type.id == "mob":
         points = amount + 1 
      elif target_type.id == "friendly_mobs":
         points = -amount * 2
      elif target_type.id == "all_mobs":
         points = amount * 2
      elif target_type.id == "enemy_mobs":
         points = amount * 3
      else:
         print(f"unsupported target_type {target_type.id} for damage effect")

      if amount >= 15:
         points *= 4
      elif amount >= 10:
         points *= 2
      elif amount >= 5:
         points += 2

      return points

   @staticmethod
   def effect_types_for_card_type_id(card_type_id):      
      if card_type_id == card_types()["mob"].id:
         return [
            {
               "id": effect_types()["enters_play"].id,
               "name": effect_types()["enters_play"].name,
            },
            {
               "id": effect_types()["play_friendly_mob"].id,
               "name": effect_types()["play_friendly_mob"].name,
            }
         ]
      else: # the other card_type_id is spell
         return [
            {
               "id": effect_types()["spell"].id,
               "name": effect_types()["spell"].name,
            }
         ]

   @staticmethod
   def discard_random(card_type_id, amount, effect_type, target_type, ai_target_type_ids=None):
      return {
         "ai_target_types": ai_target_type_ids,
         "amount": amount,
         "effect_type": effect_type.id,
         "description": Effects.description_for_cards_effect("discard", target_type, amount, effect_type, is_random=True),
         "legal_card_type_ids": [key for key, value in card_types().items()],
         "legal_effect_types": Effects.effect_types_for_card_type_id(card_type_id),
         "legal_target_types": [
            {"id": target_types()["opponent"].id, "name": target_types()["opponent"].name},
            {"id": target_types()["self"].id, "name": target_types()["self"].name},
            {"id": target_types()["player"].id, "name": target_types()["player"].name}
         ],
         "id": "discard_random",
         "name": "Discard Random",
         "target_type": target_type.id,
         "power_points": Effects.discard_power_points(amount, target_type), 
      }

   @staticmethod
   def discard_power_points(amount, target_type):
      """
         Returns the power_points for an effect that returns mobs to their owner's hand.
      """
      points = 0
      if target_type.id == "opponent":
         points = amount * 4
      elif target_type.id == "self":
         amount = min(amount, 2)
         points = -amount * 4
      elif target_type.id == "player":
         points = amount * 4 + 1
      else:
         print(f"unsupported target_type {target_type.id} for discard effect")

      if amount > 2:
         points *= 2

      return points

   @staticmethod
   def drain():
      effect_type = effect_types()["after_deals_damage"]
      return {
         "id": "drain",
         "name": "Drain",
         "description": "Drain",
         "description_expanded": f"Gain hit points equal to this mob's strength {effect_type.description}.",
         "effect_type": effect_type.id,
         "legal_card_type_ids": [card_types()["mob"].id],
         "power_points": 1,
      }

   @staticmethod
   def draw(card_type_id, amount, effect_type, target_type, ai_target_type_ids=None):
      return {
         "ai_target_types": ai_target_type_ids,
         "amount": amount,
         "effect_type": effect_type.id,
         "description": Effects.description_for_cards_effect("draw", target_type, amount, effect_type),
         "legal_card_type_ids": [key for key, value in card_types().items()],
         "legal_effect_types": Effects.effect_types_for_card_type_id(card_type_id),
         "legal_target_types": [
            {"id": target_types()["opponent"].id, "name": target_types()["opponent"].name},
            {"id": target_types()["self"].id, "name": target_types()["self"].name},
            {"id": target_types()["player"].id, "name": target_types()["player"].name}
         ],
         "id": "draw",
         "name": "Draw",
         "power_points": Effects.draw_power_points(amount, target_type), 
         "target_type": target_type.id,
      }

   @staticmethod
   def draw_power_points(amount, target_type):
      """
         Returns the power_points for an effect that returns mobs to their owner's hand.
      """
      if target_type.id == "opponent":
         amount = min(amount, 2)
         return -amount * 3
      elif target_type.id == "self":
         return amount * 3
      elif target_type.id == "player":
         return amount * 3 + 1
      else:
         print(f"unsupported target_type {target_type.id} for draw effect")

   @staticmethod
   def guard():
      return {
         "id": "guard",
         "name": "Guard",
         "description": "Guard",
         "description_expanded": "Guard mobs must be attacked before other enemies.",
         "effect_type": effect_types()["select_mob_target"].id,
         "legal_card_type_ids": [card_types()["mob"].id],
         "power_points": 1,
      }      

   @staticmethod
   def heal(card_type_id, amount, effect_type, target_type, ai_target_type_ids=None):
      if effect_type.description != None:
         description = f"{effect_type.description}, heal {target_type.description} for {amount}."
      else:
         description = f"Heal {target_type.description} for {amount}."

      return {
         "ai_target_types": ai_target_type_ids,
         "amount": amount,
         "effect_type": effect_type.id,
         "description": description,
         "legal_card_type_ids": [key for key, value in card_types().items()],
         "legal_effect_types": Effects.effect_types_for_card_type_id(card_type_id),
         "legal_target_types": [{"id": value.id, "name": value.name} for key, value in target_types().items()],
         "id": "heal",
         "name": "Heal",
         "power_points": math.ceil(Effects.damage_power_points(amount, target_type) / 2), 
         "target_type": target_type.id
      }

   @staticmethod
   def kill(card_type_id, amount, effect_type, target_type, ai_target_type_ids=None):
      if effect_type.description != None:
         description = f"{effect_type.description}, kill {target_type.description}."
      else:
         description = f"Kill {target_type.description}."

      return {
         "ai_target_types": ai_target_type_ids,
         "effect_type": effect_type.id,
         "description": description,
         "legal_card_type_ids": [key for key, value in card_types().items()],
         "legal_effect_types": Effects.effect_types_for_card_type_id(card_type_id),
         "legal_target_types": [
            target_types()["mob"].as_dict(),
            target_types()["enemy_mob"].as_dict(),
            target_types()["friendly_mob"].as_dict()
         ],
         "id": "kill",
         "name": "Kill",
         "power_points": Effects.unwind_power_points(target_type) * 2, 
         "target_type": target_type.id
      }

   @staticmethod
   def make_from_deck(card_type_id, amount, effect_type, target_type, ai_target_type_ids=None):
      return {
         "ai_target_types": ai_target_type_ids,
         "effect_type": effect_type.id,
         "description": "Make a card from your deck.",
         "legal_card_type_ids": [key for key, value in card_types().items()],
         "legal_effect_types": Effects.effect_types_for_card_type_id(card_type_id),
         "legal_target_types": [
            target_types()["self"].as_dict(),
         ],
         "id": "make_from_deck",
         "name": "Make from Deck",
         "target_type": target_type.id,
         "power_points": 3,
      }

   @staticmethod
   def mana_increase_max(card_type_id, amount, effect_type, target_type, ai_target_type_ids=None):
      return {
         "ai_target_types": ai_target_type_ids,
         "amount": amount,
         "effect_type": effect_type.id,
         "description": f"You get {amount} extra mana on upcoming turns.",
         "legal_card_type_ids": [key for key, value in card_types().items()],
         "legal_effect_types": Effects.effect_types_for_card_type_id(card_type_id),
         "legal_target_types": [
            {"id": target_types()["self"].id, "name": target_types()["self"].name},
         ],
         "id": "mana_increase_max",
         "name": "Mana Increase Max",
         "power_points": amount * 5, 
         "target_type": target_type.id,
      }

   @staticmethod
   def shield():
      return {
         "id": "shield",
         "name": "Shield",
         "description": "Shield",
         "description_expanded": "Shielded mobs don't take damage the first time they get damaged.",
         "effect_type": effect_types()["before_is_damaged"].id,
         "legal_card_type_ids": [card_types()["mob"].id],
         "power_points": 3,
         "ui_info": {
            "effect_type": "glow",
            "outer_strength": 0,
            "inner_strength": 3,
            "color": "white"
         }
      }   

   @staticmethod
   def take_extra_turn(card_type_id, amount, effect_type, target_type, ai_target_type_ids=None):
      return {
         "ai_target_types": ai_target_type_ids,
         "effect_type": effect_type.id,
         "description": "Take an extra turn.",
         "legal_card_type_ids": [key for key, value in card_types().items()],
         "legal_effect_types": Effects.effect_types_for_card_type_id(card_type_id),
         "legal_target_types": [
            target_types()["self"].as_dict(),
         ],
         "id": "take_extra_turn",
         "name": "Take Extra Turn",
         "target_type": target_type.id,
         "power_points": 17,
      }

   @staticmethod
   def unwind(card_type_id, amount, effect_type, target_type, ai_target_type_ids=None):
      if effect_type.description != None:
         description = f"{effect_type.description}, return {target_type.description} to its owner's hand."
      else:
         description = f"Return {target_type.description} to its owner's hand."

      return {
         "ai_target_types": ai_target_type_ids,
         "effect_type": effect_type.id,
         "description": description,
         "legal_card_type_ids": [key for key, value in card_types().items()],
         "legal_effect_types": Effects.effect_types_for_card_type_id(card_type_id),
         "legal_target_types": [
            target_types()["mob"].as_dict(),
            target_types()["enemy_mob"].as_dict(),
            target_types()["friendly_mob"].as_dict()
         ],
         "id": "unwind",
         "name": "Unwind",
         "power_points": Effects.unwind_power_points(target_type), 
         "target_type": target_type.id
      }

   @staticmethod
   def unwind_power_points(target_type):
      """
         Returns the power_points for an effect that returns mobs to their owner's hand.
      """
      if target_type.id == "friendly_mob":
         return -4
      elif target_type.id == "enemy_mob":
         return 4
      elif target_type.id == "mob":
         return 5
      elif target_type.id == "friendly_mobs":
         return -20
      elif target_type.id == "all_mobs":
         return 12
      elif target_type.id == "enemy_mobs":
         return 20
      else:
         print(f"unsupported target_type {target_type.id} for unwind effect")

   @staticmethod
   def all():
      spell_effect_type = effect_types()["spell"]
      any_target_type = target_types()["any"]
      mob_target_type = target_types()["mob"]
      opponent_target_type = target_types()["self"]
      self_target_type = target_types()["self"]
      effects = [
         Effects.ambush(),
         Effects.damage(card_types()["spell"].id, 0, spell_effect_type, any_target_type, []),
         Effects.discard_random(card_types()["spell"].id, 1, spell_effect_type, opponent_target_type, [opponent_target_type.id]),
         Effects.drain(),
         Effects.draw(card_types()["spell"].id, 1, spell_effect_type, self_target_type, [self_target_type.id]),
         Effects.guard(),
         Effects.heal(card_types()["spell"].id, 0, spell_effect_type, any_target_type, []),
         Effects.make_from_deck(card_types()["spell"].id, None, spell_effect_type, self_target_type, []),
         Effects.mana_increase_max(card_types()["spell"].id, 1, spell_effect_type, self_target_type, []),
         Effects.shield(),         
         Effects.take_extra_turn(card_types()["spell"].id, None, spell_effect_type, self_target_type, []),
         Effects.unwind(card_types()["spell"].id, None, spell_effect_type, mob_target_type, [mob_target_type.id]),
      ]
      return effects

   @staticmethod
   def description_for_cards_effect(action_word, target_type, amount, effect_type, is_random=False):
      if target_type.id == "self":
         if amount == 1:
            description = f"{action_word.capitalize()} a card"
         else:
            description = f"{action_word.capitalize()} {amount} cards"
      elif target_type.id == "player": 
         if amount == 1: 
            description = f"Target player {action_word}s a card"
         else:
            description = f"Target player {action_word}s {amount} cards"
      else: #target_type.id == "opponent"
         if amount == 1:
            description = f"Your opponent {action_word}s a card"
         else:
            description = f"Your opponent {action_word}s {amount} cards"
      if is_random:
         description += " at random"
      if effect_type.description != None:
         description = description[0].lower() + description[1:]
         description = f"{effect_type.description}, {description}." 
      else:
         description += "."         
      return description   


class Cards:
   """
      The all def returns a list of dicts, one for each card in the game
   """

   def all():
      cards = [
         CardInfoMob(
               "Fairy", 
               "fairy.svg",
               1,
               card_types()["mob"],
               1,
               1,
               [
                  Effects.shield()
               ]
         ),
         CardInfoMob(
               "Cat", 
               "cat.svg",
               1,
               card_types()["mob"],
               2,
               1,
               []
         ),
         CardInfoMob(
               "Scorpion", 
               "scorpion.svg",
               2,
               card_types()["mob"],
               2,
               2,
               [
                  Effects.ambush()
               ]
         ),
         CardInfoMob(
               "Hound", 
               "labrador-head.svg",
               2,
               card_types()["mob"],
               3,
               2,
               []
         ),
         CardInfoMob(
               "Vampire", 
               "vampire-dracula.svg",
               3,
               card_types()["mob"],
               3,
               4,
               [
                  Effects.drain()
               ]
         ),
         CardInfoMob(
               "Mammoth", 
               "mammoth.svg",
               3,
               card_types()["mob"],
               4,
               3,
               []
         ),
         CardInfoMob(
               "Guard-goyle", 
               "gargoyle.svg",
               4,
               card_types()["mob"],
               3,
               5,
               [
                  Effects.guard()
               ]
         ),
         CardInfoMob(
               "Demon", 
               "fanged-skull.svg",
               4,
               card_types()["mob"],
               5,
               4,
               []
         ),
         CardInfoMob(
               "Troll", 
               "troll.svg",
               5,
               card_types()["mob"],
               6,
               5,
               []
         ),
         CardInfoMob(
               "Ogre", 
               "ogre.svg",
               6,
               card_types()["mob"],
               7,
               6,
               []
         ),
         CardInfoMob(
               "Dragon", 
               "drakkar-dragon.svg",
               7,
               card_types()["mob"],
               8,
               7,
               []
         ),
         CardInfo(
               "Zap", 
               "lightning-trio.svg",
               2,
               card_types()["spell"],
               [
                  Effects.damage(
                     card_types()["spell"].id, 
                     3, 
                     effect_types()["spell"],
                     target_types()["any"], 
                     [target_types()["opponent"].id, target_types()["enemy_mob"].id]
                  )
               ]
         ),
         CardInfo(
               "Heal", 
               "monk-face.svg",
               1,
               card_types()["spell"],
               [
                  Effects.heal(
                     card_types()["spell"].id, 
                     3, 
                     effect_types()["spell"],
                     target_types()["any"], 
                     [target_types()["self"].id, target_types()["friendly_mob"].id]
                  )
               ]
         ),
         CardInfo(
               "Meditate", 
               "enlightenment.svg",
               1,
               card_types()["spell"],
               [
                  Effects.make_from_deck(
                     card_types()["spell"].id, 
                     None, 
                     effect_types()["spell"],
                     target_types()["self"], 
                     []
                  )
               ]
         ),
         CardInfo(
               "Unwind", 
               "acrobatic.svg",
               2,
               card_types()["spell"],
               [
                  Effects.unwind(
                     card_types()["spell"].id, 
                     1, 
                     effect_types()["spell"],
                     target_types()["mob"], 
                     [target_types()["enemy_mob"].id]
                  )
               ]
         ),
         CardInfo(
               "Think", 
               "think.svg",
               3,
               card_types()["spell"],
               [
                  Effects.draw(card_types()["spell"].id, 2, effect_types()["spell"], target_types()["self"], [])
               ]
         ),
         CardInfo(
               "Study the Masters", 
               "pianist.svg",
               2,
               card_types()["spell"],
               [
                  Effects.mana_increase_max(card_types()["spell"].id, 1, effect_types()["spell"], target_types()["self"], [])
               ]
         ),
         CardInfo(
               "Explode", 
               "wind-hole.svg",
               4,
               card_types()["spell"],
               [
                  Effects.damage(
                     card_types()["spell"].id, 
                     6, 
                     effect_types()["spell"],
                     target_types()["any"], 
                     [target_types()["opponent"].id, target_types()["enemy_mob"].id]
                  )
               ]
         ),
         CardInfo(
               "Rolling Flames", 
               "rolling-energy.svg",
               7,
               card_types()["spell"],
               [
                  Effects.damage(
                     card_types()["spell"].id, 
                     4, 
                     effect_types()["spell"],
                     target_types()["enemy_mobs"], 
                     []
                  )
               ]
         ),
         CardInfo(
               "Kill", 
               "deathcab.svg",
               5,
               card_types()["spell"],
               [
                  Effects.kill(
                     card_types()["spell"].id, 
                     1, 
                     effect_types()["spell"],
                     target_types()["mob"], 
                     [target_types()["enemy_mob"].id]
                  )
               ]
         ),
         CardInfo(
               "Tame Time", 
               "pocket-watch.svg",
               8,
               card_types()["spell"],
               [
                  Effects.take_extra_turn(card_types()["spell"].id, None, effect_types()["spell"], target_types()["self"], [])
               ]
         ),
         CardInfo(
               "Daze", 
               "diamonds-smile.svg",
               3,
               card_types()["spell"],
               [
                  Effects.discard_random(
                     card_types()["spell"].id, 
                     2, 
                     effect_types()["spell"], 
                     target_types()["opponent"],
                     [],
                  ),                  
               ]
         ),
         CardInfo(
               "Inner Fire", 
               "burning-passion.svg",
               0,
               card_types()["spell"],
               [
                  Effects.damage(
                     card_types()["spell"].id, 
                     4, 
                     effect_types()["spell"],
                     target_types()["any"], 
                     [target_types()["opponent"].id, target_types()["enemy_mob"].id]
                  ),
                  Effects.discard_random(
                     card_types()["spell"].id, 
                     1, 
                     effect_types()["spell"], 
                     target_types()["self"],
                     [],
                  ),                  
               ]
         ),
         CardInfoMob(
               "LionKin", 
               "lion.svg",
               2,
               card_types()["mob"],
               3,
               3,
               [
                  Effects.guard(),                  
               ]
         ),
         CardInfoMob(
               "Riftwalker Djinn", 
               "djinn.svg",
               5,
               card_types()["mob"],
               3,
               2,
               [
                  Effects.ambush(),                  
                  Effects.drain(),                  
                  Effects.guard(),                  
                  Effects.shield(),                  
               ]
         ),
         CardInfoMob(
               "Spouty Gas Ball", 
               "crumbling-ball.svg",
               2,
               card_types()["mob"],
               3,
               2,
               [
                  Effects.damage(
                     card_types()["mob"].id, 
                     1, 
                     effect_types()["play_friendly_mob"],
                     target_types()["enemy_mob_random"], 
                     None
                  )                  
               ]
         ),
      ]
      return [card_info.as_dict() for card_info in cards]
