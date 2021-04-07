class GameUX {

    static lastSelectedCard = null;
    static lastSelectedCardInHand = null;

    static username = document.getElementById("data_store").getAttribute("username");
    static gameType = document.getElementById("data_store").getAttribute("game_type");

    static thisPlayer(game) {
        for(let player of game.players) {
            if (player.username == GameUX.username) {
                return player
            }
        }
    }

    static opponent(game) {
        for(let player of game.players) {
            if (player.username != GameUX.username) {
                return player
            }
        }
    }

    static updateUsername(game) {
        document.getElementById("username").innerHTML = GameUX.thisPlayer(game).username + " (me)";
    }

    static updateHitPoints(game) {
        document.getElementById("hit_points").innerHTML = GameUX.thisPlayer(game).hit_points + " hp";
    }

    static updateMana(game) {
        document.getElementById("mana").innerHTML = GameUX.thisPlayer(game).mana + " mana";
    }

    static updateOpponentUsername(game) {
        GameUX.opponentUsername = GameUX.opponent(game).username;
        document.getElementById("opponent_username").innerHTML = GameUX.opponent(game).username + " (opponent)";
    }

    static updateOpponentHitPoints(game) {
        document.getElementById("opponent_hit_points").innerHTML = GameUX.opponent(game).hit_points + " hp";
    }

    static updateOpponentMana(game) {
        document.getElementById("opponent_mana").innerHTML = GameUX.opponent(game).mana + " mana";
    }
    static updateOpponentCardCount(game) {
        document.getElementById("opponent_card_count").innerHTML = GameUX.opponent(game).hand.length + " cards";                    
    }
    static updateTurnLabel(game) {
        if (game.turn % 2 == 0 && GameUX.username == game.players[0].username
            || game.turn % 2 == 1 && GameUX.username == game.players[1].username) {
            document.getElementById("turn_label").innerHTML = "Turn " + game.turn;                                
        } else {
            document.getElementById("turn_label").innerHTML = "Turn " + game.turn;                                
        }
    }
    static updateHand(game) {
        let handDiv = document.getElementById("hand");
        handDiv.innerHTML = '';
        for (let card of GameUX.thisPlayer(game).hand) {
            handDiv.appendChild(GameUX.cardSprite(game, card, GameUX.username));
        }
    }

    static updateInPlay(game) {
        var inPlayDiv = document.getElementById("in_play");
        inPlayDiv.innerHTML = '';
        for (let card of GameUX.thisPlayer(game).in_play) {
            inPlayDiv.appendChild(GameUX.cardSprite(game, card, GameUX.username));
        }        
    }

    static updateOpponentInPlay(game) {
        let opponentInPlayDiv = document.getElementById("opponent_in_play");
        opponentInPlayDiv.innerHTML = '';
        for (let card of GameUX.opponent(game).in_play) {
            opponentInPlayDiv.appendChild(GameUX.cardSprite(game, card, GameUX.username));
        }
    }

    static enableEndTurnButton() {
        document.getElementById("end-turn-button").style.backgroundColor = "red";
        document.getElementById("end-turn-button").style.pointerEvents = "auto";
        document.getElementById("end-turn-button").innerHTML = "End Turn";
    }

    static updateForEndTurn() {
        GameUX.lastSelectedCard = null;
        GameUX.lastSelectedCardInHand = null;
        document.getElementById("end-turn-button").style.backgroundColor = "lightgray";
        document.getElementById("end-turn-button").style.pointerEvents = "none";
        document.getElementById("end-turn-button").innerHTML = "Opponent's Turn";
    }
   
    static enableInPlayEntities() {
        for (let childCardDiv of document.getElementById("in_play").children) {
            childCardDiv.style.backgroundColor = "red";
        }
    }

    static showDamage(game, target) {
        var avatar = "opponent";
        if (target == GameUX.opponent(game).username) {
            avatar = "player1";
        }
        document.getElementById(avatar).style.backgroundColor = "red";
        setTimeout(function() {
            document.getElementById(avatar).style.backgroundColor = "lightgray";
        }, 400);
        if (GameUX.opponent(game).hit_points <= 0 || GameUX.thisPlayer(game).hit_points <= 0) {
            alert("GAME OVER");
        }
    }

    static disableCardAfterAttack(game, attackingPlayer, attackingCard) {
        var container = "opponent_in_play"
        if (attackingPlayer == GameUX.thisPlayer(game).username) {
            container = "in_play";
        }
        for (let childCardDiv of document.getElementById(container).children) {
            if (childCardDiv.id == "card_"+attackingCard) {
                childCardDiv.style.backgroundColor = "gray";
            }
        }
    }

    static selectEntity(game, selectingPlayer, card_id) {
        if (selectingPlayer == GameUX.opponent(game).username) {
            for (let childCardDiv of document.getElementById("opponent_in_play").children) {
                if (childCardDiv.id == "card_"+card_id) {
                    childCardDiv.style.backgroundColor = "orange";
                }
            }
        }
    }

    static cardSprite(game, card, username) {
        let cardDiv = document.createElement("div");
        cardDiv.id = "card_" + card.id;
        cardDiv.effects = card.effects;
        cardDiv.style = 'cursor: pointer;height:120px;width:75px;background-color:red;border-width: 1px;border-color: white;border-style: solid;border-radius:4px;padding:5px;font-size:12px';

        let nameDiv = document.createElement("b");
        nameDiv.innerHTML = card.name;
        cardDiv.appendChild(nameDiv)

        if (card.card_type != "Effect") {
            let costDiv = document.createElement("div");
            costDiv.innerHTML = "Cost: " + card.cost;
            cardDiv.appendChild(costDiv)

            let cardTypeDiv = document.createElement("div");
            cardTypeDiv.innerHTML = card.card_type;
            cardDiv.appendChild(cardTypeDiv)            
        }

        if (card.description) {
            let descriptionDiv = document.createElement("div");
            descriptionDiv.innerHTML = card.description;
            cardDiv.appendChild(descriptionDiv);
        }

        if (card.card_type == "Entity") {
            let powerToughnessDiv = document.createElement("div");
            powerToughnessDiv.innerHTML = card.power + "/" + (card.toughness - card.damage);
            cardDiv.appendChild(powerToughnessDiv);
        }

        cardDiv.onclick = function() { 
            if (cardDiv.parentElement == document.getElementById("hand")) {  
                GameUX.lastSelectedCard = null;
                if (card.card_type == "Entity") {
                    GameRoom.sendPlayMoveEvent("PLAY_CARD", {"card":card.id});
                    GameUX.lastSelectedCardInHand = null;
                } else {
                    if (cardDiv.style.backgroundColor == "orange")   {
                        cardDiv.style.backgroundColor = "red";                
                        GameUX.lastSelectedCardInHand = null;
                        if (card.name == "Think") {           
                            var effect_targets = {};
                            effect_targets[card.effects[0].id] = {"id": GameUX.username, "target_type":"player"};
                            GameRoom.sendPlayMoveEvent("PLAY_CARD", {"card":card.id, "effect_targets": effect_targets});
                        } else if (card.name == "Make Entity" || card.name == "Make Spell" || card.name == "Make Global Effect") {     
                            var effect_targets = {};
                            effect_targets[card.effects[0].id] = {"id": GameUX.username, "target_type":"player"};
                            GameRoom.sendPlayMoveEvent("PLAY_CARD", {"card":card.id, "effect_targets": effect_targets});
                        }
                    } else {
                        cardDiv.style.backgroundColor = "orange";                
                        GameUX.lastSelectedCardInHand = cardDiv;
                    }
                }                          
            }
            if (cardDiv.parentElement == document.getElementById("in_play")) {    
                GameUX.lastSelectedCard = null;
                if (cardDiv.style.backgroundColor == "darkgray") {
                    // do nothing, already attacked
                } else if (cardDiv.style.backgroundColor == "orange")   {
                    GameRoom.sendPlayMoveEvent("ATTACK", {"card":card.id});
                    cardDiv.style.backgroundColor = "darkgray";                
                    GameUX.lastSelectedCard = null;
                } else {
                    if (card.turn_played < game.turn) {
                        cardDiv.style.backgroundColor = "orange";                
                        GameUX.lastSelectedCard = cardDiv;
                        GameRoom.sendPlayMoveEvent("SELECT_ENTITY", {"card":card.id});
                    }
                }                 
            }
            if (GameUX.lastSelectedCard && cardDiv.parentElement == document.getElementById("opponent_in_play")) {
                GameRoom.sendPlayMoveEvent("ATTACK", {"defending_card":card.id, "card":parseInt(GameUX.lastSelectedCard.id.slice(5))});
                GameUX.lastSelectedCard = null;
            }    

            if (GameUX.lastSelectedCardInHand
                && (cardDiv.parentElement == document.getElementById("opponent_in_play") || cardDiv.parentElement == document.getElementById("in_play"))) {
                var effect_targets = {};
                effect_targets[GameUX.lastSelectedCardInHand.effects[0].id] = {"id": parseInt(cardDiv.id.slice(5)), "target_type":"entity"};
                
                // hack for siz pop
                if (GameUX.lastSelectedCardInHand.effects.length == 2) {
                    effect_targets[GameUX.lastSelectedCardInHand.effects[1].id] = {"id": GameUX.username, "target_type":"player"};
                }
                GameRoom.sendPlayMoveEvent("PLAY_CARD", {"card":parseInt(GameUX.lastSelectedCardInHand.id.slice(5)), "effect_targets": effect_targets});
                GameUX.lastSelectedCardInHand = null;
            }    
        };
        return cardDiv;
    }

    static opponentClick () {
        if (GameUX.lastSelectedCard) {
            if (GameUX.lastSelectedCard.style.backgroundColor == "orange") {
                GameUX.lastSelectedCard.style.backgroundColor = "gray";
                GameRoom.sendPlayMoveEvent("ATTACK", {"card":parseInt(GameUX.lastSelectedCard.id.slice(5))});
                GameUX.lastSelectedCard.style.backgroundColor = "darkgray";                
                GameUX.lastSelectedCard = null;
                GameUX.lastSelectedCardInHand = null;
            }
        } else if (GameUX.lastSelectedCardInHand) {
            if (GameUX.lastSelectedCardInHand.style.backgroundColor == "orange") {
                var effect_targets = {};
                effect_targets[GameUX.lastSelectedCardInHand.effects[0].id] = {"id": GameUX.opponentUsername, "target_type":"player"};

                // hack for siz pop
                if (GameUX.lastSelectedCardInHand.effects.length == 2) {
                    effect_targets[GameUX.lastSelectedCardInHand.effects[1].id] = {"id": GameUX.username, "target_type":"player"};
                }

                GameRoom.sendPlayMoveEvent("PLAY_CARD", {"card":parseInt(GameUX.lastSelectedCardInHand.id.slice(5)), "effect_targets": effect_targets});
                GameUX.lastSelectedCardInHand.style.backgroundColor = "red";                
                GameUX.lastSelectedCard = null;
                GameUX.lastSelectedCardInHand = null;
            }
        }
    }

    static viewHelp() {
        alert("1. Click cards in hand to play them.\n2. To attack, click your entity, then your opponent's.\n3. To attack your opponent's face, double click an entity or click your entity then the opponent.\n4. To cast a spell at your opponent's entity, click your spell, then your opponent's entity.\n5. To cast a spell at your opponent's face, click a spell or click a spell then the opponent.\n6. Entities can't attack the turn they come into play.");
    }

    static updateForGameStart(game) {
        if (GameUX.opponent(game)) {
            GameUX.updateOpponentUsername(game);
            GameUX.updateOpponentHitPoints(game);
            GameUX.updateOpponentCardCount(game);
        }
        if (GameUX.thisPlayer(game)) {
            GameUX.updateUsername(game);
            GameUX.updateHitPoints(game);
        }
    }

    static updateForStartTurn(game) {
        GameUX.updateHand(game);
        if (game.turn % 2 == 0 && GameUX.username == game.players[0].username
            || game.turn % 2 == 1 && GameUX.username == game.players[1].username) {
            GameUX.enableEndTurnButton();
            GameUX.enableInPlayEntities();
        } else {
            GameUX.updateForEndTurn();            
        }
        GameUX.updateOpponentCardCount(game);
        GameUX.updateOpponentMana(game);
        GameUX.updateMana(game);
        GameUX.updateTurnLabel(game);

        // refresh cards so turn_played gets set for summoning sickness
        GameUX.updateInPlay(game);
    }

    static updateForAttack(game, attackingUser, attackingCard, defendingCard) {
        if (defendingCard) {
            GameUX.updateInPlay(game);
            GameUX.updateOpponentInPlay(game);
        } else {
            GameUX.updateOpponentHitPoints(game);
            GameUX.updateHitPoints(game);
            GameUX.showDamage(game, attackingUser);
        }
        GameUX.disableCardAfterAttack(game, attackingUser, attackingCard);
    }

    static updateForPlayCard(game) {
        if (GameUX.opponent(game).hit_points <= 0 || GameUX.thisPlayer(game).hit_points <= 0) {
            alert("GAME OVER");
        }
        GameUX.updateOpponentCardCount(game);
        GameUX.updateOpponentMana(game);
        GameUX.updateMana(game);
        GameUX.updateOpponentHitPoints(game);
        GameUX.updateHitPoints(game);

        GameUX.updateInPlay(game);
        GameUX.updateOpponentInPlay(game);
        GameUX.updateHand(game);
    }
    
    static showCardSelectionView(cards, game, username) {
        document.getElementById("room").style.display = "none";
        document.getElementById("card_selector").innerHTML = "";
        var cardSelector = document.getElementById("card_selector");
        cardSelector.style.display = "block";
        for (var card of cards) {
            var cs = GameUX.cardSprite(card, game, username);
            cs.onclick = function () {
                alert("choose card " + card.name);
            };
            cardSelector.appendChild(cs);
        }

    }

    static showFXSelectionView(game, decks) {
        document.getElementById("room").style.display = "none";
        document.getElementById("fx_selector").innerHTML = "";
        var fxSelector = document.getElementById("fx_selector");
        fxSelector.style.display = "block";

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
        var td = document.createElement("td");
        td.style.border = "1px solid black";
        td.innerHTML = "Name";
        tr.appendChild(td);
        var td = document.createElement("td");
        td.style.border = "1px solid black";
        td.innerHTML = "Power";
        tr.appendChild(td);
        var td = document.createElement("td");
        td.style.border = "1px solid black";
        td.innerHTML = "Toughness";
        tr.appendChild(td);
        var td = document.createElement("td");
        td.style.border = "1px solid black";
        td.innerHTML = "Cost";
        tr.appendChild(td);
        var td = document.createElement("td");
        td.style.border = "1px solid black";
        td.style.color = 'blue';
        td.innerHTML = "# In Deck";
        tr.appendChild(td);
        table.appendChild(tr);

        for(var c of cards) {
            if (c.card_type != "Entity") {
                continue;
            }
            GameUX.addRowToTableForCard(c, decks, table);
        }   

        table = document.createElement("table");
        table.style.width = "45%";
        table.id = "spell_table";
        fxSelector.appendChild(table);

        th = document.createElement("th");
        th.innerHTML = "Spells";
        table.appendChild(th);

        var tr = document.createElement("tr");
        var td = document.createElement("td");
        td.style.border = "1px solid black";
        td.innerHTML = "Name";
        tr.appendChild(td);
        var td = document.createElement("td");
        td.style.border = "1px solid black";
        td.innerHTML = "Description";
        tr.appendChild(td);
        var td = document.createElement("td");
        td.style.border = "1px solid black";
        td.innerHTML = "Cost";
        tr.appendChild(td);
        var td = document.createElement("td");
        td.style.border = "1px solid black";
        td.style.color = 'blue';
        td.innerHTML = "# In Deck";
        tr.appendChild(td);
        table.appendChild(tr);

        for(var c of cards) {
            if (c.card_type != "Spell") {
                continue;
            }
            GameUX.addRowToTableForCard(c, decks, table);
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
        var td = document.createElement("td");
        td.style.border = "1px solid black";
        td.innerHTML = "Choose 1";
        tr.appendChild(td);
        var td = document.createElement("td");
        td.style.border = "1px solid black";
        td.innerHTML = "Effect";
        tr.appendChild(td);

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
            var td = document.createElement("td");
            td.style.border = "1px solid black";
            td.appendChild(input);
            tr.appendChild(td);

            var td = document.createElement("td");
            td.style.border = "1px solid black";
            td.appendChild(label);
            tr.appendChild(td);

        }  

        var button = document.createElement("button");
        button.id = "startGameButton";
        button.innerHTML = "Start Game";
        button.disabled = true;
        button.style  = "width:250px;height:100px;margin-top:30px;background-color:lightgray;color:white;font-size:24px"
        button.onclick = function() {
            this.disabled = true;
            button.style.backgroundColor = "lightgray"
            button.innerHTML = "Waiting for Opponent...";
            GameRoom.chooseEffect(game, GameUX.startingEffectId) 
        };
        fxSelector.appendChild(button);
    }

    static addRowToTableForCard(c, decks, table) {
        var input = document.createElement("input");
        input.id = c.name;
        input.name = "card";
        input.style.color = 'blue';
        input.value = 1;
        if (GameUX.username in decks) {
            if (c.name in decks[GameUX.username]) {
               input.value = decks[GameUX.username][c.name];
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
        document.getElementById("room").style.display = "none";
        document.getElementById("make_selector").innerHTML = "";
        var makeSelector = document.getElementById("make_selector");
        makeSelector.style.display = "block";

        var cards = GameUX.thisPlayer(game).make_to_resolve;

        var h1 = document.createElement("h1");
        h1.innerHTML = "Make a Card"
        makeSelector.appendChild(h1);
        makeSelector.appendChild(document.createElement('br'));
        makeSelector.appendChild(document.createElement('br'));

        var cardContainerDiv = document.createElement('div');
        cardContainerDiv.classList.add("card_container");
        makeSelector.appendChild(cardContainerDiv);

        for (let card of cards) {
            let cardDiv = GameUX.cardSprite(game, card, GameUX.username);
            cardContainerDiv.appendChild(cardDiv);
            cardDiv.onclick = function() {
                if (card.starting_effect) {
                    GameRoom.sendPlayMoveEvent("MAKE_EFFECT", {"card":card});
                } else {
                    GameRoom.sendPlayMoveEvent("MAKE_CARD", {"card_name":card.name});
                }
            };
        }
    }

}



class GameRoom {

    static gameSocket = null;

    static connect() {
        if (GameRoom.gameSocket == null) {
            GameRoom.setupSocket();
        }
        if (GameRoom.gameSocket.readyState == WebSocket.OPEN) {
            GameRoom.sendPlayMoveEvent("JOIN", {});
            console.log('WebSockets connection created.');
        } else {
            setTimeout(function () {
                GameRoom.connect();
            }, 100);
        }
    }

    static setupSocket() {
        const gameType = document.getElementById("data_store").getAttribute("game_type");
        const roomCode = document.getElementById("data_store").getAttribute("room_code");
        const url = new URL(window.location.href);
        var protocol = url.protocol == 'https:' ? 'wss://' : 'ws://';
        var connectionString = protocol + window.location.host + '/ws/play/' + gameType + '/' + roomCode + '/';
        GameRoom.gameSocket = new WebSocket(connectionString);

        GameRoom.gameSocket.onclose = function (e) {
            console.log('Socket is closed. Reconnect will be attempted in 1 second.', e.reason);
            setTimeout(function () {
                GameRoom.connect();
            }, 1000);
        };

        GameRoom.gameSocket.onmessage = function (e) {
            let data = JSON.parse(e.data)["payload"];
            let event = data["event"];

            switch (event) {
                case "NEXT_ROOM":
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

                    var url = location.host + location.pathname;
                    var roomNumber = parseInt(url.split( '/' ).pop()) + 1;
                    var usernameParameter = getSearchParameters()["username"];
                    var nextRoomUrl = "/play/" + GameUX.gameType + '/' + roomNumber + "?username=" + usernameParameter;
                    if (data["username"] == usernameParameter) {
                       window.location.href = nextRoomUrl;
                    } else {
                        setTimeout(function(){
                            window.location.href = nextRoomUrl;
                        }, 100); 
                    }
                    break;
                case "PLAY_MOVE":
                    let move_type = data["move_type"];
                    var game = "game" in data ? data["game"] : null;
                    switch (move_type) {
                        case "CHOOSE_STARTING_EFFECT":
                            if (game.starting_effects.length == 2) {
                                GameUX.showGame();
                                if (GameUX.username == game.players[0].username) {
                                    GameRoom.sendPlayMoveEvent("START_TURN", {})
                                }
                            }
                            break
                        case "JOIN":
                            if (game) {
                                if (game.players.length == 2 && GameUX.username == game.players[0].username) {
                                    if (GameUX.gameType == "deckbuilder") {
                                           GameRoom.sendPlayMoveEvent("START_TURN", {})                                        
                                    } else {  // ccg
                                        if (game.starting_effects.length != 2) {
                                          GameRoom.sendPlayMoveEvent("ENTER_FX_SELECTION", {})
                                        } else {
                                           GameRoom.sendPlayMoveEvent("START_TURN", {})                                        
                                        }                                        
                                    }
                                }
                                GameUX.updateForGameStart(game);         
                            }
                            break;
                        case "START_TURN":
                            GameUX.updateForStartTurn(game);
                            break;
                        case "END_TURN":
                            if (data["username"] == GameUX.opponent(game).username) {
                                GameRoom.sendPlayMoveEvent("START_TURN", {})
                            }
                            break;
                        case "ATTACK":
                            GameUX.updateForAttack(game, data["username"], data["attacking_card"], data["defending_card"]);
                            break;
                        case "SELECT_ENTITY":
                            GameUX.selectEntity(game, data["username"], data["card"]);
                            break;
                        case "PLAY_CARD":
                            GameUX.updateForPlayCard(game);
                            if (data["is_make_effect"] && data["username"] == GameUX.username) {
                                GameUX.showMakeView(game);
                            }
                            break;
                        case "MAKE_EFFECT":
                        case "MAKE_CARD":
                            if (data["username"] == GameUX.thisPlayer(game).username) {
                                GameUX.showGame();
                            }
                            GameUX.updateHand(game);
                            GameUX.updateOpponentCardCount(game);
                            break;
                        case "ENTER_FX_SELECTION":
                            GameUX.showFXSelectionView(game, data["decks"]);
                            break;
                        break;
                    }
                    break;
                default:
                    console.log("No event")
            }
        };
    }

    static sendPlayMoveEvent(move_type, info) {
        info["move_type"] = move_type
        info["username"] = GameUX.username
        GameRoom.gameSocket.send(JSON.stringify({
            "event": "PLAY_MOVE", 
            "message": info
        }));                
    }

    // methods on buttons in game.html

    static nextRoom() {
        GameRoom.gameSocket.send(JSON.stringify({
            "event": "NEXT_ROOM",
            "message": {"username":GameUX.username}
        }));
    }

    static endTurn() {
        GameUX.updateForEndTurn();
        GameRoom.sendPlayMoveEvent("END_TURN", {});
    }

    static chooseEffect(game, effect_id) {
        var info = {"id": effect_id, "card_counts":{}};
        for(var c of game.all_cards) {
            var input = document.getElementById(c.name);
            info["card_counts"][c.name] = input.value
        }
        GameRoom.sendPlayMoveEvent("CHOOSE_STARTING_EFFECT", info);
    }
}