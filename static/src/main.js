// this import due to: https://flaviocopes.com/parcel-regeneratorruntime-not-defined/
import 'regenerator-runtime/runtime'

import { DeckBuilder } from '../js/views/DeckBuilder';
import { DeckViewer } from '../js/views/DeckViewer';
import { GameRoom } from '../js/components/GameRoom';
import { GameUX } from '../js/views/Game';
import { MatchFinder } from '../js/views/MatchFinder';
import { OpponentChooser } from '../js/views/OpponentChooser';
import { TopDecks } from '../js/views/TopDecks';
import { TopPlayers } from '../js/views/TopPlayers';

import * as Constants from '../js/Constants';
import ReactDOM from "react-dom";
import CardBuilderType from '../js/views/create_cards/CardBuilderType';
import CardView from '../js/views/create_cards/CardView';
import NewCardBuilderEffects from '../js/views/create_cards/NewCardBuilderEffects';
import NewCardBuilderMob from '../js/views/create_cards/NewCardBuilderMob';
import NewCardBuilderSpell from '../js/views/create_cards/NewCardBuilderSpell';
import NewCardBuilderNameAndImage from '../js/views/create_cards/NewCardBuilderNameAndImage';

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
        const effectsAndTypes = JSON.parse(document.getElementById("data_store").getAttribute("effects_and_types"));
        const cardInfo = JSON.parse(document.getElementById("data_store").getAttribute("card_info"));
        const cardID = document.getElementById("data_store").getAttribute("card_id");
        const effectIndex = parseInt(document.getElementById("data_store").getAttribute("effect_index"));
        const cardView = new CardView("card", cardInfo);
        ReactDOM.render(<NewCardBuilderEffects effectIndex={effectIndex} cardView={cardView} cardID={cardID} originalCardInfo={cardInfo} effectsAndTypes={effectsAndTypes} />, document.getElementById("app"));
    } else if (window.location.pathname.endsWith("name_and_image")) {
        const cardID = document.getElementById("data_store").getAttribute("card_id");
        const imagePaths = JSON.parse(document.getElementById("data_store").getAttribute("image_paths"));
        const cardInfo = JSON.parse(document.getElementById("data_store").getAttribute("card_info"));
        cardInfo.name = "Unnamed Card";
        cardInfo.image = "uncertainty.svg";
        cardInfo.description = Constants.cardDescription(cardInfo);
        const cardView = new CardView("card", cardInfo);
        ReactDOM.render(<NewCardBuilderNameAndImage cardView={cardView} cardID={cardID} originalCardInfo={cardInfo} imagePaths={imagePaths}  />, document.getElementById("app"));
    } else if (window.location.pathname.endsWith("spell")) {
        const effectsAndTypes = JSON.parse(document.getElementById("data_store").getAttribute("effects_and_types"));
        const cardID = document.getElementById("data_store").getAttribute("card_id");
        const cardInfo = JSON.parse(document.getElementById("data_store").getAttribute("card_info"));
        cardInfo.name = "Unnamed Spell";
        cardInfo.image = "uncertainty.svg";
        const cardView = new CardView("card", cardInfo);
        ReactDOM.render(<NewCardBuilderSpell effectIndex={0} cardView={cardView} cardID={cardID} originalCardInfo={cardInfo} effectsAndTypes={effectsAndTypes} />, document.getElementById("app"));
    } else if (window.location.pathname.endsWith("mob")) {
        const effectsAndTypes = JSON.parse(document.getElementById("data_store").getAttribute("effects_and_types"));
        const cardID = document.getElementById("data_store").getAttribute("card_id");
        const cardInfo = JSON.parse(document.getElementById("data_store").getAttribute("card_info"));
        cardInfo.name = "Unnamed Mob";
        cardInfo.image = "uncertainty.svg";
        const cardView = new CardView("card", cardInfo);
        ReactDOM.render(<NewCardBuilderMob effectIndex={0} cardView={cardView} cardID={cardID} originalCardInfo={cardInfo} effectsAndTypes={effectsAndTypes} />, document.getElementById("app"));
    } else {
        const cardInfo = {name: "Unnamed Card", image: "uncertainty.svg", card_type: Constants.mobCardType};
        const cardView = new CardView("card", cardInfo);
        ReactDOM.render(<CardBuilderType cardView={cardView} originalCardInfo={cardInfo} />, document.getElementById("app"));
    }
}
