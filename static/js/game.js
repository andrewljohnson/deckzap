import * as PIXI from 'pixi.js'
import { Bump } from './lib/bump.js';
import { Card } from './Card.js';
import { SVGRasterizer } from './SVGRasterizer.js';
import * as Constants from './constants.js';
import { GlowFilter, GodrayFilter, OutlineFilter } from 'pixi-filters';
import { Scrollbox } from 'pixi-scrollbox'

const appWidth = 1585;
const appHeight = 855;
const avatarHeight = 128;
const avatarWidth = 300;
const cardContainerWidth = Card.cardWidth * 7 + 2 * 7;
const gameDivID = "new_game";
const oneThousandMS = 1000;
const ropeHeight = 8;

// move types recognized by the game rules engine
const moveTypeActivateArtifact = "ACTIVATE_ARTIFACT";
const moveTypeAttack = "ATTACK";
const moveTypeEndTurn = "END_TURN";
const moveTypePlayCardInHand = "PLAY_CARD_IN_HAND";
const moveTypeSelectArtifact = "SELECT_ARTIFACT";
const moveTypeSelectCardInHand = "SELECT_CARD_IN_HAND";
const moveTypeSelectMob = "SELECT_MOB";
const moveTypeSelectSelf = "SELECT_SELF";
const moveTypeSelectOpponent = "SELECT_OPPONENT";
const moveTypeSelectStackSpell = "SELECT_STACK_SPELL";
const moveTypeUnselect = "UNSELECT";

// strings shown to user (todo: localize)
const gameOverMessage = "GAME OVER"
const newGameString = "New Game";
const menuString = "Menu";


export class GameUX {

    constructor() {
        // arrows that get temporarily drawn when attacking ans casting spells
        this.arrows = []
        // damage amounts used for animating damage effects on sprites
        this.spriteDamageCounts = {};
        this.loadDataFromDOM();
        this.loadTextures();
        this.setUpPIXIView();
        this.renderStaticGameElements();
    }
 
    loadDataFromDOM() {
        this.playerType = document.getElementById("data_store").getAttribute("player_type");
        this.allCards = JSON.parse(document.getElementById("card_store").getAttribute("all_cards"));
        this.username = document.getElementById("data_store").getAttribute("username");
    }

    loadTextures() {
        this.artifactsTexture = PIXI.Texture.from("/static/images/artifacts.png");
        this.avatarTexture = PIXI.Texture.from("/static/images/avatar.png");
        this.bearTexture = PIXI.Texture.from("/static/images/bear.png");
        this.handTexture = PIXI.Texture.from("/static/images/hand.png");
        this.inPlayTexture = PIXI.Texture.from("/static/images/in_play.png");
        this.tigerTexture = PIXI.Texture.from("/static/images/tiger.png");        
    }

    setUpPIXIView() {
        this.bump = new Bump(PIXI); // keep a reference to the collision detector
        PIXI.settings.FILTER_RESOLUTION = window.devicePixelRatio || 1;
        PIXI.GRAPHICS_CURVES.adaptive = true
        this.app = new PIXI.Application({
            autoDensity: true,
            height: appHeight, 
            resolution: PIXI.settings.FILTER_RESOLUTION,
            width: appWidth, 
        });        
        document.getElementById(gameDivID).appendChild(this.app.view);
        this.rasterizer = new SVGRasterizer(this.app);
    }

    renderStaticGameElements() {
        this.app.stage.addChild(this.background());
        const centerOfMobs = cardContainerWidth/2 - avatarWidth/2;
        this.opponentAvatar = this.avatar(centerOfMobs, Constants.padding);
        const topOfMiddle = this.opponentAvatar.position.y + avatarHeight + Constants.padding
        this.inPlayOpponent = this.inPlayContainer(Constants.padding, topOfMiddle);
        const artifactX = this.inPlayOpponent.position.x + cardContainerWidth + Constants.padding * 8;
        this.artifactsOpponent = this.artifacts(artifactX,  this.inPlayOpponent.position.y - Constants.padding * 8.5);
        let gapHeight = 90;
        this.artifacts = this.artifacts(artifactX, this.artifactsOpponent.position.y + Card.cardHeight + gapHeight);
        const middleOfMiddle = this.inPlayOpponent.position.y + Card.cardHeight + Constants.padding;
        this.inPlay = this.inPlayContainer(Constants.padding, middleOfMiddle);
        const playerOneY = middleOfMiddle + Card.cardHeight + Constants.padding;
        this.playerAvatar = this.avatar(centerOfMobs, playerOneY);
        this.handContainer = this.hand(Constants.padding, playerOneY + avatarHeight + Constants.padding);
        this.gameLogScrollbox = this.scrollbox()
    }

    avatar(x, y) {
        const avatar = new PIXI.Sprite.from(this.avatarTexture);
        avatar.position.x = x;
        avatar.position.y = y;
        this.app.stage.addChild(avatar);
        return avatar;
    }

    artifacts(x, y) {
        const artifacts = new PIXI.Sprite.from(this.artifactsTexture);
        artifacts.position.x = x;
        artifacts.position.y = y;
        this.app.stage.addChild(artifacts);
        return artifacts;
    }

    inPlayContainer(x, y) {
        const inPlayContainer = new PIXI.Sprite.from(this.inPlayTexture);
        inPlayContainer.position.x = x;
        inPlayContainer.position.y = y;
        this.app.stage.addChild(inPlayContainer);
        return inPlayContainer;
    }

    hand(x, y) {
        const handContainer = new PIXI.Sprite.from(this.handTexture);
        handContainer.position.x = x;
        handContainer.position.y = y;
        this.app.stage.addChild(handContainer);
        return handContainer;
    }

    scrollbox() {
        const scrollboxHeight = avatarHeight - Constants.padding;
        const scrollBoxWidth = 418;
        const scrollbox = new Scrollbox({ boxWidth: scrollBoxWidth, boxHeight: scrollboxHeight, clampWheel: false, passiveWheel: false})
        scrollbox.position.x = this.playerAvatar.position.x + avatarWidth + Constants.padding;
        scrollbox.position.y = this.playerAvatar.position.y;
        const background = new PIXI.Sprite.from(PIXI.Texture.WHITE);
        background.tint = Constants.whiteColor
        background.width = scrollBoxWidth;
        background.height = scrollboxHeight;
        scrollbox.content.addChild(background);
        this.scrollboxBackground = background;
        scrollbox.content.filters = [
          new OutlineFilter(1, Constants.blackColor),
        ]
        this.app.stage.addChild(scrollbox);
        return scrollbox;
    }

    background() {
        const background = new PIXI.Sprite.from(PIXI.Texture.WHITE);
        background.width = appWidth;
        background.height = appHeight;
        background.tint = Constants.lightGrayColor;
        return background;
    }

    menuButton(game) {
        let button = Card.button(
            menuString, 
            Constants.whiteColor, 
            Constants.darkGrayColor, 
            0, 
            0,
            () => { this.showMenu() }
        );
        if (!this.isPlaying(game)) {
            button.buttonSprite.buttonMode = false;
            button.buttonSprite.interactive = false;
        }
        return button;
    }

    showMenu() {
        const container = new PIXI.Container();
        this.app.stage.addChild(container);

        const background = new PIXI.Sprite.from(PIXI.Texture.WHITE);
        background.width = appWidth;
        background.height = appHeight;
        background.tint = Constants.blackColor;
        background.alpha = .7;
        container.addChild(background);

        let options = Constants.textOptions();
        options.wordWrapWidth = 500
        options.fontSize = 24;
        options.fill = Constants.whiteColor;
        options.align = "middle";
        let name = new PIXI.Text(menuString, options);
        name.position.x = appWidth/2 - name.width/2;
        name.position.y = 170
        container.addChild(name);

        let cage = Card.button(
            newGameString, 
            Constants.redColor, 
            Constants.whiteColor, 
            appWidth / 2, 
            name.position.y + name.height,
            () => { this.gameRoom.nextRoom()}, 
            container,
            120
        );

        let cancelCage = Card.button(
            "Return to Game", 
            Constants.darkGrayColor, 
            Constants.whiteColor, 
            appWidth / 2, 
            cage.position.y + cage.height,
            () => { this.app.stage.removeChild(container);}, 
            container,
            120
        );

    }

    // render images that aren't in the cache, then refresh display
    refresh(game, message) {
        this.game = game;
        if (this.opponent(game)) {
            let loadingImages = this.loadInPlayImages(game);
            loadingImages = this.loadHandAndSelectionImages(game) || loadingImages;
            loadingImages = this.loadStackSpellImages(game) || loadingImages;
            loadingImages = this.loadCastingSpellImage(game, message) || loadingImages;
            if (loadingImages) {
                this.app.loader.load(() => {
                    this.finishRefresh(message)
                    this.app.loader.reset()
                });
            } else {
                this.finishRefresh(message)                        
            }
        } else {
            this.finishRefresh(message)                                    
        }
    }

    loadInPlayImages(game) {
        let inPlayCards = 
            this.thisPlayer(game).in_play
            .concat(this.opponent(game).in_play)
            .concat(this.opponent(game).artifacts)
            .concat(this.thisPlayer(game).artifacts)
        return this.rasterizer.loadCardImages(inPlayCards);
    }

    loadHandAndSelectionImages(game) {
        let handAndSelectionCards = this.thisPlayer(game).card_choice_info.cards ? this.thisPlayer(game).card_choice_info.cards : [];
        handAndSelectionCards = handAndSelectionCards.concat(this.thisPlayer(game).hand);
        return this.rasterizer.loadCardImages(handAndSelectionCards);
    }

    loadStackSpellImages(game) {
        let stackSpells = []
        for (let spell of game.stack) {
            stackSpells.push(spell[1]);
        }
        return this.rasterizer.loadCardImages(stackSpells);
    }

    loadCastingSpellImage(game, message) {
        if (this.thisPlayer(game)) {
            if (message.show_spell && !this.thisPlayer(game).card_info_to_target.card_id) {
                return this.rasterizer.loadCardImages([message.show_spell]);
            }
        }
        return false;
    }

    finishRefresh(message) {
        const game = this.game;
        if (this.thisPlayer(game)) {
            if (message.show_spell && !this.thisPlayer(game).card_info_to_target.card_id) {
                let spritesToRemove = [];
                for (let sprite of this.app.stage.children) {
                    if (sprite.card && sprite.card.id == message.show_spell.id && sprite != this.spellBeingCastSprite) {
                        if (sprite.parent) {
                            spritesToRemove.push(sprite)
                        }                        
                    }
                }
                for (let sprite of spritesToRemove) {
                    sprite.parent.removeChild(sprite);
                }

                this.showCardThatWasCast(message.show_spell, game, this.thisPlayer(game), message)
                setTimeout(() => {   
                    this.refreshDisplay(message);
                }, oneThousandMS);
                return;
            }
        }
        this.refreshDisplay(message);
    }

    showCardThatWasCast(card, game, player, message) {
      let godray = new GodrayFilter();
      let incrementGodrayTime = () => {
        godray.time += this.app.ticker.elapsedMS / oneThousandMS;
      }
      let sprite = Card.sprite(card, this, game,  player);
      sprite.scale.set(1.5)
      sprite.position.x = Card.cardWidth + Constants.padding;
      sprite.position.y = this.inPlay.position.y;
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
        }, oneThousandMS);

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
        }
        this.renderEndTurnButton(game, message);
        if (this.opponent(game)) {
            this.addMenuButton(game, this.endTurnButton.width);
        }
        this.maybeShowSpellStack(game);
        this.maybeShowGameOver(game);
        this.maybeShowAttack(game);
        this.maybeShowCardSelectionView(game);
        this.maybeShowRope(game);
        this.elevateSpritesBeingCast();
        if (message.move_type == moveTypeEndTurn) {
            this.showChangeTurnAnimation(game)
        }
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

    clearArrows() {
        if (this.arrows && this.arrows.length) {
            for (let a of this.arrows) {
                this.app.stage.removeChild(a);
            }
            this.arrows = []
        }        
    }

    updateHand(game, index=0) {
        for (let i=index;i<this.thisPlayer(game).hand.length;i++) {
            const card = this.thisPlayer(game).hand[i];
            this.addHandCard(game, card, i)
        }
    }

    addHandCard(game, card, index) {
        let sprite = Card.sprite(card, this, game, this.userOrP1(game), false);
        sprite.position.x = (Card.cardWidth)*index + Card.cardWidth / 2 + Constants.padding;
        sprite.position.y = this.handContainer.position.y + Card.cardHeight / 2;
        this.app.stage.addChild(sprite);                
        if (this.thisPlayer(game).card_info_to_target && card.id == this.thisPlayer(game).card_info_to_target.card_id) {
            sprite.alpha = Constants.beingCastCardAlpha;
        }
    }

    updatePlayer(game, player, avatarSprite) {
        let props = {fontFamily : Constants.defaultFontFamily, fontSize: Constants.defaultFontSize, fill : Constants.blackColor};
        avatarSprite.player = player;
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
        avatar.position.x = Constants.padding;
        avatar.position.y = Constants.padding;
        avatarSprite.addChild(avatar);

        let username = new PIXI.Text(usernameText, props);
        username.position.x = Constants.padding + avatar.position.x + avatar.width;
        username.position.y = Constants.padding;
        avatarSprite.addChild(username);

        let hp = new PIXI.Text(player.hit_points + " hp", props);
        hp.position.x = Constants.padding + avatar.position.x + avatar.width;
        hp.position.y = username.height + username.position.y
        avatarSprite.addChild(hp);

        let hand = hp;
        if (player == this.opponent(game)) {
            hand = new PIXI.Text("Hand: " + player.hand.length, props);
            hand.position.x = Constants.padding + avatar.position.x + avatar.width;
            hand.position.y = hp.height + hp.position.y;
            avatarSprite.addChild(hand);        
        }

        let deck = new PIXI.Text("Deck: " + player.deck.length, props);
        deck.position.x = Constants.padding + avatar.position.x + avatar.width;
        deck.position.y = hand.height + hand.position.y;
        avatarSprite.addChild(deck);

        let playedPile = new PIXI.Text("Played Pile: " + player.played_pile.length, props);
        playedPile.position.x = Constants.padding + avatar.position.x + avatar.width;
        playedPile.position.y = deck.height + deck.position.y;
        avatarSprite.addChild(playedPile);

        let mana = new PIXI.Text("Mana", props);
        mana.position.x = Constants.padding + avatar.position.x + avatar.width;
        mana.position.y = playedPile.height + playedPile.position.y + Constants.padding;
        avatarSprite.addChild(mana);

        let manaGems = Constants.manaGems(player.max_mana, player.mana);
        manaGems.position.x = mana.position.x;
        manaGems.position.y = mana.position.y + mana.height;        
        avatarSprite.addChild(manaGems);

        if (!player.can_be_clicked) {
            avatarSprite.filters = [Constants.cantBeClickedFilter()];                        
            avatarSprite.on("click", function (e) {})
            avatarSprite.interactive = false;
            avatarSprite.buttonMode = true;
       } else {
            avatarSprite.interactive = true;
            avatarSprite.buttonMode = true;
            avatarSprite.filters = [Constants.canBeClickedFilter()];                                   
            if (this.activePlayer(game).card_info_to_target.card_id) {
                let eventString = moveTypeSelectOpponent;
                if (player == this.thisPlayer(game)) {
                    eventString = moveTypeSelectSelf;
                }
                let self = this;
                avatarSprite
                    .on("click", function (e) {self.gameRoom.sendPlayMoveEvent(eventString, {});})
            }
        }

        if (player.damage_to_show > 0) {
           this.damageSprite(avatarSprite, player.username, player.damage_to_show);
        }
    }

    updateThisPlayerArtifacts(game) {
        this.updateArtifacts(game, this.thisPlayer(game), this.artifacts);
    }

    updateOpponentArtifacts(game) {
        this.updateArtifacts(game, this.opponent(game), this.artifactsOpponent);
    }

    updateArtifacts(game, player, artifactsSprite) {
        let cardIdToHide = null
        for (let card of player.artifacts) {
            if (player.card_info_to_target.card_id && card.id == player.card_info_to_target.card_id) {
                cardIdToHide = card.id;
                break;
            }
        }

        let index = 0;

        for (let card of player.artifacts) {
            let sprite = Card.spriteInPlay(card, this, game, player, false);
            sprite.position.y = artifactsSprite.position.y + Card.cardHeight/2 + 6;
            sprite.position.x = artifactsSprite.position.x + Card.cardWidth*index + Card.cardWidth/2 + 3;
            this.app.stage.addChild(sprite);
            index++;
            if (cardIdToHide && card.id == cardIdToHide) {
                sprite.filters = [Constants.targettingGlowFilter()];
            }
        }
    }

    updateThisPlayerInPlay(game) {
        this.updateInPlay(game, this.thisPlayer(game), this.inPlay);
    }

    updateOpponentInPlay(game) {
        this.updateInPlay(game, this.opponent(game), this.inPlayOpponent);
    }

    updateInPlay(game, player, inPlaySprite) {
        let cardIdToHide = null
        for (let card of player.in_play) {
            if (player.card_info_to_target.card_id && card.id == player.card_info_to_target.card_id && player.card_info_to_target["effect_type"] != "mob_comes_into_play" && player.card_info_to_target["effect_type"] != "mob_activated") {
                cardIdToHide = card.id;
                break;
            }
        }
        let inPlayLength = player.in_play.length;
        inPlaySprite.children = []
        let index = 0;
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
    }

    addCardToInPlay(game, card, player, inPlaySprite, cardIdToHide, index) {
        let sprite = Card.spriteInPlay(card, this, game, player, false);
        sprite.position.x = (Card.cardWidth)*index + Card.cardWidth/2 + Constants.padding + 3;
        sprite.position.y = inPlaySprite.position.y + Card.cardHeight/2;

        if (cardIdToHide && card.id == cardIdToHide) {
            if (player == this.opponent(game)) {
                sprite.filters = [Constants.targettableGlowFilter()];
            } else {
                sprite.alpha = Constants.beingCastCardAlpha;
            }
        }
        this.app.stage.addChild(sprite);        
    }

    addMenuButton(game, width) {
        if (!this.menuButtonAdded) {
            let menuButton = this.menuButton(game);
            menuButton.width = width;
            menuButton.position.x = appWidth - width - Constants.padding;
            menuButton.position.y = Constants.padding;
            this.app.stage.addChild(menuButton);
            this.menuButtonAdded = true;
        }
    }

    maybeShowGameOver(game) {
        if (this.opponent(game) && this.thisPlayer(game)) {
            if (this.opponent(game).hit_points <= 0 || this.thisPlayer(game).hit_points <= 0) {
                alert(gameOverMessage);
            }
        }
    }

    maybeShowAttack(game) {
        if (game.stack.length > 0 && game.stack[game.stack.length - 1][0].move_type == moveTypeAttack) {
            let attack = game.stack[game.stack.length - 1][0];
            let attacking_id = attack.card;
            let attackingCardSprite = null;
            for (let sprite of this.app.stage.children) {
                if (sprite.card && sprite.card.id == attacking_id && !this.spellStackSprites.includes(sprite)) {
                    attackingCardSprite = sprite;
                }
            } 
            if (attackingCardSprite) {
                let defending_id = null
                let defendingCardSprite = null;
                if (attack.defending_card) {
                    defending_id = attack.defending_card;
                    for (let sprite of this.app.stage.children) {
                        if (sprite.card && sprite.card.id == defending_id) {
                            defendingCardSprite = sprite;
                        }
                    } 
                }
                if (attackingCardSprite.card.card_type == "mob") { // check if attacker and defender got turned into an artifact mid-attack
                    if(defending_id && defendingCardSprite && defendingCardSprite.card.card_type == "mob") {
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
                            {x:avatar.width / 4, y: avatar.height / 2} 
                        );                                        
                    }
                }
            }
        }        
    }

    maybeShowCardSelectionView(game) {
        if (!this.isShowingCastAnimation) {
            this.showSelectionViews(game);
            this.makeCardsInteractive(game)
        } else {
            this.needsToShowMakeViews = true;
        }        
    }

    maybeShowRope(game) {
        if (!game || !game.show_rope || this.showingRope) {
            return;
        }
        let godray = new GodrayFilter();
        let sprite = new PIXI.Sprite.from(this.inPlayTexture);
        this.ropeSprite = sprite;
        sprite.tint = Constants.redColor;
        let lastElapsed = 0
        let totalElapsed = 0
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
        sprite.position.x = Constants.padding;
        sprite.position.y = this.inPlay.position.y - Constants.padding + 1;
        sprite.height = ropeHeight; 
        this.app.stage.addChild(sprite)
        this.app.ticker.add(this.ropeGodrayTimeTicker)
        this.showingRope = true;
        sprite.filters = [godray];
    }

    // put arrows and spell being cast above other refreshed sprites
    elevateSpritesBeingCast() {    
        if (this.spellBeingCastSprite) {
            this.app.stage.removeChild(this.spellBeingCastSprite);
            this.app.stage.addChild(this.spellBeingCastSprite);
        }
        for (let arrow of this.arrows) {
            this.app.stage.removeChild(arrow);
            this.app.stage.addChild(arrow);
        }
    }

    showChangeTurnAnimation(game) {
        const container = new PIXI.Container();
        this.app.stage.addChild(container);
        const background = new PIXI.Sprite.from(PIXI.Texture.WHITE);
        let modalWidth = this.opponentAvatar.width;
        let modalHeight = this.inPlay.height * 2 + Constants.padding;
        Constants.roundRectangle(background, .2)
        background.width = modalWidth;
        background.height = modalHeight;
        container.position.x = this.opponentAvatar.position.x;
        container.position.y = this.opponentAvatar.position.y + this.opponentAvatar.height + Constants.padding;
        background.tint = Constants.blackColor;
        background.alpha = .7;
        container.addChild(background);

        let options = Constants.textOptions();
        options.wordWrapWidth = 400
        options.fontSize = 32;
        options.fill = Constants.whiteColor;
        options.align = "middle";
        let name = new PIXI.Text(this.activePlayer(game).username + "'s turn", options);
        name.position.x = modalWidth/2 - name.width/2;
        name.position.y = 80
        container.addChild(name);

        let i = 1;                  
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

    showArrow(fromSprite, toSprite, adjustment={"x":0, "y": 0}){
        let cpXY1 = [30,0];
        let cpXY2 = [200,100];
        let toXY = [toSprite.position.x - fromSprite.position.x + adjustment.x, toSprite.position.y - fromSprite.position.y + adjustment.y];
        let fromXY = [fromSprite.position.x, fromSprite.position.y];
        let toXYArc = [toSprite.position.x-fromSprite.position.x+toSprite.width/4,
                        toSprite.position.y-fromSprite.position.y+toSprite.height/2];
        let toXYArrow = [toSprite.position.x+toSprite.width/4,
                        toSprite.position.y+toSprite.height/2 - Constants.padding];

        const bezierArrow = new PIXI.Graphics();
        bezierArrow.tint = Constants.redColor;
        this.arrows.push(bezierArrow);
        this.app.stage.addChild(bezierArrow); 
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
            .lineStyle(4, Constants.whiteColor, 1)
            .bezierCurveTo(cpXY1[0],cpXY1[1],cpXY2[0],cpXY2[1],toXY[0],toXY[1])
            .lineStyle(1, Constants.whiteColor, 1)
            .beginFill(Constants.redColor, 1)
            .moveTo(toXY[0] + normal[0] + tangent[0], toXY[1] + normal[1] + tangent[1])
            .lineTo(toXY[0] , toXY[1] )
            .lineTo(toXY[0] - normal[0] + tangent[0], toXY[1] - normal[1] + tangent[1])
            .lineTo(toXY[0] + normal[0] + tangent[0]-1, toXY[1] + normal[1] + tangent[1])
            .endFill();
        
        let sprite = new PIXI.Sprite(this.app.renderer.generateTexture(bezierArrow,{resolution:PIXI.settings.FILTER_RESOLUTION}))
        bezierArrow.filters = [
            new GlowFilter({ innerStrength: 0, outerStrength: 2, color: Constants.yellowColor}),
            Constants.dropshadowFilter()
        ];


        return sprite;
    }

    // hax: prevents spurious onMouseover events from firing during rendering all the cards
    makeCardsInteractive(game) {
        if (!this.isPlaying(game)) {
            return;
        }

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
        }, oneThousandMS / 5);                
    }

    showSelectionViews(game) {
        if (this.selectCardContainer) {
            this.selectCardContainer.parent.removeChild(this.selectCardContainer);
            this.selectCardContainer = null;
            this.selectCardInnerContainer = null;
        }
        if (this.thisPlayer(game).card_choice_info.cards.length && this.thisPlayer(game).card_choice_info.choice_type == "make") {
            this.showMakeView(game);
        } else if (this.thisPlayer(game).card_choice_info.cards.length && this.thisPlayer(game).card_choice_info.choice_type == "make_with_option") {
            this.showMakeWithChoiceView(game);
        } else if (this.thisPlayer(game).card_choice_info.cards.length && this.thisPlayer(game).card_choice_info.choice_type == "make_from_deck") {
            this.showMakeFromDeckView(game);
        } else if (this.thisPlayer(game).card_choice_info.cards.length && this.thisPlayer(game).card_choice_info.choice_type == "riffle") {
            this.showRiffleView(game, "FINISH_RIFFLE");
        } else if (this.thisPlayer(game).card_choice_info.cards.length && this.thisPlayer(game).card_choice_info.choice_type == "fetch_artifact_into_hand") {
            this.showChooseCardView(game, "FETCH_CARD");
        } else if (this.thisPlayer(game).card_choice_info.cards.length && this.thisPlayer(game).card_choice_info.choice_type == "fetch_into_hand") {
            this.showChooseCardView(game, "FETCH_CARD");
        } else if (this.thisPlayer(game).card_choice_info.cards.length && this.thisPlayer(game).card_choice_info.choice_type == "fetch_into_hand_from_played_pile") {
            this.showChooseFromPlayedPileView(game, "FETCH_CARD_FROM_PLAYED_PILE");
        } else if (this.thisPlayer(game).card_choice_info.cards.length && this.thisPlayer(game).card_choice_info.choice_type == "fetch_artifact_into_play") {
            this.showChooseCardView(game, "FETCH_CARD_INTO_PLAY");
        } else {
            // not a choose cards view
        }                           
    }

    showMakeView(game) {
        this.showSelectCardView(game, "Make a Card", card => {
                if (card.global_effect) {
                    this.gameRoom.sendPlayMoveEvent("MAKE_EFFECT", {"card":card});
                } else {
                    this.gameRoom.sendPlayMoveEvent("MAKE_CARD", {"card":card});
                }
            });
    }

    showMakeWithChoiceView(game) {
        this.showSelectCardView(game, "Make a Card", card => {
            this.gameRoom.sendPlayMoveEvent("MAKE_CARD", {"card":card});
            },
            "Or Keep Song of Patience");
    }

    showMakeFromDeckView(game) {
        this.showSelectCardView(game, "Make from Deck", card => {
            this.gameRoom.sendPlayMoveEvent("FETCH_CARD", {"card":card.id});
        });
    }

    showRevealView(game) {
        this.showSelectCardView(game, "Opponent's Hand", null);
        let makeDiv = document.getElementById("make_selector");
        makeDiv.onclick = () => {
            this.gameRoom.sendPlayMoveEvent("HIDE_REVEALED_CARDS", {});
            this.showGame();
            makeDiv.onclick = null
        }
        this.selectCardContainer
                .on('click',        e => {
                    this.gameRoom.sendPlayMoveEvent("HIDE_REVEALED_CARDS", {});
                })        
    }

    showChooseCardView(game, event_name) {
        this.showSelectCardView(game, "Your Deck", card => {
                this.gameRoom.sendPlayMoveEvent(event_name, {"card":card.id});                
            });
        
    }

    showChooseFromPlayedPileView(game, event_name) {
        this.showSelectCardView(game, "Your Played Pile", card => {
                this.gameRoom.sendPlayMoveEvent(event_name, {"card":card.id});                
            });
        
    }

    showRiffleView(game, event_name) {
        let self = this;
        this.showSelectCardView(game, "Top 3 Cards", card => {
                this.gameRoom.sendPlayMoveEvent(event_name, {"card":card.id});                
            });
        
    }

    showSelectCardView(game, title, card_on_click, cancelTitle=null) {
        const container = new PIXI.Container();
        this.app.stage.addChild(container);
        this.selectCardContainer = container;

        const background = new PIXI.Sprite.from(PIXI.Texture.WHITE);
        background.width = appWidth;
        background.height = appHeight;
        background.tint = Constants.blackColor;
        background.alpha = .7;
        container.addChild(background);

        let options = Constants.textOptions();
        options.wordWrapWidth = 500
        options.fontSize = 24;
        options.fill = Constants.whiteColor;
        options.align = "middle";
        let name = new PIXI.Text(title, options);
        name.position.x = appWidth/2 - name.width/2;
        name.position.y = 170
        container.addChild(name);

        const cardContainer = new PIXI.Container();
        this.selectCardInnerContainer = cardContainer
        cardContainer.position.x = appWidth/2 - Card.cardWidth*1.5;

        let cards = this.thisPlayer(game).card_choice_info.cards;
        if (cards.length >= 6) {
            cardContainer.position.x = Card.cardWidth;            
        }
        // make global effect has 5 cards
        if (cards.length == 5) {
            cardContainer.position.x = appWidth/2 - Card.cardWidth*2.5;            
        }
        cardContainer.position.y = name.position.y + 60;
        container.addChild(cardContainer);

        for (let i=0;i<cards.length;i++) {
            if (cards[i].id != this.thisPlayer(game).card_choice_info.effect_card_id) {
                this.addSelectViewCard(game, cards[i], cardContainer, card_on_click, i)                
            }
        }

        if (cancelTitle) {
            let text = new PIXI.Text(cancelTitle, {fontFamily : Constants.defaultFontFamily, fontSize: Constants.defaultFontSize, fill : Constants.whiteColor});
            text.position.x = Constants.padding * 2;
            text.position.y = text.height;
            const b = new PIXI.Sprite.from(PIXI.Texture.WHITE);
            Constants.roundRectangle(b, 2)
            b.width = text.width + Constants.padding * 4;
            b.height = text.height*3;
            b.tint = Constants.blueColor;
            b.buttonMode = true;
            b.interactive = true;
            const clickFunction = () => {
                this.gameRoom.sendPlayMoveEvent("CANCEL_MAKE", {});
            };
            b
                .on("click", clickFunction)
                .on("tap", clickFunction)
            const cage = new PIXI.Container();
            cage.position.x = appWidth / 2 - b.width/2;
            cage.position.y = cardContainer.position.y + cardContainer.height + b.height;
            cage.addChild(b);
            cage.addChild(text);
            cage.name = "button";
            cage.text = text;
            cage.buttonSprite = b;
            container.addChild(cage);
        }
    }

    addSelectViewCard(game, card, cardContainer, card_on_click, index) {
        let cardSprite = Card.sprite(card, this, game, this.userOrP1(game), false, false, true);
        cardSprite.position.x = (Card.cardWidth + Constants.padding) *  (index % 8) + Card.cardWidth/2;
        cardSprite.position.y = Card.cardHeight/2 + (Card.cardHeight + 5) * Math.floor(index / 8);            
        cardContainer.addChild(cardSprite);
        let self = this;
        cardSprite
            .on('click',        function (e) {
                Card.onMouseout(cardSprite, self);
                card_on_click(card);
            })
    }

    setCardDragListeners(card, cardSprite, game) {
        if (card.can_be_clicked) {
            let isHandCard = false;
            for (let c of this.thisPlayer(game).hand) {
                if (c.id == card.id) {
                    isHandCard = true;
                }
            }
            //  todo: cleaner if/then for Duplication Chamber/Upgrade Chamber/Mana Coffin
            if (isHandCard && this.thisPlayer(game).card_info_to_target.effect_type == "artifact_activated") {
                cardSprite.on('click',        e => {this.gameRoom.sendPlayMoveEvent(moveTypeSelectCardInHand, {"card":card.id});})
            } else if (this.thisPlayer(game).card_info_to_target.card_id) {
                cardSprite.on('click',        e => {this.gameRoom.sendPlayMoveEvent(moveTypeSelectMob, {"card":card.id});})
            } else {
                let self = this;
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

    showArrowsForSpell(game, sprite, spellMessage, card) {
        if (spellMessage.effect_targets && spellMessage.effect_targets[0].target_type == "player") {
            if (spellMessage.effect_targets[0].id == this.opponent(game).username) {
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
        } else if (spellMessage.effect_targets && ["mob", "artifact"].includes(spellMessage.effect_targets[0].target_type)) {
            let targetID = spellMessage.effect_targets[0].id;
            let targetCardSprite = null;
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
        if (spellMessage.effect_targets && spellMessage.effect_targets.length == 2 && spellMessage.effect_targets[1].target_type == "player" && spellMessage.effect_targets[1].id == this.opponent(game).username) {
            let avatar = this.playerAvatar;
            if (spellMessage.effect_targets[1].id == this.opponent(game).username) {
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

    activePlayerHasMoves(game) {
        for (let sprite of this.app.stage.children) {
            if(sprite.card && sprite.card.can_be_clicked) {
                return true;
            }
        }        
        if (game.players[0] && game.players[0].can_be_clicked) {
            return true;
        }
        if (game.players[1] && game.players[1].can_be_clicked) {
            return true;
        }
        return false;
    }

    renderEndTurnButton(game, message) {
        if (this.turnLabel) {
            this.app.stage.removeChild(this.turnLabel)
        }
        if (this.endTurnButton) {
            this.app.stage.removeChild(this.endTurnButton)
        }

        let clickFunction = () => {
            if (game.stack.length > 0) {
                this.gameRoom.pass(message)
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

        let title = "End Turn";
        let textFillColor = Constants.whiteColor;
        let buttonColor = null;
        
        if (this.isActivePlayer(game)) {
            if (!this.activePlayerHasMoves(game) || game.stack.length > 0) {
                buttonColor = Constants.redColor;
            } else {
                buttonColor = Constants.lightRedColor;
            }

            if (this.thisPlayer(game).card_info_to_target.effect_type) {
                buttonColor = Constants.menuGrayColor;
                title = "Choose Target";
            }
        } else {
            title = "Waiting...";
            textFillColor = Constants.darkGrayColor;
        }

        if (game.stack.length > 0) {
            if (this.isActivePlayer(game)) {
                title = "OK";
            } else {    
                title = "Waiting...";
            }
        }

        let buttonWidth = 160;

        let b = Card.button(
            title, 
            buttonColor, 
            textFillColor, 
            23, 
            17,
            clickFunction, 
            this.app.stage,
            buttonWidth
        );
        b.position.x = this.artifactsOpponent.position.x;
        b.position.y = this.artifactsOpponent.position.y + this.artifactsOpponent.height + b.height / 4;

        if (this.isActivePlayer(game)) {
            if (this.thisPlayer(game).card_info_to_target.effect_type) {
                b.interactive = false;
            }
        } else {
            b.interactive = false;
        }
        if (!this.isPlaying(game)) {
            b.buttonSprite.buttonMode = false;
            b.buttonSprite.interactive = false;
        }

        this.endTurnButton = b;

        let turnText = new PIXI.Text(`${this.thisPlayer(game).username} is Active\n(Turn ${game.turn})`, {fontFamily : Constants.defaultFontFamily, fontSize: Constants.defaultFontSize, fill : Constants.darkGrayColor, align: "center"});
        turnText.position.x = b.position.x + buttonWidth + Constants.padding * 10;
        turnText.position.y = b.position.y + b.height / 2;
        turnText.anchor.set(0.5, 0.5);
        this.turnLabel = turnText;
        this.app.stage.addChild(turnText);

    }

    maybeShowSpellStack(game) {
        if (game.stack.length == 0) {
            return;
        }
        if (!this.spellStackSprites) {
            this.spellStackSprites = []
        }
        let index = -1;
        for (let spell of game.stack) {
            index++;
            let playerName = spell[0].username;
            let player = null;
            if (this.opponent(game).username == playerName) {
                player = this.opponent(game);
            } else {
                player = this.thisPlayer(game);
            }

            let sprite = Card.sprite(spell[1], this, game, player);
            if (spell[0].move_type == moveTypeAttack) {
                continue;
            }
            sprite.scale.set(1.5)
            sprite.position.x = 100 + 20*index;
            sprite.position.y = this.inPlay.position.y + Constants.padding + 40*index;
            this.app.stage.addChild(sprite)
            this.spellStackSprites.push(sprite)
            let card = spell[1]
            let spellMessage = spell[0]
            this.showArrowsForSpell(game, sprite, spellMessage, card);
        }
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

    damageSprite(spriteToDamage, spriteId, damage_to_show) {
          setTimeout(() => { 
                this.spriteDamageCounts[spriteId] += 1;
                if (!this.spriteDamageCounts[spriteId] && this.spriteDamageCounts[spriteId] != 0) {
                    this.spriteDamageCounts[spriteId] = 0                    
                    let godray = new GlowFilter({ outerStrength: 8, innerStrength: 2 , color: Constants.redColor});
                    spriteToDamage.filters = [godray];
                    this.damageSprite(spriteToDamage, spriteId, damage_to_show);                    
                } else if (this.spriteDamageCounts[spriteId] >= damage_to_show*3) {
                    this.spriteDamageCounts[spriteId] = 0
                    spriteToDamage.filters = []; 
                } else {
                    let godray = new GlowFilter({ outerStrength: 8, innerStrength: 2 , color: Constants.redColor});
                    spriteToDamage.filters = [godray];
                    setTimeout(() => { 
                        spriteToDamage.filters = [];
                    }, 100); 
                    this.spriteDamageCounts[spriteId] += 1
                    this.damageSprite(spriteToDamage, spriteId, damage_to_show);                    
                }
            }, 200);   
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
        if (game.players[1] && this.username == game.players[1].username) {
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
            let textSprite = new PIXI.Text(text, {wordWrap: true, wordWrapWidth: 360, fontSize: 10});
            textSprite.position.x = 5;
            textSprite.position.y = this.messageNumber * 16 + 5;
            this.scrollboxBackground.height = Math.max(this.playerAvatar.height - Constants.padding, (this.messageNumber + 1) * 16);
            this.gameLogScrollbox.content.addChild(textSprite);
        }
        this.gameLogScrollbox.content.top += this.gameLogScrollbox.content.worldScreenHeight;
        this.gameLogScrollbox.update();
    }

    isPlaying(game) {
        if (!game.players[1]) {
            return false;
        }
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
    cardSprite.off('mouseover', Card.onMouseover);
    cardSprite.off('mouseout', Card.onMouseout);
    Card.onMouseout(cardSprite, gameUX);

    cardSprite.dragging = true;

    if (cardSprite.card.turn_played == -1) {
        gameUX.gameRoom.sendPlayMoveEvent(moveTypeSelectCardInHand, {"card":cardSprite.card.id});
    } else if (cardSprite.card.card_type == Constants.mobCardType) {
        gameUX.gameRoom.sendPlayMoveEvent(moveTypeSelectMob, {"card":cardSprite.card.id});
    } else if (cardSprite.card.card_type == Constants.artifactCardType) {
        gameUX.gameRoom.sendPlayMoveEvent(moveTypeSelectArtifact, {"card":cardSprite.card.id});
        let enabled_effects = [];
        for (let e of cardSprite.card.effects) {
            if (e.effect_type == "activated" && e.enabled == true) {
                enabled_effects.push(e);
            }
        }
        let dragging = true;
        for (let e of enabled_effects) {
            if (!["any", "any_enemy", "mob", "opponents_mob", "self_mob", "artifact", "any_player"].includes(e.target_type)) {
               // e.target_type is in ["self", "opponent", Constants.artifactCardType, "all"]
               cardSprite.dragging = false; 
            }
        }
    }

}


function onDragEnd(cardSprite, gameUX) {
    let playedMove = false;
    let collidedSprite = mostOverlappedNonInHandSprite(gameUX, cardSprite);

    if (cardSprite.card.turn_played == -1) {
        if(!gameUX.bump.hit(cardSprite, gameUX.handContainer) && !cardSprite.card.needs_targets) {
            gameUX.gameRoom.sendPlayMoveEvent(moveTypePlayCardInHand, {"card":cardSprite.card.id});
            playedMove = true;
        } else if (collidedSprite == gameUX.opponentAvatar && cardSprite.card.card_type == Constants.spellCardType && gameUX.opponent(gameUX.game).can_be_clicked) {
            gameUX.gameRoom.sendPlayMoveEvent(moveTypeSelectOpponent, {});
            playedMove = true;
        } else if(collidedSprite == gameUX.playerAvatar && cardSprite.card.card_type == Constants.spellCardType && gameUX.thisPlayer(gameUX.game).can_be_clicked) {
            gameUX.gameRoom.sendPlayMoveEvent(moveTypeSelectSelf, {});
            playedMove = true;
        } else {
            if(collidedSprite && collidedSprite.card && collidedSprite.card.can_be_clicked) {
                if (collidedSprite.card.turn_played == -1) {
                    gameUX.gameRoom.sendPlayMoveEvent(moveTypeSelectStackSpell, {"card": collidedSprite.card.id});
                } else if (collidedSprite.card.card_type == Constants.mobCardType) {
                    gameUX.gameRoom.sendPlayMoveEvent(moveTypeSelectMob, {"card": collidedSprite.card.id});
                } else if (collidedSprite.card.card_type == Constants.artifactCardType) {
                    gameUX.gameRoom.sendPlayMoveEvent(moveTypeSelectArtifact, {"card": collidedSprite.card.id});
                } else {
                    console.log("tried to select unknown card type: " + collidedSprite.card.card_type);
                }
                playedMove = true;
            }
        }
    } else {  // it's a mob or artifact already in play
        if(collidedSprite == gameUX.opponentAvatar) {
            gameUX.gameRoom.sendPlayMoveEvent(moveTypeSelectOpponent, {});
            playedMove = true;
        } else if(!gameUX.bump.hit(cardSprite, gameUX.artifacts) && cardSprite.card.card_type == Constants.artifactCardType && cardSprite.card.effects[0] && cardSprite.card.effects[0].target_type == "all") {
            gameUX.gameRoom.sendPlayMoveEvent(moveTypeActivateArtifact, {"card":cardSprite.card.id});
            playedMove = true;
        } else if(collidedSprite == gameUX.playerAvatar) {
            // todo: can't attack or target current player with effects of in play mobs and artifacts?
        } else if (collidedSprite) {
            gameUX.gameRoom.sendPlayMoveEvent(moveTypeSelectMob, {"card": collidedSprite.card.id});
            playedMove = true;
        }
    }
    if(!playedMove) {
        gameUX.gameRoom.sendPlayMoveEvent(moveTypeUnselect, {});
    }
    cardSprite.dragging = false;
    gameUX.inPlay.filters = [];
    gameUX.opponentAvatar.filters = [];
}


function onDragMove(dragSprite, gameUX, bump) {
    if (!dragSprite.dragging) {
        return;
    }

    // take sprite out of the hand container so it can collide with other sprites when dragged
    let newPosition = dragSprite.data.getLocalPosition(dragSprite.parent);
    dragSprite.position.x = newPosition.x;
    dragSprite.position.y = newPosition.y;
    let parent = dragSprite.parent;
    parent.removeChild(dragSprite);
    parent.addChild(dragSprite);

    let collidedSprite = updateDraggedCardFilters(gameUX, dragSprite);
    updatePlayerAvatarFilters(collidedSprite, gameUX.opponent(gameUX.game), gameUX.opponentAvatar);
    updatePlayerAvatarFilters(collidedSprite, gameUX.thisPlayer(gameUX.game), gameUX.playerAvatar);
    updateCardsInFieldSpriteFilters(gameUX, dragSprite, collidedSprite);
}


function updateDraggedCardFilters(gameUX, cardSprite){
    let collidedSprite = mostOverlappedNonInHandSprite(gameUX, cardSprite);
    let newFilters = Constants.glowAndShadowFilters();
    if(!gameUX.bump.hit(cardSprite, gameUX.handContainer) && !cardSprite.card.needs_targets) {
    } else if(gameUX.bump.hit(cardSprite, gameUX.opponentAvatar) && cardSprite.card.card_type == Constants.spellCardType && gameUX.opponent(gameUX.game).can_be_clicked) {
    } else if(gameUX.bump.hit(cardSprite, gameUX.playerAvatar) && cardSprite.card.card_type == Constants.spellCardType && gameUX.thisPlayer(gameUX.game).can_be_clicked) {
    } else if(collidedSprite && collidedSprite.card && collidedSprite.card.can_be_clicked) {
    } else {
        newFilters = [Constants.dropshadowFilter()]
    }
    if (!filtersAreEqual(cardSprite.filters, newFilters) || cardSprite.filters.length == 0) {
        clearDragFilters(cardSprite);
        for (let filter of newFilters) {
            if (!filtersContainsFilter(cardSprite.filters, filter)) {
                cardSprite.filters.push(filter)
            }
        }
    }
    return collidedSprite;
}


function updatePlayerAvatarFilters(collidedSprite, player, playerAvatar) {
    if(collidedSprite == playerAvatar && player.can_be_clicked) {
        if (!filtersAreEqual(playerAvatar.filters, [Constants.targettableGlowFilter()]) || playerAvatar.filters.length == 0) {
            playerAvatar.filters = [Constants.targettableGlowFilter()];
        }
    } else if (player.can_be_clicked) {
        if (!filtersAreEqual(playerAvatar.filters, [Constants.canBeClickedFilter()]) || playerAvatar.filters.length == 0) {
            playerAvatar.filters = [Constants.canBeClickedFilter()];
        }
    } else {
        if (!filtersAreEqual(playerAvatar.filters, [Constants.cantBeClickedFilter()]) || playerAvatar.filters.length == 0) {
            playerAvatar.filters = [Constants.cantBeClickedFilter()];
        }
    }
}


function updateCardsInFieldSpriteFilters(gameUX, dragSprite, collidedSprite) {
    if(collidedSprite && collidedSprite.card && collidedSprite.card.can_be_clicked) {
        if (!filtersAreEqual(collidedSprite.filters, [Constants.targettableGlowFilter()]) || collidedSprite.filters.length == 0) {
            clearDragFilters(collidedSprite);
            collidedSprite.filters.push(Constants.targettableGlowFilter());                
        }
    }

    for (let mob of gameUX.app.stage.children) {
        if (mob.card && dragSprite.card.id != mob.card.id && (!collidedSprite || !collidedSprite.card || mob.card.id != collidedSprite.card.id)) {
            if (mob.card.can_be_clicked) {
                if (!hasCanBeClickedFilter(mob) || hasCantBeTargettedFilter(mob)) {
                    clearDragFilters(mob);
                    mob.filters.push(Constants.canBeClickedFilter());                                                        
                }
            }  else {
                if (!hasCantBeTargettedFilter(mob) || hasCanBeClickedFilter(mob)) {
                    clearDragFilters(mob);
                    mob.filters.push(Constants.cantBeTargettedFilter());                                                        
                }
            }
        }
    }
}


function filtersContainsFilter(filters, filter) {
    for (let f of filters) {
        if (filtersAreEqual([f], [filter])) {
            return true;
        }
    }
    return false;
}


function filtersAreEqual(a, b) {

    let matches = true;
    if (a.length == b.length) {
        let index = 0;
        for(let filter of a) {
            if (filter.constructor.name != b[index].constructor.name) {
                return false;
            }
            if ([Constants.canBeClickedFilter().constructor.name, Constants.targettableGlowFilter().constructor.name, Constants.targettingGlowFilter()].includes(filter.constructor.name)) {
                if (filter.color != b[index].color) {
                    return false;
                }
                if (filter.innerStrength != b[index].innerStrength) {
                    return false;
                }
                if (filter.outerStrength != b[index].outerStrength) {
                    return false;
                }
            }
            if (filter.constructor.name == Constants.cantBeTargettedFilter().constructor.name) {
                if (filter.alpha != b[index].alpha) {
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


function hasCanBeClickedFilter(cardSprite) {
    let newFilters = []
    const cbcf = Constants.canBeClickedFilter()
    for (let filter of cardSprite.filters) {
        if (filter.constructor.name == cbcf.constructor.name && filter.innerStrength == cbcf.innerStrength && filter.outerStrength == cbcf.outerStrength && (filter.color == cbcf.color)) {
            return true;
        }
    }
    return false;
}


function hasCantBeTargettedFilter(cardSprite) {
    let newFilters = []
    const cbtf = Constants.cantBeTargettedFilter()
    for (let filter of cardSprite.filters) {
        if (filter.constructor.name == cbtf.constructor.name && filter.alpha == cbtf.alpha) {
            return true;
        }
    }
    return false;
}


function clearDragFilters(cardSprite) {
    let newFilters = []
    for (let filter of cardSprite.filters) {
        const lf = Constants.lurkerFilter();
        const sf = Constants.shieldFilter();
        if (filter.constructor.name == lf.constructor.name && filter.outerStrength == lf.outerStrength && filter.innerStrength == lf.innerStrength && filter.color == lf.color) {
            newFilters.push(filter);
        } else if (filter.constructor.name == sf.constructor.name && filter.outerStrength == sf.outerStrength && filter.innerStrength == sf.innerStrength && filter.color == sf.color) {
            newFilters.push(filter);
        }
    }
    cardSprite.filters = newFilters;
}


function mostOverlappedNonInHandSprite(gameUX, cardSprite) {
    let collidedSprite;
    let overlapArea = 0;
    for (let sprite of gameUX.app.stage.children) {
        if (gameUX.bump.hit(cardSprite, sprite) && cardSprite.card && sprite.card && cardSprite.card.id != sprite.card.id) {
            let inHand = false;
            for (let card of gameUX.thisPlayer(gameUX.game).hand) {
                if (card.id == sprite.card.id) {
                    inHand = true;
                }
            }
            if (!inHand) {
                let newOverlapArea = getOverlap(cardSprite, sprite);
                if (newOverlapArea > overlapArea && sprite.card.can_be_clicked) {
                    overlapArea = newOverlapArea;
                    collidedSprite = sprite;
                }
            }
        }
    }
    let newOverlapArea = getOverlap(cardSprite, gameUX.playerAvatar);
    if (newOverlapArea > overlapArea && gameUX.playerAvatar.player.can_be_clicked) {
        overlapArea = newOverlapArea;
        collidedSprite = gameUX.playerAvatar;
    }
    newOverlapArea = getOverlap(cardSprite, gameUX.opponentAvatar);
    if (newOverlapArea > overlapArea && gameUX.opponentAvatar.player.can_be_clicked) {
        overlapArea = newOverlapArea;
        collidedSprite = gameUX.opponentAvatar;
    }
    return collidedSprite;
}


function getOverlap(cardSprite, sprite) {
    let bounds = [cardSprite.position.x, cardSprite.position.y, cardSprite.position.x+cardSprite.width, cardSprite.position.y+cardSprite.height]
    let boundsMob = [sprite.position.x, sprite.position.y, sprite.position.x+sprite.width, sprite.position.y+sprite.height]

    let x_overlap = Math.max(0, Math.min(bounds[2], boundsMob[2]) - Math.max(bounds[0], boundsMob[0]));
    let y_overlap = Math.max(0, Math.min(bounds[3], boundsMob[3]) - Math.max(bounds[1], boundsMob[1]));
    return x_overlap * y_overlap;
}
