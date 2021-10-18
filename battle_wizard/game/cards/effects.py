import json


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
   def __init__(self, name, image, cost, card_type, power, toughness, effects):
      super().__init__(name, image, cost, card_type, effects)
      self.power = power
      self.toughness = toughness

   def as_dict(self):
      info = super().as_dict()
      info["power"] = self.power
      info["toughness"] = self.toughness
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
         "name": self.name
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


def damage_effect(amount, effect_type, target_type, ai_target_type_ids):
   if effect_type.description != None:
      description = f"{effect_type.description}, deal {amount} damage to {target_type.description}." 
   else:
      description = f"Deal {amount} damage to {target_type.description}."   
   return {
      "ai_target_types": ai_target_type_ids,
      "amount": amount,
      "effect_type": effect_type.id,
      "description": description,
      "name": "damage",
      "target_type": target_type.id
   }


def discard_random_effect(amount, effect_type, target_type):
   if amount == 1:
      description = "Discard a random card."
   else: 
      description = f"Discard {amount} random cards."
   return {
      "amount": amount,
      "effect_type": effect_type.id,
      "description": description,
      "name": "discard_random",
      "target_type": target_type.id
   }


def draw_effect(amount, effect_type, target_type):
   if target_type.id == "self":
      if amount == 1:
         description = "Draw a card."
      else:
         description = f"Draw {amount} cards."
   elif target_type.id == "player": 
      if amount == 1: 
         description = "Target player draws a card."
      else:
         description = f"Target player draws {amount} cards."
   else: #target_type.id == "opponent"
      if amount == 1:
         description = "Your opponent draws a card."
      else:
         description = f"Your opponent draws {amount} cards."
   return {
      "amount": amount,
      "effect_type": effect_type.id,
      "description": description,
      "name": "draw",
      "target_type": target_type.id,
   }


def dictify(dict_of_objects):
   dict_of_dicts = {}
   for i, k in dict_of_objects.items():
      dict_of_dicts[i] = k.as_dict()
   return dict_of_dicts


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
      "spell": EffectType("spell", "Spell", None),
      "play_friendly_mob": EffectType("play_friendly_mob", "Play Friendly Mob", "When you play a mob")
   }
   if as_dicts:
      return dictify(all_effect_types)
   return all_effect_types


def target_types(as_dicts=False): 
   all_target_types = {
      "any": TargetType("any", "Any Player or Mob", "any target"),
      "enemy_mob": TargetType("enemy_mob", "Enemy Mob", "an enemy mob"),
      "opponent": TargetType("opponent", "Opponent", "your opponent"),
      "opponents_mob_random": TargetType("opponents_mob_random", "Opponent's Mob (random)", "a random enemy mob"),
      "self": TargetType("self", "Self", "yourself")
   }
   if as_dicts:
      return dictify(all_target_types)
   return all_target_types


def effects(as_dicts=False):
   effects = [
      damage_effect(0, effect_types()["spell"], target_types()["any"], []),
      discard_random_effect(1, effect_types()["spell"], target_types()["any"]),
      draw_effect(1, effect_types()["spell"], target_types()["self"]),
   ]
   return effects


def card_infos():
   return [
      CardInfo(
            "Think", 
            "think.svg",
            4,
            card_types()["spell"],
            [
               draw_effect(3, effect_types()["spell"], target_types()["self"])
            ]
      ),
      CardInfo(
            "Inner Fire", 
            "burning-passion.svg",
            0,
            card_types()["spell"],
            [
               damage_effect(
                  4, 
                  effect_types()["spell"],
                  target_types()["any"], 
                  [target_types()["opponent"].id, target_types()["enemy_mob"].id]
               ),
               discard_random_effect(
                  1, 
                  effect_types()["spell"], 
                  target_types()["self"],
               ),                  
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
               damage_effect(
                  1, 
                  effect_types()["play_friendly_mob"],
                  target_types()["opponents_mob_random"], 
                  None
               )                  
            ]
      ),
      CardInfo(
            "Zap", 
            "lightning-trio.svg",
            2,
            card_types()["spell"],
            [
               damage_effect(
                  3, 
                  effect_types()["spell"],
                  target_types()["any"], 
                  [target_types()["opponent"].id, target_types()["enemy_mob"].id]
               )
            ]
      ),
   ]


info = {
   "cards": [card_info.as_dict() for card_info in card_infos()],
   "effects": effects(),
   "card_types": card_types(as_dicts=True),
   "effect_types": effect_types(as_dicts=True),
   "target_types": target_types(as_dicts=True)
}
print(json.dumps(info, indent=4, sort_keys=True))