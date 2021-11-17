import * as PIXI from 'pixi.js'
const TextInput = require("pixi-text-input");
import * as Constants from '../../constants.js';
import { Card } from '../../components/Card.js';
import { CardBuilderBase } from './CardBuilderBase.js'

export class CardBuilderCost extends CardBuilderBase {

    constructor(containerID, originalCardInfo, cardID) {
        super(containerID)
        this.originalCardInfo = originalCardInfo;
        this.cardID = cardID;
        this.loadUX(containerID);
        console.log("FOOO")
    }

    cardInfo() {
        const info = super.cardInfo();
        info.cost = this.cardCost();
        return info;
    }

    loadUXAfterCardImageLoads() {
        super.loadUXAfterCardImageLoads()
        const yPosition = this.titleText.position.y + this.titleText.height + Constants.padding * 4;
        this.addCostInput(Constants.padding * 2, yPosition)
        this.updateCard();
    }

    cardCost() {
        if (this.userCardCost) {
            return this.userCardCost;
        }
    }

    title() {
        return "Choose Mana Cost"
    }

    nextButtonClicked() {
        Constants.postData(`${this.baseURL()}/save_cost`, { card_info: this.cardInfo(), card_id: this.cardID })
        .then(data => {
            if("error" in data) {
                console.log(data); 
                alert("error saving card");
            } else {
                window.location.href = `${this.baseURL()}/${this.cardID}/name_and_image`
            }
        })
    }

    addCostInput(x, y) {
        const costLabel = new PIXI.Text("Mana Cost", {fontFamily : Constants.defaultFontFamily, fontSize: Constants.defaultButtonFontSize, fill : Constants.blackColor});
        costLabel.position.x = x;
        costLabel.position.y = y;
        this.app.stage.addChild(costLabel);    

        let costInput = new TextInput({
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
        costInput.placeholder = 'Mana Cost'
        costInput.position.x = x;
        costInput.position.y = costLabel.position.y + costLabel.height + Constants.padding * 4;
        this.app.stage.addChild(costInput);
        this.lastText = 0;
        this.costInput = costInput;
        costInput.on('input', text => {
            if (!Constants.isPositiveWholeNumber(text) && text && text != '0') {
                this.costInput.text = this.lastText;
                console.log("here")
                return;
            }
            console.log("there")
            this.userCardCost = parseInt(text);
            this.lastText = text;
            if (text.length) {
                this.getPowerPoints();
            } else {
                this.updateCard();
            }
        })
    }

    updateCard() {
        super.updateCard();
        console.log(this.userCardCost);
        this.toggleNextButton(
            this.userCardCost >= 0 && this.userCardCost <= 10 && !isNaN(this.userCardCost), 
            "Cards must cost at least 0 and no more than 10 mana."
            );
    }

}
