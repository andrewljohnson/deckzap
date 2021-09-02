import * as PIXI from 'pixi.js'
import { Card } from './Card.js';
import * as Constants from './constants.js';
import { DeckContainer } from './DeckContainer.js';
import { DeckPicker } from './DeckPicker.js';
import { DeckInfo } from './DeckInfo.js';
import { SVGRasterizer } from './SVGRasterizer.js';


export class DeckViewer {

	constructor(decks, allCards, containerID) {
		this.allCards = allCards;
		this.decks = decks;
		this.setUpPIXIApp()
		this.loadUX(containerID);
	}

	setUpPIXIApp() {
		let cardWidth = 7;
		let appWidth = Card.cardWidth * cardWidth + Constants.padding * cardWidth;
		let appHeight = Card.cardHeight * 10 + Constants.padding * 2;
        PIXI.settings.FILTER_RESOLUTION = window.devicePixelRatio || 1;
        this.app = new PIXI.Application({
            antialias: true,
            backgroundColor: Constants.whiteColor,
            height: appHeight,
            width: appWidth, 
            resolution: PIXI.settings.FILTER_RESOLUTION,
        });        
        this.rasterizer = new SVGRasterizer(this.app);
	}

	loadUX(containerID) {			
		let container = document.getElementById(containerID);
		container.appendChild(this.app.view);

		let background = Constants.background(0, 0, Card.cardWidth * (6), .1)
		background.tint = 0xEEEEEE;
		background.height = (Card.cardHeight) * 12
		this.app.stage.addChild(background);

        let titleText = this.addTitle();
        this.deckPicker = new DeckPicker(this, this.decks, this.allCards, titleText.position.y + titleText.height + 20, deckIndex => {this.redisplayDeck(deckIndex)} )
		this.deckContainer = new DeckContainer(this, this.decks[0], this.allCards, 0, this.deckPicker.position.y + 60 );
		this.deckPicker.select(0);
		this.addFindMatchButton();
	}

	addTitle() {
		let title = "Choose Deck";
        let titleText = new PIXI.Text(title, {fontFamily : Constants.defaultFontFamily, fontSize: Constants.titleFontSize, fill : Constants.blackColor});
        titleText.position.x = Constants.padding;
        titleText.position.y = Constants.padding * 2.5;
        this.app.stage.addChild(titleText);		
        return titleText;
	}

	addFindMatchButton() {
        const buttonWidth = Card.cardWidth * 1.25;
        const buttonHeight = 40;
        const buttonX = this.app.renderer.width / this.app.renderer.resolution - buttonWidth - Constants.padding - Card.cardWidth + Constants.padding * 2;
        let b = Card.button(
                "Find Match", 
                Constants.blueColor, 
                Constants.whiteColor, 
                buttonX, 
                -buttonHeight + Constants.padding,
                () => {
                	window.location.href = `/choose_opponent/${this.decks[this.deckPicker.selectedIndex].id}`
                },
                null,
                buttonWidth
            );
       this.app.stage.addChild(b);
       return b;
	}

	redisplayDeck(deckIndex) {
		this.deckContainer.deck = this.decks[deckIndex];
		this.deckContainer.redisplayDeck()

		if (this.disciplineDescriptionText) {
			this.disciplineDescriptionText.parent.removeChild(this.disciplineDescriptionText);
			this.disciplineDescriptionText = null;
		}
		let disciplineDescription = new DeckInfo(this.decks[deckIndex].discipline).infoListText()
        this.disciplineDescriptionText = new PIXI.Text(disciplineDescription, {fontFamily : Constants.defaultFontFamily, fontSize: Constants.defaultFontSize, fill : Constants.darkGrayColor});
        this.disciplineDescriptionText.position.x = this.deckContainer.position.x + Card.cardWidth* 1.25 + Constants.padding * 2;
        this.disciplineDescriptionText.position.y = this.deckContainer.position.y;
        this.app.stage.addChild(this.disciplineDescriptionText);
	}

	// protocol for DeckContainer
    setDeckCardDragListeners(cardSprite) {
		return;
		let self = this;
		cardSprite
		    .on('mousedown',        function (e) {self.removeCard(this)})
		    .on('touchstart',       function (e) {self.removeCard(this)})
    }

}
