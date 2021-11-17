import * as Constants from '../constants.js';


export class GameRoom {

    gameSocket = null;

    constructor(gameUX) {
        this.gameUX = gameUX;
        this.username = gameUX.username;
        gameUX.gameRoom = this;
    }

    connect() {
        if (this.gameSocket === null) {
            this.setupSocket();
        }
        if (this.gameSocket.readyState === WebSocket.OPEN) {
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
            setTimeout(() => {
                this.connect();
            }, 100);
        }
    }

    sendHeartbeatRequest() {
        setTimeout(() => {
            this.sendPlayMoveEvent( "GET_TIME", {});
            this.sendHeartbeatRequest();
        }, 500);
    }

    setupSocket() {
        this.gameSocket = new WebSocket(this.roomSocketUrl());
        this.gameSocket.onclose = e => {
            console.log('Socket is closed. Reconnect will be attempted in 1 second.', e.reason);
            setTimeout(() => {
                this.connect();
            }, 1000);
        };

        this.gameSocket.onmessage = e => {
            const message = JSON.parse(e.data)["payload"];
            if (message["move_type"] === "NEXT_ROOM") {
                let usernameParameter = Constants.getSearchParameters()["username"];
                if (message["username"] === usernameParameter) {
                   window.location.href = this.nextRoomUrl();
                } else {
                    setTimeout(() => {
                        window.location.href = this.nextRoomUrl();
                    }, 100); 
                }
            } else if (!message["move_type"]) {
                if (message["turn_time"] >= message["max_turn_time"]) {
                    this.gameUX.maybeShowRope();   
                }
            } else {
                let game = message["game"];
                if (!message["game"]) {
                    console.log(message);                    
                }
                if (!this.gameUX.allCards) {
                    this.gameUX.allCards = message["all_cards"]
                }
                if (this.gameUX.actionQueue.length === 0) {
                    this.gameUX.actionQueue.push({game, message});
                    this.gameUX.refresh(game, message);
                } else {
                    this.gameUX.actionQueue.push({game, message});
                }
                // only used for onDragMove and onDragEnd
                this.gameUX.game = game;
            }
        };
    }

    roomSocketUrl() {
        const roomCode = document.getElementById("data_store").getAttribute("game_record_id");
        const url = new URL(window.location.href);
        let protocol = url.protocol === 'https:' ? 'wss://' : 'ws://';
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
        if (!ai || ai === "None") {
            const deckID = document.getElementById("data_store").getAttribute("deck_id");
            return `/find_match?deck_id=${deckID}`;
        }
        let basePath = "play";
        let roomNumber = parseInt(url.split( '/' ).pop()) + 1;
        let usernameParameter = Constants.getSearchParameters()["username"];
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
}
