import * as Constants from '../constants.js';
import React, {Component} from "react";
import Button from '@mui/material/Button';
import { ThemeProvider } from '@mui/material/styles';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';

class Profile extends Component {
    state = {
        deleteCardOpen: false
    }

    confirmDeleteCard = (cardID) => {
        this.setState({deleteCardOpen: true, deleteCardID: cardID})
    }

    finishDeleteCard = async () => {
        const json = await Constants.postData(`/create_card/delete`, { card_id: this.state.deleteCardID })
        if("error" in json) {
            console.log(json); 
            alert("error fetching power points");
        } else {
            window.location.href = "/";
        }        
    }

    cancelDeleteCard = () => {
        this.setState({deleteCardOpen: false})
    }
    
    render = () => {
        let rankText = "unranked"
        if (this.props.player_rank > 0) {
            rankText = this.props.player_rank;
        }
        const rankParagraph = <p>{this.props.username} is <a href="/top_players">{rankText}</a> on deckzap.com.</p>;

        let userButtons = null;
        if (this.props.userOwnsProfile) {
            userButtons = 
                <div>
                    <Button variant="contained" href="/choose_deck_for_match" style={{marginRight:30}}>Find Match</Button> 
                    <Button variant="contained" href="/build_deck">Build Deck</Button>
                </div>;
        }

        let deckLIs = [];
        for (let deck of this.props.decks) {
            deckLIs.push(
                <li key={deck.id}>
                    <h3>
                        {this.props.userOwnsProfile &&
                            <Button 
                                href={`/build_deck?deck_id=${deck.id}`}
                                style={{marginRight:40}}
                                variant="outlined"
                            >
                                Edit
                            </Button>
                        }   
                        {deck.title}
                    </h3>
                    
                </li>
            );
        }

        let cardLIs = [];
        for (let card of this.props.cards) {
            cardLIs.push(
                <li key={card.id}>
                    <h3>
                        {this.props.userOwnsProfile &&
                            <Button 
                                color="warning"
                                style={{marginRight:40}}
                                variant="outlined"
                                disabled={card.used_count > 0 }
                                onClick={() => {this.confirmDeleteCard(card.id)}}

                            >
                                Delete
                            </Button>
                        }   
                        {card.name} <i>(used in {card.used_count} decks</i>)
                    </h3>
                    
                </li>
            );
        }

        let noCardsParagraph = null;
        if (this.props.cards.length == 0) {
            noCardsParagraph = 
                <p style={{marginBottom: 30}}>
                    You haven't created any cards yet. <a href="/create_card/">Create new cards</a> to use in your decks.
                </p>
        }

        let deleteCardDialog = null;
        if (this.state.deleteCardID) {

        }

        return (
            <ThemeProvider theme={Constants.theme()}>
                <h1>{this.props.username}</h1>
                {rankParagraph}
                <p>{this.props.username} was the #{this.props.accountNumber} signup on deckzap.com.</p>
                {userButtons}
                <hr style={{marginTop: 25}} />
                <h2>Decks</h2>
                <ul style={{padding:0}}>
                    {deckLIs}
                </ul>
                <hr style={{marginTop: 25}} />
                <h2>Custom Cards</h2>
                <ul style={{padding:0}}>
                    {cardLIs}
                </ul>
                {noCardsParagraph}
                <Dialog
                    open={this.state.deleteCardOpen}
                    onClose={this.cancelDeleteCard}
                    aria-labelledby="alert-dialog-title"
                    aria-describedby="alert-dialog-description"
                >
                    <DialogTitle id="alert-dialog-title">
                      {"Delete card?"}
                    </DialogTitle>
                    <DialogContent>
                      <DialogContentText id="alert-dialog-description">
                        Are you sure you want to delete your custom card?
                      </DialogContentText>
                    </DialogContent>
                    <DialogActions>
                      <Button onClick={this.cancelDeleteCard}>Cancel</Button>
                      <Button color="warning" onClick={this.finishDeleteCard} autoFocus>
                        Delete
                      </Button>
                    </DialogActions>
                </Dialog>            
            </ThemeProvider>
        );
    }
}

export default Profile;