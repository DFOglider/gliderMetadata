import os
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "manage.py").exists())
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gliderMetadataDjango.settings")

import django
django.setup()

from gliderMetadataApp import models
# name, vocabulary
institution = [['Bedford Institute of Oceanography', 'https://edmo.seadatanet.org/report/1811'],
               ['Northwest Atlantic Fisheries Centre', 'https://edmo.seadatanet.org/report/4157'],
               ['St. Andrews Biological Station', 'https://edmo.seadatanet.org/report/4161'],
               ['Maurice Lamontagne Institute', 'https://edmo.seadatanet.org/report/4160']
              ]

for inst in institution:
    im = models.Institute(institute_name=inst[0],
                          institute_vocabulary=inst[1])
    im.save()