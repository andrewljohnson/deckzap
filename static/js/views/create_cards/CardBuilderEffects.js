import * as PIXI from 'pixi.js'
const TextInput = require("pixi-text-input");
import * as Constants from '../../Constants.js';
import { ButtonPicker } from '../../components/ButtonPicker.js';
import { Card } from '../../components/Card.js';
import { CardBuilderBase } from './CardBuilderBase.js'


export class CardBuilderEffects extends CardBuilderBase {

    constructor(containerID, effectsAndTypes, originalCardInfo, cardID) {
        super(containerID)
        this.effectsAndTypes = effectsAndTypes;
        this.originalCardInfo = originalCardInfo;
        this.effects = originalCardInfo.effects ? originalCardInfo.effects : [];
        this.cardID = cardID;
        this.loadUX(containerID);
    }

    cardInfo() {
        return {
            name: this.defaultCardName(), 
            image: this.defaultCardImageFilename(), 
            card_type: this.originalCardInfo.card_type, 
            power: this.originalCardInfo.power, 
            toughness: this.originalCardInfo.toughness, 
            effects: this.effects, 
            description:this.cardDescription()
        };
    }

    cardDescription() {
        if (this.effects && this.effects.length) {
            return this.effects[0].description;
        }
        return super.cardDescription()
    }

    loadUXAfterCardImageLoads() {
        super.loadUXAfterCardImageLoads()
        const yPosition = this.titleText.position.y + this.titleText.height + Constants.padding * 4;
        const effectPicker = new ButtonPicker(
            Constants.padding, 
            yPosition, 
            "Effect Name", 
            this.effectsAndTypes.effects.filter(effect => {
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
        for (let effect of this.effectsAndTypes.effects) {
            if (effect.name == effect_label) {
                this.effect = effect;
            }
        }
        if (this.effectDescription) {
            this.effectDescription.parent.removeChild(this.effectDescription);
        }
        this.targetSelected = false;
        this.removeTargetControl();
        this.removeEffectTypeControl();
        this.removeAmountControl();
        let description = this.effect.description_expanded ? this.effect.description_expanded : this.effect.description;
        this.effectDescription = new PIXI.Text(description, {fontFamily : Constants.defaultFontFamily, fontSize: Constants.defaultButtonFontSize, fill : Constants.darkGrayColor});
        this.effectDescription.position.x = Constants.padding;
        this.effectDescription.position.y = this.effectPicker.position.y + this.effectPicker.height + Constants.padding * 2;
        this.app.stage.addChild(this.effectDescription);     

        let yPosition = this.effectDescription.position.y + this.effectDescription.height + Constants.padding * 4;
        
        this.effects = [this.effect]
        Constants.postData(`${this.baseURL()}/get_effect_for_info`, { card_info: this.cardInfo(), card_id: this.cardID })
        .then(data => {
            if("error" in data) {
                console.log(data); 
                alert("error fetching effect info");
            } else {
                this.effect = data.server_effect
                this.effects = [this.effect]
                this.updateCard();
                if (this.originalCardInfo.card_type == Constants.mobCardType && this.effect.legal_target_type_ids) {
                    this.addEffectTypePicker()
                } else if (this.originalCardInfo.card_type == Constants.spellCardType) {
                    let yPosition = this.effectDescription.position.y + this.effectDescription.height + Constants.padding * 4;
                    this.addTargetTypePicker(yPosition);
                } else {
                    // it's a mob ability like Ambush, Drain, Guard, or Shield
                    this.getEffectForInfo();
                }
            }
        });

    }

    addEffectTypePicker() {
        // mobs only, because spells always have effect type spell
        const yPosition = this.effectDescription.position.y + this.effectDescription.height + Constants.padding * 4;
        const effectTypePicker = new ButtonPicker(
            Constants.padding, 
            yPosition, 
            "Effect Trigger", 
            this.effect.legal_effect_type_ids,
            effect_type_label => { this.selectEffectType(effect_type_label) }).container;
        this.app.stage.addChild(effectTypePicker);
        this.effectTypePicker = effectTypePicker;
    }

    selectEffectType(effect_type_label) {
        if (this.effectTypeDescription) {
            this.effectTypeDescription.parent.removeChild(this.effectTypeDescription);
        }
        this.effect.effect_type = effect_type_label;
        this.effects = [this.effect];
        let description = this.effectsAndTypes["effect_types"][effect_type_label].description;
        this.effectTypeDescription = new PIXI.Text(description, {fontFamily : Constants.defaultFontFamily, fontSize: Constants.defaultButtonFontSize, fill : Constants.darkGrayColor});
        this.effectTypeDescription.position.x = Constants.padding;
        this.effectTypeDescription.position.y = this.effectTypePicker.position.y + this.effectTypePicker.height + Constants.padding * 2;
        this.app.stage.addChild(this.effectTypeDescription);     
        Constants.postData(`${this.baseURL()}/get_effect_for_info`, { card_info: this.cardInfo(), card_id: this.cardID })
        .then(data => {
            if("error" in data) {
                console.log(data); 
                alert("error fetching effect info");
            } else {
                this.effect = data.server_effect
                this.effects = [this.effect]
                this.updateCard();
                if (this.effect.legal_target_type_ids) {
                    let yPosition = this.effectTypeDescription.position.y + this.effectTypeDescription.height + Constants.padding * 4;
                    this.addTargetTypePicker(yPosition);
                } else {
                    this.getEffectForInfo();
                }
            }
        });        
    }

    addTargetTypePicker (yPosition) {
        this.removeTargetControl();
        const targetTypePicker = new ButtonPicker(
            Constants.padding, 
            yPosition, 
            "Target", 
            this.effect.legal_target_type_ids,
            target_label => { this.selectTarget(target_label) }).container;
        this.app.stage.addChild(targetTypePicker);
        this.targetTypePicker = targetTypePicker;
    }

    selectTarget(target_label) {
        this.targetSelected = true;
        for (let target in this.effectsAndTypes.target_types) {
            if (target == target_label) {
                this.target = this.effectsAndTypes.target_types[target];
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
        this.getEffectForInfo();
    }

    getEffectForInfo() {
        Constants.postData(`${this.baseURL()}/get_effect_for_info`, { card_info: this.cardInfo(), card_id: this.cardID })
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
                width: (200 - 5) + 'px',
                textAlign: 'center',
            }, 
            box: {
                borderWidth: '1px',
                stroke: 'black',
                borderStyle: 'solid',
            }
        })
        amountInput.placeholder = 'Amount for Effect'
        amountInput.position.x = x;
        amountInput.position.y = this.amountLabel.position.y + this.amountLabel.height + Constants.padding * 4;
        this.app.stage.addChild(amountInput);
        this.amountInput = amountInput;
        this.lastText = 0;
        this.amountInput.on('input', text => {
            if (!Constants.isWholeNumber(text) && text) {
                this.amountInput.text = this.lastText;
                return;
            }
            amountInput.text = text;
            this.lastText = text;
            this.effects[0].amount = text

            if (text) {
                Constants.postData(`${this.baseURL()}/get_effect_for_info`, { card_info: this.cardInfo(), card_id: this.cardID })
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

        })
    }

    isWholeNumber(value) {
        return /^-?\d+$/.test(value);
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

    removeEffectTypeControl() {
        if (this.effectTypeDescription) {
            this.effectTypeDescription.parent.removeChild(this.effectTypeDescription);
        }
        if (this.effectTypePicker) {
            this.effectTypePicker.parent.removeChild(this.effectTypePicker);
        }
        this.effectTypeDescription = null;
        this.effectTypePicker = null;
    }

    title() {
        return "Choose Effects"
    }

    nextButtonClicked() {
        Constants.postData(`${this.baseURL()}/save_effects`, { card_info: this.cardInfo(), card_id: this.cardID })
        .then(data => {
            if("error" in data) {
                console.log(data); 
                alert("error saving card");
            } else {
                window.location.href = `${this.baseURL()}/${this.cardID}/cost`
            }
        })
    }

    updateCard() {
        super.updateCard();
        const choseMobAbility = this.effect && !this.effect.legal_target_type_ids;
        const completedNonMobAbilityEffect = this.targetSelected && this.amountInput && parseInt(this.amountInput.text) > 0;
        this.toggleNextButton(choseMobAbility || completedNonMobAbilityEffect);
    }
}
