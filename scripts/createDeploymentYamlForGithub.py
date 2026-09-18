"""Create a pyglider/IOOS deployment YAML for glider missions.

Writes one YAML per mission into the deploymentYaml repository, which is then
pushed to GitHub and pulled on the server.

Run standalone:

    python scripts/createDeploymentYamlForGithub.py --help
    python scripts/createDeploymentYamlForGithub.py --dry-run
    python scripts/createDeploymentYamlForGithub.py --latest
    python scripts/createDeploymentYamlForGithub.py --cruise GLI2025_SEA021_030

Or as a management command (no arguments available that way):

    python manage.py createDeploymentYamlForGithub

Output directory
----------------
Resolved in this order, first match wins:

  1. --output on the command line
  2. the GLIDER_DEPLOYMENT_YAML_DIR environment variable
  3. DEPLOYMENT_YAML_DIR in Django settings
  4. a directory named deploymentYaml beside the gliderMetadata repository

The previous version hardcoded one person's local path, so it silently wrote
nothing useful on any other machine.
"""

import argparse
import os
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "manage.py").exists())
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gliderMetadataDjango.settings")

import django
django.setup()

from django.conf import settings

from gliderMetadataApp import models
from scripts import createPygliderIOOSyaml as d

# --- Configuration ---------------------------------------------------------

ENV_VAR = "GLIDER_DEPLOYMENT_YAML_DIR"
SETTINGS_KEY = "DEPLOYMENT_YAML_DIR"
DEFAULT_DIRNAME = "deploymentYaml"

PLATFORM_COMPANY = "Alseamar"
PLATFORM_MODEL = "SeaExplorer"
TIMEBASE_SOURCE_VARIABLE = "NAV_LATITUDE"


class DeploymentYamlError(Exception):
    """Raised when the output location or mission data is unusable."""


# --- Output location -------------------------------------------------------

def resolveOutputDir(override=None, create=False):
    """Find the deploymentYaml directory without hardcoding anyone's machine."""
    candidate = None
    source = None

    if override:
        candidate, source = Path(override), "--output"
    elif os.environ.get(ENV_VAR):
        candidate, source = Path(os.environ[ENV_VAR]), f"${ENV_VAR}"
    elif getattr(settings, SETTINGS_KEY, None):
        candidate, source = Path(getattr(settings, SETTINGS_KEY)), f"settings.{SETTINGS_KEY}"
    else:
        candidate, source = ROOT.parent / DEFAULT_DIRNAME, "default location"

    resolved = candidate.expanduser().resolve()

    if not resolved.is_dir():
        if create:
            resolved.mkdir(parents=True, exist_ok=True)
        else:
            raise DeploymentYamlError(
                f"Output directory does not exist: {resolved}\n"
                f"(from {source})\n\n"
                f"Either clone the deploymentYaml repository there, or point at "
                f"the existing clone with one of:\n"
                f"  --output <path>\n"
                f'  $env:{ENV_VAR} = "<path>"\n'
                f"  {SETTINGS_KEY} = r\"<path>\"   # in gliderMetadataDjango/settings.py"
            )

    if not (resolved / ".git").exists():
        print(
            f"WARNING: {resolved} is not a git repository. Files written here "
            f"cannot be pushed to deploymentYaml.",
            file=sys.stderr,
        )

    return resolved, source


# --- Mission data ----------------------------------------------------------

def buildFilename(cruiseNumber):
    """Turn a cruise number into a deploymentYaml filename.

    'GLI2020_SEA019_078'  ->  'GLI2020SEA019M78.yaml'

    Returns None, with a reason, if the cruise number is not in that form.
    The previous implementation used re.sub, which returns the input unchanged
    when the pattern does not match, producing a plausible-looking but wrong
    filename instead of an error.
    """
    if not cruiseNumber:
        return None, "cruise number is empty"

    parts = str(cruiseNumber).strip().split("_")
    if len(parts) != 3:
        return None, f"expected 3 underscore-separated parts, got {len(parts)}"

    prefix, glider, missionPart = (p.strip() for p in parts)
    if not prefix or not glider:
        return None, "prefix or glider identifier is blank"

    try:
        missionIndex = int(missionPart)
    except ValueError:
        return None, f"mission part {missionPart!r} is not a number"

    return f"{prefix}{glider}M{missionIndex}.yaml", None


def collectMissions(cruiseFilter=None, latest=False):
    """Gather the fields needed to build each YAML, reporting unusable rows."""
    queryset = models.Mission.objects.all()

    if cruiseFilter:
        queryset = queryset.filter(mission_cruiseNumber__icontains=cruiseFilter)
    if latest:
        queryset = queryset.order_by("-id")[:1]

    usable = []
    skipped = []

    for mission in queryset.iterator():
        cruiseNumber = mission.mission_cruiseNumber
        label = cruiseNumber or f"mission pk={mission.pk}"

        platform = getattr(mission, "mission_platformName", None)
        if platform is None:
            skipped.append(f"{label}: no platform linked")
            continue

        serialNumber = getattr(platform, "platform_serial", None)
        if not serialNumber:
            skipped.append(f"{label}: platform has no serial number")
            continue

        missionNumber = mission.mission_number
        if missionNumber is None:
            skipped.append(f"{label}: mission number is empty")
            continue

        filename, reason = buildFilename(cruiseNumber)
        if filename is None:
            skipped.append(f"{label}: cannot build filename ({reason})")
            continue

        usable.append(
            {
                "serialNumber": serialNumber,
                "missionNumber": missionNumber,
                "cruiseNumber": cruiseNumber,
                "filename": filename,
            }
        )

    # Two missions resolving to the same filename means one silently overwrites
    # the other, so treat it as an error rather than letting it happen.
    seen = {}
    for record in usable:
        seen.setdefault(record["filename"], []).append(record["cruiseNumber"])

    for filename, cruises in seen.items():
        if len(cruises) > 1:
            raise DeploymentYamlError(
                f"{len(cruises)} missions produce the same filename {filename}: "
                f"{', '.join(map(str, cruises))}"
            )

    return usable, skipped


# --- Writing ---------------------------------------------------------------

def writeYaml(record, outputDir, overwrite=True, dryRun=False):
    """Create one deployment YAML. Returns 'written', 'skipped' or 'failed'."""
    destination = outputDir / record["filename"]

    if destination.exists() and not overwrite:
        return "skipped", f"{record['filename']} already exists"

    if dryRun:
        return "written", f"would write {record['filename']}"

    try:
        d.createPygliderIOOSyaml(
            platform_company=PLATFORM_COMPANY,
            platform_model=PLATFORM_MODEL,
            platform_serial=record["serialNumber"],
            mission_number=record["missionNumber"],
            timebase_sourceVariable=TIMEBASE_SOURCE_VARIABLE,
            interpolate=False,
            add_keep_variables=True,
            filename=str(destination),
        )
    except Exception as exc:
        return "failed", f"{record['filename']}: {exc}"

    if not destination.exists():
        return "failed", f"{record['filename']}: nothing was written"

    return "written", record["filename"]


# --- Entry point -----------------------------------------------------------

def parseArguments(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--output", help="deploymentYaml directory to write into")
    parser.add_argument("--cruise", help="only missions whose cruise number contains this")
    parser.add_argument("--latest", action="store_true", help="only the most recent mission")
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    parser.add_argument("--no-overwrite", action="store_true",
                        help="leave existing YAML files alone")
    parser.add_argument("--create-dir", action="store_true",
                        help="create the output directory if absent")

    # parse_known_args so the script still runs under the management command
    # wrapper, where sys.argv carries manage.py's own arguments.
    options, _ = parser.parse_known_args(argv)
    return options


def main(argv=None):
    options = parseArguments(argv)

    try:
        outputDir, source = resolveOutputDir(options.output, create=options.create_dir)
        missions, skipped = collectMissions(options.cruise, options.latest)
    except DeploymentYamlError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    print(f"Output directory: {outputDir}  (from {source})")
    if options.dry_run:
        print("Dry run: nothing will be written.\n")

    if skipped:
        print(f"{len(skipped)} mission(s) skipped:", file=sys.stderr)
        for line in skipped:
            print(f"  {line}", file=sys.stderr)
        print("", file=sys.stderr)

    if not missions:
        print("No missions to process.")
        return 0

    counts = {"written": 0, "skipped": 0, "failed": 0}
    failures = []

    for record in missions:
        status, detail = writeYaml(
            record,
            outputDir,
            overwrite=not options.no_overwrite,
            dryRun=options.dry_run,
        )
        counts[status] += 1

        if status == "failed":
            failures.append(detail)
            print(f"  FAILED  {detail}", file=sys.stderr)
        elif status == "written":
            print(
                f"  {detail}  (glider {record['serialNumber']}, "
                f"mission {record['missionNumber']})"
            )

    print(
        f"\n{counts['written']} written, {counts['skipped']} left alone, "
        f"{counts['failed']} failed, {len(skipped)} unusable."
    )

    if failures:
        print("\nNext: fix the failures above, then commit and push deploymentYaml.",
              file=sys.stderr)
        return 1

    if not options.dry_run and counts["written"]:
        print("Next: commit and push deploymentYaml, then pull it on the server.")

    return 0


if __name__ == "__main__":
    sys.exit(main())