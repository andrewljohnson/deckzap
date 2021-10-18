local DamageEffect(amount, effect_type, target_type, ai_target_type_ids) = {
   ai_target_types: ai_target_type_ids,
   amount: amount,
   effect_type: effect_type.id,
   description: 
      if "description" in effect_type 
      then '%s, deal %d damage to %s.' % [effect_type["description"], amount, target_type.description] 
      else 'Deal %d damage to %s.'% [amount, target_type.description],   
   name: "damage",
   target_type: target_type.id,
};

local DiscardRandomEffect(amount, effect_type, target_type_id) = {
   amount: amount,
   effect_type: effect_type.id,
   description: 
      if amount == 1 then 'Discard a random card.'
      else 'Discard %d random cards.' % [amount],
   name: "discard_random",
   target_type: target_type_id,
};

local DrawEffect(amount, effect_type, target_type_id) = {
   amount: amount,
   effect_type: effect_type.id,
   description: 
      if target_type_id == "self" then 
         if amount == 1 then 'Draw a card.'
         else 'Draw %d cards.' % [amount]
      else if target_type_id == "player" then 
         if amount == 1 then 'Target player draws a card.'
         else 'Target player draws %d cards.' % [amount]
      else if target_type_id == "opponent" then 
         if amount == 1 then 'Your opponent draws a card.'
         else 'Your opponent draws %d cards.' % [amount],
   name: "draw",
   target_type: target_type_id,
};

{  
   cards: [
      {
         "name": "Think",
         "image": "think.svg",
         "cost": 4,
         "card_type": $['card_types'].spell.id,
         "effects": [
            DrawEffect(
               3, 
               $['effect_types'].spell, 
               $['target_types'].self_player.id
            ),         
         ]
      },
      {
         "name": "Inner Fire",
         "image": "burning-passion.svg",
         "cost": 0,
         "card_type": $['card_types'].spell.id,
         "effects": [
            DamageEffect(
               4, 
               $['effect_types'].spell, 
               $['target_types'].any, 
               [  
                  $['target_types'].opponent.id, 
                  $['target_types'].enemy_mob.id
               ]
            ),         
            DiscardRandomEffect(
               1, 
               $['effect_types'].spell, 
               $['target_types'].self_player.id,
            ),         
         ]
      },
      {
         "name": "Spouty Gas Ball",
         "image": "crumbling-ball.svg",
         "cost": 2,
         "card_type": $['card_types'].mob.id,
         "power": 3,
         "toughness": 2,
         "effects": [
            DamageEffect(
               1, 
               $['effect_types'].play_friendly_mob, 
               $['target_types'].opponents_mob_random,
               null
            ),
         ]
      },
      {
         "name": "Zap",
         "image": "lightning-trio.svg",
         "cost": 2,
         "card_type": $['card_types'].spell.id,
         "effects": [
            DamageEffect(
               3, 
               $['effect_types'].spell, 
               $['target_types'].any, 
               [  
                  $['target_types'].opponent.id, 
                  $['target_types'].enemy_mob.id
               ]
            ),
         ]
      }
   ],
   effects: [
      DamageEffect(0, $['effect_types'].spell, $['target_types'].any, []),
      DiscardRandomEffect(1, $['effect_types'].spell, $['target_types'].any.id),
      DrawEffect(1, $['effect_types'].spell, $['target_types'].self_player.id),
   ],
   card_types: {
      mob: {
         id: "mob",
         name: "Mob",
      },
      spell: {
         id: "spell",
         name: "Spell",
      },
   },
   effect_types: {
      spell: {
         id: "spell",
         name: "Spell",
      },
      play_friendly_mob: {
         description: "When you play a mob",
         id: "play_friendly_mob",
         name: "Play Friendly Mob"
      }
   },
   target_types: {
      any: {
         description: "any target",
         id: "any",
         name: "Any Player or Mob",
      },
      enemy_mob: {
         description: "an enemy mob",
         id: "enemy_mob",
         name: "Enemy Mob",
      },
      opponent: {
         description: "your opponent",
         id: "opponent",
         name: "Opponent",
      },
      opponents_mob_random : {
         description: "a random enemy mob",
         id: "opponents_mob_random",
         name: "Opponent's Mob (random)"
      },
      self_player: {
         description: "yourself",
         id: "self",
         name: "Self",
      },
   },
}