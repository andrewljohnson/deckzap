// this import due to: https://flaviocopes.com/parcel-regeneratorruntime-not-defined/
import 'regenerator-runtime/runtime'

import { CardBuilder } from '../js/views/CardBuilder';
import { DeckBuilder } from '../js/views/DeckBuilder';
import { DeckViewer } from '../js/views/DeckViewer';
import { GameRoom } from '../js/components/GameRoom';
import { GameUX } from '../js/views/Game';
import { MatchFinder } from '../js/views/MatchFinder';
import { OpponentChooser } from '../js/views/OpponentChooser';
import { TopDecks } from '../js/views/TopDecks';
import { TopPlayers } from '../js/views/TopPlayers';


if (window.location.pathname.startsWith("/play")) {
    const DEBUG = document.getElementById("data_store").getAttribute("debug");
	const gameUX = new GameUX(DEBUG);
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
} else if (window.location.pathname.startsWith("/create_card")) {
    new CardBuilder("app", JSON.parse(document.getElementById("data_store").getAttribute("effects_and_types")));
}
