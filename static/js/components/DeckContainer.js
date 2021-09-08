import * as PIXI from 'pixi.js'
import { Card } from './Card.js';
import * as Constants from './constants.js';


export class DeckContainer {

	constructor(pixiUX, deck, allCards, x, y) {
        this.allCards = allCards;
		this.cardSprites = [];
        this.deck = deck;
        this.pixiUX = pixiUX;
		this.background = Constants.background(x, y, Card.cardWidth * 1.25, .2)
    	this.pixiUX.app.stage.addChild(this.background)
    	this.position = this.background.position;
	}

	redisplayDeck() {
	    for (let sprite of this.cardSprites) {
	    	this.pixiUX.app.stage.removeChild(sprite);
	    }
		this.cards = Card.cardsForDeck(this.deck.cards, this.allCards);
		this.cards.sort((a, b) => (a.name < b.name) ? 1 : -1)
		this.cards.sort((a, b) => (a.cost > b.cost) ? 1 : -1)

		this.cardSprites = [];
		this.cards.forEach((card, i) => {
			this.addCardToContainer(card, i);
		});
		this.background.height = 18 * 30;
	}

	addCardToContainer(card, index) {
        let cardSprite = Card.spriteTopSliver(card, this.pixiUX, this.deck.cards[card.name]);
        cardSprite.interactive = true
        cardSprite.position.x = this.background.position.x;
        let cardHeight = 30;
        cardSprite.position.y = (cardHeight * index) + this.background.position.y;            
        this.pixiUX.app.stage.addChild(cardSprite);
        this.cardSprites.push(cardSprite)
	}

	hide() {
		this.background.alpha = 0;
    	for (let sprite of this.cardSprites) {
    		sprite.alpha = 0;
    	}
	}

	show() {
		this.background.alpha = 1;
    	for (let sprite of this.cardSprites) {
    		sprite.alpha = 1;
    	}		
	}

}
