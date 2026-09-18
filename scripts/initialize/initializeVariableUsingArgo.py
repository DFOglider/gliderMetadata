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

# 4 tables need to be initialized using ARGO parameters
# variableCFStandard (have to check what is already there) - done
# variableNERCStandard - done
# unitCFStandard - done
# unitNERCStandard - done
# then the major table, Variable, will use those 4 tables, we'll hook everything up by
# using the ARGO file

def initiate_VariableCFStandard():
    file = io.FileIO(file=r".\initializationData\variable\variable_CFStandard_ARGO.csv")
    df = pd.read_csv(file)
    for row in df.itertuples():
        # check if the standardName is already in the table if not, initialize
        check = models.VariableCFStandard.objects.filter(variable_standardName=getattr(row, 'standardName'))
        if check.count() == 0:
            print(f"Adding {getattr(row, 'standardName')} to VariableCFStandard table")
            vcf = models.VariableCFStandard(variable_nameVocabulary = models.Vocabulary.objects.get(pk=1), # CF standard name
                                            variable_standardName = getattr(row, 'standardName'))
            vcf.save()
        else:
            print(f"{getattr(row, 'standardName')} is already in VariableCFStandard table")

def initiate_VariableNERCStandard():
    file = io.FileIO(file=r".\initializationData\variable\variable_NERCStandard_ARGO.csv")
    df = pd.read_csv(file)
    for row in df.itertuples():
         vcf = models.VariableNERCStandard(variable_nameVocabulary = None, # don't need this for NERC... for now
                                           variable_standardNameUrn = getattr(row, 'standardNameUrn'),
                                           variable_standardNameUri = getattr(row, 'standardNameUri'))
         vcf.save()


def initiate_UnitCFStandard():
    file = io.FileIO(file=r".\initializationData\variable\unit_CFStandard_ARGO.csv")
    df = pd.read_csv(file)
    for row in df.itertuples():
         vcf = models.UnitCFStandard(variable_nameVocabulary = models.Vocabulary.objects.get(pk=1), # CF standard name
                                     variable_unit = getattr(row, 'units'))
         vcf.save()

def initiate_UnitNERCStandard():
    file = io.FileIO(file=r".\initializationData\variable\unit_NERCStandard_ARGO.csv")
    df = pd.read_csv(file)
    for row in df.itertuples():
         vcf = models.UnitNERCStandard(variable_nameVocabulary = None, # don't need this for NERC... for now
                                     variable_unitUri = getattr(row, 'unitUri'),
                                     variable_unitUrn = getattr(row, 'unitUrn'))
         vcf.save()

def initiate_Variable():
    file = io.FileIO(file=r".\initializationData\variable\variable_ARGO.csv")
    dfPrimary = pd.read_csv(file)
    file = io.FileIO(file=r".\initializationData\variable\variable_argoStandard.csv")
    df = pd.read_csv(file, skiprows=1)
    # clean it up
    # when I read the file on 20230823 there were a lot of empty rows
    # let's use 'parameter name'  to check which rows have mostly empty values
    # unable to check if every value in the row is empty b/c there are notes in the file
    emptyRow = df['parameter name'].isna()
    keepRow = [not x for x in emptyRow]
    df = df[keepRow]
    # remove empty columns by the column name
    # anything with 'Unnamed: ' will be removed
    emptyColumn = [bool(re.search('Unnamed: ', x)) for x in df.columns]
    keepColumn = [not x for x in emptyColumn]
    df = df.loc[:, keepColumn]
    # remove the column that has the 'Note \\d' notes
    # do this by checking the length of the column name
    longColumnName = [len(x) for x in df.columns]
    keepColumn2 = [x < 100 for x in longColumnName]
    df = df.loc[:, keepColumn2]
    # now only keep parameterNames indicated in dfPrimary
    allParameters = list(df['parameter name'])
    subParameters = list(dfPrimary['parameterName'])
    primaryMatch = [x in subParameters for x in allParameters]
    df = df.loc[primaryMatch, :]
    # remove white spaces from column names
    df.columns = df.columns.str.replace(' ', '')
    # now initialize Variable table
    for row in df.itertuples():
        # get pk for each parameter
        print(f"{getattr(row, 'parametername')}")
        #variable_cfName
        cfName = models.VariableCFStandard.objects.filter(variable_standardName=getattr(row, 'cf_standard_name'))
        if cfName.count() == 0:
            cfNamePk = None
        else:
            cfNamePk = models.VariableCFStandard.objects.get(pk=cfName.first().pk)
        print(f"{cfNamePk}")
        #variable_nercName
        nercName = models.VariableNERCStandard.objects.filter(variable_standardNameUrn=getattr(row, 'sdn_parameter_urn'),
                                                             variable_standardNameUri=getattr(row, 'sdn_parameter_uri'))
        if nercName.count() == 0:
            nercNamePk = None
        else:
            nercNamePk = models.VariableNERCStandard.objects.get(pk=nercName.first().pk)
        print(f"{nercNamePk}")
        #variable_cfUnit
        cfUnit = models.UnitCFStandard.objects.filter(variable_unit=getattr(row, 'unit'))
        if cfUnit.count() == 0:
            cfUnitPk = None
        else:
            cfUnitPk = models.UnitCFStandard.objects.get(pk=cfUnit.first().pk)
        print(f"{cfUnitPk}")
        #variable_nercUnit
        nercUnit = models.UnitNERCStandard.objects.filter(variable_unitUrn=getattr(row, 'sdn_uom_urn'),
                                                         variable_unitUri=getattr(row, 'sdn_uom_uri'))
        if nercUnit.count() == 0:
            nercUnitPk = None
        else:
            nercUnitPk = models.UnitNERCStandard.objects.get(pk=nercUnit.first().pk)
        print(f"{nercUnitPk}")
        v = models.Variable(variable_parameterName=getattr(row, 'parametername'),
                            variable_longName=getattr(row, 'long_name'),
                            variable_parameterNameComment='argo',
                            variable_cfName=cfNamePk,
                            variable_nercName=nercNamePk,
                            variable_cfUnit=cfUnitPk,
                            variable_nercUnit=nercUnitPk)
        print(f"{v}")
        v.save()



#initiate_VariableCFStandard()
#initiate_VariableNERCStandard()
#initiate_UnitCFStandard()
#initiate_UnitNERCStandard()
#initiate_Variable()