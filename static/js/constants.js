import * as PIXI from 'pixi.js'
import { AdjustmentFilter, DropShadowFilter, GlowFilter } from 'pixi-filters';
import { Card } from './components/Card.js';
import { createTheme } from '@mui/material/styles';


// constants recognized by the game rules engine
export const artifactCardType = "artifact";
export const mobCardType = "mob";
export const spellCardType = "spell";

// file/networking
export const cardImagesPath = "/static/images/card-art/";
export const customCardImagesPath = "/static/images/card-art-custom/";
export const largeSpriteQueryString = "?large";

// colors
export const blackColor = 0x000000;
export const whiteColor = 0xFFFFFF; 
export const brownColor = 0x765C48;
export const redColor = 0xff0000;
export const purpleColor = 0xff00ff;
export const blueColor = 0x0000ff;
export const lightBlueColor = 0xAAAAff;
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

export function glowFilter() {
    return GlowFilter;
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

export function infoListText(discipline) {
    if (discipline == "magic") {
        return "Magic\n\n• 30 card deck\n• more mana each turn\n• draw one card a turn";
    }
    return "Tech\n\n• 15 card deck\n• 3 mana each turn\n• new hand each turn";
}

export async function postData(url, data) {
    const csrftoken = getCookie('csrftoken');
    // Default options are marked with *
    const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken,

        },
        body: JSON.stringify(data) 
    });
    return response.json(); // parses JSON response into native JavaScript objects
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        // Does this cookie string begin with the name we want?
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            break;
        }
        }
    }
    return cookieValue;
}

export function isPositiveWholeNumber(value) {
    return /^-?\d+$/.test(value) && parseInt(value) >= 0;
}

export function showArrow(app, fromSprite, toSprite, adjustment={"x":0, "y": 0}, fromAdjustment={"x":0, "y": 0}){
    let cpXY1 = [30,0];
    let cpXY2 = [200,100];
    let toXY = [toSprite.position.x - fromSprite.position.x + adjustment.x - fromAdjustment.x, toSprite.position.y - fromSprite.position.y + adjustment.y - fromAdjustment.y];
    let fromXY = [fromSprite.position.x + fromAdjustment.x, fromSprite.position.y + fromAdjustment.y];
    let toXYArc = [toSprite.position.x-fromSprite.position.x+toSprite.width/4,
                    toSprite.position.y-fromSprite.position.y+toSprite.height/2];
    let toXYArrow = [toSprite.position.x+toSprite.width/4,
                    toSprite.position.y+toSprite.height/2 - padding];

    const bezierArrow = new PIXI.Graphics();
    bezierArrow.tint = redColor;
    app.stage.addChild(bezierArrow); 
    const normal = [
        - (toXY[1] - cpXY2[1]),
        toXY[0] - cpXY2[0],
    ]
    const l = Math.sqrt(normal[0] ** 2 + normal[1] ** 2);
    normal[0] /= l;
    normal[1] /= l;
    
    let arrowSize = 10;
    const tangent = [
        -normal[1] * arrowSize,
        normal[0] * arrowSize
    ]

    normal[0] *= arrowSize;
    normal[1] *= arrowSize;
    
    bezierArrow.position.set(fromXY[0], fromXY[1], 0);
    
    bezierArrow
        .lineStyle(4, whiteColor, 1)
        .bezierCurveTo(cpXY1[0],cpXY1[1],cpXY2[0],cpXY2[1],toXY[0],toXY[1])
        .lineStyle(1, whiteColor, 1)
        .beginFill(redColor, 1)
        .moveTo(toXY[0] + normal[0] + tangent[0], toXY[1] + normal[1] + tangent[1])
        .lineTo(toXY[0] , toXY[1] )
        .lineTo(toXY[0] - normal[0] + tangent[0], toXY[1] - normal[1] + tangent[1])
        .lineTo(toXY[0] + normal[0] + tangent[0]-1, toXY[1] + normal[1] + tangent[1])
        .endFill();
    
    let sprite = new PIXI.Sprite(app.renderer.generateTexture(bezierArrow,{resolution:PIXI.settings.FILTER_RESOLUTION}))
    bezierArrow.filters = [
        new GlowFilter({ innerStrength: 0, outerStrength: 2, color: yellowColor}),
        dropshadowFilter()
    ];

    return bezierArrow;
}

export function cardDescription (cardInfo) {
    if (cardInfo && cardInfo.effects && cardInfo.effects.length) {
        return descriptionForEffects(cardInfo.effects);
    }
}

function descriptionForEffects (effects) {
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

export function theme () {
    return createTheme({
        palette: {
            primary: {
                light: '#0000FF',
                main: '#0000FF',
                dark: '#0000FF',
                contrastText: '#fff',
            },            
        },
        components: {
            MuiSlider: {
              styleOverrides: {
                 markLabel: {
                    transform: 'translateX(-12%)',
                },
              },
            },
            MuiButton: { 
                styleOverrides: { 
                    root: { minWidth: 150, minHeight: 60 } 
                } 
            }
        },
    });
}




