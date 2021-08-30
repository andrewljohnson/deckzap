import * as PIXI from 'pixi.js'
import { Card } from './Card.js';
import * as Constants from './constants.js';
import { SVGRasterizer } from './SVGRasterizer.js';


export class DeckViewer {

	constructor(decks, allCards, containerID) {
		this.cardWidth = 7;
		let appWidth = Card.cardWidth * this.cardWidth + Constants.padding * this.cardWidth;
		let appHeight = Card.cardHeight * 3 + Constants.padding * 2;
		this.decks = decks;
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
		let controlsContainer = document.createElement("div");
		container.appendChild(controlsContainer);
		let titleH1 = document.createElement("h1");
		titleH1.innerHTML = `
			<a id=findMatchButton class="button button-top-right">Find Match</a> 
        	Choose Deck
		`;
		titleH1.class = "title-with-button";
		controlsContainer.appendChild(titleH1);

		let select = document.createElement("select");
		controlsContainer.appendChild(select);
		this.deckSelector = select;
		select.name = "decks";
		select.id = "decks";
		select.onchange = () => {
			this.redisplayDeck();
		};

		for (let deck of decks) {
			let option = document.createElement("option");
			select.appendChild(option)
			option.innerHTML = `${deck.name} (${deck.race})`;
			option.value = deck.id;
		}

		this.deckInfoDiv  = document.createElement("div");
		controlsContainer.appendChild(this.deckInfoDiv);

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
		document.getElementById("findMatchButton").href = `/choose_opponent/${this.deckSelector.value}`

		let chosenDeck = this.decks[this.deckSelector.value];

       	if (chosenDeck.race == "dwarf") {
            this.deckInfoDiv.innerHTML = 
                "<ul><li>three mana per turn</li><li>new hand of five cards each turn</li><li>15 card deck</li></ul>"
        } else {
            this.deckInfoDiv.innerHTML = 
                "<ul><li>get more mana each turn</li><li>start with 4 cards, draw a card per turn</li><li>30 card deck</li></ul>"          
        }


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

		for (let dcName in chosenDeck.cards) {
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