import * as PIXI from 'pixi.js'
const TextInput = require("pixi-text-input");
import * as Constants from '../Constants.js';
import { ButtonPicker } from '../components/ButtonPicker.js';
import { Card } from '../components/Card.js';
import { CardBuilderBase } from './CardBuilderBase.js'


export class CardBuilderEffects extends CardBuilderBase {

    constructor(containerID, cardsAndEffects, originalCardInfo, cardID) {
        super(containerID)
        this.cardsAndEffects = cardsAndEffects;
        this.originalCardInfo = originalCardInfo;
        this.effects = originalCardInfo.effects ? originalCardInfo.effects : [];
        this.cardID = cardID;
        this.loadUX(containerID);
    }

    cardInfo() {
        return {
            name: "Unnamed Card", 
            card_type: this.originalCardInfo.card_type, 
            image: "uncertainty.svg", 
            effects: this.effects, 
            description:this.cardDescription()
        };
    }

    loadUXAfterCardImageLoads() {
        super.loadUXAfterCardImageLoads()
        const yPosition = this.titleText.position.y + this.titleText.height + Constants.padding * 4;
        const effectPicker = new ButtonPicker(
            Constants.padding, 
            yPosition, 
            "Effect Name", 
            this.cardsAndEffects.effects.filter(effect => {
                return effect.legal_card_type_ids.includes(this.cardInfo().card_type);
            }).map(effect => {
                return effect.name;
            }),
            effect_label => { this.selectEffect(effect_label) }).container;
        this.app.stage.addChild(effectPicker);
        this.effectPicker = effectPicker;
        this.updateCard();
    }

    selectEffect(effect_label) {
        for (let effect of this.cardsAndEffects.effects) {
            if (effect.name == effect_label) {
                this.effect = effect;
            }
        }
        if (this.effectDescription) {
            this.effectDescription.parent.removeChild(this.effectDescription);
        }
        this.removeAmountControl();
        this.removeTargetControl();
        let description = this.effect.description_expanded ? this.effect.description_expanded : this.effect.description;
        this.effectDescription = new PIXI.Text(description, {fontFamily : Constants.defaultFontFamily, fontSize: Constants.defaultButtonFontSize, fill : Constants.darkGrayColor});
        this.effectDescription.position.x = Constants.padding;
        this.effectDescription.position.y = this.effectPicker.position.y + this.effectPicker.height + Constants.padding * 2;
        this.app.stage.addChild(this.effectDescription);     

        let yPosition = this.effectDescription.position.y + this.effectDescription.height + Constants.padding * 4;
        const targetTypePicker = new ButtonPicker(
            Constants.padding, 
            yPosition, 
            "Target", 
            this.effect.legal_target_type_ids,
            target_label => { this.selectTarget(target_label) }).container;
        this.app.stage.addChild(targetTypePicker);
        this.targetTypePicker = targetTypePicker;
        this.effects = [this.effect]
        this.updateCard();
    }

    cardDescription() {
        if (this.effects && this.effects.length) {
            return this.effects[0].description;
        }
    }

    selectTarget(target_label) {
        for (let target in this.cardsAndEffects.target_types) {
            if (target == target_label) {
                this.target = this.cardsAndEffects.target_types[target];
            }
        }
        if (this.targetDescription) {
            this.targetDescription.parent.removeChild(this.targetDescription);
        }
        let description = this.target.name;
        this.targetDescription = new PIXI.Text(description, {fontFamily : Constants.defaultFontFamily, fontSize: Constants.defaultButtonFontSize, fill : Constants.darkGrayColor});
        this.targetDescription.position.x = Constants.padding;
        this.targetDescription.position.y = this.targetTypePicker.position.y + this.targetTypePicker.height + Constants.padding * 2;
        this.app.stage.addChild(this.targetDescription);    

        this.effect["target_type"] = target_label
        this.effects = [this.effect];
        if ("amount" in this.effect && !this.amountLabel) {
            this.addAmountInput(Constants.padding, this.targetDescription.position.y + this.targetDescription.height + Constants.padding * 2);
        } 
        Constants.postData('/create_card/get_card_info', { card_info: this.cardInfo(), card_id: this.cardID })
        .then(data => {
            if("error" in data) {
                console.log(data); 
                alert("error fetching effect info");
            } else {
                this.effect = data.server_effect
                this.effects = [this.effect]
                this.updateCard();
            }
        });
    }

    addAmountInput(x, y) {
        this.removeAmountControl();
        this.amountLabel = new PIXI.Text("Amount", {fontFamily : Constants.defaultFontFamily, fontSize: Constants.defaultButtonFontSize, fill : Constants.blackColor});
        this.amountLabel.position.x = x;
        this.amountLabel.position.y = y;
        this.app.stage.addChild(this.amountLabel);    

        let amountInput = new TextInput({
            input: {
                fontSize: '14pt',
                width: (100 - 5) + 'px',
                textAlign: 'center',
            }, 
            box: {
                borderWidth: '1px',
                stroke: 'black',
                borderStyle: 'solid',
            }
        })
        amountInput.placeholder = 'Amount for Effect'
        amountInput.text = 1;
        amountInput.position.x = x;
        amountInput.position.y = this.amountLabel.position.y + this.amountLabel.height + Constants.padding * 4;
        this.app.stage.addChild(amountInput);
        this.amountInput = amountInput;
        this.effects[0].amount = 1
        this.amountInput.on('input', text => {
            amountInput.text = text
            this.effects[0].amount = text

            Constants.postData('/create_card/get_card_info', { card_info: this.cardInfo(), card_id: this.cardID })
            .then(data => {
                if("error" in data) {
                    console.log(data); 
                    alert("error fetching effect info");
                } else {
                    this.effect = data.server_effect
                    this.effects = [this.effect]
                    this.updateCard();
                }
            });

        })

        /*
        MOBS ONLY
        const yPosition = this.amountInput.position.y + this.amountInput.height + Constants.padding * 4;
        const effectTypePicker = new ButtonPicker(
            Constants.padding, 
            yPosition, 
            "Effect Trigger", 
            this.effect.legal_effect_type_ids,
            effect_type_label => { this.selectEffectType(effect_type_label) }).container;
        this.app.stage.addChild(effectTypePicker);
        this.effectTypePicker = effectTypePicker;
        */
    }

    removeTargetControl() {
        if (this.targetTypePicker) {
            this.targetTypePicker.parent.removeChild(this.targetTypePicker);
            this.targetTypePicker = null;
        }
        if (this.targetDescription) {
            this.targetDescription.parent.removeChild(this.targetDescription);
            this.targetDescription = null;
        }
    }

    removeAmountControl() {
        if (this.amountLabel) {
            this.amountLabel.parent.removeChild(this.amountLabel);
            this.amountInput.parent.removeChild(this.amountInput);
        }
        this.amountLabel = null;
        this.amountInput = null;
    }


    selectEffectType(effect_type_label) {
        // console.log(this.cardsAndEffects.effect_types[effect_type_label]);
    }

    title() {
        return "Choose Effects"
    }

    nextButtonClicked() {
        Constants.postData('/create_card/save_effects', { card_info: this.cardInfo(), card_id: this.cardID })
        .then(data => {
            if("error" in data) {
                console.log(data); 
                alert("error saving card");
            } else {
                window.location.href = `/create_card/${this.cardID}/name_and_image`
            }
        })
    }

}
