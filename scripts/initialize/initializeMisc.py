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


def initiate_Institute():
    file = io.FileIO(file=r".\initializationData\misc\institute.csv", mode="r")
    df = pd.read_csv(file)
    for row in df.itertuples():
        ins = models.Institute(institute_name=getattr(row, "institute_name"),
                               institute_agency=getattr(row, "institute_agency"),
                               institute_city=getattr(row, "institute_city"),
                               institute_country=getattr(row, "institute_country"))

        ins.save()


def initiate_ArgosTag():
    file = io.FileIO(file=r".\initializationData\misc\argosTag.csv", mode="r")
    df = pd.read_csv(file)
    for row in df.itertuples():
        at = models.ArgosTag(argosTag_PTT=getattr(row, "argosTag_PTT"),
                             argosTag_serialNumber=getattr(row, "argosTag_serialNumber"))
        at.save()



def initiate_Vessel():
    file = io.FileIO(file=r".\initializationData\misc\vessel.csv", mode="r")
    df = pd.read_csv(file)
    for row in df.itertuples():
        ve = models.Vessel(vessel_name=getattr(row, "vessel_name"))
        ve.save()


#initiate_Institute()
initiate_ArgosTag()
initiate_Vessel()