class DeckBuilder {

	constructor(deck) {
		this.username = document.getElementById("data_store").getAttribute("username");
		this.deck = JSON.parse(deck);
		this.allCards = JSON.parse(document.getElementById("data_store").getAttribute("all_cards"));
	}

	loadAllCards() {
		for(var c of this.allCards) {
			this.addCardToContainer(c, "all_cards_container");
		}   
	}

	deckSize() {
		var count = 0;		
		for (var dcName in this.deck["cards"]) {
			count += this.deck["cards"][dcName];
		}
		return count;
	}

	cardFCorName(cardName) {
		for (var c of this.allCards) {
			if (c.name == cardName) {
				return c;
			}
		}
	}

	addCardToContainer(card, containerId) {
		var cardRow = document.createElement("div");
		cardRow.id = card.name;
		cardRow.style.height = "80px";
		cardRow.style.width = "94%";
		cardRow.style.backgroundColor = "#DFBF9F";
		cardRow.style.border = "4px solid #C4A484";
		cardRow.style.borderRadius = "4px";
		cardRow.style.margin = "5px";
		cardRow.style.marginBottom = "10px";
		cardRow.style.padding = "5px";
		cardRow.style.position = "relative";

		var self = this;
		if (containerId == "all_cards_container") {
			cardRow.onclick = function() {
				if (self.deckSize() == 30) {
					console.log("deck's can only have 30 cards");
					return;
				}
				if (!(card.name in self.deck["cards"])) {
					self.deck["cards"][card.name] = 1
				} else if (self.deck["cards"][card.name] == 1 && card.card_type == "Relic") {
					console.log("can't add more than 1 relic")
					return;
				} else if (self.deck["cards"][card.name] == 1) {
					self.deck["cards"][card.name] = 2				
				} else {
					console.log("can't add more than 2 cards")
					return;
				}
				self.redisplayDeck();
			} 
		} else {
			cardRow.onclick = function() {
				self.deck["cards"][card.name] -= 1
				if (self.deck["cards"][card.name] == 0) {
					delete self.deck["cards"][card.name];
				}
				self.redisplayDeck();
			}		 	
		}

		var nameBold = document.createElement("b"); 
		nameBold.innerHTML = card.name;
		cardRow.appendChild(nameBold);

		let costDiv = document.createElement("b");
	    costDiv.innerHTML = card.cost;
	    costDiv.style.position = 'absolute';
	    costDiv.style.top = '5px';
	    costDiv.style.right = '5px';
	    cardRow.appendChild(costDiv)

		if (card.description) {
			let descriptionDiv = document.createElement("div");
			descriptionDiv.innerHTML = card.description;
			cardRow.appendChild(descriptionDiv);
		}
		if (card.card_type != "Spell" && card.card_type != "Relic" ) {
			if(card.abilities) {
		        let abilitiesDiv = document.createElement("div");
		        for (let a of card.abilities) {
		            abilitiesDiv.innerHTML += a.name;
		            if (a != card.abilities[card.abilities.length-1]) {                
		                abilitiesDiv.innerHTML += ", ";
		            }
		        }
        		cardRow.appendChild(abilitiesDiv);
			}
			let powerToughnessDiv = document.createElement("div");
			powerToughnessDiv.innerHTML = card.power + "/" + card.toughness;
            powerToughnessDiv.style.position = "absolute";
            powerToughnessDiv.style.bottom = "0px";
			cardRow.appendChild(powerToughnessDiv);
		} else {
			let typeDiv = document.createElement("div");
			typeDiv.innerHTML = card.card_type;
            typeDiv.style.position = "absolute";
            typeDiv.style.bottom = "0px";
			cardRow.appendChild(typeDiv);
			
		}

		 if (this.deck["cards"][card.name] == 2 && containerId == "new_deck_container") {
			var countBold = document.createElement("b"); 
			countBold.innerHTML = this.deck["cards"][card.name];
			cardRow.appendChild(countBold);
			countBold.style.position = "absolute";
			countBold.style.top = "5px";
			countBold.style.right = "5px";
			countBold.style.backgroundColor = "yellow";
			countBold.style.height = "16px";
			countBold.style.width = "16px";
			countBold.style.textAlign = "center";
			countBold.style.borderRadius = "8px";

		}


	   document.getElementById(containerId).appendChild(cardRow);
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

	redisplayDeck() {
		document.getElementById("deck_count").innerHTML = this.deckSize() + "/30";
		document.getElementById("new_deck_container").style = "min-height:1224px";;
		document.getElementById("new_deck_container").innerHTML = null;
		for (var dcName in this.deck["cards"]) {
			for(var ac of this.allCards) {
				if (ac.name == dcName) {
					this.addCardToContainer(ac, "new_deck_container");
				}
			}   
		}

		if (this.deckSize() == 30) {
			document.getElementById("save_button").disabled = false;
			document.getElementById("save_button").style.backgroundColor = "green";
			document.getElementById("save_button").style.color = "white";
			var self = this;
			document.getElementById("save_button").onclick = function() {
				self.saveDeck()
			}
		} else {
			document.getElementById("save_button").disabled = true;
			document.getElementById("save_button").style.backgroundColor = "lightgray";
			document.getElementById("save_button").onclick = null;
		}

		if (this.deckSize() == 0) {
			document.getElementById("new_deck_container").style = "padding:50px;padding-top:200px;text-align:center;font-size:16px;color:white;font-weight:bold;min-height:974px";
  			document.getElementById("new_deck_container").innerHTML = "Click cards on the left to add them to your deck. Decks must be 30 cards, no more than 2 of any card.";
		}
	}

	saveDeck() {
		this.postData('/build_deck/save', { username: this.username, deck: this.deck })
	  	.then(data => {
	  		if("error" in data) {
				console.log(data); // JSON data parsed by `data.json()` call
				alert("error saving deck");
	  		} else {
	  			window.location.href = `/u/${this.username}`
	  		}
	  	});
	}

	async postData(url, data) {
		const csrftoken = getCookie('csrftoken');
	  	// Default options are marked with *
	  	const response = await fetch(url, {
			method: 'POST',
			headers: {
			  'Accept': 'application/json',
			  'Content-Type': 'application/json',
			  'X-CSRFToken': csrftoken,

			},
			body: JSON.stringify(data) 
		});
		return response.json(); // parses JSON response into native JavaScript objects
	}
}

function getCookie(name) {
	let cookieValue = null;
	if (document.cookie && document.cookie !== '') {
		const cookies = document.cookie.split(';');
		for (let i = 0; i < cookies.length; i++) {
			const cookie = cookies[i].trim();
			// Does this cookie string begin with the name we want?
			if (cookie.substring(0, name.length + 1) === (name + '=')) {
				cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
				break;
			}
		}
	}
	return cookieValue;
}
