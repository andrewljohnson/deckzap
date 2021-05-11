const appWidth = 840;
const appHeight = 800;
const cardHeight = 114;
const cardWidth = 80;
const padding = 10;
const avatarHeight = 128;
const avatarWidth = 300;
const brownColor = 0x765C48;
const lightBrownColor = 0xDFBF9F;
const cardContainerWidth = cardWidth * 7 + 12;

const bump = new Bump(PIXI);
var cardTexture = PIXI.Texture.from('/static/images/card.png');
var inPlayTexture = PIXI.Texture.from('/static/images/in_play.png');
var handTexture = PIXI.Texture.from('/static/images/hand.png');
var artifactsTexture = PIXI.Texture.from('/static/images/relics.png');
var avatarTexture = PIXI.Texture.from('/static/images/avatar.png');
var menuTexture = PIXI.Texture.from('/static/images/menu.png');
var newGameButtonTexture = PIXI.Texture.from('/static/images/menu-button.png');
 
var bearTexture = PIXI.Texture.from('/static/images/bear.png');
var tigerTexture = PIXI.Texture.from('/static/images/tiger.png');

class GameUX {

    constructor() {
        this.aiType = document.getElementById("data_store").getAttribute("ai_type");
        this.allCards = JSON.parse(document.getElementById("card_store").getAttribute("all_cards"));
        this.gameType = document.getElementById("data_store").getAttribute("game_type");
        this.username = document.getElementById("data_store").getAttribute("username");
        this.oldOpponentArmor = 0;
        this.oldOpponentHP = 30;
        this.oldSelfArmor = 0;        
        this.oldSelfHP = 30;        

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

    cardSprite(game, card, username, index, parent, dont_attach_listeners) {
        let cardSprite = new PIXI.Sprite.from(cardTexture);
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
            filters.push(new PIXI.filters.AdjustmentFilter({ brightness: .8}));                        
        }
        if (card.shielded && card.turn_played > -1) {
            filters.push(new PIXI.filters.GlowFilter({color: 0xffff00}));                        
        }

        if (card.abilities.length > 0 && card.abilities[0].descriptive_id == "Lurker" && card.abilities[0].enabled && card.turn_played > -1) {
            filters.push(new PIXI.filters.GlowFilter({color: 0x000000}));                        
        }

        cardSprite.filters = filters;


        if (dont_attach_listeners) {
            return cardSprite;
        }

        if (card.can_be_clicked) {
            var self = this;
            cardSprite
                .on('mousedown',        function (e) {onDragStart(e, this, self)})
                .on('touchstart',       function (e) {onDragStart(e, this, self)})
                .on('mouseup',          function ()  {onDragEnd(this, self)})
                .on('mouseupoutside',   function ()  {onDragEnd(this, self)})
                .on('touchend',         function ()  {onDragEnd(this, self)})
                .on('touchendoutside',  function ()  {onDragEnd(this, self)})
                .on('mousemove',        function ()  {onDragMove(this, self, game)})
                .on('touchmove',        function ()  {onDragMove(this, self, game)})
        }

        return cardSprite;
    }

    usernameOrP1(game) {
        if (this.username == game.players[0].username || this.username == game.players[1].username) {
            return this.username;
        }
        return game.players[0].username;
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
    }

    background() {
        const background = new PIXI.Sprite.from(PIXI.Texture.WHITE);
        background.width = appWidth;
        background.height = appHeight;
        background.tint = 0xEEEEEE;
        return background;
    }

    newGameButton(x, y, gameUX) {
        const b = new PIXI.Sprite.from(newGameButtonTexture);
        b.buttonMode = true;
        b.position.x = x;
        b.position.y = y;
        // b.anchor.set(0.5);
        b.interactive = true;
        var clickFunction = function() {
            gameUX,gameRoom.nextRoom()
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
        const avatar = new PIXI.Sprite.from(avatarTexture);
        avatar.position.x = x;
        avatar.position.y = y;
        return avatar;
    }

    artifacts(x, y) {
        const artifacts = new PIXI.Sprite.from(artifactsTexture);
        artifacts.position.x = x;
        artifacts.position.y = y;
        return artifacts;
    }

    inPlayContainer(x, y) {
        const inPlayContainer = new PIXI.Sprite.from(inPlayTexture);
        inPlayContainer.position.x = x;
        inPlayContainer.position.y = y;
        return inPlayContainer;
    }

    hand(x, y) {
        const handContainer = new PIXI.Sprite.from(handTexture);
        handContainer.position.x = x;
        handContainer.position.y = y;
        return handContainer;
    }

    menu(x, y) {
        const menu = new PIXI.Sprite.from(menuTexture);
        menu.position.x = x;
        menu.position.y = y;
        return menu;
    }

    refresh(game, message) {
        this.removeCardsFromStage(game)

        if (this.thisPlayer(game)) {
            this.updateHand(game);
            if (message["show_spell"]) {
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

        if (true) {
            this.renderEndTurnButton(game);
        }
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
      var godray = new PIXI.filters.GodrayFilter();
      var incrementGodrayTime = () => {
        godray.time += this.app.ticker.elapsedMS / 1000;
      }
      let sprite = this.cardSprite(game, card, this.usernameOrP1(game), 0, null);
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
        if (this.endTurnButton) {
            this.buttonMenu.removeChild(this.endTurnButton)
        }

        const b = new PIXI.Sprite.from(newGameButtonTexture);
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
            avatar = new PIXI.Sprite.from(bearTexture);
        } else {
            avatar = new PIXI.Sprite.from(tigerTexture);
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

        let armor = new PIXI.Text(player.hit_points + " armor", props);
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
            avatarSprite.filters = [new PIXI.filters.AdjustmentFilter({ brightness: .8,})];                        
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
            let sprite = this.cardSprite(game, card, this.usernameOrP1(game), index, this.handContainer);
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
            if (player.card_info_to_resolve["card_id"] && card.id == player.card_info_to_resolve["card_id"]) {
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
            let sprite = this.cardSprite(game, card, this.usernameOrP1(game), index, inPlaySprite);
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
            let sprite = this.cardSprite(game, card, this.usernameOrP1(game), index, artifactsSprite);
            artifactsSprite.addChild(sprite);
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
        new PIXI.filters.DropShadowFilter({ distance: 15, outerStrength: 2 }),
    ];

    if (card.card.turn_played == -1) {
        if(card.card.card_type == "Spell" && card.card.needs_targets) {
            gameUX.gameRoom.sendPlayMoveEvent("SELECT_CARD_IN_HAND", {"card":card.card.id});
        } 
    } else if (card.card.card_type == "Entity") {
        gameUX.gameRoom.sendPlayMoveEvent("SELECT_ENTITY", {"card":card.card.id});
    }

}

function onDragEnd(cardSprite, gameUX) {
    var playedMove = false;
    if (cardSprite.card.turn_played == -1) {
        if(!bump.hit(cardSprite, gameUX.handContainer) && cardSprite.card.card_type == "Spell" && !cardSprite.card.needs_targets) {
            gameUX.gameRoom.sendPlayMoveEvent("SELECT_CARD_IN_HAND", {"card":cardSprite.card.id});
            playedMove = true;
        } else if(bump.hit(cardSprite, gameUX.inPlay) && cardSprite.card.card_type == "Entity" && cardSprite.card.can_be_clicked) {
            gameUX.gameRoom.sendPlayMoveEvent("SELECT_CARD_IN_HAND", {"card":cardSprite.card.id});
            playedMove = true;
        } else {
            for (let entity of gameUX.app.stage.children) {
                if(entity.card && entity.card.id != cardSprite.card.id && entity.card.can_be_clicked && bump.hit(cardSprite, entity)) {
                    gameUX.gameRoom.sendPlayMoveEvent("SELECT_ENTITY", {"card": entity.card.id});
                    playedMove = true;
                }
            }
        }
    } else {  // it's an entity or artifact already in play
        if(bump.hit(cardSprite, gameUX.opponentAvatar)) {
            gameUX.gameRoom.sendPlayMoveEvent("SELECT_OPPONENT", {});
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

function onDragMove(cardSprite, gameUX, game) {
    if (cardSprite.dragging) {
        var newPosition = cardSprite.data.getLocalPosition(cardSprite.parent);
        cardSprite.position.x = newPosition.x;
        cardSprite.position.y = newPosition.y;
    
        var parent = cardSprite.parent;
        parent.removeChild(cardSprite);
        parent.addChild(cardSprite);

        let opponentCollision = bump.hit(cardSprite, gameUX.opponentAvatar);
        let handCollision = bump.hit(cardSprite, gameUX.handContainer);
        let inPlayCollision = bump.hit(cardSprite, gameUX.inPlay);
        let cardInHand = cardSprite.card.turn_played == -1;

        let collidedEntity = null;
        for (let entity of gameUX.app.stage.children) {
            if(entity.card  && entity.card.turn_played != -1 && entity.card.id != cardSprite.card.id && entity.card.can_be_clicked && bump.hit(cardSprite, entity)) {
                collidedEntity = entity;
                break;
            }
        }

        if(!handCollision && cardSprite.card.card_type == "Spell" && !cardSprite.card.needs_targets) {
            cardSprite.filters = [
              new PIXI.filters.GlowFilter({ distance: 15, outerStrength: 2 , color: 0xffff00}),
              new PIXI.filters.DropShadowFilter({ distance: 15, outerStrength: 2 }),
            ];
            if (!cardSprite.card.can_be_clicked) {
                cardSprite.filters.append(new PIXI.filters.AdjustmentFilter({ brightness: .8,}));                        
            }
        } else if(cardInHand && inPlayCollision && cardSprite.card.card_type == "Entity") {
            cardSprite.filters = [
              new PIXI.filters.GlowFilter({ distance: 15, outerStrength: 2 , color: 0xffff00}),
              new PIXI.filters.DropShadowFilter({ distance: 15, outerStrength: 2 }),
            ];
            if (!cardSprite.card.can_be_clicked) {
                cardSprite.filters.append(new PIXI.filters.AdjustmentFilter({ brightness: .8,}));                        
            }
        } else if(!cardInHand && opponentCollision && cardSprite.card.card_type == "Entity") {
            cardSprite.filters = [
              new PIXI.filters.GlowFilter({ distance: 15, outerStrength: 2 , color: 0xffff00}),
              new PIXI.filters.DropShadowFilter({ distance: 15, outerStrength: 2 }),
            ];
            gameUX.opponentAvatar.filters = [
              new PIXI.filters.GlowFilter({ distance: 15, outerStrength: 2 , color: 0xffff00}),
            ];

            if (!cardSprite.card.can_be_clicked) {
                cardSprite.filters.append(new PIXI.filters.AdjustmentFilter({ brightness: .8,}));                        
            }
        } else if (collidedEntity && collidedEntity.card.can_be_clicked) {
            collidedEntity.filters = [
              new PIXI.filters.GlowFilter({ distance: 15, outerStrength: 2 , color: 0xffff00}),
            ];
        } else {
            gameUX.inPlay.filters = [];
            if (!cardSprite.card.can_be_clicked) {
                cardSprite.filters = [
                    new PIXI.filters.DropShadowFilter({ distance: 15, outerStrength: 2 }),
                ];
            } else {
                cardSprite.filters = [
                    new PIXI.filters.DropShadowFilter({ distance: 15, outerStrength: 2 }),
                    new PIXI.filters.AdjustmentFilter({ brightness: .8,})
                ];
            }
        }
        // if (!collidedEntity) {
        //     for (let opponentEntity of gameUX.opponentSprites) {
        //         // todo don't kill filters for stuff like shield
         //        opponentEntity.filters = [];
        //     }
        // }

        // if (!opponentCollision) {
        //     gameUX.opponentAvatar.filters = [];
        // }

    }
}




/*

const gameLog = PIXI.Sprite.from(PIXI.Texture.WHITE);
gameLog.width = appWidth;
gameLog.height = cardHeight *1.25;
gameLog.tint = 0xAAAAAA;
gameLog.position.x = padding;
gameLog.position.y = handContainer.position.y + handContainer.height - padding;
stage.addChild(gameLog);


*/
