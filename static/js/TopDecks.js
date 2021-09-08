import * as PIXI from 'pixi.js'
import * as Constants from './constants.js';
import { Card } from './Card.js';
import { TopPlayers } from './TopPlayers.js';

export class TopDecks {
	constructor(containerID, decks) {
		this.decks = decks;
		this.setUpPIXIApp()
		this.loadUX(containerID);
	}

	setUpPIXIApp() {
		this.cardWidth = 7;
		let appWidth = 1160;
		let appHeight = 750;
        PIXI.settings.FILTER_RESOLUTION = window.devicePixelRatio || 1;
        this.app = new PIXI.Application({
            antialias: true,
            autoDensity: true,
            backgroundColor: Constants.whiteColor,
            height: appHeight,
            width: appWidth, 
            resolution: PIXI.settings.FILTER_RESOLUTION,
        });        
	}

	loadUX(containerID) {			
		let container = document.getElementById(containerID);
		container.appendChild(this.app.view);

		let background = Constants.background(0, 0, Card.cardWidth * (this.cardWidth-1), .1)
		background.tint = 0xEEEEEE;
		background.height = 750
		this.app.stage.addChild(background);

        let titleText = TopPlayers.addTitle(this.app, "Top Decks")

        let index = 0;
        let yPosition = titleText.position.y + Constants.padding * 9 + Constants.padding * 5 * index
        const leftPadding = Constants.padding;

    	let sortParameter = getSearchParameters()["sort"];
    	let orderParameter = getSearchParameters()["order"];
    	TopPlayers.addHeaderCellFor(this.app, Constants.padding + leftPadding, yPosition, "top_decks", sortParameter, orderParameter, "descending", "title", "Title", 0)    	
    	TopPlayers.addHeaderCellFor(this.app, 190 + leftPadding, yPosition, "top_decks", sortParameter, orderParameter, "descending", "author", "Author")    	
    	TopPlayers.addHeaderCellFor(this.app, 350 + leftPadding, yPosition, "top_decks", sortParameter, orderParameter, "ascending", "win_rate", "Win Rate")    	
    	TopPlayers.addHeaderCellFor(this.app, 450 + leftPadding, yPosition, "top_decks", sortParameter, orderParameter, "descending", "wins", "Wins")
    	TopPlayers.addHeaderCellFor(this.app, 550 + leftPadding, yPosition, "top_decks", sortParameter, orderParameter, "descending", "losses", "Losses")

        for (let deck of this.decks) {
	        index += 1;
	        yPosition = titleText.position.y + Constants.padding * 10 + Constants.padding * 6 * index
        	const cell = TopPlayers.addCell(this.app, deck.title, Constants.padding + leftPadding, yPosition, true, Constants.blueColor, 0, ()=>{window.location.href=`/build_deck?deck_id=${deck.id}`})
        	TopPlayers.toggleUnderline(cell, 0);
        	const cellAuthor = TopPlayers.addCell(this.app, deck.author, 190 + leftPadding, yPosition, true, Constants.blueColor, 0.5, ()=>{window.location.href=`/u/${deck.author}`})
        	TopPlayers.toggleUnderline(cellAuthor, 0.5);
        	TopPlayers.addCell(this.app, parseFloat(deck.win_rate).toFixed(3)*100+"%", 350 + leftPadding, yPosition)
        	TopPlayers.addCell(this.app, deck.wins, 450 + leftPadding, yPosition)
        	TopPlayers.addCell(this.app, deck.losses, 550 + leftPadding, yPosition)
        }
	}
}


function getSearchParameters() {
    let prmstr = window.location.search.substr(1);
    return prmstr != null && prmstr != "" ? transformToAssocArray(prmstr) : {};
}

function transformToAssocArray( prmstr ) {
    let params = {};
    let prmarr = prmstr.split("&");
    for ( let i = 0; i < prmarr.length; i++) {
        let tmparr = prmarr[i].split("=");
        params[tmparr[0]] = tmparr[1];
    }
    return params;
}