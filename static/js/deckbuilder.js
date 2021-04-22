class DeckBuilder {

	constructor() {
    	this.deck = {cards: {}, id: null}
    	this.deckSize = 0
    	this.allCards = JSON.parse(document.getElementById("data_store").getAttribute("all_cards"));
  	}

	save() {
		alert("save");
	}

	showHelp() {
		alert("showHelp");
	}

	loadDeck() {
		alert("loadDeck");
	}

	loadAllCards() {
        for(var c of this.allCards) {
            this.addRowToAllCards(c, "all_cards_container");
        }   
	}

   addRowToAllCards(c, containerId) {
        var cardRow = document.createElement("div");
        cardRow.id = c.name;
        cardRow.style.height = "40px";
        cardRow.style.width = "95%";
        cardRow.style.backgroundColor = "white";
        cardRow.style.border = "2px solid black";
        cardRow.style.cornerRadius = "4px";
        cardRow.style.margin = "5px";
        cardRow.style.marginBottom = "10px";
        cardRow.style.padding = "5px";
		cardRow.style.display = "flex";
		cardRow.style.justifyContent = "space-between";

        var self = this;
        cardRow.onclick = function() {
        	if (self.deckSize == 30) {
        		console.log("deck's can only have 30 cards");
        		return;
        	}
        	if (!(c.name in self.deck["cards"])) {
        		self.deck["cards"][c.name] = 1
        		self.deckSize += 1;
        	} else if (self.deck["cards"][c.name] == 1) {
        		self.deck["cards"][c.name] = 2        		
        		self.deckSize += 1;
        	} else {
        		console.log("can't add more than 2 cards")
        		return;
        	}
        	self.redisplayDeck();
        } 
        var nameBold = document.createElement("b"); 
        nameBold.innerHTML = c.name;
        cardRow.appendChild(nameBold);

        if (self.deck["cards"][c.name] == 2) {
	        var countBold = document.createElement("b"); 
	        countBold.innerHTML = self.deck["cards"][c.name];
	        cardRow.appendChild(countBold);
        }

        document.getElementById(containerId).appendChild(cardRow);
    }

	redisplayDeck() {
		document.getElementById("new_deck_container").style = null;
		document.getElementById("new_deck_container").innerHTML = null;
        for (var dcName in this.deck["cards"]) {
        	for(var ac of this.allCards) {
        		if (ac.name == dcName) {
			    	this.addRowToAllCards(ac, "new_deck_container");
        		}
        	}   
		}

		if (this.deckSize == 2) {
			document.getElementById("save_button").style.backgroundColor = "green";
			document.getElementById("save_button").style.color = "white";
        	var self = this;
			document.getElementById("save_button").onclick = function() {
				self.saveDeck()
			}
		}
	}

	saveDeck() {
		var usernameDiv = document.getElementById("username");
		if(!usernameDiv.value.length) {
			alert("username required");
			return;
		}
		this.postData('/build_deck/create', { username: usernameDiv.value, deck: this.deck })
	  	.then(data => {
	  		if("error" in data) {
		    	console.log(data); // JSON data parsed by `data.json()` call
		    	alert("error saving deck");
	  		} else {
	  			window.location.href = `/u/${usernameDiv.value}?username=${usernameDiv.value}`
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
