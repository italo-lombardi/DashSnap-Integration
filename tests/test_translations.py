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


def _flatten_values(obj: object, prefix: str = "") -> dict[str, str]:
    """Return {dotted key path: value} for all leaf strings in a nested dict."""
    out: dict[str, str] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(_flatten_values(v, f"{prefix}.{k}" if prefix else k))
    elif isinstance(obj, str):
        out[prefix] = obj
    return out


# Leaf values that are legitimately identical to English in every language
# (brand names, proper nouns), excluded from the English-match ratio below.
# Add a key here only when the English text is genuinely untranslatable, never
# to silence a real missing translation.
_ALLOWED_UNTRANSLATED = {
    "config.step.user.title",  # "DashSnap"
    "options.step.init.title",  # "DashSnap"
}

# A real translation file matches English on only a few cognates. The measured
# max across all files is 6.4% (3/47); a wholesale English paste (PR #40) is
# 100%. 50% sits far above the noise and below any paste, so it flags a pasted
# file without tripping on legitimate cognates.
_MAX_ENGLISH_RATIO = 0.5


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


def test_no_file_is_mostly_english() -> None:
    """Catch an untranslated paste per file via its English-match ratio.

    PR #40 pasted the English `lang` strings into the non-English files. A real
    translation matches English on only a handful of cognates (measured max
    6.4%); a pasted file matches ~100%. Any file above _MAX_ENGLISH_RATIO is an
    untranslated paste. This is per file, so it catches a partial paste (one
    file), not just the all-files case. Brand names are excluded via
    _ALLOWED_UNTRANSLATED. A missing key reads as None != en_val, so absence is
    covered by test_all_translations_have_en_keys, not this test.
    """
    with (TRANSLATIONS_DIR / "en.json").open(encoding="utf-8") as f:
        en = _flatten_values(json.load(f))
    keys = [k for k in en if k not in _ALLOWED_UNTRANSLATED]

    offenders: dict[str, float] = {}
    for path in sorted(TRANSLATIONS_DIR.glob("*.json")):
        if path.name == "en.json":
            continue
        with path.open(encoding="utf-8") as f:
            vals = _flatten_values(json.load(f))
        ratio = sum(vals.get(k) == en[k] for k in keys) / len(keys)
        if ratio > _MAX_ENGLISH_RATIO:
            offenders[path.name] = ratio

    assert not offenders, (
        "Translation files that are mostly untranslated English "
        f"(> {_MAX_ENGLISH_RATIO:.0%} match):\n"
        + "\n".join(f"  {name}: {ratio:.0%}" for name, ratio in offenders.items())
    )
