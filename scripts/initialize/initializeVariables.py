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

def initiate_VariableCFStandard():
    file = io.FileIO(file=r".\initializationData\variable\variables_CFStandard.csv")
    df = pd.read_csv(file)
    for row in df.itertuples():
         vcf = models.VariableCFStandard(variable_nameVocabulary = models.Vocabulary.objects.get(pk=getattr(row, 'variable_nameVocabulary')),
                                         variable_standardName = getattr(row, 'variable_standardName'))#,
                                         #variable_longName = getattr(row, 'variable_longName'),
                                         #variable_units = getattr(row, 'variable_units'))
         # on 20230908 changes the table, omitted longName and units
         vcf.save()


def initiate_InstrumentVariables():
    file = io.FileIO(file=r".\initializationData\variable\variable_instrument.csv")
    df = pd.read_csv(file)
    for row in df.itertuples():
        # get pk for instrument_variableInstrumentModel
        if pd.isna(getattr(row, 'instrument_variableInstrumentModel')):
            instrumentModelPk = None
        else:
            instrumentModelPk = models.InstrumentModel.objects.get(pk=getattr(row, 'instrument_variableInstrumentModel'))
        # get pk for instrument_variableStandardCF
        if pd.isna(getattr(row, 'instrument_variableStandardCF')):
            CFstandardPk = None
        else:
            CFstandardPk = models.VariableCFStandard.objects.get(pk=getattr(row, 'instrument_variableStandardCF'))

        iv = models.InstrumentVariable(instrument_variablePlatformCompany = models.PlatformCompany.objects.get(pk=getattr(row, 'instrument_variablePlatformCompany')),
                                       instrument_variableInstrumentModel = instrumentModelPk,
                                       instrument_variableStandardCF = CFstandardPk,
                                       instrument_variableSourceName = getattr(row, 'instrument_variableSourceName'),
                                       instrument_variableSourceUnits = getattr(row, 'instrument_variableSourceUnits'))
        iv.save()

def initiate_PlatformVariables():
    file = io.FileIO(file=r".\initializationData\variable\variable_platform.csv")
    df = pd.read_csv(file)
    for row in df.itertuples():
        # get pk for platform_variableStandardCF
        if pd.isna(getattr(row, 'platform_variableStandardCF')):
            CFstandardPk = None
        else:
            CFstandardPk = models.VariableCFStandard.objects.get(pk=getattr(row, 'platform_variableStandardCF'))
        pv = models.PlatformVariable(platform_variablePlatformCompany = models.PlatformCompany.objects.get(pk=getattr(row, 'platform_variablePlatformCompany')),
                                     platform_variableStandardCF = CFstandardPk,
                                     platform_variableSourceName = getattr(row, 'platform_variableSourceName'),
                                     platform_variableSourceUnits = getattr(row, 'platform_variableSourceUnits'))
        pv.save()

#initiate_VariableCFStandard()
#initiate_InstrumentVariables()
#initiate_PlatformVariables()