import * as Constants from '../../constants.js';
import React from "react";
import { ThemeProvider } from '@mui/material/styles';
import CardBuilderBase from './CardBuilderBase';


class CardBuilderEffects extends CardBuilderBase {
    render() {
        return (
            <ThemeProvider theme={Constants.theme()}>
                <h1>Add Another Effect</h1>
                {this.effectGroup()}
            </ThemeProvider>
        );
    }
}

export default CardBuilderEffects;