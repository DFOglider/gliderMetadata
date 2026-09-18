"""Read and validate the glider mission metadata spreadsheet.

Used by the initialize/, add/, edit/ and reInitialize/ scripts:

    from scripts import fn_readMissionFile as rmf
    df = rmf.readMissionFile()

Run directly for a diagnostic report, including exactly how each spreadsheet
header was matched to a column name, without touching the database:

    python scripts/fn_readMissionFile.py

Column matching
---------------
Spreadsheet headers are matched on a normalized key: lowercased, with
whitespace, non-breaking spaces, slashes, parentheses and punctuation removed.
So all of these resolve to the same column:

    "Deployment date"   "Deployment Date"   "DEPLOYMENT  DATE"   "Deploymentdate"

This matters because matching on the literal header text fails on a trailing
space or a capitalisation change, and the resulting error surfaces later, in
whichever script uses the column, rather than here.

Add new spellings to COLUMN_ALIASES rather than editing the matching logic.

The resolved names are identical to those the original implementation produced
for a well-formed spreadsheet, so downstream scripts are unaffected.

Dates
-----
Every date column is parsed from any of the four forms Excel produces: a real
datetime, a YYYYMMDD number, a YYYYMMDD string, or an Excel serial. Values that
cannot be read are reported, never silently coerced to NaT.
"""

import re
import sys
from pathlib import Path

import pandas as pd

# --- Configuration ---------------------------------------------------------

SPREADSHEET_DIR = "initializationData"

# Chantelle's documentation calls this GliderMetadata.xlsx; the original code
# opened GliderMission.xlsx. Both are accepted.
SPREADSHEET_NAMES = ("GliderMission.xlsx", "GliderMetadata.xlsx")

# Header is normally on row 2 (skiprows=1), but the row is detected rather
# than assumed. These are the candidates tried, in order of preference.
HEADER_SKIPROWS_CANDIDATES = (1, 0, 2, 3)

# Rows without these are not missions and are dropped.
REQUIRED_COLUMNS = ("annualMissionIndex", "Deploymentdate")

DATE_COLUMNS = (
    "Deploymentdate",
    "Recoverydate",
    "GPCTDcaldate",
    "GPCTDDOcaldate",
    "Rinkocaldate",
    "Ecopuckcaldate",
    "LEGATOcaldate",
    "CODAcaldate",
    "Minifluocaldate",
    "Tridentecaldate",
    "ADCPcaldate",
)

NUMERIC_COLUMNS = (
    "Ecopuckwarmup",
    "GPCTDwarmup",
    "Rinkowarmup",
    "LEGATOwarmup",
    "Minifluowarmup",
)

# Identifiers that must be text, never "12345.0" and never "nan".
IDENTIFIER_COLUMNS = ("ArgosTagPTT",)

# Columns that are genuinely instrument-dependent. Their absence is normal and
# is not reported. Move a column here once you have confirmed it is optional.
EXPECTED_OPTIONAL = {
    "Rinkocaldate",
    "CODAcaldate",
    "Minifluocaldate",
    "Tridentecaldate",
    "ADCPcaldate",
    "Rinkowarmup",
    "Minifluowarmup",
}

# Extra spellings seen in the wild, beyond the canonical name itself.
# Matching is on the normalized key, so case, spacing and punctuation do not
# need to be listed. Add a line here when a header changes.
COLUMN_ALIASES = {
    "annualMissionIndex": ["annual mission index", "mission index"],
    "missionNumber": ["mission #", "mission no", "mission number", "mission num"],
    "numberOfDays": ["# days", "num days", "number of days", "days"],
    "numberOfYos": ["# yo", "# yos", "num yo", "number of yos", "yos"],
    "numberOfScienceProfiles": [
        "# sc profile", "# sci profile", "# science profiles",
        "num science profiles", "number of science profiles",
    ],
    "numberOfAlarms": ["# alarm", "# alarms", "num alarms", "number of alarms"],
    "numberOfAlarmsWithOT": [
        "# alarm ot", "# alarms ot", "# alarm o t", "number of alarms ot",
    ],
    "scienceEveryNumberOfYos": [
        "science every # yos", "science every n yos", "sci every # yos",
    ],
    "Deploymentdate": ["deployment date", "deploy date", "date deployed"],
    "Recoverydate": ["recovery date", "recover date", "date recovered"],
    "GPCTDcaldate": ["gpctd cal date", "gp ctd cal date", "gpctd calibration date"],
    "GPCTDDOcaldate": [
        "gpctd do cal date", "gpctd-do cal date", "gpctd do calibration date",
    ],
    "Rinkocaldate": ["rinko cal date", "rinko calibration date"],
    "Ecopuckcaldate": ["ecopuck cal date", "eco puck cal date"],
    "LEGATOcaldate": ["legato cal date", "legato calibration date"],
    "CODAcaldate": ["coda cal date", "coda calibration date"],
    "Minifluocaldate": ["minifluo cal date", "mini fluo cal date"],
    "Tridentecaldate": ["tridente cal date", "trident cal date"],
    "ADCPcaldate": ["adcp cal date", "adcp calibration date"],
    "Ecopuckwarmup": ["ecopuck warmup", "ecopuck warm up", "eco puck warmup"],
    "GPCTDwarmup": ["gpctd warmup", "gpctd warm up"],
    "Rinkowarmup": ["rinko warmup", "rinko warm up"],
    "LEGATOwarmup": ["legato warmup", "legato warm up"],
    "Minifluowarmup": ["minifluo warmup", "minifluo warm up", "mini fluo warmup"],
    "ArgosTagPTT": ["argos tag ptt", "argos ptt", "ptt"],
}

MIN_PLAUSIBLE_YEAR = 2000
MAX_PLAUSIBLE_YEAR = 2100

EXCEL_SERIAL_MIN = 10_000
EXCEL_SERIAL_MAX = 80_000
EXCEL_EPOCH = "1899-12-30"

UNNAMED_PATTERN = re.compile(r"^unnamed:?\d*$")
PANDAS_DUPLICATE_SUFFIX = re.compile(r"\.\d+$")
# Which blank-header column is the mission index, 0-based. The original code
# hardcoded "Unnamed: 1". Used only to break a tie when content cannot
# distinguish the candidates.
ANNUAL_MISSION_INDEX_POSITION = 1


class MissionFileError(Exception):
    """Raised when the spreadsheet cannot be read or fails validation."""


# --- Column name matching --------------------------------------------------

def matchKey(name):
    """Reduce a header to a form that ignores cosmetic differences.

    'Deployment  Date ' and 'deployment date' both become 'deploymentdate'.
    '#' is kept, because it distinguishes 'Mission #' from a plain 'Mission'.
    """
    text = str(name).replace("\u00a0", " ")
    text = text.lower()
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[/()\[\].,;:'\"_\-]", "", text)
    return text


def buildAliasLookup():
    """Map every known spelling to its canonical column name."""
    lookup = {}
    collisions = []

    def register(key, canonical):
        if key in lookup and lookup[key] != canonical:
            collisions.append(f"{key!r} maps to both {lookup[key]} and {canonical}")
            return
        lookup[key] = canonical

    canonicalNames = (
        set(DATE_COLUMNS)
        | set(NUMERIC_COLUMNS)
        | set(IDENTIFIER_COLUMNS)
        | set(REQUIRED_COLUMNS)
        | set(COLUMN_ALIASES)
    )

    for canonical in canonicalNames:
        register(matchKey(canonical), canonical)
        for alias in COLUMN_ALIASES.get(canonical, []):
            register(matchKey(alias), canonical)

    if collisions:
        raise MissionFileError(
            "COLUMN_ALIASES contains ambiguous entries:\n  " + "\n  ".join(collisions)
        )

    return lookup


ALIAS_LOOKUP = buildAliasLookup()


def legacyClean(name):
    """The original cleaning, used for columns with no canonical name."""
    text = str(name).replace("\u00a0", " ")
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[/()]", "", text)
    return text

def chooseAnnualMissionIndex(dataframe, unnamedPositions, problems):
    """Pick which blank-header column holds the annual mission index.

    Recent spreadsheets have two unnamed numeric columns: a running total of
    all missions, and an annual tally that resets each January. They are
    distinguished by that reset — the annual tally decreases at least once,
    the running total never does.
    """
    if not unnamedPositions:
        return None
    if len(unnamedPositions) == 1:
        return unnamedPositions[0]

    scored = []
    for position in unnamedPositions:
        numeric = pd.to_numeric(dataframe.iloc[:, position], errors="coerce")
        valid = numeric.dropna()

        if valid.empty:
            scored.append((-1.0, position, "empty"))
            continue

        resets = int((valid.diff() < 0).sum())
        score = 0.0
        notes = []

        if resets:
            score += 10.0
            notes.append(f"{resets} reset(s)")
        else:
            notes.append("never decreases")

        # An annual tally stays small; a running total grows without bound.
        score += 1.0 / (1.0 + valid.max() / 100.0)
        notes.append(f"max {valid.max():g}")

        if position == ANNUAL_MISSION_INDEX_POSITION:
            score += 0.25
            notes.append("expected position")

        scored.append((score, position, ", ".join(notes)))

    scored.sort(key=lambda item: item[0], reverse=True)
    best = scored[0][1]

    detail = "; ".join(
        f"column {position + 1}: {notes}" for _, position, notes in scored
    )
    problems.append(
        f"{len(unnamedPositions)} columns have no header. Using column "
        f"{best + 1} as annualMissionIndex ({detail}). If that is wrong, set "
        f"ANNUAL_MISSION_INDEX_POSITION in this file."
    )

    # A spreadsheet spanning several years with no reset means the chosen
    # column is probably the running total, not the annual tally.
    chosenValues = pd.to_numeric(dataframe.iloc[:, best], errors="coerce").dropna()
    if not chosenValues.empty and (chosenValues.diff() < 0).sum() == 0:
        problems.append(
            f"column {best + 1} never resets, so it may be the running total "
            f"rather than the annual tally. Check the choice above."
        )

    return best

def resolveColumns(dataframe, problems):
    """Map raw headers to canonical names, reporting how each was matched.

    Returns (resolvedNames, report) where report is a list of
    (rawName, resolvedName, how).
    """
    rawColumns = list(dataframe.columns)
    resolved = [None] * len(rawColumns)
    report = [None] * len(rawColumns)
    usedCanonical = {}
    unnamedPositions = []

    # Pass one: columns that have a header.
    for position, raw in enumerate(rawColumns):
        rawText = str(raw)

        if PANDAS_DUPLICATE_SUFFIX.search(rawText):
            problems.append(
                f"column {position + 1} ({rawText!r}) looks like a duplicate "
                f"header; pandas renamed it. Check for two columns with the "
                f"same title."
            )

        key = matchKey(rawText)

        if UNNAMED_PATTERN.match(key):
            unnamedPositions.append(position)
            continue

        canonical = ALIAS_LOOKUP.get(key)

        if canonical is None:
            name = legacyClean(rawText)
            resolved[position] = name
            report[position] = (rawText, name, "no canonical name")
            continue

        if canonical in usedCanonical:
            problems.append(
                f"columns {usedCanonical[canonical] + 1} and {position + 1} "
                f"both resolve to {canonical}. Using the first."
            )
            name = legacyClean(rawText) + "_duplicate"
            resolved[position] = name
            report[position] = (rawText, name, f"duplicate of {canonical}")
            continue

        how = "exact" if matchKey(canonical) == key else "alias"
        resolved[position] = canonical
        usedCanonical[canonical] = position
        report[position] = (rawText, canonical, how)

    # Pass two: blank headers, decided on content.
    chosen = None
    if "annualMissionIndex" not in usedCanonical:
        chosen = chooseAnnualMissionIndex(dataframe, unnamedPositions, problems)

    for position in unnamedPositions:
        rawText = str(rawColumns[position])

        if position == chosen:
            resolved[position] = "annualMissionIndex"
            usedCanonical["annualMissionIndex"] = position
            report[position] = (rawText, "annualMissionIndex", "blank header")
        else:
            name = legacyClean(rawText)
            resolved[position] = name
            report[position] = (rawText, name, "blank header, unused")

    return resolved, report

# --- Header row detection --------------------------------------------------

def scoreHeaderRow(path, skiprows):
    """How many headers on this row resolve to a canonical name."""
    try:
        sample = pd.read_excel(path, skiprows=skiprows, nrows=0)
    except Exception:
        return -1, []

    keys = [matchKey(c) for c in sample.columns]
    matched = [ALIAS_LOOKUP[k] for k in keys if k in ALIAS_LOOKUP]
    return len(set(matched)), list(sample.columns)


def detectHeaderRow(path, problems):
    """Pick the header row rather than assuming it, so an inserted row above
    the header does not produce a dataframe of nonsense."""
    scores = {}
    for skiprows in HEADER_SKIPROWS_CANDIDATES:
        score, _ = scoreHeaderRow(path, skiprows)
        scores[skiprows] = score

    best = max(scores, key=lambda k: (scores[k], -HEADER_SKIPROWS_CANDIDATES.index(k)))

    if scores[best] <= 0:
        raise MissionFileError(
            f"Could not find a header row in {path.name}.\n"
            f"Tried skipping {', '.join(map(str, HEADER_SKIPROWS_CANDIDATES))} row(s); "
            f"none produced recognisable column names.\n"
            f"Check that the sheet has not been restructured, and that the first "
            f"sheet in the workbook is the mission table."
        )

    preferred = HEADER_SKIPROWS_CANDIDATES[0]
    if best != preferred:
        problems.append(
            f"header found by skipping {best} row(s), not the usual {preferred}. "
            f"A row may have been added above or removed from the header."
        )

    return best, scores


# --- Value conversion ------------------------------------------------------

def parseDateValue(raw):
    """Parse one cell into a Timestamp, or None if it cannot be read."""
    if pd.isna(raw):
        return None

    if isinstance(raw, pd.Timestamp) or hasattr(raw, "year"):
        return pd.Timestamp(raw).normalize()

    if isinstance(raw, (int, float)):
        number = int(raw)
        if 10_000_000 <= number <= 99_999_999:
            parsed = pd.to_datetime(str(number), format="%Y%m%d", errors="coerce")
            return None if pd.isna(parsed) else parsed
        if EXCEL_SERIAL_MIN <= number <= EXCEL_SERIAL_MAX:
            return pd.Timestamp(EXCEL_EPOCH) + pd.Timedelta(days=number)
        return None

    text = str(raw).strip()
    if not text:
        return None

    digits = re.sub(r"\D", "", text)
    if len(digits) == 8:
        parsed = pd.to_datetime(digits, format="%Y%m%d", errors="coerce")
        if not pd.isna(parsed):
            return parsed

    parsed = pd.to_datetime(text, errors="coerce")
    return None if pd.isna(parsed) else parsed


def excelRow(index, firstDataRow):
    try:
        return int(index) + firstDataRow
    except (TypeError, ValueError):
        return index


def convertDateColumn(series, columnName, problems, firstDataRow):
    converted = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")

    for index, raw in series.items():
        if pd.isna(raw):
            continue

        value = parseDateValue(raw)
        row = excelRow(index, firstDataRow)

        if value is None:
            problems.append(f"row {row}: could not read {columnName} value {raw!r}")
            continue

        if not (MIN_PLAUSIBLE_YEAR <= value.year <= MAX_PLAUSIBLE_YEAR):
            problems.append(
                f"row {row}: {columnName} parsed to {value.date()} from {raw!r}, "
                f"outside the plausible range"
            )
            continue

        converted.at[index] = value

    return converted


def convertNumericColumn(series, columnName, problems, firstDataRow):
    converted = pd.to_numeric(series, errors="coerce")
    failed = converted.isna() & series.notna()

    for index in series.index[failed]:
        problems.append(
            f"row {excelRow(index, firstDataRow)}: {columnName} value "
            f"{series.at[index]!r} is not numeric"
        )
    return converted


def convertIdentifierColumn(series, columnName, problems, firstDataRow):
    """Keep identifiers as text. astype(str) turns a float-typed identifier
    into '12345.0' and a blank cell into the string 'nan'."""
    values = []
    for index, raw in series.items():
        if pd.isna(raw):
            values.append(None)
            continue

        if isinstance(raw, float) and raw.is_integer():
            values.append(str(int(raw)))
        elif isinstance(raw, int):
            values.append(str(raw))
        else:
            text = str(raw).strip()
            if text.lower() in {"", "nan", "none", "n/a", "na", "-"}:
                problems.append(
                    f"row {excelRow(index, firstDataRow)}: {columnName} contains "
                    f"placeholder text {raw!r}, treated as blank"
                )
                values.append(None)
            else:
                values.append(text)

    return pd.Series(values, index=series.index, dtype=object)


# --- Validation ------------------------------------------------------------

def checkLastRowComplete(dataframe, problems, firstDataRow):
    """The final row is the mission being processed; it should be filled in."""
    if dataframe.empty:
        problems.append("no mission rows found after cleaning")
        return

    lastIndex = dataframe.index[-1]
    row = dataframe.loc[lastIndex]
    blanks = [column for column in dataframe.columns if pd.isna(row[column])]

    if blanks:
        problems.append(
            f"row {excelRow(lastIndex, firstDataRow)} (the newest mission) has "
            f"{len(blanks)} blank field(s): {', '.join(blanks[:12])}"
            + (" ..." if len(blanks) > 12 else "")
        )


def checkDateOrder(dataframe, problems, firstDataRow):
    if not {"Deploymentdate", "Recoverydate"}.issubset(dataframe.columns):
        return

    both = dataframe["Deploymentdate"].notna() & dataframe["Recoverydate"].notna()
    reversed_ = both & (dataframe["Recoverydate"] < dataframe["Deploymentdate"])

    for index in dataframe.index[reversed_]:
        problems.append(
            f"row {excelRow(index, firstDataRow)}: recovery "
            f"{dataframe.at[index, 'Recoverydate'].date()} precedes deployment "
            f"{dataframe.at[index, 'Deploymentdate'].date()}"
        )


# --- Locating the file -----------------------------------------------------

def findProjectRoot():
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "manage.py").exists():
            return candidate
    raise MissionFileError(
        "Could not locate manage.py. This module must live inside the repository."
    )


def resolveSpreadsheetPath(path=None):
    if path is not None:
        resolved = Path(path).expanduser().resolve()
        if not resolved.exists():
            raise MissionFileError(f"Spreadsheet not found: {resolved}")
        return resolved

    directory = findProjectRoot() / SPREADSHEET_DIR
    if not directory.is_dir():
        raise MissionFileError(f"Directory not found: {directory}")

    existing = [directory / name for name in SPREADSHEET_NAMES]
    existing = [c for c in existing if c.exists()]

    if not existing:
        listing = sorted(p.name for p in directory.glob("*.xlsx"))
        raise MissionFileError(
            f"No spreadsheet found in {directory}.\n"
            f"Expected one of: {', '.join(SPREADSHEET_NAMES)}\n"
            f"Found: {', '.join(listing) if listing else '(no .xlsx files)'}"
        )

    if len(existing) > 1:
        newest = max(existing, key=lambda p: p.stat().st_mtime)
        print(
            f"WARNING: more than one spreadsheet present "
            f"({', '.join(p.name for p in existing)}). Using the most recently "
            f"modified: {newest.name}",
            file=sys.stderr,
        )
        return newest

    return existing[0]


# --- Entry point -----------------------------------------------------------

def readMissionFile(path=None, strict=False, verbose=True, returnReport=False):
    """Read the mission spreadsheet into a cleaned dataframe.

    Parameters
    ----------
    path : str or Path, optional
        Spreadsheet to read. Defaults to the one in initializationData/.
    strict : bool
        Raise MissionFileError if any problem was found. Use in a --dry-run
        check before writing to the database.
    verbose : bool
        Print warnings to stderr.
    returnReport : bool
        Return (dataframe, report) instead of just the dataframe, where report
        lists how each header was matched.

    Returns
    -------
    pandas.DataFrame
        One row per mission, in spreadsheet order. The last row is the
        newest mission.
    """
    resolved = resolveSpreadsheetPath(path)
    problems = []

    skiprows, _ = detectHeaderRow(resolved, problems)
    firstDataRow = skiprows + 2

    try:
        dataframe = pd.read_excel(resolved, skiprows=skiprows)
    except Exception as exc:
        raise MissionFileError(f"Could not read {resolved}: {exc}") from exc

    rawColumns = list(dataframe.columns)
    resolvedNames, report = resolveColumns(dataframe, problems)
    dataframe.columns = resolvedNames
    
    missingRequired = [c for c in REQUIRED_COLUMNS if c not in dataframe.columns]
    if missingRequired:
        headerList = "\n  ".join(f"{raw!r} -> {name}" for raw, name, _ in report)
        raise MissionFileError(
            f"{resolved.name} is missing required column(s): "
            f"{', '.join(missingRequired)}.\n\n"
            f"Headers found (skipping {skiprows} row(s)):\n  {headerList}\n\n"
            f"If one of these is the column you expect, add its spelling to "
            f"COLUMN_ALIASES in this file."
        )

    rowsRead = len(dataframe)
    dataframe = dataframe.dropna(subset=list(REQUIRED_COLUMNS))
    rowsKept = len(dataframe)

    if rowsKept == 0:
        raise MissionFileError(
            f"{resolved.name} has no usable rows. Every row was missing "
            f"{' or '.join(REQUIRED_COLUMNS)}."
        )

    for column in DATE_COLUMNS:
        if column in dataframe.columns:
            dataframe[column] = convertDateColumn(
                dataframe[column], column, problems, firstDataRow
            )
        elif column not in EXPECTED_OPTIONAL:
            problems.append(f"date column {column} is absent")

    for column in NUMERIC_COLUMNS:
        if column in dataframe.columns:
            dataframe[column] = convertNumericColumn(
                dataframe[column], column, problems, firstDataRow
            )
        elif column not in EXPECTED_OPTIONAL:
            problems.append(f"numeric column {column} is absent")

    for column in IDENTIFIER_COLUMNS:
        if column in dataframe.columns:
            dataframe[column] = convertIdentifierColumn(
                dataframe[column], column, problems, firstDataRow
            )
        elif column not in EXPECTED_OPTIONAL:
            problems.append(f"identifier column {column} is absent")

    lostToParsing = dataframe["Deploymentdate"].isna()
    if lostToParsing.any():
        for index in dataframe.index[lostToParsing]:
            problems.append(
                f"row {excelRow(index, firstDataRow)}: dropped, deployment date "
                f"could not be read"
            )
        dataframe = dataframe[~lostToParsing]

    checkDateOrder(dataframe, problems, firstDataRow)
    checkLastRowComplete(dataframe, problems, firstDataRow)

    if problems:
        message = (
            f"{len(problems)} issue(s) reading {resolved.name}:\n  "
            + "\n  ".join(problems)
        )
        if strict:
            raise MissionFileError(message)
        if verbose:
            print(f"WARNING: {message}", file=sys.stderr)

    if verbose:
        aliased = sum(1 for _, _, how in report if how == "alias")
        unmatched = sum(1 for _, _, how in report if how == "no canonical name")
        print(
            f"Read {resolved.name}: {rowsKept} mission row(s) from {rowsRead} "
            f"spreadsheet row(s); {aliased} header(s) matched by alias, "
            f"{unmatched} not recognised, {len(problems)} issue(s)."
        )

    if returnReport:
        return dataframe, report
    return dataframe


def convert_date(date):
    """Deprecated. Kept for scripts still importing the old helper."""
    return date.apply(lambda d: parseDateValue(d) or pd.NaT)


# --- Diagnostic ------------------------------------------------------------

def main():
    try:
        dataframe, report = readMissionFile(returnReport=True)
    except MissionFileError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    print("\nHeader matching:")
    for raw, name, how in report:
        marker = {"exact": "  ", "alias": "~ ", "blank header": "? "}.get(how, "! ")
        print(f"  {marker}{raw!r:<40} -> {name:<32} ({how})")

    print("\n  ~ matched by alias    ? blank header    ! not recognised")

    print(f"\nColumns ({len(dataframe.columns)}):")
    for column in dataframe.columns:
        populated = dataframe[column].notna().sum()
        print(f"  {column:<40} {populated:>4}/{len(dataframe)} populated")

    if not dataframe.empty:
        last = dataframe.iloc[-1]
        print("\nNewest mission:")
        for column in dataframe.columns:
            if pd.notna(last[column]):
                print(f"  {column:<40} {last[column]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())