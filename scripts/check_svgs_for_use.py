import os
  

directory = "../static/images/card-art/"
for filename in os.listdir(directory):
	if not filename.endswith(".svg"):
		continue
	found_usage = False

	with open('../battle_wizard/battle_wizard_cards.json') as f:
		if filename in  f.read(): 
			found_usage = True
	with open('../static/old_cards.json') as f:
		if filename in  f.read(): 
			found_usage = True

	# uncertainty.svg
	with open('../static/js/SVGRasterizer.js') as f:
		if filename in  f.read(): 
			found_usage = True

	# piercing-sword.svg, hearts.svg, amethyst.svg
	with open('../static/js/Card.js') as f:
		if filename in  f.read(): 
			found_usage = True

	# cyborg-face.svg, card-random.svg, suspicious.svg
	with open('../static/js/PlayerTypePicker.js') as f:
		if filename in  f.read(): 
			found_usage = True

	if not found_usage:
		print(f"{filename} is unused")