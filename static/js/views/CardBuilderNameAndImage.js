import * as PIXI from 'pixi.js'
const TextInput = require("pixi-text-input");
import * as Constants from '../Constants.js';
import { Card } from '../components/Card.js';
import { CardBuilderBase } from './CardBuilderBase.js'


export class CardBuilderNameAndImage extends CardBuilderBase {

    constructor(containerID, originalCardInfo, cardID) {
        super(containerID)
        this.originalCardInfo = originalCardInfo;
        this.effects = originalCardInfo.effects ? originalCardInfo.effects : [];
        this.cardID = cardID;
        this.loadUX(containerID);
    }

    cardInfo() {
        return {
            name: this.cardName(), 
            card_type: this.originalCardInfo.card_type, 
            image: this.cardImage(), 
            effects: this.originalCardInfo.effects, 
            description:this.cardDescription()
        };
    }

    loadUXAfterCardImageLoads() {
        super.loadUXAfterCardImageLoads()
        const yPosition = this.titleText.position.y + this.titleText.height + Constants.padding * 4;
        this.updateCard();
    }

    cardName() {
        if (this.userCardName) {
            return this.userCardName;
        }
        return "Unnamed Card";
    }

    cardImage() {
        if (this.userCardImage) {
            return this.userCardImage;
        }
        return "uncertainty.svg";
    }

    cardDescription() {
        if (this.effects && this.effects.length) {
            return this.effects[0].description;
        }
    }
    title() {
        return "Choose Name and Image"
    }

    nextButtonClicked() {
        Constants.postData('/create_card/save_name_and_image', { card_info: this.cardInfo(), card_id: this.cardID })
        .then(data => {
            if("error" in data) {
                console.log(data); 
                alert("error saving card");
            } else {
                window.location.href = `/create_card/${this.cardID}/name_and_image`
            }
        })
    }

    updateCard() {
        super.updateCard();
    }     

}
