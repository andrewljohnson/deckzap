class CoFXGame {
    constructor(username, info) {
        this.username = username;
        if (info) {
            this.players = info["players"].map(e => (new CoFXPlayer(e)));            
        }
    }

    thisPlayer() {
        for(let player of this.players) {
            if (player.username == this.username) {
                return player
            }
        }
    }

    opponent() {
        for(let player of this.players) {
            if (player.username != this.username) {
                return player
            }
        }
    }
}

class CoFXPlayer {
    constructor(info) {
        this.username = info["username"];
        this.hit_points = info["hit_points"];            
        this.mana = info["mana"];   
        this.hand = info["hand"].map(e => (new CoFXCard(e)))          
        this.in_play = info["in_play"].map(e => (new CoFXCard(e)))          
    }
}

class CoFXCard {
    constructor(info) {
        this.id = info["id"];
        this.name = info["name"];
        this.power = info["power"];            
        this.toughness = info["toughness"];            
        this.cost = info["cost"];            
        this.damage = info["damage"];            
        this.turn_played = info["turn_played"];            
        this.card_type = info["card_type"];            
        this.description = info["description"];            
        this.effects = info["effects"];            
    }
}

class GamePainter {

    static lastSelectedCard = null;
    static lastSelectedCardInHand = null;

    static username = document.getElementById("data_store").getAttribute("username");

    static updateUsername(game) {
        document.getElementById("username").innerHTML = game.thisPlayer().username + " (me)";
    }

    static updateHitPoints(game) {
        document.getElementById("hit_points").innerHTML = game.thisPlayer().hit_points + " hp";
    }

    static updateMana(game) {
        document.getElementById("mana").innerHTML = game.thisPlayer().mana + " mana";
    }

    static updateOpponentUsername(game) {
        document.getElementById("opponent_username").innerHTML = game.opponent().username + " (opponent)";
    }

    static updateOpponentHitPoints(game) {
        document.getElementById("opponent_hit_points").innerHTML = game.opponent().hit_points + " hp";
    }

    static updateOpponentMana(game) {
        document.getElementById("opponent_mana").innerHTML = game.opponent().mana + " mana";
    }
    static updateOpponentCardCount(game) {
        document.getElementById("opponent_card_count").innerHTML = game.opponent().hand.length + " cards";                    
    }

    static updateHand(game) {
        let handDiv = document.getElementById("hand");
        handDiv.innerHTML = '';
        for (let card of game.thisPlayer().hand) {
            handDiv.appendChild(GamePainter.cardSprite(card, GamePainter.username));
        }
    }

    static updateInPlay(game) {
        var inPlayDiv = document.getElementById("in_play");
        inPlayDiv.innerHTML = '';
        for (let card of game.thisPlayer().in_play) {
            inPlayDiv.appendChild(GamePainter.cardSprite(card, GamePainter.username));
        }        
    }

    static updateOpponentInPlay(game) {
        let opponentInPlayDiv = document.getElementById("opponent_in_play");
        opponentInPlayDiv.innerHTML = '';
        for (let card of game.opponent().in_play) {
            opponentInPlayDiv.appendChild(GamePainter.cardSprite(card, GamePainter.username));
        }
    }

    static enableEndTurnButton() {
        document.getElementById("end-turn-button").style.backgroundColor = "red";
        document.getElementById("end-turn-button").style.pointerEvents = "auto";
    }

    static disableEndTurnButton() {
        document.getElementById("end-turn-button").style.backgroundColor = "lightgray";
        document.getElementById("end-turn-button").style.pointerEvents = "none";
    }
   
    static enableInPlayEntities() {
        for (let childCardDiv of document.getElementById("in_play").children) {
            childCardDiv.style.backgroundColor = "red";
        }
    }

    static showDamage(game, target) {
        var avatar = "opponent";
        if (target == game.opponent().username) {
            avatar = "player1";
        }
        document.getElementById(avatar).style.backgroundColor = "red";
        setTimeout(function() {
            document.getElementById(avatar).style.backgroundColor = "lightgray";
        }, 400);
        if (game.opponent().hit_points <= 0 || game.thisPlayer().hit_points <= 0) {
            alert("GAME OVER");
        }
    }

    static disableCardAfterAttack(game, attackingPlayer) {
        var container = "opponent_in_play"
        if (attackingPlayer == game.thisPlayer().username) {
            container = "in_play";
        }
        for (let childCardDiv of document.getElementById(container).children) {
            if (childCardDiv.id == "card_"+data["card"]) {
                childCardDiv.style.backgroundColor = "gray";
            }
        }
    }

    static selectEntity(game, selectingPlayer, card_id) {
        if (selectingPlayer == game.opponent().username) {
            for (let childCardDiv of document.getElementById("opponent_in_play").children) {
                if (childCardDiv.id == "card_"+card_id) {
                    childCardDiv.style.backgroundColor = "orange";
                }
            }
        }
    }
    static playEntity(game, card, playingPlayer) {
        if (playingPlayer == game.thisPlayer().username) {
            document.getElementById("in_play").appendChild(document.getElementById("card_"+card.id)); 
        } else {
            let cardDiv = GamePainter.cardSprite(card, GamePainter.username)
            document.getElementById("opponent_in_play").appendChild(cardDiv);                         
        }
    }


    static cardSprite(card, username) {
        let cardDiv = document.createElement("div");
        cardDiv.id = "card_" + card.id;
        cardDiv.style = 'height:100px;width:75px;background-color:red;border-width: 1px;border-color: white;border-style: solid;border-radius:4px;padding:5px';

        let nameDiv = document.createElement("div");
        nameDiv.innerHTML = card.name;
        cardDiv.appendChild(nameDiv)

        let costDiv = document.createElement("div");
        costDiv.innerHTML = "Cost: " + card.cost;
        cardDiv.appendChild(costDiv)

        let cardTypeDiv = document.createElement("div");
        cardTypeDiv.innerHTML = card.card_type;
        cardDiv.appendChild(cardTypeDiv)

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
                if (card.card_type == "Entity") {
                    GameRoom.sendPlayMoveEvent("PLAY_CARD", {"card":card.id});
                } else {
                    if (cardDiv.style.backgroundColor == "orange")   {
                        cardDiv.style.backgroundColor = "red";                
                        GamePainter.lastSelectedCardInHand = null;
                        if (card.name == "Think") {           
                            var effect_targets = {};
                            effect_targets[card.effects[0].id] = GamePainter.username;
                            GameRoom.sendPlayMoveEvent("PLAY_CARD", {"card":card.id, "effect_targets": effect_targets});
                        }
                    } else {
                        cardDiv.style.backgroundColor = "orange";                
                        GamePainter.lastSelectedCardInHand = cardDiv;
                    }
                }                          
            }
            if (cardDiv.parentElement == document.getElementById("in_play")) {    
                if (cardDiv.style.backgroundColor == "darkgray") {
                    // do nothing, already attacked
                    GamePainter.lastSelectedCard = null;
                } else if (cardDiv.style.backgroundColor == "orange")   {
                    GameRoom.sendPlayMoveEvent("ATTACK", {"card":card.id});
                    cardDiv.style.backgroundColor = "darkgray";                
                    GamePainter.lastSelectedCard = null;
                } else {
                    if (card.turn_played != -1) {
                        cardDiv.style.backgroundColor = "orange";                
                        GamePainter.lastSelectedCard = cardDiv;
                        GameRoom.sendPlayMoveEvent("SELECT_ENTITY", {"card":card.id});
                    }
                }                 
            }
            if (GamePainter.lastSelectedCard && cardDiv.parentElement == document.getElementById("opponent_in_play")) {
                GameRoom.sendPlayMoveEvent("ATTACK", {"defending_card":card.id, "card":parseInt(GamePainter.lastSelectedCard.id.slice(5))});
            }    

            if (GamePainter.lastSelectedCardInHand
                && (cardDiv.parentElement == document.getElementById("opponent_in_play") || cardDiv.parentElement == document.getElementById("in_play"))) {
                var effect_targets = {};
                effect_targets[card.effects[0].id] = cardDiv.id.slice(5);
                GameRoom.sendPlayMoveEvent("PLAY_CARD", {"card":GamePainter.lastSelectedCardInHand.id.slice(5), "effect_targets": effect_targets});
            }    
        };
        return cardDiv;
    }

    static opponentClick () {
        console.log("click opponent");
        if (GamePainter.lastSelectedCard) {
            if (GamePainter.lastSelectedCard.style.backgroundColor == "orange") {
                GamePainter.lastSelectedCard.style.backgroundColor = "gray";
                GameRoom.sendGameEventForDivId("ATTACK", {}, lastSelectedCard.id);
                GamePainter.lastSelectedCard.style.backgroundColor = "darkgray";                
                GamePainter.lastSelectedCard = null;
                GamePainter.lastSelectedCardInHand = null;
            }
        } else if (GamePainter.lastSelectedCardInHand) {
            if (GamePainter.lastSelectedCardInHand.style.backgroundColor == "orange") {
                GameRoom.sendGameEventForDivId("PLAY_CARD", {"target_player":document.getElementById("opponent_username").innerHTML}, GamePainter.lastSelectedCardInHand.id);
                GamePainter.lastSelectedCardInHand.style.backgroundColor = "red";                
                GamePainter.lastSelectedCard = null;
                GamePainter.lastSelectedCardInHand = null;
            }
        }
    }

    static viewHelp() {
        alert("1. Click cards in hand to play them.\n2. To attack, click your entity, then your opponent's.\n3. To attack your opponent's face, double click an entity or click your entity then the opponent.\n4. To cast a spell at your opponent's entity, click your spell, then your opponent's entity.\n5. To cast a spell at your opponent's face, click a spell or click a spell then the opponent.\n6. Entities can't attack the turn they come into play.");
    }
}


class GameRoom {

    static gameSocket = null;

    static connect() {
        if (GameRoom.gameSocket == null) {
            GameRoom.setupSocket();
        }
        if (GameRoom.gameSocket.readyState == WebSocket.OPEN) {
            console.log('WebSockets connection created.');
            GameRoom.sendPlayMoveEvent("JOIN", {});
        } else {
            setTimeout(function () {
            GameRoom.connect();
            }, 100);
        }
    }

    static setupSocket() {
        const roomCode = document.getElementById("data_store").getAttribute("room_code");
        const url = new URL(window.location.href);
        var protocol = url.protocol == 'https:' ? 'wss://' : 'ws://';
        var connectionString = protocol + window.location.host + '/ws/play/' + roomCode + '/';
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
                    var url = location.host + location.pathname;
                    var roomNumber = parseInt(url.split( '/' ).pop()) + 1;
                    var usernameParameter = GameRoom.getSearchParameters()["username"];
                    var nextRoomUrl = "/play/" + roomNumber + "?username=" + usernameParameter;
                    if (data["username"] == usernameParameter) {
                       window.location.href = nextRoomUrl;
                    } else {
                        setTimeout(function(){
                            window.location.href = nextRoomUrl;
                        }, 100); 
                    }
                    break;
                case "PLAY_MOVE":
                    let event_type = data["event_type"];
                    switch (event_type) {
                        case "JOIN":
                            if ("game" in data) {
                                // joining an existing game
                                var game = new CoFXGame(GamePainter.username, data["game"]);
                                if (game.players.length == 2 && GamePainter.username == game.players[0].username) {
                                    GameRoom.sendPlayMoveEvent("START_TURN", {})
                                }         
                                if (game.opponent()) {
                                    GamePainter.updateOpponentUsername(game);
                                    GamePainter.updateOpponentHitPoints(game);
                                    GamePainter.updateOpponentCardCount(game);
                                }
                                GamePainter.updateUsername(game);
                                GamePainter.updateHitPoints(game);
                            }
                                break;
                        case "START_TURN":
                            var game = new CoFXGame(GamePainter.username, data["game"]);
                            GamePainter.updateHand(game);
                            if (data["username"] == game.thisPlayer().username) {
                                GamePainter.enableEndTurnButton();
                                GamePainter.enableInPlayEntities();
                            }
                            GamePainter.updateOpponentCardCount(game);
                            GamePainter.updateOpponentMana(game);
                            GamePainter.updateMana(game);

                            // refresh cards so turn_played gets set for summoning sickness
                            GamePainter.updateInPlay(game);

                            break;
                        case "END_TURN":
                                var game = new CoFXGame(GamePainter.username, data["game"]);
                                if (data["username"] == game.opponent().username) {
                                    GameRoom.sendPlayMoveEvent("START_TURN", {})
                                }
                            break;
                        case "ATTACK":
                            if (data["defending_card"]) {
                                GamePainter.updateInPlay(game);
                                GamePainter.updateOpponentInPlay(game);
                            } else {
                                var game = new CoFXGame(GamePainter.username, data["game"]);
                                GamePainter.updateOpponentHitPoints(game);
                                GamePainter.updateHitPoints(game);
                                GamePainter.showDamage(game, data["username"]);
                            }
                            GamePainter.disableCardAfterAttack(game, data["username"]);
                            break;
                        case "SELECT_ENTITY":
                            var game = new CoFXGame(GamePainter.username, data["game"]);
                            GamePainter.selectEntity(game, data["username"], data["card"]);
                            break;
                        case "PLAY_CARD":
                            var game = new CoFXGame(GamePainter.username, data["game"]);
                            if (game.opponent().hit_points <= 0 || game.thisPlayer().hit_points <= 0) {
                                alert("GAME OVER");
                            }
                            GamePainter.updateOpponentCardCount(game);
                            GamePainter.updateOpponentMana(game);
                            GamePainter.updateMana(game);
                            GamePainter.updateOpponentHitPoints(game);
                            GamePainter.updateHitPoints(game);

                            let card = new CoFXCard(data["card"]);
                            if (card.card_type == "Entity") {
                                GamePainter.playEntity(game, card, data["username"]);
                            } else {                        
                                GamePainter.updateInPlay(game);
                                GamePainter.updateOpponentInPlay(game);
                            }
                            GamePainter.updateHand(game);
                            break;
                }
                default:
                    console.log("No event")
            }
        };
    }

    static getSearchParameters() {
        var prmstr = window.location.search.substr(1);
        return prmstr != null && prmstr != "" ? GameRoom.transformToAssocArray(prmstr) : {};
    }

    static transformToAssocArray( prmstr ) {
        var params = {};
        var prmarr = prmstr.split("&");
        for ( var i = 0; i < prmarr.length; i++) {
            var tmparr = prmarr[i].split("=");
            params[tmparr[0]] = tmparr[1];
        }
        return params;
    }

    static sendPlayMoveEvent(event_type, info) {
        info["event_type"] = event_type
        info["username"] = GamePainter.username
        GameRoom.gameSocket.send(JSON.stringify({
            "event": "PLAY_MOVE", 
            "message": info
        }));                
    }

    static sendGameEventForDivId(event_type, info, div_card_id) {
        info["event_type"] = event_type
        info["card"] = parseInt(div_card_id.slice(5))
        info["username"] = GamePainter.username
        GameRoom.gameSocket.send(JSON.stringify({
            "event": "PLAY_MOVE",
            "message": info
        }));
    }

    static nextRoom() {
        GameRoom.gameSocket.send(JSON.stringify({
            "event": "NEXT_ROOM",
            "message": {"username":GamePainter.username}
        }));
    }

    static endTurn() {
        GamePainter.lastSelectedCard = null;
        GamePainter.lastSelectedCardInHand = null;
        GamePainter.disableEndTurnButton();
        GameRoom.sendPlayMoveEvent("END_TURN", {});
    }
}