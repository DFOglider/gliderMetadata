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

# Doing the Bonavista Bay, 'BB' missions, so subset df to those missions
df = df[df['Missiontype'] == 'BB']

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
                         'to monitor hydrographic sections associated with the AZMP. Here, the AZMP Bonavista Bay ' \
                         'transect is occupied from outside the mouth of Bonavista Bay, Newfoundland Canada at ' \
                         '(48.733N, 52.967W) in the off-shelf direction approximately 150 nautical miles to the ' \
                         'continental slope at (49.85N, 49.5W).'
    im.save()

