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

from gliderMetadataApp import models


#reInitializeAll = True


def initiate_PlatformCompany():
    #  initialize PlatformCompany
    file = io.FileIO(file=r".\initializationData\platform\platformCompany.csv", mode="r")
    df = pd.read_csv(file)
    for row in df.itertuples():
        print(getattr(row, "platform_company"))
        pc = models.PlatformCompany(platform_company=getattr(row, "platform_company"),
                                    platform_model=getattr(row, "platform_model"))
        pc.save()


def initiate_PlatformName():
    file = io.FileIO(file=r".\initializationData\platform\platformName.csv", mode="r")
    df = pd.read_csv(file)
    for row in df.itertuples():
        pn = models.PlatformName(platform_companyId=models.PlatformCompany.objects.get(pk=getattr(row, "platform_companyId")),
                                 platform_serial=getattr(row, "platform_serial"),
                                 platform_name=getattr(row, "platform_name"),
                                 platform_wmo=getattr(row, "platform_wmo"))
        pn.save()


def initiate_PlatformNavigationFirmware():
    file = io.FileIO(file=r".\initializationData\platform\platformNavigationFirmware.csv", mode="r")
    df = pd.read_csv(file)
    for row in df.itertuples():
        pnf = models.PlatformNavigationFirmware(platform_navFirmwareVersion=getattr(row, "platformNavigationFirmware"),
                                                platform_navFirmwareComments=getattr(row, "platformNavigationFirmwareNotes"))
        pnf.save()


def initiate_PlatformPayload():
    file = io.FileIO(file=r".\initializationData\platform\platformPayload.csv", mode="r")
    df = pd.read_csv(file)
    for row in df.itertuples():
        pp = models.PlatformPayload(platform_payloadSerialNumber=getattr(row, "platformPayloadSerialNumber"),
                                    platform_payloadOriginalPlatform=models.PlatformName.objects.get(pk=getattr(row, "platformPayloadOriginalPlatform")))
        pp.save()


def initiate_PlatformPayloadFirmware():
    file = io.FileIO(file=r".\initializationData\platform\platformPayloadFirmware.csv", mode="r")
    df = pd.read_csv(file)
    for row in df.itertuples():
        ppf = models.PlatformPayloadFirmware(platform_payloadFirmwareVersion=getattr(row, "platformPayloadFirmware"),
                                             platform_payloadFirmwareVersionComments=getattr(row, "platformPayloadFirmwareComments"))
        ppf.save()


def initiate_PlatformBattery():
    file = io.FileIO(file=r".\initializationData\platform\platformBattery.csv", mode="r")
    df = pd.read_csv(file)
    for row in df.itertuples():
        pb = models.PlatformBattery(platform_batteryType=getattr(row, "platformBatteryType"),
                                    platform_batteryGeneration=getattr(row, "platformBatteryGeneration"))
        pb.save()


def initiate_PlatformRelease():
    file = io.FileIO(file=r".\initializationData\platform\platformRelease.csv", mode="r")
    df = pd.read_csv(file)
    for row in df.itertuples():
        pr = models.PlatformRelease(platform_releaseType=getattr(row, "platformReleaseType"),
                                    platform_releaseAttachMethod=getattr(row, "platformReleaseAttachMethod"))
        pr.save()


# commented out calls to functions indicates that the tables were initialized
# note that if the database has to be re-initialized, some care should be taken
# for the primary key call (see comments next to applicable functions)
# initiate_PlatformCompany()
# initiate_PlatformName() # primary key call
# initiate_PlatformNavigationFirmware()
# initiate_PlatformPayload() # primary key call to Platform
# initiate_PlatformPayloadFirmware()
# initiate_PlatformBattery()
# initiate_PlatformRelease()
