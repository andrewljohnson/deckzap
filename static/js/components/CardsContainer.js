import * as PIXI from 'pixi.js'
import { Card } from './Card.js';
import * as Constants from '../constants.js';


export class CardsContainer {

    constructor(pixiUX, cards, allCards, cardWidth, x, y) {
        this.pixiUX = pixiUX;
        this.cards = cards;
        this.allCards = allCards;
        this.cardWidth = cardWidth;
        this.cardSprites = [];

        const background = new PIXI.Sprite.from(PIXI.Texture.WHITE);
        background.tint = Constants.blueColor;            
        Constants.roundRectangle(background, .1)
        pixiUX.app.stage.addChild(background)
        background.position.x = x;
        background.position.y = y;
        background.width = (Card.cardWidth + Constants.padding) * cardWidth + Constants.padding;
        this.background = background;
    }

    redisplayDeck() {
        for (let sprite of this.cardSprites) {
            this.pixiUX.app.stage.removeChild(sprite);
        }
        this.cards = Card.cardsForCardList(this.deck.cards, this.allCards);

        let loadingImages = this.pixiUX.rasterizer.loadCardImages(this.cards);
        this.pixiUX.app.loader.load(() => {
            this.cardSprites = [];
            this.cards.forEach((card, i) => {
                this.addCardToContainer(card, i);
            });
            this.pixiUX.app.loader.reset()
        });
        let cardHeight = Card.cardHeight + Constants.padding * 2;
        this.background.height = Math.max(275, (this.cards.length / this.cardWidth + .5) * cardHeight);
    }

    addCardToContainer(card, index) {
        let pixiUX = this;
        let cardSprite = Card.sprite(card, this.pixiUX);
        let cardHeight = Card.cardHeight;
        cardSprite.position.x = (Card.cardWidth + Constants.padding) *  (index % this.cardWidth) + Card.cardWidth/2 + this.background.position.x + Constants.padding;
        cardSprite.position.y = cardHeight/2 + (cardHeight + 5) * Math.floor(index / this.cardWidth) + this.background.position.y + Constants.padding;            
        this.pixiUX.app.stage.addChild(cardSprite);
        this.cardSprites.push(cardSprite)
        cardSprite.interactive = true;
        return cardSprite;
    }

}
