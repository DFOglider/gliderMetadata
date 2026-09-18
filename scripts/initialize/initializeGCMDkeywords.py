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

# included all vars, but commented out ones that don't have a match
# first is platformVariable
# second is the GMCD key word 'Category > Topic > Term > Variable_Level_1
m = [['GPCTD_CONDUCTIVITY', 'Earth Science > Oceans > Salinity/Density > Conductivity'],
     ['GPCTD_TEMPERATURE', 'Earth Science > Oceans > Ocean Temperature > Water Temperature'],
     ['GPCTD_PRESSURE', 'Earth Science > Oceans > Ocean Pressure > Water Pressure'],
     #['GPCTD_DOF', ''],
     #['FLBBCD_CHL_COUNT', ''],
     ['FLBBCD_CHL_SCALED', 'Earth Science > Oceans > Ocean Chemistry > Chlorophyll'],
     #['FLBBCD_BB_700_COUNT', ''],
     #['FLBBCD_BB_700_SCALED', ''],
     #['FLBBCD_CDOM_COUNT', '', ''],
     #['FLBBCD_CDOM_SCALED', ''],
     #['MFLUV1_V1_COUNT', ''],
     #['MFLUV1_V2_COUNT', ''],
     #['MFLUV1_V3_COUNT', ''],
     #['MFLUV1_V4_COUNT', ''],
     #['MFLUV1_TMP', ''],
     #['MFLUV1_TRY_SCALED', ''],
     #['MFLUV1_PHE_SCALED', ''],
     #['MFLUV1_NAPH_SCALED', ''],
     #['AROD_FT_TEMP', ''],
     ['AROD_FT_DO', 'Earth Science > Oceans > Ocean Chemistry > Dissolved Gases'],
     #['PORPOISE_STATUS', ''],
     #['PORPOISE_EVTS', ''],
     #['PORPOISE_DISK_MOUNTED', ''],
     #['PORPOISE_DISKS_USAGE', ''],
     #['PORPOISE_DISKS_FULL', ''],
     #['PORPOISE_SAMPLING_STATUS', ''],
     #['PORPOISE_ACOUSTIC_RECORDING', '', ''],
     ['LEGATO_CONDUCTIVITY', 'Earth Science > Oceans > Salinity/Density > Conductivity'],
     ['LEGATO_TEMPERATURE', 'Earth Science > Oceans > Ocean Temperature > Water Temperature'],
     ['LEGATO_PRESSURE', 'Earth Science > Oceans > Ocean Pressure > Water Pressure'],
     ['LEGATO_SALINITY', 'Earth Science > Oceans > Salinity/Density > Salinity']
     ]

for var in m:
    x = models.InstrumentVariable.objects.get(instrument_variableSourceName = var[0])
    if not (len(var[1]) == 0):
        x.instrument_gcmdKeyword = var[1]
        x.save()