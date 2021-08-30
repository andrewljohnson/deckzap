import * as PIXI from 'pixi.js'
import { AdjustmentFilter, DropShadowFilter, GlowFilter } from 'pixi-filters';

// file system
export const cardImagesPath = "/static/images/card-art/";

// constants recognized by the game rules engine
export const artifactCardType = "artifact";
export const mobCardType = "mob";
export const spellCardType = "spell";

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
export const defaultFontSize = 12;
export const defaultFontSizeSmall = 8;
export const defaultFontFamily = "Arial";
export const padding = 5;

export function textOptions() {
    return {
    	fontFamily : defaultFontFamily, 
    	fontSize: defaultFontSizeSmall, 
    	fill : blackColor, 
    	wordWrap: true, 
    	wordWrapWidth: 75
    };
}

// networking
export const largeSpriteQueryString = "?large";


// filters
export function glowAndShadowFilters() {
    return [
        targettableGlowFilter(),
        dropshadowFilter()
    ];
}

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

export function targettingGlowFilter() {
    return new GlowFilter({ innerStrength: 2, outerStrength: 2, color: yellowColor});
}

export function targettableGlowFilter() {
    return new GlowFilter({ innerStrength: 2, outerStrength: 2, color: greenColor});
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

