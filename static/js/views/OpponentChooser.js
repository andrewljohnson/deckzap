import * as PIXI from 'pixi.js'
import * as Constants from '../Constants.js';
import { Card } from '../components/Card.js';
import { CardsContainer } from '../components/CardsContainer.js';
import { DeckContainer } from '../components/DeckContainer.js';
import { DeckPicker } from '../components/DeckPicker.js';
import { PlayerTypePicker } from '../components/PlayerTypePicker.js';
import { SVGRasterizer } from '../components/SVGRasterizer.js';


export class OpponentChooser {

	constructor(opponentDecks, allCards, containerID, deckID) {
		this.allCards = allCards;
		this.opponentDecks = opponentDecks;
		this.deckID = deckID;
		this.cardWidth = 7;
		Constants.setUpPIXIApp(this)
        	this.rasterizer = new SVGRasterizer(this.app);
		this.loadUX(containerID);
	}

	loadUX(containerID) {			
		let container = document.getElementById(containerID);
		container.appendChild(this.app.view);

		let background = Constants.background(0, 0, Card.cardWidth * (this.cardWidth-1), .1)
		background.tint = 0xEEEEEE;
		background.height = (Card.cardHeight) * 12
		this.app.stage.addChild(background);

	        let titleText = this.addTitle()
	        this.playerTypePicker = new PlayerTypePicker(this, Constants.padding, titleText.position.y + titleText.height + Constants.padding*3, playerIndex => {this.selectPlayer(playerIndex)} )
	        let subtitleText = this.addChooseDeckTitle();
	        this.deckPickerTitle = subtitleText;
	        this.deckPicker = new DeckPicker(this, this.opponentDecks, this.allCards, this.playerTypePicker.position.y + 140, deckIndex => {this.selectOpponentDeck(deckIndex)}, true);
		this.deckContainer = new DeckContainer(this, this.opponentDecks[0], this.allCards, this.app.renderer.width / this.app.renderer.resolution - Card.cardWidth* 3 - Constants.padding * 4, 90 );
	        this.playerTypePicker.select(0);
		this.deckPicker.select(this.deckPicker.options.length-1);
		this.addPlayButton();		
	}

	addTitle() {
		let title = "Choose Opponent";
	        let titleText = new PIXI.Text(title, {fontFamily : Constants.defaultFontFamily, fontSize: Constants.titleFontSize, fill : Constants.blackColor});
	        titleText.position.x = Constants.padding;
	        titleText.position.y = Constants.padding * 2.5;
	        this.app.stage.addChild(titleText);		
	        return titleText;
	}

	addChooseDeckTitle() {
		let title = "Opponent's Deck";
	        let titleText = new PIXI.Text(title, {fontFamily : Constants.defaultFontFamily, fontSize: Constants.h2FontSize, fill : Constants.blackColor});
	        titleText.position.x = Constants.padding;
	        titleText.position.y = this.playerTypePicker.position.y + 105;
	        this.app.stage.addChild(titleText);		
	        return titleText;
	}

	// todo use identifier like the_coven
	addPlayButton() {
	        const buttonWidth = Card.cardWidth * 1.25;
	        const buttonHeight = 40;
	        const buttonX = this.app.renderer.width / this.app.renderer.resolution - buttonWidth * 2;
	        let b = Card.button(
	                "Play", 
	                Constants.blueColor, 
	                Constants.whiteColor, 
	                buttonX, 
	                -buttonHeight + Constants.padding,
	                () => {
	                	let playerID = this.playerTypePicker.players[this.playerTypePicker.selectedIndex].id;
	                	let deckID = this.deckID;
						if (playerID == "human") {
							window.location.href = `/play/pvp?deck_id=${deckID}`;
						} else if (this.deckPicker.selectedIndex == this.opponentDecks.length) {
							window.location.href = `/play/pvai?ai=${playerID}&deck_id=${deckID}`;
						} else {
							window.location.href = `/play/pvai?ai=${playerID}&opponent_deck_id=${this.opponentDecks[this.deckPicker.selectedIndex].url}&deck_id=${deckID}`;			
						}
	                },
	                null,
	                buttonWidth
	        );
	       this.app.stage.addChild(b);
	       return b;
	}

	selectPlayer(playerIndex) {
		if (playerIndex == 3) {
			this.hideDeckSelector();
		} else {
			this.showDeckSelector();			
		}
	}

	hideDeckSelector() {
		if (this.disciplineDescriptionText) {
			this.disciplineDescriptionText.parent.removeChild(this.disciplineDescriptionText)			
		}
		this.deckPickerTitle.parent.removeChild(this.deckPickerTitle)
		this.deckPicker.hide()
		this.deckContainer.hide()
	}

	showDeckSelector() {
		if (this.disciplineDescriptionText) {
			this.app.stage.addChild(this.disciplineDescriptionText)
		}
		this.app.stage.addChild(this.deckPickerTitle)
		this.deckPicker.show()
		this.deckContainer.show()
	}

	selectOpponentDeck(deckIndex) {
		if (this.disciplineDescriptionText) {
			this.disciplineDescriptionText.parent.removeChild(this.disciplineDescriptionText);
			this.disciplineDescriptionText = null;
		}
		if (deckIndex == this.opponentDecks.length) {
			this.deckContainer.hide()
		} else {
			this.deckContainer.show()
			this.deckContainer.deck = this.opponentDecks[deckIndex];
			this.deckContainer.redisplayDeck()			
			let disciplineDescription = Constants.infoListText(this.opponentDecks[deckIndex].discipline)
	        this.disciplineDescriptionText = new PIXI.Text(disciplineDescription, {fontFamily : Constants.defaultFontFamily, fontSize: Constants.h2FontSize, fill : Constants.darkGrayColor});
	        this.disciplineDescriptionText.position.x = Constants.padding;
	        this.disciplineDescriptionText.position.y = this.deckPicker.position.y + 80;
	        this.app.stage.addChild(this.disciplineDescriptionText);
		}
	}

	// protocol for DeckContainer
	setDeckCardDragListeners(cardSprite) {
		return;
		let self = this;
		cardSprite
		    .on('mousedown',        function (e) {self.foo(this)})
		    .on('touchstart',       function (e) {self.foo(this)})
	}

}
