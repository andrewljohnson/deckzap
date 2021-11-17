import * as PIXI from 'pixi.js'
import * as Constants from '../constants.js';
import { Card } from './Card.js';


export class CardPile {
	constructor(pixiUX, game, x, y, labelText, clickFunction) {
        let sprite = Card.spriteCardBack(null, game, pixiUX, true);
        sprite.interactive = true;
        sprite.buttonMode = true;
    	sprite.anchor.set(.5);
        sprite.position.x = x + sprite.width / 2;
        sprite.position.y = y + sprite.height / 2;
        pixiUX.app.stage.addChild(sprite);  
        this.pileSprite = sprite;
        sprite
            .on("click", clickFunction)
            .on("tap", clickFunction)

	    let labelOptions = {align: 'center', fontFamily : Constants.defaultFontFamily, fontSize: Constants.defaultFontSize, fill : Constants.blueColor};
		let label = new PIXI.Text(labelText, labelOptions);
    	label.anchor.set(.5);
    	label.position.x = sprite.position.x;
    	label.position.y = sprite.height / 2 + sprite.position.y + Constants.padding * 2;
    	this.label = label;
    	pixiUX.app.stage.addChild(label);
	}

	clear() {
		this.pileSprite.parent.removeChild(this.pileSprite);
		this.label.parent.removeChild(this.label);
	}
}