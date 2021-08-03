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
            const deck_id = document.getElementById("card_store").getAttribute("deck_id");
            if (deck_id) {
                this.sendPlayMoveEvent("JOIN", { deck_id });                
            }
            this.sendHeartbeatRequest()
            console.log('WebSockets connection created.');
        } else {
            var self = this;
            setTimeout(function () {
                self.connect();
            }, 100);
        }
    }

    sendHeartbeatRequest() {
        var self = this;
        setTimeout(function () {
            self.sendPlayMoveEvent( "GET_TIME", {});
            self.sendHeartbeatRequest();
        }, 500);
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
            } else if (data["move_type"] == "GET_TIME") {
                if (data["turn_time"] >= data["max_turn_time"]) {
                    self.gameUX.showRope();   
                }
            } else {
                let game = data["game"];
                if (!data["game"]) {
                    console.log(data);                    
                }
                self.gameUX.refresh(game, data);
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
        var basePath = "play";
        if (url.includes("play_new")) {
            basePath = "play_new";            
        }
        var roomNumber = parseInt(url.split( '/' ).pop()) + 1;
        var usernameParameter = getSearchParameters()["username"];
        var nextRoomUrl = `/${basePath}/` + this.gameUX.aiType + "/" + this.gameUX.gameType + '/' + roomNumber;
        var getParams =  "?new_game_from_button=true";
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
            nextRoomUrl = `/${basePath}/custom/` + roomNumber+ '/'  + customGameId + getParams;
        }
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

    passForAttack(message) {
        this.sendPlayMoveEvent("ALLOW_ATTACK", message);
    }

    passForSpellResolution(message) {
        this.sendPlayMoveEvent("RESOLVE_CARD", message);
    }
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