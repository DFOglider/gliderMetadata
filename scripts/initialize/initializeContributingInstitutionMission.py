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

# Doing the 'BBL' missions, so subset df to those missions
#df = df[df['Missiontype'] == 'BBL']

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
        # define institution and role
        # halifax line (HL) and passive acoustic monitoring in emerald basin (PAM EB)
    if getattr(row, 'Missiontype') in ['HL', 'PAM EB', 'Overnight', 'HL part']:
        cim=[['Bedford Institute of Oceanography', 'Operator'],
            ['Bedford Institute of Oceanography', 'PI']]
    # bonavista (BBL)
    elif getattr(row, 'Missiontype') in ['BBL']:
        cim = [['Bedford Institute of Oceanography', 'Operator'],
               ['Northwest Atlantic Fisheries Centre', 'Operator'],
               ['Northwest Atlantic Fisheries Centre', 'PI']]
    else:
        print(f"Not an identified missionType")
        continue
    for x in cim:
        # get pk of institute
        ins = models.Institute.objects.filter(institute_name=x[0]).first()
        # get pk of role
        r = models.Role.objects.filter(role_name=x[1]).first()
        # check if it exists yet
        cicheck = models.ContributingInstitutionMission.objects.filter(contributingInstitution_mission=models.Mission.objects.get(pk=missionQ.pk),
                                                                       contributingInstitution_missionRole=models.Role.objects.get(pk=r.pk),
                                                                       contributingInstitution_missionInstitute=models.Institute.objects.get(pk=ins.pk))
        if(cicheck.exists()):
            print(
                f"Contributor information for mission {missionQ.mission_number} and glider {missionQ.mission_platformName.platform_serial} in database")
        else:
            print(
                f"Adding information for mission {missionQ.mission_number} and glider {missionQ.mission_platformName.platform_serial} in database")
            ci = models.ContributingInstitutionMission(contributingInstitution_mission=models.Mission.objects.get(pk=missionQ.pk),
                                                       contributingInstitution_missionRole=models.Role.objects.get(pk=r.pk),
                                                       contributingInstitution_missionInstitute=models.Institute.objects.get(pk=ins.pk))
            ci.save()
