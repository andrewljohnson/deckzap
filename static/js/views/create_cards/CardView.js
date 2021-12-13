import * as Constants from '../../constants.js';
import { Card } from '../../components/Card.js';
import { SVGRasterizer } from '../../components/SVGRasterizer.js';
import * as PIXI from 'pixi.js'

class CardView {

    constructor(containerID, cardInfo) {
        this.setUpPIXIApp();
        this.cardInfo = cardInfo;
        this.loadUX(containerID);
    }

    setUpPIXIApp() {
        const widthInCards = 1;
        const appWidth = Card.cardWidth;
        const appHeight = (Card.cardHeight) + Constants.padding * 2;
        Constants.setUpPIXIApp(this, appHeight, appWidth)
    }

    setProperty(key, value) {
        this.cardInfo[key] = value;
        if (key == "name" || key == "image") {
            const cardImagesPath = this.customImagesURL();
            this.clearTextureCache(cardImagesPath, this.cardInfo.image);
            if (key === "name") {
                this.clearTextureCache("/static/images/card-art/", this.cardInfo.image);
            }
            const rasterizer = new SVGRasterizer(this.app);
            rasterizer.loadCardImages([this.cardInfo]);
            this.app.loader.load(() => {
                this.updateCard()
                this.app.loader.reset()
            });        
        } else {
            this.updateCard();
        }
    }

    clearTextureCache(cardImagesPath, filename) {
        let fullPath = window.location.protocol + "//" + window.location.host + cardImagesPath + filename
        PIXI.BaseTexture.removeFromCache(fullPath)
        PIXI.Texture.removeFromCache(fullPath)
        PIXI.BaseTexture.removeFromCache(fullPath + "?large")
        PIXI.Texture.removeFromCache(fullPath + "?large")
        PIXI.BaseTexture.removeFromCache(this.cardInfo.name)
        PIXI.Texture.removeFromCache(this.cardInfo.name)
        PIXI.BaseTexture.removeFromCache(this.cardInfo.name + "?large")
        PIXI.Texture.removeFromCache(this.cardInfo.name + "?large")        
    }

    customImagesURL() {
        return "/static/images/card-art-custom/";
    }
    
    loadUX(containerID) {
        const container = document.getElementById(containerID);
        container.appendChild(this.app.view);

        this.rasterizer = new SVGRasterizer(this.app);
        this.rasterizer.loadCardImages([this.cardInfo]);
        this.app.loader.load(() => {
            this.updateCard();
            this.app.loader.reset()
        });        
    }

    addCardSprite() {
        const cardSprite = Card.sprite(this.cardInfo, this);
        const cardHeight = Card.cardHeight;
        cardSprite.position.x = Card.cardWidth / 2;
        cardSprite.position.y = Card.cardHeight / 2 + Constants.padding * 2;
        this.app.stage.addChild(cardSprite);
        cardSprite.interactive = true;
        this.card = cardSprite;
    }

    updateCard() {
        if (this.card) {
            this.card.parent.removeChild(this.card);
            this.card = null;
        }
        this.addCardSprite();
    }
}

export default CardView;


