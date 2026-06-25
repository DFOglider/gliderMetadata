import io
import pandas as pd
from gliderMetadataApp import models

data = {'instrument_model' :['RBR Legato3', 'RBR Legato3', 'RBR Legato3', 'RBR Legato3',
                             'RBR Coda T.ODO', 'RBR Coda T.ODO',
                             'RBR Legato3',
                             'RBR Coda T.ODO',
                             'RBR Legato3',
                             'RBR Coda T.ODO',
                             'RBR tridente', 'RBR tridente', 'RBR tridente',
                             'Pro-Oceanus Mini pCO2', 'Pro-Oceanus Mini pCO2',
                             'Nortek Glider1000 AD2CP',
                             'RBR Legato3', 'RBR Legato3', 'RBR Legato3',
                             'RBR Coda T.ODO', 'RBR Coda T.ODO', 'RBR Coda T.ODO'
                             ],
        'instrument_originalPlatform' : [None, None, None, None,
                                         None, None,
                                         None,
                                         None,
                                         None,
                                         None,
                                         None, None, None,
                                         None, None,
                                         None,
                                         None, None, None,
                                         None, None, None],
        'instrument_serialNumber' : ['"205045"', '"210185"', '"212531"', '"214386"',
                                     '"212279"', '"212973"',
                                     '"214389"',
                                     '"212970"',
                                     '"212536"',
                                     '"211391"',
                                     '"239559"', '"240453"', '"241970"',
                                     '"45-624-18"', '"45-623-18"',
                                     '"107453"',
                                     '"241049"', '"241050"', '"241286"',
                                     '"240440"', '"240444"', '"240447"'
                                     ]}
df = pd.DataFrame(data)
for row in df.itertuples():
    print(f"Getting {getattr(row, 'instrument_serialNumber')} for instrument_model {getattr(row, 'instrument_model')}")
    # query to get instrument_model
    imQ = models.InstrumentModel.objects.filter(instrument_model=getattr(row, 'instrument_model'))
    if imQ.first() is None:
        print('instrument_model not in database yet, please add')
        print(f"Skipping {getattr(row, 'instrument_serialNumber')} for instrument_model {getattr(row, 'instrument_model')}")
        continue
    else :
        instrumentModelQ = imQ.first()
    # query to get instrument_originalPlatform
    ## skipping for now, settting to NULL
    # check if data has already been added
    isnQ = models.InstrumentSerialNumber.objects.filter(instrument_serialNumberModel=instrumentModelQ,
                                                        instrument_serialNumber=getattr(row, 'instrument_serialNumber'))
    if isnQ.first() is None:
        print('Adding...')
        isn = models.InstrumentSerialNumber(instrument_serialNumberModel=instrumentModelQ,
                                            instrument_originalPlatform=None,
                                            instrument_serialNumber=getattr(row, "instrument_serialNumber"))
        isn.save()
    else:
        print("Already in database.")