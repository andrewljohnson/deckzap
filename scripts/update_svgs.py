"""
	Add height and width attributes to SVGs because pixi.js needs them.
"""

import os
import xml.dom.minidom

directory = './static/images/card-art/'

def resize_svg(full_path):
	doc = xml.dom.minidom.parse(full_path)
	svg = doc.getElementsByTagName('svg')[0]
	svg.attributes['height'] = '192'
	svg.attributes['width'] = '192'
	with open(full_path, 'w') as file:
		file.write(doc.toprettyxml())
	# minidom adds an xml tag that breaks the svg
	with open(full_path, 'r') as fin:
		data = fin.readlines()[1:]
		new_data = []
		for line in data:
			line = line.replace('\t', '')
			line = line.replace('\n', '')
			line = line.replace('\r', '')	
			new_data.append(line)		
	with open(full_path, 'w') as fout:
		fout.writelines(new_data)

for filename in os.listdir(directory):
	full_path = os.path.join(directory, filename)
	if filename.endswith('svg'):
		resize_svg(full_path)