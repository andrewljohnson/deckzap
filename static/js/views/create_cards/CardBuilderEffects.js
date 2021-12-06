import * as PIXI from 'pixi.js'
const TextInput = require("pixi-text-input");
import * as Constants from '../../constants.js';
import { ButtonPicker } from '../../components/ButtonPicker.js';
import { Card } from '../../components/Card.js';
import { CardBuilderMobAndSpellBase } from './CardBuilderMobAndSpellBase.js'


export class CardBuilderEffects extends CardBuilderMobAndSpellBase {

    constructor(containerID, effectsAndTypes, originalCardInfo, cardID, effectIndex) {
        super(containerID, effectsAndTypes, originalCardInfo, cardID, effectIndex);
        this.loadUX(containerID);
    }

    title() {
        return "Choose Additional Effects"
    }

    updateCard() {
        super.updateCard();
        const choseMobAbility = this.effect && !this.effect.legal_target_types;
        let completedNonMobAbilityEffect = this.targetSelected && this.amountInput && parseInt(this.amountInput.text) > 0;
        if (this.effect && !("amount" in this.effect)) {
            completedNonMobAbilityEffect = this.targetSelected;
        }
        const formComplete = choseMobAbility || completedNonMobAbilityEffect
        this.toggleNextButton(formComplete);
        if (formComplete) {
            let yPosition = Constants.padding * 4;
            if (this.amountInput) {
                yPosition += this.amountInput.position.y + this.amountLabel.height;
            } else if (this.targetTypePicker) {
                yPosition += this.targetTypePicker.position.y + this.targetTypePicker.height;
            } else {
                yPosition += this.effectPicker.position.y + this.effectPicker.height;

            }
            this.addAdditionalEffectButton(yPosition);
        }
    }

    async nextButtonClicked(additionalEffectButtonClicked=false) {
        super.nextButtonClicked("save_effects", additionalEffectButtonClicked);
    }
}
