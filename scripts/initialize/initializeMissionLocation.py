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
    if getattr(row, 'Missiontype') in ['HL', 'HL part']:
        location = 'Halifax Line'
    elif getattr(row, 'Missiontype') in ['BB']:
        location = 'Bonavista Bay'
    elif getattr(row, 'Missiontype') in ['Trinity']:
        location = 'Trinity Bay'
    elif getattr(row, 'Missiontype') in ['PAM EB']:
        location = 'Emerald Basin'
    else:
        print(f"Missiontype {getattr(row, 'Missiontype')} is not in one of the options, adding blank space")
        location = ' '
    im.mission_location = location
    im.save()