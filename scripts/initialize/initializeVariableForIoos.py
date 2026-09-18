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

def initiateVariableWithIOOS():
    file = io.FileIO(file=r".\initializationData\variable\variable_ioosStandard.csv")
    df = pd.read_csv(file)
    for row in df.itertuples():
        print(f"{getattr(row, 'parameterName')}")
        # get pk for each parameter
        # check if each parameter is in the database, if not add it
        # variable_cfName
        if pd.isnull(getattr(row, 'cfStandardName')):
            print(f"cfStandardName is null")
            cfNamePk = None
        else:
            cfName = models.VariableCFStandard.objects.filter(variable_standardName=getattr(row, 'cfStandardName'))
            if cfName.count() == 0:
                print(f"cf standard name : {getattr(row, 'cfStandardName')} is not in VariableCFStandard yet. Adding it.")
                vcf = models.VariableCFStandard(variable_nameVocabulary=models.Vocabulary.objects.get(pk=1),
                                                variable_standardName=getattr(row, 'cfStandardName'))
                vcf.save()
                cfName2 = models.VariableCFStandard.objects.filter(variable_standardName=getattr(row, 'cfStandardName'))
                cfNamePk = models.VariableCFStandard.objects.get(pk=cfName2.first().pk)
            else:
                cfNamePk = models.VariableCFStandard.objects.get(pk=cfName.first().pk)
            print(f"{cfNamePk}")
        # variable_nercName
        if pd.isnull(getattr(row, 'nercParameterUrn')): # only check one, if one is null, the other is
            print(f"nercParameter values are null")
            nercNamePk = None
        else:
            nercName = models.VariableNERCStandard.objects.filter(
                variable_standardNameUrn=getattr(row, 'nercParameterUrn'),
                variable_standardNameUri=getattr(row, 'nercParameterUri'))
            if nercName.count() == 0:
                # shouldn't have to add anything for nerc, should all be there
                print(f"nerc urn: {getattr(row, 'nercParameterUrn')} is not in VariableNERCStandard yet. Adding it.")
                vcf = models.VariableNERCStandard(variable_nameVocabulary=None,  # don't need this for NERC... for now
                                                  variable_standardNameUrn=getattr(row, 'nercParameterUrn'),
                                                  variable_standardNameUri=getattr(row, 'nercParameterUri'))
                vcf.save()
                nercName2 = models.VariableNERCStandard.objects.filter(
                variable_standardNameUrn=getattr(row, 'nercParameterUrn'),
                variable_standardNameUri=getattr(row, 'nercParameterUri'))
                nercNamePk = models.VariableNERCStandard.objects.get(pk=nercName2.first().pk)
            else:
                nercNamePk = models.VariableNERCStandard.objects.get(pk=nercName.first().pk)
            print(f"{nercNamePk}")
        # variable_cfUnit
        if pd.isnull(getattr(row, 'cfUnit')):
            print(f"cfUnit is null")
            cfUnitPk = None
        else:
            cfUnit = models.UnitCFStandard.objects.filter(variable_unit=getattr(row, 'cfUnit'))
            if cfUnit.count() == 0:
                print(f"cf unit: {getattr(row, 'cfUnit')} is not in UnitCFStandard yet. Adding it.")
                vcf = models.UnitCFStandard(variable_nameVocabulary=models.Vocabulary.objects.get(pk=1),
                                            variable_unit=getattr(row, 'cfUnit'))
                vcf.save()
                cfUnit2 = models.UnitCFStandard.objects.filter(variable_unit=getattr(row, 'cfUnit'))
                cfUnitPk = models.UnitCFStandard.objects.get(pk=cfUnit2.first().pk)
            else:
                cfUnitPk = models.UnitCFStandard.objects.get(pk=cfUnit.first().pk)
        # variable_nercUnit
        if pd.isnull(getattr(row, 'nercUnitUrn')): # only need to check one
            print(f"nercUnit parameters are null")
            nercUnitPk = None
        else:
            nercUnit = models.UnitNERCStandard.objects.filter(variable_unitUrn=getattr(row, 'nercUnitUrn'),
                                                              variable_unitUri=getattr(row, 'nercUnitUri'))
            if nercUnit.count() == 0:
                print(f"nerc unit urn: {getattr(row, 'nercUnitUrn')} is not in UnitNERCStandard yet. Adding it")
                vcf = models.UnitNERCStandard(variable_nameVocabulary=None,  # don't need this for NERC... for now
                                              variable_unitUri=getattr(row, 'nercUnitUri'),
                                              variable_unitUrn=getattr(row, 'nercUnitUrn'))
                vcf.save()
                nercUnit2 = models.UnitNERCStandard.objects.filter(variable_unitUrn=getattr(row, 'nercUnitUrn'),
                                                                  variable_unitUri=getattr(row, 'nercUnitUri'))
                nercUnitPk = models.UnitNERCStandard.objects.get(pk=nercUnit2.first().pk)
            else:
                nercUnitPk = models.UnitNERCStandard.objects.get(pk=nercUnit.first().pk)
        v = models.Variable(variable_parameterName=getattr(row, 'parameterName'),
                            variable_longName=getattr(row, 'longName'),
                            variable_parameterNameComment=getattr(row, 'nameComment'),
                            variable_cfName=cfNamePk,
                            variable_nercName=nercNamePk,
                            variable_cfUnit=cfUnitPk,
                            variable_nercUnit=nercUnitPk)
        print(f"{v}")
        v.save()

initiateVariableWithIOOS()