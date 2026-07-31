"""Tests for translation completeness — every translation file must have all keys from en.json."""

from __future__ import annotations

import json
from pathlib import Path

TRANSLATIONS_DIR = Path(__file__).parent.parent / "custom_components" / "dashsnap" / "translations"


def _flatten(obj: object, prefix: str = "") -> set[str]:
    """Return dotted key paths for all leaf strings in a nested dict."""
    keys: set[str] = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            keys |= _flatten(v, f"{prefix}.{k}" if prefix else k)
    return keys


def test_all_translation_files_are_valid_json() -> None:
    for path in sorted(TRANSLATIONS_DIR.glob("*.json")):
        with path.open(encoding="utf-8") as f:
            json.load(f)  # raises on invalid JSON


def test_all_translations_have_en_keys() -> None:
    en_path = TRANSLATIONS_DIR / "en.json"
    with en_path.open(encoding="utf-8") as f:
        en_keys = _flatten(json.load(f))

    missing: dict[str, list[str]] = {}
    for path in sorted(TRANSLATIONS_DIR.glob("*.json")):
        if path.name == "en.json":
            continue
        with path.open(encoding="utf-8") as f:
            lang_keys = _flatten(json.load(f))
        absent = sorted(en_keys - lang_keys)
        if absent:
            missing[path.name] = absent

    assert not missing, "Translation files missing keys from en.json:\n" + "\n".join(
        f"  {lang}: {keys}" for lang, keys in missing.items()
    )
