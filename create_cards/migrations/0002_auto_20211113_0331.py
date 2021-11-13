# Generated by Django 3.1.13 on 2021-11-13 03:31

from django.db import migrations
from scripts.update_svgs import resize_svg
import os
import shutil
import zipfile


def load_images_to_db(apps, schema_editor):
    CustomCardImage = apps.get_model('create_cards', 'CustomCardImage')

    dirname = os.path.dirname(__file__)
    file_to_unzip = os.path.join(dirname, "..", "game-icons.net.svg.zip")
    extract_to_dir = os.path.join(dirname, "..", "unprocessed-images")

    with zipfile.ZipFile(file_to_unzip, 'r') as zip_ref:
        zip_ref.extractall(extract_to_dir)


    dir_to_store_images = os.path.join(dirname, "..", "..", "static", "images", "card-art-custom")
    if not os.path.isdir(dir_to_store_images):
        os.mkdir(dir_to_store_images)
    for subdir, dirs, files in os.walk(extract_to_dir):
        for filename in files:
            filepath = subdir + os.sep + filename
            shutil.copy2(filepath, dir_to_store_images)

    for entry in os.scandir(dir_to_store_images):
        if entry.name.endswith('svg'):
            resize_svg(entry.path)
            if not CustomCardImage.objects.filter(filename=entry.name).first():
                cci = CustomCardImage.objects.create(filename=entry.name)
                cci.save()

    shutil.rmtree(extract_to_dir)


class Migration(migrations.Migration):
    dependencies = [
        ('create_cards', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_images_to_db),
    ]
