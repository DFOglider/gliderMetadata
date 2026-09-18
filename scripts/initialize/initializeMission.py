import io
import operator
import numpy as np
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
# Pull out information from sheet to match with database
# refer to 'relationDiagram.png' going to follow the order in the 'Mission' table

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
        platformNamePk.append(np.nan)
    else:
        platformNamePk.append(platformNameQ.pk)

# add platformNamePk to df
df['platformNamePk'] = platformNamePk

# mission_platformNavFirmware
# remove leading spaces
gliderNavFirm = [x.lstrip() for x in df['Navfirmware']]
# get only the version (sometimes there's comments separated by a space)
gliderNavFirm = [x.split(' ')[0] for x in gliderNavFirm]
# some indicies do not have a 'v' in the front, add it to ones that are missing
gliderNavFirm = ['v' + x if operator.not_(bool(re.search('v', x))) else x for x in gliderNavFirm]
# add '-r' to ones that are missing it
gliderNavFirm = [x + '-r' if operator.not_(bool(re.search('-r|-cr', x))) else x for x in gliderNavFirm]
# get pk from models.PlatformNavigationFirmware
platformNavFirmPk = []
for i in gliderNavFirm:
    platformNavFirmQ = models.PlatformNavigationFirmware.objects.filter(platform_navFirmwareVersion=i).first()
    if platformNavFirmQ is None:
        print(f"Unable to find primary key value for navigation firmware for version {i}")
        platformNavFirmPk.append(np.nan)
    else:
        platformNavFirmPk.append(platformNavFirmQ.pk)

# add platformNavFirmPk to df
df['platformNavigationFirmwarePk'] = platformNavFirmPk

# mission_platformBattery
gliderBattery = df['Battery']
gliderBattery = [re.sub('(\\d+)\\w+ gen', '\\1', x) for x in gliderBattery]
# get pk from models.PlatformBattery
platformBatteryPk = []
for i in gliderBattery:
    platformBatteryQ = models.PlatformBattery.objects.filter(platform_batteryGeneration=i).first()
    if platformBatteryQ is None:
        print(f"Unable to find primary key value for battery with generation {i}")
        platformBatteryPk.append(np.nan)
    else:
        platformBatteryPk.append(platformBatteryQ.pk)

# add plotformBatteryPk to df
df['platformBatteryPk'] = platformBatteryPk

# mission_platformRelease
gliderRelease = df['Release']
gliderRelease = gliderRelease.tolist()
gliderRelease = [x.replace('-', ', ') for x in gliderRelease]
gliderRelease = [x.split(', ') for x in gliderRelease]
# need both the release type and attach method for database
gliderReleaseType = [x[0] for x in gliderRelease]
gliderReleaseType = [x.replace('Mag', 'Magnetic') for x in gliderReleaseType]
gliderReleaseType = [x.replace('wire', 'Wire') for x in gliderReleaseType]
gliderReleaseAttach = [x[1] if x.__len__() > 1 else 'NULL' for x in
                       gliderRelease]  # might have to replace 'NULL' with None
# capitalize releaseAttach
gliderReleaseAttach = [x.capitalize() for x in gliderReleaseAttach]
# replace 'Null' with 'nan'
gliderReleaseAttach = [x.replace('Null', 'nan') for x in gliderReleaseAttach]
# get pk from models.PlatformBattery
gliderReleaseList = list(zip(gliderReleaseType, gliderReleaseAttach))
gliderReleaseDf = pd.DataFrame(gliderReleaseList, columns=['Type', 'Attach'])
platformReleasePk = []
for i in gliderReleaseDf.itertuples():
    platformReleaseQ = models.PlatformRelease.objects.filter(platform_releaseType=getattr(i, 'Type'),
                                                             platform_releaseAttachMethod=getattr(i, 'Attach')).first()
    if platformReleaseQ is None:
        print(f"Unable to find primary key value for release system type {getattr(i, 'Type')}"
              f"with attach method {getattr(i, 'Attach')}")
        platformReleasePk.append(None)
    else:
        platformReleasePk.append(platformReleaseQ.pk)

# add platformReleasePk to df
df['platformReleasePk'] = platformReleasePk

# mission_platformPayload
# useful : np.array(df.columns)
gliderPldSN = df['PLDSN']
# convert to string for matching up with platform
gliderPldSN = [str(int(x)) for x in gliderPldSN]
# get pk from models.PlatformPayload
platformPayloadPk = []
for i in gliderPldSN:
    platformPayloadQ = models.PlatformPayload.objects.filter(platform_payloadSerialNumber=i).first()
    if platformPayloadQ is None:
        print(f"Unable to find primary key value for payload with serial number {i}")
        platformPayloadPk.append(None)
    else:
        platformPayloadPk.append(platformPayloadQ.pk)

# add platformPayloadPk to df
df['platformPayloadPk'] = platformPayloadPk

# mission_platformPayloadFirmware
gliderPldFirm = df['pldfirmware']
# remove notes
gliderPldFirm = [x.split(' ')[0] for x in gliderPldFirm]
# get pk from models.PlatformPayloadFirmware
platformPayloadFirmPk = []
for i in gliderPldFirm:
    platformPayloadFirmQ = models.PlatformPayloadFirmware.objects.filter(platform_payloadFirmwareVersion=i).first()
    if platformPayloadFirmQ is None:
        print(f"Unable to find primary key value for payload firmware with version {i}")
        platformPayloadFirmPk.append(None)
    else:
        platformPayloadFirmPk.append(platformPayloadFirmQ.pk)

# add platformPayloadFirmPk to df
df['platformPayloadFirmwarePk'] = platformPayloadFirmPk

# vessel for recovery and deployment
vessel = df['boatdeprec']
# meaning of vessel objects : deployment/recovery
# mission_deploymentVessel
deploymentVessel = [x.split('/')[0] for x in vessel]
# remove '-'
deploymentVessel = [re.sub('-', ' ', x) for x in deploymentVessel]
# mission_recoveryVessel
recoveryVessel = [x.split('/')[1] for x in vessel]
# remove '-'
recoveryVessel = [re.sub('-', ' ', x) for x in recoveryVessel]
# get pk from models.Vessels
# go through deployment and recovery separately
# note that we'll have to match them based on partial knowledge on the vessel name provided in excel file
modelsVessels = models.Vessel.objects.values_list('vessel_name', flat=True).distinct()
depVesselPk = []
for i in deploymentVessel:
    if i == "Eastcom":
        print(f"Renaming {i} as EastCom")
        i = "EastCom"
    # find which one it best matches with
    ok = [bool(re.search(i, x)) for x in modelsVessels]  # True, False
    ok = [i for i, x in enumerate(ok) if x]  # index
    # get the first index so it's easier to use
    if len(ok) == 0:
        print(f"Unable to find a match for deployment vessel {i}")
        depVesselPk.append(np.nan)
    else:
        if len(ok) > 1:
            print(
                f"Found more than 1 match for deployment vessel {i}. The matches are {[modelsVessels[x] for x in ok]}")
            print(f"Using the first one")
            ok = ok[0]
        else:
            ok = ok[0]
        okvessel = modelsVessels[ok]
        depVesselQ = models.Vessel.objects.filter(vessel_name=okvessel).first()  # first() is a bit redundant
        depVesselPk.append(depVesselQ.pk)

# add depVesselPk to df
df['deploymentVesselPk'] = depVesselPk
# mission_recoveryVessel
recVesselPk = []
for i in recoveryVessel:
    if i == "Eastcom":
        print(f"Renaming {i} as EastCom")
        i = "EastCom"
    # find which one it best matches with
    ok = [bool(re.search(i, x)) for x in modelsVessels]  # True, False
    ok = [i for i, x in enumerate(ok) if x]  # index
    # get the first index so it's easier to use
    if len(ok) == 0:
        print(f"Unable to find a match for recovery vessel {i}")
        recVesselPk.append(np.nan)
    else:
        if len(ok) > 1:
            print(f"Found more than 1 match for recovery vessel {i}. The matches are {[modelsVessels[x] for x in ok]}")
            print(f"Using the first one")
            ok = ok[0]
        else:
            ok = ok[0]
        okvessel = modelsVessels[ok]
        recVesselQ = models.Vessel.objects.filter(vessel_name=okvessel).first()  # first() is a bit redundant
        recVesselPk.append(recVesselQ.pk)

# add recVesselPk to df
df['recoveryVesselPk'] = recVesselPk

# mission_argosTag - need serial number and(/or?) PTT
# argosTag_serialNumber
argosTagSerial = df['ArgosTagsn']
# argosTag_PTT
argosTagPTT = df['ArgosTagPTT']
argosGlider = df['Glider']
argosMissionNumber = df['missionNumber']
# get pk from models.ArgosTag
argosTagList = list(zip(argosTagSerial, argosTagPTT, argosGlider, argosMissionNumber))
argosTagDf = pd.DataFrame(argosTagList, columns=['serialNumber', 'PTT', 'Glider', 'missionNumber'])
argosTagPk = []

for i in argosTagDf.itertuples():
    apttQ = models.ArgosTagPTT.objects.get(argosTag_PTT=getattr(i, 'PTT'))
    argosTagQ = models.ArgosTagSerialNumber.objects.filter(argosTag_PTTNumber=apttQ,
                                                            argosTag_serialNumber=getattr(i, 'serialNumber'))
    if argosTagQ.first() is None:
        print(f"Unable to find match for Argos tag with PTT {getattr(i, 'PTT')}"
              f" and serial number {getattr(i, 'serialNumber')}")
        argosTagPk.append(None)
    else:
        argosTagPk.append(argosTagQ.first().pk)

# add argosTagPk to df
df['argosTagPk'] = argosTagPk

# initialize model.Mission
for row in df.itertuples():
    imQ = models.Mission.objects.filter(mission_platformName=getattr(row, 'platformNamePk'),
                                        mission_number=getattr(row, 'missionNumber'))
    if imQ.first() is None: # mission is not in database yet
        print(f"Adding glider {getattr(row, 'Glider')} and mission {getattr(row, 'missionNumber')} to database.")
        im = models.Mission(mission_platformName=models.PlatformName.objects.get(pk=getattr(row, 'platformNamePk')),
                            mission_number=getattr(row, 'missionNumber'),
                            mission_cruiseNumber=getattr(row, 'CruiseName'), # check
                            mission_platformNavFirmware= models.PlatformNavigationFirmware.objects.get(pk=getattr(row, 'platformNavigationFirmwarePk')),
                            mission_platformBattery=None if pd.isna(getattr(row, 'platformBatteryPk')) else models.PlatformBattery.objects.get(pk=getattr(row, 'platformBatteryPk')),
                            mission_platformRelease=None if pd.isna(getattr(row, 'platformReleasePk')) else models.PlatformRelease.objects.get(pk=getattr(row, 'platformReleasePk')),
                            mission_platformPayload=models.PlatformPayload.objects.get(pk=getattr(row, 'platformPayloadPk')),
                            mission_platformPayloadFirmware=None if pd.isna(getattr(row, 'platformPayloadFirmwarePk')) else models.PlatformPayloadFirmware.objects.get(pk=getattr(row, 'platformPayloadFirmwarePk')),
                            mission_deploymentDate=getattr(row, 'Deploymentdate'),
                            mission_recoveryDate=getattr(row, 'Recoverydate'),
                            mission_batteryMax=None if pd.isna(getattr(row, 'Batterymax')) else getattr(row, 'Batterymax'),
                            mission_batteryMin=None if pd.isna(getattr(row,'Batterymin')) else getattr(row,'Batterymin'),
                            mission_deploymentVessel=None if pd.isna(getattr(row, 'deploymentVesselPk')) else models.Vessel.objects.get(pk=getattr(row, 'deploymentVesselPk')),
                            mission_deploymentLongitude=None if pd.isna(getattr(row, 'Deploylon')) else getattr(row, 'Deploylon'),
                            mission_deploymentLatitude=None if pd.isna(getattr(row, 'Deploylat')) else getattr(row, 'Deploylat'),
                            mission_recoveryVessel=None if pd.isna(getattr(row, 'recoveryVesselPk')) else models.Vessel.objects.get(pk=getattr(row, 'recoveryVesselPk')),
                            mission_recoveryLongitude=None,
                            mission_recoveryLatitude=None,
                            mission_minimumLongitude=None if pd.isna(getattr(row, 'Lonmin')) else getattr(row, 'Lonmin'),
                            mission_minimumLatitude=None if pd.isna(getattr(row, 'Latmin')) else getattr(row, 'Latmin'),
                            mission_maximumLongitude=None if pd.isna(getattr(row, 'Lonmax')) else getattr(row, 'Lonmax'),
                            mission_maximumLatitude=None if pd.isna(getattr(row, 'Latmax')) else getattr(row, 'Latmax'),
                            mission_waypointsGiven=None if pd.isna(getattr(row, 'Waypointgiven')) else getattr(row, 'Waypointgiven'),
                            mission_distanceTravelled=None if pd.isna(getattr(row, 'Distancetravelledkm')) else getattr(row, 'Distancetravelledkm'),
                            mission_numberOfYos=None if pd.isna(getattr(row, 'numberOfYos')) else getattr(row, 'numberOfYos'),
                            mission_numberOfScienceYos=None if pd.isna(getattr(row, 'numberOfScienceProfiles')) else getattr(row, 'numberOfScienceProfiles'),
                            mission_profilingScheme=None if pd.isna(getattr(row, 'scienceEveryNumberOfYos')) else getattr(row, 'scienceEveryNumberOfYos'), # check attr name
                            mission_numberOfAlarms=None if pd.isna(getattr(row, 'numberOfAlarms')) else getattr(row, 'numberOfAlarms'),
                            mission_numberOfAlarmsWithOT=None if pd.isna(getattr(row, 'numberOfAlarmsWithOT')) else getattr(row, 'numberOfAlarmsWithOT'), # check db name
                            mission_hoursOfOT=None if pd.isna(getattr(row, 'numberOfAlarmsWithOT')) else getattr(row, 'numberOfAlarmsWithOT'), # check db name
                            mission_ballastedDensity=None if pd.isna(getattr(row, 'Ballasteddensity')) else getattr(row, 'Ballasteddensity'),
                            mission_argosTag=models.ArgosTagSerialNumber.objects.get(pk=getattr(row, 'argosTagPk')),
                            mission_institute=None,
                            mission_comments=getattr(row, 'Commentfordatafile'))
        im.save()
    else :
        print(f"There is already a mission for glider {getattr(row, 'Glider')} mission {getattr(row, 'missionNumber')}, "
              f"proceeding to next mission.")