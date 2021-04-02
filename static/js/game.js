var roomCode = document.getElementById("data_store").getAttribute("room_code");
var username = document.getElementById("data_store").getAttribute("username");

const url = new URL(window.location.href);
var protocol = url.protocol == 'https:' ? 'wss://' : 'ws://';
var connectionString = protocol + window.location.host + '/ws/play/' + roomCode + '/';
const gameSocket = new WebSocket(connectionString);
var lastSelectedCard = null;
var lastSelectedCardInHand = null;

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
        this.abilities = info["abilities"];            
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
    var inPlayDiv = document.getElementById("in_play");
    let opponentInPlayDiv = document.getElementById("opponent_in_play");
    let handDiv = document.getElementById("hand");

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
                document.getElementById("in_play").style = 'height:110px;width:610px;background-color:black;';
                document.getElementById("opponent_in_play").style = 'height:110px;width:610px;background-color:black;';
                document.getElementById("hand").style = 'height:110px;width:100%;background-color:yellow;';
            }
                break;
        case "START_TURN":
            var game = new CoFXGame(username, data["game"]);
            handDiv.innerHTML = '';
            for (let card of game.thisPlayer().hand) {
                handDiv.appendChild(cardSprite(card, username));
            }
            if (data["username"] == game.thisPlayer().username) {
                document.getElementById("end-turn-button").style.backgroundColor = "red";
                document.getElementById("end-turn-button").style.pointerEvents = "auto";
                for (let childCardDiv of document.getElementById("in_play").children) {
                    childCardDiv.style.backgroundColor = "red";
                }
            }
            document.getElementById("opponent_card_count").innerHTML = game.opponent().hand.length+ " cards";
            document.getElementById("opponent_mana").innerHTML = game.opponent().mana + " mana";
            document.getElementById("mana").innerHTML = game.thisPlayer().mana + " mana";

            // refresh cards so turn_played gets set for summoning sickness
            inPlayDiv.innerHTML = '';
            for (let card of game.thisPlayer().in_play) {
                inPlayDiv.appendChild(cardSprite(card, username));
            }

            break;
        case "PLAY_CARD":
                var game = new CoFXGame(username, data["game"]);
                let card = new CoFXCard(data["card"]);
                document.getElementById("opponent_card_count").innerHTML = game.opponent().hand.length+ " cards";
                document.getElementById("opponent_mana").innerHTML = game.opponent().mana + " mana";
                document.getElementById("mana").innerHTML = game.thisPlayer().mana + " mana";
                if (card.card_type == "Entity") {
                    if (data["username"] == game.thisPlayer().username) {
                        document.getElementById("in_play").appendChild(document.getElementById("card_"+card.id)); 
                    } else {
                        let cardDiv = cardSprite(card, username)
                        document.getElementById("opponent_in_play").appendChild(cardDiv);                         
                    }
                }
                handDiv.innerHTML = '';
                for (let card of game.thisPlayer().hand) {
                    handDiv.appendChild(cardSprite(card, username));
                }
                document.getElementById("opponent_card_count").innerHTML = game.opponent().hand.length+ " cards";
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

            if (data["username"] == game.opponent().username) {
                for (let childCardDiv of document.getElementById("opponent_in_play").children) {
                    if (childCardDiv.id == "card_"+data["card"]) {
                        childCardDiv.style.backgroundColor = "gray";
                    }
                }
                document.getElementById("player1").style.backgroundColor = "red";
                setTimeout(function() {
                    document.getElementById("player1").style.backgroundColor = "lightgray";
                }, 400);
            } else  {
                document.getElementById("opponent").style.backgroundColor = "red";
                setTimeout(function() {
                    document.getElementById("opponent").style.backgroundColor = "lightgray";
                }, 400);                
            }
            if (game.opponent().hit_points <= 0 || game.thisPlayer().hit_points <= 0) {
                alert("GAME OVER");
            }
            break;
        case "ATTACK_ENTITY":
            var game = new CoFXGame(username, data["game"]);
            inPlayDiv.innerHTML = '';
            for (let card of game.thisPlayer().in_play) {
                inPlayDiv.appendChild(cardSprite(card, username));
            }
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
        case "CAST_SPELL_ON_ENTITY":
            var game = new CoFXGame(username, data["game"]);
            inPlayDiv.innerHTML = '';
            for (let card of game.thisPlayer().in_play) {
                inPlayDiv.appendChild(cardSprite(card, username));
            }
            opponentInPlayDiv.innerHTML = '';
            for (let card of game.opponent().in_play) {
                opponentInPlayDiv.appendChild(cardSprite(card, username));
            }
            handDiv.innerHTML = '';
            for (let card of game.thisPlayer().hand) {
                handDiv.appendChild(cardSprite(card, username));
            }
            document.getElementById("opponent_card_count").innerHTML = game.opponent().hand.length+ " cards";
            break;
        case "CAST_SPELL_ON_OPPONENT":
            var game = new CoFXGame(username, data["game"]);
            document.getElementById("opponent_hit_points").innerHTML = game.opponent().hit_points + " hp";
            if (game.opponent().hit_points <= 0) {
                alert("GAME OVER");
            }
            handDiv.innerHTML = '';
            for (let card of game.thisPlayer().hand) {
                handDiv.appendChild(cardSprite(card, username));
            }
            document.getElementById("opponent_card_count").innerHTML = game.opponent().hand.length+ " cards";
        case "CAST_SPELL_ON_SELF":
            var game = new CoFXGame(username, data["game"]);
            document.getElementById("hit_points").innerHTML = game.thisPlayer().hit_points + " hp";
            if (game.opponent().hit_points <= 0) {
                alert("GAME OVER");
            }
            handDiv.innerHTML = '';
            for (let card of game.thisPlayer().hand) {
                handDiv.appendChild(cardSprite(card, username));
            }
            document.getElementById("opponent_card_count").innerHTML = game.opponent().hand.length+ " cards";
        default:
            console.log("No event")
    }
};

function endTurn() {
    lastSelectedCard = null;
    lastSelectedCardInHand = null;
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
                gameSocket.send(JSON.stringify({
                    "event": "PLAY_CARD",
                    "message": {"card":card.id, "username":username}
                }));                
            } else {
                if (cardDiv.style.backgroundColor == "orange")   {
                    cardDiv.style.backgroundColor = "red";                
                    lastSelectedCardInHand = null;
                    if (card.name == "Think") {                
                        gameSocket.send(JSON.stringify({
                            "event": "PLAY_CARD",
                            "message": {"card":card.id, "username":username}
                        }));                
                    }
                } else {
                    cardDiv.style.backgroundColor = "orange";                
                    lastSelectedCardInHand = card;
                }
            }                          
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
                if (card.turn_played != -1) {
                    cardDiv.style.backgroundColor = "orange";                
                    lastSelectedCard = card;
                    gameSocket.send(JSON.stringify({
                        "event": "SELECT_ENTITY",
                        "message": {"card":card.id, "username":username}
                    }));                    
                }
            }                 
        }
        if (lastSelectedCard && cardDiv.parentElement == document.getElementById("opponent_in_play")) {
            gameSocket.send(JSON.stringify({
                "event": "ATTACK_ENTITY",
                "message": {"defending_card":card.id, "attacking_card":lastSelectedCard.id, "username":username}
            }));            
        }    

        if (lastSelectedCardInHand
            && (cardDiv.parentElement == document.getElementById("opponent_in_play") || cardDiv.parentElement == document.getElementById("in_play"))) {
            gameSocket.send(JSON.stringify({
                "event": "CAST_SPELL_ON_ENTITY", 
                "message": {"target_card":card.id, "spell_card":lastSelectedCardInHand.id, "username":username}
            }));            
        }    

    };

    return cardDiv;

}

document.getElementById("opponent").onclick = function() {
    for (let childCardDiv of document.getElementById("in_play").children) {
        if (childCardDiv.style.backgroundColor == "orange") {
            childCardDiv.style.backgroundColor = "gray";
            gameSocket.send(JSON.stringify({
                "event": "ATTACK_FACE",
                "message": {"card":parseInt(childCardDiv.id.slice(5)), "username":username}
            }));
            childCardDiv.style.backgroundColor = "darkgray";                
            lastSelectedCard = null;
            lastSelectedCardInHand = null;
        }
    }
    for (let childCardDiv of document.getElementById("hand").children) {
        if (childCardDiv.style.backgroundColor == "orange") {
            gameSocket.send(JSON.stringify({
                "event": "CAST_SPELL_ON_OPPONENT",
                "message": {"card":parseInt(childCardDiv.id.slice(5)), "username":username}
            }));
            childCardDiv.style.backgroundColor = "red";                
            lastSelectedCard = null;
            lastSelectedCardInHand = null;
        }
    }
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
connect();

function nextRoom() {
    gameSocket.send(JSON.stringify({
        "event": "NEXT_ROOM",
        "message": {"username":username}
    }));
}

function viewHelp() {
    alert("1. Click cards in hand to play them.\n2. To attack, click your entity, then your opponent's.\n3. To attack your opponent's face, double click an entity or click your entity then the opponent.\n4. To cast a spell at your opponent's entity, click your spell, then your opponent's entity.\n5. To cast a spell at your opponent's face, click a spell or click a spell then the opponent.\n6. Entities can't attack the turn they come into play.");
}

