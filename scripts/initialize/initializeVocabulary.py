import io
import pandas as pd
import os
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "manage.py").exists())
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gliderMetadataDjango.settings")

import django
django.setup()

from gliderMetadataApp import models


def initiate_Vocabulary():
    file = io.FileIO(file=r".\initializationData\vocabulary\vocabulary.csv", mode="r")
    df = pd.read_csv(file)
    for row in df.itertuples():
        v = models.Vocabulary(vocabulary_name=getattr(row, "vocabulary_name"),
                                     vocabulary_note=getattr(row, "vocabulary_notes"))

        v.save()

initiate_Vocabulary()