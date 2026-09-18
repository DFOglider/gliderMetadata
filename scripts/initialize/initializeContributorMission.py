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

roleAbbrev = ['PI',
              'Operator']
contributorPeoplePk = []
contributorPeopleRolePk = []
contributorPeopleMissionPk = []
# ContributionMission table
for d in df.itertuples():
    print(f"{getattr(d, 'Glider')} mission {getattr(d, 'missionNumber')}")
    # get pk value from models.Mission
    missionQ = models.Mission.objects.filter(mission_platformName=getattr(d, 'platformNamePk'),
                                             mission_number=getattr(d, 'missionNumber')).first()
    for i in roleAbbrev:
        name = getattr(d, i)
        lastName = name.split(' ')[1]
        firstName = name.split(' ')[0]
        # get pk value from models.ContributorPeople
        cpQ = models.ContributorPeople.objects.filter(contributor_lastName=lastName,
                                                      contributor_firstName=firstName)
        # check to see there was a match, if there was, append pk
        if(len(cpQ) > 1):
            print(f"Found more than 1 match for {firstName} {lastName}, "
                  f"{cpQ.all().values()}")
            print(f"Using the first match")
            contributorPeoplePk.append(cpQ.first().pk)
        if(len(cpQ) == 0):
            print(f"Unable to find a match for {firstName} {lastName}, "
                  f"appending None")
            contributorPeoplePk.append(None)
        if(len(cpQ) == 1):
            contributorPeoplePk.append(cpQ.first().pk)
        # get pk from models.ContributorRole
        # as of 20230721, the NERC G04 vocabulary
        # this is a bit dirty, but I know the role names, so pull it out by that
        if(i == 'PI'):
            crQ = models.Role.objects.get(role_name='PI')
            contributorPeopleRolePk.append(crQ.pk)
        if(i == 'Operator'):
            crQ = models.Role.objects.get(role_name='Operator')
            contributorPeopleRolePk.append(crQ.pk)
        # append mission pk
        if missionQ is None:
            print(f"Unable to find primary key value for glider{getattr(d, 'Glider')} mission {getattr(d, 'missionNumber')}")
            contributorPeopleMissionPk.append(None)
        else:
            contributorPeopleMissionPk.append(missionQ.pk)


contributorDf = pd.DataFrame(list(zip(contributorPeopleMissionPk,
                                      contributorPeoplePk,
                                      contributorPeopleRolePk)),
                            columns=['contributorMissionPk',
                                     'contributorPersonPk',
                                     'contributorPersonRolePk'])

# initialize InstrumentMission
for row in contributorDf.itertuples():
    # get info for statements
    missionNumber = models.Mission.objects.get(pk=getattr(row, 'contributorMissionPk'))
    # check if information is already in database
    icmcheck = models.ContributorMission.objects.filter(contributor_mission = models.Mission.objects.get(pk=getattr(row, 'contributorMissionPk')),
                                                                contributor_missionPerson = models.ContributorPeople.objects.get(pk=getattr(row, 'contributorPersonPk')),
                                                                contributor_missionRole = models.Role.objects.get(pk=getattr(row, 'contributorPersonRolePk')))
    if(icmcheck.exists()):
        print(f"Contributor information for mission {missionNumber.mission_number} and glider {missionNumber.mission_platformName.platform_serial} in database")
    else:
        print(f"Adding contributor information for mission {missionNumber.mission_number} and glider {missionNumber.mission_platformName.platform_serial}")
        icm = models.ContributorMission(contributor_mission = models.Mission.objects.get(pk=getattr(row, 'contributorMissionPk')),
                                        contributor_missionPerson = models.ContributorPeople.objects.get(pk=getattr(row, 'contributorPersonPk')),
                                        contributor_missionRole = models.Role.objects.get(pk=getattr(row, 'contributorPersonRolePk')))
        icm.save()