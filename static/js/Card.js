import * as PIXI from 'pixi.js'
import * as Constants from './constants.js';


export class Card {

	static cardHeight = 114;
	static cardWidth = 80;
    static cardTexture = PIXI.Texture.from("/static/images/card.png");
    static cardLargeTexture = PIXI.Texture.from("/static/images/card-large.png");
    static cardTextureInPlay = PIXI.Texture.from("/static/images/in play mob.png");
    static cardTextureInPlayGuard = PIXI.Texture.from("/static/images/in play guard mob.png");

	static sprite(card, pixiUX, game, player, dont_attach_listeners=false, useLargeSize=false, overrideClickable=false) {
        let cw = Card.cardWidth;
        let ch = Card.cardHeight;
        let imageBackgroundSize = 128
        let spellWidth = Card.cardWidth - 6;
        let spellHeight = 54;
        let portraitHeight = 44;
        let portraitWidth = 24;
        let loaderId = card.name;
        let aFX = -8;
        let aFY = -9;
        let cardTexture = Card.cardTexture
        if (useLargeSize) {
            aFX = -Card.cardWidth / 4 + 16;
            aFY = -Card.cardHeight / 4;
            cw *= 2;
            ch *= 2; 
            imageBackgroundSize *= 2;           
            spellWidth = Card.cardWidth * 2 - 6;
            spellHeight *= 2;
            portraitHeight *= 2.2;
            portraitWidth *= 2;
            loaderId = card.name + Constants.largeSpriteQueryString 
            cardTexture = Card.cardLargeTexture
        }

        let cardSprite = Card.baseSprite(card, cardTexture, game);
        cardSprite.card = card;
        cardSprite.buttonMode = true;  // hand cursor
        let imageSprite = Card.framedSprite(loaderId, imageBackgroundSize, pixiUX.app);
        if (card.card_type == Constants.mobCardType || card.card_type == Constants.artifactCardType) {
            imageSprite.position.y = -imageSprite.height / 4;
            Card.ellipsifyImageSprite(imageSprite, card, portraitWidth, portraitHeight)        
        } else if (card.card_type == Constants.spellCardType) {
            imageSprite.position.y = -spellHeight / 2;
            Card.rectanglifyImageSprite(imageSprite, spellWidth, spellHeight)                                    
        }
        cardSprite.addChild(imageSprite);

        const nameBackground = new PIXI.Sprite.from(PIXI.Texture.WHITE);
        nameBackground.tint = Constants.blackColor;
        nameBackground.width = cw - 6;
        nameBackground.height = Constants.defaultFontSize;
        nameBackground.alpha = .7;
        nameBackground.position.x = aFX + 8;
        nameBackground.position.y = aFY + 2;
        let nameOptions = Constants.textOptions();
        if (card.name.length >= 22) {
            nameOptions.fontSize --;
        }
        if (useLargeSize) {
            nameOptions.fontSize = Constants.defaultFontSize;
            nameOptions.wordWrapWidth = 142;
            nameBackground.position.x -= 4
            nameBackground.position.y += 19
            nameBackground.height = 16;
        }
        cardSprite.addChild(nameBackground);

        if ("effects" in card) {
	        for (let e of card.effects) {
	            // hax, don't reference card name
	            if (e.name == "evolve" && card.name != "Warty Evolver") {
	                let evolveLabelOptions = Constants.textOptions();
	                evolveLabelOptions.fill = Constants.whiteColor;
	                evolveLabelOptions.fontSize = 6;
	                const evolveLabel = new PIXI.Sprite.from(PIXI.Texture.WHITE);
	                evolveLabel.tint = Constants.blueColor;
	                evolveLabel.height = 6;
	                evolveLabel.alpha = .7;
	                evolveLabel.position.x = aFX + 8;
	                evolveLabel.position.y = aFY + 2 - evolveLabel.height - Constants.padding;
	                if (useLargeSize) {
	                    evolveLabelOptions.fontSize = Constants.defaultFontSize;
	                    evolveLabel.position.x -= 4
	                    evolveLabel.height = 12;
	                    evolveLabel.position.y += evolveLabel.height
	                }
	                cardSprite.addChild(evolveLabel);
	                let evolveText = new PIXI.Text("Evolved", evolveLabelOptions);
	                evolveLabel.width = evolveText.width + Constants.padding;
	                cardSprite.addChild(evolveText);
	                evolveText.position.x = evolveLabel.position.x;
	                evolveText.position.y = evolveLabel.position.y;
	            }
	        }
		}

        nameOptions.fill = Constants.whiteColor;
        let name = new PIXI.Text(card.name, nameOptions);
        cardSprite.addChild(name);
        name.position.x = nameBackground.position.x;
        name.position.y = nameBackground.position.y;

        const descriptionBackground = new PIXI.Sprite.from(PIXI.Texture.WHITE);
        descriptionBackground.tint = Constants.whiteColor;
        descriptionBackground.alpha = .8;
        descriptionBackground.width = cw - 6;
        descriptionBackground.height = ch / 2 - 10;
        descriptionBackground.position.y = descriptionBackground.height/2;
        cardSprite.addChild(descriptionBackground);

        let activatedEffects = [];
        let attackEffect = null;
        if ("effects" in card) {
	        for (let e of card.effects) {
	            if (e.effect_type == "activated" && e.enabled) {
	                activatedEffects.push(e)
	                if (e.name == "attack" || e.name == "make_random_townie") {
	                    attackEffect = e;
	                }
	            }
	        }
	    }

        if (card.card_type != "Effect") {
            let costX = aFX - 23;
            let costY = aFX - 38;
            if (useLargeSize) {
                costX -= cw/4;
                costY -= ch/4;
            }

            imageSprite = new PIXI.Sprite.from(PIXI.Texture.from(Constants.cardImagesPath + "amethyst.svg"));
            imageSprite.tint = Constants.blueColor;
            imageSprite.height = 15;
            imageSprite.width = 15;
            if (useLargeSize) {
                imageSprite.height = 25;
                imageSprite.width = 25;
            }
            imageSprite.position.x = costX;
            imageSprite.position.y = costY;
            cardSprite.addChild(imageSprite);

            let ptOptions = Constants.textOptions()
            ptOptions.stroke = Constants.blackColor;
            ptOptions.strokeThickness = 2;
            ptOptions.fill = Constants.whiteColor;
            ptOptions.fontSize = Constants.defaultFontSize;
            if (useLargeSize) {
                ptOptions.fontSize = 17;
            }
            let cost = new PIXI.Text(card.cost, ptOptions);
            cost.position.x = costX;
            cost.position.y = costY;
            cardSprite.addChild(cost);

        }            

        let abilitiesText = "";
        let color = Constants.darkGrayColor;
        if ("abilities" in card) {
	        for (let a of card.abilities) {
	            if (!["Starts in Play", "die_to_top_deck", "discard_random_to_deck", "multi_mob_attack", "Weapon"].includes(a.descriptive_id)) {
	                if (a.description) {
	                    abilitiesText += a.description;
	                    color = Constants.blackColor;
	                } else {
	                    if (a.name == "DamageDraw") {
	                        continue;
	                    }
	                    abilitiesText += a.name;
	                    if (a != card.abilities[card.abilities.length-1]) {                
	                           abilitiesText += ", ";
	                    }               
	                }
	            }
	        }

	        if ("tokens" in card) {
		        for (let c of card.tokens) {
		           if (c.set_can_act == false) {
		            if (abilitiesText.length) {
		                abilitiesText += ", ";
		            }
		            abilitiesText += "Can't Attack";
		           }
		        }        	
		    }
        }

        let baseDescription =  card.description ? card.description : "";
        if (card.name == "Tame Shop Demon") {
           baseDescription = card.effects[0].card_descriptions[card.level];
        }
        if (card.name == "Doomer") {
           let damage = card.effects[0].amount;
           baseDescription = `All enemies take ${damage} damage end of your turn. Increase this each turn.`;
        }
        if (card.name == "Rolling Thunder") {
           let damage = card.effects[0].amount;
           baseDescription = `Deal ${damage} damage. Improves when cast.`;
        }
        if (card.card_for_effect && card.name == "Upgrade Chamber") {
           baseDescription = `Get ${card.card_for_effect.name} back next turn, upgraded.`;
        }
        if (card.card_for_effect && card.name == "Duplication Chamber") {
           baseDescription = `Get two copies of ${card.card_for_effect.name} back next turn.`;
        }


        if (card.added_descriptions && card.added_descriptions.length) {
            for (let d of card.added_descriptions) {
                baseDescription += " " + d
            }
        }
        let descriptionOptions = Constants.textOptions();
        if ((abilitiesText + ". " + baseDescription).length > 95) {
            descriptionOptions.fontSize = 6; 
        }
        if (useLargeSize) {
            descriptionOptions.wordWrapWidth = 142;
            descriptionOptions.fontSize = Constants.defaultFontSize;
        }


        let description = new PIXI.Text(abilitiesText + ". " + baseDescription, descriptionOptions);
        if (abilitiesText.length == 0) {
            description = new PIXI.Text(baseDescription, descriptionOptions);
        }
        if (abilitiesText.length != 0 && !baseDescription) {
            description = new PIXI.Text(abilitiesText + ". ", descriptionOptions);
        }

        if (baseDescription || abilitiesText.length) {
            // todo don't hardcode hide description for Infernus
            // todo don't hardcode hide description for Winding One
            if ((card.card_type == Constants.mobCardType && activatedEffects.length == 0) ||
                card.card_type != Constants.mobCardType || card.turn_played == -1) {
                cardSprite.addChild(description);
            }
        }
        description.position.x = name.position.x;
        description.position.y = name.position.y + 28;
        if (useLargeSize) {
            description.position.y += 20 + 2;
        }

        if (useLargeSize) {
            Card.showAbilityPanels(cardSprite, card, cw, ch);
            if (card.card_for_effect) {
                let subcard = Card.sprite(card.card_for_effect, pixiUX, game, player, true, true);
                Card.setCardAnchors(subcard);
                subcard.height *=.75;
                subcard.width *=.75;
                subcard.position.x = Card.cardWidth*1.75;
                cardSprite.addChild(subcard)            
            }
        }
        if (card.card_type == Constants.mobCardType) {
            Card.addStats(card, cardSprite, player, aFX, aFY, cw, ch, useLargeSize)

        } else if (card.turn_played == -1 || !("turn_played" in card)) {
            let typeX = aFX + cw/4 - 33;
            let typeY = aFY + ch/2 - 5;
            if (useLargeSize) {
                typeX -= 20;
                typeY += 20;
            }
            let typeBG = new PIXI.Graphics();
            typeBG.beginFill(Constants.blackColor);
            typeBG.drawRoundedRect(
                0,
                0,
                42,
                Constants.defaultFontSize,
                30
            );
            typeBG.position.x = typeX;
            typeBG.position.y = typeY;
            typeBG.endFill();
            typeBG.alpha = .5;
            cardSprite.addChild(typeBG);

            let typeOptions = Constants.textOptions();
            typeOptions.fill = Constants.whiteColor;

            let typeName = card.card_type;
            if ("abilities" in card) {
	            for (let a of card.abilities) {
	                if ("Weapon" == a.descriptive_id) {
	                    typeName = a.descriptive_id;
	                }
	            }
            }

            let type = new PIXI.Text(typeName.charAt(0).toUpperCase() + typeName.slice(1), typeOptions);
            type.position.x = typeX + 20;
            type.position.y = typeY + 6
            cardSprite.addChild(type);
        }

        if (attackEffect) {
            let powerX = aFX - 24;
            let powerY = aFY + ch/2;
            if (useLargeSize) {
                powerX -= 44;
                powerY += 20;
            }
            let countersX = powerX + cw - 16;
            let attackEffectOptions = Constants.textOptions() 
            if (attackEffect.name == "make_random_townie") {
                Card.addCircledLabel(countersX, powerY, cardSprite, attackEffectOptions, attackEffect.counters);
            } else {
                Card.addCircledLabel(powerX, powerY, cardSprite, attackEffectOptions, attackEffect.power);
                Card.addCircledLabel(countersX, powerY, cardSprite, attackEffectOptions, attackEffect.counters);
            }
        }

        let currentPlayer = null;
        if (pixiUX.thisPlayer) {
			currentPlayer = pixiUX.thisPlayer(game);        	
        }
 
        Card.setCardFilters(card, cardSprite, currentPlayer, overrideClickable, useLargeSize);

        if (dont_attach_listeners) {
            return cardSprite;
        }

        if (pixiUX.setCardDragListeners) {
	        pixiUX.setCardDragListeners(card, cardSprite, game);
        }
        if (!useLargeSize) {
            Card.setCardMouseoverListeners(cardSprite, game, pixiUX);
        }        	

        Card.setCardAnchors(cardSprite);

        return cardSprite;
    }

    static spriteInPlay(card, pixiUX, game, player, dont_attach_listeners) {
        let cardTexture = Card.cardTextureInPlay;
        for (let a of card.abilities) {
            if (a.name == "Guard") {
                cardTexture = Card.cardTextureInPlayGuard;
            }                    
        }

        let cardSprite = Card.baseSprite(card, cardTexture, game);
        let imageSprite = Card.framedSprite(card.name+Constants.largeSpriteQueryString, 256, pixiUX.app);
        cardSprite.addChild(imageSprite);
        Card.ellipsifyImageSprite(imageSprite, card, 38, 82)

        if (card.name == "Mana Battery") {
            let currentBatteryMana = 0;
            for (let effect of card.effects) {
                if (effect.name == "store_mana") {
                    currentBatteryMana = effect.counters;
                }
            }
            let gems = Constants.manaGems(3, currentBatteryMana);
            gems.position.x = -gems.width/2;
            gems.position.y = Card.cardHeight/2 - 7 - gems.height;
            cardSprite.addChild(gems);
        }

        let effect = null;
        if (card.effects.length > 0 && card.effects[0].enabled && card.effects[0].effect_type == "activated") {
            effect = card.effects[0];
        } else if (card.effects.length > 1 && card.effects[1].enabled && card.effects[1].effect_type == "activated") { 
            effect = card.effects[1];
        }

        if (effect) {
            let gems = Constants.manaGems(effect.cost, effect.cost);
            if (effect.cost == 0) {
                gems = Constants.manaGems(1, 1, "power-button.svg", Constants.blackColor);
                if (card.name == "Lute") {
                    gems = Constants.manaGems(1, 1, "musical-notes.svg", Constants.blackColor);                    
                }
            }
            let color = Constants.greenColor;
            if (!card.can_be_clicked) {
                color = Constants.darkGrayColor;
            }
            let b = Card.button(
                "", 
                color, 
                null, 
                0, 
                -Constants.padding,
                () => {}, 
                null,
                gems.width*2, true
            );
            b.addChild(gems);
            gems.position.x = gems.width/2;
            gems.position.y = gems.height*.75;
            cardSprite.addChild(b);
        }
        
        let options = Constants.textOptions();
        
        let aFX = -Card.cardWidth / 2;
        let aFY = -Card.cardHeight / 2;

        let activatedEffects = [];
        let attackEffect = null;
        for (let e of card.effects) {
            if (e.effect_type == "activated" && e.enabled) {
                activatedEffects.push(e)
                if (e.name == "attack" || e.name == "make_random_townie") {
                    attackEffect = e;
                }
            }
        }

        if (card.card_type == Constants.mobCardType) {
            Card.addStats(card, cardSprite, player, -8, -14, Card.cardWidth-16, Card.cardHeight, false)
        } else if (card.turn_played == -1 && !attackEffect) {
            let type = new PIXI.Text(card.card_type, options);
            type.position.x = aFX + Card.cardWidth - 28;
            type.position.y = aFY + Card.cardHeight - 18;
            cardSprite.addChild(type);
        }

        if (attackEffect) {
            let powerCharges = new PIXI.Text(attackEffect.power + "/" + attackEffect.counters, options);
            if (attackEffect.name == "make_random_townie") {
                let attackEffectOptions = Constants.textOptions() 
                Card.addCircledLabel(aFX + Card.cardWidth - 14, aFY + Card.cardHeight - 18, cardSprite, attackEffectOptions, attackEffect.counters);
            } else {
                powerCharges.position.x = aFX + Card.cardWidth - 14;
                powerCharges.position.y = aFY + Card.cardHeight - 18;
                cardSprite.addChild(powerCharges);                
            }
        }

        if (card.card_for_effect) {
            let subcard = Card.sprite(card.card_for_effect, pixiUX, game, player, true);
            Card.setCardAnchors(subcard);
            subcard.height = Card.cardHeight/2
            subcard.width = Card.cardWidth/2
            subcard.position.y += 20
            cardSprite.addChild(subcard)            
        }

        Card.setCardFilters(card, cardSprite, pixiUX.thisPlayer(game));

        if (dont_attach_listeners) {
            return cardSprite;
        }

        pixiUX.setCardDragListeners(card, cardSprite, game);
        Card.setCardMouseoverListeners(cardSprite, game, pixiUX);

        Card.setCardAnchors(cardSprite);

         if (cardSprite.card.damage_to_show > 0) {
           pixiUX.damageSprite(imageSprite, cardSprite.card.id + '_pic', cardSprite.card.damage_to_show);
           pixiUX.damageSprite(cardSprite, cardSprite.card.id, cardSprite.card.damage_to_show);
        }

        return cardSprite;
    }

    static spriteTopSliver(card, pixiUX, count) {
        let cardSprite = Card.baseSprite(card, PIXI.Texture.from("/static/images/card-sliver.png"));
        cardSprite.card = card;
        cardSprite.buttonMode = true;

        const nameBackground = new PIXI.Sprite.from(PIXI.Texture.WHITE);
        nameBackground.tint = Constants.blackColor;
        nameBackground.width = Card.cardWidth * 1.25 - Constants.padding * 4;
        nameBackground.height = Constants.defaultFontSize;
        nameBackground.alpha = .7;
        nameBackground.position.x = Constants.padding/2;
        nameBackground.position.y = Constants.padding/2;
        let nameOptions = Constants.textOptions();
        cardSprite.addChild(nameBackground);

        nameOptions.fill = Constants.whiteColor;
        let name = new PIXI.Text(card.name, nameOptions);
        name.anchor.set(0);
        cardSprite.addChild(name);
        name.position.x = nameBackground.position.x + 1;
        name.position.y = nameBackground.position.y + 1;

        if (count > 1) {
            let options = Constants.textOptions();            
            let circle = Card.addCircledLabel(Card.cardWidth * 1.25 - options.fontSize, options.fontSize + 1, cardSprite, options, count, Constants.yellowColor);
            circle.anchor.set(.5)
        }

        let currentPlayer = null;
        if (pixiUX.thisPlayer) {
            currentPlayer = pixiUX.thisPlayer(game);            
        }
 
        pixiUX.setDeckCardDragListeners(cardSprite);

        Card.setCardFilters(card, cardSprite, currentPlayer, false, false);

        Card.setCardMouseoverListeners(cardSprite, null, pixiUX);


        return cardSprite;
    }

    static button(title, color, textColor, x, y, clickFunction, container=null, width=null, short=false, fontSize=null) {
        const buttonBG = new PIXI.Sprite.from(PIXI.Texture.WHITE);
        Constants.roundRectangle(buttonBG, 1)
        let options = {fontFamily : Constants.defaultFontFamily, fontSize: Constants.defaultFontSize, fill : textColor};
        if (fontSize != null) {
            options.fontSize = fontSize;
        }
        let textSprite = new PIXI.Text(title, options);
        textSprite.position.y = textSprite.height;
        buttonBG.width = textSprite.width + Constants.padding * 8;
        textSprite.position.x = buttonBG.width / 2 - textSprite.width / 2;
        if (width != null) {
            buttonBG.width = width;
            textSprite.position.x = width / 2 - textSprite.width / 2;
        }        
        buttonBG.height = textSprite.height * 3;
        if (short) {
            buttonBG.height = textSprite.height * 2;            
            textSprite.position.y = buttonBG.height / 2 - textSprite.height / 2 - 1;
            textSprite.height = options.fontSize * 2;
        }
        buttonBG.tint = color;
        buttonBG.buttonMode = true;
        buttonBG.interactive = true;
        buttonBG
            .on("click", clickFunction)
            .on("tap", clickFunction)
        const cage = new PIXI.Container();
        cage.position.x = x - buttonBG.width / 2;
        cage.position.y = y + buttonBG.height;
        cage.addChild(buttonBG);
        cage.addChild(textSprite);
        cage.name = "button";
        cage.text = textSprite;
        cage.buttonSprite = buttonBG;
        if (container) {
            container.addChild(cage);            
        }
        return cage;
    }

    static addStats(card, cardSprite, player, aFX, aFY, cw, ch, useLargeSize) {
    	let damage = 0;
    	if (card.damage) {
    		damage = card.damage;
    	}
        let cardPower = card.power;
        let cardToughness = card.toughness - damage;
        if (card.tokens) {
            // todo does this code need to be clientside?
            for (let c of card.tokens) {
                if (c.multiplier == "self_artifacts" && player.artifacts) {
                    cardPower += c.power_modifier * player.artifacts.length;                        
                } else if (c.multiplier == "self_mobs_and_artifacts") {
                    if (player.artifacts) {
                        cardPower += c.power_modifier * player.artifacts.length;                        
                    }
                    if (player.in_play) {
                        cardPower += c.power_modifier * (player.in_play.length - 1);                        
                    }
                } else {
                    cardPower += c.power_modifier;                        
                }
            }
            for (let c of card.tokens) {
                cardToughness += c.toughness_modifier;
            }
        }

        let ptOptions = Constants.textOptions()

        let centerOfEllipse = 16

        let powerX = aFX - cw/2 + centerOfEllipse;
        let powerY = aFY + ch/2;
        let defenseX = aFX + cw/2;

        if (useLargeSize) {
            powerY += 20;
            powerX -= 5;
            defenseX -= 5;
        }

        let imageSprite = new PIXI.Sprite.from(PIXI.Texture.from(Constants.cardImagesPath + "piercing-sword.svg"));
        imageSprite.tint = Constants.yellowColor;
        imageSprite.height = 17;
        imageSprite.width = 17;
        imageSprite.position.x = powerX;
        imageSprite.position.y = powerY;
        cardSprite.addChild(imageSprite);

        Card.addCircledLabel(powerX, powerY, cardSprite, ptOptions, cardPower, Constants.yellowColor);

        imageSprite = new PIXI.Sprite.from(PIXI.Texture.from(Constants.cardImagesPath + "hearts.svg"));
        imageSprite.tint = Constants.redColor;
        imageSprite.height = 17;
        imageSprite.width = 17;
        imageSprite.position.x = defenseX;
        imageSprite.position.y = powerY;
        cardSprite.addChild(imageSprite);

        ptOptions.stroke = Constants.blackColor;
        ptOptions.strokeThickness = 2;
        ptOptions.fill = Constants.whiteColor;
        ptOptions.fontSize = 9;
        let defense = new PIXI.Text(cardToughness, ptOptions);
        defense.position.x = defenseX;
        defense.position.y = powerY;
        cardSprite.addChild(defense);        

        if (card.id && window.location.hostname.startsWith("127.")) {
	        let cardId = new PIXI.Text("id: " + card.id, ptOptions);
	        cardId.position.x = defenseX - Card.cardWidth/4 - 5;
	        cardId.position.y = powerY;
	        cardSprite.addChild(cardId);                	
        }
    }

    static addCircledLabel(costX, costY, cardSprite, options, value, fillColor) {
        options.stroke = Constants.blackColor;
        options.strokeThickness = 2;
        options.fill = Constants.whiteColor;
        options.fontSize = 11;

        let circle = Card.circleBackground(costX, costY);
        circle.tint = fillColor
        cardSprite.addChild(circle);
        let cost = new PIXI.Text(value, options);
        cost.position.x = -4;
        cost.position.y = -8;
        circle.addChild(cost);
        return circle;
    }

    static circleBackground(x, y) {
        const circleRadius = 7;
        const background = new PIXI.Graphics();
        background.beginFill(Constants.blackColor, 1);
        background.lineStyle(2, Constants.blackColor, 1); 
        background.drawCircle(0, 0, circleRadius);
        background.endFill();

        const sprite = new PIXI.Sprite.from(PIXI.Texture.WHITE);
        sprite.position.x = x;
        sprite.position.y = y;
        sprite.mask = background;
        sprite.width = circleRadius * 2;
        sprite.height = circleRadius * 2;
        sprite.addChild(background);
        return sprite;
    }

    static baseSprite(card, cardTexture, game) { 
        let cardSprite = new PIXI.Sprite.from(cardTexture);
        cardSprite.card = card;
        // if (Card.isPlaying(game)) {
        //    cardSprite.buttonMode = true;  // hand cursor
        //}
        return cardSprite;
    }

    static framedSprite(loaderID, size, app) {
        let imageSprite = PIXI.Sprite.from(loaderID);
        let spriteWidth = imageSprite.width
        const bgSprite = new PIXI.Sprite.from(PIXI.Texture.WHITE);
        bgSprite.tint = Constants.blackColor;
        bgSprite.width = size;
        bgSprite.height = size;
        const imageContainer = new PIXI.Container();
        imageContainer.addChild(bgSprite);
        imageContainer.addChild(imageSprite);
        imageSprite.position.x = bgSprite.width / 2 - imageSprite.width / 2;
        imageSprite.position.y = bgSprite.height / 2 - imageSprite.height / 2;
        let texture = app.renderer.generateTexture(imageContainer)
        imageSprite = new PIXI.Sprite(texture);
        return imageSprite
    }

    static ellipsifyImageSprite(imageSprite, card, width, height) {
        let bg = Card.ellipseBackground(width, height, imageSprite.width);
        imageSprite.mask = bg;
        imageSprite.addChild(bg);        
        return imageSprite
    }

    static ellipseBackground(width, height, imageSpriteWidth) {
        const ellipseW = width;
        const ellipseH = height;
        const background = new PIXI.Graphics();
        background.beginFill(Constants.whiteColor, 1);
        background.drawEllipse(0, 0, ellipseW, ellipseH - height/3)
        background.endFill();
        const sprite = new PIXI.Sprite.from(PIXI.Texture.WHITE);
        sprite.mask = background;
        sprite.addChild(background);
        return background;
    }

    static rectanglifyImageSprite(imageSprite, width, height) {
        let bg = Card.rectangleBackground(width, height);
        imageSprite.mask = bg;
        imageSprite.addChild(bg);        
    }

    static rectangleBackground(width, height) {
        const rectangleW = width;
        const rectangleH = height;
        const background = new PIXI.Graphics();
        background.beginFill(Constants.whiteColor, 1);
        background.drawRect(-rectangleW/2, -rectangleH/2, rectangleW, rectangleH);
        background.endFill();
        const sprite = new PIXI.Sprite.from(PIXI.Texture.WHITE);
        sprite.mask = background;
        sprite.addChild(background);
        return background;
    }

    static showAbilityPanels(cardSprite, card, cw, ch) {
    	if (!card.abilities) {
    		return;
    	}
        let options = Constants.textOptions();
        options.fontSize = 10;
        options.wordWrapWidth = cw - 8;

        const topBG = new PIXI.Sprite.from(PIXI.Texture.WHITE);
        cardSprite.addChild(topBG);
        topBG.tint = Constants.yellowColor;
        const textContainer = new PIXI.Container();
        cardSprite.addChild(textContainer);
        let yPosition = 0;
        for (let a of card.abilities) {
            let abilityText = new PIXI.Text("", options);
            if (a.name == "Shield") {
                abilityText.text = "Shield - Shielded mobs don't take damage the first time they get damaged.";
            }                    
            if (a.name == "Guard") {
                abilityText.text = "Guard - Guard mobs must be attacked before anything else.";
            }                    
            if (a.name == "Syphon") {
                abilityText.text = "Syphon - Gain hit points when this deals damage.";
            }                    
            if (a.name == "Fast") {
                abilityText.text = "Fast - Fast mobs may attack the turn they come into play.";
            }                    
            if (a.name == "Conjure") {
                abilityText.text = "Conjure - Conjure mobs may be played as instants.";
            }                    
            if (a.name == "Instant Attack") {
                abilityText.text = "Instant Attack - Instant Attack mobs can attack as instants.";
            }                    
            if (a.name == "Ambush") {
                abilityText.text = "Ambush - Ambush mobs may attack other mobs the turn they come into play.";
            }                    
            if (a.name == "Instrument Required") {
                abilityText.text = "Instrument Required - You must have an Instrument in play to play Card.";
            }                    
            if (a.name == "Townie") {
                abilityText.text = "Townie - Townies have a little ability.";
            }                    
            if (a.name == "Unique") {
                abilityText.text = "Unique - only one Unique card is allowed per deck.";
            }                    
            if (a.name == "Weapon") {
                abilityText.text = "Weapon - Weapons can be used to attack players and mobs.";
            }                    
            if (a.name == "Instrument") {
                abilityText.text = "Instrument - Instruments have special abilities and are needed for other cards.";
            } 
            if (a.name == "Fade") {
                abilityText.text = "Fade - Fade mobs get -1/-1 at the beginning of the turn.";
            }                    
            if (a.name == "Stomp") {
                abilityText.text = "Stomp - Stomp mobs deal excess damage to players.";
            }                    
            if (a.name == "Lurker") {
                abilityText.text = "Lurker - Lurker mobs can't be targetted until they attack.";
            }                    
            if (a.name == "Keep") {
                abilityText.text = "Keep - Cards with Keep can be Kept by discplines (tech) that discard their hand each turn.";
            }                    
            if (a.name == "Disappear") {
                abilityText.text = "Disappear - Cards with Disappear don't go to the Played Pile when played, they are removed instead.";
            }                    
            if (a.name == "Defend") {
                abilityText.text = "Defend - Defend mobs that didn't attack last turn can intercept an attack as an instant. Defended attacks are cancelled if the attacker dies.";
            }                    
            if (abilityText.text) {
                abilityText.position.x -= cw/2 - 4;
                abilityText.position.y = yPosition - ch/2 + 2;
                yPosition += abilityText.height + 10;
                textContainer.addChild(abilityText);
            }
        }
    	if (card.effects) {
	        for (let e of card.effects) {
	            if (e.name == "evolve") {
	                let effectText = new PIXI.Text("", options);
	                effectText.text = "Evolve - Evolve Mobs turn into better ones when they die.";
	                effectText.position.x -= cw / 2 - 4;
	                effectText.position.y = yPosition - ch / 2 + 2;
	                yPosition += effectText.height + 10;
	                textContainer.addChild(effectText);
	            }                    
	        }
	    }

        if (yPosition == 0) {
            cardSprite.removeChild(topBG);
            cardSprite.removeChild(textContainer);
        }
        topBG.width = cw;
        topBG.height = ch;
        topBG.position.x = cw + 5;
        topBG.position.y = 0;
        textContainer.position.x = topBG.position.x;
        textContainer.position.y = topBG.position.y;

    }
 
    static setCardAnchors(cardSprite) {
        cardSprite.anchor.set(.5);
        for (let child of cardSprite.children) {
            // graphics don't have an anchor, such as the circle for costBackground
            if (child.anchor) {
                child.anchor.set(.5);                
            }
        }        
    }

    static setCardFilters(card, cardSprite, currentPlayer, overrideClickable, isStackCard) {
        let filters = []
        if (card.can_be_clicked || overrideClickable) {
            if (!currentPlayer.card_info_to_target.effect_type || currentPlayer.card_info_to_target.card_id != card.id) {
                if (currentPlayer.card_info_to_target.effect_type && ["mob_comes_into_play", "spell_cast", "artifact_activated"].includes(currentPlayer.card_info_to_target.effect_type)) {
                    filters.push(Constants.targettableGlowFilter());                                    
                } else {
                    filters.push(Constants.canBeClickedFilter());                                    
                }
            }
        } else {
            if (!isStackCard && currentPlayer) {
                filters.push(Constants.cantBeClickedFilter());                                        
            }
        }
        if (card.shielded && card.turn_played > -1) {
            filters.push(Constants.shieldFilter());                        
        }
        if (card.abilities && card.abilities.length > 0 && card.abilities[0].descriptive_id == "Lurker" && card.abilities[0].enabled && card.turn_played > -1) {
            filters.push(Constants.lurkerFilter());                        
        }

        cardSprite.filters = filters;
    }

    static setCardMouseoverListeners(cardSprite, game, pixiUX) {
        cardSprite.onMouseover = () => {Card.onMouseover(cardSprite, game, pixiUX)};
        cardSprite.onMouseout = () => {Card.onMouseout(cardSprite, pixiUX)};
        cardSprite
            .on('mouseover',        cardSprite.onMouseover)
            .on('mouseout',        cardSprite.onMouseout)
    }

    static onMouseover(cardSprite, game, pixiUX) {
        pixiUX.hovering = true;
        pixiUX.hoverTimeout = setTimeout(() => { 
            if (pixiUX.hovering) {
                pixiUX.app.stage.removeChild(pixiUX.hoverCards);
                pixiUX.hovering = false;
                const card = cardSprite.card
                const loaderID = card.name+Constants.largeSpriteQueryString
                const loaderURL = pixiUX.rasterizer.fullImagePath(card) + Constants.largeSpriteQueryString;
                if (!PIXI.utils.TextureCache[loaderURL]) {
                    pixiUX.app.loader.reset()
                    pixiUX.rasterizer.loadCardImage(
                        card.card_type,
                        loaderID,
                        loaderURL,
                        .9,
                    );
                    pixiUX.app.loader.load(() => {
                        Card.addHoverCard(cardSprite, game, pixiUX);
                    });                     
            	} else {
                    Card.addHoverCard(cardSprite, game, pixiUX);
            	}
            }
        }, 300);

    }

    static addHoverCard(cardSprite, game, pixiUX) {
        console.log(pixiUX.constructor.name)
    	let player = null;
    	if (pixiUX.thisPlayer) {
    		player = pixiUX.thisPlayer(game);
    	}
        let sprite = Card.sprite(cardSprite.card, pixiUX, game, player, false, true);
        sprite.position.x = cardSprite.position.x + Card.cardWidth/2;
        sprite.position.y = cardSprite.position.y - Card.cardHeight*1.5;
        if (sprite.position.y < Card.cardHeight) {
            sprite.position.y = Card.cardHeight;
            sprite.position.x = cardSprite.position.x + Card.cardWidth*1.5 + 10;
        }
        // hax - because cards are in an unusual container?
        if (player && player.card_choice_info.cards.length) {
            sprite.position.x += Card.cardWidth * 2.5 + Constants.padding * 2;
        }
        if (sprite.position.x >= 677) {
            sprite.position.x = cardSprite.position.x - Card.cardWidth;
        }

        if (pixiUX.constructor.name == "DeckViewer" || pixiUX.constructor.name == "OpponentChooser") {
            sprite.position.x = cardSprite.position.x + (Card.cardWidth+Constants.padding*2)*2;
            sprite.position.y = cardSprite.position.y + Card.cardHeight;
        }
        if (pixiUX.constructor.name == "DeckBuilder") {
            sprite.position.x = cardSprite.position.x - (Card.cardWidth);
            sprite.position.y = cardSprite.position.y + Card.cardHeight;
        }
        if (pixiUX.constructor.name == "DeckBuilder" && cardSprite.height == 114) {
            sprite.position.x = cardSprite.position.x + (Card.cardWidth* 1.5);
            sprite.position.y = cardSprite.position.y + Card.cardHeight/2;
        }

        pixiUX.app.stage.addChild(sprite)
        pixiUX.hoverCards = sprite;        
        pixiUX.hovering = true;        
    }

    static onMouseout(cardSprite, pixiUX) {
        clearTimeout(pixiUX.hoverTimeout);
        pixiUX.hovering = false
        pixiUX.app.stage.removeChild(pixiUX.hoverCards);
    }    

    static hasAbility(card, abilityName) {
        if (!card.abilities) {
            return false;
        }
        for (let ability of card.abilities) {
            if (ability.name == abilityName) {
                return true;
            }
        }
        return false;
    }

    static cardsForDeck(deck, allCards) {
        let cards = [];
        for (let nameKey in deck) {
            for(let card of allCards) {
                if (card.name == nameKey) {
                    cards.push(card);
                }
            }   
        }   
        return cards;
    }

    static cardsForCardList(cardList, allCards) {
        let cards = [];
        for (let nameKey of cardList) {
            for(let card of allCards) {
                if (card.name == nameKey) {
                    cards.push(card);
                }
            }   
        }   
        return cards;
    }
}