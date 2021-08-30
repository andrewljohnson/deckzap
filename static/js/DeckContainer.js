import * as PIXI from 'pixi.js'
import { Card } from './Card.js';
import * as Constants from './constants.js';
import { SVGRasterizer } from './SVGRasterizer.js';


export class DeckContainer {

	constructor(deck, allCards, containerID) {
		this.cardWidth = 7;
		let appWidth = Card.cardWidth * this.cardWidth + Constants.padding * this.cardWidth;
		let appHeight = Card.cardHeight * 3 + Constants.padding * 2;
		this.deck = deck;
		this.allCards = allCards;
        PIXI.settings.FILTER_RESOLUTION = window.devicePixelRatio || 1;
        this.app = new PIXI.Application({
            antialias: true,
            autoDensity: true,
            backgroundColor: Constants.whiteColor,
            height: appHeight,
            width: appWidth, 
            resolution: PIXI.settings.FILTER_RESOLUTION,
        });        
        this.rasterizer = new SVGRasterizer(this.app);

		let container = document.getElementById(containerID);
		let deckContainer = document.createElement("div");
		container.appendChild(deckContainer);
        deckContainer.appendChild(this.app.view);
        const background = new PIXI.Sprite.from(PIXI.Texture.WHITE);
        this.app.stage.addChild(background)
        Constants.roundRectangle(background)
        background.width = appWidth;
        background.height = appHeight;
        background.tint = Constants.blueColor;
	}

	redisplayDeck() {
		let spritesToRemove = [];
	    for (let sprite of this.app.stage.children) {
	    	if (sprite.card) {
	    		spritesToRemove.push(sprite)
	    	}
	    }
	    for (let sprite of spritesToRemove) {
	    	this.app.stage.removeChild(sprite);
	    }
		this.cards = [];

		for (let dcName in this.deck.cards) {
			for(let ac of this.allCards) {
				if (ac.name == dcName) {
					this.cards.push(ac);
				}
			}   
		}

        let loadingImages = this.rasterizer.loadCardImages(this.cards);
		let index = 0;
        this.app.loader.load(() => {
			for (let card of this.cards) {
				this.addCardToContainer(card, index);
				index += 1;
			}
            for (let sprite of this.app.stage.children) {
                if (sprite.card) {
                    sprite.interactive = true;
                }
            }
            this.app.loader.reset()
        });
	}

	addCardToContainer(card, index) {
		let pixiUX = this;
        let cardSprite = Card.sprite(card, pixiUX);
        cardSprite.position.x = (Card.cardWidth + Constants.padding) *  (index % this.cardWidth) + Card.cardWidth/2;
        cardSprite.position.y = Card.cardHeight/2 + (Card.cardHeight + 5) * Math.floor(index / this.cardWidth);            
        this.app.stage.addChild(cardSprite);
	}

}
