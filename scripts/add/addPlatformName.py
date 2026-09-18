import io
import pandas as pd
from gliderMetadataApp import models

data = {'platform_company' : ['Alseamar',
                              'Alseamar'],
        'platform_name' : ['Aspy',
                           'Sissiboo'],
        'platform_serial' : ['"220"',
                             '"221"'],
        'platform_wmo' : [8901224,
                          8901225],
        'platform_ices' : ['',
                           '']}
df = pd.DataFrame(data)
for row in df.itertuples():
    print(f"Getting {getattr(row, 'platform_name')} with serial {getattr(row, 'platform_serial')}")
    # query to get platform_company
    pcQ = models.PlatformCompany.objects.filter(platform_company=getattr(row, 'platform_company'))
    if pcQ.first() is None:
        print('platform_company not in database yet, please add.')
        print(f"Skipping  {getattr(row, 'platform_name')} with serial {getattr(row, 'platform_serial')}")
        continue
    else :
        platformCompanyQ = pcQ.first()
    # check if data has already been added
    pnQ = models.PlatformName.objects.filter(platform_name=getattr(row, 'platform_name'),
                                             platform_serial=getattr(row, 'platform_serial'))
    if pnQ.first() is None:
        print('Adding ...')
        im = models.PlatformName(platform_companyId = platformCompanyQ,
                                    platform_name=getattr(row, 'platform_name'),
                                    platform_serial=getattr(row, 'platform_serial'),
                                    platform_wmo=getattr(row, 'platform_wmo'),
                                 platform_ices= getattr(row, 'platform_ices'))
        im.save()
    else :
        print("Already in database.")