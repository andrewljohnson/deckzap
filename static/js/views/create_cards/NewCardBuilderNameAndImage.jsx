import React from "react";
import TextField from '@mui/material/TextField';
import NewCardBuilderBase from './NewCardBuilderBase';


class NewCardBuilderNameAndImage extends NewCardBuilderBase {
    state = {
        doneTyping: false
    }

    updateName = (event) => {
        if (this.doneTyping) {
            clearTimeout(this.doneTyping);                
        }
        this.doneTyping = setTimeout(()=>{ 
            this.props.cardView.setProperty("name", event.target.value);
        }, 200)

    }

    render = () => {
        return (
            <div>
                <h1>Chooose Name and Image</h1>
                <TextField 
                    id="outlined-basic" 
                    label="Card Name" 
                    variant="outlined" 
                    value={this.state.name}
                    onChange={this.updateName}
                  />
            </div>
        );
    }
}

export default NewCardBuilderNameAndImage;