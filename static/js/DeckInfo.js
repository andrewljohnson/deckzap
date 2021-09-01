export class DeckInfo {

	constructor(discipline) {
		this.discipline = discipline
	}

	infoListText () {
		if (this.discipline == "magic") {
			return "• 30 card deck\n• more mana each turn\n• draw one card a turn";
		}
		return "• 15 card deck\n• 3 mana each turn\n• new hand each turn";
	}
}