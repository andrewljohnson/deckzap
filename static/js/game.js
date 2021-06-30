import * as PIXI from 'pixi.js'
import { Bump } from './lib/bump.js';
import { AdjustmentFilter, DropShadowFilter, GlowFilter, GodrayFilter, OutlineFilter } from 'pixi-filters';

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
        this.inPlayTexture = PIXI.Texture.from('/static/images/in_play.png');
        this.handTexture = PIXI.Texture.from('/static/images/hand.png');
        this.artifactsTexture = PIXI.Texture.from('/static/images/relics.png');
        this.avatarTexture = PIXI.Texture.from('/static/images/avatar.png');
        this.menuTexture = PIXI.Texture.from('/static/images/menu.png');
        this.newGameButtonTexture = PIXI.Texture.from('/static/images/menu-button.png');
        this.bearTexture = PIXI.Texture.from('/static/images/bear.png');
        this.tigerTexture = PIXI.Texture.from('/static/images/tiger.png');

        PIXI.settings.FILTER_RESOLUTION = window.devicePixelRatio || 1;
        this.app = new PIXI.Application({
            width: appWidth, 
            height: appHeight, 
            antialias: false, 
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

        /*
        const mockScroll = new PUXI.ScrollWidget({
            scrollY: true,
            scrollX: true,
            scrollBars: true,
        }).setLayoutOptions(
            new PUXI.FastLayoutOptions({
                width: 0.5,
                height: 0.25,
                x: 0.5,
                y: 0.7,
                anchor: PUXI.FastLayoutOptions.CENTER_ANCHOR,
            }),
        ).setBackground(0xffaabb)
            .setBackgroundAlpha(0.5)
            .addChild(new PUXI.Button({ text: 'Button 1' }).setBackground(0xff))
            .addChild(new PUXI.Button({ text: 'Button 2' })
                .setLayoutOptions(new PUXI.FastLayoutOptions({ x: 0, y: 50 }))
                .setBackground(0xff));

        this.app.stage.addChild(mockScroll);
        */
        return

        const gameLog = PIXI.Sprite.from(PIXI.Texture.WHITE);
        gameLog.width = appWidth-4;
        gameLog.height = cardHeight *1.25;
        gameLog.tint = 0xFFFFFF;
        gameLog.position.x = 2;
        gameLog.position.y = this.handContainer.position.y + cardHeight + padding;
        gameLog.filters = [
          new OutlineFilter(1, 0x000000),
        ]
        this.app.stage.addChild(gameLog);

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
                this.showCardThatWasCast(message["show_spell"], game)
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
            for (let sprite of this.app.stage.children) {
                if (sprite.card && sprite.card.can_be_clicked) {
                    sprite.filters = [
                      new GlowFilter({ distance: 15, outerStrength: 2 , color: 0xffff00}),
                    ]
                }
            }
            if (this.thisPlayer(game).can_be_clicked) {
                this.playerAvatar.filters = [
                  new GlowFilter({ distance: 15, outerStrength: 2 , color: 0xffff00}),
                ]                
            }
            if (this.opponent(game).can_be_clicked) {
                this.opponentAvatar.filters = [
                  new GlowFilter({ distance: 15, outerStrength: 2 , color: 0xffff00}),
                ]                
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
        this.showSelectCardView(game, "Artifacts in Your Deck", function (card) {
                self.gameRoom.sendPlayMoveEvent(event_name, {"card":card.id});                
            });
        
    }

    showRiffleView(game, event_name) {
        var self = this;
        this.showSelectCardView(game, "Top 3 Cards", function (card) {
                self.gameRoom.sendPlayMoveEvent(event_name, {"card":card.id});                
            });
        
    }

    showSelectCardView(game, title, card_on_click) {
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
        cardContainer.position.y = 140;
        container.addChild(cardContainer);

        var cards = this.thisPlayer(game).card_choice_info["cards"];

        var index = 0;
        for (let card of cards) {
            let cardSprite = this.cardSprite(game, card, this.usernameOrP1(game), index);
            cardContainer.addChild(cardSprite);

            var self = this;
            cardSprite
                .on('click',        function (e) {
                    card_on_click(card);
                })
            index += 1;
        }
    }

    cardSprite(game, card, username, index, dont_attach_listeners) {
        let cardSprite = new PIXI.Sprite.from(this.cardTexture);
        cardSprite.interactive = true;
        cardSprite.anchor.set(.5);
        cardSprite.card = card;
        cardSprite.buttonMode = true;  // hand cursor
        cardSprite.position.x = (cardWidth)*index + cardWidth/2;
        cardSprite.position.y = cardHeight/2;
        cardSprite.index = index;

        let options = {fontFamily : 'Helvetica', fontSize: 8, fill : 0x00000, wordWrap: true, wordWrapWidth: 49};
        let name = new PIXI.Text(card.name, options);
        cardSprite.addChild(name);

        let aFX = -38;
        let aFY = -55;
        name.position.x = aFX + 7;
        name.position.y = aFY + padding/2;

        if (card.card_type != "Effect") {
            let cost = new PIXI.Text(card.cost, options);
            cardSprite.addChild(cost);
            cost.position.x = aFX + cardWidth - 18;
            cost.position.y = aFY + 11;
        }

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

        options.wordWrapWidth = 62;
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
        description.position.y = name.position.y + 30;

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
                    abilitiesText += a.name;
                }
                if (a != card.abilities[card.abilities.length-1]) {                
                    abilitiesText += ", ";
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
            cardSprite.addChild(abilities);
        }        


        if (card.card_type == "Entity") {
            let cardPower = card.power;
            let cardToughness = card.toughness - card.damage;
            if (card.tokens) {
                // todo does this code need to be clientside?
                let user = this.usernameOrP1(game);
                for (let c of card.tokens) {
                    if (c.multiplier == "self_artifacts" && user.artifacts) {
                        cardPower += c.power_modifier * user.artifacts.length;                        
                    } else {
                        cardPower += c.power_modifier;                        
                    }
                }
                for (let c of card.tokens) {
                    cardToughness += c.toughness_modifier;
                }
            }
            options.fill = 0x000000;
            let powerToughness = new PIXI.Text(cardPower + "/" + cardToughness, options);
            powerToughness.position.x = aFX + cardWidth - 22;
            powerToughness.position.y = aFY + cardHeight - 20;
            cardSprite.addChild(powerToughness);
        } else if (card.turn_played == -1 && !attackEffect) {
            let type = new PIXI.Text(card.card_type, options);
            type.position.x = aFX + cardWidth - 22;
            type.position.y = aFY + cardHeight - 20;
            cardSprite.addChild(type);
        }

        if (attackEffect) {
            let powerCharges = new PIXI.Text(attackEffect.power + "/" + attackEffect.counters, options);
            powerCharges.position.x = aFX + cardWidth - 22;
            powerCharges.position.y = aFY + cardHeight - 20;
            cardSprite.addChild(powerCharges);
        }

        var filters = []
        if (!card.can_be_clicked) {
            filters.push(new AdjustmentFilter({ brightness: .8}));                        
        }
        if (card.shielded && card.turn_played > -1) {
            filters.push(new GlowFilter({color: 0xffff00}));                        
        }

        if (card.abilities.length > 0 && card.abilities[0].descriptive_id == "Lurker" && card.abilities[0].enabled && card.turn_played > -1) {
            filters.push(new GlowFilter({color: 0x000000}));                        
        }

        cardSprite.filters = filters;


        if (dont_attach_listeners) {
            return cardSprite;
        }

        if (card.can_be_clicked) {
            if (this.thisPlayer(game).card_info_to_resolve["card_id"]) {
                var self = this;
                cardSprite
                    .on('click',        function (e) {self.gameRoom.sendPlayMoveEvent("SELECT_ENTITY", {"card":card.id});})
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

                }        
        }

        return cardSprite;
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

    showCardThatWasCast(card, game) {
      var godray = new GodrayFilter();
      var incrementGodrayTime = () => {
        godray.time += this.app.ticker.elapsedMS / 1000;
      }
      let sprite = this.cardSprite(game, card, this.usernameOrP1(game), null);
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
        // b.anchor.set(0.5);
        b.interactive = true;
        var clickFunction = () => {
            this.gameRoom.endTurn()
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
        return (game.turn % 2 == 0 && this.usernameOrP1(game) == game.players[0].username
                || game.turn % 2 == 1 && this.usernameOrP1(game) == game.players[1].username)
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
            avatarSprite.filters = [new AdjustmentFilter({ brightness: .8,})];                        
            avatarSprite.on('click', function (e) {})
            avatarSprite.interactive = false;
            avatarSprite.buttonMode = true;
       } else {
            console.log("player can be clicked")
            avatarSprite.interactive = true;
            avatarSprite.buttonMode = true;
            avatarSprite.filters = [];                                   
            if (player.card_info_to_resolve["card_id"]) {
                console.log("card_info_to_resolve")
                var eventString = "SELECT_OPPONENT";
                if (player == this.thisPlayer(game)) {
                    eventString = "SELECT_SELF";
                }
                var self = this;
                avatarSprite
                    .on('click', function (e) {console.log("click player"); self.gameRoom.sendPlayMoveEvent(eventString, {});})
            }
        }



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
            let sprite = this.cardSprite(game, card, this.usernameOrP1(game), index);
            sprite.position.y = this.handContainer.position.y + cardHeight/2;
            sprite.position.x += padding;
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
        if (cardIdToHide) {
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
            if (cardIdToHide && card.id == cardIdToHide) {
                continue;
            }
            let sprite = this.cardSprite(game, card, this.usernameOrP1(game), index);
            sprite.position.y = inPlaySprite.position.y + cardHeight/2;
            sprite.position.x += padding;
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
        artifactsSprite.children = []
        var index = 0;
        for (let card of player.artifacts) {
            let sprite = this.cardSprite(game, card, this.usernameOrP1(game), index);
            this.app.stage.addChild(sprite);
            sprite.position.y = artifactsSprite.position.y + cardHeight/2;
            sprite.position.x = artifactsSprite.position.x + cardWidth*index + cardWidth/2;
            index++;
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

    usernameOrP1(game) {
        if (this.username == game.players[0].username || this.username == game.players[1].username) {
            return this.username;
        }
        return game.players[0].username;
    }

    logMessage(log_lines) {
        return;
        for (let text of log_lines) {
            var line = this.addLogLine();
            line.innerHTML = text
        }
        this.scrollLogToEnd()
    }

    addLogLine() {
        return;
        var line = document.createElement('div');
        document.getElementById("game_log_inner").appendChild(line);
        return line;
    }

    scrollLogToEnd() {
        return;
        document.getElementById("game_log_inner").scrollTop = document.getElementById("game_log_inner").scrollHeight;
    }

    // used for observer mode code
    usernameOrP1(game) {
        if (this.username == game.players[0].username || this.username == game.players[1].username) {
            return this.username;
        }
        return game.players[0].username;
    }
}


function onDragStart(event, card, gameUX) {
    // store a reference to the data
    // the reason for this is because of multitouch
    // we want to track the movement of this particular touch
    card.data = event.data;
    card.dragging = true;
    card.filters = [
        new DropShadowFilter({ distance: 15, outerStrength: 2 }),
    ];
    if (card.card.turn_played == -1) {
        if(card.card.card_type == "Spell" && card.card.needs_targets) {
            gameUX.gameRoom.sendPlayMoveEvent("SELECT_CARD_IN_HAND", {"card":card.card.id});
        } 
    } else if (card.card.card_type == "Entity") {
        gameUX.gameRoom.sendPlayMoveEvent("SELECT_ENTITY", {"card":card.card.id});
    } else if (card.card.card_type == "Artifact") {
        gameUX.gameRoom.sendPlayMoveEvent("SELECT_ARTIFACT", {"card":card.card.id});
    }

}

function onDragEnd(cardSprite, gameUX) {
    var playedMove = false;
    var bump = gameUX.bump;
    if (cardSprite.card.turn_played == -1) {
        if(!bump.hit(cardSprite, gameUX.handContainer) && cardSprite.card.card_type == "Spell" && !cardSprite.card.needs_targets) {
            gameUX.gameRoom.sendPlayMoveEvent("SELECT_CARD_IN_HAND", {"card":cardSprite.card.id});
            playedMove = true;
        } else if(bump.hit(cardSprite, gameUX.inPlay) && cardSprite.card.card_type == "Entity" && cardSprite.card.can_be_clicked) {
            gameUX.gameRoom.sendPlayMoveEvent("SELECT_CARD_IN_HAND", {"card":cardSprite.card.id});
            playedMove = true;
        } else if(bump.hit(cardSprite, gameUX.artifacts) && cardSprite.card.card_type == "Artifact" && cardSprite.card.can_be_clicked) {
            gameUX.gameRoom.sendPlayMoveEvent("SELECT_CARD_IN_HAND", {"card":cardSprite.card.id});
            playedMove = true;
        } else if(bump.hit(cardSprite, gameUX.opponentAvatar) && cardSprite.card.card_type == "Spell" && gameUX.opponent(gameUX.game).can_be_clicked) {
            gameUX.gameRoom.sendPlayMoveEvent("SELECT_OPPONENT", {});
            playedMove = true;
        } else if(bump.hit(cardSprite, gameUX.playerAvatar) && cardSprite.card.card_type == "Spell" && gameUX.thisPlayer(gameUX.game).can_be_clicked) {
            gameUX.gameRoom.sendPlayMoveEvent("SELECT_SELF", {});
            playedMove = true;
        } else {
            for (let sprite of gameUX.app.stage.children) {
                if(sprite.card && sprite.card.turn_played != -1  && sprite.card.id != cardSprite.card.id && sprite.card.can_be_clicked && bump.hit(cardSprite, sprite)) {
                    if (sprite.card.card_type == "Entity") {
                        gameUX.gameRoom.sendPlayMoveEvent("SELECT_ENTITY", {"card": sprite.card.id});
                    } else if (sprite.card.card_type == "Artifact") {
                        gameUX.gameRoom.sendPlayMoveEvent("SELECT_ARTIFACT", {"card": sprite.card.id});
                    } else {
                        console.log("tried to select unknown card type: " + sprite.card.card_type);
                    }
                    playedMove = true;
                }
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
    cardSprite.filters = [];
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
            if (entity.card) {
                if (entity.card.can_be_clicked) {
                    entity.filters = []
                } else {
                    entity.filters = [new AdjustmentFilter({ brightness: .8,})];                                        
                }                
                if(entity.card.turn_played != -1 && entity.card.id != cardSprite.card.id && entity.card.can_be_clicked && bump.hit(cardSprite, entity)) {
                    collidedEntity = entity;
                }
            }
        }

        if(!handCollision && cardSprite.card.card_type == "Spell" && !cardSprite.card.needs_targets) {
            cardSprite.filters = [
              new GlowFilter({ distance: 15, outerStrength: 2 , color: 0xffff00}),
              new DropShadowFilter({ distance: 15, outerStrength: 2 }),
            ];
            if (!cardSprite.card.can_be_clicked) {
                cardSprite.filters.append(new AdjustmentFilter({ brightness: .8,}));                        
            }
        } else if(!bump.hit(cardSprite, gameUX.artifacts) && cardSprite.card.card_type == "Artifact" && cardSprite.card.effects[0] && cardSprite.card.effects[0].target_type == "all") {
            cardSprite.filters = [
              new GlowFilter({ distance: 15, outerStrength: 2 , color: 0xffff00}),
              new DropShadowFilter({ distance: 15, outerStrength: 2 }),
            ];
        } else if((cardSprite.card.card_type == "Spell" || cardSprite.card.card_type == "Artifact") && opponentCollision && gameUX.opponent(gameUX.game).can_be_clicked) {
            gameUX.opponentAvatar.filters = [
              new GlowFilter({ distance: 15, outerStrength: 2 , color: 0xffff00}),
            ];
        } else if((cardSprite.card.card_type == "Spell" || cardSprite.card.card_type == "Artifact") && selfCollision && gameUX.thisPlayer(gameUX.game).can_be_clicked) {
            gameUX.playerAvatar.filters = [
              new GlowFilter({ distance: 15, outerStrength: 2 , color: 0xffff00}),
            ];
        } else if(cardInHand && inPlayCollision && cardSprite.card.card_type == "Entity") {
            cardSprite.filters = [
              new GlowFilter({ distance: 15, outerStrength: 2 , color: 0xffff00}),
              new DropShadowFilter({ distance: 15, outerStrength: 2 }),
            ];
            if (!cardSprite.card.can_be_clicked) {
                cardSprite.filters.append(new AdjustmentFilter({ brightness: .8,}));                        
            }
        } else if(cardInHand && artifactsCollision && cardSprite.card.card_type == "Artifact") {
            cardSprite.filters = [
              new GlowFilter({ distance: 15, outerStrength: 2 , color: 0xffff00}),
              new DropShadowFilter({ distance: 15, outerStrength: 2 }),
            ];
        } else if(!cardInHand && opponentCollision && cardSprite.card.card_type == "Entity") {
            cardSprite.filters = [
              new GlowFilter({ distance: 15, outerStrength: 2 , color: 0xffff00}),
              new DropShadowFilter({ distance: 15, outerStrength: 2 }),
            ];
            gameUX.opponentAvatar.filters = [
              new GlowFilter({ distance: 15, outerStrength: 2 , color: 0xffff00}),
            ];

            if (!cardSprite.card.can_be_clicked) {
                cardSprite.filters.append(new AdjustmentFilter({ brightness: .8,}));                        
            }
        } else if (collidedEntity && collidedEntity.card.can_be_clicked) {
            collidedEntity.filters = [
              new GlowFilter({ distance: 15, outerStrength: 2 , color: 0xffff00}),
            ];
        } else {
            gameUX.inPlay.filters = [];
            if (!cardSprite.card.can_be_clicked) {
                cardSprite.filters = [
                    new DropShadowFilter({ distance: 15, outerStrength: 2 }),
                ];
            } else {
                cardSprite.filters = [
                    new DropShadowFilter({ distance: 15, outerStrength: 2 }),
                    new AdjustmentFilter({ brightness: .8,})
                ];
            }
        }
        // if (!collidedEntity) {
        //     for (let opponentEntity of gameUX.opponentSprites) {
        //         // todo don't kill filters for stuff like shield
         //        opponentEntity.filters = [];
        //     }
        // }

        if (!opponentCollision || !gameUX.opponent(gameUX.game).can_be_clicked) {
            if (gameUX.opponent(gameUX.game).can_be_clicked) {
                gameUX.opponentAvatar.filters = [];
            } else {
                gameUX.opponentAvatar.filters = [new AdjustmentFilter({ brightness: .8,})]; 
            }
        }

        if (!selfCollision || !gameUX.thisPlayer(gameUX.game).can_be_clicked) {
            if (gameUX.thisPlayer(gameUX.game).can_be_clicked) {
                gameUX.playerAvatar.filters = [];
            } else {
                gameUX.playerAvatar.filters = [new AdjustmentFilter({ brightness: .8,})]; 
            }
        }

    }
}




