var roomCode = document.getElementById("data_store").getAttribute("room_code");
var username = document.getElementById("data_store").getAttribute("username");

const url = new URL(window.location.href);
var protocol = url.protocol == 'https:' ? 'wss://' : 'ws://';
var connectionString = protocol + window.location.host + '/ws/play/' + roomCode + '/';
const gameSocket = new WebSocket(connectionString);
var lastSelectedCard = null;

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
    }
}

gameSocket.onclose = function (e) {
    console.log('Socket is closed. Reconnect will be attempted in 1 second.', e.reason);
    setTimeout(function () {
        connect();
    }, 1000);
};

gameSocket.onmessage = function (e) {
    let data = JSON.parse(e.data)["payload"];
    let event = data["event"];
    switch (event) {
        case "JOIN":
            if ("game" in data) {
                // joining an existing game
                var game = new CoFXGame(username, data["game"]);
                console.log(game);
                if (!game.thisPlayer().hand.length) {
                    gameSocket.send(JSON.stringify({
                        "event": "START_TURN",
                        "message": {"username":username}
                    }));
                }         
                document.getElementById("opponent_username").innerHTML = game.opponent().username + " (opponent)";
                document.getElementById("opponent_hit_points").innerHTML = game.opponent().hit_points + " hp";
                document.getElementById("opponent_card_count").innerHTML = game.opponent().hand.length + " cards";
                document.getElementById("username").innerHTML = game.thisPlayer().username + " (me)";
                document.getElementById("hit_points").innerHTML = game.thisPlayer().hit_points + " hp";
                document.getElementById("in_play").style = 'height:150px;width:630px;background-color:black;';
                document.getElementById("opponent_in_play").style = 'height:150px;width:630px;background-color:black;';
                document.getElementById("hand").style = 'height:150px;width:630px;background-color:yellow;';
            }
                break;
        case "START_TURN":
            var game = new CoFXGame(username, data["game"]);
            let handDiv = document.getElementById("hand");
            handDiv.innerHTML = '';
            for (let card of game.thisPlayer().hand) {
                handDiv.appendChild(cardSprite(card, username));
            }
            if (data["username"] == game.thisPlayer().username) {
                document.getElementById("end-turn-button").style.backgroundColor = "gray";
                document.getElementById("end-turn-button").style.pointerEvents = "auto";
                for (let childCardDiv of document.getElementById("in_play").children) {
                    childCardDiv.style.backgroundColor = "red";
                }
            }
            document.getElementById("opponent_card_count").innerHTML = game.opponent().hand.length+ " cards";
            document.getElementById("opponent_mana").innerHTML = game.opponent().mana + " mana";
            document.getElementById("mana").innerHTML = game.thisPlayer().mana + " mana";
            break;
        case "PLAY_CARD":
                var game = new CoFXGame(username, data["game"]);
                let card = new CoFXCard(data["card"]);
                document.getElementById("opponent_card_count").innerHTML = game.opponent().hand.length;
                document.getElementById("opponent_mana").innerHTML = game.opponent().mana + " mana";
                document.getElementById("mana").innerHTML = game.thisPlayer().mana + " mana";
                if (data["username"] == game.thisPlayer().username) {
                        document.getElementById("in_play").appendChild(document.getElementById("card_"+card.id)); 
                    return;
                }
                let cardDiv = cardSprite(card, username)
                document.getElementById("opponent_in_play").appendChild(cardDiv); 
            break;
        case "END_TURN":
                var game = new CoFXGame(username, data["game"]);
                if (data["username"] == game.opponent().username) {
                    gameSocket.send(JSON.stringify({
                        "event": "START_TURN",
                        "message": {"username":username}
                    }));
                }
            break;
        case "NEXT_ROOM":
            var url = location.host + location.pathname;
            var roomNumber = parseInt(url.split( '/' ).pop()) + 1;
            var usernameParameter = getSearchParameters()["username"];
            var nextRoomUrl = "/play/" + roomNumber + "?username=" + usernameParameter;
            if (data["username"] == username) {
               window.location.href = nextRoomUrl;
            } else {
                setTimeout(function(){
                    window.location.href = nextRoomUrl;
                }, 100); 
            }
            break;
        case "ATTACK_FACE":
            var game = new CoFXGame(username, data["game"]);
            document.getElementById("opponent_hit_points").innerHTML = game.opponent().hit_points + " hp";
            document.getElementById("hit_points").innerHTML = game.thisPlayer().hit_points + " hp";

            if (game.opponent().hit_points <= 0 || game.thisPlayer().hit_points <= 0) {
                alert("GAME OVER");
            }
            break;
        case "ATTACK_ENTITY":
            var game = new CoFXGame(username, data["game"]);
            let inPlayDiv = document.getElementById("in_play");
            inPlayDiv.innerHTML = '';
            for (let card of game.thisPlayer().in_play) {
                inPlayDiv.appendChild(cardSprite(card, username));
            }
            let opponentInPlayDiv = document.getElementById("opponent_in_play");
            opponentInPlayDiv.innerHTML = '';
            for (let card of game.opponent().in_play) {
                opponentInPlayDiv.appendChild(cardSprite(card, username));
            }
            if (data["username"] == game.thisPlayer().username) {
                for (let childCardDiv of document.getElementById("in_play").children) {
                    if (childCardDiv.id == "card_"+data["attacking_card"]) {
                        childCardDiv.style.backgroundColor = "gray";
                    }
                }

            }
            if (data["username"] == game.opponent().username) {
                for (let childCardDiv of document.getElementById("opponent_in_play").children) {
                    if (childCardDiv.id == "card_"+data["attacking_card"]) {
                        childCardDiv.style.backgroundColor = "gray";
                    }
                }

            }
            break;
        case "SELECT_ENTITY":
            var game = new CoFXGame(username, data["game"]);
            if (data["username"] == game.opponent().username) {
                for (let childCardDiv of document.getElementById("opponent_in_play").children) {
                    if (childCardDiv.id == "card_"+data["card"]) {
                        childCardDiv.style.backgroundColor = "orange";
                    }
                }

            }
            break;
        default:
            console.log("No event")
    }
};

function endTurn() {
    lastSelectedCard = null;
    document.getElementById("end-turn-button").style.pointerEvents = "none";
    document.getElementById("end-turn-button").style.backgroundColor = "lightgray";
    gameSocket.send(JSON.stringify({
        "event": "END_TURN",
        "message": {"username":username}
    }));    
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

function cardSprite(card, username) {
    let cardDiv = document.createElement("div");
    cardDiv.id = "card_" + card.id;
    cardDiv.style = 'height:138px;width:90px;background-color:red;border-width: 1px;border-color: white;border-style: solid;border-radius:4px;padding:5px';

    let nameDiv = document.createElement("div");
    nameDiv.innerHTML = card.name;
    cardDiv.appendChild(nameDiv)

    let costDiv = document.createElement("div");
    costDiv.innerHTML = "Cost: " + card.cost;
    cardDiv.appendChild(costDiv)

    let powerToughnessDiv = document.createElement("div");
    powerToughnessDiv.innerHTML = card.power + "/" + (card.toughness - card.damage);
    cardDiv.appendChild(powerToughnessDiv)

    cardDiv.onclick = function() { 
        if (cardDiv.parentElement == document.getElementById("hand")) {                            
            gameSocket.send(JSON.stringify({
                "event": "PLAY_CARD",
                "message": {"card":card.id, "username":username}
            }));
        }
        if (cardDiv.parentElement == document.getElementById("in_play")) {    
            if (cardDiv.style.backgroundColor == "darkgray") {
                // do nothing, already attacked
                lastSelectedCard = null;
            } else if (cardDiv.style.backgroundColor == "orange")   {
                gameSocket.send(JSON.stringify({
                    "event": "ATTACK_FACE",
                    "message": {"card":card.id, "username":username}
                }));
                cardDiv.style.backgroundColor = "darkgray";                
                lastSelectedCard = null;
            } else {
                cardDiv.style.backgroundColor = "orange";                
                lastSelectedCard = card;
                gameSocket.send(JSON.stringify({
                    "event": "SELECT_ENTITY",
                    "message": {"card":card.id, "username":username}
                }));
            }                 
        }
        console.log(lastSelectedCard);
        console.log(cardDiv.parentElement);
        if (lastSelectedCard && cardDiv.parentElement == document.getElementById("opponent_in_play")) {
            gameSocket.send(JSON.stringify({
                "event": "ATTACK_ENTITY",
                "message": {"defending_card":card.id, "attacking_card":lastSelectedCard.id, "username":username}
            }));            
        }    

    };

    return cardDiv;

}

function connect() {
    if (gameSocket.readyState == WebSocket.OPEN) {
        console.log('WebSockets connection created.');
        gameSocket.send(JSON.stringify({
            "event": "JOIN",
            "message": {"username":username}
        }));
    } else {
        setTimeout(function () {
        connect();
        }, 100);
    }
}

function nextRoom() {
    gameSocket.send(JSON.stringify({
        "event": "NEXT_ROOM",
        "message": {"username":username}
    }));
}

connect();
