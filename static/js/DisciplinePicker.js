import * as PIXI from 'pixi.js'
import { Card } from './Card.js';
import * as Constants from './constants.js';

import { GlowFilter } from 'pixi-filters';

export class DisciplinePicker {

	constructor(pixiUX, yPosition, clickFunction) {
        var self = this;
        const switchClass = function() {
        	for (let sprite of [magic, tech]) {
        		sprite.filters = [];
        	}
            this.filters = [new GlowFilter({ innerStrength: 1, outerStrength: 1, color: Constants.blueColor})];

			if (self.disciplineDescriptionText) {
				self.disciplineDescriptionText.parent.removeChild(self.disciplineDescriptionText);
				self.disciplineDescriptionText = null;
			}
			let disciplineDescription = "• 30 card deck\n• more mana each turn\n• draw one card a turn";
			if (this.id == "tech") {
				disciplineDescription = "• 15 card deck\n• 3 mana each turn\n• new hand each turn";
			}
	        self.disciplineDescriptionText = new PIXI.Text(disciplineDescription, {fontFamily : Constants.defaultFontFamily, fontSize: Constants.defaultFontSize, fill : Constants.blackColor});
	        self.disciplineDescriptionText.position.x = tech.position.x + choiceWidth + Constants.padding * 2;
	        self.disciplineDescriptionText.position.y = tech.position.y - choiceHeight / 2;
	        pixiUX.app.stage.addChild(self.disciplineDescriptionText);

			clickFunction(this.id)
		};

	    const choiceWidth = 20;
	    const choiceHeight = 40;
	    let magic = Constants.ovalSprite(
			pixiUX,
			"wizard-face.svg",
			"Magic",
			choiceWidth,
			choiceHeight,
			"magic",
			choiceWidth + Constants.padding * 2,
			yPosition + Constants.padding * 3 + choiceHeight/2,
			switchClass	
	    );

	    let tech = Constants.ovalSprite(
			pixiUX,
			"robot-antennas.svg",
			"Tech",
			choiceWidth,
			choiceHeight,
			"tech",
			magic.position.x + choiceWidth * 2.5,
			magic.position.y,
			switchClass 	
	    );

       this.magic = magic;
       this.tech = tech;
       this.position = this.magic.position;

	}

	select(discipline) {
        if (discipline == "magic") {
	        this.magic.emit("click")
        } else {
	        this.tech.emit("click")
        }

	}
}