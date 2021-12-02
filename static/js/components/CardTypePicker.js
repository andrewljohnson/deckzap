import * as PIXI from 'pixi.js'
import { AdjustmentFilter, GlowFilter } from 'pixi-filters';
import { Card } from './Card.js';
import * as Constants from '../constants.js';


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
            let cardTypeDescription = "Mob\n\n• up to seven in play\n• mobs can attack players and other mobs\n• the simplest mob has just strength and hit points, but mobs can also have effects";
            if (this.id == "spell") {
                cardTypeDescription = "Spell\n\n• does one or more effects when cast\n• spell cards go to your discard pile immediately when cast and don't go into play like Mobs";
            }
            self.cardTypeDescriptionText = new PIXI.Text(cardTypeDescription, {fontFamily : Constants.defaultFontFamily, fontSize: Constants.h2FontSize, fill : Constants.darkGrayColor});
            self.cardTypeDescriptionText.position.x = spell.position.x - choiceWidth + Constants.padding;
            self.cardTypeDescriptionText.position.y = spell.position.y + choiceHeight;
            pixiUX.app.stage.addChild(self.cardTypeDescriptionText);

            clickFunction(this.id)
        };

        const choiceWidth = 45;
        const choiceHeight = 90;
        let spell = Constants.ovalSprite(
            pixiUX,
            "magick-trick.svg",
            "Spell",
            choiceWidth,
            choiceHeight,
            "spell",
            choiceWidth + Constants.padding * 2,
            yPosition + Constants.padding * 3 + choiceHeight/2,
            switchCardType     
        );
        let mob = Constants.ovalSprite(
            pixiUX,
            "robot-antennas.svg",
            "Mob",
            choiceWidth,
            choiceHeight,
            "mob",
            spell.position.x + choiceWidth * 2.5,
            spell.position.y,
            switchCardType    
        );


       this.spell = spell;
       this.mob = mob;
       this.position = this.spell.position;

    }

    select(cardType) {
        if (cardType == "mob") {
            this.mob.emit("click")
        } else {
            this.spell.emit("click")
        }

    }

}