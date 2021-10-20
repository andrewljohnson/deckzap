import * as PIXI from 'pixi.js'
const TextInput = require("pixi-text-input");
import * as Constants from '../Constants.js';
import { Card } from '../components/Card.js';
import { CardTypePicker } from '../components/CardTypePicker.js';
import { SVGRasterizer } from '../components/SVGRasterizer.js';


export class CardBuilder {

    constructor(containerID, cardsAndEffects, username) {
        this.cardsAndEffects = cardsAndEffects;
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

    newCard() {
        return {name: "Unnamed Card", card_type: this.cardType, image: "uncertainty.svg"};
    }

    loadUX(containerID) {
        let container = document.getElementById(containerID);
        container.appendChild(this.app.view);

        let background = Constants.background(0, 0, (Card.cardWidth + Constants.padding) * 5 + Constants.padding * 4, .1)
        background.tint = 0xEEEEEE;
        background.height = (Card.cardHeight) * 12
        this.app.stage.addChild(background);
        let titleText = this.addTitle();
        this.addNextButton();
        this.cardTypePicker = new CardTypePicker(this, titleText.position.y + titleText.height + Constants.padding * 4, cardTypeID => {this.updateCard(cardTypeID)} )
        let b = this.addNextButton();
        this.cardTypePicker.select(this.cardType)
        this.rasterizer.loadCardImages([this.newCard()]);
        this.app.loader.load(() => {
            this.addCard();
            this.app.loader.reset()
        });        
    }

    updateCard(cardTypeID) {
        this.cardType = cardTypeID;        
        if (this.card) {
            this.card.parent.removeChild(this.card);
        }
        this.addCard();
    }

    addTitle() {
        let title = "Choose Type";
        let titleText = new PIXI.Text(title, {fontFamily : Constants.defaultFontFamily, fontSize: Constants.titleFontSize, fill : Constants.blackColor});
        titleText.position.x = Constants.padding;
        titleText.position.y = Constants.padding * 1.5;
        this.app.stage.addChild(titleText);        
        return titleText;
    }

    addNextButton() {
        const buttonWidth = Card.cardWidth * 1.25;
        const buttonHeight = 40;
        const buttonX = this.app.renderer.width / this.app.renderer.resolution - buttonWidth - Constants.padding - Card.cardWidth * 2 + Constants.padding * 2;
        let buttonTitle = "Next";
        let b = Card.button(
            buttonTitle, 
            Constants.blueColor, 
            Constants.whiteColor, 
            buttonX, 
            -buttonHeight - 16,
            () => {
            // go to HP/Power for Mob, Effects for Spell
            },
            null,
            buttonWidth
        );
        this.nextButton = b
        this.app.stage.addChild(b);
        return b;
    }

    addCard() {
        let cardSprite = Card.sprite(this.newCard(), this);
        let cardHeight = Card.cardHeight;
        cardSprite.position.x = this.nextButton.position.x + Card.cardWidth * 1.25 / 2;
        cardSprite.position.y = this.nextButton.position.y + 200;            
        this.app.stage.addChild(cardSprite);
        cardSprite.interactive = true;
        this.card = cardSprite;
        return cardSprite;
    }


    async postData(url, data) {
        // const csrftoken = getCookie('csrftoken');
     //      // Default options are marked with *
     //      const response = await fetch(url, {
        //     method: 'POST',
        //     headers: {
        //       'Accept': 'application/json',
        //       'Content-Type': 'application/json',
        //       'X-CSRFToken': csrftoken,

        //     },
        //     body: JSON.stringify(data) 
        // });
        // return response.json(); // parses JSON response into native JavaScript objects
    // 
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
