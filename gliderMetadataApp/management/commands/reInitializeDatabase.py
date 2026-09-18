"""Auto-generated wrapper for scripts/reInitialize/reInitializeDatabase.py.

Do not edit by hand. Regenerate with:  python scripts/tools/makeCommands.py
The logic lives in scripts/reInitialize/reInitializeDatabase.py
"""

import runpy
from pathlib import Path

from django.core.management.base import BaseCommand

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = PROJECT_ROOT / "scripts/reInitialize/reInitializeDatabase.py"


class Command(BaseCommand):
    help = "Run scripts/reInitialize/reInitializeDatabase.py"

    def handle(self, *args, **options):
        if not SCRIPT.exists():
            self.stderr.write(self.style.ERROR(f"Script not found: {SCRIPT}"))
            return

        self.stdout.write(f"Running {SCRIPT.name}")
        runpy.run_path(str(SCRIPT), run_name="__main__")
        self.stdout.write(self.style.SUCCESS(f"{SCRIPT.name} finished"))
