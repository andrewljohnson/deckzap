import * as Constants from '../Constants.js';
import { Card } from '../components/Card.js';
import { CardBuilderBase } from './CardBuilderBase.js'
import { CardTypePicker } from '../components/CardTypePicker.js';

export class CardBuilder extends CardBuilderBase {

    constructor(containerID, cardsAndEffects, originalCardInfo, cardID) {
        super(containerID)
        this.cardType = "spell"
        this.loadUX(containerID);
    }

    cardInfo() {
        return {name: "Unnamed Card", card_type: this.cardType, image: "uncertainty.svg"};
    }

    loadUXAfterCardImageLoads() {
        this.cardTypePicker = new CardTypePicker(this, this.titleText.position.y + this.titleText.height + Constants.padding * 4, cardTypeID => {this.updateCard(cardTypeID)} )
        this.cardTypePicker.select(this.cardType)
        super.loadUXAfterCardImageLoads()
    }

    title() {
        return "Choose Type"
    }

    nextButtonClicked() {
        Constants.postData('/create_card/save_new', { card_info: this.cardInfo() })
        .then(data => {
            if("error" in data) {
                console.log(data); 
                alert("error saving card");
            } else if (this.cardType == "mob") {
                window.location.href = `/create_card/${data.card_id}/mob_stats`
            } else if (this.cardType == "spell") {
                window.location.href = `/create_card/${data.card_id}/effects`
            } else {
                console.log(`tried to save card with unknown type ${this.cardType}`);
            }
        });

    }

    updateCard(cardTypeID) {
        this.cardType = cardTypeID;
        super.updateCard();
    }

}
