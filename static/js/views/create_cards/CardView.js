import * as Constants from '../../constants.js';
import { Card } from '../../components/Card.js';
import { CardBuilderBase } from './CardBuilderBase.js'
import { SVGRasterizer } from '../../components/SVGRasterizer.js';

export class CardView extends CardBuilderBase {

    constructor(containerID) {
        super(containerID);
        this.loadUX(containerID);
    }

    cardInfo() {
        const info = super.cardInfo();
        const cardType = this.cardType ? this.cardType : Constants.mobCardType;
        info.card_type = cardType;
        if (cardType == Constants.mobCardType) {
            info.strength = this.strength ? this.strength : 0;
            info.hit_points = this.hitPoints ? this.hitPoints : 1;
        }
        info.cost = this.manaCost ? this.manaCost : 0;
        info.power_points = this.powerPoints;
        info.effects = this.effects ? this.effects : [];
        return info;
    }

    setCardType(cardType) {
        this.cardType = cardType;
        this.updateCard();
    }

    setManaCost(cost) {
        this.manaCost = cost;
        this.updateCard();
    }

    setStrength(strength) {
        this.strength = strength;
        this.updateCard();
    }

    setHitPoints(hitPoints) {
        this.hitPoints = hitPoints;
        this.updateCard();
    }

    setPowerPoints(powerPoints) {
        this.powerPoints = powerPoints;
        this.updateCard();
    }

    setEffects(effects) {
        this.effects = effects;
        this.updateCard();
    }

    loadUX(containerID) {
        const container = document.getElementById(containerID);
        container.appendChild(this.app.view);

        this.rasterizer = new SVGRasterizer(this.app);
        this.rasterizer.loadCardImages([this.cardInfo()]);
        this.app.loader.load(() => {
            this.updateCard();
            this.app.loader.reset()
        });        
    }
}

export default CardView;