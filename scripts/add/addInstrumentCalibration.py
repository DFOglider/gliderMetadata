import io
import operator
import pandas as pd
import re
from gliderMetadataApp import models
# can either put information in a .csv file, or create a dataframe here with comments
# need 6 columns,
# 'instrument_model'
# 'instrument_serialNumber'
# 'instrument_calibrationDate'
# 'instrument_calibrationReportNotes'
# 'instrument_calibrationDateNotes'

# read in file
# file = io.FileIO(file=r".\initializationData\instrument\instrumentCalibrationUpdate01.csv", mode="r")
# df = pd.read_csv(file)
# 20250509 - add SX Legato and coda instruments
# 20250512 - add GPCTD and 43F sensors calibrated at end of 2024 season
# 20250904 - add additional SX Legato and coda
data = {'instrument_model' :['RBR Legato3',
                             'RBR Legato3', 'RBR Legato3', 'RBR Legato3', 'RBR Legato3',
                             'RBR Legato3',
                             'RBR Legato3',
                             'RBR Coda T.ODO',
                             'RBR Coda T.ODO',
                             'SBE GPCTD',
                             'SBE GPCTD',
                             'SBE 43F DO',
                             'SBE 43F DO',
                             'RBR Legato3', 'RBR Coda T.ODO',
                             'RBR Legato3', 'RBR Coda T.ODO',
                             'WET Labs ECO FLBBCD', 'WET Labs ECO FLBBCD',
                             'WET Labs ECO FLBBCD',
                             'RBR tridente', 'RBR tridente', 'RBR tridente',
                             'Pro-Oceanus Mini pCO2', 'Pro-Oceanus Mini pCO2',
                             'Nortek Glider1000 AD2CP',
                             'RBR Coda T.ODO','RBR Coda T.ODO',
                             'RBR Legato3',
                             'RBR Legato3',
                             'RBR Legato3',
                             'RBR Coda T.ODO',
                             'RBR Coda T.ODO',
                             'RBR Coda T.ODO'],
        'instrument_serialNumber' : ['"205045"',
                                     '"210185"', '"210185"', '"210185"', '"210185"',
                                     '"212531"',
                                     '"214386"',
                                     '"212279"',
                                     '"212973"',
                                     '"0188"',
                                     '"0184"',
                                     '"43-3365"',
                                     '"43-3336"',
                                     '"214389"', '"212970"',
                                     '"212536"', '"211391"',
                                     '"4548"', '"4739"',
                                     '"4550"',
                                     '"239559"', '"240453"', '"241970"',
                                     '"45-624-18"', '"45-623-18"',
                                     '"107453"',
                                     '"212973"', '"212279"',
                                     '"241286"',
                                     '"241049"',
                                     '"241050"',
                                     '"240440"',
                                     '"240444"',
                                     '"240447"'],
        'instrument_calibrationDate' : ['"2020-07-29"',
                                        '"2023-01-09"', '"2023-09-06"', '"2023-11-15"', '"2024-09-16"',
                                        '"2025-04-16"',
                                        '"2025-04-17"',
                                        '"2025-03-26"',
                                        '"2025-03-25"',
                                        '"2024-12-17"',
                                        '"2024-12-11"',
                                        '"2024-11-23"',
                                        '"2024-12-21"',
                                        '"2025-06-12"', '"2025-06-12"',
                                        '"2025-06-13"', '"2025-06-12"',
                                        '"2024-12-05"', '"2024-12-03"',
                                        '"2025-11-03"',
                                        '"2026-01-27"', '"2026-01-27"', '"2026-03-07"',
                                        '"2025-10-21"', '"2025-10-21"',
                                        '"2026-01-30"',
                                        '"2025-08-25"', '"2025-10-21"',
                                        '"2026-01-20"',
                                        '"2026-01-29"',
                                        '"2026-01-08"',
                                        '"2025-12-16"',
                                        '"2025-12-16"',
                                        '"2025-12-16"'],
        'instrument_calibrationReport' : ['LEGATO_205045-20200729.pdf',
                                          'LEGATO_210185_20230109.pdf', 'LEGATO_210185_20230906.pdf', 'LEGATO_210185_20231115.pdf', 'LEGATO_210185_20240916.pdf',
                                          'LEGATO_212531_20250416.pdf',
                                          'LEGATO_214386_20250417.pdf',
                                          'CODA_212279_20250326.pdf',
                                          'CODA_212973_20250325.pdf',
                                          'GPCTD_0188_20241211_T.pdf, GPCTD_0188_20241211_C.pdf, GPCTD_0188_20241211_P.pdf',
                                          'GPCTD_0184_20241211_T.pdf, GPCTD_0184_20241211_C.pdf, GPCTD_0184_20241211_P.pdf',
                                          '43F_3365_20241123_SOCAdjusted.pdf',
                                          '43F_3336_20241221_SOCAdjusted.pdf',
                                          'LEGATO_214389_20250612.pdf', 'CODA_212970_20250612.pdf',
                                          'LEGATO_212536_20250613.pdf', 'CODA_211391_20250612.pdf',
                                          'FLBBCD_4548_20241205.pdf', 'FLBBCD_4739_20241203.pdf',
                                          'FLBBCD_4550_20251103.pdf',
                                          'TRIDENTE_239559_fluo_2_20260127.pdf, TRIDENTE_239559_fluo_3_20260127.pdf, TRIDENTE_239559_turb_1_20260127.pdf',
                                          'TRIDENTE_240453_fluo_2_20260127.pdf, TRIDENTE_240453_fluo_3_20260127.pdf, TRIDENTE_240453_turb_1_20260127.pdf',
                                          'TRIDENTE_241970_fluo_2_20260311.pdf, TRIDENTE_241970_fluo_3_20260311.pdf, TRIDENTE_241970_turb_1_20260312.pdf',
                                          'pCO2_45-623-18.pdf', 'pCO2_45-624-18.pdf',
                                          'AD2CP_107453_20260130.pdf',
                                          'CODA_212973_20250825.pdf', 'CODA_212279_20251021.pdf',
                                          'LEGATO_241286_C_20260120.pdf, LEGATO_241286_P_20260113.pdf, LEGATO_241286_T_20260113.pdf',
                                          'LEGATO_241049_cond_1_20260129.pdf, LEGATO_241049_pres_3_20260127.pdf, LEGATO_241049_temp_2_20260126.pdf',
                                          'LEGATO_241050_cond_1_20260108.pdf, LEGATO_241050_pres_3_20251223.pdf, LEGATO_241050_temp_2_20251222.pdf',
                                          'CODA_240440_DO_20251216.pdf, CODA_240440_T_1_20251111.pdf',
                                          'CODA_240444_doxy_4_20251216.pdf, CODA_240444_temp_1_20251117.pdf',
                                          'CODA_240447_doxy_4_20251216.pdf, CODA_240447_temp_1_20251111.pdf'],
        'instrument_calibrationReportNotes' : ['',
                                               '', '', '', '',
                                               '',
                                               '',
                                               '',
                                               '',
                                               '',
                                               '',
                                               '',
                                               '',
                                               '', '',
                                               '', '',
                                               '', '',
                                               '',
                                               '', '', '',
                                               '','',
                                               '',
                                               '', '',
                                               '',
                                               '',
                                               '',
                                               '',
                                               '',
                                               ''],
        'instrument_calibrationDateNotes' : ['',
                                            '', '','','',
                                            '',
                                            '',
                                            '',
                                            '',
                                            '',
                                            '',
                                            '',
                                            '',
                                            '', '',
                                            '', '',
                                            '', '',
                                            '',
                                            '', '', '',
                                            '','',
                                            '',
                                            '','',
                                             '',
                                             '',
                                             '',
                                             '',
                                             '',
                                             '']}
df = pd.DataFrame(data)
# format instrument_calibrationDate
df['instrument_calibrationDate'] = pd.to_datetime(df['instrument_calibrationDate'], format='"%Y-%m-%d"')
for row in df.itertuples():
    print(f"Getting {getattr(row, 'instrument_model')} with SN {getattr(row, 'instrument_serialNumber')}"
          f" with calibration date {getattr(row, 'instrument_calibrationDate')}")
    # get the instrument model pk
    imQ = models.InstrumentModel.objects.get(instrument_model = getattr(row, 'instrument_model'))
    # get instrument serial number
    isnQ = models.InstrumentSerialNumber.objects.get(instrument_serialNumberModel = imQ.pk,
                                                     instrument_serialNumber = getattr(row, 'instrument_serialNumber'))
    # check if new calibration has been added
    icdQ = models.InstrumentCalibration.objects.filter(instrument_calibrationSerial = isnQ,
                                                       instrument_calibrationDate = getattr(row, 'instrument_calibrationDate'))
    # if not there, add it
    if icdQ.first() is None:
        print("Adding...")
    # now set the new calibration date and other info
        icd = models.InstrumentCalibration(instrument_calibrationSerial = isnQ,
                                           instrument_calibrationDate = getattr(row, 'instrument_calibrationDate'),
                                           instrument_calibrationReport = getattr(row, 'instrument_calibrationReport'),
                                           instrument_calibrationReportNotes = getattr(row, 'instrument_calibrationReportNotes'),
                                           instrument_calibrationDateNotes = getattr(row, 'instrument_calibrationDateNotes'))
        icd.save()
    else:
        print("Already in database.")