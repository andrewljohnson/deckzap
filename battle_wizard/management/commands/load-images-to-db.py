from battle_wizard.models import CustomCardImage
from django.core.management.base import BaseCommand, CommandError
import os
import shutil
import zipfile

class Command(BaseCommand):
    help = 'Loads images from a zipfile from game-icons.net into the DB for use with CustomCard creation'

    def handle(self, *args, **options):
        dirname = os.path.dirname(__file__)
        file_to_unzip = os.path.join(dirname, "game-icons.net.svg.zip")
        extract_to_dir = os.path.join(dirname, "unprocessed-images")

        with zipfile.ZipFile(file_to_unzip, 'r') as zip_ref:
            zip_ref.extractall(extract_to_dir)


        dir_to_store_images = os.path.join(dirname, "../../game/cards/images")
        if not os.path.isdir(dir_to_store_images):
            os.mkdir(dir_to_store_images)
        for subdir, dirs, files in os.walk(extract_to_dir):
            for filename in files:
                filepath = subdir + os.sep + filename
                shutil.copy2(filepath, dir_to_store_images)

        for entry in os.scandir(dir_to_store_images):
            if not CustomCardImage.objects.filter(filename=entry.name).first():
                cci = CustomCardImage.objects.create(filename=entry.name)
                cci.save()

        shutil.rmtree(extract_to_dir)
