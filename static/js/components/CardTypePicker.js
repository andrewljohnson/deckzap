import * as PIXI from 'pixi.js'
import { AdjustmentFilter, GlowFilter } from 'pixi-filters';
import { Card } from './Card.js';
import * as Constants from '../Constants.js';


export class CardTypePicker {

	constructor(pixiUX, yPosition, clickFunction) {
        var self = this;
        const switchCardType = function() {
        	for (let sprite of [spell, mob]) {
        		sprite.filters = [];
        		if (sprite != this) {
					sprite.filters = [new AdjustmentFilter({ alpha: .5})];
        		}
        	}
            this.filters = [new GlowFilter({ innerStrength: 1, outerStrength: 1, color: Constants.blueColor})];

			if (self.cardTypeDescriptionText) {
				self.cardTypeDescriptionText.parent.removeChild(self.cardTypeDescriptionText);
				self.cardTypeDescriptionText = null;
			}
			let cardTypeDescription = "Mob\n\n• up to seven in play\n• mobs can attack players and other mobs\n• the simplest mob has just power and hit points, but mobs can also have special effects";
			if (this.id == "spell") {
				cardTypeDescription = "Spell\n\n• does one or more effects when cast\n• spell cards go to your discard pile immediately when cast and don't go into play like Mobs";
			}
	        self.cardTypeDescriptionText = new PIXI.Text(cardTypeDescription, {fontFamily : Constants.defaultFontFamily, fontSize: Constants.h2FontSize, fill : Constants.darkGrayColor});
	        self.cardTypeDescriptionText.position.x = mob.position.x - choiceWidth + Constants.padding;
	        self.cardTypeDescriptionText.position.y = mob.position.y + choiceHeight;
	        pixiUX.app.stage.addChild(self.cardTypeDescriptionText);

			clickFunction(this.id)
		};

	    const choiceWidth = 45;
	    const choiceHeight = 90;
	    let mob = Constants.ovalSprite(
			pixiUX,
			"wizard-face.svg",
			"Mob",
			choiceWidth,
			choiceHeight,
			"mob",
			choiceWidth + Constants.padding * 2,
			yPosition + Constants.padding * 3 + choiceHeight/2,
			switchCardType	
	    );

	    let spell = Constants.ovalSprite(
			pixiUX,
			"robot-antennas.svg",
			"Spell",
			choiceWidth,
			choiceHeight,
			"spell",
			mob.position.x + choiceWidth * 2.5,
			mob.position.y,
			switchCardType 	
	    );

       this.mob = mob;
       this.spell = spell;
       this.position = this.mob.position;

	}

	select(cardType) {
        if (cardType == "mob") {
	        this.mob.emit("click")
        } else {
	        this.spell.emit("click")
        }

	}

}