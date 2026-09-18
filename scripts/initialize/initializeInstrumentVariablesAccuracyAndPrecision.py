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

# included all vars, but commented out ones that I haven't been able to find values for
# first is platformVariable
# second is accuracy
# third is precision
# fourth is resolution
# fifth is valid_min
# sixth is valid_max
m = [['GPCTD_CONDUCTIVITY', 0.0003, '', 0.00001, 0, 9],
     ['GPCTD_TEMPERATURE', 0.002, '', 0.001, -5, 42],
     ['GPCTD_PRESSURE', 0.1, '', 0.002, 0, 1000],
     # ['GPCTD_DOF', '', ''],
     #['FLBBCD_CHL_COUNT', ''],
     # ['FLBBCD_CHL_SCALED', '', ''],
     #['FLBBCD_BB_700_COUNT', ''],
     # ['FLBBCD_BB_700_SCALED', '', ''],
     #['FLBBCD_CDOM_COUNT', '', ''],
     # ['FLBBCD_CDOM_SCALED', '', ''],
     #['MFLUV1_V1_COUNT', ''],
     #['MFLUV1_V2_COUNT', ''],
     #['MFLUV1_V3_COUNT', ''],
     #['MFLUV1_V4_COUNT', ''],
     #['MFLUV1_TMP', ''],
     #['MFLUV1_TRY_SCALED', ''],
     #['MFLUV1_PHE_SCALED', ''],
     #['MFLUV1_NAPH_SCALED', ''],
     ['AROD_FT_TEMP', 0.01, '', 0.001, -3, 45],
     ['AROD_FT_DO', 2.0, '', 0.01, 0, 425],
     #['PORPOISE_STATUS', ''],
     #['PORPOISE_EVTS', ''],
     #['PORPOISE_DISK_MOUNTED', ''],
     #['PORPOISE_DISKS_USAGE', ''],
     #['PORPOISE_DISKS_FULL', ''],
     #['PORPOISE_SAMPLING_STATUS', ''],
     #['PORPOISE_ACOUSTIC_RECORDING', '', ''],
     ['LEGATO_CONDUCTIVITY', 0.0003, '', 0.00001, 0, 8.5],
     ['LEGATO_TEMPERATURE', 0.002, '', 0.00005, -5, 42],
     ['LEGATO_PRESSURE', 0.05 , '', 0.001, 0, 1000],
     # ['LEGATO_SALINITY', '', '']
     ]

for var in m:
    print(f"Getting variable {var[0]}")
    x = models.InstrumentVariable.objects.get(instrument_variableSourceName = var[0])
    if not (len(str(var[1])) == 0):
        print(f"Adding accuracy.")
        x.instrument_accuracy = var[1]
    if not (len(str(var[2])) == 0):
        print(f"Adding precision.")
        x.instrument_precision = var[2]
    if not (len(str(var[3])) == 0):
        print(f"Adding resolution.")
        x.instrument_resolution = var[3]
    if not (len(str(var[4])) == 0):
        print(f"Adding validMin.")
        x.instrument_validMin = var[4]
    if not (len(str(var[5])) == 0):
        print(f"Adding validMax.")
        x.instrument_validMax = var[5]
    x.save()