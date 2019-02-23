import glob
import os
import shutil

from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'Cleans stupid files'

    def handle(self, *args, **kwargs):
        shutil.rmtree("__pycache__")
        for f in glob.glob("*.pyc", recursive=True):
            os.unlink(f)
