import io
import pandas as pd
from gliderMetadataApp import models
# note that we used to track the original platform they payload was associated with, but no longer
data = {'platform_payloadSerialNumber' : ['163']
        }
df = pd.DataFrame(data)
for row in df.itertuples():
    print(f"Getting {getattr(row, 'platform_payloadSerialNumber')}")
    # query to get platform payload
    ippQ = models.PlatformPayload.objects.filter(platform_payloadSerialNumber=getattr(row, 'platform_payloadSerialNumber'))
    if ippQ.first() is None:
        print('Adding ...')
        ipp = models.PlatformPayload(platform_payloadSerialNumber=getattr(row, 'platform_payloadSerialNumber'),
                                     platform_payloadOriginalPlatform=None)
        ipp.save()
    else:
        print('Already in database.')