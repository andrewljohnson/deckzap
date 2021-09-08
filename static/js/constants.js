import * as PIXI from 'pixi.js'
import { Card } from './Card.js';
import { AdjustmentFilter, DropShadowFilter, GlowFilter } from 'pixi-filters';


// constants recognized by the game rules engine
export const artifactCardType = "artifact";
export const mobCardType = "mob";
export const spellCardType = "spell";

// file/networking
export const cardImagesPath = "/static/images/card-art/";
export const largeSpriteQueryString = "?large";

// colors
export const blackColor = 0x000000;
export const whiteColor = 0xFFFFFF;
export const brownColor = 0x765C48;
export const redColor = 0xff0000;
export const blueColor = 0x0000ff;
export const lightRedColor = 0xff7b7b;
export const lightBrownColor = 0xDFBF9F;
export const yellowColor = 0xEAFF00;
export const greenColor = 0x00FF00;
export const darkGrayColor = 0xAAAAAA;
export const lightGrayColor = 0xEEEEEE;
export const menuGrayColor = 0x969696;

// styles
export const titleFontSize = 24;
export const h2FontSize = 16;
export const defaultButtonFontSize = 16;
export const defaultFontSize = 12;
export const defaultFontSizeSmall = 10;
export const defaultFontFamily = "Arial";
export const padding = 5;

export function textOptions() {
    return {
    	fontFamily : defaultFontFamily, 
    	fontSize: defaultFontSize, 
    	fill : blackColor, 
    	wordWrap: true, 
    	wordWrapWidth: 75
    };
}

// filters
export function canBeClickedFilter() {
    return new GlowFilter({ innerStrength: 1, outerStrength: 1, color: greenColor});
}

export function cantBeTargettedFilter() {
    return new AdjustmentFilter({ alpha: .5});
}

export function cantBeClickedFilter() {
    return new AdjustmentFilter({ brightness: .7});
}

export function dropshadowFilter() {
    return new GlowFilter({ outerStrength: 1 , color: blackColor});
}

export function targettableGlowFilter() {
    return new GlowFilter({ innerStrength: 2, outerStrength: 2, color: greenColor});
}

export function targettingGlowFilter() {
    return new GlowFilter({ innerStrength: 2, outerStrength: 2, color: yellowColor});
}

export function lurkerFilter() {
    return new GlowFilter({ outerStrength: 0, innerStrength: 3, color: blackColor});
}

export function shieldFilter() {
    return new GlowFilter({ outerStrength: 0, innerStrength: 3, color: whiteColor});
}

// Game UX
export const beingCastCardAlpha = .3;

export function manaGems(maxMana, currentMana, icon, iconColor) {
    const background = new PIXI.Container();
    let xPixels = 0;
    let gemSize = defaultFontSize;
    if (!icon) {
        icon = "amethyst.svg";
    }
    for (let i=0;i<currentMana;i++) {
        let imageSprite = new PIXI.Sprite.from(PIXI.Texture.from(cardImagesPath + icon));
        if (iconColor) {
            imageSprite.tint = iconColor;                
        } else {
            imageSprite.tint = blueColor;                
        }
        imageSprite.height = gemSize;
        imageSprite.width = gemSize;
        imageSprite.position.x = xPixels;
        imageSprite.position.y = 0;
        background.addChild(imageSprite)
        xPixels += gemSize + 1;
    }
    for (let i=0;i<maxMana-currentMana;i++) {
        let imageSprite = new PIXI.Sprite.from(PIXI.Texture.from(cardImagesPath + icon));
        if (iconColor) {
            imageSprite.tint = iconColor;                
        } else {
            imageSprite.tint = blueColor;                
        }
        imageSprite.height = gemSize;
        imageSprite.width = gemSize;
        imageSprite.position.x = xPixels;
        imageSprite.position.y = 0;
        imageSprite.alpha = beingCastCardAlpha;
        background.addChild(imageSprite)
        xPixels += gemSize + 1;
    }
    return background
}

export function roundRectangle(sprite, cornerRadius) {
    let graphics = new PIXI.Graphics();
    graphics.beginFill(blackColor);
    graphics.drawRoundedRect(
        0,
        0,
        sprite.width,
        sprite.height,
        cornerRadius
    );
    graphics.endFill();
    sprite.mask = graphics;
    sprite.addChild(graphics)
}

export function background(x, y, width, cornerRadius) {
    const background = new PIXI.Sprite.from(PIXI.Texture.WHITE);
    background.tint = blueColor;          
    roundRectangle(background, cornerRadius)
    background.position.x = x;
    background.position.y = y;
    background.width = width;
    return background
}

export function ovalSprite(pixiUX, imageName, labelText, choiceWidth, choiceHeight, choiceID, x, y, clickFunction) {
    let ovalSprite = new PIXI.Sprite.from(PIXI.Texture.from("/static/images/card-art/" + imageName));
    ovalSprite.anchor.set (.5);
    ovalSprite.interactive = true;
    ovalSprite.buttonMode = true;
    ovalSprite.id = choiceID;
    Card.ellipsifyImageSprite(ovalSprite, null, choiceWidth, choiceHeight);
    ovalSprite.position.x = x; 
    ovalSprite.position.y = y;
    pixiUX.app.stage.addChild(ovalSprite);

    let labelOptions = {align: 'center', fontFamily : defaultFontFamily, fontSize: h2FontSize, fill : yellowColor, stroke: blueColor, strokeThickness: 4};
    let label = new PIXI.Text(labelText, labelOptions);
    label.anchor.set(.5);
    label.position.y = choiceHeight - choiceHeight/1.5;
    ovalSprite.addChild(label);
    ovalSprite
        .on("click", clickFunction)
        .on("tap", clickFunction)
    return ovalSprite;
}

export function getSearchParameters() {
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

export function setUpPIXIApp(appOwner, appHeight=855, appWidth=1160) {
        PIXI.GRAPHICS_CURVES.adaptive = true
        PIXI.settings.FILTER_RESOLUTION = window.devicePixelRatio || 1;
        appOwner.app = new PIXI.Application({
            antialias: true,
            autoDensity: true,
            backgroundColor: whiteColor,
            height: appHeight,
            width: appWidth, 
            resolution: PIXI.settings.FILTER_RESOLUTION,
        });        
}