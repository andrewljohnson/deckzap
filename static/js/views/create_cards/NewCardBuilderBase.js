import React, { Component } from "react";
import * as Constants from '../../constants.js';

class NewCardBuilderBase extends Component {
    state = {
    };

    baseURL = () => {
        return "/create_card";
    }

    baseCardInfo = () => {
        let info;
        if (this.props.originalCardInfo) {
            info = this.props.originalCardInfo;
        } else {
            info = {};
        }
        if (!this.props.originalCardInfo || !this.props.originalCardInfo.name) {
            info.name = this.defaultCardName();
        }
        if (!this.props.originalCardInfo || !this.props.originalCardInfo.image) {
            info.image = this.defaultCardImageFilename();
        }
        info.description = this.cardDescription();
        return info;
    }

    defaultCardName = () => {
        return "Unnamed Card";
    }

    defaultCardImageFilename = () => {
        return "uncertainty.svg";
    }

    cardDescription = () => {
        if (this.props.originalCardInfo && this.props.originalCardInfo.effects && this.props.originalCardInfo.effects.length) {
            return this.descriptionForEffects(this.props.originalCardInfo.effects);
        }
    }

    descriptionForEffects= (effects) => {
        let description = "";
        for (const effect of effects) {
            description += effect.description;
            if (!effect.description.endsWith(".")) {
                description += ".";
            }
            if (effect != effects[effects.length - 1]) {
                description += " ";
            }
        }
        return description;
    }

    getPowerPoints = async () => {
        const json = await Constants.postData(`${this.baseURL()}/get_power_points`, { card_info: this.cardInfo(), card_id: this.props.cardID })
        if("error" in json) {
            console.log(json); 
            alert("error fetching power points");
        } else {
            this.setState({powerPoints:json.power_points});
            this.props.cardView.setPowerPoints(json.power_points);
        }
    }

    getEffectForInfo = async (effect, successFunction=null) => {
        let cardInfo = this.cardInfo();
        cardInfo.effects = [effect];
        let json = await Constants.postData(`${this.baseURL()}/get_effect_for_info`, { card_info: cardInfo, card_id: this.props.cardID });
        if("error" in json) {
            console.log(json); 
            alert("error fetching effect info");
        } else {
            if (json.server_effect.legal_effect_type) {
                json.server_effect.effect_type = json.server_effect.legal_effect_types[0].id;
            }
            this.setState({effect:json.server_effect, effects:[json.server_effect], powerPoints:json.power_points});
            this.props.cardView.setEffects([json.server_effect]);
            this.props.cardView.setPowerPoints(json.power_points);
            if (successFunction) {
                successFunction();
            }

        }
    }


    nextOrNewEffectButtonClicked = async (path, additionalEffectButtonClicked=false) => {
        const json = await Constants.postData(`${this.baseURL()}/${path}`, { card_info: this.cardInfo(), card_id: this.props.cardID })
        if("error" in json) {
            console.log(json); 
            alert("error saving mob card");
        } else {
            if(additionalEffectButtonClicked) {
                window.location.href = `${this.baseURL()}/${this.props.cardID}/effects/${this.effects.length}`
            } else {
                window.location.href = `${this.baseURL()}/${this.props.cardID}/name_and_image`
            }
        }
    }

}

export default NewCardBuilderBase;