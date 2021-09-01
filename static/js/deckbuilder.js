import * as PIXI from 'pixi.js'
const TextInput = require("pixi-text-input");
import { Card } from './Card.js';
import * as Constants from './constants.js';
import { CardsContainer } from './CardsContainer.js';
import { DeckContainer } from './DeckContainer.js';
import { DeckInfo } from './DeckInfo.js';
import { DisciplinePicker } from './DisciplinePicker.js';
import { SVGRasterizer } from './SVGRasterizer.js';


export class DeckBuilder {

	constructor(containerID, deck, username, allCards) {
		this.decks = {"magic": {"cards":{}, "discipline": "magic", "name": null}, "tech": {"cards":{}, "discipline": "tech", "name": null}}
		const jsonDeck = JSON.parse(deck);
		if (Object.keys(jsonDeck.cards).length) {
			this.decks[jsonDeck.discipline] = jsonDeck;
	    	this.discipline = jsonDeck.discipline;
	    	console.log(this.decks[jsonDeck.discipline])
		} else {
	    	this.discipline = "magic"			
		}
		this.allCards = JSON.parse(allCards);
		this.username = username;
		this.setUpPIXIApp()
		this.loadUX(containerID);
	    this.disciplinePicker.select(this.discipline)
	}

	setUpPIXIApp() {
		const widthInCards = 8;
		let appWidth = Card.cardWidth * widthInCards + Constants.padding * widthInCards
		let appHeight = (Card.cardHeight) * 12;
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

	}

	loadUX(containerID) {
		let container = document.getElementById(containerID);
		container.appendChild(this.app.view);

		let background = Constants.background(0, 0, (Card.cardWidth + Constants.padding) * 5 + Constants.padding * 4, .1)
		background.tint = 0xEEEEEE;
		background.height = (Card.cardHeight) * 12
		this.app.stage.addChild(background);

        let titleText = this.addTitle();
        this.disciplinePicker = new DisciplinePicker(this, titleText.position.y + titleText.height, disciplineID => {this.switchClassFunction(disciplineID)} )
        let b = this.addSaveButton();
        this.addDeckTitleInput(b.position.x, b.position.y + b.height + Constants.padding, b.width);
	}

	addTitle() {
		let title = "Build Deck";
        let titleText = new PIXI.Text(title, {fontFamily : Constants.defaultFontFamily, fontSize: Constants.titleFontSize, fill : Constants.blackColor});
        titleText.position.x = Constants.padding;
        titleText.position.y = Constants.padding * 1.5;
        this.app.stage.addChild(titleText);		
        return titleText;
	}

	addSaveButton() {
        const buttonWidth = Card.cardWidth * 1.25;
        const buttonHeight = 40;
        const buttonX = this.app.renderer.width / this.app.renderer.resolution - buttonWidth - Constants.padding - Card.cardWidth + Constants.padding * 2;
        let b = Card.button(
                "Save", 
                Constants.blueColor, 
                Constants.whiteColor, 
                buttonX, 
                -buttonHeight - 2,
                () => {
                	if (this.deckIsFull()) {
                		console.log("Saving, deck is complete")
                		this.saveDeck();
                	} else {
                		console.log(`Not saving, ${this.discipline} deck only has ${this.deckSize()} cards`)
                	}
                },
                null,
                buttonWidth
            );
       this.app.stage.addChild(b);
       return b;
	}

	addDeckTitleInput(x, y, buttonWidth) {
       let deckTitleInput = new TextInput({
		    input: {
		        fontSize: '8pt',
		        width: (buttonWidth - 5) + 'px',
		        textAlign: 'center'
		    }, 
		    box: {
		    	borderWidth: '1px',
		    	stroke: 'black',
		    	borderStyle: 'solid',
		    }
		})
       	deckTitleInput.placeholder = 'My Deck'
       	deckTitleInput.text = this.decks[this.discipline].name
  		deckTitleInput.position.x = x;
        deckTitleInput.position.y = y;
        this.app.stage.addChild(deckTitleInput);
        this.deckTitleInput = deckTitleInput;

        this.deckTitleInput.on('input', text => {
    		console.log('text:', text)
    		this.decks[this.discipline].name = text
		})
	}

	switchClassFunction (disciplineID) {
    	this.discipline = disciplineID;
		this.updateCards();
		this.updateCardCountLabel();
		this.updateDeckCards();
	}

	updateCards() {
		let disciplineCards = []
		for (let card of this.allCards) {
			if (this.discipline == card.discipline) {
				disciplineCards.push(card.name)
			}
		}
		if (!this.cardsContainer) {
			this.cardsContainer = new CardsContainer(this, [], this.allCards, 5, this.disciplinePicker.position.x-25, this.disciplinePicker.position.y+40);
		}
		this.cardsContainer.deck = {"cards":disciplineCards};
		this.cardsContainer.redisplayDeck();				
	}

	updateCardCountLabel() {
		if (this.cardCountLabel)  {
			this.cardCountLabel.parent.removeChild(this.cardCountLabel);
			this.cardCountLabel = null;
		}
		let cardCountText;
		if (this.discipline == "magic") {
			cardCountText = this.deckSize() + " / 30"
		} else {
			cardCountText = this.deckSize() + " / 15"					
		}
		let labelColor = Constants.redColor;
		if (this.deckIsFull()) {
			labelColor = Constants.blueColor;
		}
		this.cardCountLabel = new PIXI.Text(cardCountText, {fontFamily : Constants.defaultFontFamily, fontSize: Constants.defaultFontSize, fill : Constants.whiteColor, stroke: labelColor, strokeThickness: 2});

        this.cardCountLabel.position.x = this.deckTitleInput.position.x;
        this.cardCountLabel.position.y = this.deckTitleInput.position.y + this.deckTitleInput.height + Constants.padding * 2;
        this.app.stage.addChild(this.cardCountLabel);
	}

	deckIsFull() {
		if (this.discipline == "magic") {
			return this.deckSize() == 30;
		} else {
			return this.deckSize() == 15;
		}
	}

	deckSize() {
		if (!this.decks[this.discipline]) {
			return 0;
		}
		let count = 0;		
		for (let dcName in this.decks[this.discipline].cards) {
			count += this.decks[this.discipline]["cards"][dcName];
		}
		return count;
	}

	updateDeckCards() {
    	if (!this.deckContainer) {
        	this.deckContainer = new DeckContainer(this, {"cards":[]}, this.allCards, this.cardCountLabel.position.x, this.cardCountLabel.position.y + 20);
    	}
		this.deckContainer.deck = this.decks[this.discipline];
		this.deckContainer.redisplayDeck();

	    if ("name" in this.decks[this.discipline]) {
		    this.deckTitleInput.text = this.decks[this.discipline].name;
	    } else {
		    this.deckTitleInput.text = null;
	    }		
	}

	// protocol for CardsContainer
    setCardDragListeners(card, cardSprite, game) {
		let self = this;
		cardSprite
		    .on('mousedown',        function (e) {self.selectCard(this)})
		    .on('touchstart',       function (e) {self.selectCard(this)})
    }

	// protocol for DeckContainer
    setDeckCardDragListeners(cardSprite) {
		let self = this;
		cardSprite
		    .on('mousedown',        function (e) {self.removeCard(this)})
		    .on('touchstart',       function (e) {self.removeCard(this)})
    }

	selectCard(cardSprite) {
		if (this.deckIsFull()) {
			console.log("Deck is full, can't add more cards");
			return;
		}
		let card = cardSprite.card;
		let cardName = card.name;
		let cardIsUnique = card.card_type == Constants.artifactCardType || Card.hasAbility(card, "unique") ;
		if (!this.decks[this.discipline].cards[cardName]) {
			this.decks[this.discipline].cards[cardName] = 1
			this.switchClassFunction(this.discipline)
		} else if (this.decks[this.discipline].cards[cardName] == 1 && !cardIsUnique) {
			this.decks[this.discipline].cards[cardName] += 1			
			this.switchClassFunction(this.discipline)
		} else if (cardIsUnique) {
			console.log(`Can't add that unique card ${cardName}, there is already 1 in the deck`)
		} else {
			console.log(`Can't add ${cardName}, there are already 2 in the deck`)
		}
	}

	removeCard(cardSprite) {
		this.decks[this.discipline].cards[cardSprite.card.name] -= 1
		if (this.decks[this.discipline].cards[cardSprite.card.name] == 0) {
			delete this.decks[this.discipline].cards[cardSprite.card.name];
		}
		this.switchClassFunction(this.discipline)
	}

	saveDeck() {
		console.log("saving deck")
		console.log(this.decks[this.discipline])
		this.postData('/build_deck/save', { username: this.username, deck: this.decks[this.discipline] })
	  	.then(data => {
	  		if("error" in data) {
				console.log(data); // JSON data parsed by `data.json()` call
				alert("error saving deck");
	  		} else {
	  			window.location.href = `/u/${this.username}`
	  		}
	  	});
	}

	async postData(url, data) {
		const csrftoken = getCookie('csrftoken');
	  	// Default options are marked with *
	  	const response = await fetch(url, {
			method: 'POST',
			headers: {
			  'Accept': 'application/json',
			  'Content-Type': 'application/json',
			  'X-CSRFToken': csrftoken,

			},
			body: JSON.stringify(data) 
		});
		return response.json(); // parses JSON response into native JavaScript objects
	}
}

function getCookie(name) {
	let cookieValue = null;
	if (document.cookie && document.cookie !== '') {
		const cookies = document.cookie.split(';');
		for (let i = 0; i < cookies.length; i++) {
			const cookie = cookies[i].trim();
			// Does this cookie string begin with the name we want?
			if (cookie.substring(0, name.length + 1) === (name + '=')) {
				cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
				break;
			}
		}
	}
	return cookieValue;
}
