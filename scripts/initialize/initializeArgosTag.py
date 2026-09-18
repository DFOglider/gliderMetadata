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

from gliderMetadataApp import models   # everything Django must come after django.setup()

def initiate_ArgosTagPTT():
    file = io.FileIO(file=r".\initializationData\argosTag\argosTagPTT.csv", mode="r")
    df = pd.read_csv(file)
    for row in df.itertuples():
        cp = models.ArgosTagPTT(argosTag_PTT=getattr(row, "argosTag_PTT"))
        cp.save()


def initiate_ArgosTagSN():
    file = io.FileIO(file=r".\initializationData\argosTag\argosTagSerialNumber.csv", mode="r")
    df = pd.read_csv(file)
    for row in df.itertuples():
        cp = models.ArgosTagSerialNumber(argosTag_PTTNumber=models.ArgosTagPTT.objects.get(pk=getattr(row, "argosTagPTT_id")),
                                         argosTag_serialNumber=getattr(row, "argosTagSN"))
        cp.save()

initiate_ArgosTagPTT()
initiate_ArgosTagSN()