import * as PIXI from 'pixi.js'
const TextInput = require("pixi-text-input");
import * as Constants from '../../constants.js';
import { ButtonPicker } from '../../components/ButtonPicker.js';
import { Card } from '../../components/Card.js';
import { CardBuilderMobAndSpellBase } from './CardBuilderMobAndSpellBase.js'

export class CardBuilderSpell extends CardBuilderMobAndSpellBase {

    constructor(containerID, effectsAndTypes, originalCardInfo, cardID, effectIndex) {
        super(containerID, effectsAndTypes, originalCardInfo, cardID, effectIndex);
        this.loadUX(containerID);
    }

    title() {
        return "Create Spell"
    }

    addInputs(x, y) {
        this.addInput(x, y, "Mana Cost");
        return 100;
    }

    async nextButtonClicked(additionalEffectButtonClicked=false) {
        super.nextButtonClicked("save_spell", additionalEffectButtonClicked);
    }

    updateCard() {
        super.updateCard();
        let errorMessage = "";
        const hasManaCost = this.userCardCost >= 0 && this.userCardCost <= 10 && !isNaN(this.userCardCost);
        if (!hasManaCost) {
            errorMessage += "Cards must cost at least 0 and no more than 10 mana."
        }

        let completedNonMobAbilityEffect = this.targetSelected && this.amountInput && parseInt(this.amountInput.text) > 0;
        if (this.effect && !("amount" in this.effect)) {
            completedNonMobAbilityEffect = this.targetSelected;
        }
        const effectFormComplete = completedNonMobAbilityEffect
        this.toggleNextButton(hasManaCost && effectFormComplete, errorMessage);

        if (effectFormComplete) {
            let yPosition = Constants.padding * 4;
            if (this.amountInput) {
                yPosition += this.amountInput.position.y + this.amountLabel.height;
            } else if (this.targetTypePicker) {
                yPosition += this.targetTypePicker.position.y + this.targetTypePicker.height;
            } else {
                yPosition += this.effectPicker.container.position.y + this.effectPicker.container.height;

            }
            this.addAdditionalEffectButton(yPosition);
        }
    }

}
