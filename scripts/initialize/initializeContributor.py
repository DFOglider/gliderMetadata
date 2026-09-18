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


def initiate_ContributorPeople():
    file = io.FileIO(file=r".\initializationData\contributor\contributorPeople.csv", mode="r")
    df = pd.read_csv(file)
    for row in df.itertuples():
        cp = models.ContributorPeople(contributor_lastName=getattr(row, "contributor_lastName"),
                                      contributor_firstName=getattr(row, "contributor_firstName"),
                                      contributor_email=getattr(row, "contributor_email"))

        cp.save()


def initiate_Role():
    file = io.FileIO(file=r".\initializationData\contributor\W08Roles.csv", mode="r")
    df = pd.read_csv(file)
    for row in df.itertuples():
        cr = models.Role(role_vocabulary = getattr(row, 'rolevocab'),
                         role_name=getattr(row, "role"))
        cr.save()



#initiate_ContributorPeople()
initiate_Role()
