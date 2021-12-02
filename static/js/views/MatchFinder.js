import * as Constants from '../constants.js';


export class MatchFinder {
    gameSocket = null;
    constructor(containerID, deckID, username) {
        let container = document.getElementById(containerID);
        let controlsContainer = document.createElement("div");
        container.appendChild(controlsContainer);
        let titleH1 = document.createElement("h1");
        titleH1.innerHTML = `
            Waiting for Opponent...
        `;
        controlsContainer.appendChild(titleH1);

        this.connect(username, deckID)
    }

    connect (username, deckID) {
        if (this.gameSocket == null) {
            this.setupSocket(deckID);
        }
        if (this.gameSocket.readyState == WebSocket.OPEN) {
            console.log('WebSockets connection created.');
            this.gameSocket.send(JSON.stringify(
                {"username": username, "message_type": "JOIN"}
            ));                
        } else {
            setTimeout(() => {
                this.connect(username);
            }, 100);
        }
    }

    setupSocket(deckID) {
        this.gameSocket = new WebSocket(this.roomSocketUrl());

        this.gameSocket.onclose = e => {
            console.log('Socket is closed. Reconnect will be attempted in 1 second.', e.reason);
            setTimeout(function () {
                this.connect();
            }, 1000);
        };

        this.gameSocket.onmessage = function (e) {
            let data = JSON.parse(e.data)["payload"];
            console.log(data);

            if (data.message_type == "start_match") {
                window.location.href = `/play/pvp/${data.game_record_id}?deck_id=${deckID}`                
            }
        };
    }


    roomSocketUrl() {
        const url = new URL(window.location.href);
        let protocol = url.protocol == 'https:' ? 'wss://' : 'ws://';
        let connectionString = protocol + window.location.host + '/ws/find_match/';
        return connectionString;
    }

}
