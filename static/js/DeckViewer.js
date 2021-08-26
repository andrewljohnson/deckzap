import * as PIXI from 'pixi.js'

export class DeckViewer {

	constructor(deck, allCards, containerID) {
		this.deck = deck;
		this.allCards = allCards;
		this.containerID = containerID;

        PIXI.settings.FILTER_RESOLUTION = window.devicePixelRatio || 1;
        this.app = new PIXI.Application({
            autoDensity: true,
            height: 400, 
            width: 800, 
            resolution: PIXI.settings.FILTER_RESOLUTION,
        });        
        document.getElementById(containerID).appendChild(this.app.view);
	}

	redisplayDeck() {
		for (var dcName in this.deck["cards"]) {
			for(var ac of this.allCards) {
				if (ac.name == dcName) {
					this.addCardToContainer(ac);
				}
			}   
		}
	}

	addCardToContainer(card) {

	}

}
