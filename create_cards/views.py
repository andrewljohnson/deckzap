import datetime
import json

from battle_wizard.analytics import Analytics
from battle_wizard.game.card import all_cards
from battle_wizard.game.card import Card
from battle_wizard.game.data import Constants
from battle_wizard.models import GlobalDeck
from create_cards.cards_and_effects import Effects
from create_cards.cards_and_effects import effect_types
from create_cards.cards_and_effects import target_types
from create_cards.models import CustomCard
from create_cards.models import CustomCardImage
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.http import require_POST
from inspect import signature
from operator import attrgetter
from operator import itemgetter

def create_card(request):
    """
        A view to create a new card.
    """
    if not request.user.is_authenticated:
        return redirect('/signup?next=create_card')
    Analytics.log_amplitude(
        request,
        "Page View - Create Card",
        {"path":"/create_card", "page":"create card"}
    )
    return render(request, "create_card.html", {})

def mob(request, card_id):
    """
        A view to create the effects for a new mob card.
    """
    return effect_page(request, "Page View - Create Card Mob", "create card mob", card_id, 0)

def spell(request, card_id):
    """
        A view to create the effects for a new spell card.
    """
    return effect_page(request, "Page View - Create Card Spell", "create card spell", card_id, 0)

def effects(request, card_id, effect_index):
    """
        A view to create the effects for a new card.
    """
    return effect_page(request, "Page View - Create Card Effects", "create card effects", card_id, effect_index)

def effect_page(request, analytics_title, analytics_page, card_id, effect_index):
    if not request.user.is_authenticated:
        return redirect(f"/signup?next={request.path}")
    Analytics.log_amplitude(
        request, 
        analytics_title, 
        {"page":analytics_page}
    )
    json_data = json.load(open('create_cards/cards_and_effects.json'))
    del json_data["cards"]
    return render(request, "create_card_effects.html", 
        {
            "card_id":card_id, 
            "effect_index":effect_index, 
            "card_info": json.dumps(CustomCard.objects.get(id=card_id).card_json), 
            "effects_and_types": json.dumps(json_data)
        }
    )

def name_and_image(request, card_id):
    """
        A view to set the name and image for a new card.
    """
    if not request.user.is_authenticated:
        return redirect(f"/signup?next={request.path}")
    Analytics.log_amplitude(
        request, 
        "Page View - Create Card Name and Image", 
        {"page":"create card name and image"}
    )

    images = CustomCardImage.objects.filter(card=None)
    image_paths = sorted([{"path": f"/static/card-art-custom/{image.filename}", "name":image.filename.removesuffix(".svg"), "filename":image.filename} for image in images], key=itemgetter('name'))

    return render(
        request, 
        "create_card_name_and_image.html", 
        {
            "card_id":card_id, 
            "card_info": json.dumps(CustomCard.objects.get(id=card_id).card_json),
            "image_paths": json.dumps(image_paths)
        }
    )

@require_POST
def get_effect_for_info(request):
    """
        A view to get a calculated card for some info set by a form in the UX.
    """
    info = json.load(request)
    card_info = info["card_info"]
    if not len(card_info["effects"]):
        error_message = "effect required to get a modified effect"
        print(error_message)
        return JsonResponse({"error": error_message})
    else: 
        Analytics.log_amplitude(request, "Create Card Get Card Info", {})
        effect = card_info["effects"][-1]
        effect_def = None
        if effect["id"] == "ambush":
            effect_def = Effects.ambush
        elif effect["id"] == "damage":
            effect_def = Effects.damage
        elif effect["id"] == "discard_random":
            effect_def = Effects.discard_random
        elif effect["id"] == "drain":
            effect_def = Effects.drain
        elif effect["id"] == "draw":
            effect_def = Effects.draw
        elif effect["id"] == "guard":
            effect_def = Effects.guard
        elif effect["id"] == "heal":
            effect_def = Effects.heal
        elif effect["id"] == "kill":
            effect_def = Effects.kill
        elif effect["id"] == "make_from_deck":
            effect_def = Effects.make_from_deck
        elif effect["id"] == "mana_increase_max":
            effect_def = Effects.mana_increase_max
        elif effect["id"] == "shield":
            effect_def = Effects.shield
        elif effect["id"] == "take_extra_turn":
            effect_def = Effects.take_extra_turn
        elif effect["id"] == "unwind":
            effect_def = Effects.unwind
        else:
            return JsonResponse({"error": f"Unsupported effect id {effect['id']}"})
        if len(signature(effect_def).parameters) == 0:
            # for mob abilities like Ambush, Drain, Guard, and Shield
            server_effect = effect_def()
        else:
            # all non-ability-effects take 5 parameters
            amount = None
            if "amount" in effect:
                amount = effect["amount"]
            effect_type = effect_types()[effect["effect_type"]]
            server_effect = effect_def(
                card_info["card_type"], 
                amount, 
                effect_type, 
                target_types()[effect["target_type"]], 
                effect["ai_target_types"]
            )
            is_legal_type = False
            for legal_type in server_effect["legal_effect_types"]:
                if effect_type.id == legal_type["id"]:
                    is_legal_type = True
            if not is_legal_type:
                server_effect = effect_def(
                    card_info["card_type"], 
                    amount, 
                    effect_types()[server_effect["legal_effect_types"][0]["id"]], 
                    target_types()[effect["target_type"]], 
                    effect["ai_target_types"]
                )
        card_info["effects"][-1] = server_effect
        power_points = Card(card_info).power_points_value()
        card_info["power_points"] = power_points
        card_is_duplicate(card_info)
        return JsonResponse({"server_effect": server_effect, "power_points": power_points})

@require_POST
def get_power_points(request):
    """
        A view to get a calculated power_points for some info set by a form in the UX.
    """
    info = json.load(request)
    card_info = info["card_info"]
    if card_info.get("cost") is not None:
        card_info["cost"] = card_info["cost"]
    if card_info.get("strength") is not None:
        card_info["strength"] = card_info["strength"]
    if card_info.get("hit_points") is not None:
        card_info["hit_points"] = card_info["hit_points"]
    Analytics.log_amplitude(request, "Create Card Get Power Points", {})
    power_points = Card(card_info).power_points_value()
    card_info["power_points"] = power_points
    dupe_card = card_is_duplicate(card_info)
    return JsonResponse({"power_points": power_points})

@require_POST
def save_new_card(request):
    """
        A view to save a new card after the user selects the card type.
    """
    info = json.load(request)
    card_info = info["card_info"]
    if "card_type" not in card_info:
        error_message = "card_type required to save a new card"
        print(error_message)
        return JsonResponse({"error": error_message})
    else: 
        custom_card = CustomCard.objects.create(
            card_json={"card_type": card_info["card_type"], "author_username": request.user.username, "is_custom": True}, 
            author=request.user, 
            date_created=datetime.datetime.now()
        )
        custom_card.save()
        Analytics.log_amplitude(request, "Save New Card", {})
        return JsonResponse({"card_id": custom_card.id})

def save_effects(request):
    """
        A POST view to save the additional effects for a new card.
    """
    return create_card_save(request, "card_id", "Save Card Effects")

def save_mob(request):
    """
        A POST view to save the cost, strength, hit points, and effects for a new mob.
    """
    return create_card_save(request, "card_id", "Save Mob")

def save_spell(request):
    """
        A POST view to save the cost and effects for a new spell.
    """
    return create_card_save(request, "card_id", "Save Spell")

@require_POST
def create_card_save(request, required_key, event_name):
    info = json.load(request)
    card_info = info["card_info"]
    if required_key not in info:
        error_message = f"{required_key} required to save cost for a card"
        print(error_message)
        return JsonResponse({"error": error_message})
    else: 
        custom_card = CustomCard.objects.get(id=info["card_id"])
        if custom_card.author != request.user:
            error_message = "only the card's author can edit a CustomCard"
            print(error_message)
            return JsonResponse({"error": error_message})
        card_info = Card(card_info).as_dict(for_card_builder=True)
        custom_card.card_json = card_info
        custom_card.save()
        Analytics.log_amplitude(request, event_name, {})
        return JsonResponse({})

@require_POST
def save_name_and_image(request):
    """
        A view to save the name and image for a new card.
    """
    info = json.load(request)
    card_info = info["card_info"]
    if "card_id" not in info:
        error_message = "card_id required to save name and image for a card"
        print(error_message)
        return JsonResponse({"error": error_message})
    else: 
        same_name = False
        for card in all_cards():
            if card["name"] == card_info["name"]:
                error_message = f"Please choose a different name, {card_info['name']} is used by a different card."
                print(error_message)
                return JsonResponse({"error": error_message})                    
        custom_card = CustomCard.objects.get(id=info["card_id"])
        if custom_card.author != request.user:
            error_message = "only the card's author can edit a CustomCard"
            print(error_message)
            return JsonResponse({"error": error_message})
        image = CustomCardImage.objects.filter(card=None, filename=card_info["image"]).first()
        if image:
            image.card = custom_card
            image.save()
        else:
            error_message = f"CustomCardImage for file {card_info['image']} is not available"
            print(error_message)
            return JsonResponse({"error": error_message})

        new_info = custom_card.card_json
        new_info["name"] = card_info["name"]
        new_info["image"] = card_info["image"]
        custom_card.card_json = Card(new_info).as_dict(for_card_builder=True)
        custom_card.save()
        Analytics.log_amplitude(request, "Save Card Name and Image", {})
        return JsonResponse({})

@require_POST
def get_card_info(request):
    """
        A view to return card json for a card ID.
    """
    info = json.load(request)
    card_id = info["card_id"]
    card_info = CustomCard.objects.get(id=card_id).card_json
    if "effects" in card_info:
        all_effects = json.load(open('create_cards/cards_and_effects.json'))["effects"]
        for effect in card_info["effects"]:
            for ae in all_effects:
                if "legal_target_types" in ae:
                    if ae["id"]== effect["id"]:
                        effect["legal_target_types"] = ae["legal_target_types"]
                if "legal_effect_types" in ae:
                    if ae["id"]== effect["id"]:
                        effect["legal_effect_types"] = ae["legal_effect_types"]
    return JsonResponse({"card_info": json.dumps(card_info)})

@require_POST
def delete(request):
    info = json.load(request)
    card_id = info["card_id"]
    custom_card = CustomCard.objects.get(id=card_id)
    if custom_card.author != request.user:
        error_message = "only the card's author can delete a CustomCard"
        print(error_message)
        return JsonResponse({"error": error_message})
    card_is_used = False
    for gd in GlobalDeck.objects.all():
        for name, _ in gd.deck_json.items():
            for card_name, _ in gd.deck_json["cards"].items():
                if card_name == custom_card.card_json["name"]:
                    card_is_used = True
    if card_is_used:
        error_message = "can't delete custom cards used in a Deck"
        print(error_message)
        return JsonResponse({"error": error_message})
    custom_card.delete()
    Analytics.log_amplitude(request, "Delete Card", {})
    return JsonResponse({})

def card_is_duplicate(card_info):
    new_card = Card(card_info)
    possible_dupes = []
    for ac_info in all_cards(include_old_cards=False):
        card = Card(ac_info)
        if card.cost != new_card.cost:
            continue
        if card.power_points != new_card.power_points:
            continue
        if card.card_type != new_card.card_type:
            continue
        if len(card.effects) != len(new_card.effects):
            continue
        if card.card_type == Constants.mobCardType:
            if card.strength != new_card.strength:
                continue
            if card.hit_points != new_card.hit_points:
                continue
        possible_dupes.append(card)

    if len(possible_dupes) == 1 and len(new_card.effects) == 0:
        print("this is a dupe of " + possible_dupes[0].name)
        print(possible_dupes[0].as_dict(for_card_builder=True))
        return possible_dupes[0]

    if len(possible_dupes) == 0:
        print("no dupes")
        print(new_card.as_dict(for_card_builder=True))
        return None

    new_card_effects = new_card.effects
    new_card_effects.sort(key=attrgetter('target_type'))
    new_card_effects.sort(key=attrgetter('effect_type'))
    new_card_effects.sort(key=attrgetter('amount'))
    new_card_effects.sort(key=attrgetter('id'))
    dupe_card = None
    for card in possible_dupes:
        card_effects = card.effects
        card_effects.sort(key=attrgetter('target_type'))
        card_effects.sort(key=attrgetter('effect_type'))
        card_effects.sort(key=attrgetter('amount'))
        card_effects.sort(key=attrgetter('id'))
        i = -1
        for effect in card_effects:
            i += 1
            if effect.id != new_card_effects[i].id:
                continue
            if effect.amount != new_card_effects[i].amount:
                continue
            if effect.effect_type != new_card_effects[i].effect_type:
                continue
            if effect.target_type != new_card_effects[i].target_type:
                continue
            dupe_card = card
            break
        if dupe_card:
            break
    if dupe_card:
        print("this is a dupe of " + dupe_card.name)
    return dupe_card








