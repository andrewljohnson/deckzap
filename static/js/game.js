import * as PIXI from 'pixi.js'
import { Bump } from './lib/bump.js';
import { AdjustmentFilter, DropShadowFilter, GlowFilter, GodrayFilter, OutlineFilter } from 'pixi-filters';
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
        this.oldOpponentHP = 30;
        this.oldSelfHP = 30;        

        this.spriteDamageCounts = {};
        this.arrows = []
        this.bump = new Bump(PIXI);
        this.cardTexture = PIXI.Texture.from('/static/images/card.png');
        this.cardLargeTexture = PIXI.Texture.from('/static/images/card-large.png');
        this.cardTextureInPlay = PIXI.Texture.from('/static/images/in play mob.png');
        this.cardTextureInPlayGuard = PIXI.Texture.from('/static/images/in play guard mob.png');
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
            autoDensity: true,
            backgroundAlpha: true            
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

    newGameButton(x, y, game) {
        const b = new PIXI.Sprite.from(this.newGameButtonTexture);
        b.position.x = x;
        b.position.y = y;
        if (this.isPlaying(game)) {
            b.buttonMode = true;
            b.interactive = true;
        }
        var self = this;
        var clickFunction = function() {
            self.gameRoom.nextRoom()
        };
        b
            .on('click', clickFunction)
            .on('tap', clickFunction)

        let text = new PIXI.Text("New Game", {fontFamily : 'Arial', fontSize: 12, fill : 0x00000});
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
        this.game = game;
        this.loadImagesThenRefreshDisplay(game, message);        
    }

    loadImagesThenRefreshDisplay(game, message) {
        let loadingImages = false;

        if (!this.inPlayNameSet) {
            this.inPlayNameSet = new Set()
        }
        let cards = this.thisPlayer(game).in_play.concat(this.opponent(game).in_play).concat(this.opponent(game).artifacts).concat(this.thisPlayer(game).artifacts)
        loadingImages = this.loadCardImages(cards, 1) || loadingImages;

        cards = this.thisPlayer(game).card_choice_info["cards"] ? this.thisPlayer(game).card_choice_info["cards"] : [];
        cards = cards.concat(this.thisPlayer(game).hand);
        loadingImages = this.loadCardImages(cards, 1) || loadingImages;

        let stackSpells = []
        for (let spell of game.stack) {
            stackSpells.push(spell[1]);
        }
        loadingImages = this.loadCardImages(stackSpells, 1) || loadingImages;

        if (this.thisPlayer(game)) {
            if (message["show_spell"] && !this.thisPlayer(game).card_info_to_target["card_id"]) {
                loadingImages = this.loadCardImages([message["show_spell"]], 1) || loadingImages;
            }
        }

        if (loadingImages) {
            this.app.loader.load(() => {
                this.finishRefresh(message)
                this.app.loader.reset()
            });
        } else {
            this.finishRefresh(message)                        
        }
    }

    loadCardImages(cards, scale) {
        let loadingImages = false;
        for (let card of cards) {
            const loaderURL = this.fullImagePath(card);
            if (this.inPlayNameSet.has(loaderURL)) {
                continue;
            }
            const loaderID = card.name;
            this.inPlayNameSet.add(loaderURL)
            if (!PIXI.utils.TextureCache[loaderID]) {
                loadingImages = true;
                this.loadCardImage(
                    card.card_type,
                    loaderID,
                    loaderURL,
                    scale,
                    );
            }
        }
        return loadingImages;
    }

    // todo: svgs still blurry: https://github.com/pixijs/pixijs/issues/6113
    loadCardImage(cardType, loaderID, loaderURL, scale) {
        if (cardType == "Spell") {
            this.app.loader.add(loaderID, loaderURL, { 
                // resolution: window.devicePixelRatio || 1,
                // resolution: 2,
                metadata: {
                    resourceOptions: {
                        scale: .5,
                    }
                }
            });                       
            this.app.loader.add(loaderID+"?large", loaderURL+"?large", { 
                // resolution: window.devicePixelRatio || 1,
                // resolution: 2,
                metadata: {
                    resourceOptions: {
                        scale: 1,
                    }
                }
            });                       
        } else {
            this.app.loader.add(loaderID, loaderURL, { 
                // resolution: window.devicePixelRatio || 1,
                // resolution: 2,
                metadata: {
                    resourceOptions: {
                        scale: .5,
                    }
                }
            });                       
            this.app.loader.add(loaderID+"?large", loaderURL+"?large", { 
                // resolution: window.devicePixelRatio || 1,
                // resolution: 2,
                metadata: {
                    resourceOptions: {
                        scale: 1,
                    }
                }
            });                       
            this.app.loader.add(loaderID+"?inplay", loaderURL+"?inplay", { 
                // resolution: window.devicePixelRatio || 1,
                // resolution: 2,
                metadata: {
                    resourceOptions: {
                        scale: 1.25,
                    }
                }
            });                       
        }
    }

    finishRefresh(message) {
        const game = this.game;
        if (this.thisPlayer(game)) {
            if (message["show_spell"] && !this.thisPlayer(game).card_info_to_target["card_id"]) {
                for (let sprite of this.app.stage.children) {
                    if (sprite.card && sprite.card.id == message["show_spell"]["id"] && sprite != this.spellBeingCastSprite) {
                        if (sprite.parent) {
                            sprite.parent.removeChild(sprite)
                        }                        
                    }
                }
                this.showCardThatWasCast(message["show_spell"], game, this.thisPlayer(game), message)
                setTimeout(() => {   
                    this.refreshDisplay(message);
                }, 1000);
                return;
            }
        }
        this.refreshDisplay(message);
    }

    refreshDisplay(message) {
        const game = this.game;
        this.clearArrows()
        this.removeCardsFromStage(game)
        if (this.thisPlayer(game)) {
            this.updateHand(game);
            this.updatePlayer(game, this.thisPlayer(game), this.playerAvatar);
            this.updateThisPlayerArtifacts(game);
            this.updateThisPlayerInPlay(game);
        }

        if (this.opponent(game)) {
            this.updatePlayer(game, this.opponent(game), this.opponentAvatar);
            this.updateOpponentArtifacts(game);
            this.updateOpponentInPlay(game);
            if (!this.newGameButtonAdded) {
                this.buttonMenu.addChild(this.newGameButton(22, 230 - 40 - padding - 8, game));
                this.newGameButtonAdded = true;
            }

        }

        if (game.stack.length > 0) {
            this.showSpellStack(game);
        }

        this.renderEndTurnButton(game, message);

        this.game = game;

        if (this.opponent(game) && this.thisPlayer(game)) {
            if (this.opponent(game).hit_points <= 0 || this.thisPlayer(game).hit_points <= 0) {
                alert("GAME OVER");
            }
        }

        this.showAttack(game);

        if (!this.isShowingCastAnimation) {
            this.showSelectionViews(game);
            this.makeCardsInteractive(game)
        } else {
            this.needsToShowMakeViews = true;
        }

        if (game.show_rope) {
            this.showRope();
        }

        // put arrows and spell being cast above other refreshed sprites
        if (this.spellBeingCastSprite) {
            this.app.stage.removeChild(this.spellBeingCastSprite);
            this.app.stage.addChild(this.spellBeingCastSprite);
        }
        for (let arrow of this.arrows) {
            this.app.stage.removeChild(arrow);
            this.app.stage.addChild(arrow);
        }
        if (message["move_type"] == "END_TURN") {
            this.showChangeTurnAnimation(game)
        }
    }

    showAttack(game) {
        if (game.stack.length > 0 && game.stack[game.stack.length-1][0].move_type == "ATTACK") {
            var attack = game.stack[game.stack.length-1][0];
            var attacking_id = attack["card"];
            var attackingCardSprite = null;
            for (let sprite of this.app.stage.children) {
                if (sprite.card && sprite.card.id == attacking_id && !this.spellStackSprites.includes(sprite)) {
                    attackingCardSprite = sprite;
                }
            } 

            if (attackingCardSprite) {
                var defending_id = null
                var defendingCardSprite = null;
                if (attack["defending_card"]) {
                    defending_id = attack["defending_card"];
                    for (let sprite of this.app.stage.children) {
                        if (sprite.card && sprite.card.id == defending_id) {
                            defendingCardSprite = sprite;
                        }
                    } 
                }

                if(defending_id && defendingCardSprite) {
                    this.showArrow(
                        attackingCardSprite,
                        defendingCardSprite, 
                        );                    
                } else {
                    let avatar = this.opponentAvatar;
                    if (this.activePlayer(game).username != this.opponent(game).username) {                        
                        avatar = this.playerAvatar;
                    }
                    this.showArrow(
                        attackingCardSprite,
                        avatar,
                        {x:avatar.width/4, y: avatar.height/2} 
                        );                                        
                }
            }
        }        
    }

    showChangeTurnAnimation(game) {
        const container = new PIXI.Container();
        this.app.stage.addChild(container);
        const background = new PIXI.Sprite.from(PIXI.Texture.WHITE);
        var modalWidth = this.opponentAvatar.width;
        var modalHeight = this.inPlay.height * 2 + padding;
        this.roundRectangle(background)
        background.width = modalWidth;
        background.height = modalHeight;
        container.position.x = this.opponentAvatar.position.x;
        container.position.y = this.opponentAvatar.position.y + this.opponentAvatar.height + padding;
        background.tint = 0x000000;
        background.alpha = .7;
        container.addChild(background);

        let options = this.textOptions();
        options.wordWrapWidth = 400
        options.fontSize = 32;
        options.fill = 0xFFFFFF;
        options.align = "middle";
        let name = new PIXI.Text(this.activePlayer(game).username + "'s turn", options);
        name.position.x = modalWidth/2 - name.width/2;
        name.position.y = 80
        container.addChild(name);

        var i = 1;                  

        function myLoop() {        
          setTimeout(function() {   
            container.alpha -= .01
            i++;                    
            if (container.alpha > 0) {          
              myLoop();            
            }                     
          }, 40-i)
        }

        myLoop();             
    }

    roundRectangle(sprite) {
        var graphics = new PIXI.Graphics();
        graphics.beginFill(0x000000);
        graphics.drawRoundedRect(
            0,
            0,
            sprite.width,
            sprite.height,
            1
        );
        graphics.endFill();
        sprite.mask = graphics;
        sprite.addChild(graphics)
    }

    clearArrows() {
        if (this.arrows && this.arrows.length) {
            for (let a of this.arrows) {
                this.app.stage.removeChild(a);
            }
            this.arrows = []
        }        
    }

    showArrow(fromSprite, toSprite, adjustment={'x':0, 'y': 0}){
        let cpXY1 = [30,0];
        let cpXY2 = [200,100];
        let toXY = [toSprite.position.x - fromSprite.position.x + adjustment.x, toSprite.position.y - fromSprite.position.y + adjustment.y];
        let fromXY = [fromSprite.position.x, fromSprite.position.y];
        let toXYArc = [toSprite.position.x-fromSprite.position.x+toSprite.width/4,
                        toSprite.position.y-fromSprite.position.y+toSprite.height/2];
        let toXYArrow = [toSprite.position.x+toSprite.width/4,
                        toSprite.position.y+toSprite.height/2 - 10];

        const bezierArrow = new PIXI.Graphics();
        bezierArrow.tint = 0xff0000;
        this.arrows.push(bezierArrow);
        this.app.stage.addChild(bezierArrow); 
        const normal = [
            - (toXY[1] - cpXY2[1]),
            toXY[0] - cpXY2[0],
        ]
        const l = Math.sqrt(normal[0] ** 2 + normal[1] ** 2);
        normal[0] /= l;
        normal[1] /= l;
        
        var arrowSize = 10;
        const tangent = [
            -normal[1] * arrowSize,
            normal[0] * arrowSize
        ]

        normal[0] *= arrowSize;
        normal[1] *= arrowSize;
        
        bezierArrow.position.set(fromXY[0], fromXY[1], 0);
        
        bezierArrow
            .lineStyle(4, 0xffffff, 1)
            .bezierCurveTo(cpXY1[0],cpXY1[1],cpXY2[0],cpXY2[1],toXY[0],toXY[1])
            .lineStyle(1, 0xffffff, 1)
            .beginFill(0xFF0000, 1)
            .moveTo(toXY[0] + normal[0] + tangent[0], toXY[1] + normal[1] + tangent[1])
            .lineTo(toXY[0] , toXY[1] )
            .lineTo(toXY[0] - normal[0] + tangent[0], toXY[1] - normal[1] + tangent[1])
            .lineTo(toXY[0] + normal[0] + tangent[0]-1, toXY[1] + normal[1] + tangent[1])
            .endFill();
        
        var sprite = new PIXI.Sprite(this.app.renderer.generateTexture(bezierArrow,{resolution:2,region:2}))
        bezierArrow.filters = glowAndShadowFilters()

        return sprite;
    }

    makeCardsInteractive(game) {
        if (!this.isPlaying(game)) {
            return;
        }

        // hax: prevents spurious onMousover events from firing during rendering all the cards
        setTimeout(() => { 
            for (let sprite of this.app.stage.children) {
                if (sprite.card) {
                    sprite.interactive = true;
                }
            }
            if (this.selectCardInnerContainer) {
                for (let sprite of this.selectCardInnerContainer.children) {
                    if (sprite.card) {
                        sprite.interactive = true;
                    }
                }                
            }

        }, 200);                
    }

    showSelectionViews(game) {
        if (this.selectCardContainer) {
            this.selectCardContainer.parent.removeChild(this.selectCardContainer);
            this.selectCardContainer = null;
            this.selectCardInnerContainer = null;
        }
        if (this.thisPlayer(game).card_choice_info.cards.length && this.thisPlayer(game).card_choice_info.choice_type == "make") {
            this.showMakeView(game);
        } else if (this.thisPlayer(game).card_choice_info.cards.length && this.thisPlayer(game).card_choice_info.choice_type == "make_from_deck") {
            this.showMakeFromDeckView(game);
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

    showMakeFromDeckView(game) {
        var self = this;
        this.showSelectCardView(game, "Make from Deck", function(card) {
            self.gameRoom.sendPlayMoveEvent("FETCH_CARD", {"card":card.id});
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
        this.app.stage.addChild(container);
        this.selectCardContainer = container;

        const background = new PIXI.Sprite.from(PIXI.Texture.WHITE);
        background.width = appWidth;
        background.height = appHeight;
        background.tint = 0x000000;
        background.alpha = .7;
        container.addChild(background);

        let options = this.textOptions();
        options.wordWrapWidth = 500
        options.fontSize = 24;
        options.fill = 0xFFFFFF;
        options.align = "middle";
        let name = new PIXI.Text(title, options);
        name.position.x = appWidth/2 - name.width/2;
        name.position.y = 80
        container.addChild(name);


        const cardContainer = new PIXI.Container();
        this.selectCardInnerContainer = cardContainer
        cardContainer.tint = 0xFF00FF;
        cardContainer.position.x = appWidth/2 - cardWidth*1.5;
        if (showFullDeck) {
            cardContainer.position.x = cardWidth;            
        }

        var cards = this.thisPlayer(game).card_choice_info["cards"];

        // make global effect has 5 cards
        if (cards.length == 5) {
            cardContainer.position.x = appWidth/2 - cardWidth*2.5;            
        }
        cardContainer.position.y = 140;
        container.addChild(cardContainer);

        for (let i=0;i<cards.length;i++) {
            this.addSelectViewCard(game, cards[i], cardContainer, card_on_click, i)
        }

    }


    addSelectViewCard(game, card, cardContainer, card_on_click, index) {
        let cardSprite = this.cardSprite(game, card, this.userOrP1(game), false);
        cardSprite.position.x = (cardWidth + 5) *  (index % 8) + cardWidth/2;
        cardSprite.position.y = cardHeight/2 + (cardHeight + 5) * Math.floor(index / 8);            
        cardContainer.addChild(cardSprite);
        var self = this;
        cardSprite
            .on('click',        function (e) {
                this.onMouseout(cardSprite, self);
                card_on_click(card);
            })

    }

    baseCardSprite(card, cardTexture, game) { 
        let cardSprite = new PIXI.Sprite.from(cardTexture);
        cardSprite.card = card;
        if (this.isPlaying(game)) {
            cardSprite.buttonMode = true;  // hand cursor
        }
        return cardSprite;
    }

    cardSpriteInPlay(game, card, player, dont_attach_listeners) {
        var cardTexture = this.cardTextureInPlay;
        for (let a of card.abilities) {
            if (a.name == "Guard") {
                cardTexture = this.cardTextureInPlayGuard;
            }                    
        }

        var cardSprite = this.baseCardSprite(card, cardTexture, game);
        let imageSprite = PIXI.Sprite.from(this.fullImagePath(card)+"?inplay");
        cardSprite.addChild(imageSprite);
        this.ellipsifyImageSprite(imageSprite, card, 38, 82)

        if (card.name == "Mana Battery") {
            var currentBatteryMana = 0;
            for (let effect of card.effects) {
                if (effect.name == "store_mana") {
                    currentBatteryMana = effect.counters;
                }
            }
            var gems = this.manaGems(3, currentBatteryMana);
            gems.position.x = -gems.width/2;
            gems.position.y = cardHeight/2 - 7 - gems.height;
            cardSprite.addChild(gems);
        }


        let options = this.textOptions();
        
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

        if (card.card_type == "Mob") {
            this.addStats(card, cardSprite, player, -8, -14, cardWidth-16, cardHeight, false)
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

        this.setCardFilters(card, cardSprite);

        if (dont_attach_listeners) {
            return cardSprite;
        }

        this.setCardDragListeners(card, cardSprite, game);
        this.setCardMouseoverListeners(cardSprite);

        this.setCardAnchors(cardSprite);

         if (cardSprite.card.damage_to_show > 0) {
           this.damageSprite(imageSprite, cardSprite.card.id + '_pic', cardSprite.card.damage_to_show);
           this.damageSprite(cardSprite, cardSprite.card.id, cardSprite.card.damage_to_show);
        }

        return cardSprite;
    }

    fullImagePath(card) {
        let imageName = card.image;
        if (!imageName) {
            imageName = "uncertainty.svg"
        }
        return 'http://127.0.0.1:8000' + '/static/images/card-art/' + imageName;
    }

    updateHand(game, index=0) {
        for (let i=index;i<this.thisPlayer(game).hand.length;i++) {
            const card = this.thisPlayer(game).hand[i];
            this.addHandCard(game, card, i)
        }
    }

    addHandCard(game, card, index) {
        let sprite = this.cardSprite(game, card, this.userOrP1(game), false);
        sprite.position.x = (cardWidth)*index + cardWidth/2 + padding;
        sprite.position.y = this.handContainer.position.y + cardHeight/2;
        this.app.stage.addChild(sprite);                
        if (this.thisPlayer(game).card_info_to_target && card.id == this.thisPlayer(game).card_info_to_target.card_id) {
            sprite.alpha = .3;
        }
    }

    ellipsifyImageSprite(imageSprite, card, width, height) {
        if (card.image && card.image.endsWith(".jpg")) {
            // hax
            width *= 3.4;
            height *= 3.4;
        }
        var bg = this.ellipseBackground(width, height, imageSprite.width);
        imageSprite.mask = bg;
        imageSprite.addChild(bg);        
        return imageSprite
    }

    ellipseBackground(width, height, imageSpriteWidth) {
        const ellipseW = width;
        const ellipseH = height;
        const background = new PIXI.Graphics();
        background.beginFill(0xffffff, 1);
        background.drawEllipse(0, 0, ellipseW, ellipseH - height/3)
        background.endFill();
        const sprite = new PIXI.Sprite.from(PIXI.Texture.WHITE);
        sprite.mask = background;
        sprite.addChild(background);
        return background;
    }

    onMouseover(cardSprite) {
        this.hovering = true;
        this.hoverTimeout = setTimeout(() => { 
            if (this.hovering) {
                this.app.stage.removeChild(this.hoverCards);
                this.hovering = false;
                const card = cardSprite.card
                const loaderID = card.name+"?large"
                const loaderURL = this.fullImagePath(card)+"?large";
                if (!PIXI.utils.TextureCache[loaderURL]) {
                    this.app.loader.reset()
                    this.loadCardImage(
                        card.card_type,
                        loaderID,
                        loaderURL,
                        .9,
                    );
                    this.app.loader.load(() => {
                        this.addHoverCard(cardSprite);
                    });                     
                } else {
                    this.addHoverCard(cardSprite);
                }
            }
        }, 300);

    }

    addHoverCard(cardSprite) {
        let sprite = this.cardSprite(this.game, cardSprite.card, this.thisPlayer(this.game), false, true);
        sprite.position.x = cardSprite.position.x + cardWidth/2;
        sprite.position.y = cardSprite.position.y - cardHeight*1.5;
        if (sprite.position.y < cardHeight) {
            sprite.position.y = cardHeight;
            sprite.position.x = cardSprite.position.x + cardWidth*1.5 + 10;
        }
        if (sprite.position.x >= 677) {
            sprite.position.x = cardSprite.position.x - cardWidth;
        }
        this.app.stage.addChild(sprite)
        this.hoverCards = sprite;        
    }

    cardSprite(game, card, player, dont_attach_listeners, useLargeSize) {
        var cardTexture = (useLargeSize ? this.cardLargeTexture : this.cardTexture); 
        var cardSprite = this.baseCardSprite(card, cardTexture, game);

        cardSprite.card = card;
        cardSprite.buttonMode = true;  // hand cursor
        let loaderID = card.name;
        if (useLargeSize) {
            loaderID += '?large';
        }
        let imageSprite = PIXI.Sprite.from(loaderID);
        let spriteWidth = imageSprite.width
        const bgSprite = new PIXI.Sprite.from(PIXI.Texture.WHITE);
        bgSprite.tint = 0x000000;
        bgSprite.width = 128;
        bgSprite.height = 128;
        if (useLargeSize) {
            bgSprite.width = 256;
            bgSprite.height = 256;            
        }

        const imageContainer = new PIXI.Container();
        imageContainer.addChild(bgSprite);
        imageContainer.addChild(imageSprite);
        imageSprite.position.x = bgSprite.width/2 - imageSprite.width/2;
        imageSprite.position.y = bgSprite.height/2 - imageSprite.height/2;

        var texture = this.app.renderer.generateTexture(imageContainer)
        imageSprite = new PIXI.Sprite(texture);

        if (card.card_type == "Mob" || card.card_type == "Artifact") {
            if (useLargeSize) {
                imageSprite.position.y = -60;
                this.ellipsifyImageSprite(imageSprite, card, 48, 88)        
            } else {
                imageSprite.position.y = -30;
                this.ellipsifyImageSprite(imageSprite, card, 24, 44)        
            }
        } else if (card.card_type == "Spell") {
            if (useLargeSize) {
                imageSprite.position.y = -56;
                this.rectanglifyImageSprite(imageSprite, cardWidth*2-6, 110)                                    
            } else {
                imageSprite.position.y = -26;
                this.rectanglifyImageSprite(imageSprite,cardWidth-6, 54)                                    
            }
        }
        cardSprite.addChild(imageSprite);

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
        nameBackground.tint = 0x000000;
        nameBackground.width = cw - 6;
        nameBackground.height = 12;
        nameBackground.alpha = .7;
        nameBackground.position.x = aFX + 8;
        nameBackground.position.y = aFY + 2;
        let nameOptions = this.textOptions();
        if (card.name.length >= 22) {
            nameOptions.fontSize --;
        }
        if (useLargeSize) {
            nameOptions.fontSize = 12;
            nameOptions.wordWrapWidth = 142;
            nameBackground.position.x -= 4
            nameBackground.position.y += 19
            nameBackground.height = 16;
        }
        cardSprite.addChild(nameBackground);

        nameOptions.fill = 0xffffff;
        let name = new PIXI.Text(card.name, nameOptions);
        cardSprite.addChild(name);
        name.position.x = nameBackground.position.x;
        name.position.y = nameBackground.position.y;

        const descriptionBackground = new PIXI.Sprite.from(PIXI.Texture.WHITE);
        descriptionBackground.tint = 0xffffff;
        descriptionBackground.alpha = .8;
        descriptionBackground.width = cw - 6;
        descriptionBackground.height = ch/2 - 10;
        descriptionBackground.position.y = descriptionBackground.height/2;
        cardSprite.addChild(descriptionBackground);


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

            imageSprite = new PIXI.Sprite.from(PIXI.Texture.from('/static/images/card-art/' + "amethyst.svg"));
            imageSprite.tint = 0x0000ff;
            imageSprite.height = 15;
            imageSprite.width = 15;
            if (useLargeSize) {
                imageSprite.height = 25;
                imageSprite.width = 25;
            }
            imageSprite.position.x = costX;
            imageSprite.position.y = costY;
            cardSprite.addChild(imageSprite);

            var ptOptions = this.textOptions()
            ptOptions.stroke = 0x000000;
            ptOptions.strokeThickness = 2;
            ptOptions.fill = 0xffffff;
            ptOptions.fontSize = 12;
            if (useLargeSize) {
                ptOptions.fontSize = 17;
            }
            let cost = new PIXI.Text(card.cost, ptOptions);
            cost.position.x = costX;
            cost.position.y = costY;
            cardSprite.addChild(cost);

        }            

        let descriptionOptions = this.textOptions();
        if (useLargeSize) {
            descriptionOptions.wordWrapWidth = 142;
            descriptionOptions.fontSize = 12;
        }

        if (card.description && card.description.length > 120) {
            descriptionOptions.fontSize = 6; 
        }


        var abilitiesText = "";
        var color = 0xAAAAAA;
        for (let a of card.abilities) {
            if (!["Starts in Play", "die_to_top_deck", "discard_random_to_deck", "multi_mob_attack", "Weapon"].includes(a.descriptive_id)) {
                if (a.description) {
                    abilitiesText += a.description;
                    color = 0x000000;
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

        for (let c of card.tokens) {
           if (c.set_can_act == false) {
            if (abilitiesText.length) {
                abilitiesText += ", ";
            }
            abilitiesText += "Can't Attack";
           }
        }

        var baseDescription =  card.description;
        if (card.name == "Tame Shop Demon") {
           baseDescription = card.effects[0].card_descriptions[card.level];
        }
        if (card.name == "Rolling Thunder") {
           var damage = card.effects[0].amount;
           baseDescription = `Deal ${damage} damage. Improves when cast.`;
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
            if ((card.card_type == "Mob" && activatedEffects.length == 0) ||
                card.card_type != "Mob" || card.turn_played == -1) {
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
                addedDescription = new PIXI.Text(d, this.textOptions());
                addedDescription.position.x = name.position.x;
                addedDescription.position.y = description.position.y + description.height;
                cardSprite.addChild(description);
            }
        }

        if (useLargeSize) {
            this.showAbilityPanels(cardSprite, card, cw, ch);
        }


        if (card.card_type == "Mob") {
            this.addStats(card, cardSprite, player, aFX, aFY, cw, ch, useLargeSize)

        } else if (card.turn_played == -1) {
            var typeX = aFX + cw/4 - 33;
            var typeY = aFY + ch/2 - 5;
            if (useLargeSize) {
                typeX -= 20;
                typeY += 20;
            }
            var typeBG = new PIXI.Graphics();
            typeBG.beginFill(0x444444);
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

            let typeOptions = this.textOptions();
            typeOptions.fill = 0xffffff;

            var typeName = card.card_type;
            for (let a of card.abilities) {
                if ("Weapon" == a.descriptive_id) {
                    typeName = a.descriptive_id;
                }
            }

            let type = new PIXI.Text(typeName, typeOptions);
            type.position.x = typeX + 20;
            type.position.y = typeY + 6
            cardSprite.addChild(type);
        }

        if (attackEffect) {
            var powerX = aFX - 24;
            var powerY = aFY + ch/2;
            if (useLargeSize) {
                powerX -= 44;
                powerY += 20;
            }
            var countersX = powerX + cw - 16;
            var attackEffectOptions = this.textOptions() 
            if (attackEffect.name == "make_random_townie") {
                this.addCircledLabel(powerX, powerY, cardSprite, attackEffectOptions, attackEffect.counters);
                this.addCircledLabel(countersX, powerY, cardSprite, attackEffectOptions, attackEffect.amount);
            } else {
                this.addCircledLabel(powerX, powerY, cardSprite, attackEffectOptions, attackEffect.power);
                this.addCircledLabel(countersX, powerY, cardSprite, attackEffectOptions, attackEffect.counters);
            }
        }

        this.setCardFilters(card, cardSprite);

        if (dont_attach_listeners) {
            return cardSprite;
        }

        this.setCardDragListeners(card, cardSprite, game);

        if (!useLargeSize) {
            this.setCardMouseoverListeners(cardSprite);
        }

        this.setCardAnchors(cardSprite);

        return cardSprite;
    }

    setCardFilters(card, cardSprite) {
        var filters = []
        if (!card.can_be_clicked) {
            filters.push(cantBeClickedFilter());                        
        }
        if (card.shielded && card.turn_played > -1) {
            filters.push(new GlowFilter({ outerStrength: 0, innerStrength: 3, color: 0xFFFFFF}));                        
        }
        if (card.abilities.length > 0 && card.abilities[0].descriptive_id == "Lurker" && card.abilities[0].enabled && card.turn_played > -1) {
            filters.push(new GlowFilter({ outerStrength: 0, innerStrength: 3, color: 0x000000}));                        
        }

        cardSprite.filters = filters;

    }

    setCardDragListeners(card, cardSprite, game) {
        if (card.can_be_clicked) {
            if (this.thisPlayer(game).card_info_to_target["card_id"]) {
                var self = this;
                cardSprite.on('click',        function (e) {self.gameRoom.sendPlayMoveEvent("SELECT_MOB", {"card":card.id});})
            } else {
                var self = this;
                cardSprite
                    .on('mousedown',        function (e) {onDragStart(e, this, self, game)})
                    .on('touchstart',       function (e) {onDragStart(e, this, self, game)})
                    .on('mouseup',          function ()  {onDragEnd(this, self)})
                    .on('mouseupoutside',   function ()  {onDragEnd(this, self)})
                    .on('touchend',         function ()  {onDragEnd(this, self)})
                    .on('touchendoutside',  function ()  {onDragEnd(this, self)})
                    .on('mousemove',        function ()  {onDragMove(this, self, self.bump)})
                    .on('touchmove',        function ()  {onDragMove(this, self, self.bump)})
            }
        } else { 
        }
    }

    setCardMouseoverListeners(cardSprite) {
        var self = this;
        cardSprite.onMouseover = function ()  {self.onMouseover(cardSprite)};
        cardSprite.onMouseout = function ()  {self.onMouseout(cardSprite)};
        cardSprite
            .on('mouseover',        cardSprite.onMouseover)
            .on('mouseout',        cardSprite.onMouseout)
    }

    setCardAnchors(cardSprite) {
        cardSprite.anchor.set(.5);
        for (let child of cardSprite.children) {
            // graphics we draw don't have an anchor, like the circle for costBackground
            if (child.anchor) {
                child.anchor.set(.5);                
            }
        }        
    }

    onMouseout(cardSprite) {
        clearTimeout(this.hoverTimeout);
        this.hovering = false
        this.app.stage.removeChild(this.hoverCards);
    }

    imagePath(card) {
        let imageName = card.image;
        if (!imageName) {
            imageName = "uncertainty.svg"
        }
        return '/static/images/card-art/' + imageName;
    }

    textOptions() {
        return {fontFamily : 'Helvetica', fontSize: 8, fill : 0x00000, wordWrap: true, wordWrapWidth: 75};
    }

    addStats(card, cardSprite, player, aFX, aFY, cw, ch, useLargeSize) {
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

        var ptOptions = this.textOptions()

        let centerOfEllipse = 16

        var powerX = aFX - cw/2 + centerOfEllipse;
        var powerY = aFY + ch/2;
        var defenseX = aFX + cw/2;

        if (useLargeSize) {
            powerY += 20;
            powerX -= 5;
            defenseX -= 5;
        }

        let imageSprite = new PIXI.Sprite.from(PIXI.Texture.from('/static/images/card-art/' + "piercing-sword.svg"));
        imageSprite.tint = 0xffff00;
        imageSprite.height = 17;
        imageSprite.width = 17;
        imageSprite.position.x = powerX;
        imageSprite.position.y = powerY;
        cardSprite.addChild(imageSprite);

        this.addCircledLabel(powerX, powerY, cardSprite, ptOptions, cardPower, 0xffff00);


        imageSprite = new PIXI.Sprite.from(PIXI.Texture.from('/static/images/card-art/' + "hearts.svg"));
        imageSprite.tint = 0xff0000;
        imageSprite.height = 17;
        imageSprite.width = 17;
        imageSprite.position.x = defenseX;
        imageSprite.position.y = powerY;
        cardSprite.addChild(imageSprite);


        ptOptions.stroke = 0x000000;
        ptOptions.strokeThickness = 2;
        ptOptions.fill = 0xffffff;
        ptOptions.fontSize = 9;
        let defense = new PIXI.Text(cardToughness, ptOptions);
        defense.position.x = defenseX;
        defense.position.y = powerY;
        cardSprite.addChild(defense);        

        let cardId = new PIXI.Text("id: " + card.id, ptOptions);
        cardId.position.x = defenseX - cardWidth/4 - 5;
        cardId.position.y = powerY;
        cardSprite.addChild(cardId);        
    }

    addCircledLabel(costX, costY, cardSprite, options, value, fillColor) {
        options.stroke = 0x000000;
        options.strokeThickness = 2;
        options.fill = 0xffffff;
        options.fontSize = 11;

        var circle = this.circleBackground(costX, costY);
        circle.tint = fillColor
        cardSprite.addChild(circle);
        let cost = new PIXI.Text(value, options);
        cost.position.x = -4;
        cost.position.y = -8;
        circle.addChild(cost);
    }

    circleBackground(x, y) {
        const circleRadius = 7;
        const background = new PIXI.Graphics();
        
        background.beginFill(0x000000, 1);
        background.lineStyle(2, 0x000000, 1); 
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

    rectanglifyImageSprite(imageSprite, width, height) {
        var bg = this.rectangleBackground(width, height);
        imageSprite.mask = bg;
        imageSprite.addChild(bg);        
    }

    rectangleBackground(width, height) {
        const rectangleW = width;
        const rectangleH = height;
        const background = new PIXI.Graphics();
        background.beginFill(0xffffff, 1);
        background.drawRect(-rectangleW/2, -rectangleH/2, rectangleW, rectangleH);
        background.endFill();
        const sprite = new PIXI.Sprite.from(PIXI.Texture.WHITE);
        sprite.mask = background;
        sprite.addChild(background);
        return background;
    }

    showAbilityPanels(cardSprite, card, cw, ch) {
        var options = this.textOptions();
        options.fontSize = 10;
        options.wordWrapWidth = cw - 8;

        const topBG = new PIXI.Sprite.from(PIXI.Texture.WHITE);
        cardSprite.addChild(topBG);
        topBG.tint = 0xffff00;
        const textContainer = new PIXI.Container();
        cardSprite.addChild(textContainer);
        var yPosition = 0;
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
            if (a.name == "Superfast") {
                abilityText.text = "Superfast - Superfast mobs may be played and attack as instants.";
            }                    
            if (a.name == "Ambush") {
                abilityText.text = "Ambush - Ambush mobs may attack other mobs the turn they come into play.";
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
                abilityText.text = "Keep - Cards with Keep can be Kept by races (dwarves) that discard their hand each turn.";
            }                    
            if (abilityText.text) {
                abilityText.position.x -= cw/2 - 4;
                abilityText.position.y = yPosition - ch/2 + 2;
                yPosition += abilityText.height + 10;
                textContainer.addChild(abilityText);
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

    removeCardsFromStage(game) {
        if (this.thisPlayer(game) && this.opponent(game)) {
            let spritesToRemove = [];
            for (let sprite of this.app.stage.children) {
                if (sprite.card && sprite != this.spellBeingCastSprite) {
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

    showCardThatWasCast(card, game, player, message) {
      var godray = new GodrayFilter();
      var incrementGodrayTime = () => {
        godray.time += this.app.ticker.elapsedMS / 1000;
      }
      let sprite = this.cardSprite(game, card, player, false);
      sprite.scale.set(1.5);
      sprite.position.x = 100;
      sprite.position.y = this.inPlay.position.y + padding;
      this.spellBeingCastSprite = sprite;
      this.app.stage.addChild(sprite)
      this.showArrowsForSpell(game, sprite, message, card);
      this.app.ticker.add(incrementGodrayTime)
      this.app.stage.filters = [godray];
      this.isShowingCastAnimation = true;
      setTimeout(() => { 
            this.clearArrows()
            this.isShowingCastAnimation = false;
            this.app.stage.filters = []; 
            this.app.ticker.remove(incrementGodrayTime)
            this.app.stage.removeChild(sprite)
            if (this.needsToShowMakeViews) {
                this.needsToShowMakeViews = false;
                this.showSelectionViews(this.game);
                this.makeCardsInteractive(game)
            }
            this.spellBeingCastSprite = null;
        }, 1000);

    }

    showSpellStack(game) {
        if (!this.spellStackSprites) {
            this.spellStackSprites = []
        }
        var index = -1;
        for (let spell of game.stack) {
            index++;
            var playerName = spell[0].username;
            var player = null;
            if (this.opponent(game).username == playerName) {
                player = this.opponent(game);
            } else {
                player = this.thisPlayer(game);
            }

            let sprite = this.cardSprite(game, spell[1], player, false);
            if (spell[0].move_type == "ATTACK") {
                continue;
            }
            sprite.scale.set(1.5);
            sprite.position.x = 100 + 20*index;
            sprite.position.y = this.inPlay.position.y + padding + 40*index;
            this.app.stage.addChild(sprite)
            this.spellStackSprites.push(sprite)
            var card = spell[1]
            var spellMessage = spell[0]
            this.showArrowsForSpell(game, sprite, spellMessage, card);
        }
    }

    showArrowsForSpell(game, sprite, spellMessage, card) {
        if (spellMessage["effect_targets"] && spellMessage["effect_targets"][0].target_type == "player") {
            if (spellMessage["effect_targets"][0].id == this.opponent(game).username) {
               this.showArrow(
                    sprite, 
                    this.opponentAvatar,
                    {x:this.opponentAvatar.width/4, y: this.opponentAvatar.height/2});
            } else {
               this.showArrow(
                    sprite, 
                    this.playerAvatar,
                    {x:this.playerAvatar.width/4, y: this.playerAvatar.height/2});

            }
        } else if (spellMessage["effect_targets"] && ["mob", "artifact"].includes(spellMessage["effect_targets"][0].target_type)) {
            var targetID = spellMessage["effect_targets"][0].id;
            var targetCardSprite = null;
            for (let sprite of this.app.stage.children) {
                if (sprite.card && sprite.card.id == targetID) {
                    targetCardSprite = sprite;
                }
            } 
            if(targetCardSprite && sprite != targetCardSprite) {
                this.showArrow(sprite, targetCardSprite);
            }
        }

        // hax: impale, inner fire, other 2 effect cards
        if (spellMessage["effect_targets"] && spellMessage["effect_targets"].length == 2 && spellMessage["effect_targets"][1].target_type == "player" && spellMessage["effect_targets"][1].id == this.opponent(game).username) {
            let avatar = this.playerAvatar;
            if (spellMessage["effect_targets"][1].id == this.opponent(game).username) {
                avatar = this.opponentAvatar;
            }
            this.showArrow(
                sprite, avatar,
                {x:avatar.width/4, y:avatar.height/2} 
                );

        }
    }

    hideSpellStack() {
        for (let sprite of this.spellStackSprites) {
            this.app.stage.removeChild(sprite)
        }
        this.spellStackSprites = null
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

    activePlayerHasMoves(game) {
        for (let sprite of this.app.stage.children) {
            if(sprite.card && sprite.card.can_be_clicked) {
                return true;
            }
        }        
        if (game.players[0].can_be_clicked) {
            return true;
        }
        if (game.players[1].can_be_clicked) {
            return true;
        }
        return false;
    }

    renderEndTurnButton(game, message) {
        if (this.turnLabel) {
            this.buttonMenu.removeChild(this.turnLabel)
        }
        if (this.endTurnButton) {
            this.buttonMenu.removeChild(this.endTurnButton)
        }

        const b = new PIXI.Sprite.from(this.newGameButtonTexture);
        b.position.x = 23;
        b.position.y = 17;
        if (this.isPlaying(game)) {
            b.buttonMode = true;
            b.interactive = true;
        }

        var clickFunction = () => {
            if (game.stack.length > 0 && game.stack[game.stack.length-1][0].move_type == "ATTACK") {
                this.gameRoom.passForAttack(message)
            } else if (game.stack.length > 0) {
                this.gameRoom.passForSpellResolution(message)
            } else {
                this.gameRoom.endTurn()
            }
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

        var title = "End Turn";
        let textFillColor = 0xffffff;
        if (this.isActivePlayer(game)) {
            if (!this.activePlayerHasMoves(game) || game.stack.length > 0) {
                b.tint = 0xff0000;
            } else {
                b.tint = 0xff7b7b;
            }
        } else {
            title = "Waiting...";
            textFillColor = 0xAAAAAA;
            b.interactive = false;
        }
        var positionX = 27;

        if (game.stack.length > 0) {
            if (this.isActivePlayer(game)) {
                title = "OK";
                if (game.stack[game.stack.length-1][0].move_type == "ATTACK") {
                    title = "OK"
                }
                positionX = 45;
            } else {    
                title = "Waiting...";
                positionX = 28;

            }
        }
        let text = new PIXI.Text(title, {fontFamily : 'Arial', fontSize: 12, fill : textFillColor});
        text.position.x = positionX;
        text.position.y = 14;
        b.addChild(text);


        this.endTurnButton = b;
        this.buttonMenu.addChild(this.endTurnButton)

        let turnText = new PIXI.Text(`${this.thisPlayer(game).username} is Active\n(Turn ${game.turn})`, {fontFamily : 'Arial', fontSize: 12, fill : textFillColor, align: "center"});
        turnText.position.x = this.buttonMenu.width/2;
        turnText.position.y = b.position.y + 60 + padding;
        turnText.anchor.set(0.5, 0.5);
        this.turnLabel = turnText;
        this.buttonMenu.addChild(turnText);

    }

    isActivePlayer(game) {
        return (game.actor_turn % 2 == 0 && this.userOrP1(game).username == game.players[0].username
                || game.actor_turn % 2 == 1 && this.userOrP1(game).username == game.players[1].username)
    }

    activePlayer(game) {
        if (game.actor_turn % 2 == 0) {
            return game.players[0];
        }
        return game.players[1];
    }


    updatePlayer(game, player, avatarSprite) {
        var props = {fontFamily : 'Arial', fontSize: 12, fill : 0x00000};
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

        let hand = hp;
        if (player == this.opponent(game)) {
            hand = new PIXI.Text("Hand: " + player.hand.length, props);
            hand.position.x = padding/2 + avatar.position.x + avatar.width;
            hand.position.y = hp.height + hp.position.y;
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

        let mana = new PIXI.Text("Mana", props);
        mana.position.x = padding/2 + avatar.position.x + avatar.width;
        mana.position.y = playedPile.height + playedPile.position.y + 8;
        avatarSprite.addChild(mana);

        var manaGems = this.manaGems(player.max_mana, player.mana);
        manaGems.position.x = mana.position.x;
        manaGems.position.y = mana.position.y + mana.height;        
        avatarSprite.addChild(manaGems);

        if (!player.can_be_clicked) {
            avatarSprite.filters = [cantBeClickedFilter()];                        
            avatarSprite.on('click', function (e) {})
            avatarSprite.interactive = false;
            avatarSprite.buttonMode = true;
       } else {
            avatarSprite.interactive = true;
            avatarSprite.buttonMode = true;
            avatarSprite.filters = [];                                   
            if (this.activePlayer(game).card_info_to_target["card_id"]) {
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
           this.damageSprite(avatarSprite, player.username, player.damage_to_show);
        }
    }

    damageSprite(spriteToDamage, spriteId, damage_to_show) {
          setTimeout(() => { 
                this.spriteDamageCounts[spriteId] += 1;
                if (!this.spriteDamageCounts[spriteId] && this.spriteDamageCounts[spriteId] != 0) {
                    this.spriteDamageCounts[spriteId] = 0                    
                    var godray = new GlowFilter({ distance: 8,  outerStrength: 8, innerStrength: 2 , color: 0xFF0000});
                    spriteToDamage.filters = [godray];
                    this.damageSprite(spriteToDamage, spriteId, damage_to_show);                    
                } else if (this.spriteDamageCounts[spriteId] >= damage_to_show*3) {
                    this.spriteDamageCounts[spriteId] = 0
                    spriteToDamage.filters = []; 
                } else {
                    var godray = new GlowFilter({ distance: 8,  outerStrength: 8, innerStrength: 2 , color: 0xFF0000});
                    spriteToDamage.filters = [godray];
                    setTimeout(() => { 
                        spriteToDamage.filters = [];
                    }, 100); 
                    this.spriteDamageCounts[spriteId] += 1
                    this.damageSprite(spriteToDamage, spriteId, damage_to_show);                    
                }
            }, 200);   
    }

    manaString(maxMana, currentMana) {
        var manaString = ""
        for (var i=0;i<currentMana;i++) {
            manaString += "✦"
        }
        for (var i=0;i<maxMana-currentMana;i++) {
            manaString += "✧"
        }
        return manaString
    }

    manaGems(maxMana, currentMana) {
        const background = new PIXI.Container();
        var xPixels = 0;
        var gemSize = 12;
        for (var i=0;i<currentMana;i++) {
            let imageSprite = new PIXI.Sprite.from(PIXI.Texture.from('/static/images/card-art/' + "amethyst.svg"));
            imageSprite.tint = 0x0000ff;
            imageSprite.height = gemSize;
            imageSprite.width = gemSize;
            imageSprite.position.x = xPixels;
            imageSprite.position.y = 0;
            background.addChild(imageSprite)
            xPixels += gemSize + 1;
        }
        for (var i=0;i<maxMana-currentMana;i++) {
            let imageSprite = new PIXI.Sprite.from(PIXI.Texture.from('/static/images/card-art/' + "amethyst.svg"));
            imageSprite.tint = 0x0000ff;
            imageSprite.height = gemSize;
            imageSprite.width = gemSize;
            imageSprite.position.x = xPixels;
            imageSprite.position.y = 0;
            imageSprite.alpha = .3
            background.addChild(imageSprite)
            xPixels += gemSize + 1;
        }
        return background
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
            if (player.card_info_to_target["card_id"] && card.id == player.card_info_to_target["card_id"] && player.card_info_to_target["effect_type"] != "mob_comes_into_play" && player.card_info_to_target["effect_type"] != "mob_activated") {
                cardIdToHide = card.id;
                break;
            }
        }

        var inPlayLength = player.in_play.length;

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
            this.addCardToInPlay(game, card, player, inPlaySprite, cardIdToHide, index);
            index++;
        }



        for (let card of player.in_play) {
        }
    }

    addCardToInPlay(game, card, player, inPlaySprite, cardIdToHide, index) {
        let sprite = this.cardSpriteInPlay(game, card, player, false);
        sprite.position.x = (cardWidth)*index + cardWidth/2 + padding + 4;
        sprite.position.y = inPlaySprite.position.y + cardHeight/2;

        if (cardIdToHide && card.id == cardIdToHide) {
            if (player == this.opponent(game)) {
                sprite.filters = [targettableGlowFilter()];
            } else {
                sprite.alpha = .3;
            }
        }
        this.app.stage.addChild(sprite);        
    }

    updateThisPlayerArtifacts(game) {
        this.updateArtifacts(game, this.thisPlayer(game), this.artifacts);
    }

    updateOpponentArtifacts(game) {
        this.updateArtifacts(game, this.opponent(game), this.artifactsOpponent);
    }

    updateArtifacts(game, player, artifactsSprite) {
        var cardIdToHide = null
        for (let card of player.artifacts) {
            if (player.card_info_to_target["card_id"] && card.id == player.card_info_to_target["card_id"]) {
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
            sprite.position.y = artifactsSprite.position.y + cardHeight/2;
            sprite.position.x = artifactsSprite.position.x + cardWidth*index + cardWidth/2;
            this.app.stage.addChild(sprite);
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

    isPlaying(game) {
        return [game.players[0].username, game.players[1].username].includes(this.username)
        
    }
}


function onDragStart(event, cardSprite, gameUX, game) {
    if (!gameUX.isPlaying(game)) {
        return;
    }

    // store a reference to the data
    // the reason for this is because of multitouch
    // we want to track the movement of this particular touch
    cardSprite.data = event.data;
    cardSprite.off('mouseover', cardSprite.onMouseover);
    cardSprite.off('mouseout', cardSprite.onMouseout);
    gameUX.onMouseout(cardSprite, gameUX);

    clearDragFilters(cardSprite)
    cardSprite.dragging = true;

    if (cardSprite.card.turn_played == -1) {
        gameUX.gameRoom.sendPlayMoveEvent("SELECT_CARD_IN_HAND", {"card":cardSprite.card.id});
    } else if (cardSprite.card.card_type == "Mob") {
        gameUX.gameRoom.sendPlayMoveEvent("SELECT_MOB", {"card":cardSprite.card.id});
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
            if (!["any", "any_enemy", "mob", "opponents_mob", "self_mob", "artifact", "any_player"].includes(e.target_type)) {
                // e.target_type is in ["self", "opponent", "Artifact", "all"]
                dragging = false;
            }
        }
        if (!dragging) {
            clearDragFilters(cardSprite)
            cardSprite.dragging = false; 
        }
    }

}

function onDragEnd(cardSprite, gameUX) {
    var playedMove = false;
    var collidedSprite = mostOverlappedNonInHandSprite(gameUX, cardSprite);
    if (cardSprite.card.turn_played == -1) {
        if(!gameUX.bump.hit(cardSprite, gameUX.handContainer) && !cardSprite.card.needs_targets) {
            gameUX.gameRoom.sendPlayMoveEvent("PLAY_CARD_IN_HAND", {"card":cardSprite.card.id});
            playedMove = true;
        } else if(gameUX.bump.hit(cardSprite, gameUX.opponentAvatar) && cardSprite.card.card_type == "Spell" && gameUX.opponent(gameUX.game).can_be_clicked) {
            gameUX.gameRoom.sendPlayMoveEvent("SELECT_OPPONENT", {});
            playedMove = true;
        } else if(gameUX.bump.hit(cardSprite, gameUX.playerAvatar) && cardSprite.card.card_type == "Spell" && gameUX.thisPlayer(gameUX.game).can_be_clicked) {
            gameUX.gameRoom.sendPlayMoveEvent("SELECT_SELF", {});
            playedMove = true;
        } else {
            if(collidedSprite && collidedSprite.card && collidedSprite.card.can_be_clicked) {
                if (collidedSprite.card.turn_played == -1) {
                    gameUX.gameRoom.sendPlayMoveEvent("SELECT_STACK_SPELL", {"card": collidedSprite.card.id});
                } else if (collidedSprite.card.card_type == "Mob") {
                    gameUX.gameRoom.sendPlayMoveEvent("SELECT_MOB", {"card": collidedSprite.card.id});
                } else if (collidedSprite.card.card_type == "Artifact") {
                    gameUX.gameRoom.sendPlayMoveEvent("SELECT_ARTIFACT", {"card": collidedSprite.card.id});
                } else {
                    console.log("tried to select unknown card type: " + collidedSprite.card.card_type);
                }
                playedMove = true;
            }
        }
    } else {  // it's a mob or artifact already in play
        if(gameUX.bump.hit(cardSprite, gameUX.opponentAvatar)) {
            gameUX.gameRoom.sendPlayMoveEvent("SELECT_OPPONENT", {});
            playedMove = true;
        } else if(!gameUX.bump.hit(cardSprite, gameUX.artifacts) && cardSprite.card.card_type == "Artifact" && cardSprite.card.effects[0] && cardSprite.card.effects[0].target_type == "all") {
            gameUX.gameRoom.sendPlayMoveEvent("ACTIVATE_ARTIFACT", {"card":cardSprite.card.id});
            playedMove = true;
        } else if (collidedSprite) {
            gameUX.gameRoom.sendPlayMoveEvent("SELECT_MOB", {"card": collidedSprite.card.id});
            playedMove = true;
        }
    }
    
    if(!playedMove) {
        gameUX.gameRoom.sendPlayMoveEvent("UNSELECT", {});
    }

    cardSprite.dragging = false;
    cardSprite.data = null;
    clearDragFilters(cardSprite)
    gameUX.inPlay.filters = [];
    gameUX.opponentAvatar.filters = [];
}



function onDragMove(cardSprite, gameUX, bump) {
    if (!cardSprite.dragging) {
        return;
    }
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

    let collidedSprite = mostOverlappedNonInHandSprite(gameUX, cardSprite);

    let newFilters = glowAndShadowFilters();
    if(!gameUX.bump.hit(cardSprite, gameUX.handContainer) && !cardSprite.card.needs_targets) {
    } else if(gameUX.bump.hit(cardSprite, gameUX.opponentAvatar) && cardSprite.card.card_type == "Spell" && gameUX.opponent(gameUX.game).can_be_clicked) {
    } else if(gameUX.bump.hit(cardSprite, gameUX.playerAvatar) && cardSprite.card.card_type == "Spell" && gameUX.thisPlayer(gameUX.game).can_be_clicked) {
    } else if(collidedSprite && collidedSprite.can_be_clicked) {
    } else {
        newFilters = [dropshadowFilter(), cantBeClickedFilter()];
    }

    if (!filtersAreEqual(cardSprite.filters, newFilters) || cardSprite.filters.length == 0) {
        clearDragFilters(cardSprite);
        for (let filter of newFilters) {
            cardSprite.filters.push(filter)
        }
    }

    if(opponentCollision && gameUX.opponent(gameUX.game).can_be_clicked) {
        gameUX.opponentAvatar.filters = [targettableGlowFilter()];
    } else if (gameUX.opponent(gameUX.game).can_be_clicked) {
        gameUX.opponentAvatar.filters = [];
    } else {
        gameUX.opponentAvatar.filters = [cantBeClickedFilter()]; 
    }

    if(selfCollision && gameUX.thisPlayer(gameUX.game).can_be_clicked) {
        gameUX.playerAvatar.filters = [targettableGlowFilter()];
    } else if (gameUX.thisPlayer(gameUX.game).can_be_clicked) {
        gameUX.playerAvatar.filters = [];
    } else {
        gameUX.thisPlayer.filters = [cantBeClickedFilter()]; 
    }

    if(collidedSprite && collidedSprite.card && collidedSprite.card.can_be_clicked) {
        if (!filtersAreEqual(collidedSprite.filters, [targettableGlowFilter()]) || collidedSprite.filters.length == 0) {
            clearDragFilters(collidedSprite);
            collidedSprite.filters.push(targettableGlowFilter());                
        }
    }

    for (let mob of gameUX.app.stage.children) {
        if (mob.card && cardSprite.card.id != mob.card.id && (!collidedSprite || mob.card.id != collidedSprite.card.id)) {
            if (mob.card.can_be_clicked) {
                clearDragFilters(mob);
            }  else {
                clearDragFilters(mob);
                mob.filters.push(cantBeClickedFilter());                                                        
            }
        }
    }
}


function clearDragFilters(cardSprite) {
    let newFilters = []
    for (let filter of cardSprite.filters) {
        // retain Shield and Lurker filters
        if (filter.constructor.name == "GlowFilter" && filter.outerStrength == 0 && filter.innerStrength == 3 && (filter.color == 0x000000 || filter.color == 0xFFFFFF)) {
            newFilters.push(filter);
        }
    }

    cardSprite.filters = newFilters;
}


function mostOverlappedNonInHandSprite(gameUX, cardSprite) {
    var collidedSprite;
    var overlapArea = 0;
    for (let sprite of gameUX.app.stage.children) {
        if (gameUX.bump.hit(cardSprite, sprite) && cardSprite.card && sprite.card && cardSprite.card.id != sprite.card.id) {
            var inHand = false;
            for (let card of gameUX.thisPlayer(gameUX.game).hand) {
                if (card.id == sprite.card.id) {
                    inHand = true;
                }
            }
            if (!inHand) {
                var newOverlapArea = getOverlap(cardSprite, sprite);
                if (newOverlapArea > overlapArea) {
                    overlapArea = newOverlapArea;
                    collidedSprite = sprite;
                }
            }
        }
    }
    return collidedSprite;
}

function getOverlap(cardSprite, sprite) {
    var bounds = [cardSprite.position.x, cardSprite.position.y, cardSprite.position.x+cardSprite.width, cardSprite.position.y+cardSprite.height]
    var boundsMob = [sprite.position.x, sprite.position.y, sprite.position.x+sprite.width, sprite.position.y+sprite.height]

    var x_overlap = Math.max(0, Math.min(bounds[2], boundsMob[2]) - Math.max(bounds[0], boundsMob[0]));
    var y_overlap = Math.max(0, Math.min(bounds[3], boundsMob[3]) - Math.max(bounds[1], boundsMob[1]));
    return x_overlap * y_overlap;
}


function filtersAreEqual(a, b) {
    let matches = true;
    if (a.length == b.length) {
        let index = 0;
        for(let filter of a) {
            if (filter.constructor.name != b[index].constructor.name) {
                return false;
            }
            if (filter.constructor.name == "GlowFilter") {
                if (filter.options != b[index].options) {
                    return false;
                }
            }
            index++;
        }
    } else {
       return false; 
    }
    return true    
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
