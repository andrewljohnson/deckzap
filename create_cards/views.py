import datetime
import json

from battle_wizard.analytics import Analytics
from create_cards.cards_and_effects import Effects
from create_cards.cards_and_effects import effect_types
from create_cards.cards_and_effects import target_types
from create_cards.models import CustomCard
from create_cards.models import CustomCardImage
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render
from inspect import signature
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

def effects(request, card_id, effect_index=0):
    """
        A view to create the effects for a new card.
    """
    if not request.user.is_authenticated:
        return redirect(f"/signup?next={request.path}")
    Analytics.log_amplitude(
        request, 
        "Page View - Create Card Effects", 
        {"page":"create card effects"}
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

def cost(request, card_id):
    """
        A view to set the mana cost for a new card.
    """
    if not request.user.is_authenticated:
        return redirect(f"/signup?next={request.path}")
    Analytics.log_amplitude(
        request, 
        "Page View - Create Card Cost", 
        {"page":"create card cost"}
    )
    return render(
        request, 
        "create_card_cost.html", 
        {"card_id":card_id, "card_info": json.dumps(CustomCard.objects.get(id=card_id).card_json)}
    )

def mob_stats(request, card_id):
    """
        A view to create the effects for a new card.
    """
    if not request.user.is_authenticated:
        return redirect(f"/signup?next={request.path}")
    Analytics.log_amplitude(
        request, 
        "Page View - Create Card Mob Stats", 
        {"page":"create card mob stats"}
    )
    return render(
        request, 
        "create_card_mob_stats.html", 
        {"card_id":card_id, "card_info": json.dumps(CustomCard.objects.get(id=card_id).card_json)}
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

def get_effect_for_info(request):
    """
        A POST view to get a calculated card for some info set by a form in the UX.
    """
    if request.method == "POST":
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
            if effect["name"] == "damage":
                effect_def = Effects.damage
            elif effect["name"] == "discard_random":
                effect_def = Effects.discard_random
            elif effect["name"] == "draw":
                effect_def = Effects.draw
            elif effect["name"] == "add_ambush":
                effect_def = Effects.add_ambush
            elif effect["name"] == "drain_hp":
                effect_def = Effects.drain_hp
            elif effect["name"] == "force_attack_guard_first":
                effect_def = Effects.force_attack_guard_first
            elif effect["name"] == "protect_with_shield":
                effect_def = Effects.protect_with_shield
            else:
                return JsonResponse({"error": f"Unsupported effect name {effect['name']}"})
            if len(signature(effect_def).parameters) == 0:
                # for mob abilities like Ambush, Drain, Guard, and Shield
                server_effect = effect_def()
            else:
                # all non-ability-effects take 5 parameters
                server_effect = effect_def(
                    card_info["card_type"], 
                    int(effect["amount"]), 
                    effect_types()[effect["effect_type"]], 
                    target_types()[effect["target_type"]], 
                    effect["ai_target_types"]
                )
            return JsonResponse({"server_effect": server_effect})
    else:
        return JsonResponse({"error": "Unsupported request type"})

def save_new_card(request):
    """
        A POST view to save a new card after the user selects the card type.
    """
    if request.method == "POST":
        info = json.load(request)
        card_info = info["card_info"]
        if "card_type" not in card_info:
            error_message = "card_type required to save a new card"
            print(error_message)
            return JsonResponse({"error": error_message})
        else: 
            custom_card = CustomCard.objects.create(
                card_json={"card_type": card_info["card_type"]}, 
                author=request.user, 
                date_created=datetime.datetime.now()
            )
            custom_card.save()
            Analytics.log_amplitude(request, "Save New Card", {})
            return JsonResponse({"card_id": custom_card.id})
    else:
        return JsonResponse({"error": "Unsupported request type"})

def save_cost(request):
    """
        A POST view to save the mana cost for a new card.
    """
    return create_card_save(request, "card_id", "Save Card Cost")

def save_mob_stats(request):
    """
        A POST view to save the mana cost for a new card.
    """
    return create_card_save(request, "card_id", "Save Mob Stats")

def save_effects(request):
    """
        A POST view to save the effects for a new card.
    """
    return create_card_save(request, "card_id", "Save Card Effects")

def create_card_save(request, required_key, event_name):
    if request.method == "POST":
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
            if "strength" in card_info:
                card_info["strength"] = int(card_info["strength"])    
            if "hit_points" in card_info:
                card_info["hit_points"] = int(card_info["hit_points"])    
            if "cost" in card_info:
                card_info["cost"] = int(card_info["cost"])    
            if "effects" in card_info:
                for e in card_info["effects"]:
                    if "amount" in e:
                        e["amount"] = int(e["amount"])    
            custom_card.card_json = card_info
            custom_card.save()
            Analytics.log_amplitude(request, event_name, {})
            return JsonResponse({})
    else:
        return JsonResponse({"error": "Unsupported request type"})

def save_name_and_image(request):
    """
        A POST view to save the name and image for a new card.
    """

    if request.method == "POST":
        info = json.load(request)
        card_info = info["card_info"]
        if "card_id" not in info:
            error_message = "card_id required to save name and image for a card"
            print(error_message)
            return JsonResponse({"error": error_message})
        else: 
            custom_card = CustomCard.objects.get(id=info["card_id"])
            if custom_card.author != request.user:
                error_message = "only the card's author can edit a CustomCard"
                print(error_message)
                return JsonResponse({"error": error_message})
            print(card_info["image"])
            image = CustomCardImage.objects.filter(card=None, filename=card_info["image"]).first()
            print(image)
            if image:
                image.card = custom_card
                image.save()
            else:
                error_message = f"CustomCardImage for file {card_info['image']} is not available"
                print(error_message)
                return JsonResponse({"error": error_message})

            custom_card.card_json = card_info
            custom_card.save()
            Analytics.log_amplitude(request, "Save Card Name and Image", {})
            return JsonResponse({})
    else:
        return JsonResponse({"error": "Unsupported request type"})

