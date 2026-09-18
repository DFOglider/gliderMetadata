import io
import re
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

def initiateVariableNERCStandardWOG1():
    file = io.FileIO(file=r".\initializationData\variable\OG1NERCVariables.csv")
    df = pd.read_csv(file)
    for row in df.itertuples():
        print(f"{getattr(row, 'variableName')}")
        # check if each variable is in the database, if not add it
        # should only need to filter on variable_nerc_variableName,
        #   there wouldn't be multiple mappings of the save variableName
        m = models.VariableNERCStandard.objects.filter(
            variable_nerc_variableName=getattr(row, 'variableName')
        )
        if m.count() == 0:
            print(f"NERC parameter {getattr(row, 'variableName')} is not in VariableNERCStandard yet. Adding it.")
            z = models.VariableNERCStandard(
                variable_nerc_variableName = getattr(row, 'variableName'),
                variable_nerc_variableLongName = getattr(row, 'variableLongName'),
                variable_nerc_variableVocabulary = getattr(row, 'variableVocab'),
                variable_nerc_unit = getattr(row, 'unit'),
                variable_nerc_unitLongName = getattr(row, 'unitLongName'),
                variable_nerc_unitVocabulary = getattr(row, 'unitVocab'))
            z.save()
        else :
            print(f"NERC parameter {getattr(row, 'variableName')} exists in VariableNERCStandard.")

initiateVariableNERCStandardWOG1()