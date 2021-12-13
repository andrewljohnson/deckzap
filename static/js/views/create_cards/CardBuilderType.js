import React, { Component } from "react";
import * as Constants from '../../constants.js';
import { Card } from '../../components/Card.js';
import Button from '@mui/material/Button';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import CardBuilderBase from './CardBuilderBase';
import { ThemeProvider } from '@mui/material/styles';


class CardBuilderType extends CardBuilderBase {
    state = {
        cardType: Constants.mobCardType,
    };

    changeType = (event, cardType) => {
        this.setState({cardType});
        this.props.cardView.setProperty("card_type", cardType);
    }

    nextButtonClicked = async () => {
        const json = await Constants.postData(`${this.baseURL()}/save_new`, { card_info: this.props.cardView.cardInfo })
        if("error" in json) {
            console.log(json); 
            alert("error saving card");
        } else if (this.state.cardType == Constants.mobCardType) {
            window.location.href = `${this.baseURL()}/${json.card_id}/mob`
        } else if (this.state.cardType == Constants.spellCardType) {
            window.location.href = `${this.baseURL()}/${json.card_id}/spell`
        } else {
            console.log(`tried to save card with unknown type ${this.cardType}`);
        }
    }

    render() {
        const control = {
            value: this.state.cardType,
            onChange: this.changeType,
            exclusive: true,
        };

        return (
            <ThemeProvider theme={this.theme()}>
                <h1>Choose Card Type</h1>
                <p>
                    <b>Mobs</b> have strength and hit points, and they can attack your opponent and their mobs.
                </p>
                <p>
                    <b>Spells</b> have an effect on the game when you play them and then go to your discard pile.
                </p>
                <ToggleButtonGroup size="large" {...control}>
                    <ToggleButton value={Constants.mobCardType} key={Constants.mobCardType}>
                        Mob
                    </ToggleButton>,
                    <ToggleButton value={Constants.spellCardType} key={Constants.spellCardType}>
                        Spell
                    </ToggleButton>,
                </ToggleButtonGroup>
                <br /><br /><br /><br />
                <Button 
                    variant="contained"
                    onClick={this.nextButtonClicked}
                >
                    Next
                </Button> 
                <br /><br /><br /> 
            </ThemeProvider>
        );
    }
}

export default CardBuilderType;