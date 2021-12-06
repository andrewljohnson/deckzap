import * as PIXI from 'pixi.js'
const TextInput = require("pixi-text-input");
import * as Constants from '../../constants.js';
import { ButtonPicker } from '../../components/ButtonPicker.js';
import { Card } from '../../components/Card.js';
import { CardBuilderMobAndSpellBase } from './CardBuilderMobAndSpellBase.js'

export class CardBuilderMob extends CardBuilderMobAndSpellBase {

    constructor(containerID, effectsAndTypes, originalCardInfo, cardID, effectIndex) {
        super(containerID, effectsAndTypes, originalCardInfo, cardID, effectIndex);
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

    title() {
        return "Create Mob"
    }

    addInputs(x, y) {
        this.addInput(x, y, "Mana Cost", "userCardCost");
        this.addInput(x + 220, y, "Strength", "strength");
        this.addInput(x + 440, y, "Hit Points", "hitPoints");
        return 100;
    }

    async nextButtonClicked(additionalEffectButtonClicked=false) {
        super.nextButtonClicked("save_mob", additionalEffectButtonClicked);
    }

    updateCard() {
        super.updateCard();
        let errorMessage = "";
        if ((this.strength < 0 || isNaN(this.strength)) && (this.hitPoints <= 0 || isNaN(this.hitPoints))) {
            errorMessage = "Strength must be >= 0. Hit Points must be >= 1.";
        } else if (this.strength < 0 || isNaN(this.strength)) {
            errorMessage = "Strength must be >= 0;";
        } else if (this.hitPoints <= 0 || isNaN(this.hitPoints)) {
            errorMessage = "Hit Points must be >= 1.";
        }
        const hasMobStats = parseInt(this.strength) >= 0 && parseInt(this.hitPoints) >= 1;
        const hasManaCost = this.userCardCost >= 0 && this.userCardCost <= 10 && !isNaN(this.userCardCost);
        if (!hasManaCost) {
            if(errorMessage.length) {
                errorMessage += " ";
            }
            errorMessage += "Cards must cost at least 0 and no more than 10 mana."
        }

        const choseMobAbility = this.effect && !this.effect.legal_target_types;
        let completedNonMobAbilityEffect = this.targetSelected && this.amountInput && parseInt(this.amountInput.text) > 0;
        if (this.effect && !("amount" in this.effect)) {
            completedNonMobAbilityEffect = this.targetSelected;
        }
        const effectFormComplete = choseMobAbility || completedNonMobAbilityEffect
        this.toggleNextButton(hasMobStats && hasManaCost && (effectFormComplete || !this.effect), errorMessage);

        if (effectFormComplete) {
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

}
