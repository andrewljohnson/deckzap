// this import due to: https://flaviocopes.com/parcel-regeneratorruntime-not-defined/
import 'regenerator-runtime/runtime'

import { DeckBuilder } from '../js/DeckBuilder';
import { DeckViewer } from '../js/DeckViewer';
import { GameRoom } from '../js/GameRoom';
import { GameUX } from '../js/game';
import { MatchFinder } from '../js/MatchFinder';
import { OpponentChooser } from '../js/OpponentChooser';
import { TopDecks } from '../js/TopDecks';
import { TopPlayers } from '../js/TopPlayers';

if (window.location.pathname.startsWith("/play")) {
	const gameUX = new GameUX();
	const gameRoom = new GameRoom(gameUX);
	gameRoom.connect();
} else if (window.location.pathname.startsWith("/choose_deck_for_match")) {
    const decks = JSON.parse(document.getElementById("data_store").getAttribute("json_decks"));
    const allCards = JSON.parse(document.getElementById("data_store").getAttribute("all_cards"))
    new DeckViewer(decks, allCards, "app");
} else if (window.location.pathname.startsWith("/choose_opponent")) {
    const opponentDecks = JSON.parse(document.getElementById("data_store").getAttribute("json_opponent_decks"));
    const deckID = JSON.parse(document.getElementById("data_store").getAttribute("deck_id"));
    const allCards = JSON.parse(document.getElementById("data_store").getAttribute("all_cards"))
    new OpponentChooser(opponentDecks, allCards, "app", deckID);
} else if (window.location.pathname.startsWith("/find_match")) {
    const deckID = JSON.parse(document.getElementById("data_store").getAttribute("deck_id"));
    const username = document.getElementById("data_store").getAttribute("username");
    new MatchFinder("app", deckID, username);
} else if (window.location.pathname.startsWith("/build_deck")) {
    new DeckBuilder("app", document.getElementById("data_store").getAttribute("deck"), document.getElementById("data_store").getAttribute("username"), document.getElementById("data_store").getAttribute("all_cards"));
} else if (window.location.pathname.startsWith("/top_players")) {
    new TopPlayers("app", JSON.parse(document.getElementById("data_store").getAttribute("players")));
} else if (window.location.pathname.startsWith("/top_decks")) {
    new TopDecks("app", JSON.parse(document.getElementById("data_store").getAttribute("decks")));
}
