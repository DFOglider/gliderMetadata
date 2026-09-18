# gliderMetadata

Metadata database for glider missions. Django is used here purely as an ORM and
migration layer over a SQLite database — there is no web interface. All work is
done by running management commands from the command line.

## Repository layout

```
gliderMetadata/
├── manage.py                          # Django entry point; project root
├── requirements.txt
├── gliderMetadataDjango/              # settings package
│   └── settings.py
├── gliderMetadataApp/
│   ├── models.py
│   └── management/commands/           # command wrappers (auto-generated)
├── initializationData/
│   └── GliderMetadata.xlsx            # metadata spreadsheet, overwritten each mission
├── scripts/
│   ├── fn_readMissionFile.py          # shared spreadsheet reader
│   ├── initialize/                    # the actual logic
│   └── tools/makeCommands.py          # regenerates the command wrappers
└── db.sqlite3                         # confirm path in settings.py
```

**The project root is the directory containing `manage.py`.** Run everything from there.

## Setup

### First time on a machine

```powershell
cd C:\Users\<user>\Documents\gliderMetadata
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py check
```

`check` loads settings, imports every app in `INSTALLED_APPS`, and validates the
models. It does not touch the database. A clean result means the environment is
sound. Run it before each mission as a smoke test.

If PowerShell blocks the activate script, allow it once for your user:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### Every session

```powershell
cd C:\Users\<user>\Documents\gliderMetadata
.\venv\Scripts\Activate.ps1
```

The prompt should show `(venv)`. Confirm with
`python -c "import sys; print(sys.prefix)"` — it must point inside the repo,
not at the system Python install.

## How the scripts are run

The logic lives in `scripts\`. Each script is exposed as a Django
management command by a thin wrapper in
`gliderMetadataApp\management\commands\`, so scripts run as:

```powershell
python manage.py initializeMission
```

Each command is its own process with a fresh interpreter, so there is no need to
exit and reopen a shell between steps.

List every available command with `python manage.py help` — commands appear
under a `[gliderMetadataApp]` heading.

### Adding or renaming a script

Put it in `scripts\`, then regenerate the wrappers:

```powershell
python scripts\tools\makeCommands.py
```

The generator prints each command name beside its source file. Dots in filenames
are collapsed, so `initializeMissionSummary.Misc.py` becomes the command
`initializeMissionSummaryMisc`.

### Editing a script

Every script in `scripts\` starts with this header so that it can be run standalone with Django:

```python
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
```

Two rules:

- **All Django and project imports must come after `django.setup()`.** Moving a
  `models` import to the top of the file breaks it with `AppRegistryNotReady`.
- Do not delete the header. It is redundant when run via `manage.py`, but it lets
  the script still be run standalone as `python scripts\initialize\<name>.py`,
  which is useful when debugging one in isolation.

---

## Per-mission workflow

### 1. Move the mission data

1. Copy the glider mission from the shared drive (`R:\`) to the local machine.
2. Connect to the server in FileZilla.
3. Copy the mission from the local machine into `delayedData/` in the server root.

### 2. Stage the spreadsheet

Copy the metadata spreadsheet from the shared drive into `initializationData\`.
It is always named `GliderMetadata.xlsx` — overwrite the previous copy, as the
newest file contains the newest mission.

Before running anything, open it and confirm:

- Missions that are planned or still in progress have been removed. (Chantelle
  deletes these trailing rows.)
- **The last row of the table is the mission being processed.**
- That final row is completely filled in.
- Some columns may legitimately be blank depending on what instruments the glider
  carried.

### 3. Back up the database

The commands write to SQLite and there is no undo.

```powershell
New-Item -ItemType Directory -Force backups | Out-Null
Copy-Item db.sqlite3 "backups\db_$(Get-Date -Format yyyyMMdd_HHmmss).sqlite3"
```

### 4. Run the initialization commands

Run these one at a time, in order, checking the result of each before moving on.
Later steps depend on rows created by earlier ones. Not every mission needs every
command — skip what does not apply.

| # | Updates | Command |
|---|---|---|
| 1 | `Mission` table | `python manage.py initializeMission` |
| 2 | `InstrumentMission` table | `python manage.py initializeInstrumentMission` |
| 3 | `ContributorMission` table | `python manage.py initializeContributorMission` |
| 4 | `ContributingInstitutionMission` table | `python manage.py initializeContributingInstitutionMission` |
| 5 | `Mission.summary` | one of the summary commands — see below |
| 6 | `Mission.network` | `python manage.py initializeNetwork` |
| 7 | `Mission.location` | `python manage.py initializeMissionLocation` |

#### Step 5: choosing the summary command

The summary text is written into `Mission.summary` for the mission matching that
location, so **which command you run depends on where the glider flew**:

- **HL line** — the variant with no suffix: `initializeMissionSummary`
- **Misc** — for missions that do not follow a defined region:
  `initializeMissionSummaryMisc`
- **PAM** — passive acoustic monitoring, the whale team's Emerald Basin missions:
  `initializeMissionSummaryPAM`
- **Browns Bank** — does not exist yet; a new variant needs to be written.

If unsure which applies, re-running all of them is safe. The text is boilerplate —
check wording with Melany and Clark before adding a new region.

#### Watch for

- **Mission type** — confirm no new mission type has appeared that the scripts do
  not know about. A new type generally means a new summary variant is needed.
- **`initializeNetwork`** prints nothing on success. Silence is expected; verify
  the field in the database rather than waiting for a message.
- **`initializeMissionLocation`** was added for CIOOS and needs attention when
  there is a new mission type. Its overnight-mission warning can be ignored — it
  refers to an early mission that is not of interest.


### 6. Verify

```powershell
python manage.py shell
```

```python
from gliderMetadataApp import models
m = models.Mission.objects.latest("id")
print(m.mission_platformName, m.mission_network, m.mission_location)
print(m.mission_summary[:200])
```

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'gliderMetadataApp'`**
The bootstrap header is missing from that script, or the script is being run from
a copy outside the repository. Python puts the *script's* directory on `sys.path`,
not the current working directory.

**`ImproperlyConfigured` / `AppRegistryNotReady`**
A Django or project import is sitting above `django.setup()` in the file.

**`ModuleNotFoundError` for a third-party package during `check`**
That package is in `INSTALLED_APPS` but not installed. Django stops at the first
failure, so there may be more than one. Install it, re-run `check`, repeat. Note
that pip names use hyphens while `INSTALLED_APPS` uses underscores
(`pip install django-extensions` → `django_extensions`).

**`Unknown command: '<name>'`**
Django found no wrapper. Check that `gliderMetadataApp\management\__init__.py`
and `gliderMetadataApp\management\commands\__init__.py` both exist and are真 `.py`
files (Windows can silently create `__init__.py.txt` when extensions are hidden).
Then re-run `python scripts\tools\makeCommands.py`.

**`django.db.utils.OperationalError: no such table`**
Migrations have not been applied to this database: `python manage.py migrate`.
Check state first with `python manage.py showmigrations`.

**Spreadsheet read errors**
Chantelle patched the reader for a parsing problem. Confirm you have her latest
version of `fn_readMissionFile.py` before debugging from scratch.

---

## Known gaps

Tracked here so they are not rediscovered each mission. Do this work on a branch.

- **Spreadsheet reader is fragile.** `fn_readMissionFile.py` is shared by most of
  the initialize scripts, so hardening it once fixes every caller. Wanted:
  explicit dtype handling, validation that the final row is complete, and a clear
  error when an expected column is absent. A silent misparse writes wrong
  metadata to the database instead of failing loudly — this is the highest-value
  fix.
- **Summary variants duplicate code.** Better as one script taking a `--region`
  argument with the boilerplate text in a data file.
- **Browns Bank summary variant** still needs writing.
- **No arguments.** Mission identifiers and paths are implicit in the spreadsheet
  and in hardcoded values. Giving the commands real arguments
  (`--mission`, `--dry-run`) would make each run self-documenting in shell history
  and add `--help` for free.
- **No transaction safety.** A command that fails halfway leaves partial rows.
  Wrapping the wrapper body in `transaction.atomic()` would fix this, but confirm
  first that no script intentionally commits in stages.