import * as PIXI from 'pixi.js'
import * as Constants from '../../constants.js';
import { Card } from '../../components/Card.js';
import { SVGRasterizer } from '../../components/SVGRasterizer.js';


export class CardBuilderBase {

    constructor(containerID) {
        this.setUpPIXIApp();
    }

    setUpPIXIApp() {
        const widthInCards = 9;
        const appWidth = Card.cardWidth * widthInCards + Constants.padding * widthInCards
        const appHeight = (Card.cardHeight) * 15;
        Constants.setUpPIXIApp(this, appHeight, appWidth)
    }

    loadUX(containerID) {
        const container = document.getElementById(containerID);
        container.appendChild(this.app.view);

        const background = Constants.background(0, 0, (Card.cardWidth + Constants.padding) * 5 + Constants.padding * 4, .1)
        background.tint = 0xEEEEEE;
        background.height = (Card.cardHeight) * 12
        this.app.stage.addChild(background);
        const titleText = this.addTitle();
        this.addNextButton();
        this.addErrorText();
        this.toggleNextButton(false);
        this.rasterizer = new SVGRasterizer(this.app);
        this.rasterizer.loadCardImages([this.cardInfo()]);
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
        const title = this.title();
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
        const buttonTitle = this.nextButtonTitle();
        const b = Card.button(
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

    addErrorText() {
        this.errorText = new PIXI.Text("", {fontFamily : Constants.defaultFontFamily, fontSize: Constants.defaultFontSize, fill : Constants.redColor, wordWrap: true, wordWrapWidth: this.nextButton.width});
        this.errorText.position.x = this.nextButton.position.x;
        this.errorText.position.y = this.nextButton.position.y + this.nextButton.height + Constants.padding;
        this.app.stage.addChild(this.errorText);                
    }

    toggleNextButton(enabled, errorMessage="") {
        this.errorText.text = "";
        if (this.errorArrow) {
            this.errorArrow.parent.removeChild(this.errorArrow);
            this.errorArrow = null;
        }
        if (this.powerPoints && this.powerPoints >= 100) {
            enabled = false;
            this.errorText.text = "Cards must have less than 100 power points.";
            this.errorArrow = Constants.showArrow(this.app, this.errorText, this.card, {x:Constants.padding*2.5, y: Constants.padding*4}, {x:this.nextButton.width - 10, y: 10});
        } else if (!enabled) {
            this.errorText.text = errorMessage;
        }
        this.nextButton.background.tint = enabled ? Constants.blueColor : Constants.darkGrayColor;
        this.nextButton.background.buttonMode = enabled;
        this.nextButton.background.interactive = enabled;
    }

    updateCard() {
        if (this.card) {
            this.card.parent.removeChild(this.card);
            this.card = null;
        }
        this.addCardSprite();
    }

    addCardSprite() {
        const cardSprite = Card.sprite(this.cardInfo(), this);
        const cardHeight = Card.cardHeight;
        cardSprite.position.x = this.errorText.position.x + Card.cardWidth * 1.25 / 2;
        cardSprite.position.y = this.errorText.position.y + 140;            
        this.app.stage.addChild(cardSprite);
        cardSprite.interactive = true;
        this.card = cardSprite;
    }

    baseURL() {
        return "/create_card";
    }

    defaultCardName() {
        return "Unnamed Card";
    }

    defaultCardImageFilename() {
        return "uncertainty.svg";
    }

    cardDescription() {
        if (this.originalCardInfo && this.originalCardInfo.effects && this.originalCardInfo.effects.length) {
            return this.descriptionForEffects(this.originalCardInfo.effects);
        }
    }

    descriptionForEffects(effects) {
        let description = "";
        for (const effect of effects) {
            description += effect.description;
            if (!effect.description.endsWith(".")) {
                description += ".";
            }
            if (effect != effects[effects.length - 1]) {
                description += " ";
            }
        }
        return description;
    }

    async getPowerPoints() {
        const json = await Constants.postData(`${this.baseURL()}/get_power_points`, { card_info: this.cardInfo(), card_id: this.cardID })
        if("error" in json) {
            console.log(json); 
            alert("error fetching power points");
        } else {
            this.powerPoints = json.power_points;
            this.updateCard();

        }
    }

    // functions overriden by subclasses 

    cardInfo() {
        let info;
        if (this.originalCardInfo) {
            info = this.originalCardInfo;
        } else {
            info = {};
        }
        if (!this.originalCardInfo || !this.originalCardInfo.name) {
            info.name = this.defaultCardName();

        }
        if (!this.originalCardInfo || !this.originalCardInfo.image) {
            info.image = this.defaultCardImageFilename();

        }
        info.description = this.cardDescription();
        if (this.powerPoints != null) {
            info.power_points = this.powerPoints;
        }
        return info;
    }

    initializeProperties() { }

    loadUXAfterCardImageLoads() { }

    title() {
        return "";
    }

    nextButtonTitle() {
        return "Next";
    }

    async nextButtonClicked() { }
}
