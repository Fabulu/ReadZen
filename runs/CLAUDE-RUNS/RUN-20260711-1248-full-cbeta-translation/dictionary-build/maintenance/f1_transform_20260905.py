#!/usr/bin/env python3
"""SPEC_F1_20260905.md §1-2: the follow-up-lane correction engine (F1).

Input is the CLONE pre-state at pinned HEAD 8457672 (the R2 install
commit; confinement law: engine(clone) == terms bytes after apply,
asserted before writing). F1_CLONE_DIR mirrors R2's env override for
the archive bundle's post-commit re-run (default: the agent clone).

Like R2 the lane is AUTHORED — every new attribution note, actor block,
and prose replacement is a SPEC-frozen constant verified against local
authorities by probe_f1_corpus_windows_20260905.py (the full-case
re-reads: 普請 communal-labor directive for 1144b03; 遷化 funeral
scheduling for 1127c04; the 常曰 Baizhang narrative contrast at
1119b01) and probe_f1_design_facts_20260905.py (fleet census exactly 2;
roster "Dongyang Dehui" in / exact "Dehui" out; R2's installed
convention bytes mirrored):

  per entry (SPEC §1) —
    - occ-attribution (ab715 s1o2; 351fa s1o1): carry-over-with-
      overwrite — RelPath/FromLb/ToLb/Kwic/Curated carried
      byte-identically (neither row carries HeadwordSpanReview);
      MasterName -> null; ContextMasters -> the R2 precedent compiler
      block; ActorAttribution appended (frozen); AttributionNote
      replaced (frozen; pre notes asserted byte-exactly first).
    - relatedmasters-rename (both entries): "Dehui" -> "Dongyang
      Dehui" in place.
    - explanation-rewrite (351fa s1): find-once "redacted by Dehui," ->
      "redacted by Dongyang Dehui,".

  Post-state laws asserted before any output is accepted:
    - fleet census (derive): the T48n2025+"Dehui" defect is exactly
      these 2 rows, and R2's three products still carry the R2 repair
      (MasterName null windows intact — the lane must not disturb them);
    - no retired rel anywhere fleet-wide; sense and per-sense occurrence
      counts unchanged;
    - attribution-convention law: the 2 repaired rows carry MasterName
      null, the frozen ContextMasters/ActorAttribution, ActorLabel
      verbatim (casefold) inside the new note, and neither entry names
      exact "Dehui" anywhere afterwards;
    - headword-span law: single-span kwics carry no review block;
    - prose-anchoring gate on the edited senses;
    - path-scope law (SPEC §2).

Receipt maintenance/f1-edit-receipt-20260905.json is written ONLY by
main() (importers call transform() for the oracle). Run with --apply
to write terms bytes; without it, dry. Determinism: pure function of
the clone bytes (no wall-clock, no randomness).
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
# F1_CLONE_DIR lets the archive bundle re-run the pin checks against a
# detached git worktree of the pin commit after this lane's install is
# committed locally (clone HEAD then = the F1 commit). Default: agent
# clone.
CLONE = Path(os.environ.get(
    "F1_CLONE_DIR", r"C:\temp\NewTranslationrepos\CbetaZenTranslations"))
CLONE_HEAD_PIN = "8457672"
RECEIPT = "f1-edit-receipt-20260905.json"
RETIRED = {"T/T48/T48n2023.xml", "X/X63/X63n1245.xml"}
COHORT = ("t_ab715aa474d5", "t_351fa42d396b")
R2_PRODUCTS = ("t_ea2a427c7aba", "t_057cc9ea8755", "t_968a2f97c9ff")
CJK_RE = re.compile(r"[㐀-鿿豈-﫿]+")
T4825 = "T/T48/T48n2025.xml"

# ---- frozen attribution constants (R2-installed convention, mirrored) --------
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
    "ReviewedBy": "F1 follow-up correction lane author",
    "ReviewedUtc": "2026-09-05T01:34:58+02:00",
}


def actor_block(evidence: str) -> dict:
    """Field order mirrors the live institutional blocks."""
    return {**AA_COMMON, "GrammarEvidence": evidence}

# ---- frozen occurrence attribution rewrites ----------------------------------
# pre notes are asserted byte-exactly; every corpus byte is carried over.
OCC_ATTR_EDITS = [
    {
        "entry": "t_ab715aa474d5", "si": 1, "oi": 2,
        "expectOld": {
            "RelPath": T4825, "FromLb": "1144b03", "ToLb": "1144b04",
            "MasterName": "Dehui",
        },
        "oldNote": (
            "Source record (T/T48/T48n2025.xml). Imperially Commissioned "
            "Baizhang Monastic Regulations (勅修百丈清規): file T/T48/"
            "T48n2025.xml; exact actor: Dehui. The full-case proof "
            "distinguishes this actor from nearby respondents, "
            "questioners, and section subjects."
        ),
        "newNote": (
            "Source record (T/T48/T48n2025.xml). Imperially Commissioned "
            "Baizhang Monastic Regulations (勅修百丈清規): the monastic "
            "code's institutional voice, in the code's communal-labor "
            "(普請) section — imperially re-edited by Dongyang Dehui "
            "(元 德煇重編) — directs all but the watch, the duty-bound, "
            "the old, and the sick to attend communal labor together, "
            "bearing in mind the ancients' admonition 'a day without "
            "work is a day without food' (當思古人一日不作一日不食之誡)"
        ),
        "evidence": (
            "The complete case was read for who utters 一日不作一日不食. "
            "The passage sits in the code's communal-labor (普請) "
            "section: the regulations direct all but the watch, the "
            "duty-bound, the old, and the sick to attend communal labor "
            "together and to bear in mind the ancients' admonition — "
            "古人 marks the maxim as inherited precedent quoted by the "
            "code, not a speaking turn. This stored token is assigned "
            "to the monastic code's institutional voice; no record "
            "owner is substituted merely because the passage occurs in "
            "that owner's record."
        ),
    },
    {
        "entry": "t_351fa42d396b", "si": 1, "oi": 1,
        "expectOld": {
            "RelPath": T4825, "FromLb": "1127c04", "ToLb": "1127c10",
            "MasterName": "Dehui",
        },
        "oldNote": (
            "Source record (T/T48/T48n2025.xml). Imperially Commissioned "
            "Baizhang Monastic Regulations (勅修百丈清規). Redacted by "
            "Dehui, prescribes gruel and rice at two times and tea and "
            "hot water at three during funeral observances."
        ),
        "newNote": (
            "Source record (T/T48/T48n2025.xml). Imperially Commissioned "
            "Baizhang Monastic Regulations (勅修百丈清規): the monastic "
            "code's institutional voice, in the code's funeral-observance "
            "sequence — imperially re-edited by Dongyang Dehui (元 德煇"
            "重編) — prescribes gruel and rice at two times and tea and "
            "hot water at three during funeral observances, with the "
            "assembly reciting sutras"
        ),
        "evidence": (
            "The complete case was read for who utters 粥飯. The passage "
            "sits in the code's funeral-observance (遷化) sequence: it is "
            "serialized scheduling regulation for the mourning period — "
            "gruel and rice at two times, tea and hot water at three, "
            "the assembly reciting sutras — with no dialogue frame and "
            "no first person. This stored token is assigned to the "
            "monastic code's institutional voice; no record owner is "
            "substituted merely because the passage occurs in that "
            "owner's record."
        ),
    },
]

# ---- frozen prose / list edits (find-once laws) -------------------------------
PROSE_EDITS: dict[str, list] = {
    "t_351fa42d396b": [
        {"si": 1, "field": "Explanation",
         "class": "explanation-rewrite",
         "old": "redacted by Dehui,",
         "new": "redacted by Dongyang Dehui,"},
    ],
}

RELATED_RENAME = {"old": "Dehui", "new": "Dongyang Dehui"}

# ---- path-scope law (SPEC §2) --------------------------------------------------
OCC_FIELD_RE = (r"Senses\[0\]\.Occurrences\[(1|0)\]\."
                r"(?:MasterName|ContextMasters|AttributionNote"
                r"|ActorAttribution)")
ALLOWED_PATHS: dict[str, list] = {
    "t_ab715aa474d5": [
        re.compile(OCC_FIELD_RE.replace("(1|0)", "[1]")),
        re.compile(r"^Senses\[0\]\.RelatedMasters\[1\]$"),
    ],
    "t_351fa42d396b": [
        re.compile(OCC_FIELD_RE.replace("(1|0)", "[0]")),
        re.compile(r"^Senses\[0\]\.RelatedMasters\[1\]$"),
        re.compile(r"^Senses\[0\]\.Explanation$"),
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
    "t_ab715aa474d5": 1,       # this lane repairs it
    "t_351fa42d396b": 1,       # this lane repairs it
}

# R2's three repaired windows must be intact in the pre-state (the F1
# lane must not disturb the shipped R2 repair).
R2_REPAIRED_WINDOWS = {
    "t_ea2a427c7aba": {"1143a07", "1113a21", "1143a12"},
}


def derive(by_id: dict[str, dict]) -> list[str]:
    """First-principles cross-check of the defect this lane repairs.

    Requires the FULL clone view (clone_state() output)."""
    for protected in R2_PRODUCTS + COHORT:
        if protected not in by_id:
            raise SystemExit(f"derive() requires the full clone view "
                             f"(missing {protected}; pass clone_state())")
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
        if any(x.get("RelPath") in RETIRED
               for s in e.get("Senses") or []
               for x in (s.get("Occurrences") or [])
               + (s.get("ClaimAnchors") or [])))
    if citing:
        raise SystemExit(f"retired-rel regression: {citing}")
    for eid in COHORT:
        for s in by_id[eid].get("Senses") or []:
            for rel in s.get("SourceTexts") or []:
                if rel in RETIRED:
                    raise SystemExit(f"{eid}: retired rel still listed in "
                                     "SourceTexts")
    # R2 repair intact: the three ea2 windows still carry the
    # institutional-voice fix (null MasterName + compiler context).
    ea2 = by_id["t_ea2a427c7aba"]
    for o in ea2["Senses"][0]["Occurrences"]:
        if o.get("FromLb") in R2_REPAIRED_WINDOWS["t_ea2a427c7aba"]:
            if (o.get("MasterName") is not None
                    or o.get("ContextMasters")
                    != FROZEN_CONTEXT_MASTERS):
                raise SystemExit(
                    f"R2 repair disturbed pre-F1: window {o.get('FromLb')}")
    if len([o for o in ea2["Senses"][0]["Occurrences"]
            if o.get("MasterName") is None
            and o.get("ContextMasters") == FROZEN_CONTEXT_MASTERS]) != 3:
        raise SystemExit("R2 ea2 repair shape drifted (expected 3 rows)")
    # find-once anchors for the frozen prose edit
    expl = by_id["t_351fa42d396b"]["Senses"][0].get("Explanation") or ""
    if expl.count(PROSE_EDITS["t_351fa42d396b"][0]["old"]) != 1:
        raise SystemExit("351fa: Explanation 'redacted by Dehui,' anchor "
                         "not find-once")
    for eid in COHORT:
        rm = by_id[eid]["Senses"][0].get("RelatedMasters") or []
        if rm.count(RELATED_RENAME["old"]) != 1:
            raise SystemExit(f"{eid}: RelatedMasters 'Dehui' not "
                             f"find-once: {rm}")
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

    # ---- occ-attribution rewrites (both entries) ---------------------------
    for spec in OCC_ATTR_EDITS:
        eid, si, oi = spec["entry"], spec["si"], spec["oi"]
        e = by_id[eid]
        term = e["SourceTerm"]
        occs = e["Senses"][si - 1]["Occurrences"]
        old = occs[oi - 1]
        for k, v in spec["expectOld"].items():
            if old.get(k) != v:
                raise SystemExit(
                    f"{eid} s{si} o{oi}: pre {k}={old.get(k)!r} != "
                    f"expected {v!r} (identity drift)")
        if old.get("AttributionNote") != spec["oldNote"]:
            raise SystemExit(
                f"{eid} s{si} o{oi}: pre AttributionNote drift (byte "
                "inequality against the frozen pre note)")
        if old.get("ContextMasters") != [
                {"MasterName": "Dehui", "Roles": ["utterer"]}]:
            raise SystemExit(
                f"{eid} s{si} o{oi}: pre ContextMasters drift")
        new = dict(old)
        new["MasterName"] = None
        new["ContextMasters"] = copy.deepcopy(FROZEN_CONTEXT_MASTERS)
        new["ActorAttribution"] = actor_block(spec["evidence"])
        new["AttributionNote"] = spec["newNote"]
        for k in CARRIED_KEYS:
            if old.get(k) != new.get(k) and (k in old or k in new):
                raise SystemExit(f"{eid} s{si} o{oi}: carried key {k} "
                                 "moved")
        occs[oi - 1] = new
        records.append({
            "class": "occ-attribution", "entry": eid, "si": si, "oi": oi,
            "oldMasterName": old.get("MasterName"),
            "newMasterName": None,
            "newContextMasters": FROZEN_CONTEXT_MASTERS,
            "newActorAttribution": new["ActorAttribution"],
            "oldAttributionNote": spec["oldNote"],
            "newAttributionNote": spec["newNote"],
            "carried": {k: old.get(k) for k in CARRIED_KEYS if k in old},
        })
        del term  # headword asserted in the span law below

    # ---- RelatedMasters renames (both entries) ------------------------------
    for eid in COHORT:
        rm = by_id[eid]["Senses"][0]["RelatedMasters"]
        if rm.count(RELATED_RENAME["old"]) != 1:
            raise SystemExit(f"{eid}: RelatedMasters 'Dehui' not "
                             f"find-once at apply: {rm}")
        rm[rm.index(RELATED_RENAME["old"])] = RELATED_RENAME["new"]
        records.append({
            "class": "relatedmasters-rename", "entry": eid, "si": 1,
            "renamed": RELATED_RENAME,
            "postRelatedMasters": list(rm),
        })

    # ---- prose rewrites (351fa) ----------------------------------------------
    for eid, specs in PROSE_EDITS.items():
        for spec in specs:
            s = by_id[eid]["Senses"][spec["si"] - 1]
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

    # ---- post-state laws ------------------------------------------------------

    # attribution-convention law on the two repaired rows
    for spec in OCC_ATTR_EDITS:
        eid, si, oi = spec["entry"], spec["si"], spec["oi"]
        o = by_id[eid]["Senses"][si - 1]["Occurrences"][oi - 1]
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
            raise SystemExit(f"{eid} s{si} o{oi}: attribution-convention "
                             "law violated")
    for eid in COHORT:
        e = by_id[eid]
        for s in e.get("Senses") or []:
            for o in s.get("Occurrences") or []:
                names = [o.get("MasterName")] + [
                    cm.get("MasterName")
                    for cm in o.get("ContextMasters") or []]
                if "Dehui" in names:
                    raise SystemExit(f"{eid}: a 'Dehui' name survived the "
                                     "repair")
        for s in e.get("Senses") or []:
            if "Dehui" in (s.get("RelatedMasters") or []):
                raise SystemExit(f"{eid}: RelatedMasters still contains "
                                 "'Dehui'")

    # headword-span law on the two repaired rows (both single-span)
    for spec in OCC_ATTR_EDITS:
        eid, si, oi = spec["entry"], spec["si"], spec["oi"]
        e = by_id[eid]
        term = e["SourceTerm"]
        o = e["Senses"][si - 1]["Occurrences"][oi - 1]
        spans = _kwic(o).count(term)
        review = o.get("HeadwordSpanReview")
        if spans > 1 and not (review and review.get("Count") == spans
                              and review.get("Disposition")
                              == "single-actor-single-turn-repetition"):
            raise SystemExit(f"{eid} s{si} o{oi}: span law violated "
                             f"({spans} spans)")
        if spans <= 1 and review:
            raise SystemExit(f"{eid} s{si} o{oi}: review block on "
                             f"{spans}-span kwic")

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

    # prose-anchoring gate on the edited senses
    for eid, si in (("t_351fa42d396b", 1),):
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

    if len(records) != 5:
        raise SystemExit(f"edit records {len(records)} != 5")
    return out, records


def write_receipt(out: dict[str, str], records: list[dict],
                  worklist: list[str]) -> None:
    counts: dict[str, int] = {}
    for r in records:
        counts[r["class"]] = counts.get(r["class"], 0) + 1
    receipt = {
        "schemaVersion": "f1-edit-receipt",
        "lane": "F1",
        "spec": "SPEC_F1_20260905.md",
        "cloneHead": CLONE_HEAD_PIN,
        "engine": Path(__file__).name,
        "applied": "--apply" in sys.argv,
        "products": worklist,
        "r2ProductsProtected": list(R2_PRODUCTS),
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
