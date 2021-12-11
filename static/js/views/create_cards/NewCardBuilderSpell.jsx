import React from "react";
import { ThemeProvider } from '@mui/material/styles';
import NewCardBuilderBase from './NewCardBuilderBase';


class NewCardBuilderMob extends NewCardBuilderBase {
    render() {
        return (
            <ThemeProvider theme={this.theme()}>
                <h1>Create Spell</h1>
                <div style={{display: "flex"}}>
                    {this.sliderDiv("Mana Cost", "Mana", this.manaMarks(), this.changeManaCost, () => this.getPowerPoints())}
                </div>
                {this.effectGroup()}
            </ThemeProvider>
        );
    }
}

export default NewCardBuilderMob;