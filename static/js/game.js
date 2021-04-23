class GameUX {

    constructor() {
        this.username = document.getElementById("data_store").getAttribute("username");
        this.gameType = document.getElementById("data_store").getAttribute("game_type");
        this.aiType = document.getElementById("data_store").getAttribute("ai_type");
        this.allCards = JSON.parse(document.getElementById("card_store").getAttribute("all_cards"));
        this.oldOpponentHP = 30;
        this.oldSelfHP = 30;        
    }

    usernameOrP1(game) {
        if (this.username == game.players[0].username || this.username == game.players[1].username) {
            return this.username;
        }
        return game.players[0].username;
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

    updateUsername(game) {
        document.getElementById("username").innerHTML = this.thisPlayer(game).username + " (me)";
    }

    updateRace(game) {
        document.getElementById("race").innerHTML = this.thisPlayer(game).race;
    }

    updateOpponentRace(game) {
        document.getElementById("opponent_race").innerHTML = this.opponent(game).race;
    }

    updateHitPoints(game) {
        if(this.thisPlayer(game).hit_points < this.oldSelfHP) {
            this.oldSelfHP = this.thisPlayer(game).hit_points;
            this.showDamage(game, this.opponent(game));            
        }
        document.getElementById("hit_points").innerHTML = this.thisPlayer(game).hit_points + " hp";
    }

    updateMana(game) {
        document.getElementById("mana").innerHTML = "Mana: " + this.manaString(this.thisPlayer(game).max_mana, this.thisPlayer(game).mana);
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

    updatePlayerBorder(game) {
        if (this.thisPlayer(game).can_be_clicked && this.isActivePlayer(game)) {
            document.getElementById("player1").style.border = "4px solid orange";    
        } else {            
            document.getElementById("player1").style.border = "4px solid #765C48";    
        }
    }

    updateOpponentBorder(game) {
        if (this.opponent(game).can_be_clicked && this.isActivePlayer(game)) {
            document.getElementById("opponent").style.border = "4px solid orange";    
        } else {            
            document.getElementById("opponent").style.border = "4px solid #765C48";    
        }
    }

    updateOpponentUsername(game) {
        this.opponentUsername = this.opponent(game).username;
        document.getElementById("opponent_username").innerHTML = this.opponent(game).username + " (opponent)";
    }

    updateOpponentHitPoints(game) {
        if(this.opponent(game).hit_points < this.oldOpponentHP) {
            this.oldOpponentHP = this.opponent(game).hit_points;
            this.showDamage(game, this.thisPlayer(game));            
        }
        document.getElementById("opponent_hit_points").innerHTML = this.opponent(game).hit_points + " hp";
    }

    updateStartingEffectsForPlayer(player, divId) {
        let div = document.getElementById(divId);
        if (player.starting_effects && player.starting_effects.length > 0) {
            div.innerHTML = "Starting Effects: ";
            for (let effects of player.starting_effects) {
             div.innerHTML += effect.name + " | ";
            }
        } else {
            div.innerHTML = "";            
        }
    }

    updateStartingEffects(game) {
        this.updateStartingEffectsForPlayer(this.thisPlayer(game), "starting_effects");
    }

    updateOpponentStartingEffects(game) {
        this.updateStartingEffectsForPlayer(this.opponent(game), "opponent_starting_effects");
    }

    updateAddedAbilitiesForPlayer(player, divId) {
        let div = document.getElementById(divId);
        if (player.added_abilities.length > 0) {
            div.innerHTML = "Added Abilities: ";
            for (let ability of player.added_abilities) {
             div.innerHTML += ability.name + " | "
            }
        } else {
            div.innerHTML = "";            
        }
    }

    updateAddedAbilities(game) {
        this.updateAddedAbilitiesForPlayer(this.thisPlayer(game), "added_abilities");
    }

    updateOpponentAddedAbilities(game) {
        this.updateAddedAbilitiesForPlayer(this.opponent(game), "opponent_added_abilities");
    }

    updateOpponentMana(game) {
        document.getElementById("opponent_mana").innerHTML = "Mana: " + this.manaString(this.opponent(game).max_mana, this.opponent(game).mana);
    }

    updateOpponentCardCount(game) {
        document.getElementById("opponent_card_count").innerHTML = "Hand: " + this.opponent(game).hand.length + " cards";                    
    }

    updateDeckCount(game) {
        document.getElementById("deck_count").innerHTML = "Deck: " + this.thisPlayer(game).deck.length + " cards";                    
    }

    updateOpponentDeckCount(game) {
        document.getElementById("opponent_deck_count").innerHTML = "Deck: " + this.opponent(game).deck.length + " cards";                    
    }

    updatePlayedPileCount(game) {
        document.getElementById("played_pile_count").innerHTML = "Played: " + this.thisPlayer(game).played_pile.length + " cards";                    
    }

    updateOpponentPlayedPileCount(game) {
        document.getElementById("opponent_played_pile_count").innerHTML = "Played: " + this.opponent(game).played_pile.length + " cards";                    
    }

    updateTurnLabel(game) {
        document.getElementById("turn_label").innerHTML = "Turn " + game.turn;                                
    }

    updateHand(game) {
        let handDiv = document.getElementById("hand");
        handDiv.innerHTML = '';
        for (let card of this.thisPlayer(game).hand) {
            handDiv.appendChild(this.cardSprite(game, card, this.usernameOrP1(game)));
        }
    }

    updateInPlay(game) {
        var inPlayDiv = document.getElementById("in_play");
        inPlayDiv.innerHTML = '';
        for (let card of this.thisPlayer(game).in_play) {
            inPlayDiv.appendChild(this.cardSprite(game, card, this.usernameOrP1(game)));
        }        
    }

    updateOpponentInPlay(game) {
        let opponentInPlayDiv = document.getElementById("opponent_in_play");
        opponentInPlayDiv.innerHTML = '';
        for (let card of this.opponent(game).in_play) {
            opponentInPlayDiv.appendChild(this.cardSprite(game, card, this.usernameOrP1(game)));
        }
    }

    showDamage(game, target) {
        var avatar = "opponent";
        if (target == this.opponent(game)) {
            avatar = "player1";
        }
        document.getElementById(avatar).style.backgroundColor = "red";
        setTimeout(function() {
            document.getElementById(avatar).style.backgroundColor = "#DFBF9F";
        }, 400);
    }

    isActivePlayer(game) {
        return (game.turn % 2 == 0 && this.usernameOrP1(game) == game.players[0].username
                || game.turn % 2 == 1 && this.usernameOrP1(game) == game.players[1].username)
    }

    cardSprite(game, card, username) {
        let cardDiv = document.createElement("div");
        cardDiv.id = "card_" + card.id;
        cardDiv.effects = card.effects;
        cardDiv.style = 'margin-right:2px;cursor: pointer;height:114px;width:71px;border-radius:4px;padding:5px;font-size:12px';
        if (card.attacked) {
            cardDiv.style.backgroundColor = "#C4A484";                
        } else if (card.selected) {
            cardDiv.style.backgroundColor = "orange";                            
        } else {
            cardDiv.style.backgroundColor = "#DFBF9F";            
        }
        if (this.isActivePlayer(game)) {
            if (card.can_be_clicked) {
                cardDiv.style.border = "3px solid yellow";                
            } else {
                cardDiv.style.border = "3px solid #C4A484";                            
            }
        } else {
            cardDiv.style.border = "3px solid #C4A484";                            
        }

        let nameDiv = document.createElement("b");
        nameDiv.innerHTML = card.name;
        cardDiv.appendChild(nameDiv)

        if (card.card_type != "Effect") {
            let costDiv = document.createElement("div");
            costDiv.innerHTML = this.manaString(card.cost, card.cost);
            cardDiv.appendChild(costDiv)
        }

        if (card.description) {
            let descriptionDiv = document.createElement("div");
            descriptionDiv.innerHTML = card.description;
            cardDiv.appendChild(descriptionDiv);
        }
        if (card.added_descriptions.length) {
            for (let d of card.added_descriptions) {
                let descriptionDiv = document.createElement("div");
                descriptionDiv.innerHTML = d;
                cardDiv.appendChild(descriptionDiv);                
            }
        }

        if (card.card_type == "Entity") {
            for (let a of card.abilities) {
                let abilitiesDiv = document.createElement("div");
                abilitiesDiv.innerHTML = card.abilities[0].name;
                cardDiv.appendChild(abilitiesDiv);

            }
            for (let a of card.added_abilities) {
                let abilitiesDiv = document.createElement("div");
                abilitiesDiv.innerHTML = card.added_abilities[0].name;
                cardDiv.appendChild(abilitiesDiv);
                
            }
            let cardPower = card.power;
            let cardToughness = card.toughness - card.damage;
           if (card.tokens) {
            for (let c of card.tokens) {
                cardPower += c.power_modifier;
            }
            for (let c of card.tokens) {
                cardToughness += c.toughness_modifier;
            }
           }
            let powerToughnessDiv = document.createElement("div");
            powerToughnessDiv.innerHTML = cardPower + "/" + cardToughness;
            cardDiv.appendChild(powerToughnessDiv);


        }
        var self = this;
        cardDiv.onclick = function() { 
            if (cardDiv.parentElement == document.getElementById("hand")) {  
                self.sendPlayMoveEvent("SELECT_CARD_IN_HAND", {"card":card.id});
            } else { 
                self.sendPlayMoveEvent("SELECT_ENTITY", {"card":card.id});
            }
        }
        return cardDiv;
    }

    selfClick () {
        this.sendPlayMoveEvent("SELECT_SELF", {});
    }

    opponentClick () {
        this.sendPlayMoveEvent("SELECT_OPPONENT", {});
    }

    viewHelp() {
        alert("1. Click cards in hand to play them.\n2. To attack, click your entity, then your opponent's.\n3. To attack your opponent's face, double click an entity or click your entity then the opponent.\n4. To cast a spell at your opponent's entity, click your spell, then your opponent's entity.\n5. To cast a spell at your opponent's face, click a spell or click a spell then the opponent.\n6. Entities can't attack the turn they come into play.");
    }
   
    enableEndTurnButton(game) {
        document.getElementById("end-turn-button").style.backgroundColor = "red";
        if (this.thisPlayer(game).mana == 0) {
            document.getElementById("end-turn-button").style.border = "4px black solid";
        } else {            
            document.getElementById("end-turn-button").style.border = "4px red solid";
        }
        document.getElementById("end-turn-button").style.pointerEvents = "auto";
        document.getElementById("end-turn-button").innerHTML = "End Turn";
    }

    disableEndTurnButton(game) {
        document.getElementById("end-turn-button").style.border = "4px lightgray solid";
        document.getElementById("end-turn-button").style.backgroundColor = "lightgray";
        document.getElementById("end-turn-button").style.pointerEvents = "none";
        document.getElementById("end-turn-button").innerHTML = "Opponent's Turn";
    }
   
    refresh(game) {
        if (this.opponent(game)) {
            if (this.isActivePlayer(game)) {
                this.enableEndTurnButton(game);
            } else {
                this.disableEndTurnButton(game);            
            }
            this.updateTurnLabel(game);
            this.updateOpponentCardCount(game);
            this.updateOpponentMana(game);
            this.updateOpponentHitPoints(game);
            this.updateOpponentInPlay(game);
            this.updateOpponentDeckCount(game);
            this.updateOpponentPlayedPileCount(game);
            this.updateOpponentBorder(game);
            this.updateOpponentAddedAbilities(game);
            this.updateOpponentStartingEffects(game);
            this.updateOpponentUsername(game);
            this.updateOpponentRace(game);
        }
        if (this.thisPlayer(game)) {
            this.updateMana(game);
            this.updateHitPoints(game);
            this.updateInPlay(game);
            this.updateHand(game);
            this.updateDeckCount(game);
            this.updatePlayedPileCount(game);
            this.updatePlayerBorder(game);
            this.updateStartingEffects(game);
            this.updateAddedAbilities(game);
            this.updateUsername(game);
            this.updateRace(game);
        }
        if (this.opponent(game) && this.thisPlayer(game)) {
            if (this.opponent(game).hit_points <= 0 || this.thisPlayer(game).hit_points <= 0) {
                alert("GAME OVER");
            }
        }
        if (game.decks_to_set && game.starting_effects.length < 2) {
            this.showFXSelectionView(game);
        } else if ((this.gameType == "choose_race" || this.gameType == "choose_race_prebuilt") && (!game.players[0].race || !game.players[1].race)) {
            this.showChooseRace(game);
        } else if (this.thisPlayer(game).make_to_resolve.length) {
            this.showMakeView(game);
        } else {
            this.showGame();
        }                           
    }
    
    showChooseRace(game) {
        var raceSelector = document.getElementById("race_selector");
        if (raceSelector.style.display == "block") {
            return;
        }
        raceSelector.style.display = "block";
        raceSelector.style.backgroundColor = "white";
        document.getElementById("race_selector").innerHTML = "";

        var h1 = document.createElement("h1");
        h1.innerHTML = "Choose Race"
        raceSelector.appendChild(h1);

        var p = document.createElement("p");
        p.innerHTML = "Your race affects what cards you have access to in the game."
        raceSelector.appendChild(p);

        var options = [
            {"id": "elf", "label": "Elf"},
            {"id": "genie", "label": "Genie"},
        ];

        var table = document.createElement("table");
        table.style.width = "100%";
        raceSelector.appendChild(table);
        var th = document.createElement("th");
        th.innerHTML = "Races";
        table.appendChild(th);

        var tr = document.createElement("tr");
        table.appendChild(tr);
        tr.appendChild(tdForTitle("Choose 1"));
        tr.appendChild(tdForTitle("Race"));

        var self = this
        for(var o of options) {
            var input = document.createElement("input");
            input.type = "radio";
            input.id = o.id;
            input.name = "effect";
            input.value = o.id;
            input.onclick = function() { 
                self.race = this.id;
                document.getElementById("startGameButton").disabled = false;
                document.getElementById("startGameButton").style.backgroundColor = "green";
            };

            var label = document.createElement("label"); 
            label.for = o.id;
            label.innerHTML = o.label;
            var tr = document.createElement("tr");
            table.appendChild(tr);
            var td = tdForTitle("");
            td.appendChild(input);
            tr.appendChild(td);
            var td = tdForTitle("");
            td.appendChild(label);
            tr.appendChild(td);
        }  

        var button = document.createElement("button");
        button.id = "startGameButton";
        button.innerHTML = "Start Game";
        button.disabled = true;
        button.classList = ["light-gray-button"];
        var self = this;
        button.onclick = function() {
            this.disabled = true;
            button.style.backgroundColor = "lightgray"
            button.innerHTML = "Waiting for Opponent...";
            self.chooseRace(game, self.race) 
        };
        raceSelector.appendChild(button);
    }

    showFXSelectionView(game) {
        let decks = game.decks_to_set;
        document.getElementById("fx_selector").innerHTML = "";
        var fxSelector = document.getElementById("fx_selector");
        fxSelector.style.display = "block";
        fxSelector.style.backgroundColor = "white";

        h1 = document.createElement("h1");
        h1.innerHTML = "Change Your Deck"
        fxSelector.appendChild(h1);

        var table = document.createElement("table");
        table.style.float = "left";
        table.style.width = "45%";
        table.id = "entity_table";
        fxSelector.appendChild(table);

        var th = document.createElement("th");
        th.innerHTML = "Entities";
        table.appendChild(th);

        var tr = document.createElement("tr");
        tr.appendChild(tdForTitle("Name"));
        tr.appendChild(tdForTitle("Description"));
        tr.appendChild(tdForTitle("Power"));
        tr.appendChild(tdForTitle("Toughness"));
        tr.appendChild(tdForTitle("Cost"));
        var td = tdForTitle("# In Deck");
        td.style.color = '000080';
        td.style.border = "1px solid black";
        tr.appendChild(td);
        table.appendChild(tr);

        for(var c of this.allCards) {
            if (c.card_type == "Spell") {
                continue;
            }
            this.addRowToTableForCard(game, c, decks, table);
        }   

        table = document.createElement("table");
        table.style.width = "45%";
        table.id = "spell_table";
        fxSelector.appendChild(table);

        th = document.createElement("th");
        th.innerHTML = "Spells";
        table.appendChild(th);

        var tr = document.createElement("tr");
        tr.appendChild(tdForTitle("Name"));
        tr.appendChild(tdForTitle("Description"));
        tr.appendChild(tdForTitle("Cost"));
        var td = tdForTitle("# In Deck");
        td.style.color = '000080';
        td.style.border = "1px solid black";
        tr.appendChild(td);
        table.appendChild(tr);

        for(var c of this.allCards) {
            if (c.card_type != "Spell") {
                continue;
            }
            this.addRowToTableForCard(game, c, decks, table);
        }   

        fxSelector.appendChild(document.createElement("br"));
        fxSelector.appendChild(document.createElement("br"));

        var h1 = document.createElement("h1");
        h1.innerHTML = "Choose FX"
        fxSelector.appendChild(h1);

        var p = document.createElement("p");
        p.innerHTML = "Each player chooses one effect that affects everyone's cards."
        fxSelector.appendChild(p);

        var options = [
            {"id": "draw_extra_card", "label": "Players Draw an Extra Card Each Turn"},
            {"id": "spells_cost_less", "label": "Spells Cost 1 Less"},
            {"id": "spells_cost_more", "label": "Spells Cost 1 More"},
            {"id": "entities_cost_less", "label": "Entities Cost 1 Less"},
            {"id": "entities_cost_more", "label": "Entities Cost 1 More"},
            {"id": "entities_get_more_toughness", "label": "Entities Get +0/+2"},
            {"id": "entities_get_less_toughness", "label": "Entities Get +0/-2"},
            {"id": "entities_get_more_power", "label": "Entities Get +2/+0"},
            {"id": "entities_get_less_power", "label": "Entities Get -2/+0"},
        ];

        var table = document.createElement("table");
        table.style.width = "100%";
        fxSelector.appendChild(table);
         var th = document.createElement("th");
        th.innerHTML = "Effects";
        table.appendChild(th);

        var tr = document.createElement("tr");
        table.appendChild(tr);
        tr.appendChild(tdForTitle("Choose 1"));
        tr.appendChild(tdForTitle("Effect"));

        var self = this;
        for(var o of options) {
            var input = document.createElement("input");
            input.type = "radio";
            input.id = o.id;
            input.name = "effect";
            input.value = o.id;
            input.onclick = function() { 
                self.startingEffectId = this.id;
                document.getElementById("startGameButton").disabled = false;
                document.getElementById("startGameButton").style.backgroundColor = "green";
            };

            var label = document.createElement("label"); 
            label.for = o.id;
            label.innerHTML = o.label;
            var tr = document.createElement("tr");
            table.appendChild(tr);
            var td = tdForTitle("");
            td.appendChild(input);
            tr.appendChild(td);
            var td = tdForTitle("");
            td.appendChild(label);
            tr.appendChild(td);
        }  

        var button = document.createElement("button");
        button.id = "startGameButton";
        button.innerHTML = "Start Game";
        button.disabled = true;
        button.classList = ["light-gray-button"];
        button.onclick = function() {
            this.disabled = true;
            button.style.backgroundColor = "lightgray"
            button.innerHTML = "Waiting for Opponent...";
            self.chooseEffect(game, self.startingEffectId) 
        };
        fxSelector.appendChild(button);
    }

    addRowToTableForCard(game, c, decks, table) {
        var input = document.createElement("input");
        input.id = c.name;
        input.name = "card";
        input.style.color = '000080';
        input.value = 1;
        if (this.usernameOrP1(game) in decks) {
            if (c.name in decks[this.usernameOrP1(game)]) {
               input.value = decks[this.usernameOrP1(game)][c.name];
            }
        }
        input.style.width = "50px";

        var label = document.createElement("b"); 
        label.for = c.id;
        label.innerHTML = c.name;

        var tr = document.createElement("tr");
        table.appendChild(tr);

        var tdName = document.createElement("td");
        tdName.style.border = "1px solid black";
        tdName.appendChild(label)
        tr.appendChild(tdName);
        if (c.card_type != "Spell") {
            tr.appendChild(tdForTitle(c.power));            
            tr.appendChild(tdForTitle(c.toughness));            
        }

        tr.appendChild(tdForTitle(c.description));            
        tr.appendChild(tdForTitle(c.cost));            
        var tdAmount = document.createElement("td");
        tdAmount.appendChild(input)
        tr.appendChild(tdAmount);

    }

    showGame() {
        document.getElementById("room").style.display = "block";
        document.getElementById("fx_selector").style.display = "none";
        document.getElementById("race_selector").style.display = "none";
        document.getElementById("make_selector").style.display = "none";
    }

    showMakeView(game) {
        document.getElementById("make_selector").innerHTML = "";
        var makeSelector = document.getElementById("make_selector");
        makeSelector.style.display = "flex";
        makeSelector.style.background = "rgba(0, 0, 0, .7)";

        var container = document.createElement("div");
        container.style.width = 80+ 80*3 + "px";
        container.style.height = 130+50+100 + "px";
        container.style.margin = "auto";
        container.style.backgroundColor = "white";
        makeSelector.appendChild(container);

        var cards = this.thisPlayer(game).make_to_resolve;

        var h1 = document.createElement("h1");
        h1.innerHTML = "Make a Card"
        container.appendChild(h1);
        container.appendChild(document.createElement('br'));
        container.appendChild(document.createElement('br'));

        var cardContainerDiv = document.createElement('div');
        cardContainerDiv.classList.add("card_container");
        container.appendChild(cardContainerDiv);

        var self = this;
        for (let card of cards) {
            let cardDiv = self.cardSprite(game, card, this.usernameOrP1(game));
            cardContainerDiv.appendChild(cardDiv);
            cardDiv.onclick = function() {
                if (card.starting_effect) {
                    self.sendPlayMoveEvent("MAKE_EFFECT", {"card":card});
                } else {
                    self.sendPlayMoveEvent("MAKE_CARD", {"card_name":card.name});
                }
            };
        }
    }

    addLogLine() {
        var line = document.createElement('div');
        document.getElementById("game_log_inner").appendChild(line);
        return line;
    }

    scrollLogToEnd() {
        document.getElementById("game_log_inner").scrollTop = document.getElementById("game_log_inner").scrollHeight;
    }

    endTurn() {
        this.sendPlayMoveEvent("END_TURN", {});
    }

    chooseEffect(game, effect_id) {
        var info = {"id": effect_id, "card_counts":{}};
        for(var c of this.allCards) {
            var input = document.getElementById(c.name);
            info["card_counts"][c.name] = input.value
        }
        this.sendPlayMoveEvent("CHOOSE_STARTING_EFFECT", info);
    }

    chooseRace(game, race) {
        this.sendPlayMoveEvent("CHOOSE_RACE", {"race": race});
    }

    logMessage(log_lines) {
        for (let text of log_lines) {
            var line = this.addLogLine();
            line.innerHTML = text
        }
        this.scrollLogToEnd()
    }

    nextRoom() {
        if (this.gameRoom.gameSocket.readyState != WebSocket.OPEN) {
            window.location.href = this.gameRoom.nextRoomUrl();
        }

        this.gameRoom.gameSocket.send(JSON.stringify(
            {"move_type": "NEXT_ROOM", "username":this.username}
        ));
    }

    sendPlayMoveEvent(move_type, info) {
        info["move_type"] = move_type
        info["username"] = this.username
        this.gameRoom.gameSocket.send(JSON.stringify(
            info
        ));                
    }

}


class GameRoom {

    gameSocket = null;

    constructor(gameUX) {
        this.gameUX = gameUX;
        gameUX.gameRoom = this;
    }

    connect() {
        if (this.gameSocket == null) {
            this.setupSocket();
        }
        if (this.gameSocket.readyState == WebSocket.OPEN) {
            const deck_id = document.getElementById("card_store").getAttribute("deck_id");
            if (deck_id) {
                this.gameUX.sendPlayMoveEvent("JOIN", { deck_id });                
            }
            console.log('WebSockets connection created.');
        } else {
            var self = this;
            setTimeout(function () {
                self.connect();
            }, 100);
        }
    }

    setupSocket() {
        this.gameSocket = new WebSocket(this.roomSocketUrl());

        var self = this;
        this.gameSocket.onclose = function (e) {
            console.log('Socket is closed. Reconnect will be attempted in 1 second.', e.reason);
            setTimeout(function () {
                self.connect();
            }, 1000);
        };

        this.gameSocket.onmessage = function (e) {
            let data = JSON.parse(e.data)["payload"];
            if (data["move_type"] == "NEXT_ROOM") {
                var usernameParameter = getSearchParameters()["username"];
                if (data["username"] == usernameParameter) {
                   window.location.href = self.nextRoomUrl();
                } else {
                    setTimeout(function(){
                        window.location.href = self.nextRoomUrl();
                    }, 100); 
                }
            } else {
                let game = data["game"];
                if (!data["game"]) {
                    console.log(data);                    
                }
                self.gameUX.refresh(game);
                self.gameUX.logMessage(data["log_lines"]);
            }
        };
    }

    roomSocketUrl() {
        const roomCode = document.getElementById("data_store").getAttribute("room_code");
        const url = new URL(window.location.href);
        var protocol = url.protocol == 'https:' ? 'wss://' : 'ws://';
        var connectionString = protocol + window.location.host + '/ws/play/' + this.gameUX.aiType + '/' + this.gameUX.gameType + '/' + roomCode + '/';
        const ai = document.getElementById("data_store").getAttribute("ai");
        if (ai && ai != "None") {
            connectionString += ai + '/';
        }
        const isCustom = document.getElementById("data_store").getAttribute("is_custom");
        const customGameId = document.getElementById("data_store").getAttribute("custom_game_id");
        if (isCustom != "False") {
            connectionString = protocol + window.location.host + '/ws/play_custom/' + customGameId + '/' + roomCode + '/';
        }
        return connectionString;
    }

    nextRoomUrl() {
        var url = location.host + location.pathname;
        var roomNumber = parseInt(url.split( '/' ).pop()) + 1;
        var usernameParameter = getSearchParameters()["username"];
        var nextRoomUrl = "/play/" + this.gameUX.aiType + "/" + this.gameUX.gameType + '/' + roomNumber;
        var getParams =  "?username=" + usernameParameter + "&new_game_from_button=true";
        const ai = document.getElementById("data_store").getAttribute("ai");
        if (ai && ai != "None") {
            getParams += '&ai=' + ai;
        }
        const deck_id = document.getElementById("card_store").getAttribute("deck_id");
        if (deck_id && deck_id != "None") {
            getParams += '&deck_id=' + deck_id;
        }
        nextRoomUrl +=  getParams;
        const isCustom = document.getElementById("data_store").getAttribute("is_custom");
        const customGameId = document.getElementById("data_store").getAttribute("custom_game_id");
        if (isCustom != "False") {
            nextRoomUrl = "/play/custom/" + roomNumber+ '/'  + customGameId + getParams;
        }
        return nextRoomUrl;
    }
}

function tdForTitle(title) {
    var td = document.createElement("td");
    td.style.border = "1px solid black";
    td.innerHTML = title;
    return td;
}

function getSearchParameters() {
    var prmstr = window.location.search.substr(1);
    return prmstr != null && prmstr != "" ? transformToAssocArray(prmstr) : {};
}

function transformToAssocArray( prmstr ) {
    var params = {};
    var prmarr = prmstr.split("&");
    for ( var i = 0; i < prmarr.length; i++) {
        var tmparr = prmarr[i].split("=");
        params[tmparr[0]] = tmparr[1];
    }
    return params;
}