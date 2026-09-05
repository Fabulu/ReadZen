#!/usr/bin/env python3
"""SPEC_R2_20260903.md §1-2: the external-review correction engine (lane R2).

Input is the CLONE pre-state at pinned HEAD 145b090 (the R1c commit;
confinement law: engine(clone) == terms bytes after apply, asserted
before writing). CLONE may be re-pointed via the R2_CLONE_DIR env to a
detached worktree of the pin commit (archive-bundle post-commit re-run;
the pin/clean assertions then hold there — default unchanged). Like R1c the lane is AUTHORED — every new attribution
note, actor block, and prose replacement is a SPEC-frozen constant
verified against local authorities by probe_r2_design_facts_20260903.py
and probe_r2_semantics_20260903.py:

  registry: T48n2025 DetailedClass "institutional regulation
  compilation", ReviewNeeded true; corpus TEI header 元 德煇重編;
  roster: "Dehui" is not a roster name, "Dongyang Dehui" is, and
  t_3f7a6ab74b68 is the in-house precedent for exactly this person and
  work (MasterName null + ContextMasters [{"Dongyang Dehui",
  ["compiler"]}] + impersonal ActorAttribution). Status "impersonal"
  (not "narrated") because 坐禪 matches
  NARRATED_PHYSICAL_ACTION_HEADWORD_RE and the governed-performer law
  must not be triggered; audit_attribution exception_named accepts the
  label-verbatim branch (lines 1038-1039) and the roster scan
  (roster_names() only, whole-note fail-closed) sees no unrepresented
  name in the frozen notes.

  per entry (SPEC §1) —
    - occ-attribution (ea2 slots 1/8/9): carry-over-with-overwrite —
      RelPath/FromLb/ToLb/Kwic/Curated/HeadwordSpanReview are carried
      byte-identically; MasterName -> null; ContextMasters -> the
      precedent compiler block; ActorAttribution appended (frozen);
      AttributionNote replaced (frozen; the pre notes are asserted
      byte-exactly first). Slot 8's note also repairs its duplicated
      English title defect in passing (same field, same edit class).
    - prose rewrites: find-once laws (ea2 Explanation Dehui sentence;
      057 Note "own record" sentence; 057 occurrence 3 AttributionNote
      compiler insertion).
    - relatedmasters-rename (ea2): "Dehui" -> "Dongyang Dehui" in place.
    - searchaliases-add (968): append "一不成、二不是" to the frozen
      single-element list.

  Post-state laws asserted before any output is accepted:
    - fleet census: the T48n2025+"Dehui" defect is exactly the frozen
      census (3 ea2 + 2 follow-up-lane rows untouched by this lane);
    - no retired rel anywhere fleet-wide (Occurrences/ClaimAnchors/
      SourceTexts); sense and per-sense occurrence counts unchanged;
    - attribution-convention law: the 3 repaired rows carry MasterName
      null, the frozen ContextMasters/ActorAttribution, ActorLabel
      verbatim (casefold) inside the new note, and no ea2 occurrence
      names "Dehui" anywhere afterwards;
    - headword-span law: review blocks stay consistent with their kwic
      span counts;
    - prose-anchoring gate on every edited sense;
    - path-scope law (SPEC §2): only the SPEC-listed paths may differ.

Receipt maintenance/r2-edit-receipt-20260903.json is written ONLY by
main() (importers call transform() for the oracle). Run with --apply
to write terms bytes; without it, dry. The pre-apply drift check
tolerates idempotent re-apply. Determinism: pure function of the clone
bytes (no wall-clock, no randomness).
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
# R2_CLONE_DIR lets the archive bundle re-run the pin checks against a
# detached git worktree of the pin commit after the install has been
# committed locally (clone HEAD then = the R2 commit, no longer the
# pin). Unchanged default: the agent clone itself.
CLONE = Path(os.environ.get(
    "R2_CLONE_DIR", r"C:\temp\NewTranslationrepos\CbetaZenTranslations"))
CLONE_HEAD_PIN = "145b090"
RECEIPT = "r2-edit-receipt-20260903.json"
RETIRED = {"T/T48/T48n2023.xml", "X/X63/X63n1245.xml"}
COHORT = ("t_ea2a427c7aba", "t_057cc9ea8755", "t_968a2f97c9ff")
CJK_RE = re.compile(r"[㐀-鿿豈-﫿]+")
T4825 = "T/T48/T48n2025.xml"

# ---- frozen attribution constants (probe-verified) ---------------------------
FROZEN_CONTEXT_MASTERS = [
    {"MasterName": "Dongyang Dehui", "Roles": ["compiler"]},
]
AA_COMMON = {
    "Status": "impersonal",
    "Kind": "institutional procedure",
    "ActorLabel": "the monastic code's institutional voice",
    "ActorRole": "compiler",
    "RungsChecked": [
        "line", "expanded-context", "section-header", "book-title",
        "tei-header", "parallel-passage",
    ],
    "ReviewedBy": "R2 external-review correction lane author",
    "ReviewedUtc": "2026-09-03T23:26:00+02:00",
}


def actor_block(evidence: str) -> dict:
    """Field order mirrors the live institutional blocks."""
    return {**AA_COMMON, "GrammarEvidence": evidence}

# ---- frozen occurrence attribution rewrites (ea2 sense 1) --------------------
# pre notes are asserted byte-exactly; every corpus byte is carried over.
OCC_ATTR_EDITS = [
    {
        "si": 1, "oi": 1,
        "expectOld": {
            "RelPath": T4825, "FromLb": "1143a07", "MasterName": "Dehui",
        },
        "oldNote": (
            "Source record (T/T48/T48n2025.xml). Imperially Commissioned "
            "Baizhang Monastic Regulations (勅修百丈清規): the code's titled "
            "Rules for Sitting Chan (坐禪儀) section, redacted by Dehui: the "
            "code directs sitting in a quiet place on a thick seat, in the "
            "full or half cross-legged position, the left palm resting on "
            "the right with the thumbs touching, the body upright with the "
            "ears to the shoulders and nose to the navel, the tongue against "
            "the upper palate, and the eyes slightly open to avoid "
            "drowsiness, and records Fayun Yuantong's rebuke of sitting "
            "with closed eyes as a black mountain ghost cave"
        ),
        "newNote": (
            "Source record (T/T48/T48n2025.xml). Imperially Commissioned "
            "Baizhang Monastic Regulations (勅修百丈清規): the monastic "
            "code's institutional voice, in the code's titled Rules for "
            "Sitting Chan (坐禪儀) section — imperially re-edited by "
            "Dongyang Dehui (元 德煇重編) — directs sitting in a quiet place "
            "on a thick seat, in the full or half cross-legged position, "
            "the left palm resting on the right with the thumbs touching, "
            "the body upright with the ears to the shoulders and nose to "
            "the navel, the tongue against the upper palate, and the eyes "
            "slightly open to avoid drowsiness, and records the rebuke of "
            "sitting with closed eyes as a black mountain ghost cave"
        ),
        "evidence": (
            "The complete case was read for who utters 坐禪. The passage is "
            "serialized procedural regulation — posture directions to the "
            "assembly with no dialogue frame and no first person; the "
            "closing rebuke anecdote is quoted precedent, not a speaking "
            "turn. This stored token is assigned to the monastic code's "
            "institutional voice; no record owner is substituted merely "
            "because the passage occurs in that owner's record."
        ),
    },
    {
        "si": 1, "oi": 8,
        "expectOld": {
            "RelPath": T4825, "FromLb": "1113a21", "MasterName": "Dehui",
        },
        "oldNote": (
            "Source record (T/T48/T48n2025.xml). Imperially Commissioned "
            "Baizhang Monastic Regulations (勅修百丈清規): The Imperially "
            "Revised Baizhang Monastic Code (勅修百丈清規), redacted by "
            "Dehui: the code assembles the community in the hall, says "
            "that ordinary sitting Chan faces inward, and directs everyone "
            "to turn outward when the drum sounds"
        ),
        "newNote": (
            "Source record (T/T48/T48n2025.xml). Imperially Commissioned "
            "Baizhang Monastic Regulations (勅修百丈清規): the monastic "
            "code's institutional voice, imperially re-edited by Dongyang "
            "Dehui (元 德煇重編), assembles the community in the hall, "
            "states that ordinary sitting Chan faces inward, and directs "
            "everyone to turn outward when the drum sounds"
        ),
        "evidence": (
            "The complete case was read for who utters 坐禪. The passage "
            "is an announced hall procedure: it prescribes the assembly's "
            "collective orientation on an audible signal — the register of "
            "institutional directive, not reported speech. This stored "
            "token is assigned to the monastic code's institutional voice; "
            "no record owner is substituted merely because the passage "
            "occurs in that owner's record."
        ),
    },
    {
        "si": 1, "oi": 9,
        "expectOld": {
            "RelPath": T4825, "FromLb": "1143a12", "MasterName": "Dehui",
        },
        "oldNote": (
            "Source record (T/T48/T48n2025.xml). Imperially Commissioned "
            "Baizhang Monastic Regulations (勅修百丈清規): the code's titled "
            "Rules for Sitting Chan (坐禪儀) section, redacted by Dehui: the "
            "code directs thinking neither good nor evil and noticing the "
            "moment a thought arises, calls this the essential procedure of "
            "sitting Chan and sitting Chan a gate of ease, and notes that "
            "many are harmed by missing its essentials"
        ),
        "newNote": (
            "Source record (T/T48/T48n2025.xml). Imperially Commissioned "
            "Baizhang Monastic Regulations (勅修百丈清規): the monastic "
            "code's institutional voice, in the code's titled Rules for "
            "Sitting Chan (坐禪儀) section — imperially re-edited by "
            "Dongyang Dehui (元 德煇重編) — directs thinking neither good "
            "nor evil and noticing the moment a thought arises, calls this "
            "the essential procedure of sitting Chan and sitting Chan a "
            "gate of ease, and notes that many are harmed by missing its "
            "essentials"
        ),
        "evidence": (
            "The complete case was read for who utters 坐禪. The passage "
            "is impersonal doctrinal summary in declarative register — no "
            "addressee, no dialogue frame, no first person — the code's "
            "own regulation prose. This stored token is assigned to the "
            "monastic code's institutional voice; no record owner is "
            "substituted merely because the passage occurs in that "
            "owner's record."
        ),
    },
]

# ---- frozen prose / list edits (find-once or exact-list laws) ----------------
PROSE_EDITS: dict[str, list] = {
    "t_ea2a427c7aba": [
        {"si": 1, "field": "Explanation", "class": "explanation-rewrite",
         "old": ("Dehui's monastic code gives an observable hall "
                 "convention:"),
         "new": ("The Baizhang monastic code redacted by Dongyang Dehui "
                 "gives an observable hall convention:")},
    ],
    "t_057cc9ea8755": [
        {"si": 1, "field": "Note", "class": "note-rewrite",
         "old": "verse in his own record retains",
         "new": ("verse in his recorded sayings, compiled by his "
                 "disciples, retains")},
        {"si": 1, "field": "OccAttributionNote", "oi": 3,
         "class": "attributionnote-rewrite",
         "old": ("Shiwu Qinghong: Sayings (石屋清洪禪師語錄): in the "
                 "verse"),
         "new": ("Shiwu Qinghong: Sayings (石屋清洪禪師語錄), compiled by "
                 "his disciples (至柔等編): in the verse")},
    ],
}

RELATED_RENAME = {"old": "Dehui", "new": "Dongyang Dehui"}
ALIAS_OLD = ["one fails, two is wrong"]
ALIAS_ADD = "一不成、二不是"

# ---- path-scope law (SPEC §2) ------------------------------------------------
ALLOWED_OCC_RE = re.compile(r"^Senses\[\d+\]\.Occurrences(?:[.\[]|$)")
ALLOWED_PATHS: dict[str, list] = {
    "t_ea2a427c7aba": [
        ALLOWED_OCC_RE,
        re.compile(r"^Senses\[0\]\.Explanation$"),
        re.compile(r"^Senses\[0\]\.RelatedMasters(?:[.\[]|$)"),
    ],
    "t_057cc9ea8755": [
        re.compile(r"^Senses\[0\]\.Note$"),
        re.compile(r"^Senses\[0\]\.Occurrences\[2\]\.AttributionNote$"),
    ],
    "t_968a2f97c9ff": [
        re.compile(r"^Senses\[0\]\.SearchAliases(?:[.\[]|$)"),
    ],
}


def canon(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def clone_state() -> dict[str, dict]:
    head = subprocess.run(
        ["git", "-C", str(CLONE), "rev-parse", "HEAD"],
        capture_output=True, text=True).stdout.strip()
    if head[:7] != CLONE_HEAD_PIN:
        raise SystemExit(f"clone HEAD {head[:7]} != pin {CLONE_HEAD_PIN}")
    dirty = subprocess.run(
        ["git", "-C", str(CLONE), "status", "--porcelain"],
        capture_output=True, text=True).stdout.splitlines()
    if dirty:
        raise SystemExit(f"clone dirty: {dirty[:5]}")
    v2 = json.loads((CLONE / "termbase.v2.json").read_text(encoding="utf-8"))
    return {e["Id"]: e for e in v2["Entries"]}


DEFECT_CENSUS = {
    "t_ea2a427c7aba": 3,       # this lane repairs all three
    "t_ab715aa474d5": 1,       # follow-up lane (user decision 2026-09-03)
    "t_351fa42d396b": 1,       # follow-up lane (user decision 2026-09-03)
}


def derive(by_id: dict[str, dict]) -> list[str]:
    """First-principles cross-check of the defect this lane repairs.

    Requires the FULL clone view (clone_state() output): the defect
    census counts rows in entries outside this lane's cohort, so a
    cohort-only snapshot must not be passed here (transform() applies
    only cohort-scoped preconditions)."""
    for sibling in ("t_ab715aa474d5", "t_351fa42d396b"):
        if sibling not in by_id:
            raise SystemExit(f"derive() requires the full clone view "
                             f"(missing {sibling}; pass clone_state())")
    census: Counter = Counter()
    for eid, e in by_id.items():
        for s in e.get("Senses") or []:
            for o in s.get("Occurrences") or []:
                if (o.get("RelPath") == T4825
                        and o.get("MasterName") == "Dehui"):
                    census[eid] += 1
    if dict(census) != DEFECT_CENSUS:
        raise SystemExit(f"defect census drift: {dict(census)} != "
                         f"{DEFECT_CENSUS}")
    citing = sorted(
        eid for eid, e in by_id.items()
        if any(o.get("RelPath") in RETIRED or a.get("RelPath") in RETIRED
               for s in e.get("Senses") or []
               for o in s.get("Occurrences") or []
               for a in s.get("ClaimAnchors") or []))
    if citing:
        raise SystemExit(f"retired-rel regression: {citing}")
    # SourceTexts rows that merely LIST a retired work (no citing
    # occurrence/anchor) are a pre-existing stale-list class outside this
    # lane's scope (~49 entries, incl. 水頭); only the R2 cohort must not
    # list them:
    for eid in COHORT:
        for s in by_id[eid].get("Senses") or []:
            for rel in s.get("SourceTexts") or []:
                if rel in RETIRED:
                    raise SystemExit(f"{eid}: retired rel still listed in "
                                     "SourceTexts")
    note57 = by_id["t_057cc9ea8755"]["Senses"][0].get("Note") or ""
    if note57.count(PROSE_EDITS["t_057cc9ea8755"][0]["old"]) != 1:
        raise SystemExit("057: 'own record' anchor not find-once")
    sa = by_id["t_968a2f97c9ff"]["Senses"][0].get("SearchAliases")
    if sa != ALIAS_OLD or len(by_id["t_968a2f97c9ff"]["Senses"]) != 1:
        raise SystemExit(f"968: SearchAliases/shape drift: {sa!r}")
    return list(COHORT)


def flat(value, prefix: str = "", out: list | None = None) -> list:
    """Flatten to (path, canonical-leaf-bytes) pairs for path-scope diff."""
    if out is None:
        out = []
    if isinstance(value, dict):
        for k in sorted(value):
            flat(value[k], f"{prefix}.{k}" if prefix else k, out)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            flat(v, f"{prefix}[{i}]", out)
    else:
        out.append((prefix, canon(value)))
    return out


def _kwic(o) -> str:
    return str(o.get("Kwic") or "")


def _anchored(quote: str, kwics: list[str]) -> bool:
    return any(quote in k or k in quote for k in kwics if k)


CARRIED_KEYS = ("RelPath", "FromLb", "ToLb", "Kwic", "Curated",
                "HeadwordSpanReview")


def transform(by_id: dict[str, dict]) -> tuple[dict[str, str], list[dict]]:
    """Apply the frozen edits IN PLACE over the cohort; return
    {eid: canon bytes} + edit records. by_id must be a private deep copy
    of at least the cohort (main() snapshots the cohort; importers may
    pass clone_state() output they own — full-view fleet laws live in
    derive(), which only main() calls)."""
    for eid in COHORT:
        if eid not in by_id:
            raise SystemExit(f"transform(): cohort entry {eid} missing")
    pre = {eid: copy.deepcopy(by_id[eid]) for eid in COHORT}
    pre_senses = {eid: len(by_id[eid].get("Senses") or [])
                  for eid in COHORT}
    pre_occ_counts = {
        eid: [len(s.get("Occurrences") or [])
              for s in by_id[eid].get("Senses") or []]
        for eid in COHORT}
    records: list[dict] = []
    out: dict[str, str] = {}

    # ---- ea2: occ-attribution rewrites -----------------------------------
    e = by_id["t_ea2a427c7aba"]
    term = e["SourceTerm"]
    for spec in OCC_ATTR_EDITS:
        si, oi = spec["si"], spec["oi"]
        occs = e["Senses"][si - 1]["Occurrences"]
        old = occs[oi - 1]
        for k, v in spec["expectOld"].items():
            if old.get(k) != v:
                raise SystemExit(
                    f"ea2 s{si} o{oi}: pre {k}={old.get(k)!r} != expected "
                    f"{v!r} (identity drift)")
        if old.get("AttributionNote") != spec["oldNote"]:
            raise SystemExit(
                f"ea2 s{si} o{oi}: pre AttributionNote drift (byte "
                "inequality against the frozen pre note)")
        new = dict(old)
        new["MasterName"] = None
        new["ContextMasters"] = copy.deepcopy(FROZEN_CONTEXT_MASTERS)
        new["ActorAttribution"] = actor_block(spec["evidence"])
        new["AttributionNote"] = spec["newNote"]
        for k in CARRIED_KEYS:
            if old.get(k) != new.get(k) and (k in old or k in new):
                raise SystemExit(f"ea2 s{si} o{oi}: carried key {k} moved")
        occs[oi - 1] = new
        records.append({
            "class": "occ-attribution", "entry": "t_ea2a427c7aba",
            "si": si, "oi": oi,
            "oldMasterName": old.get("MasterName"),
            "newMasterName": None,
            "newContextMasters": FROZEN_CONTEXT_MASTERS,
            "newActorAttribution": new["ActorAttribution"],
            "oldAttributionNote": spec["oldNote"],
            "newAttributionNote": spec["newNote"],
            "carried": {k: old.get(k) for k in CARRIED_KEYS if k in old},
        })

    # ---- ea2: RelatedMasters rename ---------------------------------------
    rm = e["Senses"][0]["RelatedMasters"]
    if rm.count(RELATED_RENAME["old"]) != 1:
        raise SystemExit(f"ea2: RelatedMasters 'Dehui' not find-once: {rm}")
    rm[rm.index(RELATED_RENAME["old"])] = RELATED_RENAME["new"]
    records.append({
        "class": "relatedmasters-rename", "entry": "t_ea2a427c7aba",
        "si": 1, "renamed": RELATED_RENAME,
        "postRelatedMasters": list(rm),
    })

    # ---- prose rewrites (ea2 + 057) ----------------------------------------
    for eid in ("t_ea2a427c7aba", "t_057cc9ea8755"):
        for spec in PROSE_EDITS[eid]:
            s = by_id[eid]["Senses"][spec["si"] - 1]
            if spec["field"] == "OccAttributionNote":
                holder = s["Occurrences"][spec["oi"] - 1]
                val = str(holder.get("AttributionNote") or "")
                if val.count(spec["old"]) != 1:
                    raise SystemExit(
                        f"{eid} s{spec['si']} o{spec['oi']}: find-once "
                        f"violation for {spec['old'][:40]!r}")
                holder["AttributionNote"] = \
                    val.replace(spec["old"], spec["new"], 1)
            else:
                val = str(s.get(spec["field"]) or "")
                if val.count(spec["old"]) != 1:
                    raise SystemExit(
                        f"{eid} s{spec['si']} {spec['field']}: find-once "
                        f"violation for {spec['old'][:40]!r} "
                        f"({val.count(spec['old'])} hits)")
                s[spec["field"]] = val.replace(spec["old"], spec["new"], 1)
            records.append({
                "class": spec["class"], "entry": eid, "si": spec["si"],
                "field": spec["field"], "oi": spec.get("oi"),
                "before": spec["old"], "after": spec["new"],
            })

    # ---- 968: SearchAliases append -----------------------------------------
    sa = by_id["t_968a2f97c9ff"]["Senses"][0]["SearchAliases"]
    if sa != ALIAS_OLD:
        raise SystemExit(f"968: SearchAliases drift at apply: {sa!r}")
    sa.append(ALIAS_ADD)
    records.append({
        "class": "searchaliases-add", "entry": "t_968a2f97c9ff", "si": 1,
        "added": ALIAS_ADD, "postSearchAliases": list(sa),
    })

    # ---- post-state laws -----------------------------------------------------

    # attribution-convention law on the three repaired rows
    for spec in OCC_ATTR_EDITS:
        o = e["Senses"][spec["si"] - 1]["Occurrences"][spec["oi"] - 1]
        aa = o.get("ActorAttribution") or {}
        if (o.get("MasterName") is not None
                or o.get("ContextMasters") != FROZEN_CONTEXT_MASTERS
                or aa.get("Status") != "impersonal"
                or aa.get("Kind") != "institutional procedure"
                or aa.get("ActorRole") != "compiler"
                or aa.get("RungsChecked") != AA_COMMON["RungsChecked"]
                or aa.get("ActorLabel") != AA_COMMON["ActorLabel"]
                or aa.get("GrammarEvidence") != spec["evidence"]
                or str(aa.get("ActorLabel")).casefold()
                not in str(o.get("AttributionNote")).casefold()):
            raise SystemExit(f"ea2 s{spec['si']} o{spec['oi']}: "
                             "attribution-convention law violated")
    for s in e.get("Senses") or []:
        for o in s.get("Occurrences") or []:
            names = [o.get("MasterName")] + [
                cm.get("MasterName") for cm in o.get("ContextMasters") or []]
            if "Dehui" in names:
                raise SystemExit("ea2: a 'Dehui' name survived the repair")
    if "Dehui" in e["Senses"][0]["RelatedMasters"]:
        raise SystemExit("ea2: RelatedMasters still contains 'Dehui'")

    # headword-span law on the three repaired rows only (untouched rows
    # are out of this lane's scope; s1o9's carried review block is
    # additionally byte-asserted by the CARRIED_KEYS law above)
    for spec in OCC_ATTR_EDITS:
        o = e["Senses"][spec["si"] - 1]["Occurrences"][spec["oi"] - 1]
        spans = _kwic(o).count(term)
        review = o.get("HeadwordSpanReview")
        if spans > 1 and not (review and review.get("Count") == spans
                              and review.get("Disposition")
                              == "single-actor-single-turn-repetition"):
            raise SystemExit(f"ea2 s{spec['si']} o{spec['oi']}: span law "
                             f"violated ({spans} spans)")
        if spans <= 1 and review:
            raise SystemExit(f"ea2 s{spec['si']} o{spec['oi']}: review "
                             f"block on {spans}-span kwic")

    # counts unchanged + no retired rel + occ rel ⊆ SourceTexts (cohort)
    for eid in COHORT:
        entry = by_id[eid]
        if (len(entry.get("Senses") or []) != pre_senses[eid]
                or [len(s.get("Occurrences") or [])
                    for s in entry.get("Senses") or []]
                != pre_occ_counts[eid]):
            raise SystemExit(f"{eid}: sense/occurrence count drift")
        for s in entry.get("Senses") or []:
            for o in s.get("Occurrences") or []:
                if o.get("RelPath") in RETIRED:
                    raise SystemExit(f"{eid}: retired occurrence present")
            for a in s.get("ClaimAnchors") or []:
                if a.get("RelPath") in RETIRED:
                    raise SystemExit(f"{eid}: retired anchor present")
            for rel in {o.get("RelPath")
                        for o in s.get("Occurrences") or []}:
                if rel not in s.get("SourceTexts", []):
                    raise SystemExit(f"{eid}: occ rel {rel} missing from "
                                     "SourceTexts")
            for rel in s.get("SourceTexts") or []:
                if rel in RETIRED:
                    raise SystemExit(f"{eid}: retired rel in SourceTexts")

    # prose-anchoring gate on the senses whose prose fields were edited
    for eid, si in (("t_ea2a427c7aba", 1), ("t_057cc9ea8755", 1)):
        s = by_id[eid]["Senses"][si - 1]
        survivors = [_kwic(o) for o in s.get("Occurrences") or []]
        survivors += [_kwic(a) for a in s.get("ClaimAnchors") or []]
        prose = "\n".join(str(s.get(k) or "")
                          for k in ("Explanation", "Note"))
        for quote in sorted(set(CJK_RE.findall(prose))):
            if not _anchored(quote, survivors):
                raise SystemExit(f"{eid} s{si}: prose dangles: "
                                 f"{quote[:24]}")

    # path-scope law (SPEC §2) + changed-path ledger
    changed_paths: dict[str, list] = {}
    for eid in COHORT:
        pre_map = dict(flat(pre[eid]))
        post_map = dict(flat(by_id[eid]))
        changed = sorted(
            path for path in set(pre_map) | set(post_map)
            if pre_map.get(path) != post_map.get(path))
        for path in changed:
            if not any(rx.search(path) for rx in ALLOWED_PATHS[eid]):
                raise SystemExit(f"path-scope escape: {eid} {path}")
        changed_paths[eid] = changed
        out[eid] = canon(by_id[eid])

    if len(records) != 8:
        raise SystemExit(f"edit records {len(records)} != 8")
    return out, records


def write_receipt(out: dict[str, str], records: list[dict],
                  worklist: list[str]) -> None:
    counts: dict[str, int] = {}
    for r in records:
        counts[r["class"]] = counts.get(r["class"], 0) + 1
    receipt = {
        "schemaVersion": "r2-edit-receipt",
        "lane": "R2",
        "spec": "SPEC_R2_20260903.md",
        "cloneHead": CLONE_HEAD_PIN,
        "engine": Path(__file__).name,
        "applied": "--apply" in sys.argv,
        "products": worklist,
        "followUpLane": ["t_ab715aa474d5", "t_351fa42d396b"],
        "editClassCounts": counts,
        "editRecords": records,
        "entryShas": {},
    }
    for eid in worklist:
        receipt["entryShas"][eid] = hashlib.sha256(
            out[eid].encode("utf-8")).hexdigest()
    (HERE / RECEIPT).write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="")


def main() -> None:
    by_id = clone_state()
    worklist = derive(by_id)
    snapshot = {eid: copy.deepcopy(by_id[eid]) for eid in worklist}
    out, records = transform(snapshot)
    if "--apply" in sys.argv:
        drift = []
        for p in sorted((ROOT / "terms").glob("*/entry.v2.json")):
            eid = p.parent.name
            if eid in by_id:
                cur = p.read_text(encoding="utf-8-sig")
                if (cur != canon(by_id[eid])
                        and not (eid in out and cur == out[eid])):
                    drift.append(eid)
        if drift:
            raise SystemExit(f"terms != canon(clone) (and not this "
                             f"engine's output): {drift[:5]} ({len(drift)})")
        for eid, text in out.items():
            (ROOT / "terms" / eid / "entry.v2.json").write_text(
                text, encoding="utf-8", newline="")
        write_receipt(out, records, worklist)
        print(f"APPLIED {len(records)} edits over {len(out)} entries")
    else:
        write_receipt(out, records, worklist)
        print(f"DRY {len(records)} edits over {len(out)} entries; "
              f"classes={sorted(set(r['class'] for r in records))}")


if __name__ == "__main__":
    main()
