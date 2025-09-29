import importlib.util
import json
import sys
import types
from pathlib import Path


def load_seed_module():
    repo_root = Path(__file__).parents[2]
    seed_path = repo_root / "supabase" / "seed.py"
    # inject a fake supabase.client module so seed.py can import get_client without
    # pulling the installed `supabase` package from site-packages
    fake_client = types.ModuleType("supabase.client")

    def dummy_get_client():
        class Dummy:
            postgrest = types.SimpleNamespace(
                rpc=lambda *a, **k: types.SimpleNamespace(execute=lambda: None)
            )

        return Dummy()

    fake_client.get_client = dummy_get_client
    # ensure package module exists too
    if "supabase" not in sys.modules:
        sys.modules["supabase"] = types.ModuleType("supabase")
    sys.modules["supabase.client"] = fake_client

    spec = importlib.util.spec_from_file_location("proj_seed", seed_path)
    seed = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(seed)

    # cleanup inserted modules to avoid side effects in other tests
    try:
        del sys.modules["supabase.client"]
    except KeyError:
        pass
    # leave 'supabase' package module if it existed before
    return seed, seed_path.parent


def test_load_field_map_file_present():
    seed, seed_dir = load_seed_module()
    mapping = {"Resin": "NIS", "RSD": "NDS", "Sécurité informatique": "INFOSEC"}
    map_file = seed_dir / "field_mapping.json"
    # backup existing file if present
    backup = None
    if map_file.exists():
        backup = map_file.read_text(encoding="utf-8")
    try:
        map_file.write_text(json.dumps(mapping), encoding="utf-8")
        loaded = seed.load_field_map()
        assert loaded.get("Resin") == "NIS"
        assert loaded.get("RSD") == "NDS"
    finally:
        if backup is None:
            try:
                map_file.unlink()
            except Exception:
                pass
        else:
            map_file.write_text(backup, encoding="utf-8")


def test_resolve_field_code_variants():
    seed, _ = load_seed_module()
    fm = {
        "RSD": "NDS",
        "Resin": "NIS",
        "Intelligence Artificielle": "AI",
        "Sciences des Données": "DATASCI",
    }
    assert seed.resolve_field_code("RSD", fm) == "NDS"
    # lower-case variant should fall back to provided mapping via title or raw fallback
    out = seed.resolve_field_code("resin", fm)
    assert out in ("NIS", "resin")
    assert seed.resolve_field_code("Intelligence Artificielle", fm) == "AI"


def test_validate_students_structure():
    seed, _ = load_seed_module()
    students = [
        {"id": "s1", "complete_name": "Alice Doe", "field": "RSD"},
        {"id": "", "complete_name": "", "field": ""},
    ]
    stats = seed.validate_students_structure(students)
    assert stats["total"] == 2
    assert stats["missing_id"] == 1
    assert stats["missing_name"] == 1
    assert stats["missing_field"] == 1


def test_validate_programs_against_migration():
    seed, seed_dir = load_seed_module()
    repo_root = Path(__file__).parents[2]
    migration_path = repo_root / "tests" / "fixtures" / "sample_migration.sql"

    # test with a program missing required columns
    programs = [
        {
            "name": "Test Program",
            "extra_field": "should flag",
        },  # missing code, has extra
        {
            "code": "TEST",
            "name": "Complete",
            "description": "OK",
            "department": "CS",
        },  # matches schema
    ]

    results = seed.validate_programs_against_migration(programs, migration_path)
    assert len(results) == 2

    # program with missing and extra fields
    prog1 = results["Test Program"]
    assert "code" in prog1["missing_keys"]
    assert "extra_field" in prog1["extra_keys"]

    # program that matches schema (except auto fields like id, timestamps)
    prog2 = results["Complete"]
    required_present = {"code", "name", "description", "department"}
    assert not (required_present & prog2["missing_keys"])  # no missing required fields
    assert not prog2["extra_keys"]  # no extra fields
