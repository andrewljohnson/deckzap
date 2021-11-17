import * as PIXI from 'pixi.js'
const TextInput = require("pixi-text-input");
import * as Constants from '../../constants.js';
import { ButtonPicker } from '../../components/ButtonPicker.js';
import { Card } from '../../components/Card.js';
import { CardBuilderBase } from './CardBuilderBase.js'


export class CardBuilderEffects extends CardBuilderBase {

    constructor(containerID, effectsAndTypes, originalCardInfo, cardID, effectIndex) {
        super(containerID)
        this.effectsAndTypes = effectsAndTypes;
        this.originalCardInfo = originalCardInfo;
        this.effects = originalCardInfo.effects ? originalCardInfo.effects : [];
        this.effectIndex = effectIndex;
        this.cardID = cardID;
        this.loadUX(containerID);
    }

    cardInfo() {
        const info = super.cardInfo();
        info.effects = this.effects;
        return info;
    }

    cardDescription() {
        if (this.effects && this.effects.length) {
            return this.descriptionForEffects(this.effects);
        }
        return super.cardDescription()
    }

    loadUXAfterCardImageLoads() {
        super.loadUXAfterCardImageLoads()
        const yPosition = this.titleText.position.y + this.titleText.height + Constants.padding * 4;
        let effects = this.effectsAndTypes.effects.filter(effect => {
                return effect.legal_card_type_ids.includes(this.cardInfo().card_type);
            })
        let unusedOrDuplicableEffects = [];
        for (let effect of effects) {
            let used = false;
            for (let usedEffect of this.effects) {
                if (usedEffect.id == effect.id) {
                    used = true;
                }
            }
            if (effect.effect_type == "spell" || !used) {
                unusedOrDuplicableEffects.push(effect);
            } 
        }
        let effectNamesAndIDs = unusedOrDuplicableEffects.map(effect => {
                return {name: effect.name, id: effect.id};
        });
        const effectPicker = new ButtonPicker(
            Constants.padding, 
            yPosition, 
            "Effect Name", 
            effectNamesAndIDs,
            effect_id => { this.selectEffect(effect_id) }).container;
        this.app.stage.addChild(effectPicker);
        this.effectPicker = effectPicker;
        this.updateCard();
    }

    selectEffect(effect_id) {
        this.removeAddEffectButton();
        for (let effect of this.effectsAndTypes.effects) {
            if (effect.id == effect_id) {
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
        
        this.updateEffects();
        this.getEffectForInfo(
            () => {
                if (this.originalCardInfo.card_type == Constants.mobCardType && this.effect.legal_target_types) {
                    this.addEffectTypePicker()
                } else if (this.originalCardInfo.card_type == Constants.spellCardType) {
                    let yPosition = this.effectDescription.position.y + this.effectDescription.height + Constants.padding * 4;
                    this.addTargetTypePicker(yPosition);
                } else {
                    // it's a mob ability like Ambush, Drain, Guard, or Shield
                    this.getEffectForInfo();
                }                
            }
        );
    }

    updateEffects() {
        if (this.effects.length == this.effectIndex) {
            this.effects.push(this.effect);
        } else {
            this.effects[this.effects.length - 1] = this.effect            
        }

    }

    addEffectTypePicker() {
        // mobs only, because spells always have effect type spell
        const yPosition = this.effectDescription.position.y + this.effectDescription.height + Constants.padding * 4;
        const effectTypePicker = new ButtonPicker(
            Constants.padding, 
            yPosition, 
            "Effect Trigger", 
            this.effect.legal_effect_types,
            effect_type_id => { this.selectEffectType(effect_type_id) }).container;
        this.app.stage.addChild(effectTypePicker);
        this.effectTypePicker = effectTypePicker;
    }

    selectEffectType(effect_type_id) {
        this.removeAddEffectButton();
        this.targetSelected = false;
        if (this.effectTypeDescription) {
            this.effectTypeDescription.parent.removeChild(this.effectTypeDescription);
        }
        this.effect.effect_type = effect_type_id;
        this.updateEffects();
        let description = this.effectsAndTypes["effect_types"][effect_type_id].description;
        this.effectTypeDescription = new PIXI.Text(description, {fontFamily : Constants.defaultFontFamily, fontSize: Constants.defaultButtonFontSize, fill : Constants.darkGrayColor});
        this.effectTypeDescription.position.x = Constants.padding;
        this.effectTypeDescription.position.y = this.effectTypePicker.position.y + this.effectTypePicker.height + Constants.padding * 2;
        this.app.stage.addChild(this.effectTypeDescription);   
        this.app.stage.interactiveChildren = false;  
        this.getEffectForInfo(
            () => {
                if (this.effect.legal_target_types) {
                    let yPosition = this.effectTypeDescription.position.y + this.effectTypeDescription.height + Constants.padding * 4;
                    this.addTargetTypePicker(yPosition);
                } else {
                    this.getEffectForInfo();
                }
            }
        );
    }

    addTargetTypePicker (yPosition) {
        this.removeTargetControl();
        const targetTypePicker = new ButtonPicker(
            Constants.padding, 
            yPosition, 
            "Target", 
            this.effect.legal_target_types,
            target_id => { this.selectTarget(target_id) }).container;
        this.app.stage.addChild(targetTypePicker);
        this.targetTypePicker = targetTypePicker;
    }

    selectTarget(target_id) {
        this.targetSelected = true;
        for (let target in this.effectsAndTypes.target_types) {
            if (this.effectsAndTypes.target_types[target].id == target_id) {
                this.target = this.effectsAndTypes.target_types[target];
            }
        }
        if (this.targetDescription) {
            this.targetDescription.parent.removeChild(this.targetDescription);
        }
        console.log(this.target)
        let description = this.target.name;
        this.targetDescription = new PIXI.Text(description, {fontFamily : Constants.defaultFontFamily, fontSize: Constants.defaultButtonFontSize, fill : Constants.darkGrayColor});
        this.targetDescription.position.x = Constants.padding;
        this.targetDescription.position.y = this.targetTypePicker.position.y + this.targetTypePicker.height + Constants.padding * 2;
        this.app.stage.addChild(this.targetDescription);    

        this.effect["target_type"] = target_id
        this.updateEffects();
        if ("amount" in this.effect && !this.amountLabel) {
            this.addAmountInput(Constants.padding, this.targetDescription.position.y + this.targetDescription.height + Constants.padding * 2);
        } 
        this.getEffectForInfo();
    }

    async getEffectForInfo(successFunction=null) {
        this.app.stage.interactiveChildren = false;  
        let json = await Constants.postData(`${this.baseURL()}/get_effect_for_info`, { card_info: this.cardInfo(), card_id: this.cardID });
        if("error" in json) {
            console.log(json); 
            alert("error fetching effect info");
        } else {
            this.effect = json.server_effect;
            this.powerPoints = json.power_points;
            this.updateEffects();
            this.updateCard();
            if (successFunction) {
                successFunction();
            }

        }
        this.app.stage.interactiveChildren = true;  
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
            if (!Constants.isPositiveWholeNumber(text) && text) {
                this.amountInput.text = this.lastText;
                return;
            }
            this.removeAddEffectButton();
            amountInput.text = text;
            this.lastText = text;
            this.effects[this.effectIndex].amount = text

            if (text) {
                this.getEffectForInfo();
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

    updateCard() {
        super.updateCard();
        const choseMobAbility = this.effect && !this.effect.legal_target_types;
        const completedNonMobAbilityEffect = this.targetSelected && this.amountInput && parseInt(this.amountInput.text) > 0;
        const formComplete = choseMobAbility || completedNonMobAbilityEffect
        this.toggleNextButton(formComplete);
        if (formComplete) {
            let yPosition = Constants.padding * 4;
            if (this.amountInput) {
                yPosition += this.amountInput.position.y + this.amountLabel.height;
            } else {
                yPosition += this.effectPicker.position.y + this.effectPicker.height;

            }
            this.addAdditionalEffectButton(yPosition);
        }
    }

    addAdditionalEffectButton(buttonY) {
        this.removeAddEffectButton();
        const buttonWidth = Card.cardWidth * 1.25;
        const buttonHeight = 40;
        const buttonX = Constants.padding * 3 + buttonWidth / 2;
        let buttonTitle = "Add Another Effect";
        let b = Card.button(
            buttonTitle, 
            Constants.blueColor, 
            Constants.whiteColor, 
            buttonX, 
            buttonY,
            () => {
                this.additionalEffectButtonClicked();
            },
            null,
            buttonWidth
        );
        this.app.stage.addChild(b);
        this.addEffectButton = b
    }

    removeAddEffectButton() {
        if (this.addEffectButton) {
            this.addEffectButton.parent.removeChild(this.addEffectButton);
            this.addEffectButton = null;
        }
    }

    additionalEffectButtonClicked() {
        this.nextButtonClicked(true);
    }

    async nextButtonClicked(additionalEffectButtonClicked=false) {
        const json = await Constants.postData(`${this.baseURL()}/save_effects`, { card_info: this.cardInfo(), card_id: this.cardID })
        if("error" in json) {
            console.log(json); 
            alert("error saving card");
        } else {
            if(additionalEffectButtonClicked) {
                window.location.href = `${this.baseURL()}/${this.cardID}/effects/${this.effects.length}`
            } else {
                window.location.href = `${this.baseURL()}/${this.cardID}/cost`
            }
        }
    }

}
