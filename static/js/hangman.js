var gameDiv = document.getElementById("game");

var infoDiv = document.createElement("p");
infoDiv.innerHTML = "There are 3 of me in the house. You have visited one, and you need to visit another.<br/><br/>"
gameDiv.appendChild(infoDiv);

var clueDiv = document.createElement("b");
clueDiv.id = "clue"
clueDiv.innerHTML = "_ _ _ _ _ _ _"
gameDiv.appendChild(clueDiv);

var questionDiv = document.createElement("p");
questionDiv.style = "font-weight:bold"
questionDiv.innerHTML = "Type a letter to guess at the clue, but don't guess too many times!"
gameDiv.appendChild(questionDiv);

// riddle to hangman upstairs

// 3 of me and youve already been to one
// bath tub

var guesses = [];
document.addEventListener('keydown', function (event) {
	guesses.push(event.key);

	var displayString = "b a t h t u b";
	for (var i = 0; i < displayString.length; i++) {
		let char = displayString.charAt(i);
		if (char == " ") {
			continue;
		}
	  if (!guesses.includes(char)) {
	  	displayString = displayString.substring(0, i) + '_' + displayString.substring(i + 1);
	  }
	}
	var clueDiv = document.getElementById("clue");
	clueDiv.innerHTML = displayString;

	if (checker(guesses, "bathu".split(""))) {
		alert("You have guessed the clue, it is BATHTUB!");
	}

});
let checker = (arr, target) => target.every(v => arr.includes(v));
