import * as PIXI from 'pixi.js'
import { GlowFilter, OutlineFilter } from 'pixi-filters';
import { Card } from '../components/Card.js';
import * as Constants from '../Constants.js';


export class ButtonPicker {

    constructor(x, y, labelText, labels, clickFunction) {
        let container = new PIXI.Container();
        this.container = container;
        container.position.x = x;
        container.position.y = y;
        let effectsLabel = new PIXI.Text(labelText, {fontFamily : Constants.defaultFontFamily, fontSize: Constants.h2FontSize, fill : Constants.blackColor});
        container.addChild(effectsLabel);      

        const buttonWidth = Card.cardWidth * 1.25;
        const buttonHeight = 40;
        let positionX = Constants.padding + buttonWidth / 2;
        let positionY = -buttonHeight / 2;

        let index = 0;
        this.buttons = [];
        var self = this;
        for (let label of labels) {
            let buttonTitle = label;
            let b = Card.button(
                buttonTitle, 
                Constants.brownColor, 
                Constants.whiteColor, 
                positionX, 
                positionY,
                function() {
                    for (let button of self.buttons) {
                        button.background.filters = [];
                        button.background.tint = Constants.darkGrayColor;
                    }
                    this.filters = [
                        new OutlineFilter(1, Constants.blackColor), 
                        new GlowFilter({ innerStrength: 0, outerStrength: 2, color: Constants.yellowColor})
                    ];
                    this.tint = Constants.blueColor;
                    clickFunction(label)
                },
                null,
                buttonWidth
            );
            this.container.addChild(b);
            this.buttons.push(b);
            index += 1;
            positionX += buttonWidth + Constants.padding * 2;
            if (index > 1 && index % 4 == 0) {
                positionX = Constants.padding + buttonWidth / 2;
                positionY += buttonHeight + Constants.padding * 4;
            }
        }
    }

}