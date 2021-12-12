import React from "react";
import { ThemeProvider } from '@mui/material/styles';
import CardBuilderBase from './CardBuilderBase';


class CardBuilderEffects extends CardBuilderBase {
    render() {
        return (
            <ThemeProvider theme={this.theme()}>
                <h1>Add More Effects</h1>
                {this.effectGroup()}
            </ThemeProvider>
        );
    }
}

export default CardBuilderEffects;