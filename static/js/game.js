import * as PIXI from 'pixi.js'
import { Bump } from './lib/bump.js';
import { AdjustmentFilter, DropShadowFilter, ShockwaveFilter, GlowFilter, GodrayFilter, OutlineFilter } from 'pixi-filters';
import { Scrollbox } from 'pixi-scrollbox'

const appWidth = 840;
const appHeight = 803;
const cardHeight = 114;
const cardWidth = 80;
const padding = 10;
const avatarHeight = 128;
const avatarWidth = 300;
const brownColor = 0x765C48;
const lightBrownColor = 0xDFBF9F;
const cardContainerWidth = cardWidth * 7 + 12;

export class GameUX {

    constructor() {
        this.aiType = document.getElementById("data_store").getAttribute("ai_type");
        this.allCards = JSON.parse(document.getElementById("card_store").getAttribute("all_cards"));
        this.gameType = document.getElementById("data_store").getAttribute("game_type");
        this.username = document.getElementById("data_store").getAttribute("username");
        this.oldOpponentArmor = 0;
        this.oldOpponentHP = 30;
        this.oldSelfArmor = 0;        
        this.oldSelfHP = 30;        

        this.bump = new Bump(PIXI);
        this.cardTexture = PIXI.Texture.from('/static/images/card.png');
        this.cardLargeTexture = PIXI.Texture.from('/static/images/card-large.png');
        this.cardTextureInPlay = PIXI.Texture.from('/static/images/in play mob.png');
        this.cardTextureInPlayArtifact = PIXI.Texture.from('/static/images/in play mana artifact.png');
        this.inPlayTexture = PIXI.Texture.from('/static/images/in_play.png');
        this.handTexture = PIXI.Texture.from('/static/images/hand.png');
        this.artifactsTexture = PIXI.Texture.from('/static/images/relics.png');
        this.avatarTexture = PIXI.Texture.from('/static/images/avatar.png');
        this.menuTexture = PIXI.Texture.from('/static/images/menu.png');
        this.newGameButtonTexture = PIXI.Texture.from('/static/images/menu-button.png');
        this.bearTexture = PIXI.Texture.from('/static/images/bear.png');
        this.tigerTexture = PIXI.Texture.from('/static/images/tiger.png');

        PIXI.settings.FILTER_RESOLUTION = window.devicePixelRatio || 1;
        PIXI.GRAPHICS_CURVES.adaptive = true
        this.app = new PIXI.Application({
            width: appWidth, 
            height: appHeight, 
            antialias: true, 
            backgroundAlpha: true,
            resolution: window.devicePixelRatio || 1,
            autoDensity: true
        });
        document.getElementById("new_game").appendChild(this.app.view);
        this.renderStaticElements();
    }
 
    renderStaticElements() {
        this.app.stage.addChild(this.background());

        this.opponentAvatar = this.avatar(cardContainerWidth/2 - avatarWidth/2, padding);
        this.app.stage.addChild(this.opponentAvatar);

        this.artifactsOpponent = this.artifacts(cardContainerWidth/2 + avatarWidth/2 + padding, padding+6);
        this.app.stage.addChild(this.artifactsOpponent);

        let topOfMiddle = this.opponentAvatar.position.y + avatarHeight + padding
        this.inPlayOpponent = this.inPlayContainer(padding, topOfMiddle);
        this.app.stage.addChild(this.inPlayOpponent);

        let middleOfMiddle = this.inPlayOpponent.position.y + cardHeight + padding
        this.inPlay = this.inPlayContainer(padding, middleOfMiddle);
        this.app.stage.addChild(this.inPlay);

        this.buttonMenu = this.menu(cardContainerWidth + padding * 2, topOfMiddle);
        this.app.stage.addChild(this.buttonMenu);
        this.buttonMenu.addChild(this.newGameButton(22, 230 - 40 - padding - 8, this));

        let playerOneY = middleOfMiddle + cardHeight + padding;
        this.playerAvatar = this.avatar(cardContainerWidth/2 - avatarWidth/2, playerOneY);
        this.app.stage.addChild(this.playerAvatar);
        
        this.artifacts = this.artifacts(cardContainerWidth/2 + avatarWidth/2 + padding, playerOneY+6);
        this.app.stage.addChild(this.artifacts);

        this.handContainer = this.hand(padding, playerOneY + avatarHeight + padding);
        this.app.stage.addChild(this.handContainer);

        // create the scrollbox
        const scrollbox = new Scrollbox({ boxWidth: appWidth-4, boxHeight: cardHeight *1.25, clampWheel: false, passiveWheel: false})

        scrollbox.position.x = 2;
        scrollbox.position.y = this.handContainer.position.y + cardHeight + padding;

        const background = new PIXI.Sprite.from(PIXI.Texture.WHITE);
        background.tint = 0xffffff
        background.width = appWidth-4;
        background.height = cardHeight *1.25;
        this.scrollboxBackground = background;
        scrollbox.content.addChild(background);
        this.gameLogScrollbox = scrollbox;
        this.app.stage.addChild(scrollbox)
        scrollbox.content.filters = [
          new OutlineFilter(1, 0x000000),
        ]

    }

    background() {
        const background = new PIXI.Sprite.from(PIXI.Texture.WHITE);
        background.width = appWidth;
        background.height = appHeight;
        background.tint = 0xEEEEEE;
        return background;
    }

    newGameButton(x, y, gameUX) {
        const b = new PIXI.Sprite.from(this.newGameButtonTexture);
        b.buttonMode = true;
        b.position.x = x;
        b.position.y = y;
        // b.anchor.set(0.5);
        b.interactive = true;
        var clickFunction = function() {
            gameUX.gameRoom.nextRoom()
        };
        b
            .on('click', clickFunction)
            .on('tap', clickFunction)

        let text = new PIXI.Text("New Game", {fontFamily : 'Helvetica', fontSize: 12, fill : 0x00000});
        text.position.x = 23;
        text.position.y = 13;
        b.addChild(text);

        return b;
    }

    avatar(x, y) {
        const avatar = new PIXI.Sprite.from(this.avatarTexture);
        avatar.position.x = x;
        avatar.position.y = y;
        return avatar;
    }

    artifacts(x, y) {
        const artifacts = new PIXI.Sprite.from(this.artifactsTexture);
        artifacts.position.x = x;
        artifacts.position.y = y;
        return artifacts;
    }

    inPlayContainer(x, y) {
        const inPlayContainer = new PIXI.Sprite.from(this.inPlayTexture);
        inPlayContainer.position.x = x;
        inPlayContainer.position.y = y;
        return inPlayContainer;
    }

    hand(x, y) {
        const handContainer = new PIXI.Sprite.from(this.handTexture);
        handContainer.position.x = x;
        handContainer.position.y = y;
        return handContainer;
    }

    menu(x, y) {
        const menu = new PIXI.Sprite.from(this.menuTexture);
        menu.position.x = x;
        menu.position.y = y;
        return menu;
    }

    refresh(game, message) {
        if (this.selectCardContainer) {
            this.selectCardContainer.parent.removeChild(this.selectCardContainer);
            this.selectCardContainer = null;
        }

        this.removeCardsFromStage(game)

        if (this.thisPlayer(game)) {
            this.updateHand(game);
            if (message["show_spell"] && !this.thisPlayer(game).card_info_to_resolve["card_id"]) {
              // using this.thisPlayer(game) will break with a counterspell effect 
              // but we dont shjow counterspells being cast yet
                this.showCardThatWasCast(message["show_spell"], game, this.thisPlayer(game))
            }
            this.updatePlayer(game, this.thisPlayer(game), this.playerAvatar);
            this.updateThisPlayerArtifacts(game);
            this.updateThisPlayerInPlay(game);
        }

        if (this.opponent(game)) {
            this.updatePlayer(game, this.opponent(game), this.opponentAvatar);
            this.updateOpponentArtifacts(game);
            this.updateOpponentInPlay(game);
        }

        this.renderEndTurnButton(game);

        if (this.thisPlayer(game).card_info_to_resolve["card_id"]) {
            var targettableSprites = [];
            for (let sprite of this.app.stage.children) {
                if (sprite.card && sprite.card.can_be_clicked) {
                    targettableSprites.push(sprite)
                }
            }
            if (this.thisPlayer(game).can_be_clicked) {
                targettableSprites.push(this.playerAvatar);
            }
            if (this.opponent(game).can_be_clicked) {
                targettableSprites.push(this.opponentAvatar);
            }
            for (let sprite of targettableSprites) {
                sprite.filters = [targettableGlowFilter()]
            }
        }

        this.game = game;

        if (this.opponent(game) && this.thisPlayer(game)) {
            if (this.opponent(game).hit_points <= 0 || this.thisPlayer(game).hit_points <= 0) {
                alert("GAME OVER");
            }
        }

        if (this.thisPlayer(game).card_choice_info.cards.length && this.thisPlayer(game).card_choice_info.choice_type == "make") {
            this.showMakeView(game);
        } else if (this.thisPlayer(game).card_choice_info.cards.length && this.thisPlayer(game).card_choice_info.choice_type == "riffle") {
            this.showRiffleView(game, "FINISH_RIFFLE");
        } else if (this.thisPlayer(game).card_choice_info.cards.length && this.thisPlayer(game).card_choice_info.choice_type == "fetch_artifact_into_hand") {
            this.showChooseCardView(game, "FETCH_CARD");
        } else if (this.thisPlayer(game).card_choice_info.cards.length && this.thisPlayer(game).card_choice_info.choice_type == "fetch_into_hand") {
            this.showChooseCardView(game, "FETCH_CARD");
       } else if (this.thisPlayer(game).card_choice_info.cards.length && this.thisPlayer(game).card_choice_info.choice_type == "fetch_artifact_into_play") {
            this.showChooseCardView(game, "FETCH_CARD_INTO_PLAY");
        } else if (this.thisPlayer(game).card_choice_info.cards.length && this.thisPlayer(game).card_choice_info.choice_type == "view_hand") {
            this.showRevealView(game);
        } else {
            // not a choose cards view
        }                           
        if (game.show_rope) {
            this.showRope();
        }
        // this.app.renderer.render(this.app.stage)
    }

    showMakeView(game) {
        var self = this;
        this.showSelectCardView(game, "Make a Card", function(card) {
                if (card.global_effect) {
                    self.gameRoom.sendPlayMoveEvent("MAKE_EFFECT", {"card":card});
                } else {
                    self.gameRoom.sendPlayMoveEvent("MAKE_CARD", {"card":card});
                }
            });
    }

   showRevealView(game) {
        this.showSelectCardView(game, "Opponent's Hand", null);
        var self = this;

        document.getElementById("make_selector").onclick = function() {
            self.gameRoom.sendPlayMoveEvent("HIDE_REVEALED_CARDS", {});
            self.showGame();
            this.onclick = null
        }

        this.selectCardContainer
                .on('click',        function (e) {
                    self.gameRoom.sendPlayMoveEvent("HIDE_REVEALED_CARDS", {});
                })        
    }

    showChooseCardView(game, event_name) {
        var self = this;
        this.showSelectCardView(game, "Your Deck", function (card) {
                self.gameRoom.sendPlayMoveEvent(event_name, {"card":card.id});                
            }, true);
        
    }

    showRiffleView(game, event_name) {
        var self = this;
        this.showSelectCardView(game, "Top 3 Cards", function (card) {
                self.gameRoom.sendPlayMoveEvent(event_name, {"card":card.id});                
            });
        
    }

    showSelectCardView(game, title, card_on_click, showFullDeck) {
        const container = new PIXI.Container();
        this.selectCardContainer = container;
        this.app.stage.addChild(container);

        const background = new PIXI.Sprite.from(PIXI.Texture.WHITE);
        background.width = appWidth;
        background.height = appHeight;
        background.tint = 0x000000;
        background.alpha = .7;
        container.addChild(background);


        let options = {fontFamily : 'Helvetica', fontSize: 24, fill : 0xFFFFFF, align: "middle"};
        let name = new PIXI.Text(title, options);
        name.position.x = appWidth/2 - name.width/2;
        name.position.y = 80
        container.addChild(name);


        const cardContainer = new PIXI.Container();
        cardContainer.tint = 0xFF00FF;
        cardContainer.position.x = appWidth/2 - cardWidth*1.5;
        if (showFullDeck) {
            cardContainer.position.x = cardWidth;            
        }
        cardContainer.position.y = 140;
        container.addChild(cardContainer);

        var cards = this.thisPlayer(game).card_choice_info["cards"];

        var index = 0;
        for (let card of cards) {
            let cardSprite = this.cardSprite(game, card, this.userOrP1(game), false);
            cardSprite.position.x = (cardWidth + 5) *  (index % 8) + cardWidth/2;
            cardSprite.position.y = cardHeight/2 + (cardHeight + 5) * Math.floor(index / 8);            
            cardContainer.addChild(cardSprite);

            var self = this;
            cardSprite
                .on('click',        function (e) {
                    card_on_click(card);
                })
            index += 1;
        }
    }

    baseCardSprite(card, cardTexture) {
        let cardSprite = new PIXI.Sprite.from(cardTexture);
        cardSprite.interactive = true;
        cardSprite.card = card;
        cardSprite.buttonMode = true;  // hand cursor

        return cardSprite;
    }

    cardSpriteInPlay(game, card, player, dont_attach_listeners) {
        var cardTexture;
        if (card.name == "Mana Battery") {
            cardTexture = this.cardTextureInPlayArtifact;
        } else {
            cardTexture = this.cardTextureInPlay;
        }

        var cardSprite = this.baseCardSprite(card, cardTexture);
        let imageSprite = new PIXI.Sprite.from(PIXI.Texture.from(this.imagePath(card)));
        imageSprite.width = 66;
        imageSprite.height = 75;
        imageSprite.position.y = -2;
        cardSprite.addChild(imageSprite);

        let options = {fontFamily : 'Helvetica', fontSize: 8, fill : 0x00000, wordWrap: true, wordWrapWidth: 60};
        
        let aFX = -cardWidth / 2;
        let aFY = -cardHeight / 2;

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

        if (card.card_type == "Entity") {
            let cardPower = card.power;
            let cardToughness = card.toughness - card.damage;
            if (card.tokens) {
                // todo does this code need to be clientside?
                for (let c of card.tokens) {
                    if (c.multiplier == "self_artifacts" && player.artifacts) {
                        cardPower += c.power_modifier * player.artifacts.length;                        
                    } else if (c.multiplier == "self_entities_and_artifacts") {
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
            options.fill = 0x000000;
            let centerOfEllipse = 17
            var powerX = aFX + centerOfEllipse;
            var powerY  = aFY + cardHeight - 14;
            this.addCircledLabel(powerX, powerY, cardSprite, options, cardPower);
            var toughnessX  = aFX + cardWidth - centerOfEllipse;
            this.addCircledLabel(toughnessX, powerY, cardSprite, options, cardToughness);
        } else if (card.turn_played == -1 && !attackEffect) {
            let type = new PIXI.Text(card.card_type, options);
            type.position.x = aFX + cardWidth - 28;
            type.position.y = aFY + cardHeight - 18;
            cardSprite.addChild(type);
        }

        if (attackEffect) {
            let powerCharges = new PIXI.Text(attackEffect.power + "/" + attackEffect.counters, options);
            if (attackEffect.name == "make_random_townie") {
                powerCharges = new PIXI.Text(attackEffect.counters + "/" + attackEffect.amount, options);
            }
            powerCharges.position.x = aFX + cardWidth - 14;
            powerCharges.position.y = aFY + cardHeight - 18;
            cardSprite.addChild(powerCharges);
        }

        var filters = []
        if (!card.can_be_clicked) {
            filters.push(cantBeClickedFilter());                        
        }
        if (card.shielded && card.turn_played > -1) {
            filters.push(new GodrayFilter());                        
        }
        if (card.abilities.length > 0 && card.abilities[0].descriptive_id == "Lurker" && card.abilities[0].enabled && card.turn_played > -1) {
            filters.push(new GodrayFilter());                        
            cardSprite.tint = 0xff0000;
        }

        cardSprite.filters = filters;

        if (dont_attach_listeners) {
            return cardSprite;
        }

        if (card.can_be_clicked) {
            if (this.thisPlayer(game).card_info_to_resolve["card_id"]) {
                var self = this;
                cardSprite.on('click',        function (e) {self.gameRoom.sendPlayMoveEvent("SELECT_ENTITY", {"card":card.id});})
            } else {
                var self = this;
                cardSprite
                    .on('mousedown',        function (e) {onDragStart(e, this, self)})
                    .on('touchstart',       function (e) {onDragStart(e, this, self)})
                    .on('mouseup',          function ()  {onDragEnd(this, self)})
                    .on('mouseupoutside',   function ()  {onDragEnd(this, self)})
                    .on('touchend',         function ()  {onDragEnd(this, self)})
                    .on('touchendoutside',  function ()  {onDragEnd(this, self)})
                    .on('mousemove',        function ()  {onDragMove(this, self, self.bump)})
                    .on('touchmove',        function ()  {onDragMove(this, self, self.bump)})
                    .on('mouseover',        function ()  {onMouseover(this, self)})
                    .on('mouseout',        function ()  {onMouseout(this, self)})
            }
        } else { 
            var self = this;
            cardSprite
                .on('mouseover',        function ()  {onMouseover(this, self)})
                .on('mouseout',        function ()  {onMouseout(this, self)})
        }


         if (cardSprite.card.damage_to_show > 0) {
           this.damageSprite(cardSprite);
        }

        cardSprite.anchor.set(.5);
        for (let child of cardSprite.children) {
            child.anchor.set(.5);
        }

        return cardSprite;
    }

    imagePath(card) {
        let imageName = card.image;
        if (!imageName) {
            imageName = "hades-symbol.svg"
        }
        return '/static/images/card-art/' + imageName;
    }

    cardSprite(game, card, player, dont_attach_listeners, useLargeSize) {
        var cardTexture = (useLargeSize ? this.cardLargeTexture : this.cardTexture); 
        var cardSprite = this.baseCardSprite(card, cardTexture);

        cardSprite.interactive = true;
        cardSprite.card = card;
        cardSprite.buttonMode = true;  // hand cursor

        let imageSprite = new PIXI.Sprite.from(PIXI.Texture.from(this.imagePath(card)));
        imageSprite.width = 37;
        imageSprite.height = 52;
        imageSprite.position.y = -29;
        if (useLargeSize) {
            imageSprite.height *=2;
            imageSprite.width *=2;
            imageSprite.position.y = -58;
        }
        cardSprite.addChild(imageSprite);

        let options = {fontFamily : 'Helvetica', fontSize: 8, fill : 0x00000, wordWrap: true, wordWrapWidth: 60};        
        if (useLargeSize) {
            options = {fontFamily : 'Helvetica', fontSize: 10, fill : 0x00000, wordWrap: true, wordWrapWidth: 109};        
        }

        let aFX = -8;
        let aFY = -9;

        var cw = cardWidth;
        var ch = cardHeight;
        if (useLargeSize) {
            aFX = -cardWidth/4 + 16;
            aFY = -cardHeight/4;
            cw*= 2;
            ch*= 2;            
        }

        const nameBackground = new PIXI.Sprite.from(PIXI.Texture.WHITE);
        nameBackground.tint = 0x000000
        nameBackground.width = cw - 6;
        nameBackground.height = 12;
        nameBackground.alpha = .7;
        nameBackground.position.x = aFX + 8;
        nameBackground.position.y = aFY;
            if (useLargeSize) {
                nameBackground.position.y += 20
                nameBackground.width -= 24;
            }
        cardSprite.addChild(nameBackground);

        let nameOptions = { ...options };
        nameOptions.fill = 0xffffff;
        let name = new PIXI.Text(card.name, nameOptions);
        cardSprite.addChild(name);
        name.position.x = nameBackground.position.x;
        name.position.y = nameBackground.position.y;


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
        if (card.card_type != "Effect") {
            var costX = aFX - 23;
            var costY = aFX - 38;
            if (useLargeSize) {
                costX -= cw/4;
                costY -= ch/4;
            }
            this.addCircledLabel(costX, costY, cardSprite, options, card.cost);
        }            

        options.wordWrapWidth = 72;
        if (useLargeSize) {
            options.wordWrapWidth = 142;
        }

        if (card.description && card.description.length > 120) {
               options.fontSize = 6; 
        }


        let description = new PIXI.Text(card.description, options);
        if (card.description) {
            // todo don't hardcode hide description for Infernus
            // todo don't hardcode hide description for Winding One
            if ((card.card_type == "Entity" && activatedEffects.length == 0) ||
                card.card_type != "Entity" ||
                card.turn_played == -1) {
                cardSprite.addChild(description);
            }
        }
        description.position.x = name.position.x;
        description.position.y = name.position.y + 28;
        if (useLargeSize) {
            description.position.y += 20 + 2;
        }


        var addedDescription = null;
        if (card.added_descriptions.length) {
            for (let d of card.added_descriptions) {
                addedDescription = new PIXI.Text(d, options);
                addedDescription.position.x = name.position.x;
                addedDescription.position.y = description.position.y + description.height;
                cardSprite.addChild(description);
            }
        }

        var abilitiesText = "";
        var color = 0xAAAAAA;
        for (let a of card.abilities) {
            if (!["Starts in Play", "die_to_top_deck", "discard_random_to_deck"].includes(a.descriptive_id)) {
                if (a.description) {
                    abilitiesText += a.description;
                    color = 0x000000;
                } else {
                    var hasSpecialLargeText = false;
                    // for Befuddling Guitar
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

        if (useLargeSize) {
            this.showAbilityPanels(cardSprite, card, options, cw, ch);
        }

        for (let c of card.tokens) {
           if (c.set_can_act == false) {
            if (abilitiesText.length) {
                abilitiesText += ", ";
            }
            abilitiesText += "Can't Attack";
           }
        }

        if (abilitiesText) {
            options.fill = color;
            let abilities = new PIXI.Text(abilitiesText, options);
            abilities.position.x = name.position.x;                
            if (card.added_descriptions.length) {
                abilities.position.y = addedDescription.position.y + addedDescription.height;
            } else if (card.description) {
                abilities.position.y = description.position.y + description.height;
            } else {
                abilities.position.y = name.position.y + 30;                
            }
            if (useLargeSize) {
                abilities.position.y += 20 + 2;
            }
            cardSprite.addChild(abilities);
        }        


        if (card.card_type == "Entity") {
            let cardPower = card.power;
            let cardToughness = card.toughness - card.damage;
            if (card.tokens) {
                // todo does this code need to be clientside?
                for (let c of card.tokens) {
                    if (c.multiplier == "self_artifacts" && player.artifacts) {
                        cardPower += c.power_modifier * player.artifacts.length;                        
                    } else if (c.multiplier == "self_entities_and_artifacts") {
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
            options.fill = 0x000000;

            let centerOfEllipse = 16

            var powerX = aFX - cw/2 + centerOfEllipse;
            var powerY = aFY + ch/2;
            var defenseX = aFX + cw/2;

            if (useLargeSize) {
                powerY += 20;
                powerX -= 5;
                defenseX -= 5;

            }

            this.addCircledLabel(powerX, powerY, cardSprite, options, cardPower);
            this.addCircledLabel(defenseX, powerY, cardSprite, options, cardToughness);

        } else if (card.turn_played == -1 && !attackEffect) {
            var typeX = aFX + cw/4 - 33;
            var typeY = aFY + ch/2 - 5;
            if (useLargeSize) {
                typeX -= 20;
                typeY += 20;
            }
            var typeBG = new PIXI.Graphics();
            typeBG.beginFill(0x111111);
            typeBG.drawRoundedRect(
                0,
                0,
                42,
                12,
                30
            );
            typeBG.position.x = typeX;
            typeBG.position.y = typeY;
            typeBG.endFill();
            typeBG.alpha = .7;
            cardSprite.addChild(typeBG);

            let typeOptions = { ...options };
            typeOptions.fill = 0xffffff;
            let type = new PIXI.Text(card.card_type, typeOptions);
            type.position.x = typeX + 20;
            type.position.y = typeY + 6
            cardSprite.addChild(type);
        }

        if (attackEffect) {
            let powerCharges = new PIXI.Text(attackEffect.power + "/" + attackEffect.counters, options);
            if (attackEffect.name == "make_random_townie") {
                powerCharges = new PIXI.Text(attackEffect.counters + "/" + attackEffect.amount, options);
            }
            powerCharges.position.x = aFX + cw - 14;
            powerCharges.position.y = aFY + ch - 18;
            cardSprite.addChild(powerCharges);
        }

        var filters = []
        if (!card.can_be_clicked) {
            filters.push(cantBeClickedFilter());                        
        }
        if (card.shielded && card.turn_played > -1) {
            filters.push(new GodrayFilter());                        
        }
        if (card.abilities.length > 0 && card.abilities[0].descriptive_id == "Lurker" && card.abilities[0].enabled && card.turn_played > -1) {
            filters.push(new GodrayFilter());                        
            cardSprite.tint = 0xff0000;
        }

        cardSprite.filters = filters;

        if (dont_attach_listeners) {
            return cardSprite;
        }

        if (card.can_be_clicked) {
            if (this.thisPlayer(game).card_info_to_resolve["card_id"]) {
                var self = this;
                cardSprite.on('click',        function (e) {self.gameRoom.sendPlayMoveEvent("SELECT_ENTITY", {"card":card.id});})
            } else {
                var self = this;
                cardSprite
                    .on('mousedown',        function (e) {onDragStart(e, this, self)})
                    .on('touchstart',       function (e) {onDragStart(e, this, self)})
                    .on('mouseup',          function ()  {onDragEnd(this, self)})
                    .on('mouseupoutside',   function ()  {onDragEnd(this, self)})
                    .on('touchend',         function ()  {onDragEnd(this, self)})
                    .on('touchendoutside',  function ()  {onDragEnd(this, self)})
                    .on('mousemove',        function ()  {onDragMove(this, self, self.bump)})
                    .on('touchmove',        function ()  {onDragMove(this, self, self.bump)})
                if (!useLargeSize) {
                    cardSprite
                        .on('mousedown',        function (e) {onDragStart(e, this, self)})
                        .on('touchstart',       function (e) {onDragStart(e, this, self)})
                        .on('mouseup',          function ()  {onDragEnd(this, self)})
                        .on('mouseupoutside',   function ()  {onDragEnd(this, self)})
                        .on('touchend',         function ()  {onDragEnd(this, self)})
                        .on('touchendoutside',  function ()  {onDragEnd(this, self)})
                        .on('mousemove',        function ()  {onDragMove(this, self, self.bump)})
                        .on('touchmove',        function ()  {onDragMove(this, self, self.bump)})
                        .on('mouseover',        function ()  {onMouseover(this, self)})
                        .on('mouseout',        function ()  {onMouseout(this, self)})
                }
            }
        } else { 
            var self = this;
            if (!useLargeSize) {
                cardSprite
                    .on('mouseover',        function ()  {onMouseover(this, self)})
                    .on('mouseout',        function ()  {onMouseout(this, self)})
            }
        }


         if (cardSprite.card.damage_to_show > 0) {
           this.damageSprite(cardSprite);
        }

        cardSprite.anchor.set(.5);
        for (let child of cardSprite.children) {
            // graphics we draw don't have an anchor, like the circle for costBackground
            if (child.anchor) {
                child.anchor.set(.5);                
            }
        }

        return cardSprite;
    }

    addCircledLabel(costX, costY, cardSprite, options, value) {
        var circle = this.circleBackground(costX, costY);
        cardSprite.addChild(circle);
        let cost = new PIXI.Text(value, options);
        cost.position.x = -3;
        cost.position.y = -5;
        circle.addChild(cost);
    }

    circleBackground(x, y) {
        const circlRadius = 7;
        const background = new PIXI.Graphics();
        background.beginFill(0xffffff, 1);
        background.drawCircle(0, 0, circlRadius);
        background.endFill();
        const sprite = new PIXI.Sprite.from(PIXI.Texture.WHITE);
        sprite.position.x = x;
        sprite.position.y = y;
        sprite.mask = background;
        sprite.width = circlRadius*2;
        sprite.height = circlRadius*2;
        sprite.addChild(background);
        return sprite;
    }

    showAbilityPanels(cardSprite, card, options, cw, ch) {
        const topBG = new PIXI.Sprite.from(PIXI.Texture.WHITE);
        cardSprite.addChild(topBG);
        topBG.tint = 0xffff00;
        var yPosition = 0;
        for (let a of card.abilities) {
            let abilityText = new PIXI.Text("", options);
            if (a.name == "Shield") {
                abilityText.text = "Shield - Shielded entities don't take damage the first time they get damaged.";
            }                    
            if (a.name == "Guard") {
                abilityText.text = "Guard - Guard entities must be attacked before anything else.";
            }                    
            if (a.name == "Syphon") {
                abilityText.text = "Syphon - Gain hit points whenever this deals damage.";
            }                    
            if (a.name == "Fast") {
                abilityText.text = "Fast - Fast entities may attack the turn they come into play.";
            }                    
            if (a.name == "Ambush") {
                abilityText.text = "Ambush - Ambush entities may attack other entities the turn they come into play.";
            }                    
            if (a.name == "Instrument Required") {
                abilityText.text = "Instrument Required - You must have an Instrument in play to play this.";
            }                    
            if (a.name == "Townie") {
                abilityText.text = "Townie - Townies have a little ability.";
            }                    
            if (a.name == "Unique") {
                abilityText.text = "Unique - only one Unique card is allowed per deck.";
            }                    
            if (a.name == "Weapon") {
                abilityText.text = "Weapon - Weapons can be used to attack players and entities.";
            }                    
            if (a.name == "Instrument") {
                abilityText.text = "Instrument - Instruments have special abilities and are needed for other cards.";
            } 
            if (a.name == "Fade") {
                abilityText.text = "Fade - Fade entities get -1/-1 at the beginning of the turn.";
            }                    
            if (a.name == "Stomp") {
                abilityText.text = "Stomp - Stomp entities deal excess damage to players.";
            }                    
            if (a.name == "Lurker") {
                abilityText.text = "Lurker - Lurker entities can't be targetted until they attack.";
            }                    
            if (abilityText.text) {
                abilityText.position.x = cw;
                abilityText.position.y = yPosition - ch/2 + 20;
                abilityText.width = cw - 20;
                yPosition += 40;
                cardSprite.addChild(abilityText);
            }
        }
        if (yPosition == 0) {
            cardSprite.removeChild(topBG);
        }
        topBG.width = cw;
        topBG.height = yPosition + 20;
        topBG.position.x = cw + 5;
        topBG.position.y = -ch/2 + (20+yPosition)/2;

    }

    removeCardsFromStage(game) {
        if (this.thisPlayer(game) && this.opponent(game)) {
            let spritesToRemove = [];
            for (let sprite of this.app.stage.children) {
                if (sprite.card) {
                    if (sprite.card && !sprite.dragging) {
                        spritesToRemove.push(sprite);
                    }                    
                }
            }
            for (let sprite of spritesToRemove) {
                if (sprite.parent) {
                    sprite.parent.removeChild(sprite)
                }
            }
        }
    }

    showCardThatWasCast(card, game, player) {
      var godray = new GodrayFilter();
      var incrementGodrayTime = () => {
        godray.time += this.app.ticker.elapsedMS / 1000;
      }
      let sprite = this.cardSprite(game, card, player, false);
      sprite.position.x = 100;
      sprite.position.y = this.inPlay.position.y + padding;
      sprite.scale.set(1.5);
      this.app.stage.addChild(sprite)
      this.app.ticker.add(incrementGodrayTime)
      this.app.stage.filters = [godray];
      setTimeout(() => { 
            this.app.stage.filters = []; 
            this.app.ticker.remove(incrementGodrayTime)
            this.app.stage.removeChild(sprite)
        }, 1000);

    }

    showRope() {
        return;
        if (this.showingRope) {
            return;
        }
      var godray = new GodrayFilter();
      let sprite = new PIXI.Sprite.from(this.inPlayTexture);
      this.ropeSprite = sprite;
      sprite.tint = 0xff0000;
      var lastElapsed = 0
      var totalElapsed = 0
      let ropeLength = 570;
      let tickMS = 50;
      let ropeTime = tickMS*4;
      this.ropeGodrayTimeTicker = () => {
        if (sprite.position.x >= ropeLength) {
            this.gameRoom.endTurn()
            this.showingRope = false;
            sprite.filters = []; 
            this.app.ticker.remove(this.ropeGodrayTimeTicker)            
            this.app.stage.removeChild(sprite)
            this.ropeSprite = null;
        }
        godray.time += this.app.ticker.elapsedMS / tickMS;
        if ((totalElapsed - lastElapsed) <= tickMS) {
            totalElapsed += this.app.ticker.elapsedMS;
            return;
        }
        lastElapsed = totalElapsed;
        sprite.width -= ropeLength/ropeTime;
        sprite.position.x += ropeLength/ropeTime;
      }
      sprite.position.x = 10;
      sprite.position.y = this.inPlay.position.y - padding + 1;
      sprite.height = 8; 
      this.app.stage.addChild(sprite)
      this.app.ticker.add(this.ropeGodrayTimeTicker)
      this.showingRope = true;
      sprite.filters = [godray];

    }

    renderEndTurnButton(game) {
        if (this.turnLabel) {
            this.buttonMenu.removeChild(this.turnLabel)
        }
        if (this.endTurnButton) {
            this.buttonMenu.removeChild(this.endTurnButton)
        }

        const b = new PIXI.Sprite.from(this.newGameButtonTexture);
        b.buttonMode = true;
        b.position.x = 23;
        b.position.y = 17;
        b.interactive = true;
        var clickFunction = () => {
            this.gameRoom.endTurn()
            if (this.ropeSprite) {
                this.showingRope = false;
                this.ropeSprite.filters = []; 
                this.app.ticker.remove(this.ropeGodrayTimeTicker)            
                this.app.stage.removeChild(this.ropeSprite)
                this.ropeSprite = null;
            }
        };
        b
            .on('click', clickFunction)
            .on('tap', clickFunction)

        let textFillColor = 0xffffff;
        if (this.isActivePlayer(game)) {
            if (this.thisPlayer(game).mana == 0) {
                b.tint = 0xff0000;
            } else {
                b.tint = 0xff7b7b;
            }
        } else {
            textFillColor = 0xAAAAAA;
        }
        let text = new PIXI.Text("End Turn", {fontFamily : 'Helvetica', fontSize: 12, fill : textFillColor});
        text.position.x = 27;
        text.position.y = 14;
        b.addChild(text);


        this.endTurnButton = b;
        this.buttonMenu.addChild(this.endTurnButton)

        let turnText = new PIXI.Text(`${this.thisPlayer(game).username} is Active\n(Turn ${game.turn})`, {fontFamily : 'Helvetica', fontSize: 12, fill : textFillColor, align: "center"});
        turnText.position.x = this.buttonMenu.width/2;
        turnText.position.y = b.position.y + 60 + padding;
        turnText.anchor.set(0.5, 0.5);
        this.turnLabel = turnText;
        this.buttonMenu.addChild(turnText);

    }

    isActivePlayer(game) {
        return (game.turn % 2 == 0 && this.userOrP1(game).username == game.players[0].username
                || game.turn % 2 == 1 && this.userOrP1(game).username == game.players[1].username)
    }

    activePlayer(game) {
        if (game.turn % 2 == 0) {
            return game.players[0];
        }
        return game.players[1];
    }


    updatePlayer(game, player, avatarSprite) {
        var props = {fontFamily : 'Helvetica', fontSize: 12, fill : 0x00000};
        avatarSprite.children = []
        let avatar;
        let usernameText = player.username;
        if (player == this.opponent(game)) {
            usernameText += " (opponent)"
            avatar = new PIXI.Sprite.from(this.bearTexture);
        } else {
            avatar = new PIXI.Sprite.from(this.tigerTexture);
        }
        avatar.scale.set(.5);
        avatar.position.x = padding/2;
        avatar.position.y = padding/2;
        avatarSprite.addChild(avatar);

        let username = new PIXI.Text(usernameText, props);
        username.position.x = padding/2 + avatar.position.x + avatar.width;
        username.position.y = padding/2;
        avatarSprite.addChild(username);

        let hp = new PIXI.Text(player.hit_points + " hp", props);
        hp.position.x = padding/2 + avatar.position.x + avatar.width;
        hp.position.y = username.height + username.position.y
        avatarSprite.addChild(hp);

        let armor = new PIXI.Text(player.armor + " armor", props);
        armor.position.x = padding/2 + avatar.position.x + avatar.width;
        armor.position.y = hp.height + hp.position.y;
        avatarSprite.addChild(armor);

        let mana = new PIXI.Text("Mana: " + this.manaString(player.max_mana, player.mana), props);
        mana.position.x = padding/2 + avatar.position.x + avatar.width;
        mana.position.y = armor.height + armor.position.y;
        avatarSprite.addChild(mana);

        let hand = mana;
        if (player == this.opponent(game)) {
            hand = new PIXI.Text("Hand: " + player.hand.length, props);
            hand.position.x = padding/2 + avatar.position.x + avatar.width;
            hand.position.y = mana.height + mana.position.y;
            avatarSprite.addChild(hand);        
        }

        let deck = new PIXI.Text("Deck: " + player.deck.length, props);
        deck.position.x = padding/2 + avatar.position.x + avatar.width;
        deck.position.y = hand.height + hand.position.y;
        avatarSprite.addChild(deck);

        let playedPile = new PIXI.Text("Played Pile: " + player.played_pile.length, props);
        playedPile.position.x = padding/2 + avatar.position.x + avatar.width;
        playedPile.position.y = deck.height + deck.position.y;
        avatarSprite.addChild(playedPile);

        if (!player.can_be_clicked) {
            avatarSprite.filters = [cantBeClickedFilter()];                        
            avatarSprite.on('click', function (e) {})
            avatarSprite.interactive = false;
            avatarSprite.buttonMode = true;
       } else {
            avatarSprite.interactive = true;
            avatarSprite.buttonMode = true;
            avatarSprite.filters = [];                                   
            if (this.activePlayer(game).card_info_to_resolve["card_id"]) {
                var eventString = "SELECT_OPPONENT";
                if (player == this.thisPlayer(game)) {
                    eventString = "SELECT_SELF";
                }
                var self = this;
                avatarSprite
                    .on('click', function (e) {self.gameRoom.sendPlayMoveEvent(eventString, {});})
            }
        }

        if (player.damage_to_show > 0) {
           this.damageSprite(avatarSprite);
        }
    }

    damageSprite(spriteToDamage) {
        spriteToDamage.tint = 0xFF00000;
        var godray = new GodrayFilter();
        var incrementGodrayTime = () => {
            godray.time += this.app.ticker.elapsedMS / 1000;
        }
        this.app.ticker.add(incrementGodrayTime)
        spriteToDamage.filters = [godray];
          setTimeout(() => { 
                spriteToDamage.tint = 0xFFFFFF;
                spriteToDamage.filters = []; 
                this.app.ticker.remove(incrementGodrayTime)
            }, 1000);   
    }

    manaString(maxMana, currentMana) {
        var manaString = "";

        for (var i=0;i<currentMana;i++) {
            manaString += "✦"
        }
        for (var i=0;i<maxMana-currentMana;i++) {
            manaString += "✧"
        }
        return manaString
    }

    updateHand(game) {
        var index = 0;
        for (let card of this.thisPlayer(game).hand) {
            let sprite = this.cardSprite(game, card, this.userOrP1(game), false);
            sprite.position.x = (cardWidth)*index + cardWidth/2 + padding;
            sprite.position.y = this.handContainer.position.y + cardHeight/2;
            this.app.stage.addChild(sprite);
            index++;                
        }
    }

    updateThisPlayerInPlay(game) {
        this.updateInPlay(game, this.thisPlayer(game), this.inPlay);
    }

    updateOpponentInPlay(game) {
        this.updateInPlay(game, this.opponent(game), this.inPlayOpponent);
    }

    updateInPlay(game, player, inPlaySprite) {
        var cardIdToHide = null
        for (let card of player.in_play) {
            if (player.card_info_to_resolve["card_id"] && card.id == player.card_info_to_resolve["card_id"] && player.card_info_to_resolve["effect_type"] != "entity_comes_into_play" && player.card_info_to_resolve["effect_type"] != "entity_activated") {
                cardIdToHide = card.id;
                break;
            }
        }

        var inPlayLength = player.in_play.length;
        if (cardIdToHide && player == this.thisPlayer(game)) {
            inPlayLength -= 1;
        }

        inPlaySprite.children = []
        var index = 0;
        if (inPlayLength == 1 || inPlayLength == 2) {
            index = 3
        } else if (inPlayLength == 3 || inPlayLength == 4) { 
            index = 2
        } else if (inPlayLength == 5 || inPlayLength == 6) { 
            index = 1
        }
        for (let card of player.in_play) {
            if (cardIdToHide && card.id == cardIdToHide && player == this.thisPlayer(game)) {
                continue;
            }

            let sprite = this.cardSpriteInPlay(game, card, player, false);
            sprite.position.x = (cardWidth)*index + cardWidth/4 + padding;
            sprite.position.y = inPlaySprite.position.y + cardHeight/2;

            if (cardIdToHide && card.id == cardIdToHide && player == this.opponent(game)) {
                sprite.filters = [targettableGlowFilter()];
            }

            this.app.stage.addChild(sprite);
            index++;
        }

    }

    updateThisPlayerArtifacts(game) {
        this.updateArtifacts(game, this.thisPlayer(game), this.artifacts);
    }

    updateOpponentArtifacts(game) {
        this.updateArtifacts(game, this.opponent(game), this.artifactsOpponent);
    }


    updateArtifacts(game, player, artifactsSprite) {
        // artifactsSprite.children = []
        var cardIdToHide = null
        for (let card of player.artifacts) {
            if (player.card_info_to_resolve["card_id"] && card.id == player.card_info_to_resolve["card_id"]) {
                cardIdToHide = card.id;
                break;
            }
        }

        var index = 0;

        for (let card of player.artifacts) {
            if (cardIdToHide && card.id == cardIdToHide && player == this.thisPlayer(game)) {
                continue;
            }

            let sprite = this.cardSpriteInPlay(game, card, player, false);
            this.app.stage.addChild(sprite);
            sprite.position.y = artifactsSprite.position.y + cardHeight/2;
            sprite.position.x = artifactsSprite.position.x + cardWidth*index + cardWidth/2;
            index++;
            if (cardIdToHide && card.id == cardIdToHide) {
                sprite.filters = [targettableGlowFilter()];
            }
        }
    }

    thisPlayer(game) {
        for(let player of game.players) {
            if (player.username == this.username) {
                return player
            }
        }
        return game.players[0];
    }

    opponent(game) {
        let thisPlayer = this.thisPlayer(game);
        if (thisPlayer == game.players[1]) {
            return game.players[0];
        }
        return game.players[1];
    }

    // Returns the currently player, or it returns the first player,
    // if it's an observer and not a player calling this function
    userOrP1(game) {

        if (this.username == game.players[0].username) {
            return game.players[0];
        }
        if (this.username == game.players[1].username) {
            return game.players[1];
        }
        // if the this.username isn't one of the players, return the first player
        return game.players[0];
    }

    logMessage(log_lines) {
        if (this.messageNumber == null) {
            this.messageNumber = -1;
        }
        for (let text of log_lines) {
            this.messageNumber += 1
            var textSprite = new PIXI.Text(text, {wordWrap: true, wordWrapWidth: 360, fontSize: 10});
            textSprite.position.x = 5;
            textSprite.position.y = this.messageNumber * 16 + 5;
            this.scrollboxBackground.height = Math.max(cardHeight*1.25, (this.messageNumber + 1) * 16);
            this.gameLogScrollbox.content.addChild(textSprite);
        }
        this.gameLogScrollbox.content.top += this.gameLogScrollbox.content.worldScreenHeight;
        this.gameLogScrollbox.update();
    }

}


function onDragStart(event, cardSprite, gameUX) {
    // store a reference to the data
    // the reason for this is because of multitouch
    // we want to track the movement of this particular touch
    cardSprite.data = event.data;
    cardSprite
        .on('mouseover',        function ()  {})
        .on('mouseout',        function ()  {})     
    onMouseout(cardSprite, gameUX);
    cardSprite.dragging = true;
    if (cardSprite.card.turn_played == -1) {
        if(cardSprite.card.card_type == "Spell" && cardSprite.card.needs_targets) {
            gameUX.gameRoom.sendPlayMoveEvent("SELECT_CARD_IN_HAND", {"card":cardSprite.card.id});
        } 
    } else if (cardSprite.card.card_type == "Entity") {
        gameUX.gameRoom.sendPlayMoveEvent("SELECT_ENTITY", {"card":cardSprite.card.id});
    } else if (cardSprite.card.card_type == "Artifact") {
        gameUX.gameRoom.sendPlayMoveEvent("SELECT_ARTIFACT", {"card":cardSprite.card.id});
        let enabled_effects = [];
        for (let e of cardSprite.card.effects) {
            if (e.effect_type == "activated" && e.enabled == true) {
                enabled_effects.push(e);
            }
        }
        var dragging = true;
        for (let e of enabled_effects) {
            if (!["any", "any_enemy", "entity", "opponents_entity", "self_entity", "artifact", "any_player"].includes(e.target_type)) {
                // e.target_type is in ["self", "opponent", "Artifact", "all"]
                dragging = false;
            }
        }
        if (!dragging) {
            cardSprite.filters = [];
            cardSprite.dragging = false; 
        }
    }

}

function onDragEnd(cardSprite, gameUX) {
    var playedMove = false;
    var bump = gameUX.bump;
    if (cardSprite.card.turn_played == -1) {
        if(!bump.hit(cardSprite, gameUX.handContainer) && (cardSprite.card.card_type == "Spell" || cardSprite.card.card_type == "Artifact") && !cardSprite.card.needs_targets) {
            gameUX.gameRoom.sendPlayMoveEvent("SELECT_CARD_IN_HAND", {"card":cardSprite.card.id});
            playedMove = true;
        } else if(bump.hit(cardSprite, gameUX.inPlay) && cardSprite.card.card_type == "Entity" && cardSprite.card.can_be_clicked) {
            gameUX.gameRoom.sendPlayMoveEvent("SELECT_CARD_IN_HAND", {"card":cardSprite.card.id});
            playedMove = true;
        } else if(bump.hit(cardSprite, gameUX.opponentAvatar) && cardSprite.card.card_type == "Spell" && gameUX.opponent(gameUX.game).can_be_clicked) {
            gameUX.gameRoom.sendPlayMoveEvent("SELECT_OPPONENT", {});
            playedMove = true;
        } else if(bump.hit(cardSprite, gameUX.playerAvatar) && cardSprite.card.card_type == "Spell" && gameUX.thisPlayer(gameUX.game).can_be_clicked) {
            gameUX.gameRoom.sendPlayMoveEvent("SELECT_SELF", {});
            playedMove = true;
        } else {
            var collidedSprite;
            for (let sprite of gameUX.app.stage.children) {
                if (bump.hit(cardSprite, sprite) && cardSprite.card && sprite.card && cardSprite.card.id != sprite.card.id) {
                    collidedSprite = sprite;
                }
            }
            if(collidedSprite && collidedSprite.card && collidedSprite.card.can_be_clicked) {
                if (collidedSprite.card.card_type == "Entity") {
                    gameUX.gameRoom.sendPlayMoveEvent("SELECT_ENTITY", {"card": collidedSprite.card.id});
                } else if (collidedSprite.card.card_type == "Artifact") {
                    gameUX.gameRoom.sendPlayMoveEvent("SELECT_ARTIFACT", {"card": collidedSprite.card.id});
                } else {
                    console.log("tried to select unknown card type: " + collidedSprite.card.card_type);
                }
                playedMove = true;
            }
        }
    } else {  // it's an entity or artifact already in play
        if(bump.hit(cardSprite, gameUX.opponentAvatar)) {
            gameUX.gameRoom.sendPlayMoveEvent("SELECT_OPPONENT", {});
            playedMove = true;
        } else if(!bump.hit(cardSprite, gameUX.artifacts) && cardSprite.card.card_type == "Artifact" && cardSprite.card.effects[0] && cardSprite.card.effects[0].target_type == "all") {
            gameUX.gameRoom.sendPlayMoveEvent("ACTIVATE_ARTIFACT", {"card":cardSprite.card.id});
            playedMove = true;
        } else {
            // todo: this shouldn't bump any non opponent non clickable cards, but that depends on pefect game state 
            for (let opponentEntity of gameUX.app.stage.children) {
                if(opponentEntity.card && opponentEntity.card.id != cardSprite.card.id && opponentEntity.card.can_be_clicked && bump.hit(cardSprite, opponentEntity)) {
                    gameUX.gameRoom.sendPlayMoveEvent("SELECT_ENTITY", {"card": opponentEntity.card.id});
                    playedMove = true;
                }
            }
        }

    }
    
    if(!playedMove) {
        gameUX.gameRoom.sendPlayMoveEvent("UNSELECT", {});
    }

    cardSprite.dragging = false;
    cardSprite.data = null;
    cardSprite.filters = []
    gameUX.inPlay.filters = [];
    gameUX.opponentAvatar.filters = [];
}


function onDragMove(cardSprite, gameUX, bump) {
    if (cardSprite.dragging) {
        var newPosition = cardSprite.data.getLocalPosition(cardSprite.parent);
        cardSprite.position.x = newPosition.x;
        cardSprite.position.y = newPosition.y;
        var parent = cardSprite.parent;
        parent.removeChild(cardSprite);
        parent.addChild(cardSprite);

        let opponentCollision = bump.hit(cardSprite, gameUX.opponentAvatar);
        let selfCollision = bump.hit(cardSprite, gameUX.playerAvatar);
        let handCollision = bump.hit(cardSprite, gameUX.handContainer);
        let inPlayCollision = bump.hit(cardSprite, gameUX.inPlay);
        let artifactsCollision = bump.hit(cardSprite, gameUX.artifacts);
        let cardInHand = cardSprite.card.turn_played == -1;

        let collidedEntity = null;
        for (let entity of gameUX.app.stage.children) {
            if (entity.card && cardSprite.card.id != entity.card.id) {
                if (entity.card.can_be_clicked) {
                    entity.filters = []
                } else {
                    entity.filters = [cantBeClickedFilter()];                                        
                }                
                if(entity.card.turn_played != -1 && entity.card.id != cardSprite.card.id && entity.card.can_be_clicked && bump.hit(cardSprite, entity)) {
                    collidedEntity = entity;
                }
            }
        }

        if(!handCollision && cardSprite.card.card_type == "Spell" && !cardSprite.card.needs_targets) {
            cardSprite.filters = glowAndShadowFilters();
            if (!cardSprite.card.can_be_clicked) {
                cardSprite.filters.push(cantBeClickedFilter());                        
            }
        } else if(!bump.hit(cardSprite, gameUX.artifacts) && cardSprite.card.card_type == "Artifact" && cardSprite.card.effects[0] && cardSprite.card.effects[0].target_type == "all") {
            cardSprite.filters = glowAndShadowFilters();
        } else if((cardSprite.card.card_type == "Spell" || cardSprite.card.card_type == "Artifact") && opponentCollision && gameUX.opponent(gameUX.game).can_be_clicked) {
            gameUX.opponentAvatar.filters = [targettableGlowFilter()];
        } else if((cardSprite.card.card_type == "Spell" || cardSprite.card.card_type == "Artifact") && selfCollision && gameUX.thisPlayer(gameUX.game).can_be_clicked) {
            gameUX.playerAvatar.filters = [targettableGlowFilter()];
        } else if(cardInHand && inPlayCollision && cardSprite.card.card_type == "Entity") {
            cardSprite.filters = glowAndShadowFilters();
            if (!cardSprite.card.can_be_clicked) {
                cardSprite.filters.push(cantBeClickedFilter());                        
            }
        } else if(cardInHand && artifactsCollision && cardSprite.card.card_type == "Artifact") {
            cardSprite.filters = glowAndShadowFilters();
        } else if(!cardInHand && opponentCollision && cardSprite.card.card_type == "Entity") {
            cardSprite.filters = glowAndShadowFilters();
            gameUX.opponentAvatar.filters = [targettableGlowFilter()];
        } else if (collidedEntity && collidedEntity.card.can_be_clicked && ((cardSprite.card.card_type == "Artifact" && collidedEntity.card.card_type == "Entity") || (cardSprite.card.card_type == "Entity" && collidedEntity.card.card_type == "Entity") || (cardSprite.card.card_type == "Spell" && cardSprite.card.needs_targets))) {
            cardSprite.filters = glowAndShadowFilters();
            collidedEntity.filters = [targettableGlowFilter()];
        } else {
            gameUX.inPlay.filters = [];
            if (!cardSprite.card.can_be_clicked) {
                cardSprite.filters = [dropshadowFilter(), cantBeClickedFilter()];
            } else {
                cardSprite.filters = [dropshadowFilter()];
            }
        }

        if (!opponentCollision || !gameUX.opponent(gameUX.game).can_be_clicked) {
            if (gameUX.opponent(gameUX.game).can_be_clicked) {
                gameUX.opponentAvatar.filters = [];
            } else {
                gameUX.opponentAvatar.filters = [cantBeClickedFilter()]; 
            }
        }

        if (!selfCollision || !gameUX.thisPlayer(gameUX.game).can_be_clicked) {
            if (gameUX.thisPlayer(gameUX.game).can_be_clicked) {
                gameUX.playerAvatar.filters = [];
            } else {
                gameUX.playerAvatar.filters = [cantBeClickedFilter()]; 
            }
        }

    }
}


function onMouseover(cardSprite, gameUX) {
    gameUX.hovering = true;
    gameUX.hoverTimeout = setTimeout(() => { 
        if (gameUX.hovering) {
            gameUX.app.stage.removeChild(gameUX.hoverCards);
            gameUX.hovering = false;
            let sprite = gameUX.cardSprite(gameUX.game, cardSprite.card, gameUX.thisPlayer(gameUX.game), false, true);
            sprite.position.x = cardSprite.position.x + cardWidth/2;
            sprite.position.y = cardSprite.position.y - cardHeight*1.5;
            if (sprite.position.y < cardHeight*2) {
                sprite.position.y = cardHeight;
                sprite.position.x = cardSprite.position.x + cardWidth*1.5;
            }
            if (sprite.position.x >= 677) {
                sprite.position.x = cardSprite.position.x - cardWidth;
            }
            gameUX.app.stage.addChild(sprite)
            gameUX.hoverCards = sprite;
        }
    }, 300);

}

function onMouseout(cardSprite, gameUX) {
    clearTimeout(gameUX.hoverTimeout);
    gameUX.hovering = false
    gameUX.app.stage.removeChild(gameUX.hoverCards);
}


function glowAndShadowFilters() {
    return [
        targettableGlowFilter(),
        dropshadowFilter()
    ];
}


function cantBeClickedFilter() {
    return new AdjustmentFilter({ brightness: .8});
}


function dropshadowFilter() {
    return new GlowFilter({ distance: 5, outerStrength: 1 , color: 0x000000});
}


function targettableGlowFilter() {
    return new GlowFilter({ distance: 15, outerStrength: 2 , color: 0xffff00});
}
