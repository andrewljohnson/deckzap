export class GameRoom {

    gameSocket = null;

    constructor(gameUX) {
        this.gameUX = gameUX;
        this.username = gameUX.username;
        gameUX.gameRoom = this;
    }

    connect() {
        if (this.gameSocket == null) {
            this.setupSocket();
        }
        if (this.gameSocket.readyState == WebSocket.OPEN) {
            const deck_id = document.getElementById("data_store").getAttribute("deck_id");
            if (deck_id) {
               const opponent_deck_id = document.getElementById("data_store").getAttribute("opponent_deck_id");
                if (opponent_deck_id) {
                    this.sendPlayMoveEvent("JOIN", { deck_id, opponent_deck_id });                
                } else {
                    this.sendPlayMoveEvent("JOIN", { deck_id });                
                }
            }
            this.sendHeartbeatRequest()
            console.log('WebSockets connection created.');
        } else {
            let self = this;
            setTimeout(function () {
                self.connect();
            }, 100);
        }
    }

    sendHeartbeatRequest() {
        let self = this;
        setTimeout(function () {
            self.sendPlayMoveEvent( "GET_TIME", {});
            self.sendHeartbeatRequest();
        }, 500);
    }

    setupSocket() {
        this.gameSocket = new WebSocket(this.roomSocketUrl());

        let self = this;
        this.gameSocket.onclose = function (e) {
            console.log('Socket is closed. Reconnect will be attempted in 1 second.', e.reason);
            setTimeout(function () {
                self.connect();
            }, 1000);
        };

        this.gameSocket.onmessage = function (e) {
            let data = JSON.parse(e.data)["payload"];
            if (data["move_type"] == "NEXT_ROOM") {
                let usernameParameter = getSearchParameters()["username"];
                if (data["username"] == usernameParameter) {
                   window.location.href = self.nextRoomUrl();
                } else {
                    setTimeout(function(){
                        window.location.href = self.nextRoomUrl();
                    }, 100); 
                }
            } else if (data["move_type"] == "GET_TIME") {
                if (data["turn_time"] >= data["max_turn_time"]) {
                    self.gameUX.maybeShowRope();   
                }
            } else {
                let game = data["game"];
                if (!data["game"]) {
                    console.log(data);                    
                } else {
                  self.gameUX.game = game;  
                }
                if (!self.gameUX.allCards) {
                    self.gameUX.allCards = data["all_cards"]
                }
                self.gameUX.refresh(game, data);
                self.gameUX.logMessage(data["log_lines"]);
            }
        };


    }

    roomSocketUrl() {
        const roomCode = document.getElementById("data_store").getAttribute("game_record_id");
        const url = new URL(window.location.href);
        let protocol = url.protocol == 'https:' ? 'wss://' : 'ws://';
        let connectionString = protocol + window.location.host + '/ws/play/' + this.gameUX.playerType + '/' + roomCode + '/';
        const ai = document.getElementById("data_store").getAttribute("ai");
        if (ai && ai != "None") {
            connectionString += ai + '/';
        }
        return connectionString;
    }

    nextRoomUrl() {
        const ai = document.getElementById("data_store").getAttribute("ai");
        let url = location.host + location.pathname;
        if (!ai || ai == "None") {
            const deckID = document.getElementById("data_store").getAttribute("deck_id");
            return `/find_match?deck_id=${deckID}`;
        }
        let basePath = "play";
        let roomNumber = parseInt(url.split( '/' ).pop()) + 1;
        let usernameParameter = getSearchParameters()["username"];
        let nextRoomUrl = `/${basePath}/` + this.gameUX.playerType + '/' + roomNumber;
        let getParams =  "?new_game_from_button=true";
        if (ai && ai != "None") {
            getParams += '&ai=' + ai;
        }
        const deck_id = document.getElementById("data_store").getAttribute("deck_id");
        if (deck_id && deck_id != "None") {
            getParams += '&deck_id=' + deck_id;
        }
        const opponent_deck_id = document.getElementById("data_store").getAttribute("opponent_deck_id");
        if (opponent_deck_id && opponent_deck_id != "None") {
            getParams += '&opponent_deck_id=' + opponent_deck_id;
        }
        nextRoomUrl +=  getParams;
        return nextRoomUrl;
    }

    sendPlayMoveEvent(move_type, info) {
        info["move_type"] = move_type
        info["username"] = this.username
        this.gameSocket.send(JSON.stringify(
            info
        ));                
    }

    nextRoom() {
        if (this.gameSocket.readyState != WebSocket.OPEN) {
            window.location.href = this.nextRoomUrl();
        }

        this.gameSocket.send(JSON.stringify(
            {"move_type": "NEXT_ROOM", "username":this.username}
        ));
    }

    endTurn() {
        this.sendPlayMoveEvent("END_TURN", {});
    }

    pass(message) {
        this.sendPlayMoveEvent("RESOLVE_NEXT_STACK", message);
    }

}

function getSearchParameters() {
    let prmstr = window.location.search.substr(1);
    return prmstr != null && prmstr != "" ? transformToAssocArray(prmstr) : {};
}

function transformToAssocArray( prmstr ) {
    let params = {};
    let prmarr = prmstr.split("&");
    for ( let i = 0; i < prmarr.length; i++) {
        let tmparr = prmarr[i].split("=");
        params[tmparr[0]] = tmparr[1];
    }
    return params;
}