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

admin.site.register(CustomCard)
admin.site.register(CustomCardImage)
