import * as PIXI from 'pixi.js'
const TextInput = require("pixi-text-input");
import * as Constants from '../constants.js';
import { Card } from '../components/Card.js';
import { CardsContainer } from '../components/CardsContainer.js';
import { DeckContainer } from '../components/DeckContainer.js';
import { DisciplinePicker } from '../components/DisciplinePicker.js';
import { SVGRasterizer } from '../components/SVGRasterizer.js';


export class DeckBuilder {

    constructor(containerID, deck, username, allCards) {
        this.decks = {"magic": {"cards":{}, "discipline": "magic", "title": null}, "tech": {"cards":{}, "discipline": "tech", "title": null}}
        const jsonDeck = JSON.parse(deck);
        if (jsonDeck && Object.keys(jsonDeck.cards).length) {
            this.decks[jsonDeck.discipline] = jsonDeck;
            this.discipline = jsonDeck.discipline;
        } else {
            this.discipline = "magic"            
        }
        this.allCards = JSON.parse(allCards);
        this.username = username;
        this.setUpPIXIApp();
        this.loadUX(containerID);
    }

    setUpPIXIApp() {
        const widthInCards = 9;
        let appWidth = Card.cardWidth * widthInCards + Constants.padding * widthInCards
        let appHeight = (Card.cardHeight) * 15;
        Constants.setUpPIXIApp(this, appHeight, appWidth)
        this.rasterizer = new SVGRasterizer(this.app);
    }

    loadUX(containerID) {
        let container = document.getElementById(containerID);
        container.appendChild(this.app.view);

        let background = Constants.background(0, 0, (Card.cardWidth + Constants.padding) * 5 + Constants.padding * 4, .1)
        background.tint = 0xEEEEEE;
        background.height = (Card.cardHeight) * 12
        this.app.stage.addChild(background);

        this.addTitle();
        let createCardsText = this.addCreateCardsText();
        this.disciplinePicker = new DisciplinePicker(this, createCardsText.position.y + createCardsText.height + Constants.padding * 4, disciplineID => {this.switchClassFunction(disciplineID)} )
        let b = this.addSaveButton();
        this.addDeckTitleInput(b.position.x, b.position.y + b.height + Constants.padding, b.width);
        this.disciplinePicker.select(this.discipline)
        if (this.decks[this.discipline].id != null) {
            this.disciplinePicker.disable();
        }
        // todo: totally remove this maybe
        this.disciplinePicker.disciplineDescriptionText.parent.removeChild(this.disciplinePicker.disciplineDescriptionText);
        this.disciplinePicker.magic.parent.removeChild(this.disciplinePicker.magic);
        this.disciplinePicker.tech.parent.removeChild(this.disciplinePicker.tech);
    }

    addTitle() {
        let title = "Choose Cards for Deck";
        if (this.decks[this.discipline].username && this.decks[this.discipline].username != this.username) {
            title = "View Deck: " + this.decks[this.discipline].title            
        }
        let titleText = new PIXI.Text(title, {fontFamily : Constants.defaultFontFamily, fontSize: Constants.titleFontSize, fill : Constants.blackColor});
        titleText.position.x = Constants.padding;
        titleText.position.y = Constants.padding * 1.5;
        this.app.stage.addChild(titleText);        
        this.titleText = titleText;
        return titleText;
    }

    addCreateCardsText() {
        let createCardsString = "Missing a card you want? ";
        let createCardsText = new PIXI.Text(createCardsString, {fontFamily : Constants.defaultFontFamily, fontSize: Constants.defaultButtonFontSize, fill : Constants.blackColor});
        createCardsText.position.x = Constants.padding;
        createCardsText.position.y = this.titleText.position.y + this.titleText.height + Constants.padding * 1.5;
           this.app.stage.addChild(createCardsText);        
 
        let buttonString = "Create your own cards.";
        let buttonText = new PIXI.Text(buttonString, {fontFamily : Constants.defaultFontFamily, fontSize: Constants.defaultButtonFontSize, fill : Constants.blueColor});
        buttonText.position.x = createCardsText.position.x + createCardsText.width;
        buttonText.position.y = createCardsText.position.y;
        buttonText.interactive = true;
        buttonText.buttonMode = true;
           this.app.stage.addChild(buttonText);        

        buttonText
            .on("click", () => { window.location.href = "/create_card/" })
            .on("tap", () => { window.location.href = "/create_card/" })

        const underline = new PIXI.Sprite(PIXI.Texture.WHITE);
        underline.tint = Constants.blueColor;
        underline.position.y = buttonText.height;
        underline.width = buttonText.width;
        underline.height = 1;
        buttonText.addChild(underline);

        this.createCardsText = createCardsText;
        return createCardsText;
    }

    addSaveButton() {
            const buttonWidth = Card.cardWidth * 1.25;
            const buttonHeight = 40;
            const buttonX = this.app.renderer.width / this.app.renderer.resolution - buttonWidth - Constants.padding - Card.cardWidth * 2 + Constants.padding * 2;
            let buttonTitle = "Save";
            if (this.decks[this.discipline].username && this.decks[this.discipline].username != this.username) {
            buttonTitle = "Copy Deck";            
            }
            let b = Card.button(
                    buttonTitle, 
                    Constants.blueColor, 
                    Constants.whiteColor, 
                    buttonX, 
                    -buttonHeight - 16,
                    () => {
                        if (!this.username) {
                            window.location.href = "/signup"
                        } else if (this.deckIsFull()) {
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
            this.saveButton = b;
            return b;
    }

    toggleSaveButton() {
        const enabled = this.deckIsFull() && this.salaryCap <= 100;
        this.saveButton.background.interactive = enabled;
        this.saveButton.background.buttonMode = enabled;
        this.saveButton.background.tint = enabled ? Constants.blueColor : Constants.darkGrayColor;
    }

    addDeckTitleInput(x, y, buttonWidth) {
           let deckTitleInput = new TextInput({
                input: {
                    fontSize: '14pt',
                    width: (buttonWidth - 5) + 'px',
                    textAlign: 'center',
                }, 
                box: {
                    borderWidth: '1px',
                    stroke: 'black',
                    borderStyle: 'solid',
                }
            })
               deckTitleInput.placeholder = 'My Deck'
               deckTitleInput.text = this.decks[this.discipline].title ? this.decks[this.discipline].title != undefined : ""
              deckTitleInput.position.x = x;
            deckTitleInput.position.y = y;
            if (this.decks[this.discipline].username && this.decks[this.discipline].username != this.username) {
                deckTitleInput.interactive = false
                deckTitleInput.buttonMode = false
            }
            this.app.stage.addChild(deckTitleInput);
            this.deckTitleInput = deckTitleInput;

            this.deckTitleInput.on('input', text => {
                this.decks[this.discipline].title = text
            })
    }

    switchClassFunction (disciplineID) {
        this.discipline = disciplineID;
        this.updateCards();
        this.updateCardCountLabel();
        this.updateSalaryCapLabel();
        this.updateDeckCards();
        this.toggleSaveButton();
    }

    updateCards() {
        let disciplineCards = []
        for (let card of this.allCards) {
            if (this.discipline == card.discipline) {
                disciplineCards.push(card.name)
            }
        }
        if (!this.cardsContainer) {
            let containerY = this.disciplinePicker.position.y+80;
            let containerX = this.disciplinePicker.position.x-45
            // todo: totally remove disciplinePicker maybe
            containerX = this.createCardsText.position.x;
            containerY = this.createCardsText.position.y + this.createCardsText.height + Constants.padding * 2;
            this.cardsContainer = new CardsContainer(this, [], this.allCards, 5, containerX, containerY);
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
        this.cardCountLabel = new PIXI.Text("Card Count: " + cardCountText, {fontFamily : Constants.defaultFontFamily, fontSize: Constants.h2FontSize, fill : Constants.whiteColor, stroke: labelColor, strokeThickness: 2});
        this.app.stage.addChild(this.cardCountLabel);

        this.cardCountLabel.position.x = this.deckTitleInput.position.x;
        this.cardCountLabel.position.y = this.deckTitleInput.position.y + this.deckTitleInput.height + Constants.padding * 2;
    }

    updateSalaryCapLabel() {
        if (this.salaryCapLabel)  {
            this.salaryCapLabel.parent.removeChild(this.salaryCapLabel);
            this.salaryCapLabel = null;
        }
        let salaryCapText = 0;
        for (let dcName in this.decks[this.discipline].cards) {
            let addedCard;
            for (let card of this.allCards) {
                if (card.name == dcName) {
                    addedCard = card;
                }
            }
            salaryCapText += this.decks[this.discipline]["cards"][dcName] * addedCard.power_points;
        }
        this.salaryCap = parseInt(salaryCapText);
        let labelColor = Constants.blueColor;
        if (salaryCapText > 100) {
            labelColor = Constants.redColor;
        }
        this.salaryCapLabel = new PIXI.Text("Salary Cap: " + salaryCapText + "/100", {fontFamily : Constants.defaultFontFamily, fontSize: Constants.h2FontSize, fill : Constants.whiteColor, stroke: labelColor, strokeThickness: 2});
        this.app.stage.addChild(this.salaryCapLabel);

        this.salaryCapLabel.position.x = this.deckTitleInput.position.x;
        this.salaryCapLabel.position.y = this.cardCountLabel.position.y + this.cardCountLabel.height + Constants.padding;
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
            this.deckContainer = new DeckContainer(this, {"cards":[]}, this.allCards, this.salaryCapLabel.position.x, this.salaryCapLabel.position.y + this.salaryCapLabel.height + Constants.padding * 2);
        }
        this.deckContainer.deck = this.decks[this.discipline];
        this.deckContainer.redisplayDeck();

        if ("title" in this.decks[this.discipline]) {
            this.deckTitleInput.text = this.decks[this.discipline].title;
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
        if (this.decks[this.discipline].username && this.decks[this.discipline].username != this.username) {
            return;
        }
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
        let cardIsUnique = card.card_type == Constants.artifactCardType;
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
        Constants.postData('/build_deck/save', { username: this.username, deck: this.decks[this.discipline] })
          .then(data => {
              if("error" in data) {
                console.log(data); // JSON data parsed by `data.json()` call
                alert("error saving deck");
              } else {
                  window.location.href = `/u/${this.username}`
              }
          });
    }

}
