import * as PIXI from 'pixi.js'
const TextInput = require("pixi-text-input");
import * as Constants from '../../Constants.js';
import { Card } from '../../components/Card.js';
import { CardBuilderBase } from './CardBuilderBase.js'

export class CardBuilderMobStats extends CardBuilderBase {

    constructor(containerID, originalCardInfo, cardID) {
        super(containerID)
        this.originalCardInfo = originalCardInfo;
        this.cardID = cardID;
        this.power = 0;
        this.toughness = 1;
        this.loadUX(containerID);
    }

    cardInfo() {
        return {
            name: this.defaultCardName(), 
            image: this.defaultCardImageFilename(),
            card_type: this.originalCardInfo.card_type, 
            power: this.power,
            toughness: this.toughness,
        };
    }

    loadUXAfterCardImageLoads() {
        super.loadUXAfterCardImageLoads()
        const yPosition = this.titleText.position.y + this.titleText.height + Constants.padding * 4;
        this.addMobStatsInputs(Constants.padding * 2, yPosition)
        this.updateCard();
    }

    cardCost() {
        if (this.userCardCost) {
            return this.userCardCost;
        }
    }

    title() {
        return "Choose Power and Toughness"
    }

    nextButtonClicked() {
        Constants.postData(`${this.baseURL()}/save_mob_stats`, { card_info: this.cardInfo(), card_id: this.cardID })
        .then(data => {
            if("error" in data) {
                console.log(data); 
                alert("error saving card");
            } else {
                window.location.href = `${this.baseURL()}/${this.cardID}/effects`
            }
        })
    }

    addMobStatsInputs(x, y, ) {
        this.addInput(x, y, "Power", "power");
        this.addInput(x, y + 100, "toughness");
    }

    addInput(x, y, inputLabelTitle, variableToSet) {
        const label = new PIXI.Text(inputLabelTitle, {fontFamily : Constants.defaultFontFamily, fontSize: Constants.defaultButtonFontSize, fill : Constants.blackColor});
        label.position.x = x;
        label.position.y = y;
        this.app.stage.addChild(label);    

        let input = new TextInput({
            input: {
                fontSize: '14pt',
                width: (200 - 5) + 'px',
                textAlign: 'center',
            }, 
            box: {
                borderWidth: '1px',
                stroke: 'black',
                borderStyle: 'solid',
            }
        })
        input.placeholder = inputLabelTitle;
        if (variableToSet == "power") {
            input.text = this.power;
        } else {
            input.text = this.toughness;
        }
        input.position.x = x;
        input.position.y = label.position.y + label.height + Constants.padding * 4;
        this.app.stage.addChild(input);
        input.on('input', text => {
            if (variableToSet == "power") {
                this.power = text;
            } else {
                this.toughness = text;                
            }
            this.updateCard();
        })
    }

    updateCard() {
        super.updateCard();
        this.toggleNextButton(parseInt(this.power) >= 0 && parseInt(this.toughness) >= 1);
    }

}
