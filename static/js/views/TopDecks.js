import * as PIXI from 'pixi.js'
import * as Constants from '../constants.js';
import { Card } from '../components/Card.js';
import { TopPlayers } from './TopPlayers.js';


export class TopDecks {

    constructor(containerID, decks) {
        this.decks = decks;
        this.cardWidth = 7;
        Constants.setUpPIXIApp(this, 750)
        this.loadUX(containerID);
    }

    loadUX(containerID) {            
        let container = document.getElementById(containerID);
        container.appendChild(this.app.view);
        TopPlayers.addBackground(this);
        let titleText = TopPlayers.addTitle(this.app, "Top Decks")

        let index = 0;
        let yPosition = titleText.position.y + Constants.padding * 9
        const leftPadding = Constants.padding;
        let sortParameter = Constants.getSearchParameters()["sort"];
        let orderParameter = Constants.getSearchParameters()["order"];
        TopPlayers.addHeaderCellFor(this.app, Constants.padding + leftPadding, yPosition, "top_decks", sortParameter, orderParameter, "descending", "title", "Title", 0)        
        TopPlayers.addHeaderCellFor(this.app, 190 + leftPadding, yPosition, "top_decks", sortParameter, orderParameter, "descending", "author", "Author")        
        TopPlayers.addHeaderCellFor(this.app, 350 + leftPadding, yPosition, "top_decks", sortParameter, orderParameter, "ascending", "win_rate", "Win Rate")        
        TopPlayers.addHeaderCellFor(this.app, 450 + leftPadding, yPosition, "top_decks", sortParameter, orderParameter, "descending", "wins", "Wins")
        TopPlayers.addHeaderCellFor(this.app, 550 + leftPadding, yPosition, "top_decks", sortParameter, orderParameter, "descending", "losses", "Losses")

        for (let deck of this.decks) {
            index += 1;
            yPosition = titleText.position.y + Constants.padding * 10 + Constants.padding * 6 * index
            const cell = TopPlayers.addCell(this.app, deck.title, Constants.padding + leftPadding, yPosition, true, Constants.blueColor, 0, ()=>{window.location.href=`/build_deck?global_deck_id=${deck.id}`})
            TopPlayers.toggleUnderline(cell, 0);
            const cellAuthor = TopPlayers.addCell(this.app, deck.author, 190 + leftPadding, yPosition, true, Constants.blueColor, 0.5, ()=>{window.location.href=`/u/${deck.author}`})
            TopPlayers.toggleUnderline(cellAuthor, 0.5);
            TopPlayers.addCell(this.app, parseFloat(deck.win_rate).toFixed(3)*100+"%", 350 + leftPadding, yPosition)
            TopPlayers.addCell(this.app, deck.wins, 450 + leftPadding, yPosition)
            TopPlayers.addCell(this.app, deck.losses, 550 + leftPadding, yPosition)
        }
    }

}
