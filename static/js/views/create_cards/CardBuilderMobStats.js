import * as PIXI from 'pixi.js'
const TextInput = require("pixi-text-input");
import * as Constants from '../../constants.js';
import { Card } from '../../components/Card.js';
import { CardBuilderBase } from './CardBuilderBase.js'

export class CardBuilderMobStats extends CardBuilderBase {

    constructor(containerID, originalCardInfo, cardID) {
        super(containerID)
        this.originalCardInfo = originalCardInfo;
        this.cardID = cardID;
        this.strength = 0;
        this.hitPoints = 1;
        this.loadUX(containerID);
    }

    cardInfo() {
        let info = super.cardInfo();
        info.strength = this.strength;
        info.hit_points = this.hitPoints;
        return info;
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
        return "Choose Strength and Hit Points"
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
        this.addInput(x, y, "Strength", "strength");
        this.addInput(x, y + 100, "Hit Point", "hitPoints");
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
        if (variableToSet == "strength") {
            input.text = this.strength;
        } else {
            input.text = this.hitPoints;
        }
        input.position.x = x;
        input.position.y = label.position.y + label.height + Constants.padding * 4;
        this.app.stage.addChild(input);
        input.on('input', text => {
            if ((!Constants.isPositiveWholeNumber(text) && text && text != '0') || (text == '0' && variableToSet == "hitPoints")) {
                if (variableToSet == "strength") {
                    input.text = this.lastStrength;
                } else {
                    input.text = this.lastHitPoints;
                }
                return;
            }
            if (variableToSet == "strength") {
                this.strength = parseInt(text);
                this.lastStrength = text;
            } else {
                this.hitPoints = parseInt(text);                
                this.lastHitPoints = text;
            }
            if (this.strength.length && this.hitPoints.length) {
                this.getPowerPoints();
            } else {
                this.updateCard();
            }
        })
    }

    updateCard() {
        super.updateCard();
        let errorMessage = "";
        if ((this.strength < 0 || isNaN(this.strength)) && (this.hitPoints <= 0 || isNaN(this.hitPoints))) {
            errorMessage = "Strength must be >= 0, and Hit Points must be >= 1.";
        } else if (this.strength < 0 || isNaN(this.strength)) {
            errorMessage = "Strength must be >= 0;";
        } else if (this.hitPoints <= 0 || isNaN(this.hitPoints)) {
            errorMessage = "Hit Points must be >= 1.";
        }
        this.toggleNextButton(parseInt(this.strength) >= 0 && parseInt(this.hitPoints) >= 1, errorMessage);
    }

}
