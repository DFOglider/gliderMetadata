import io
import operator

import pandas as pd
import re
from gliderMetadataApp import models
from scripts import fn_readMissionFile as rmf


def convert_date(date):
    return pd.to_datetime(date.apply(lambda d: str(d)[0:8]), errors='coerce')

df = rmf.readMissionFile()


# InstrumentMission table

# instrument_mission
# get pk value of the platform
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
# get pk from models.Mission

# have to iterate through each instrument since there are multiple instruments on the glider per mission
instrumentAbbrev = ['GPCTD',
                    'GPCTDDO',
                    'Rinko',
                    'Ecopuck',
                    'LEGATO',
                    'CODA',
                    'Minifluo',
                    'Tridente'
                    # 'PAM' # omitting PAM for now (2023 01 24) - don't have instrument information in database
                    ]
instrumentPk = []
instrumentMissionPk = []
instrumentType = []
instrumentWarmUp = []
instrumentSamplingRate = []

for d in df.itertuples():
    print(f"{getattr(d, 'Glider')} mission {getattr(d, 'missionNumber')}")
    # get pk value from models.Mission
    missionQ = models.Mission.objects.filter(mission_platformName=getattr(d, 'platformNamePk'),
                                             mission_number=getattr(d, 'missionNumber')).first()
    for i in instrumentAbbrev:
        # get the serial number
        if i == 'CODA':
            serialNumberName = i + 'sn'
        else:
            serialNumberName = i + 'SN'
        serialNumber = getattr(d, serialNumberName)
        if pd.isna(serialNumber):
            print(f"Serial number for {i} is {serialNumber} "
                  #f"for {getattr(d, 'Glider')} mission {getattr(d, 'missionNumber')} "
                  f", continuing to next instrument or mission.")
            continue
        # convert serial number to string to match with database
        if isinstance(serialNumber, float):
            serialNumber = str(int(serialNumber))
        if isinstance(serialNumber, int):
            serialNumber = str(serialNumber)
        # if GPCTD, add '0' in front of number
        if i == 'GPCTD':
            serialNumber = '0' + serialNumber
        # if Minifluo, take first three letters (MFL), add middle part, then the number at the end
        # for initialization this is fine
        if i == 'Minifluo':
            serialNumber = serialNumber[0:3] + '-01-M-10000-ENS-001-SN' + serialNumber[3]
        #  print(f"Serial number : {serialNumber}")
        # get the calibration date
        # PAM does not have calibration date, so set as nan
        if i == 'PAM':
            calibrationDate = 'nan'
        else:
            calibrationDateName = i + 'caldate'
            calibrationDate = getattr(d, calibrationDateName)
            # convert timestamp to datetime.date type object
        # get warmup
        # PAM does not have warmup, so set as nan
        if i == 'PAM':
            warmUp = 'nan'
        else:
            # GPCTD DO warm up is same as GPCTD
            if i == 'GPCTDDO':
                warmUpName = 'GPCTD' + 'warmup'
            # LEGATO CODA warm up is same as LEGATO
            elif i == 'CODA':
                warmUpName = 'LEGATO' + 'warmup'
            # Tridente warm up is same as LEGATO
            elif i == 'Tridente':
                warmUpName = 'LEGATO' + 'warmup'
            else :
                warmUpName = i + 'warmup'
        # get samplingrate
        if i == 'GPCTDDO':
            samplingRateName = 'Samplingrate' + 'GPCTD' + 's'
        elif i == 'Ecopuck':
            samplingRateName = 'Samplingrate' + 'Eco' + 's'
        elif i in ['LEGATO', 'CODA']:
            samplingRateName = 'Samplingrate' + 'Legato' + 's'
        else :
            samplingRateName = 'Samplingrate' + i + 's'
        # get match from model using serial number and calibration date
        # first see if there is a match for the calibration date
        dateMatch = models.InstrumentCalibration.objects.filter(instrument_calibrationDate=calibrationDate.date())
        # next get the serial number out of each match
        # have to do it in loop since it's a primary key value
        dateMatchSerial = []
        for item in dateMatch.iterator():
            dateMatchSerial.append(item.instrument_calibrationSerial.instrument_serialNumber)
        dateMatchSerialPk = dateMatch.values_list('instrument_calibrationSerial', flat=True).distinct()
        # dateMatchSerialList = list(zip(dateMatchSerial, dateMatchSerialPk))
        # dateMatchSerialDf = pd.DataFrame(dateMatchSerialList, columns=['serialNumber', 'PkValue'])
        ok = [bool(re.search(serialNumber, x)) for x in dateMatchSerial]  # True/False
        ok = [i for i, x in enumerate(ok) if x]  # index
        # get the first index so it's easier to use
        if len(ok) == 0:
            print(f"Unable to find a match for instrument {i} with serial number {serialNumber} "
                  f"and calibration date {calibrationDate.date()} "
                  #f"for {getattr(d, 'Glider')} {getattr(d, 'missionNumber')} "
                  )
            instrumentPk.append(None)
        else:
            if len(ok) > 1:
                print(
                    f"Found more than 1 match for instrument {i} with serial number  {serialNumber} "
                    f"and calibration date {calibrationDate.date()}. "
                    f"The serial number matches are {[dateMatchSerial[x] for x in ok]}")
                print(f"Using the first one")
                ok = ok[0]
            else:
                ok = ok[0]
            instrumentQ = models.InstrumentCalibration.objects.filter(instrument_calibrationDate=calibrationDate.date(),
                                                                      instrument_calibrationSerial=dateMatchSerialPk[ok])
            instrumentPk.append(instrumentQ.first().pk)
        instrumentType.append(i)
        instrumentWarmUp.append(getattr(d, warmUpName))
        instrumentSamplingRate.append(getattr(d, samplingRateName))
        if missionQ is None:
            print(f"Unable to find primary key value for glider{getattr(d, 'Glider')} mission {getattr(d, 'missionNumber')}")
            instrumentMissionPk.append(None)
        else:
            instrumentMissionPk.append(missionQ.pk)


instrumentDf = pd.DataFrame(list(zip(instrumentMissionPk, instrumentPk,
                                     instrumentType, instrumentWarmUp, instrumentSamplingRate)),
                            columns=['instrumentMissionPk', 'instrumentPk',
                                     'instrumentType', 'instrumentWarmUp', 'instrumentSamplingRate'])

# initialize InstrumentMission
for row in instrumentDf.itertuples():
    # check if it's already in database
    iimcheck = models.InstrumentMission.objects.filter(instrument_mission = models.Mission.objects.get(pk=getattr(row, 'instrumentMissionPk')),
                                   instrument_calibration = models.InstrumentCalibration.objects.get(pk=getattr(row, 'instrumentPk')),
                                   instrument_warmUp = getattr(row, 'instrumentWarmUp'),
                                   instrument_samplingRate = getattr(row, 'instrumentSamplingRate'))
    if iimcheck.exists():
        print(f"Instruments exists for mission")
    else:
        print(f"Adding instruments")
        iim = models.InstrumentMission(instrument_mission = models.Mission.objects.get(pk=getattr(row, 'instrumentMissionPk')),
                                       instrument_calibration = models.InstrumentCalibration.objects.get(pk=getattr(row, 'instrumentPk')),
                                       instrument_warmUp = getattr(row, 'instrumentWarmUp'),
                                       instrument_samplingRate = getattr(row, 'instrumentSamplingRate'))
        iim.save()