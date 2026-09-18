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


def readArgosVariables():
    file = io.FileIO(file=r".\initializationData\variable\variable_argoStandard.csv", mode="r")
    dataframe = pd.read_csv(file, skiprows=1)
    # clean it up
    # when I read the file on 20230823 there were a lot of empty rows
    # let's use 'parameter name'  to check which rows have mostly empty values
    # unable to check if every value in the row is empty b/c there are notes in the file
    emptyRow = dataframe['parameter name'].isna()
    keepRow = [not x for x in emptyRow]
    dataframe = dataframe[keepRow]
    # remove empty columns by the column name
    # anything with 'Unnamed: ' will be removed
    emptyColumn = [bool(re.search('Unnamed: ', x)) for x in dataframe.columns]
    keepColumn = [not x for x in emptyColumn]
    dataframe = dataframe.loc[:, keepColumn]
    # remove the column that has the 'Note \\d' notes
    # do this by checking the length of the column name
    longColumnName = [len(x) for x in dataframe.columns]
    keepColumn2 = [x < 100 for x in longColumnName]
    dataframe = dataframe.loc[:, keepColumn2]


