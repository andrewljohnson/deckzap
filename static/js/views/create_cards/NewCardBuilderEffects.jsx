import React from "react";
import { ThemeProvider } from '@mui/material/styles';
import NewCardBuilderBase from './NewCardBuilderBase';


class NewCardBuilderEffects extends NewCardBuilderBase {
    render() {
        return (
            <ThemeProvider theme={this.theme()}>
                <h1>Add More Effects</h1>
                {this.effectGroup()}
            </ThemeProvider>
        );
    }
}

export default NewCardBuilderEffects;