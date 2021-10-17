import json

class Constants:    
    spellCardType = "spell"
    mobCardType = "mob"
    artifactCardType = "artifact"


def all_cards(require_images=False, include_tokens=True):
    """
        Returns a list of all possible cards in the game. 
    """
    json_data = open('battle_wizard/game/battle_wizard_cards.json')
    all_cards = json.load(json_data)
    subset = []
    for c in all_cards:
        if include_tokens or ("is_token" not in c or c["is_token"] == False):
            if "image" in c or not require_images:
                subset.append(c)

    json_data = open('battle_wizard/game/old_cards.json')
    all_cards = json.load(json_data)
    for c in all_cards:
        if include_tokens or ("is_token" not in c or c["is_token"] == False):
            if "image" in c or not require_images:
                subset.append(c)


    json_data = open('battle_wizard/game/cards/cards_and_effects.json')
    cards_and_effects = json.load(json_data)
    for c in cards_and_effects["cards"]:
        if include_tokens or ("is_token" not in c or c["is_token"] == False):
            if "image" in c or not require_images:
                c["discipline"] = "magic"
                description = ""
                for e in c["effects"]:
                    description += e["description"]
                    if e != c["effects"][-1]:
                        description += " "
                c["description"] = description                
                subset.append(c)

    return subset

def hash_for_deck(deck):
    strings = []
    for key in deck["cards"]:
        strings.append(f"{key}{deck['cards'][key]}")
    strings.sort()
    return "".join(strings)

def default_deck_genie_wizard():
    return {
        "title": "Draw Go",
        "url": "draw_go",
        "discipline": "magic",
        "cards": {
            "Mana Battery": 1,
            "Elemental Ritual": 2,
            "Push Soul": 2,
            "Lil' Maker": 2,
            "Brarium": 1,
            "Tame Time": 2,
            "Unwind": 2,
            "Counter Mob": 2,
            "Counter Spell": 2,
            "Quickster": 1,
            "Spell Archaeologist": 2,
            "Tame Tempest": 2,
            "Wish Stone": 1,
            "Orpheus Krustal": 1,
            "Crazy Control": 2,
            "Legendary Djinn": 2,
            "Nonapug Whistle": 2,
            "Quasar Tap": 1
        }
    }

def default_deck_vampire_lich():
    return {
        "title": "The Coven",
        "url": "the_coven",
        "discipline": "magic",
        "cards": {
            "Mana Coffin": 1,
            "Orpheus Krustal": 1,
            "Make Metal": 2,
            "Bright Child Vamp": 2,
            "Studious Child Vamp": 2,
            "Send Minion": 2,
            "Flock of Bats": 2,
            "Enthralled Maker": 2,
            "OG Vamp": 2,
            "Solid Vamp Minion": 2,
            "Blood Boy Ogre": 2,
            "Elite Guardgoyle": 2,
            "Blood Shriek": 2,
            "Doomer": 1,
            "The Ancient": 2,
            "Ritual of the Night": 2,
            "Kill Artifact": 1
        }
    }

def default_deck_dwarf_tinkerer():
    return {
        "title": "Keeper",
        "url": "keeper",
        "discipline": "tech",
        "cards": {
            "Find Artifact": 1,
            "Wind of Mercury": 2,
            "Fidget Spinner": 2,
            "Rolling Thunder": 2,
            "Tame Shop Demon": 2,
            "Work in Progress": 2,
            "Side Project": 2,
            "Tinker": 2
        }
    }

def default_deck_dwarf_bard():
    return {
        "title": "Townies",
        "url": "townies",
        "discipline": "tech",
        "cards": {
            "Lute": 1,
            "Tech Crashhouse": 1,
            "Mayor's Brandy": 2,
            "Song of Patience": 1,
            "Study the Music": 1,
            "Town Council": 1,
            "Song of Rebirth": 1,
            "Duplication Chamber": 1,
            "Upgrade Chamber": 1,
            "Study the Masters": 1,
            "Sabotage": 1,
            "Fine War Music": 1,
            "Tech Revenge": 1,
            "Song of Fire": 1,
        }
    }
