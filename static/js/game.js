class GameUX {

    constructor() {
        this.username = document.getElementById("data_store").getAttribute("username");
        this.gameType = document.getElementById("data_store").getAttribute("game_type");
        this.aiType = document.getElementById("data_store").getAttribute("ai_type");
        this.allCards = JSON.parse(document.getElementById("card_store").getAttribute("all_cards"));
        this.oldOpponentHP = 30;
        this.oldSelfHP = 30;        
        this.oldOpponentArmor = 30;
        this.oldSelfArmor = 30;        
    }

    usernameOrP1(game) {
        if (this.username == game.players[0].username || this.username == game.players[1].username) {
            return this.username;
        }
        return game.players[0].username;
    }


    thisPlayer(game) {
        for(let player of game.players) {
            if (player.username == this.username) {
                return player
            }
        }
        return game.players[0];
    }

    opponent(game) {
        let thisPlayer = this.thisPlayer(game);
        if (thisPlayer == game.players[1]) {
            return game.players[0];
        }
        return game.players[1];
    }

    updateUsername(game) {
        document.getElementById("username").innerHTML = this.thisPlayer(game).username + " (me)";
    }

    updateRace(game) {
        document.getElementById("race").innerHTML = this.thisPlayer(game).race;
    }

    updateOpponentRace(game) {
        document.getElementById("opponent_race").innerHTML = this.opponent(game).race;
    }

    updateHitPoints(game) {
        if(this.thisPlayer(game).hit_points < this.oldSelfHP) {
            this.oldSelfHP = this.thisPlayer(game).hit_points;
            this.showDamage(game, this.opponent(game));            
        }
        if(this.thisPlayer(game).armor < this.oldSelfArmor) {
            this.oldSelfArmor = this.thisPlayer(game).armor;
            this.showDamage(game, this.opponent(game));            
        }
        document.getElementById("hit_points").innerHTML = this.thisPlayer(game).hit_points + " hp";
        document.getElementById("armor").innerHTML = this.thisPlayer(game).armor + " armor";
    }

    updateMana(game) {
        document.getElementById("mana").innerHTML = "Mana: " + this.manaString(this.thisPlayer(game).max_mana, this.thisPlayer(game).mana);
    }
    manaString(maxMana, currentMana) {
        var manaString = "";

        for (var i=0;i<currentMana;i++) {
            manaString += "✦"
        }
        for (var i=0;i<maxMana-currentMana;i++) {
            manaString += "✧"
        }
        return manaString
    }

    updatePlayerBorder(game) {
        if (this.thisPlayer(game).can_be_clicked && this.isActivePlayer(game)) {
            document.getElementById("player1").style.border = "4px solid orange";    
        } else {            
            document.getElementById("player1").style.border = "4px solid #765C48";    
        }
    }

    updateOpponentBorder(game) {
        if (this.opponent(game).can_be_clicked && this.isActivePlayer(game)) {
            document.getElementById("opponent").style.border = "4px solid orange";    
        } else {            
            document.getElementById("opponent").style.border = "4px solid #765C48";    
        }
    }

    updateOpponentUsername(game) {
        this.opponentUsername = this.opponent(game).username;
        document.getElementById("opponent_username").innerHTML = this.opponent(game).username + " (opponent)";
    }

    updateOpponentHitPoints(game) {
        if(this.opponent(game).hit_points < this.oldOpponentHP) {
            this.oldOpponentHP = this.opponent(game).hit_points;
            this.showDamage(game, this.thisPlayer(game));            
        }
        if(this.opponent(game).armor < this.oldOpponentArmor) {
            this.oldOpponentArmor = this.opponent(game).armor;
            this.showDamage(game, this.thisPlayer(game));            
        }
        document.getElementById("opponent_hit_points").innerHTML = this.opponent(game).hit_points + " hp";
        document.getElementById("opponent_armor").innerHTML = this.opponent(game).armor + " armor";
    }

    updateStartingEffectsForPlayer(player, divId) {
        let div = document.getElementById(divId);
        if (player.global_effects && player.global_effects.length > 0) {
            div.innerHTML = "Starting Effects: ";
            for (let effects of player.global_effects) {
             div.innerHTML += effect.name + " | ";
            }
        } else {
            div.innerHTML = "";            
        }
    }

    updateStartingEffects(game) {
        this.updateStartingEffectsForPlayer(this.thisPlayer(game), "global_effects");
    }

    updateOpponentStartingEffects(game) {
        this.updateStartingEffectsForPlayer(this.opponent(game), "opponent_global_effects");
    }

    updateAddedAbilitiesForPlayer(player, divId) {
        let div = document.getElementById(divId);
        if (player.abilities.length > 0) {
            div.innerHTML = "Added Abilities: ";
            for (let ability of player.abilities) {
             div.innerHTML += ability.name + " | "
            }
        } else {
            div.innerHTML = "";            
        }
    }

    updateAddedAbilities(game) {
        this.updateAddedAbilitiesForPlayer(this.thisPlayer(game), "added_abilities");
    }

    updateOpponentAddedAbilities(game) {
        this.updateAddedAbilitiesForPlayer(this.opponent(game), "opponent_added_abilities");
    }

    updateOpponentMana(game) {
        document.getElementById("opponent_mana").innerHTML = "Mana: " + this.manaString(this.opponent(game).max_mana, this.opponent(game).mana);
    }

    updateOpponentCardCount(game) {
        document.getElementById("opponent_card_count").innerHTML = "Hand: " + this.opponent(game).hand.length + " cards";                    
    }

    updateDeckCount(game) {
        document.getElementById("deck_count").innerHTML = "Deck: " + this.thisPlayer(game).deck.length + " cards";                    
    }

    updateOpponentDeckCount(game) {
        document.getElementById("opponent_deck_count").innerHTML = "Deck: " + this.opponent(game).deck.length + " cards";                    
    }

    updatePlayedPileCount(game) {
        document.getElementById("played_pile_count").innerHTML = "Played: " + this.thisPlayer(game).played_pile.length + " cards";                    
    }

    updateOpponentPlayedPileCount(game) {
        document.getElementById("opponent_played_pile_count").innerHTML = "Played: " + this.opponent(game).played_pile.length + " cards";                    
    }

    updateTurnLabel(game) {
        document.getElementById("turn_label").innerHTML = "Turn " + game.turn;                                
    }

    updateHand(game) {
        let handDiv = document.getElementById("hand");
        handDiv.innerHTML = '';
        for (let card of this.thisPlayer(game).hand) {
            handDiv.appendChild(this.cardSprite(game, card, this.usernameOrP1(game)));
        }
    }

    updateRelics(game) {
        var relicsDiv = document.getElementById("relics");
        if (this.thisPlayer(game).relics.length == 0 &&
            relicsDiv.innerHTML.startsWith("Play")) {
            relicsDiv.style.color = "white";
            return;
        }
        relicsDiv.style.color = "black";
        relicsDiv.innerHTML = '';
        for (let card of this.thisPlayer(game).relics) {
            relicsDiv.appendChild(this.cardSprite(game, card, this.usernameOrP1(game)));
        }        
    }

    updateOpponentRelics(game) {
        var relicsDiv = document.getElementById("opponent_relics");
        relicsDiv.innerHTML = '';
        for (let card of this.opponent(game).relics) {
            relicsDiv.appendChild(this.cardSprite(game, card, this.usernameOrP1(game)));
        }        
    }

    updateInPlay(game) {
        var inPlayDiv = document.getElementById("in_play");
        inPlayDiv.innerHTML = '';
        for (let card of this.thisPlayer(game).in_play) {
            inPlayDiv.appendChild(this.cardSprite(game, card, this.usernameOrP1(game)));
        }        
    }

    updateOpponentInPlay(game) {
        let opponentInPlayDiv = document.getElementById("opponent_in_play");
        opponentInPlayDiv.innerHTML = '';
        for (let card of this.opponent(game).in_play) {
            opponentInPlayDiv.appendChild(this.cardSprite(game, card, this.usernameOrP1(game)));
        }
    }

    showDamage(game, target) {
        var avatar = "opponent";
        if (target == this.opponent(game)) {
            avatar = "player1";
        }
        document.getElementById(avatar).style.backgroundColor = "red";
        setTimeout(function() {
            document.getElementById(avatar).style.backgroundColor = "#DFBF9F";
        }, 400);
    }

    isActivePlayer(game) {
        return (game.turn % 2 == 0 && this.usernameOrP1(game) == game.players[0].username
                || game.turn % 2 == 1 && this.usernameOrP1(game) == game.players[1].username)
    }

    cardSprite(game, card, username, dont_attach_listeners) {
        let cardDiv = document.createElement("div");
        cardDiv.id = "card_" + card.id;
        cardDiv.effects = card.effects;
        cardDiv.style = 'position:relative;margin-right:2px;cursor: pointer;height:114px;width:81px;border-radius:4px;padding:5px;font-size:12px;overflow:hidden';
        if (card.attacked) {
            cardDiv.style.backgroundColor = "#C4A484";                
        } else if (card.selected) {
            cardDiv.style.backgroundColor = "orange";                            
        } else {
            cardDiv.style.backgroundColor = "#DFBF9F";            
        }
        if (this.isActivePlayer(game)) {
            if (card.can_be_clicked) {
                cardDiv.style.border = "3px solid yellow";                
            } else {
                cardDiv.style.border = "3px solid #C4A484";                            
            }
        } else {
            cardDiv.style.border = "3px solid #C4A484";                            
        }

        if (card.shielded) {
            var div = document.createElement("div");
            div.style.backgroundColor = 'white';
            div.style.opacity = ".5";
            div.style.height = "100%";
            div.style.width = "100%";
            div.style.position = "absolute";
            div.style.top = 0;
            div.style.left = 0;
            div.style.pointerEvents = "none";
            cardDiv.appendChild(div)
        }

        if (card.abilities.length > 0 && card.abilities[0].descriptive_id == "Lurker" && card.abilities[0].enabled && card.turn_played > -1) {
            cardDiv.style.backgroundColor = 'black';
            cardDiv.style.color = 'white';
            cardDiv.style.opacity = ".6";
        }

        if (card.card_type != "Effect") {
            let costDiv = document.createElement("b");
            costDiv.innerHTML = card.cost;
            costDiv.style.position = 'absolute';
            costDiv.style.top = '5px';
            costDiv.style.right = '5px';
            cardDiv.appendChild(costDiv)
        }

        let nameDiv = document.createElement("b");
        nameDiv.style.display = 'inline-block';
        nameDiv.style.height = '30px';
        nameDiv.style.width = '61px';
        nameDiv.innerHTML = card.name;
        cardDiv.appendChild(nameDiv)


        let activatedEffects = [];
        let attackEffect = null;
        for (let e of card.effects) {
            if (e.effect_type == "activated" && e.enabled) {
                activatedEffects.push(e)
                if (e.name == "attack" || e.name == "make_random_townie") {
                    attackEffect = e;
                }
            }
        }

        let descriptionDiv = document.createElement("div");
        descriptionDiv.style.maxHeight = "60px"
        cardDiv.appendChild(descriptionDiv);
        if (card.description) {
            // todo don't hardcode hide description for Infernus
            // todo don't hardcode hide description for Winding One
            if (card.card_type == "Entity" && activatedEffects.length == 0) {
                descriptionDiv.innerHTML = card.description;
            } else if (card.card_type != "Entity" && activatedEffects.length < 2) {
                descriptionDiv.innerHTML = card.description;
            }
            if (card.turn_played == -1) {
                descriptionDiv.innerHTML = card.description;
            }
        }

        if (card.added_descriptions.length) {
            for (let d of card.added_descriptions) {
                let addedDescriptionDiv = document.createElement("div");
                addedDescriptionDiv.innerHTML = d;
                descriptionDiv.appendChild(addedDescriptionDiv);                
            }
        }

        let abilitiesDiv = document.createElement("div");
        abilitiesDiv.style.color = "gray"
        for (let a of card.abilities) {
            if (!["Starts in Play", "die_to_top_deck", "discard_random_to_deck"].includes(a.descriptive_id)) {
                abilitiesDiv.innerHTML += a.name;
                if (a != card.abilities[card.abilities.length-1]) {                
                    abilitiesDiv.innerHTML += ", ";
                }                
            }
        }
        descriptionDiv.appendChild(abilitiesDiv);

        if (card.card_type == "Entity") {
            let cardPower = card.power;
            let cardToughness = card.toughness - card.damage;
            if (card.tokens) {
                for (let c of card.tokens) {
                    cardPower += c.power_modifier;
                }
                for (let c of card.tokens) {
                    cardToughness += c.toughness_modifier;
                }
            }
            let powerToughnessDiv = document.createElement("em");
            powerToughnessDiv.innerHTML = cardPower + "/" + cardToughness;
            powerToughnessDiv.style.position = "absolute";
            powerToughnessDiv.style.bottom = "0px";
            powerToughnessDiv.style.right = "0px";
            powerToughnessDiv.style.backgroundColor = "black"
            powerToughnessDiv.style.color = "white";
            powerToughnessDiv.style.paddingLeft = "3px"
            powerToughnessDiv.style.paddingRight = "3px"
            powerToughnessDiv.style.borderRadius = "3px"
            cardDiv.appendChild(powerToughnessDiv);
        } else if (card.turn_played == -1) {
            let typeDiv = document.createElement("em");
            typeDiv.innerHTML = card.card_type;
            typeDiv.style.position = "absolute";
            typeDiv.style.bottom = "0px";
            typeDiv.style.right = "0px";
            typeDiv.style.backgroundColor = "black"
            typeDiv.style.color = "white";
            typeDiv.style.paddingLeft = "3px"
            typeDiv.style.paddingRight = "3px"
            typeDiv.style.borderRadius = "3px"
            cardDiv.appendChild(typeDiv);           
        }

        if (attackEffect) {
            let powerChargesDiv = document.createElement("em");
            powerChargesDiv.innerHTML = attackEffect.power + "/" + attackEffect.counters;
            powerChargesDiv.style.position = "absolute";
            powerChargesDiv.style.bottom = "0px";
            powerChargesDiv.style.left = "0px";
            powerChargesDiv.style.backgroundColor = "black"
            powerChargesDiv.style.color = "white";
            powerChargesDiv.style.paddingLeft = "3px"
            powerChargesDiv.style.paddingRight = "3px"
            powerChargesDiv.style.borderRadius = "3px"
            cardDiv.appendChild(powerChargesDiv);                       
        }

        if ((card.card_type != "Entity" && activatedEffects.length > 1) || (card.card_type == "Entity" && activatedEffects.length > 0)) {
            if (card.turn_played > -1) {
                var index = 0;
                for (let e of activatedEffects) {
                    if (!e.enabled) {
                        continue;
                    }
                    var input = document.createElement("div");
                    input.effect_index = index;
                    input.className = "button"
                    input.style.width = "76px";
                    if (activatedEffects.length == 1) {
                        input.style.height = "30px";                        
                        input.style.fontSize = "12px";
                    } else {
                        input.style.fontSize = "10px";
                        input.style.height = "15px";                        
                    }
                    input.style.padding = "4px";
                    input.style.marginTop = "10px";
                    input.style.textAlign = "left";
                    input.style.zIndex = 10;
                    input.innerHTML = e.description;
                    if (e.cost <= this.thisPlayer(game).mana && card.effects_can_be_clicked[index] && !this.thisPlayer(game).card_info_to_resolve["card_id"]) {
                        input.disabled = false;                
                        input.style.backgroundColor = "yellow"
                        input.style.color = "black"
                    } else {
                        input.disabled = true;
                        input.style.backgroundColor = "lightgray"
                        input.style.color = "white"
                    }
                    var self = this;
                    input.onclick = function(event) { 
                        if (e.cost <= self.thisPlayer(game).mana) {
                            if (card.card_type == "Relic" && e.target_type == "self_entity") {
                                self.sendPlayMoveEvent("SELECT_RELIC", {"card":card.id, "effect_index": this.effect_index});
                            } else if (card.card_type == "Relic" && e.target_type == "self") {
                                self.sendPlayMoveEvent("ACTIVATE_RELIC", {"card":card.id, "effect_index": this.effect_index});
                            } else if (true) {
                                self.sendPlayMoveEvent("ACTIVATE_ENTITY", {"card":card.id, "effect_index": this.effect_index});
                            }
                        }
                        event.stopPropagation()
                    };
                    cardDiv.appendChild(input);
                    index += 1;
                }
            }
        }

        cardDiv.onclick = function() {
            if (cardDiv.parentElement.parentElement == document.getElementById("hand")) {  
                self.sendPlayMoveEvent("SELECT_CARD_IN_HAND", {"card":card.id});
            } else if (cardDiv.parentElement.parentElement == document.getElementById("in_play") || cardDiv.parentElement.parentElement == document.getElementById("opponent_in_play")) {  
                self.sendPlayMoveEvent("SELECT_ENTITY", {"card":card.id, "effect_index": -1});
            } else { 
                console.log("FOOP");
                self.sendPlayMoveEvent("SELECT_RELIC", {"card":card.id, "effect_index": -1});
            }            
        }


        // todo: don't hardcode for Winding One
        /* f (card.effects.length > 0 && card.effects[0].effect_type == "activated" && card.effects[0].target_type == "entity" && card.turn_played > -1) {
            var input = document.createElement("div");
            input.className = "button"
            input.style.width = "70px";
            input.style.height = "25px";
            input.style.fontSize = "10px";
            input.style.padding = "5px";
            input.style.marginTop = "10px";
            input.style.textAlign = "left";
            input.innerHTML = "✦✦✦: unwind an entity";
            if (card.effects[0].cost <= this.thisPlayer(game).mana && card.can_activate_abilities) {
                input.disabled = false;                
                input.style.backgroundColor = "blue"
            } else {
                input.disabled = true;
                input.style.backgroundColor = "lightgray"
            }
            var self = this;
            input.onclick = function(event) { 
                if (card.effects[0].cost <= self.thisPlayer(game).mana) {
                    self.sendPlayMoveEvent("ACTIVATE_ENTITY", {"card":card.id});
                }
                event.stopPropagation()
            };
            cardDiv.appendChild(input);
        }

        cardDiv.addEventListener('mouseleave', function(){
            if(document.getElementById("bigger_card")) {
                cardDiv.style.height = "114px";
                cardDiv.style.width = "81px";
                document.getElementById("bigger_card").parentNode.removeChild(document.getElementById("bigger_card"));4            
            }
        }, false);   
         */
        if (dont_attach_listeners) {
            var span = document.createElement("span");
            span.appendChild(cardDiv)
            return span;
        }
        var self = this;
       /* 
        var cancel = false;
        let clickTime;
        cardDiv.addEventListener('mousedown', function(){
            clickTime = new Date();
            setTimeout(function() { 
                if (!cancel) {
                     var cln = cardDiv.cloneNode(true);
                     cln.id = "bigger_card";
                     cln.style.height = "171px";
                     cln.style.width = "120px"; 
                     cln.style.position = "absolute"; 
                     cln.style.left = "400px"; 
                     cln.style.top = document.getElementById("all_but_player_hand").innerHeight / 2;
                     document.getElementById("all_but_player_hand").appendChild(cln)
                }
                cancel = false;
            }, 150);
        }, false);   

        cardDiv.addEventListener('mouseup', function(event){
            cardDiv.style.height = "114px";
            cardDiv.style.width = "81px";
            if(document.getElementById("bigger_card")) {
                document.getElementById("bigger_card").parentNode.removeChild(document.getElementById("bigger_card"));
            }

            // event.stopPropagation();

            function captureClick(e) {
                if (new Date() - clickTime < 150) {
                    // play the card if it's a quick click
                    if (cardDiv.parentElement.parentElement == document.getElementById("hand")) {  
                        self.sendPlayMoveEvent("SELECT_CARD_IN_HAND", {"card":card.id});
                    } else if (cardDiv.parentElement.parentElement == document.getElementById("in_play") || cardDiv.parentElement.parentElement == document.getElementById("opponent_in_play")) {  
                        self.sendPlayMoveEvent("SELECT_ENTITY", {"card":card.id, "effect_index": 0});
                    } else { 
                        console.log("foop")
                        self.sendPlayMoveEvent("SELECT_RELIC", {"card":card.id, "effect_index": 0});
                    }
                    cancel = true;
                } else {
                    // just shrink the zoom
                }
                // e.stopPropagation(); // Stop the click from being propagated.
                window.removeEventListener('click', captureClick, true); // cleanup
            }

            window.addEventListener(
                'click',
                captureClick,
                true // <-- This registeres this listener for the capture
                     //     phase instead of the bubbling phase!
            ); 

        }, false);   
*/

        var span = document.createElement("span");
        span.appendChild(cardDiv)
        return span;
    }

    selfClick () {
        this.sendPlayMoveEvent("SELECT_SELF", {});
    }

    opponentClick () {
        // this -1 and the one in selfClick should instead store the last effect being targetted in the. game state instead
        this.sendPlayMoveEvent("SELECT_OPPONENT", {});
    }

    viewHelp() {
        alert("1. Click cards in hand to play them.\n2. To attack, click your entity, then your opponent's.\n3. To attack your opponent's face, double click an entity or click your entity then the opponent.\n4. To cast a spell at your opponent's entity, click your spell, then your opponent's entity.\n5. To cast a spell at your opponent's face, click a spell or click a spell then the opponent.\n6. Entities can't attack the turn they come into play.");
    }
   
    enableEndTurnButton(game) {
        document.getElementById("end-turn-button").style.backgroundColor = "red";
        if (this.thisPlayer(game).mana == 0) {
            document.getElementById("end-turn-button").style.border = "4px black solid";
        } else {            
            document.getElementById("end-turn-button").style.border = "4px red solid";
        }
        document.getElementById("end-turn-button").style.pointerEvents = "auto";
        document.getElementById("end-turn-button").innerHTML = "End Turn";
    }

    disableEndTurnButton(game) {
        document.getElementById("end-turn-button").style.border = "4px lightgray solid";
        document.getElementById("end-turn-button").style.backgroundColor = "lightgray";
        document.getElementById("end-turn-button").style.pointerEvents = "none";
        document.getElementById("end-turn-button").innerHTML = "Opponent's Turn";
    }
   
    refresh(game) {
        if (this.opponent(game)) {
            if (this.isActivePlayer(game)) {
                this.enableEndTurnButton(game);
            } else {
                this.disableEndTurnButton(game);            
            }
            this.updateTurnLabel(game);
            this.updateOpponentCardCount(game);
            this.updateOpponentMana(game);
            this.updateOpponentHitPoints(game);
            this.updateOpponentInPlay(game);
            this.updateOpponentRelics(game);
            this.updateOpponentDeckCount(game);
            this.updateOpponentPlayedPileCount(game);
            this.updateOpponentBorder(game);
            this.updateOpponentAddedAbilities(game);
            this.updateOpponentStartingEffects(game);
            this.updateOpponentUsername(game);
            this.updateOpponentRace(game);
        }
        if (this.thisPlayer(game)) {
            this.updateMana(game);
            this.updateHitPoints(game);
            this.updateInPlay(game);
            this.updateRelics(game);
            this.updateHand(game);
            this.updateDeckCount(game);
            this.updatePlayedPileCount(game);
            this.updatePlayerBorder(game);
            this.updateStartingEffects(game);
            this.updateAddedAbilities(game);
            this.updateUsername(game);
            this.updateRace(game);
        }
        if (this.opponent(game) && this.thisPlayer(game)) {
            if (this.opponent(game).hit_points <= 0 || this.thisPlayer(game).hit_points <= 0) {
                alert("GAME OVER");
            }
        }
        if ((this.gameType == "choose_race" || this.gameType == "choose_race_prebuilt") && (!game.players[0].race || !game.players[1].race)) {
            this.showChooseRace(game);
        } else if (this.thisPlayer(game).card_choice_info.cards.length && this.thisPlayer(game).card_choice_info.choice_type == "make") {
            this.showMakeView(game);
        } else if (this.thisPlayer(game).card_choice_info.cards.length && this.thisPlayer(game).card_choice_info.choice_type == "fetch_relic_into_hand") {
            this.showChooseCardView(game, "FETCH_CARD");
        } else if (this.thisPlayer(game).card_choice_info.cards.length && this.thisPlayer(game).card_choice_info.choice_type == "fetch_relic_into_play") {
            this.showChooseCardView(game, "FETCH_CARD_INTO_PLAY");
        } else if (this.thisPlayer(game).card_choice_info.cards.length && this.thisPlayer(game).card_choice_info.choice_type == "view_hand") {
            this.showRevealView(game);
        } else {
            this.showGame();
        }                           
    }
    
    showChooseRace(game) {
        var raceSelector = document.getElementById("race_selector");
        if (raceSelector.style.display == "block") {
            return;
        }
        raceSelector.style.display = "block";
        raceSelector.style.maxWidth = "1024px";
        raceSelector.style.padding = "10px";
        raceSelector.style.backgroundColor = "white";
        document.getElementById("race_selector").innerHTML = "";

        var h1 = document.createElement("h1");
        h1.innerHTML = "Choose Race"
        raceSelector.appendChild(h1);

        var p = document.createElement("p");
        p.innerHTML = "Your race affects what cards you have access to in the game. Choose 1:"
        raceSelector.appendChild(p);

        var options = [
            {"id": "elf", "label": "Elf"},
            {"id": "genie", "label": "Genie"},
        ];

        var div = document.createElement("div");
        div.style.width = "100%";
        raceSelector.appendChild(div);

        var self = this
        for(var o of options) {
            var input = document.createElement("div");
            input.id = o.id;
            input.className = "button"
            input.innerHTML = o.label;
            input.style.marginRight = "20px";
            input.onclick = function() { 
                self.race = this.id;
                this.onclick = null;
                self.innerHTML = "Waiting for Opponent...";
                self.chooseRace(game, self.race) 
            };
            div.appendChild(input);
        }  

    }

    addRowToTableForCard(game, c, decks, table) {
        var input = document.createElement("input");
        input.id = c.name;
        input.name = "card";
        input.style.color = '000080';
        input.value = 1;
        if (this.usernameOrP1(game) in decks) {
            if (c.name in decks[this.usernameOrP1(game)]) {
               input.value = decks[this.usernameOrP1(game)][c.name];
            }
        }
        input.style.width = "50px";

        var label = document.createElement("b"); 
        label.for = c.id;
        label.innerHTML = c.name;

        var tr = document.createElement("tr");
        table.appendChild(tr);

        var tdName = document.createElement("td");
        tdName.style.border = "1px solid black";
        tdName.appendChild(label)
        tr.appendChild(tdName);
        if (c.card_type != "Spell") {
            tr.appendChild(tdForTitle(c.power));            
            tr.appendChild(tdForTitle(c.toughness));            
        }

        tr.appendChild(tdForTitle(c.description));            
        tr.appendChild(tdForTitle(c.cost));            
        var tdAmount = document.createElement("td");
        tdAmount.appendChild(input)
        tr.appendChild(tdAmount);

    }

    showGame() {
        document.getElementById("room").style.display = "block";
        document.getElementById("race_selector").style.display = "none";
        document.getElementById("make_selector").style.display = "none";
    }

    showMakeView(game) {
        var self = this;
        this.showSelectCardView(game, "make_selector", "Make a Card", function(card) {
                if (card.global_effect) {
                    self.sendPlayMoveEvent("MAKE_EFFECT", {"card":card});
                } else {
                    self.sendPlayMoveEvent("MAKE_CARD", {"card":card});
                }
            });
    }

   showRevealView(game) {
        this.showSelectCardView(game, "make_selector", "Opponent's Hand", null);
        var self = this;
        document.getElementById("make_selector").onclick = function() {
            self.sendPlayMoveEvent("HIDE_REVEALED_CARDS", {});
            self.showGame();
            this.onclick = null
        }
    }

    showChooseCardView(game, event_name) {
        var self = this;
        this.showSelectCardView(game, "make_selector", "Relics in Your Deck", function (card) {
                self.sendPlayMoveEvent(event_name, {"card":card.id});                
            });
        
    }

    showSelectCardView(game, element_id, title, card_on_click) {
        document.getElementById(element_id).innerHTML = "";
        var makeSelector = document.getElementById(element_id);
        makeSelector.style.display = "flex";
        makeSelector.style.background = "rgba(0, 0, 0, .7)";
        makeSelector.style.zIndex = "100";

        var container = document.createElement("div");
        container.style.width = "100%";
        container.style.height = 130+50+100 + "px";
        container.style.margin = "auto";
        container.style.backgroundColor = "white";
        makeSelector.appendChild(container);

        var cards = this.thisPlayer(game).card_choice_info["cards"];

        var h1 = document.createElement("h1");
        h1.innerHTML = title
        container.appendChild(h1);
        container.appendChild(document.createElement('br'));
        container.appendChild(document.createElement('br'));

        var cardContainerDiv = document.createElement('div');
        cardContainerDiv.classList.add("card_container");
        container.appendChild(cardContainerDiv);

        let clickTime;
        let cancel = false;
        for (let card of cards) {
            let cardDiv = this.cardSprite(game, card, this.usernameOrP1(game), true);
            cardContainerDiv.appendChild(cardDiv);
            cardDiv.addEventListener('mousedown', function(){
                clickTime = new Date();
                setTimeout(function() { 
                    if (!cancel) {
                        cardDiv.children[0].style.height = "171px";
                        cardDiv.children[0].style.width = "120px";                    
                    }
                    cancel = false;
                }, 150);
            }, false);   

            if (card_on_click == null) {
               cardDiv.style.pointerEvents = "none";
                cardDiv.children[0].addEventListener('mouseup', function(event){
                    cardDiv.children[0].style.height = "114px";
                    cardDiv.children[0].style.width = "81px";
                    event.stopPropagation();

                    function captureClick(e) {
                        if (new Date() - clickTime < 150) {
                            // do nothing for a click
                            cancel = true;
                        } else {
                            // just shrink the zoom
                        }
                        e.stopPropagation(); // Stop the click from being propagated.
                        window.removeEventListener('click', captureClick, true); // cleanup
                    }

                    window.addEventListener(
                        'click',
                        captureClick,
                        true // <-- This registeres this listener for the capture
                             //     phase instead of the bubbling phase!
                    ); 

                }, false);   
            } else {
                cardDiv.children[0].addEventListener('mouseup', function(event){
                    cardDiv.children[0].style.height = "114px";
                    cardDiv.children[0].style.width = "81px";
                    event.stopPropagation();

                    function captureClick(e) {
                        if (new Date() - clickTime < 150) {
                            // play the card if it's a quick click
                            card_on_click(card);
                            cancel = true;
                        } else {
                            // just shrink the zoom
                        }
                        e.stopPropagation(); // Stop the click from being propagated.
                        window.removeEventListener('click', captureClick, true); // cleanup
                    }

                    window.addEventListener(
                        'click',
                        captureClick,
                        true // <-- This registeres this listener for the capture
                             //     phase instead of the bubbling phase!
                    ); 

                }, false);   

            }
        }
    }

    endTurn() {
        this.sendPlayMoveEvent("END_TURN", {});
    }

    chooseRace(game, race) {
        this.sendPlayMoveEvent("CHOOSE_RACE", {"race": race});
    }

    logMessage(log_lines) {
        for (let text of log_lines) {
            var line = this.addLogLine();
            line.innerHTML = text
        }
        this.scrollLogToEnd()
    }

    addLogLine() {
        var line = document.createElement('div');
        document.getElementById("game_log_inner").appendChild(line);
        return line;
    }

    scrollLogToEnd() {
        document.getElementById("game_log_inner").scrollTop = document.getElementById("game_log_inner").scrollHeight;
    }

    nextRoom() {
        if (this.gameRoom.gameSocket.readyState != WebSocket.OPEN) {
            window.location.href = this.gameRoom.nextRoomUrl();
        }

        this.gameRoom.gameSocket.send(JSON.stringify(
            {"move_type": "NEXT_ROOM", "username":this.username}
        ));
    }

    sendPlayMoveEvent(move_type, info) {
        info["move_type"] = move_type
        info["username"] = this.username
        this.gameRoom.gameSocket.send(JSON.stringify(
            info
        ));                
    }

}


class GameRoom {

    gameSocket = null;

    constructor(gameUX) {
        this.gameUX = gameUX;
        gameUX.gameRoom = this;
    }

    connect() {
        if (this.gameSocket == null) {
            this.setupSocket();
        }
        if (this.gameSocket.readyState == WebSocket.OPEN) {
            const deck_id = document.getElementById("card_store").getAttribute("deck_id");
            if (deck_id) {
                this.gameUX.sendPlayMoveEvent("JOIN", { deck_id });                
            }
            console.log('WebSockets connection created.');
        } else {
            var self = this;
            setTimeout(function () {
                self.connect();
            }, 100);
        }
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
            } else {
                let game = data["game"];
                if (!data["game"]) {
                    console.log(data);                    
                }
                self.gameUX.refresh(game);
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
        var roomNumber = parseInt(url.split( '/' ).pop()) + 1;
        var usernameParameter = getSearchParameters()["username"];
        var nextRoomUrl = "/play/" + this.gameUX.aiType + "/" + this.gameUX.gameType + '/' + roomNumber;
        var getParams =  "?username=" + usernameParameter + "&new_game_from_button=true";
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
            nextRoomUrl = "/play/custom/" + roomNumber+ '/'  + customGameId + getParams;
        }
        return nextRoomUrl;
    }
}

function tdForTitle(title) {
    var td = document.createElement("td");
    td.style.border = "1px solid black";
    td.innerHTML = title;
    return td;
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