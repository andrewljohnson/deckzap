import * as PIXI from 'pixi.js'
import * as Constants from '../Constants.js';
import { Card } from '../components/Card.js';
import { DeckContainer } from '../components/DeckContainer.js';
import { DeckPicker } from '../components/DeckPicker.js';
import { SVGRasterizer } from '../components/SVGRasterizer.js';


export class DeckViewer {

	constructor(decks, allCards, containerID) {
		this.allCards = allCards;
		this.decks = decks;
		Constants.setUpPIXIApp(this)
		this.rasterizer = new SVGRasterizer(this.app);
		this.loadUX(containerID);
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
		this.deckContainer = new DeckContainer(this, this.decks[0], this.allCards, Constants.padding * 2, this.deckPicker.position.y + 100 );
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
        const buttonX = this.app.renderer.width / this.app.renderer.resolution - buttonWidth * 2;
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
		let disciplineDescription = Constants.infoListText(this.decks[deckIndex].discipline)
        this.disciplineDescriptionText = new PIXI.Text(disciplineDescription, {fontFamily : Constants.defaultFontFamily, fontSize: Constants.h2FontSize, fill : Constants.darkGrayColor});
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
