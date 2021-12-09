// this import due to: https://flaviocopes.com/parcel-regeneratorruntime-not-defined/
import 'regenerator-runtime/runtime'

import { CardBuilderEffects } from '../js/views/create_cards/CardBuilderEffects';
import { CardBuilderMob } from '../js/views/create_cards/CardBuilderMob';
import { CardBuilderSpell } from '../js/views/create_cards/CardBuilderSpell';
import { CardBuilderNameAndImage } from '../js/views/create_cards/CardBuilderNameAndImage';
import { DeckBuilder } from '../js/views/DeckBuilder';
import { DeckViewer } from '../js/views/DeckViewer';
import { GameRoom } from '../js/components/GameRoom';
import { GameUX } from '../js/views/Game';
import { MatchFinder } from '../js/views/MatchFinder';
import { OpponentChooser } from '../js/views/OpponentChooser';
import { TopDecks } from '../js/views/TopDecks';
import { TopPlayers } from '../js/views/TopPlayers';

import ReactDOM from "react-dom";
import CardBuilderType from '../js/views/create_cards/CardBuilderType';
import CardView from '../js/views/create_cards/CardView';
import NewCardBuilderMob from '../js/views/create_cards/NewCardBuilderMob';

// Reload window in dev
if (process.env.NODE_ENV !== 'production') {
    if (module.hot) {
        module.hot.accept(function () {
            location.reload();
        });
    }
}

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
    if (window.location.pathname.includes("effects")) {
        new CardBuilderEffects(
            "app",
            JSON.parse(document.getElementById("data_store").getAttribute("effects_and_types")),
            JSON.parse(document.getElementById("data_store").getAttribute("card_info")),
            document.getElementById("data_store").getAttribute("card_id"),
            document.getElementById("data_store").getAttribute("effect_index"),
        );
    } else if (window.location.pathname.endsWith("name_and_image")) {
        new CardBuilderNameAndImage(
            "app",
            JSON.parse(document.getElementById("data_store").getAttribute("card_info")),
            JSON.parse(document.getElementById("data_store").getAttribute("card_id")),
            JSON.parse(document.getElementById("data_store").getAttribute("image_paths")),
        );
    } else if (window.location.pathname.endsWith("spell")) {
        new CardBuilderSpell(
            "app",
            JSON.parse(document.getElementById("data_store").getAttribute("effects_and_types")),
            JSON.parse(document.getElementById("data_store").getAttribute("card_info")),
            document.getElementById("data_store").getAttribute("card_id"),
            document.getElementById("data_store").getAttribute("effect_index"),
        );
    } else if (window.location.pathname.endsWith("mob")) {
            const effectsAndTypes = JSON.parse(document.getElementById("data_store").getAttribute("effects_and_types"));
            const cardInfo = JSON.parse(document.getElementById("data_store").getAttribute("card_info"));
            const cardID = document.getElementById("data_store").getAttribute("card_id");

            // const effect_index = document.getElementById("data_store").getAttribute("effect_index");

        const cardView = new CardView("card");
        ReactDOM.render(<NewCardBuilderMob cardView={cardView} cardID={cardID} originalCardInfo={cardInfo} effectsAndTypes={effectsAndTypes} />, document.getElementById("app"));

        /*new CardBuilderMob(
            "app",
            JSON.parse(document.getElementById("data_store").getAttribute("effects_and_types")),
            JSON.parse(document.getElementById("data_store").getAttribute("card_info")),
            document.getElementById("data_store").getAttribute("card_id"),
            document.getElementById("data_store").getAttribute("effect_index"),
        );*/
    } else {
        const cardView = new CardView("card");
        ReactDOM.render(<CardBuilderType cardView={cardView} />, document.getElementById("app"));
    }
}
