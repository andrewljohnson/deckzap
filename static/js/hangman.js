var gameDiv = document.getElementById("game");

var infoDiv = document.createElement("p");
infoDiv.innerHTML = "The clue you seek,<br /> it's hard to speak,<br /> but you can find treasure<br /> in something used to _ _ _ _ _ _ _."
gameDiv.appendChild(infoDiv);

var questionDiv = document.createElement("p");
questionDiv.style = "font-weight:bold"
questionDiv.innerHTML = "Enter a letter to guess at the clue, but don't guess too man times!"
gameDiv.appendChild(questionDiv);