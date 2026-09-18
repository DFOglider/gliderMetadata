import io
import operator
import pandas as pd
import re
import os
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "manage.py").exists())
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gliderMetadataDjango.settings")

import django
django.setup()

from gliderMetadataApp import models
from scripts import fn_readMissionFile as rmf

def convert_date(date):
    return pd.to_datetime(date.apply(lambda d: str(d)[0:8]), errors='coerce')

df = rmf.readMissionFile()

# Right now we're just doing the 'HL' missions, so subset df to those missions
df = df[(df['Missiontype'] == 'HL') | (df['Missiontype'] == 'HL part')]

# get pk value of the platform to find mission pk
# mission_platformName
# reformat df['Glider'] to be able to match it with database
gliderSerial = [re.sub('SEA(\\d+)', '\\1', x) for x in df['Glider']]
gliderSerial = ['"' + x + '"' for x in gliderSerial]
# get pk from models.PlatformName
platformNamePk = []
for i in gliderSerial:
    platformNameQ = models.PlatformName.objects.filter(platform_serial=i).first()
    if platformNameQ is None:
        print(f"Unable to find primary key value for glider with serial number {i}")
        platformNamePk.append(None)
    else:
        platformNamePk.append(platformNameQ.pk)

# add platformNamePk to df
df['platformNamePk'] = platformNamePk

for row in df.itertuples():
    missionQ = models.Mission.objects.filter(mission_platformName=getattr(row, 'platformNamePk'),
                                             mission_number=getattr(row, 'missionNumber')).first()
    im = models.Mission.objects.get(pk=missionQ.pk) # not sure if this is redundant
    im.mission_summary = 'The Atlantic Zone Monitoring Program (AZMP) was implemented in year 1998 by ' \
                       'the four Atlantic regions of Fisheries and Oceans Canada to collect and analyze ' \
                       'the biological, chemical, and physical oceanographic field data to characterize and ' \
                       'understand the causes of oceanic variability at various time scales, provide ' \
                       'multidisciplinary datasets to establish relationships among variables, ' \
                       'and provide adequate data to support the development of ocean activities. ' \
                       'Ocean gliders were first acquired by Fisheries and Oceans Canada in year 2017 ' \
                       'and 2018 for both the West and East coasts. On the East coast, they have been used ' \
                       'to monitor hydrographic sections associated with the AZMP. Here, the AZMP Halifax line ' \
                       'is occupied from outside the mouth of Halifax harbor, Nova Scotia Canada at (44.267N, 63.317W)' \
                       ' in the off-shelf direction approximately 135 nautical miles to deep waters off the continental' \
                       ' slope at (42.475N, 61.433W).'
    im.save()

