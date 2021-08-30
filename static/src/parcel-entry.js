import { DeckViewer } from '../js/DeckViewer';
import { GameRoom } from '../js/GameRoom';
import { GameUX } from '../js/game';
import { MatchFinder } from '../js/MatchFinder';
import { OpponentPicker } from '../js/OpponentPicker';

if (window.location.pathname.startsWith("/play")) {
	const gameUX = new GameUX();
	const gameRoom = new GameRoom(gameUX);
	gameRoom.connect();
} else if (window.location.pathname.startsWith("/choose_deck_for_match")) {
    const decks = JSON.parse(document.getElementById("data_store").getAttribute("json_decks"));
    const allCards = JSON.parse(document.getElementById("data_store").getAttribute("all_cards"))
    let deckViewer = new DeckViewer(decks, allCards, "app");
    deckViewer.redisplayDeck();
} else if (window.location.pathname.startsWith("/choose_opponent")) {
    const opponentDecks = JSON.parse(document.getElementById("data_store").getAttribute("json_opponent_decks"));
    const deckID = JSON.parse(document.getElementById("data_store").getAttribute("deck_id"));
    const allCards = JSON.parse(document.getElementById("data_store").getAttribute("all_cards"))
    let opponentPicker = new OpponentPicker(opponentDecks, allCards, "app", deckID);
} else if (window.location.pathname.startsWith("/find_match")) {
    const deckID = JSON.parse(document.getElementById("data_store").getAttribute("deck_id"));
    const username = document.getElementById("data_store").getAttribute("username");
    let opponentPicker = new MatchFinder("app", deckID, username);
}

// import './scss/index.scss';