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


def initiate_InstrumentMake():
    file = io.FileIO(file=r".\initializationData\instrument\instrumentMake.csv", mode="r")
    df = pd.read_csv(file)
    for row in df.itertuples():
        im = models.InstrumentMake(instrument_make=getattr(row, "instrument_make"))
        im.save()


def initiate_InstrumentType():
    file = io.FileIO(file=r".\initializationData\instrument\instrumentType.csv", mode="r")
    df = pd.read_csv(file)
    for row in df.itertuples():
        it = models.InstrumentType(instrument_type=getattr(row, "instrument_type"))
        it.save()


def initiate_InstrumentModel():
    file = io.FileIO(file=r".\initializationData\instrument\instrumentModel.csv", mode="r")
    df = pd.read_csv(file)
    for row in df.itertuples():
        im = models.InstrumentModel(instrument_modelMake=models.InstrumentMake.objects.get(pk = getattr(row, "instrumentMake_id")),
                                    instrument_modelType=models.InstrumentType.objects.get(pk=getattr(row, "instrumentType_id")),
                                    instrument_model=getattr(row, "instrument_model"),
                                    instrument_longname=getattr(row, "instrument_longName"))
        im.save()


def initiate_InstrumentSerialNumber():
    file = io.FileIO(file=r".\initializationData\instrument\instrumentSerialNumber.csv", mode="r")
    df = pd.read_csv(file)
    for row in df.itertuples():
        isn = models.InstrumentSerialNumber(instrument_serialNumberModel=models.InstrumentModel.objects.get(pk=getattr(row, "instrumentModel_id")),
                                            instrument_originalPlatform=models.PlatformName.objects.get(pk=getattr(row, "instrument_originalPlatform")),
                                            instrument_serialNumber=getattr(row, "instrument_serialNumber"))
        isn.save()


def initiate_InstrumentCalibration():
    file = io.FileIO(file=r".\initializationData\instrument\instrumentCalibration.csv", mode="r")
    df = pd.read_csv(file)
    # format instrument_calibrationDate
    df['instrument_calibrationDate'] = pd.to_datetime(df['instrument_calibrationDate'], format='"%Y-%m-%d"')
    for row in df.itertuples():
        ic = models.InstrumentCalibration(instrument_calibrationSerial=models.InstrumentSerialNumber.objects.get(pk=getattr(row, "instrumentSerialNumber_id")),
                                          instrument_calibrationDate=getattr(row, "instrument_calibrationDate"),
                                          instrument_calibrationReport=getattr(row, "instrument_calibrationReport"),
                                          instrument_calibrationReportNotes=getattr(row, "instrument_calibrationReportNotes"),
                                          instrument_calibrationDateNotes=getattr(row, "instrument_calibrationDateNotes"))
        ic.save()


# commented out calls to functions indicates that the tables were initialized
# note that if the database has to be re-initialized, some care should be taken
# for the primary key call (see comments next to applicable functions)
# initiate_InstrumentMake()
# initiate_InstrumentType()
# initiate_InstrumentModel() # primary key to make and type and original platform
# initiate_InstrumentSerialNumber() # primary key call to model
# initiate_InstrumentCalibration() # primary key call to serial number