import * as PIXI from 'pixi.js'
import { Card } from './Card.js';
import * as Constants from '../Constants.js';


export class GameNavigator {

	constructor(pixiUX, xPosition, yPosition, backFunction, forwardFunction, resumeFunction) {
	    const buttonSize = 90;

        let backButtonColor = Constants.darkGrayColor;
        // the 2 is so players can't navigate before the initial join moves
        if ((!pixiUX.parentGame && pixiUX.game.moves.length > 2 ) || 
            (pixiUX.parentGame && pixiUX.review_move_index > 2)) {
            backButtonColor = Constants.blueColor
        }
		let backButton = Card.button(
                "Back", 
                backButtonColor, 
	             Constants.whiteColor, 
                xPosition, 
                yPosition,
                backFunction
        )
        pixiUX.app.stage.addChild(backButton);
        if (pixiUX.parentGame && 
            pixiUX.review_move_index <= 2) {
            backButton.interactive = false;
        }

        let forwardButtonColor = Constants.darkGrayColor;
        if (pixiUX.is_reviewing && 
            pixiUX.review_move_index < pixiUX.parentGame.moves.length) {
            forwardButtonColor = Constants.blueColor
        }
		let forwardButton = Card.button(
                "Forward", 
                forwardButtonColor, 
                Constants.whiteColor, 
                xPosition + Constants.padding * 2 + buttonSize, 
                yPosition,
                forwardFunction
        )
        pixiUX.app.stage.addChild(forwardButton);
        if (!pixiUX.parentGame || 
            pixiUX.review_move_index == pixiUX.parentGame.moves.length) {
            backButton.interactive = false;
        }

        let resumeButtonColor = Constants.darkGrayColor;
        if (pixiUX.is_reviewing) {
            resumeButtonColor = Constants.blueColor
        }
        let resumeButton = Card.button(
                "Resume", 
                resumeButtonColor, 
                Constants.whiteColor, 
                xPosition + Constants.padding * 6 + buttonSize * 2, 
                yPosition,
                resumeFunction
        )
        pixiUX.app.stage.addChild(resumeButton);

       	this.position = backButton.position;

        this.backButton = backButton;
        this.forwardButton = forwardButton;
        this.resumeButton = resumeButton;

	}

    clear() {
        this.resumeButton.parent.removeChild(this.backButton);
        this.resumeButton.parent.removeChild(this.forwardButton);
        this.resumeButton.parent.removeChild(this.resumeButton);
    }

}