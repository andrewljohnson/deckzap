class GameUX {

    static username = document.getElementById("data_store").getAttribute("username");
    static gameType = document.getElementById("data_store").getAttribute("game_type");
    static oldOpponentHP = 30;
    static oldSelfHP = 30;

    static usernameOrP1(game) {
        if (GameUX.username == game.players[0].username || GameUX.username == game.players[1].username) {
            return GameUX.username;
        }
        return game.players[0].username;
    }


    static thisPlayer(game) {
        for(let player of game.players) {
            if (player.username == GameUX.username) {
                return player
            }
        }
        return game.players[0];
    }

    static opponent(game) {
        let thisPlayer = GameUX.thisPlayer(game);
        if (thisPlayer == game.players[1]) {
            return game.players[0];
        }
        return game.players[1];
    }

    static updateUsername(game) {
        document.getElementById("username").innerHTML = GameUX.thisPlayer(game).username + " (me)";
    }

    static updateHitPoints(game) {
        if(GameUX.thisPlayer(game).hit_points < GameUX.oldSelfHP) {
            GameUX.oldSelfHP = GameUX.thisPlayer(game).hit_points;
            GameUX.showDamage(game, GameUX.opponent(game));            
        }
        document.getElementById("hit_points").innerHTML = GameUX.thisPlayer(game).hit_points + " hp";
    }

    static updateMana(game) {
        document.getElementById("mana").innerHTML = "Mana: " + GameUX.manaString(GameUX.thisPlayer(game).max_mana, GameUX.thisPlayer(game).mana);
    }
    static manaString(maxMana, currentMana) {
        var manaString = "";

        for (var i=0;i<currentMana;i++) {
            manaString += "✦"
        }
        for (var i=0;i<maxMana-currentMana;i++) {
            manaString += "✧"
        }
        return manaString
    }

    static updatePlayerBorder(game) {
        if (GameUX.thisPlayer(game).can_be_targetted && GameUX.isActivePlayer(game)) {
            document.getElementById("player1").style.border = "4px solid orange";    
        } else {            
            document.getElementById("player1").style.border = "4px solid #765C48";    
        }
    }

    static updateOpponentBorder(game) {
        if (GameUX.opponent(game).can_be_targetted && GameUX.isActivePlayer(game)) {
            document.getElementById("opponent").style.border = "4px solid orange";    
        } else {            
            document.getElementById("opponent").style.border = "4px solid #765C48";    
        }
    }

    static updateOpponentUsername(game) {
        GameUX.opponentUsername = GameUX.opponent(game).username;
        document.getElementById("opponent_username").innerHTML = GameUX.opponent(game).username + " (opponent)";
    }

    static updateOpponentHitPoints(game) {
        if(GameUX.opponent(game).hit_points < GameUX.oldOpponentHP) {
            GameUX.oldOpponentHP = GameUX.opponent(game).hit_points;
            GameUX.showDamage(game, GameUX.thisPlayer(game));            
        }
        document.getElementById("opponent_hit_points").innerHTML = GameUX.opponent(game).hit_points + " hp";
    }

    static updateOpponentMana(game) {
        document.getElementById("opponent_mana").innerHTML = "Mana: " + GameUX.manaString(GameUX.opponent(game).max_mana, GameUX.opponent(game).mana);
    }

    static updateOpponentCardCount(game) {
        document.getElementById("opponent_card_count").innerHTML = "Hand: " + GameUX.opponent(game).hand.length + " cards";                    
    }

    static updateDeckCount(game) {
        document.getElementById("deck_count").innerHTML = "Deck: " + GameUX.thisPlayer(game).deck.length + " cards";                    
    }

    static updateOpponentDeckCount(game) {
        document.getElementById("opponent_deck_count").innerHTML = "Deck: " + GameUX.opponent(game).deck.length + " cards";                    
    }

    static updatePlayedPileCount(game) {
        document.getElementById("played_pile_count").innerHTML = "Played: " + GameUX.thisPlayer(game).played_pile.length + " cards";                    
    }

    static updateOpponentPlayedPileCount(game) {
        document.getElementById("opponent_played_pile_count").innerHTML = "Played: " + GameUX.opponent(game).played_pile.length + " cards";                    
    }

    static updateTurnLabel(game) {
        document.getElementById("turn_label").innerHTML = "Turn " + game.turn;                                
    }

    static updateHand(game) {
        let handDiv = document.getElementById("hand");
        handDiv.innerHTML = '';
        for (let card of GameUX.thisPlayer(game).hand) {
            handDiv.appendChild(GameUX.cardSprite(game, card, GameUX.usernameOrP1(game)));
        }
    }

    static updateInPlay(game) {
        var inPlayDiv = document.getElementById("in_play");
        inPlayDiv.innerHTML = '';
        for (let card of GameUX.thisPlayer(game).in_play) {
            inPlayDiv.appendChild(GameUX.cardSprite(game, card, GameUX.usernameOrP1(game)));
        }        
    }

    static updateOpponentInPlay(game) {
        let opponentInPlayDiv = document.getElementById("opponent_in_play");
        opponentInPlayDiv.innerHTML = '';
        for (let card of GameUX.opponent(game).in_play) {
            opponentInPlayDiv.appendChild(GameUX.cardSprite(game, card, GameUX.usernameOrP1(game)));
        }
    }

    static showDamage(game, target) {
        var avatar = "opponent";
        if (target == GameUX.opponent(game)) {
            avatar = "player1";
        }
        document.getElementById(avatar).style.backgroundColor = "red";
        setTimeout(function() {
            document.getElementById(avatar).style.backgroundColor = "#DFBF9F";
        }, 400);
        if (GameUX.opponent(game).hit_points <= 0 || GameUX.thisPlayer(game).hit_points <= 0) {
            alert("GAME OVER");
        }
    }

    static isActivePlayer(game) {
        return (game.turn % 2 == 0 && GameUX.usernameOrP1(game) == game.players[0].username
                || game.turn % 2 == 1 && GameUX.usernameOrP1(game) == game.players[1].username)
    }

    static cardSprite(game, card, username) {
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
        if (GameUX.isActivePlayer(game)) {
            if (card.can_cast) {
                cardDiv.style.border = "3px solid yellow";                
            } else if (card.can_be_targetted) {
                cardDiv.style.border = "3px solid orange";                
            } else if (
                    card.attacked == false 
                    && card.turn_played > -1 
                    && card.turn_played < game.turn 
                    && card.owner_username == GameUX.thisPlayer(game).username) {
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
            costDiv.innerHTML = GameUX.manaString(card.cost, card.cost);
            cardDiv.appendChild(costDiv)
        }

        if (card.description) {
            let descriptionDiv = document.createElement("div");
            descriptionDiv.innerHTML = card.description;
            cardDiv.appendChild(descriptionDiv);
        }

        if (card.card_type == "Entity") {
            if (card.abilities && card.abilities[0].name == "Guard") {
                let abilitiesDiv = document.createElement("div");
                abilitiesDiv.innerHTML = card.abilities[0].name;
                cardDiv.appendChild(abilitiesDiv);
            }

            let powerToughnessDiv = document.createElement("div");
            powerToughnessDiv.innerHTML = card.power + "/" + (card.toughness - card.damage);
            cardDiv.appendChild(powerToughnessDiv);


        }

        cardDiv.onclick = function() { 
            if (cardDiv.parentElement == document.getElementById("hand")) {  
                GameUX.sendPlayMoveEvent("SELECT_CARD_IN_HAND", {"card":card.id});
            } else { 
                GameUX.sendPlayMoveEvent("SELECT_ENTITY", {"card":card.id});
            }
        }
        return cardDiv;
    }

    static selfClick () {
        GameUX.sendPlayMoveEvent("SELECT_SELF", {});
    }

    static opponentClick () {
        GameUX.sendPlayMoveEvent("SELECT_OPPONENT", {});
    }

    static viewHelp() {
        alert("1. Click cards in hand to play them.\n2. To attack, click your entity, then your opponent's.\n3. To attack your opponent's face, double click an entity or click your entity then the opponent.\n4. To cast a spell at your opponent's entity, click your spell, then your opponent's entity.\n5. To cast a spell at your opponent's face, click a spell or click a spell then the opponent.\n6. Entities can't attack the turn they come into play.");
    }
   
    static enableEndTurnButton(game) {
        document.getElementById("end-turn-button").style.backgroundColor = "red";
        if (GameUX.thisPlayer(game).mana == 0) {
            document.getElementById("end-turn-button").style.border = "4px black solid";
        } else {            
            document.getElementById("end-turn-button").style.border = "4px red solid";
        }
        document.getElementById("end-turn-button").style.pointerEvents = "auto";
        document.getElementById("end-turn-button").innerHTML = "End Turn";
    }

    static disableEndTurnButton(game) {
        document.getElementById("end-turn-button").style.border = "4px lightgray solid";
        document.getElementById("end-turn-button").style.backgroundColor = "lightgray";
        document.getElementById("end-turn-button").style.pointerEvents = "none";
        document.getElementById("end-turn-button").innerHTML = "Opponent's Turn";
    }
   
    static refresh(game) {
        if (GameUX.opponent(game)) {
            if (GameUX.isActivePlayer(game)) {
                GameUX.enableEndTurnButton(game);
            } else {
                GameUX.disableEndTurnButton(game);            
            }
            GameUX.updateOpponentCardCount(game);
            GameUX.updateOpponentMana(game);
            GameUX.updateOpponentHitPoints(game);
            GameUX.updateOpponentInPlay(game);
            GameUX.updateOpponentDeckCount(game);
            GameUX.updateOpponentPlayedPileCount(game);
            GameUX.updateOpponentBorder(game);
        }
        if (GameUX.thisPlayer(game)) {
            GameUX.updateMana(game);
            GameUX.updateHitPoints(game);
            GameUX.updateInPlay(game);
            GameUX.updateHand(game);
            GameUX.updateDeckCount(game);
            GameUX.updatePlayedPileCount(game);
            GameUX.updatePlayerBorder(game);
        }
        if (GameUX.opponent(game) && GameUX.thisPlayer(game)) {
            if (GameUX.opponent(game).hit_points <= 0 || GameUX.thisPlayer(game).hit_points <= 0) {
                alert("GAME OVER");
            }
        }
        if (game.decks_to_set && game.starting_effects.length != 2) {
            GameUX.showFXSelectionView(game);
        } else if (GameUX.thisPlayer(game).make_to_resolve.length) {
            GameUX.showMakeView(game);
        } else {
            GameUX.showGame();
        }                           
    }
    
    static showFXSelectionView(game) {
        let decks = game.decks_to_set;
        document.getElementById("fx_selector").innerHTML = "";
        var fxSelector = document.getElementById("fx_selector");
        fxSelector.style.display = "block";
        fxSelector.style.backgroundColor = "white";

        var cards = game.all_cards;

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
        tr.appendChild(tdForTitle("Power"));
        tr.appendChild(tdForTitle("Toughness"));
        tr.appendChild(tdForTitle("Cost"));
        tr.appendChild(tdForTitle("Power"));
        var td = tdForTitle("# In Deck");
        td.style.color = 'blue';
        td.style.border = "1px solid black";
        tr.appendChild(td);
        table.appendChild(tr);

        for(var c of cards) {
            if (c.card_type != "Entity") {
                continue;
            }
            GameUX.addRowToTableForCard(game, c, decks, table);
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
        td.style.color = 'blue';
        td.style.border = "1px solid black";
        tr.appendChild(td);
        table.appendChild(tr);

        for(var c of cards) {
            if (c.card_type != "Spell") {
                continue;
            }
            GameUX.addRowToTableForCard(game, c, decks, table);
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

        for(var o of options) {
            var input = document.createElement("input");
            input.type = "radio";
            input.id = o.id;
            input.name = "effect";
            input.value = o.id;
            input.onclick = function() { 
                GameUX.startingEffectId = this.id;
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
            GameUX.chooseEffect(game, GameUX.startingEffectId) 
        };
        fxSelector.appendChild(button);
    }

    static addRowToTableForCard(game, c, decks, table) {
        var input = document.createElement("input");
        input.id = c.name;
        input.name = "card";
        input.style.color = 'blue';
        input.value = 1;
        if (GameUX.usernameOrP1(game) in decks) {
            if (c.name in decks[GameUX.usernameOrP1(game)]) {
               input.value = decks[GameUX.usernameOrP1(game)][c.name];
            }
        }
        input.style.width = "50px";

        var label = document.createElement("b"); 
        label.for = c.id;
        label.innerHTML = c.name;

        var tr = document.createElement("tr");
        var tdName = document.createElement("td");
        tdName.style.border = "1px solid black";
        tdName.appendChild(label)
        tr.appendChild(tdName);
        if (c.card_type == "Entity") {
            var tdPower = document.createElement("td");
            tdPower.innerHTML = c.power;
            tdPower.style.border = "1px solid black";
            tr.appendChild(tdPower);            

            var tdToughness = document.createElement("td");
            tdToughness.innerHTML = c.toughness;
            tdToughness.style.border = "1px solid black";
            tr.appendChild(tdToughness);            
        }

        if (c.description) {
            var tdDescription = document.createElement("td");
            tdDescription.innerHTML = c.description;
            tdDescription.style.border = "1px solid black";
            tr.appendChild(tdDescription);                        
        }

        var tdCost = document.createElement("td");
        tdCost.innerHTML = c.cost;
        tdCost.style.border = "1px solid black";
        tr.appendChild(tdCost);            

        var tdAmount = document.createElement("td");
        tdAmount.appendChild(input)
        tr.appendChild(tdAmount);
        table.appendChild(tr);
    }

    static showGame() {
        document.getElementById("room").style.display = "block";
        document.getElementById("fx_selector").style.display = "none";
        document.getElementById("make_selector").style.display = "none";
    }

    static showMakeView(game) {
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

        var cards = GameUX.thisPlayer(game).make_to_resolve;

        var h1 = document.createElement("h1");
        h1.innerHTML = "Make a Card"
        container.appendChild(h1);
        container.appendChild(document.createElement('br'));
        container.appendChild(document.createElement('br'));

        var cardContainerDiv = document.createElement('div');
        cardContainerDiv.classList.add("card_container");
        container.appendChild(cardContainerDiv);

        for (let card of cards) {
            let cardDiv = GameUX.cardSprite(game, card, GameUX.usernameOrP1(game));
            cardContainerDiv.appendChild(cardDiv);
            cardDiv.onclick = function() {
                if (card.starting_effect) {
                    GameUX.sendPlayMoveEvent("MAKE_EFFECT", {"card":card});
                } else {
                    GameUX.sendPlayMoveEvent("MAKE_CARD", {"card_name":card.name});
                }
            };
        }
    }

    static addLogLine() {
        var line = document.createElement('div');
        document.getElementById("game_log_inner").appendChild(line);
        return line;
    }

    static scrollLogToEnd() {
        document.getElementById("game_log_inner").scrollTop = document.getElementById("game_log_inner").scrollHeight;
    }

    static endTurn() {
        GameUX.sendPlayMoveEvent("END_TURN", {});
    }

    static chooseEffect(game, effect_id) {
        var info = {"id": effect_id, "card_counts":{}};
        for(var c of game.all_cards) {
            var input = document.getElementById(c.name);
            info["card_counts"][c.name] = input.value
        }
        GameUX.sendPlayMoveEvent("CHOOSE_STARTING_EFFECT", info);
    }

    static logMessage(game, data) {
        let move_type = data["move_type"];
        var line = GameUX.addLogLine();
        switch (move_type) {
            case "CHOOSE_STARTING_EFFECT":
                line.innerHTML = data.username + " chooses starting effect \"" + data["id"].replace(/_/g, " ") +"\"";
                break
            case "JOIN":
                line.innerHTML = data.username + " joins";
                if (game.players.length == 1) {
                    line.innerHTML += "<br/><div>Waiting for opponent...</div>"
                }
                break;
            case "START_TURN":
                line.innerHTML = data.username + "'s turn " + "(turn " + game.turn + ")";
                break;
            case "ATTACK":
                if (data["defending_card"]) {
                    line.innerHTML = data.username + " attacks with " + data["card"]["name"] + " into " + data["defending_card"]["name"];
                } else {
                    line.innerHTML = data.username + " attacks with " + data["card"]["name"];
                }
                break;
            case "PLAY_CARD":
                if (data["played_card"]) {
                    line.innerHTML = data.username + " plays " + data["card"]["name"];
                }
                if (data["was_countered"]) {
                    line.innerHTML += "<br/>COUNTERSPELL from " + data["counter_username"] + " stops " + data["card"]["name"] + ". Boom sucka!";
                } 
               break;
            case "MAKE_EFFECT":
                line.innerHTML = data.username + " makes " + data["card"]["starting_effect"];
                break;
            case "ENTER_FX_SELECTION":
                line.innerHTML = "Entering effect selection";
                break;
            break;
        }
        GameUX.scrollLogToEnd()
    }

    static nextRoom() {
        GameRoom.gameSocket.send(JSON.stringify({
            "event": "NEXT_ROOM",
            "message": {"username":GameUX.username}
        }));
    }

    static sendPlayMoveEvent(move_type, info) {
        info["move_type"] = move_type
        info["username"] = GameUX.username
        GameRoom.gameSocket.send(JSON.stringify({
            "event": "PLAY_MOVE", 
            "message": info
        }));                
    }

}


class GameRoom {

    static gameSocket = null;

    static connect() {
        if (GameRoom.gameSocket == null) {
            GameRoom.setupSocket();
        }
        if (GameRoom.gameSocket.readyState == WebSocket.OPEN) {
            GameUX.sendPlayMoveEvent("JOIN", {});
            console.log('WebSockets connection created.');
        } else {
            setTimeout(function () {
                GameRoom.connect();
            }, 100);
        }
    }

    static setupSocket() {
        GameRoom.gameSocket = new WebSocket(GameRoom.roomSocketUrl());

        GameRoom.gameSocket.onclose = function (e) {
            console.log('Socket is closed. Reconnect will be attempted in 1 second.', e.reason);
            setTimeout(function () {
                GameRoom.connect();
            }, 1000);
        };

        GameRoom.gameSocket.onmessage = function (e) {
            let data = JSON.parse(e.data)["payload"];
            switch (data["event"]) {
                case "NEXT_ROOM":
                    var usernameParameter = getSearchParameters()["username"];
                    if (data["username"] == usernameParameter) {
                       window.location.href = GameRoom.nextRoomUrl();
                    } else {
                        setTimeout(function(){
                            window.location.href = GameRoom.nextRoomUrl();
                        }, 100); 
                    }
                    break;
                case "PLAY_MOVE":
                    let game = data["game"];
                    GameUX.refresh(game);
                    GameUX.logMessage(game, data);
                    break;
                default:
                    console.log("No event")
            }
        };
    }

    static roomSocketUrl() {
        const roomCode = document.getElementById("data_store").getAttribute("room_code");
        const url = new URL(window.location.href);
        var protocol = url.protocol == 'https:' ? 'wss://' : 'ws://';
        var connectionString = protocol + window.location.host + '/ws/play/' + GameUX.gameType + '/' + roomCode + '/';

        const isCustom = document.getElementById("data_store").getAttribute("is_custom");
        const customGameId = document.getElementById("data_store").getAttribute("custom_game_id");
        if (isCustom != "False") {
            connectionString = protocol + window.location.host + '/ws/play_custom/' + customGameId + '/' + roomCode + '/';
        }
        return connectionString;
    }

    static nextRoomUrl() {
        var url = location.host + location.pathname;
        var roomNumber = parseInt(url.split( '/' ).pop()) + 1;
        var usernameParameter = getSearchParameters()["username"];
        var nextRoomUrl = "/play/" + GameUX.gameType + '/' + roomNumber + "?username=" + usernameParameter;
        const isCustom = document.getElementById("data_store").getAttribute("is_custom");
        const customGameId = document.getElementById("data_store").getAttribute("custom_game_id");
        if (isCustom != "False") {
            nextRoomUrl = "/play/custom/" + customGameId + '/' + roomNumber + "?username=" + usernameParameter;
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