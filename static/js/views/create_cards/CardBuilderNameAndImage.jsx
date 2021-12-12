import React from "react";
import CardBuilderBase from './CardBuilderBase';
import * as Constants from '../../constants.js';
import Autocomplete from '@mui/material/Autocomplete';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import { ThemeProvider } from '@mui/material/styles';


class CardBuilderNameAndImage extends CardBuilderBase {
    state = {
        doneTyping: false,
        image: "uncertainty.svg",
        disableSave: true
    }

    updateName = (event) => {
            
        if (this.doneTyping) {
            clearTimeout(this.doneTyping);                
        }
        this.doneTyping = setTimeout(()=>{ 
            this.setState({name: event.target.value}, this.toggleSaveButton);
            if (event.target.value && event.target.value.length) {
                this.props.cardView.setProperty("name", event.target.value);
            }
        }, 200)
    }

    selectImage = (event, newValue) => {
        if (newValue) {
            this.setState({image: newValue.filename}, this.toggleSaveButton);
            this.props.cardView.setProperty("image", newValue.filename);
        } else {
            this.setState({image: "uncertainty.svg"}, this.toggleSaveButton);
            this.props.cardView.setProperty("image", "uncertainty.svg");
        }
    }

    toggleSaveButton = () => {
        if (!this.state.name || !this.state.name.length || this.state.image === "uncertainty.svg") {
            this.setState({"disableSave": true});
        } else {
            this.setState({"disableSave": false});
        }        
    }

    /*
    updateCard() {
        super.updateCard();
        let errorMessage = "";
        if (!this.userCardName && !this.userCardImage) {
            errorMessage = "Type a name and select an image for your card.";
        } else if (!this.userCardName) {
            errorMessage = "Type a name for your card.";
        } else if (!this.userCardImage) {
            errorMessage = "Select an image for your card.";
        }
        this.toggleNextButton(this.userCardName && this.userCardImage, errorMessage);
    }*/


    nextButtonClicked = async() => {
        const json = await Constants.postData(`${this.baseURL()}/save_name_and_image`, { card_info: this.cardInfo(), card_id: this.props.cardID })
        if("error" in json) {
            console.log(json); 
            alert(json.error);
        } else {
            window.location.href = "/";
        }
    }

    render = () => {
        const autocompleteItems = [];
        for (let info of this.props.imagePaths) {
            info.label = info.filename;
            autocompleteItems.push(info);
        }
        let disableSave = false;
        if (this.state.disableSave) {
            disableSave = true;
        }
        return (
            <ThemeProvider theme={this.theme()}>
                <h1>Chooose Name and Image</h1>
                <TextField 
                    id="outlined-basic" 
                    label="Card Name" 
                    variant="outlined" 
                    onChange={this.updateName}
                />
                <br/><br/>
                <Autocomplete
                  disablePortal
                  id="combo-box-demo"
                  options={autocompleteItems}
                  sx={{ width: 300 }}
                  renderInput={(params) => <TextField {...params} label="Image" />}
                  onChange ={this.selectImage}
                />
                <br /><br />
                <Button 
                    color="primary"
                    disabled={disableSave}
                    variant="contained"
                    onClick={this.nextButtonClicked}
                >
                    Save and Finish
                </Button> 
            </ThemeProvider>
        );
    }
}

export default CardBuilderNameAndImage;