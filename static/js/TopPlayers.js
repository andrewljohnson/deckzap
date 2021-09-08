import * as PIXI from 'pixi.js'
import * as Constants from './constants.js';
import { Card } from './Card.js';

export class TopPlayers {
	constructor(containerID, players) {
		this.players = players;
		console.log(this.players);
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

        let titleText = TopPlayers.addTitle(this.app, "Top Players")

        let index = 0;
        let yPosition = titleText.position.y + Constants.padding * 9 + Constants.padding * 5 * index
        const leftPadding = Constants.padding;

    	let sortParameter = getSearchParameters()["sort"];
    	let orderParameter = getSearchParameters()["order"];
    	TopPlayers.addHeaderCellFor(this.app, Constants.padding + leftPadding, yPosition, "top_players", sortParameter, orderParameter, "descending", "username", "Username", 0)    	
    	TopPlayers.addHeaderCellFor(this.app, 175 + leftPadding, yPosition, "top_players", sortParameter, orderParameter, "ascending", "win_rate", "Win Rate")    	
    	TopPlayers.addHeaderCellFor(this.app, 275 + leftPadding, yPosition, "top_players", sortParameter, orderParameter, "descending", "wins", "Wins")
    	TopPlayers.addHeaderCellFor(this.app, 375 + leftPadding, yPosition, "top_players", sortParameter, orderParameter, "descending", "losses", "Losses")

        for (let player of this.players) {
	        index += 1;
	        yPosition = titleText.position.y + Constants.padding * 10 + Constants.padding * 6 * index
        	const cell = TopPlayers.addCell(this.app, player.username, Constants.padding + leftPadding, yPosition, true, Constants.blueColor, 0, ()=>{window.location.href=`/u/${player.username}`})
        	TopPlayers.toggleUnderline(cell, 0);
        	TopPlayers.addCell(this.app, parseFloat(player.win_rate).toFixed(3)*100+"%", 175 + leftPadding, yPosition)
        	TopPlayers.addCell(this.app, player.wins, 275 + leftPadding, yPosition)
        	TopPlayers.addCell(this.app, player.losses, 375 + leftPadding, yPosition)
        }
	}

	static addHeaderCellFor(app, x, y, baseURL, currentSortParameter, currentOrderParameter, defaultOrder, thisSort, defaultTitle, anchor=0.5) {
    	let url = `/${baseURL}?sort=${thisSort}&order=${defaultOrder}`;
    	let title = defaultTitle
    	if (thisSort == "win_rate" && (currentSortParameter == null || currentSortParameter == "win_rate")) {
			title = `${defaultTitle} ▼`
    	}
    	if (thisSort == currentSortParameter) {
    		if (currentOrderParameter == "ascending") {
		    	title = `${defaultTitle} ▲`
	    		url = `/${baseURL}?sort=${thisSort}&order=descending`;
		    	if (thisSort == "win_rate") {
		    		url = `/${baseURL}`;
		    	}
    		} else {
		    	title = `${defaultTitle} ▼`
	    		url = `/${baseURL}?sort=${thisSort}&order=ascending`;

    		}
    	}
    	TopPlayers.addHeaderCell(app, title, x, y, ()=>{window.location.href=url}, anchor=anchor)
	}

	static addHeaderCell(app, text, x, y, clickFunction, anchor=0.5) {
        let cell = new PIXI.Text(text, {align: "center", fontWeight: "bold", fontFamily : Constants.defaultFontFamily, fontSize: 18, fill : Constants.blueColor});
        cell.anchor.x = anchor
        cell.position.x = x;
        cell.position.y = y;
        cell.buttonMode = true;
        cell.interactive = true;
        cell
            .on("click", clickFunction)
            .on("tap", clickFunction)
        TopPlayers.toggleUnderline(cell, anchor);
        app.stage.addChild(cell);		
	}

	static toggleUnderline(Text, anchor){
	    if (Text.children.length) {return Text.removeChildren()};
	    const ULT = new PIXI.Sprite(PIXI.Texture.WHITE);
	    ULT.tint = Constants.blueColor;
	    ULT.position.y = Text.height
	    ULT.width = Text.width
	    ULT.height = 1
        ULT.anchor.x = anchor;
	    Text.addChild(ULT);
	};

	static addCell(app, text, x, y, interactive=false, fill=Constants.blackColor, anchor=.5, clickFunction=null) {
        let cell = new PIXI.Text(text, {fontFamily : Constants.defaultFontFamily, fontSize: Constants.h2FontSize, fill : fill});
        cell.anchor.x = anchor;
        cell.position.x = x;
        cell.position.y = y;
        if (clickFunction) {
	        cell.buttonMode = interactive;
	        cell.interactive = interactive;
            cell
                .on("click", clickFunction)
                .on("tap", clickFunction)

        }
        app.stage.addChild(cell);	
        return cell;	
	}

	static addTitle(app, titleString) {
		let title = titleString;
        let titleText = new PIXI.Text(title, {fontFamily : Constants.defaultFontFamily, fontSize: Constants.titleFontSize, fill : Constants.blackColor});
        titleText.position.x = Constants.padding;
        titleText.position.y = Constants.padding * 2.5;
        app.stage.addChild(titleText);		
        return titleText;
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