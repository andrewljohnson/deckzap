import * as PIXI from 'pixi.js'
import * as Constants from './constants.js';

import { GlowFilter } from 'pixi-filters';

export class DeckPicker {

	constructor(pixiUX, decks, allCards, yPosition, clickFunction, random=false) {
        var self = this;
        const switchDeck = function() {
        	for (let sprite of self.options) {
        		sprite.filters = [];
        	}
        	if (self.random) {
        		self.random.filters = [];
        	}
            this.filters = [new GlowFilter({ innerStrength: 1, outerStrength: 1, color: Constants.blueColor})];
			clickFunction(this.id)
			self.selectedIndex = this.id;
        };

		let index = 0;
		this.options = [];
	    const choiceWidth = 60;
	    const choiceHeight = 120;
		for (let deck of decks) {
			let firstCardName = Object.keys(deck.cards)[0]
			let firstCard;
			for (let card of allCards) {
				if (card.name == firstCardName) {
					firstCard = card;
				}
			}
	 		let option = Constants.ovalSprite(
				pixiUX,
				firstCard.image,
				`${deck.name}\n(${deck.discipline})`,
				choiceWidth,
				choiceHeight,
				index,
   				choiceWidth + Constants.padding * 2 + (choiceWidth + Constants.padding * 8) * index, 
	        	yPosition + Constants.padding * 3 + choiceHeight/2,
	        	switchDeck	
		    );			
           this.options.push(option)
	       index++;
		}
		if (random) {
		    let option = Constants.ovalSprite(
				pixiUX,
				"uncertainty.svg",
				`Random\nDeck`,
				choiceWidth,
				choiceHeight,
				index,
   				choiceWidth + Constants.padding * 2 + (choiceWidth + Constants.padding * 8) * index, 
	        	yPosition + Constants.padding * 3 + choiceHeight/2,
	        	switchDeck	
		    );	
		    this.random = option;		
		}
		this.position = this.options[0].position;
	}

	select(optionIndex) {
		this.options[optionIndex].emit("click")
		this.selectedIndex = optionIndex;
	}


	hide() {
    	for (let sprite of this.options) {
    		sprite.alpha = 0;
    	}
    	if (this.random) {
    		this.random.alpha = 0;
    	}
	}

	show() {
    	for (let sprite of this.options) {
    		sprite.alpha = 1;
    	}		
    	if (this.random) {
    		this.random.alpha = 1;
    	}
	}

}