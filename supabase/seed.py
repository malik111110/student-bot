"""Small seed runner that calls database RPC functions to import real data.

This script intentionally does NOT embed data into migrations. It reads
`data/professors.json`, `data/programs.json` and `data/students.json` and
calls the SQL functions defined in migrations/0002_seed_functions.sql.

Usage: set SUPABASE_URL and SUPABASE_KEY in your environment and run:

To preview what would be imported (dry run):
    python supabase/seed.py --dry-run

To run the actual import:
    python supabase/seed.py
"""

from __future__ import annotations

import json
import os
import unicodedata
from typing import Any, Dict

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from supabase import create_client


def load_field_map() -> Dict[str, str]:
    mapping_file = os.path.join(os.path.dirname(__file__), "field_mapping.json")
    try:
        with open(mapping_file, "r", encoding="utf-8") as mf:
            return json.load(mf)
    except Exception:
        # minimal fallback
        return {
            "RSD": "NDS",
            "Resin": "NIS",
            "Intelligence Artificielle": "AI",
            "Sciences des Données": "DATASCI",
            "Sécurité informatique": "INFOSEC",
        }


def load_modules_map() -> Dict[str, str]:
    mapping_file = os.path.join(os.path.dirname(__file__), "modules_map.json")
    try:
        with open(mapping_file, "r", encoding="utf-8") as mf:
            raw = json.load(mf)
        # normalize keys for robust lookup (lowercased, stripped)
        return {k.strip().lower(): v for k, v in raw.items()}
    except Exception:
        return {}


def normalize_text_for_lookup(s: str) -> str:
    if not s:
        return ""
    # Unicode normalize and collapse whitespace
    s = unicodedata.normalize("NFKC", s)
    s = " ".join(s.split())
    return s.strip().lower()


def resolve_field_code(raw_field: str, field_map: Dict[str, str]) -> str:
    if not raw_field:
        return ""
    raw_field = raw_field.strip()
    key = raw_field.lower().replace("-", " ").replace("_", " ")
    # Try exact match first, then normalized lower-case key, then title-case fallback
    return (
        field_map.get(raw_field)
        or field_map.get(key)
        or field_map.get(raw_field.title())
        or raw_field
    )


def get_programs_table_columns(migration_sql_path: str) -> set:
    """Parse the migration SQL and return a set of column names for the `programs` table.
    This is a lightweight parser that looks for `CREATE TABLE programs` and extracts the column
    identifiers before the closing parenthesis.
    """
    try:
        with open(migration_sql_path, "r", encoding="utf-8") as f:
            sql = f.read()
    except Exception:
        return set()

    marker = "create table programs"
    lower = sql.lower()
    idx = lower.find(marker)
    if idx == -1:
        return set()
    # find opening parenthesis after marker
    start = lower.find("(", idx)
    if start == -1:
        return set()
    end = lower.find(");", start)
    if end == -1:
        # try closing ')'
        end = lower.find(")", start)
        if end == -1:
            return set()
    block = sql[start + 1 : end]
    cols = set()
    for line in block.splitlines():
        line = line.strip()
        if not line or line.startswith("--"):
            continue
        # column lines usually start with "name type"
        parts = line.split()
        if not parts:
            continue
        col = parts[0].strip('"` ,')
        # skip table constraints
        if col.lower() in ("constraint", "primary", "unique", "foreign"):
            continue
        cols.add(col)
    return cols


def validate_programs_against_migration(
    programs, migration_sql_path: str
) -> Dict[str, Dict[str, set]]:
    """Return a dict mapping program code -> {missing_keys: set, extra_keys: set} compared to migration columns.
    Does not modify data; only inspects shapes.
    """
    cols = get_programs_table_columns(migration_sql_path)
    results = {}
    for p in programs if isinstance(programs, list) else []:
        keys = set(p.keys())
        # remove nested JSON fields we expect to be stored in a single JSONB column (e.g. curriculum)
        # keep this conservative: assume columns in SQL are direct columns
        missing = cols - keys
        extra = keys - cols
        results[p.get("name") or p.get("title") or str(p.get("code") or "")] = {
            "missing_keys": missing,
            "extra_keys": extra,
        }
    return results


def validate_students_structure(students) -> Dict[str, int]:
    """Basic quick-checks on the students JSON: counts missing core fields.
    Returns a dict with counters for missing fields.
    """
    counters = {"total": 0, "missing_id": 0, "missing_name": 0, "missing_field": 0}
    for s in students:
        counters["total"] += 1
        if not s.get("id"):
            counters["missing_id"] += 1
        if not s.get("complete_name"):
            counters["missing_name"] += 1
        if not s.get("field"):
            counters["missing_field"] += 1
    return counters


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def import_students(client, students, *, dry_run=False):
    # prepare normalized payload: student_number, first_name, last_name, email, field_code
    payload = []
    # Load mapping from file (editable) or fallback
    field_map = load_field_map()
    modules_map = load_modules_map()

    for s in students:
        # try to split complete_name
        name = s.get("complete_name", "").strip()
        parts = name.split()
        first = parts[0] if parts else ""
        last = " ".join(parts[1:]) if len(parts) > 1 else ""
        raw_field = (s.get("field") or "").strip()
        # apply modules_map normalize -> helpful when 'field' uses accented names
        normalized_field = normalize_text_for_lookup(raw_field)
        canonical_field = modules_map.get(normalized_field) or raw_field
        field_code = resolve_field_code(canonical_field, field_map)
        payload.append(
            {
                "student_number": s.get("id"),
                "first_name": first,
                "last_name": last,
                "email": s.get("email"),
                "field_code": field_code,
            }
        )

    if dry_run:
        print(f"[DRY RUN] Would call rpc_import_students with {len(payload)} records")
        print("Sample payload (first 2 records):")
        import json

        for i, p in enumerate(payload[:2]):
            print(f"{i+1}.", json.dumps(p, indent=2))
        if len(payload) > 2:
            print(f"... and {len(payload)-2} more records")
        return payload

    resp = client.postgrest.rpc("rpc_import_students", payload).execute()
    return resp


def import_professors(client, professors, *, dry_run=False):
    results = []
    for p in professors:
        name = p.get("name", "")
        parts = name.split()
        first = parts[0] if parts else ""
        last = " ".join(parts[1:]) if len(parts) > 1 else ""
        email = p.get("email")
        payload = {"0": first, "1": last, "2": email}

        if dry_run:
            print(f"[DRY RUN] Would call insert_or_get_professor with:")
            print(json.dumps(payload, indent=2))
            results.append(payload)
            continue

        resp = client.postgrest.rpc("insert_or_get_professor", payload).execute()
        results.append(resp)
    return results


def import_programs(client, programs_json, *, dry_run=False):
    # Accepts either a dict with 'programs' key or a list
    programs = (
        programs_json.get("programs")
        if isinstance(programs_json, dict) and "programs" in programs_json
        else programs_json
    )
    results = []
    modules_map = load_modules_map()

    def canonicalize_program_payload(program: dict) -> dict:
        # Recursively canonicalize strings in the program structure for known keys
        out = {}
        for k, v in program.items():
            if isinstance(v, str):
                key = normalize_text_for_lookup(v)
                out[k] = modules_map.get(key) or v
            elif isinstance(v, list):
                out[k] = []
                for item in v:
                    if isinstance(item, dict):
                        out[k].append(canonicalize_program_payload(item))
                    elif isinstance(item, str):
                        key = normalize_text_for_lookup(item)
                        out[k].append(modules_map.get(key) or item)
                    else:
                        out[k].append(item)
            elif isinstance(v, dict):
                out[k] = canonicalize_program_payload(v)
            else:
                out[k] = v
        return out

    for p in programs:
        canon = canonicalize_program_payload(p)
        code = (
            (canon.get("name") or canon.get("title") or "PROGRAM")
            .upper()
            .replace(" ", "_")[:64]
        )
        payload = [code, canon]

        if dry_run:
            print(f"[DRY RUN] Would call insert_program with code={code}:")
            print(json.dumps(payload[1], indent=2))
            results.append(payload)
            continue

        resp = client.postgrest.rpc("insert_program", payload).execute()
        results.append(resp)
    return results


def validate_file(name: str, path: str, validate_fn=None) -> tuple[bool, Any]:
    """Validate a JSON file exists and optionally apply a validation function.
    Returns (success, data) tuple where data is None if validation fails.
    """
    if not os.path.exists(path):
        print(f"Warning: {name} file not found at {path}")
        return False, None

    try:
        data = load_json(path)
    except Exception as e:
        print(f"Error: Failed to parse {name} JSON from {path}:", str(e))
        return False, None

    if validate_fn:
        try:
            result = validate_fn(data)
            if isinstance(result, dict) and result.get("error"):
                print(f"Error validating {name}:", result["error"])
                return False, None
        except Exception as e:
            print(f"Error validating {name}:", str(e))
            return False, None

    return True, data


def validate_students_json(students) -> dict:
    stats = validate_students_structure(students)
    if (
        stats["missing_id"] > 0
        or stats["missing_name"] > 0
        or stats["missing_field"] > 0
    ):
        return {
            "error": (
                f"Found {stats['missing_id']} students missing ID, "
                f"{stats['missing_name']} missing name, "
                f"{stats['missing_field']} missing field"
            )
        }
    return {"stats": stats}


def main(dry_run=False):
    # Get Supabase credentials from environment
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_KEY environment variables must be set")
        sys.exit(1)

    client = create_client(url, key)
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    students_path = os.path.join(base, "students.json")
    professors_path = os.path.join(base, "professors.json")
    programs_path = os.path.join(base, "programs.json")

    # Run all validations first
    print("Validating input files...")
    valid = True

    ok, students = validate_file("students", students_path, validate_students_json)
    valid = valid and ok

    ok, professors = validate_file("professors", professors_path)
    valid = valid and ok

    ok, programs = validate_file("programs", programs_path)
    if ok and programs:
        # Check programs against migration schema
        migration = os.path.join(
            os.path.dirname(__file__), "migrations", "0001_create_tables.sql"
        )
        if os.path.exists(migration):
            results = validate_programs_against_migration(programs, migration)
            has_errors = False
            for name, validation in results.items():
                if validation["missing_keys"] or validation["extra_keys"]:
                    has_errors = True
                    print(f"\nProgram '{name}' has schema mismatches:")
                    if validation["missing_keys"]:
                        print(
                            "  Missing required columns:",
                            ", ".join(validation["missing_keys"]),
                        )
                    if validation["extra_keys"]:
                        print(
                            "  Extra fields that won't be stored:",
                            ", ".join(validation["extra_keys"]),
                        )
            if has_errors:
                ok = False
                print("\nProgram schema validation failed. Review the issues above.")
    valid = valid and ok

    if not valid:
        print("\nValidation failed. Fix the issues above before proceeding.")
        sys.exit(1)

    print("All validations passed.\n")

    if os.path.exists(students_path):
        students = load_json(students_path)
        print("Importing students..." if not dry_run else "[DRY RUN] Students:")
        r = import_students(client, students, dry_run=dry_run)
        if not dry_run:
            print("Students import finished:", r)
    else:
        print("No students.json found at", students_path)

    if os.path.exists(professors_path):
        professors = load_json(professors_path)
        print("Importing professors..." if not dry_run else "[DRY RUN] Professors:")
        r = import_professors(client, professors, dry_run=dry_run)
        if not dry_run:
            print("Professors import finished")
    else:
        print("No professors.json found at", professors_path)

    if os.path.exists(programs_path):
        programs = load_json(programs_path)
        print("Importing programs..." if not dry_run else "[DRY RUN] Programs:")
        r = import_programs(client, programs, dry_run=dry_run)
        if not dry_run:
            print("Programs import finished")
    else:
        print("No programs.json found at", programs_path)


if __name__ == "__main__":
    import sys

    dry_run = "--dry-run" in sys.argv
    main(dry_run=dry_run)
