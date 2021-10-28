import * as PIXI from 'pixi.js'
import * as Constants from '../Constants.js';
import { Card } from '../components/Card.js';
import { SVGRasterizer } from '../components/SVGRasterizer.js';


export class CardBuilderBase {

    constructor(containerID) {
        this.setUpPIXIApp();
    }

    setUpPIXIApp() {
        const widthInCards = 9;
        let appWidth = Card.cardWidth * widthInCards + Constants.padding * widthInCards
        let appHeight = (Card.cardHeight) * 15;
        Constants.setUpPIXIApp(this, appHeight, appWidth)
    }

    loadUX(containerID) {
        let container = document.getElementById(containerID);
        container.appendChild(this.app.view);

        let background = Constants.background(0, 0, (Card.cardWidth + Constants.padding) * 5 + Constants.padding * 4, .1)
        background.tint = 0xEEEEEE;
        background.height = (Card.cardHeight) * 12
        this.app.stage.addChild(background);
        let titleText = this.addTitle();
        this.addNextButton();
        new SVGRasterizer(this.app).loadCardImages([this.cardInfo()]);
        this.app.loader.load(() => {
            this.addTitle();
            this.addNextButton();
            this.loadUXAfterCardImageLoads();
            this.app.loader.reset()
        });        
    }

    loadUXAfterCardImageLoads() {
        this.addCardSprite();
        this.app.loader.reset()
    }

    addTitle() {
        let title = this.title();
        this.titleText = new PIXI.Text(title, {fontFamily : Constants.defaultFontFamily, fontSize: Constants.titleFontSize, fill : Constants.blackColor});
        this.titleText.position.x = Constants.padding;
        this.titleText.position.y = Constants.padding * 1.5;
        this.app.stage.addChild(this.titleText);        
        return this.titleText;
    }

    addNextButton() {
        const buttonWidth = Card.cardWidth * 1.25;
        const buttonHeight = 40;
        const buttonX = this.app.renderer.width / this.app.renderer.resolution - buttonWidth - Constants.padding - Card.cardWidth * 2 + Constants.padding * 2;
        let buttonTitle = this.nextButtonTitle();
        let b = Card.button(
            buttonTitle, 
            Constants.blueColor, 
            Constants.whiteColor, 
            buttonX, 
            -buttonHeight - 16,
            () => {
                this.nextButtonClicked();
            },
            null,
            buttonWidth
        );
        this.nextButton = b
        this.app.stage.addChild(b);
        return b;
    }

    updateCard() {
        if (this.card) {
            this.card.parent.removeChild(this.card);
            this.card = null;
        }
        this.addCardSprite();
    }

    addCardSprite() {
        console.log("addCardSprite")
        console.log(this.cardInfo())
        let cardSprite = Card.sprite(this.cardInfo(), this);
        let cardHeight = Card.cardHeight;
        cardSprite.position.x = this.nextButton.position.x + Card.cardWidth * 1.25 / 2;
        cardSprite.position.y = this.nextButton.position.y + 200;            
        this.app.stage.addChild(cardSprite);
        cardSprite.interactive = true;
        this.card = cardSprite;
    }

    cardDescription() {
        if (this.effects && this.effects.length) {
            return this.effects[0].description;
        }
        if (this.originalCardInfo.effects && this.originalCardInfo.effects.length) {
            return this.originalCardInfo.effects[0].description;
        }
    }

    cardInfo() {
        return {};
    }

    initializeProperties() { }

    loadUXAfterCardImageLoads() { }

    title() {
        return ""
    }

    nextButtonTitle() {
        return "Next"
    }

    nextButtonClicked() { }

}
