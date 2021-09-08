"""
	Zap. An example player-created spell that deals 3 damage.

	Players can upload conforming pything files to create new cards at deckzap.com/create_card
"""


card = Card()

# required fields
card.name = "Zap"
# must be 0 or higher
card.cost = 2
# artifact, mob, or spell
card.card_type = "spell"
# magic or tech
card.discipline = "magic"
# an SVG reachable on the internet - it should be 512px square
card.image = "https://game-icons.net/icons/ffffff/000000/1x1/lorc/lightning-trio.svg"

# optional: text to appear on the card
card.description = "Deal 3 damage."

# optional: define Effects for spells, for mobs that enter play, and for other triggers
effect = Effect()
effect.effect_type = "spell",
effect.target_type = "any",

# both function_player and function_mob are required since the target_type is "any"
# these strings must correspond to defs in this file
effect.function_player = "zap_player"
effect.function_mob = "zap_mob"
card.effects = [effect]

# optional: help the AI play better by listing preferred targets
effect.ai_target_types = ["opponent", "opponents_mob"]
	
def zap_player(target, caster, target_controller, game):
	"""
	This is a method for effect.function_player, which are always passed a Card, Player, Player, and Game	
	"""
	damage_amount = 3 
    target_player.damage(damage_amount)
    log_lines = [
    	f"{caster.username} deals {damage_amount} damage to {target.username}."
    ]
    return log_lines

def zap_mob(target, caster, target_controller, game):
	"""
	This is a method for effect.function_mob, which are always passed a Card, Player, Player, and Game	
	"""
	damage_amount = 3 
	target_mob.deal_damage(damage_amount, target_controller, game)
    log_lines = [
    	f"{caster.username} deals {damage_amount} damage to {target.name}."
    ]
    return log_lines
