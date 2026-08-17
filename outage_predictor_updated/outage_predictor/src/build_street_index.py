"""
Build an expanded, searchable street/area index from the real NERC/DisCo
Band classification data (discos_band_classification.csv).

Why this exists
----------------
The original street_grid_registry.csv is a small hand-built seed (104
streets) used to drive the app's Step 1 location search. But the real
Band dataset already collected for Step 3 (2,679 feeder records across
all 11 DisCos) has actual served-community/street names embedded in its
free-text `feeder_description` field for every single row -- e.g.:

    "IKEJA ISAAC JOHN ROAD, LADOKE AKINTOLA STREET, OBA DOSUMU STREET..."

This script parses those free-text fields into individual street/area
names and produces a much larger index (expanded_street_index.csv) that
the app can search against -- while carrying the *exact* Band, minimum
supply hours, and source citation for each parsed street directly from
the row it came from (so Step 3 doesn't need to re-guess a match; it
already knows it).

This is real regulatory text, not a clean address database, so the
parser is a heuristic, not a perfect NLP pipeline: it strips obvious
feeder/substation/voltage jargon, splits on common list delimiters, and
filters short/junk tokens. Expect some noise (duplicated fragments,
the odd non-street token) -- documented as a known limitation, same as
any real-world OCR'd regulatory filing would have. It is still a large,
genuine improvement over a 104-row seed list.

Run:
    python src/build_street_index.py

Output:
    data/processed/expanded_street_index.csv
    (also copied to app/data/expanded_street_index.csv for the app to load)
"""

import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SRC_CSV = ROOT / "data" / "processed" / "discos_band_classification.csv"
OUT_PROCESSED = ROOT / "data" / "processed" / "expanded_street_index.csv"
OUT_APP = ROOT / "app" / "data" / "expanded_street_index.csv"

# DisCo id (as used by the trained model / app) -> primary state, taken
# from the existing seed registry so state filtering stays consistent.
DISCO_PRIMARY_STATE = {
    "Abuja": "FCT",
    "Benin": "Edo",
    "Eko": "Lagos",
    "Enugu": "Enugu",
    "Ibadan": "Oyo",
    "Ikeja": "Lagos",
    "Jos": "Plateau",
    "Kaduna": "Kaduna",
    "Kano": "Kano",
    "Port Harcourt": "Rivers",
    "Yola": "Adamawa",
}

# Technical/feeder jargon to strip before splitting into candidate
# street/area names. Order matters: run before delimiter splitting.
JARGON_PATTERNS = [
    r"\b\d+(\.\d+)?\s*/?\s*\d*\s*KV\b",       # 132KV, 33/11KV, 11kV
    r"\b\d+\s*X\s*\d+(\.\d+)?\s*MVA\b",       # 1X15MVA, 2X7.5MVA
    r"\bMVA\b", r"\bKVA\b",
    r"\bT/?S\b",                               # TS, T/S
    r"\bFDR\b", r"\bFEEDER\b",
    r"\bISS\b",                                # injection sub-station shorthand
    r"\bGCM\b",
    r"\bS/S\b", r"\bSUBSTATION\b",
    r"\bINJECTION\b",
    r"\bNOT ACTIVE\b",
    r"_",
]

# Suffix words that commonly glue two concatenated street names together
# with no delimiter, e.g. "ADELEBU STREETADELEBU STREET" -- insert a
# split point right after the suffix when it's immediately followed by
# another capital letter with no space.
STREET_SUFFIXES = [
    "STREET", "ROAD", "AVENUE", "CRESCENT", "CLOSE", "WAY", "DRIVE",
    "LANE", "ROUNDABOUT", "ESTATE", "LAYOUT", "EXPRESSWAY", "EXPRESS WAY",
]
SUFFIX_GLUE_RE = re.compile(
    r"(" + "|".join(STREET_SUFFIXES) + r")(?=[A-Z])"
)

DELIM_RE = re.compile(r",|;|/| AND | & |\.(?=\s|$)")

DROP_TOKENS = {
    "AND", "THE", "OF", "AREA", "ENVIRONS", "TOWN", "COMMUNITY",
    "COMMUNITIES", "PART", "ALL", "BACK", "BEHIND", "ALONG",
    "POLY", "GOVT", "ESTATE", "LAYOUT", "NONAME", "NO NAME",
}


def clean_jargon(text: str) -> str:
    t = text.upper()
    for pat in JARGON_PATTERNS:
        t = re.sub(pat, " ", t, flags=re.IGNORECASE)
    return t


def split_candidates(text: str):
    # First insert boundaries at glued street-suffix repeats.
    t = SUFFIX_GLUE_RE.sub(r"\1|", text)
    # Then split on normal list delimiters.
    parts = re.split(r"\||" + DELIM_RE.pattern, t)
    return parts


def is_valid_token(tok: str) -> bool:
    tok = tok.strip()
    if len(tok) < 4:
        return False
    if tok.upper() in DROP_TOKENS:
        return False
    if re.fullmatch(r"[\d\W]+", tok):        # pure digits/punctuation
        return False
    if re.fullmatch(r"[A-Z]{1,3}\d+", tok):   # leftover codes like "FD8", "K4"
        return False
    if LEFTOVER_UNIT_RE.match(tok.strip()):    # leftover "15MVA" fragments
        return False
    # Reject un-split run-on fragments: the splitter didn't fully
    # separate these into individual street names, so they read as
    # garbled feeder-code trails rather than a place name. Better to
    # drop them from the searchable index than show them to a user.
    if len(tok) > 45:                                   # too long to be a street name
        return False
    if len(tok.split()) > 6:                            # too many words = run-on
        return False
    if re.search(r"\bT\d\b|\bLOCAL\b.*\bLOCAL\b", tok.upper()):  # leftover feeder-topology jargon
        return False
    if re.search(r"^\d+[- ]|[- ]\d+[A-Z]{2,}\b", tok):   # numeric-prefixed feeder-code trails
        return False
    letters = sum(c.isalpha() for c in tok)
    if letters < 3:
        return False
    return True


def normalize(tok: str) -> str:
    tok = re.sub(r"\s+", " ", tok).strip(" ,.-")
    # Collapse immediate repeated words, e.g. "YAHE YAHE YAHE" -> "YAHE"
    # (a common artifact of the source text's own duplication).
    words = tok.split(" ")
    deduped = [w for i, w in enumerate(words) if i == 0 or w != words[i - 1]]
    tok = " ".join(deduped)
    return tok.title()


LEFTOVER_UNIT_RE = re.compile(r"^\d+\s*MVA$", re.IGNORECASE)


def parse_feeder_description(desc: str):
    cleaned = clean_jargon(desc)
    raw_parts = split_candidates(cleaned)
    seen = set()
    out = []
    for p in raw_parts:
        p = p.strip(" ,.-")
        if not is_valid_token(p):
            continue
        norm = normalize(p)
        key = norm.upper()
        if key in seen:
            continue
        seen.add(key)
        out.append(norm)
    return out


def main():
    df = pd.read_csv(SRC_CSV)
    # Normalize DisCo id: strip qualifiers like " (tentative)" so it
    # matches the model's DISCOS naming exactly.
    df["disco_id_clean"] = df["DisCo"].str.replace(
        r"\s*\(tentative\)\s*$", "", regex=True
    ).str.strip()

    rows = []
    for _, r in df.iterrows():
        disco = r["disco_id_clean"]
        state = DISCO_PRIMARY_STATE.get(disco, "")
        streets = parse_feeder_description(str(r["feeder_description"]))
        for s in streets:
            rows.append({
                "street_name": s,
                "area_neighborhood": disco,   # no finer area name available; DisCo territory shown
                "lga": "",
                "state": state,
                "disco_id": disco,
                "service_band": r["band"],
                "min_supply_hours": r["min_supply_hours"],
                "confidence": "verified (NERC/DisCo real data)",
                "source_report": r["source_report"],
                "feeder_description": r["feeder_description"],
                "verification_note": r.get("verification_note", ""),
            })

    out = pd.DataFrame(rows)
    before = len(out)
    out = out.drop_duplicates(subset=["disco_id", "street_name"]).reset_index(drop=True)
    after = len(out)

    OUT_PROCESSED.parent.mkdir(parents=True, exist_ok=True)
    OUT_APP.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_PROCESSED, index=False)
    out.to_csv(OUT_APP, index=False)

    print(f"Parsed {len(df)} feeder records -> {before} candidate streets, "
          f"{after} unique (disco, street) pairs.")
    print(f"Written to:\n  {OUT_PROCESSED}\n  {OUT_APP}")
    print()
    print(out["disco_id"].value_counts())


if __name__ == "__main__":
    main()
