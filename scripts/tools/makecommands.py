"""Generate a Django management command wrapper for each script under scripts/.

Run from anywhere in the repository:

    python scripts/tools/makeCommands.py

Recurses through scripts/ and its subdirectories, creating one command per
runnable script:

    python manage.py initializeMission
    python manage.py createDeploymentYamlForGithub

Re-run after adding, moving, or renaming a script. Existing wrappers are
overwritten; wrappers whose script has disappeared are reported but not deleted.

The wrappers contain no logic. All logic stays in scripts/.
"""

import re
import sys
from pathlib import Path

APP_NAME = "gliderMetadataApp"
SCRIPT_ROOT = "scripts"

# Directories under scripts/ that hold no runnable scripts.
EXCLUDE_DIRS = {"tools", "__pycache__", "archive", "old", "deprecated", ".ipynb_checkpoints"}

# Filename prefixes that mark importable helpers rather than scripts.
EXCLUDE_PREFIXES = ("_", "fn_", "test_")

# Specific filenames to skip regardless of location.
EXCLUDE_FILES = {"__init__.py", "conftest.py"}

TEMPLATE = '''"""Auto-generated wrapper for {rel_path}.

Do not edit by hand. Regenerate with:  python scripts/tools/makeCommands.py
The logic lives in {rel_path}
"""

import runpy
from pathlib import Path

from django.core.management.base import BaseCommand

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = PROJECT_ROOT / "{rel_path}"


class Command(BaseCommand):
    help = "Run {rel_path}"

    def handle(self, *args, **options):
        if not SCRIPT.exists():
            self.stderr.write(self.style.ERROR(f"Script not found: {{SCRIPT}}"))
            return

        self.stdout.write(f"Running {{SCRIPT.name}}")
        runpy.run_path(str(SCRIPT), run_name="__main__")
        self.stdout.write(self.style.SUCCESS(f"{{SCRIPT.name}} finished"))
'''


def findProjectRoot():
    """Walk up from this file until manage.py is found."""
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "manage.py").exists():
            return candidate
    sys.exit("Could not locate manage.py. Is this file inside the repository?")


def camelJoin(parts):
    """Join name fragments, capitalising all but the first."""
    parts = [p for p in parts if p]
    if not parts:
        return ""
    return parts[0] + "".join(p[:1].upper() + p[1:] for p in parts[1:])


def commandName(stem, folderParts=()):
    """Turn a script name into a valid command (module) name.

    initializeNetwork              -> initializeNetwork
    initializeMissionSummary.Misc  -> initializeMissionSummaryMisc
    initialize-mission-location    -> initializeMissionLocation

    folderParts, when given, are prefixed to disambiguate a name collision.
    """
    fragments = [f for f in re.split(r"[.\-\s]+", stem) if f]
    name = camelJoin(list(folderParts) + fragments)
    name = re.sub(r"[^0-9a-zA-Z_]", "", name)

    if not name or name[0].isdigit():
        return None
    return name


def collectScripts(scriptRoot):
    """Find every runnable script under scripts/, at any depth."""
    found = []
    for path in sorted(scriptRoot.rglob("*.py")):
        if any(part in EXCLUDE_DIRS for part in path.relative_to(scriptRoot).parts[:-1]):
            continue
        if path.name in EXCLUDE_FILES:
            continue
        if path.name.startswith(EXCLUDE_PREFIXES):
            continue
        found.append(path)
    return found


def main():
    root = findProjectRoot()
    scriptRoot = root / SCRIPT_ROOT
    commandDir = root / APP_NAME / "management" / "commands"

    if not scriptRoot.is_dir():
        sys.exit(f"Script directory not found: {scriptRoot}")

    # Django will not discover commands without these package markers.
    for pkg in (commandDir.parent, commandDir):
        pkg.mkdir(parents=True, exist_ok=True)
        initFile = pkg / "__init__.py"
        if not initFile.exists():
            initFile.write_text("")
            print(f"created {initFile.relative_to(root)}")

    scripts = collectScripts(scriptRoot)
    if not scripts:
        sys.exit(f"No scripts found under {scriptRoot}")

    # First pass: plain names. Any stem used more than once gets disambiguated
    # by its containing folder on the second pass.
    stems = [p.stem for p in scripts]
    duplicated = {s for s in stems if stems.count(s) > 1}

    generated = {}
    for script in scripts:
        relPath = script.relative_to(root).as_posix()
        folderParts = script.parent.relative_to(scriptRoot).parts if script.stem in duplicated else ()
        name = commandName(script.stem, folderParts)

        if name is None:
            print(f"SKIPPED  {relPath}  (cannot form a valid command name)")
            continue
        if name in generated:
            print(f"SKIPPED  {relPath}  (name '{name}' already used by {generated[name]})")
            continue

        (commandDir / f"{name}.py").write_text(
            TEMPLATE.format(rel_path=relPath), encoding="utf-8"
        )
        generated[name] = relPath
        print(f"{name:<45} <- {relPath}")

    # Flag wrappers left behind by renamed, moved, or deleted scripts.
    for existing in sorted(commandDir.glob("*.py")):
        if existing.name == "__init__.py":
            continue
        if existing.stem not in generated:
            print(f"STALE?   {existing.name}  (no matching script; delete if unwanted)")

    print(f"\n{len(generated)} command(s) written to {commandDir.relative_to(root)}")
    print("List them with:  python manage.py help")


if __name__ == "__main__":
    main()