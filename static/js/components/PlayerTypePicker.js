import * as PIXI from 'pixi.js'
import { GlowFilter } from 'pixi-filters';
import * as Constants from '../constants.js';


export class PlayerTypePicker {

    constructor(pixiUX, x, y, clickFunction) {
        this.players = [
            {"id": "aggro_bot", "name": "Aggro\nBot", "image": "cyborg-face.svg", "description": "A pretty bad bot that always goes face."},
            {"id": "random_bot", "name": "Random\nBot", "image": "card-random.svg", "description": "A bot that moves 100% at random."},
            {"id": "pass_bot", "name": "Pass\nBot", "image": "aquarium.svg", "description": "A bot that always passes."},
            {"id": "human", "name": "Human", "image": "suspicious.svg", "description": "Find a match with a human.\nInvite a buddy to play, or you won't get a match."}
        ];

        var self = this;
        const switchPlayer = function() {
            for (let sprite of self.options) {
                sprite.filters = [];
            }
            this.filters = [new GlowFilter({ innerStrength: 1, outerStrength: 1, color: Constants.blueColor})];

            if (self.disciplineDescriptionText) {
                self.disciplineDescriptionText.parent.removeChild(self.disciplineDescriptionText);
                self.disciplineDescriptionText = null;
            }
            self.disciplineDescriptionText = new PIXI.Text(self.players[this.id].description, {fontFamily : Constants.defaultFontFamily, fontSize: Constants.h2FontSize, fill : Constants.darkGrayColor});
            self.disciplineDescriptionText.position.x = x;
            self.disciplineDescriptionText.position.y = this.position.y + 70;
            pixiUX.app.stage.addChild(self.disciplineDescriptionText);

            clickFunction(this.id)
            self.selectedIndex = this.id;
        };

        const choiceWidth = 45;
        const choiceHeight = 90;
           let index = 0;
           this.options = [];
        for (let player of this.players) {
            let option = Constants.ovalSprite(
                pixiUX,
                player.image,
                player.name,
                choiceWidth,
                choiceHeight,
                index,
                x + (choiceHeight + Constants.padding) * index + choiceWidth,
                y + Constants.padding * 3 + choiceHeight/2,
                switchPlayer    
            );
            this.options.push(option)
            index++;
        }
       this.position = this.options[0].position;

    }

    select(index) {
        this.options[index].emit("click")
        this.selectedIndex = index;
    }
}