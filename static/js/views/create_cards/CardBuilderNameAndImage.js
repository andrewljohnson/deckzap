import * as PIXI from 'pixi.js'
const TextInput = require("pixi-text-input");
import * as Constants from '../../Constants.js';
import { Card } from '../../components/Card.js';
import { CardBuilderBase } from './CardBuilderBase.js'
import { Scrollbox } from 'pixi-scrollbox'
import { SVGRasterizer } from '../../components/SVGRasterizer.js';
import { OutlineFilter } from 'pixi-filters';

export class CardBuilderNameAndImage extends CardBuilderBase {

    constructor(containerID, originalCardInfo, cardID, imagePaths) {
        super(containerID)
        this.originalCardInfo = originalCardInfo;
        this.effects = originalCardInfo.effects ? originalCardInfo.effects : [];
        this.cardID = cardID;
        this.imagePaths = imagePaths;
        this.loadUX(containerID);
    }

    cardInfo() {
        return {
            name: this.cardName(), 
            card_type: this.originalCardInfo.card_type, 
            cost: this.originalCardInfo.cost, 
            image: this.cardImage(), 
            effects: this.originalCardInfo.effects, 
            strength: this.originalCardInfo.strength, 
            hit_points: this.originalCardInfo.hit_points, 
            description:this.cardDescription()
        };
    }

    loadUXAfterCardImageLoads() {
        super.loadUXAfterCardImageLoads()
        const yPosition = this.titleText.position.y + this.titleText.height + Constants.padding * 4;
        this.addNameInput(Constants.padding * 2, yPosition)
        this.addImagePicker(yPosition + 100);
        this.updateCard();
    }

    cardName() {
        if (this.userCardName) {
            return this.userCardName;
        }
        return this.defaultCardName();
    }

    cardImage() {
        if (this.userCardImage) {
            return this.userCardImage;
        }
        return this.defaultCardImageFilename();
    }

    title() {
        return "Choose Name and Image"
    }

    nextButtonClicked() {
        Constants.postData(`${this.baseURL()}/save_name_and_image`, { card_info: this.cardInfo(), card_id: this.cardID })
        .then(data => {
            if("error" in data) {
                console.log(data); 
                alert("error saving card");
            } else {
                window.location.href = `/`
            }
        })
    }

    nextButtonTitle() {
        return "Save Card"
    }

    updateCard() {
        super.updateCard();
    }     

    addNameInput(x, y) {
        const nameLabel = new PIXI.Text("Card Name", {fontFamily : Constants.defaultFontFamily, fontSize: Constants.defaultButtonFontSize, fill : Constants.blackColor});
        nameLabel.position.x = x;
        nameLabel.position.y = y;
        this.app.stage.addChild(nameLabel);    

        let nameInput = new TextInput({
            input: {
                fontSize: '14pt',
                width: (200 - 5) + 'px',
                textAlign: 'center',
            }, 
            box: {
                borderWidth: '1px',
                stroke: 'black',
                borderStyle: 'solid',
            }
        })
        nameInput.placeholder = this.defaultCardName();
        nameInput.position.x = x;
        nameInput.position.y = nameLabel.position.y + nameLabel.height + Constants.padding * 4;
        this.app.stage.addChild(nameInput);
        const cardImagesPath = this.customImagesURL();
        nameInput.on('input', text => {
            this.newText = text;
            if (this.doneTyping) {
                clearTimeout(this.doneTyping);                
            }
            this.doneTyping = setTimeout(()=>{ 
                this.imageScrollbox.content.interactiveChildren = false;
                this.clearTextureCache(cardImagesPath, this.cardImage());
                this.userCardName = text;
                const rasterizer = new SVGRasterizer(this.app, cardImagesPath);
                rasterizer.loadCardImages([this.cardInfo()]);
                this.app.loader.load(() => {
                    this.updateCard()
                    this.app.loader.reset()
                    this.imageScrollbox.content.interactiveChildren = true;

                });        
            }, 200)

        })
    }

    customImagesURL() {
        return "/static/images/card-art-custom/";
    }

    addImagePicker(yPosition) {
        const scrollboxWidth = 250;
        const scrollboxHeight = 600;
        const scrollbox = new Scrollbox({ boxWidth: scrollboxWidth, boxHeight: scrollboxHeight})
        scrollbox.position.x = Constants.padding * 2;
        scrollbox.position.y = yPosition;
        const background = new PIXI.Sprite.from(PIXI.Texture.WHITE);
        background.tint = Constants.whiteColor
        background.width = scrollboxWidth;
        background.height = 20 * this.imagePaths.length;
        scrollbox.content.addChild(background);
        scrollbox.content.filters = [
          new OutlineFilter(1, Constants.blackColor),
        ]
        this.app.stage.addChild(scrollbox);
        this.imageScrollbox = scrollbox;

        let line = -1;
        const bmFontName = "bmArial";
        const font = PIXI.BitmapFont.from(
            bmFontName, 
            { fontFamily: "Arial", fontSize: 12 }, 
            { resolution: window.devicePixelRatio }
        );
        const self = this;
        const unselectedAlpha = .6;
        for (let text of this.imagePaths) {
            line += 1
            let textSprite = new PIXI.BitmapText(text.name, {fontName: bmFontName, wordWrap: true, wordWrapWidth: 360});
            textSprite.alpha = unselectedAlpha;
            textSprite.position.x = 5;
            textSprite.position.y = line * 20 + 5;
            textSprite.imageInfo = text;
            textSprite.on("click", function (e) { 
                scrollbox.content.interactiveChildren = false;
                if (self.selectedImageText) {
                    self.selectedImageText.alpha = unselectedAlpha;
                }
                self.userCardImage = this.imageInfo.filename;
                const cardImagesPath = self.customImagesURL();
                self.clearTextureCache(cardImagesPath, this.imageInfo.filename);
                const rasterizer = new SVGRasterizer(self.app, cardImagesPath);
                rasterizer.loadCardImages([self.cardInfo()]);
                self.app.loader.load(() => {
                    self.updateCard()
                    self.app.loader.reset()
                    scrollbox.content.interactiveChildren = true;
                });        
                self.selectedImageText = this;
                this.alpha = 1;
            })
            textSprite.buttonMode = true;
            textSprite.interactive = true;
            scrollbox.content.addChild(textSprite);
        }

    }

    clearTextureCache(cardImagesPath, filename) {
        let fullPath = window.location.protocol + "//" + window.location.host + cardImagesPath + filename
        PIXI.BaseTexture.removeFromCache(fullPath)
        PIXI.Texture.removeFromCache(fullPath)
        PIXI.BaseTexture.removeFromCache(fullPath + "?large")
        PIXI.Texture.removeFromCache(fullPath + "?large")
        PIXI.BaseTexture.removeFromCache(this.cardName())
        PIXI.Texture.removeFromCache(this.cardName())
        PIXI.BaseTexture.removeFromCache(this.cardName() + "?large")
        PIXI.Texture.removeFromCache(this.cardName() + "?large")        
    }

    updateCard() {
        super.updateCard();
        this.toggleNextButton(this.userCardName && this.userCardImage);
    }

}
