import * as Constants from '../../constants.js';
import { Card } from '../../components/Card.js';
import { CardBuilderBase } from './CardBuilderBase.js'
import { CardTypePicker } from '../../components/CardTypePicker.js';

export class CardBuilder extends CardBuilderBase {

    constructor(containerID, cardsAndEffects, originalCardInfo, cardID) {
        super(containerID);
        this.cardType = Constants.spellCardType;
        this.loadUX(containerID);
    }

    cardInfo() {
        const info = super.cardInfo();
        info.card_type = this.cardType;
        return info;
    }

    loadUXAfterCardImageLoads() {
        this.cardTypePicker = new CardTypePicker(
            this, 
            this.titleText.position.y + this.titleText.height + Constants.padding * 4, 
            cardTypeID => {this.cardType = cardTypeID; this.updateCard();} 
        );
        this.cardTypePicker.select(this.cardType);
        super.loadUXAfterCardImageLoads();
        this.toggleNextButton(true);
    }

    title() {
        return "Choose Type";
    }

    nextButtonClicked() {
        Constants.postData(`${this.baseURL()}/save_new`, { card_info: this.cardInfo() })
        .then(data => {
            if("error" in data) {
                console.log(data); 
                alert("error saving card");
            } else if (this.cardType == Constants.mobCardType) {
                window.location.href = `${this.baseURL()}/${data.card_id}/mob_stats`
            } else if (this.cardType == Constants.spellCardType) {
                window.location.href = `${this.baseURL()}/${data.card_id}/effects`
            } else {
                console.log(`tried to save card with unknown type ${this.cardType}`);
            }
        });

    }
}
