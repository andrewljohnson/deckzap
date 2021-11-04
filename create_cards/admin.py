from django.contrib import admin
from django.db import models
from create_cards.models import CustomCard
from create_cards.models import CustomCardImage

class CustomCardImageAdmin(admin.ModelAdmin):
    model = CustomCardImage
    list_display = ('filename', 'card_name')


admin.site.register(CustomCard)
admin.site.register(CustomCardImage, CustomCardImageAdmin)

