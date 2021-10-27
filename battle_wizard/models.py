from django.conf import settings
from django.contrib import admin
from django.db import models


class CustomCard(models.Model):
	"""
		A custom card is a card designed by a user.
	"""
	author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
	date_created = models.DateTimeField()
	card_json = models.JSONField(default=dict)

class CustomCardImage(models.Model):
	"""
		An image used in a custom card, which can only be used once.
	"""
	card = models.ForeignKey(CustomCard, on_delete=models.SET_NULL, null=True)
	filename = models.TextField(null=True)

class Deck(models.Model):
	"""
		A Deck is an instance of a GlobalDeck owned by a certain user.

		Multiple players might use a deck that corresponds to a GlobalDeck.
	"""
	date_created = models.DateTimeField()
	global_deck = models.ForeignKey("GlobalDeck", on_delete=models.CASCADE)
	owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
	title = models.TextField(null=True)

class GameRecord(models.Model):
	"""
		A GameRecord is created when a game starts, and updated when it ends.
	"""
	date_finished = models.DateTimeField(null=True)
	date_started = models.DateTimeField(null=True)
	date_created = models.DateTimeField()
	game_json = models.JSONField(default=dict)
	player_one = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='player_one')
	player_two = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='player_two')
	player_one_deck = models.ForeignKey("GlobalDeck", on_delete=models.CASCADE, null=True, related_name='player_one_deck')
	player_two_deck = models.ForeignKey("GlobalDeck", on_delete=models.CASCADE, null=True, related_name='player_two_deck')
	winner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='winner')

class GlobalDeck(models.Model):
	"""
		A GlobalDeck is made the first time a certain deck is used, and linked with it's author.

		Multiple players might use a deck that corresponds to a GlobalDeck.

		Immutable except to null te author field.
	"""
	author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
	date_created = models.DateTimeField()
	cards_hash = models.TextField()
	deck_json = models.JSONField()


admin.site.register(CustomCard)
admin.site.register(CustomCardImage)
admin.site.register(Deck)
admin.site.register(GameRecord)
admin.site.register(GlobalDeck)