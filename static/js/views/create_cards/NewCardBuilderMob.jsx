import React from "react";
import { ThemeProvider } from '@mui/material/styles';
import NewCardBuilderBase from './NewCardBuilderBase';


class NewCardBuilderMob extends NewCardBuilderBase {
    changeStrength = (event, value) => {
        this.setState({strength: value});
        this.props.cardView.setProperty("strength", value);
    };

    changeHitPoints = (event, value) => {
        this.setState({hitPoints: value});
        this.props.cardView.setProperty("hit_points", value);
    };

    render() {
        const strengthMarks = [
          {
            value: 0,
            label: '0 Strength',
          },
          {
            value: 10,
            label: '10 Strength',
          },
        ];

        const hitPointMarks = [
          {
            value: 1,
            label: '1 Hit Point',
          },
          {
            value: 10,
            label: '10 Hit Points',
          },
        ];
  
        return (
            <ThemeProvider theme={this.theme()}>
                <h1>Create Mob</h1>
                <div style={{display: "flex"}}>
                    {this.sliderDiv("Mana Cost", "Mana", this.manaMarks(), this.changeManaCost, () => this.getPowerPoints())}
                    {this.sliderDiv("Strength", "Strength", strengthMarks, this.changeStrength, () => this.getPowerPoints())}
                    {this.sliderDiv("Hit Points", "Hit Points", hitPointMarks, this.changeHitPoints, () => this.getPowerPoints(), 1)}
                </div>
                {this.effectGroup()}
            </ThemeProvider>
        );
    }
}

export default NewCardBuilderMob;