import * as PIXI from 'pixi.js'
import { Card } from './Card.js';
import { DeckContainer } from './DeckContainer.js';
import * as Constants from './constants.js';
import { SVGRasterizer } from './SVGRasterizer.js';


export class OpponentPicker {

	constructor(opponentDecks, allCards, containerID, deckID) {
		this.cardWidth = 7;
		let appWidth = Card.cardWidth * this.cardWidth + Constants.padding * this.cardWidth;
		let appHeight = Card.cardHeight * 3 + Constants.padding * 2;
		this.opponentDecks = opponentDecks;
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
			<a id=findMatchButton class="button button-top-right">Play</a> 
        	Choose Opponent
		`;
		titleH1.class = "title-with-button";
		controlsContainer.appendChild(titleH1);

		this.opponentSelector = this.addOpponentSelector(controlsContainer, deckID);
		this.updateOpponentDescription();

		this.deckSelector = this.addDeckSelector(controlsContainer, deckID);
		this.updateDeckDescription(controlsContainer);
		
		this.updateFindMatchButton(deckID);
	}

	addOpponentSelector(controlsContainer, deckID) {
		let select = document.createElement("select");
		select.name = "opponents";
		select.id = "opponents";
		const humanIndex = 2;
		select.onchange = () => {
			this.updateOpponentDescription();
			if (this.deckContainer) {
				if (select.value == humanIndex) {
					this.deckContainerApp.app.stage.alpha = 0;
				} else {
					this.deckContainerApp.app.stage.alpha = 1;
				}				
			}
			if (select.value == humanIndex) {
				this.deckTitle.innerHTML = null
				this.deckDescription.style.opacity = 0;
				this.deckSelector.style.opacity = 0;
			} else {
				this.deckTitle.innerHTML = "Opponent's Deck";
				this.deckDescription.style.opacity = 1;
				this.deckSelector.style.opacity = 1;
			}				
			this.updateFindMatchButton(deckID);
		};

		this.opponents = [
			{"id": "aggro_bot", "name": "Aggro Bot", "description": "A pretty bad bot that always goes face."},
			{"id": "random_bot", "name": "Random Bot", "description": "A bot that moves 100% at random."},
			{"id": "human", "name": "Human", "description": "Find a match with a human.<br/><br/>Invite a buddy to play, or you won't get a match."}
		];

		let index = 0
		for (let opponent of this.opponents) {
			let option = document.createElement("option");
			select.appendChild(option)
			option.innerHTML = `${opponent.name}`;
			option.value = index;
			index += 1;			
		}
		controlsContainer.appendChild(select);
		this.opponentDescription = document.createElement("p");
		this.opponentDescription.style.color = "gray";
		controlsContainer.appendChild(this.opponentDescription);

		return select;		
	}

	updateOpponentDescription() {
		const index = this.opponentSelector.value;
		this.opponentDescription.innerHTML = this.opponents[index].description;
	}

	addDeckSelector(controlsContainer, deckID) {
		this.deckTitle = document.createElement("h2");
		this.deckTitle.innerHTML = `Opponent's Deck`;
		controlsContainer.appendChild(this.deckTitle);

		let select = document.createElement("select");
		select.name = "decks";
		select.id = "decks";
		select.onchange = () => {
			this.updateDeckDescription(controlsContainer);
			this.updateFindMatchButton(deckID);
		};

		let option = document.createElement("option");
		select.appendChild(option)
		option.innerHTML = "Random";
		option.value = 0;
		let index = 1
		for (let deck of this.opponentDecks) {
			let option = document.createElement("option");
			select.appendChild(option)
			option.innerHTML = `${deck.name} (${deck.race})`;
			option.value = index;
			index += 1;			
		} 

		controlsContainer.appendChild(select);
		this.deckDescription = document.createElement("p");
		this.deckDescription.style.color = "gray";
		controlsContainer.appendChild(this.deckDescription);

		return select;		
	}

	// todo use identifier like the_coven
	updateFindMatchButton(deckID) {
		let href = null
		if (this.opponents[this.opponentSelector.value].id == "human") {
			href = `/play/pvp?deck_id=${deckID}`;
		} else if (this.deckSelector.value == 0) {
			href = `/play/pvai?ai=${this.opponents[this.opponentSelector.value].id}&deck_id=${deckID}`;
		} else {
			href = `/play/pvai?ai=${this.opponents[this.opponentSelector.value].id}&opponent_deck_id=${this.opponentDecks[this.deckSelector.value-1].url}&deck_id=${deckID}`;			
		}
		document.getElementById("findMatchButton").onclick = () => {
			this.deckSelector.selectedIndex = -1;
			this.opponentSelector.selectedIndex = -1;
			window.location.href = href;		
		}
		//document.getElementById("findMatchButton").href = href;
	}

	updateDeckDescription(controlsContainer) {
		const index = this.deckSelector.value;
		this.deckDescription.innerHTML = null
		if (this.deckContainer) {
			this.deckContainer.parentElement.removeChild(this.deckContainer);
		}
		if (index == 0) {
			this.deckDescription.innerHTML = "The bot will play a random deck."
			this.deckContainer = null;
		} else {
			let deckContainerID = "deckContainer";
			this.deckContainer = document.createElement("div");
			this.deckContainer.id = deckContainerID;
			controlsContainer.appendChild(this.deckContainer);
			this.deckContainerApp = new DeckContainer(this.opponentDecks[index-1], this.allCards, deckContainerID);
			this.deckContainerApp.redisplayDeck();

		}
	}

}
