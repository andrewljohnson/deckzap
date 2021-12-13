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
import Profile from '../js/views/Profile';

import * as Constants from '../js/constants';
import ReactDOM from "react-dom";
import CardBuilderType from '../js/views/create_cards/CardBuilderType';
import CardView from '../js/views/create_cards/CardView';
import CardBuilderEffects from '../js/views/create_cards/CardBuilderEffects';
import CardBuilderMob from '../js/views/create_cards/CardBuilderMob';
import CardBuilderSpell from '../js/views/create_cards/CardBuilderSpell';
import CardBuilderNameAndImage from '../js/views/create_cards/CardBuilderNameAndImage';

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
} else if (window.location.pathname.startsWith("/u/")) {
    const playerRank = document.getElementById("data_store").getAttribute("player_rank");
    const accountNumber = document.getElementById("data_store").getAttribute("account_number");
    const username = document.getElementById("data_store").getAttribute("username");
    const userOwnsProfile = document.getElementById("data_store").getAttribute("user_owns_profile");
    const decks = JSON.parse(document.getElementById("data_store").getAttribute("decks"));
    const cards = JSON.parse(document.getElementById("data_store").getAttribute("cards"));
    ReactDOM.render(<Profile playerRank={playerRank} username={username} cards={cards} decks={decks} accountNumber={accountNumber} userOwnsProfile={userOwnsProfile} />, document.getElementById("app"));
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
        fetchCardInfo(cardID)
            .then(json => {
                let cardInfo = JSON.parse(json.card_info);
                cardInfo.name = cardInfo.name ? cardInfo.name : "Unnamed Card";
                cardInfo.image = cardInfo.image ? cardInfo.image : "uncertainty.svg";
                const effectIndex = parseInt(document.getElementById("data_store").getAttribute("effect_index"));
                const cardView = new CardView("card", cardInfo);
                ReactDOM.render(<CardBuilderEffects effectIndex={effectIndex} cardView={cardView} cardID={cardID} originalCardInfo={cardInfo} effectsAndTypes={effectsAndTypes} />, document.getElementById("app"));
            });
    } else if (window.location.pathname.endsWith("name_and_image")) {
        const cardID = document.getElementById("data_store").getAttribute("card_id");
        const imagePaths = JSON.parse(document.getElementById("data_store").getAttribute("image_paths"));
        fetchCardInfo(cardID)
            .then(json => {
                let cardInfo = JSON.parse(json.card_info);
                console.log(cardInfo);
                cardInfo.name = cardInfo.name ? cardInfo.name : "Unnamed Card";
                cardInfo.image = cardInfo.image ? cardInfo.image : "uncertainty.svg";
                cardInfo.description = Constants.cardDescription(cardInfo);
                const cardView = new CardView("card", cardInfo);
                ReactDOM.render(<CardBuilderNameAndImage cardView={cardView} cardID={cardID} originalCardInfo={cardInfo} imagePaths={imagePaths}  />, document.getElementById("app"));
            });
    } else if (window.location.pathname.endsWith("spell")) {
        const effectsAndTypes = JSON.parse(document.getElementById("data_store").getAttribute("effects_and_types"));
        const cardID = document.getElementById("data_store").getAttribute("card_id");
        fetchCardInfo(cardID)
            .then(json => {
                let cardInfo = JSON.parse(json.card_info);
                cardInfo.name = cardInfo.name ? cardInfo.name : "Unnamed Spell";
                cardInfo.image = cardInfo.image ? cardInfo.image : "uncertainty.svg";
                const cardView = new CardView("card", cardInfo);
                ReactDOM.render(<CardBuilderSpell effectIndex={0} cardView={cardView} cardID={cardID} originalCardInfo={cardInfo} effectsAndTypes={effectsAndTypes} />, document.getElementById("app"));           
            });
    } else if (window.location.pathname.endsWith("mob")) {
        const effectsAndTypes = JSON.parse(document.getElementById("data_store").getAttribute("effects_and_types"));
        const cardID = document.getElementById("data_store").getAttribute("card_id");
        fetchCardInfo(cardID)
            .then(json => {
                let cardInfo = JSON.parse(json.card_info);
                cardInfo.name = cardInfo.name ? cardInfo.name : "Unnamed Mob";
                cardInfo.image = cardInfo.image ? cardInfo.image : "uncertainty.svg";
                const cardView = new CardView("card", cardInfo);
                ReactDOM.render(<CardBuilderMob effectIndex={0} cardView={cardView} cardID={cardID} originalCardInfo={cardInfo} effectsAndTypes={effectsAndTypes} />, document.getElementById("app"));
            });
    } else {
        const cardInfo = {name: "Unnamed Card", image: "uncertainty.svg", card_type: Constants.mobCardType};
        const cardView = new CardView("card", cardInfo);
        ReactDOM.render(<CardBuilderType cardView={cardView} originalCardInfo={cardInfo} />, document.getElementById("app"));
    }
}


async function fetchCardInfo(cardID) {
    const json = await Constants.postData(`/create_card/get_card_info`, { card_id: cardID });
    return json;
}
