import { DeckViewer } from '../js/DeckViewer';
import { GameRoom } from '../js/GameRoom';
import { GameUX } from '../js/game';

if (window.location.pathname.startsWith("/play/")) {
	const gameUX = new GameUX();
	const gameRoom = new GameRoom(gameUX);
	gameRoom.connect();
} else {
    function changeDeck() {
        const chosenDeckID = document.getElementById("decks").value;
        const decks = JSON.parse(document.getElementById("data_store").getAttribute("json_decks"));
        let chosenDeck = null;
        for (let deck of decks) {
            if (deck.id == chosenDeckID) {
                chosenDeck = deck;
            }
        }
        var deckViewer = new DeckViewer(chosenDeck, JSON.parse(document.getElementById("data_store").getAttribute("all_cards")), "deck_container");
        deckViewer.redisplayDeck();
        if (chosenDeck.race == "dwarf") {
            document.getElementById("deckInfo").innerHTML = 
                "<ul><li>three mana per turn</li><li>new hand of five cards each turn</li><li>15 card deck</li></ul>"
        } else {
            document.getElementById("deckInfo").innerHTML = 
                "<ul><li>get more mana each turn</li><li>start with 4 cards, draw a card per turn</li><li>30 card deck</li></ul>"          
        }
  	}
  	changeDeck();
}


// import './scss/index.scss';