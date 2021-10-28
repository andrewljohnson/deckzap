from cards_and_effects import *

# print all cards, effects, and types to a JSON file for use by the game
info = {
   "cards": Cards.all(),
   "effects": Effects.all(),
   "card_types": card_types(as_dicts=True),
   "effect_types": effect_types(as_dicts=True),
   "target_types": target_types(as_dicts=True)
}
dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, 'cards_and_effects.json')
with open(filename, 'w') as f:
   sys.stdout = f
   print(json.dumps(info, indent=4, sort_keys=True))
