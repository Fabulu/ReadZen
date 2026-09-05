#!/usr/bin/env python3
"""Build the blind r1 DELTA review deck for the fresh10k-r7-depth lane.

The original r7 occurrences passed three blind rounds in the r7 lane; this
deck re-anchors them by SHA (baselineEntrySha256 = the installed
terms/<id>/entry.v2.json, byte-equal to the r7 product entry) and reviews
ONLY the added occurrences plus the replace contract:

  law R (replace): term already public; baselineEntrySha256 == sha of
    terms/<id>/entry.v2.json on disk; occurrences == baseline count +
    added; every added occurrence is tier<3 in the registry.
  law F (delta): each addedWindow kwic carried byte-equals the product
    occurrence Kwic; ws-stripped kwic verbatim inside the ws-stripped
    document-order corpus text; From/ToLb exist in the document; headword
    in kwic; proof clause in kwic.

Canaries are a FRESH set targeting the delta fields (added windows,
baseline pin, replace counts) — prior rounds' plants targeted fields this
deck doesn't carry, and the resumed reviewer has already seen those
payloads."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET

HERE = Path(__file__).resolve().parent
BUILD = HERE.parent
FB = BUILD / "fresh-build"
LANE = FB / "fresh10k-r7-depth" / "products"
R7 = FB / "fresh10k-r7" / "products"
XML = Path(r"C:\programmieren\CbetaZenTexts\xml-p5")
REG_SRC = Path(r"C:\programmieren\MergeWorkCbeta\CBETA-Translator"
               r"\Assets\Data\zen-source-authority.json")
CLONE_TB = Path(r"C:\temp\NewTranslationrepos\CbetaZenTranslations"
                r"\termbase.v2.json")
MATS = HERE / "fresh10k-r7-depth-blind-r1-materials-20260905"

ROUND = "r1"
STAMP = "20260905"


def canon(o) -> str:
    return json.dumps(o, ensure_ascii=False, indent=2) + "\n"


def jcanon(o) -> str:
    return json.dumps(o, ensure_ascii=False, sort_keys=True)


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def strip_ws(s: str) -> str:
    return re.sub(r"\s+", "", s)


DOCS: dict[str, str] = {}


def doc_text(rel: str) -> str:
    if rel not in DOCS:
        DOCS[rel] = strip_ws("".join(ET.parse(XML / rel).getroot().itertext()))
    return DOCS[rel]


def prefix_normalized(old_o: dict, new_o: dict) -> bool:
    """Only permitted baseline-occurrence note change: prepending the
    compiler-mandated 'Source record (<RelPath>). ' prefix."""
    old_n = old_o.get("AttributionNote") or ""
    new_n = new_o.get("AttributionNote") or ""
    m = re.match(r"^Source record \([^)]+\)\. (.*)$", new_n, re.S)
    return (new_n != old_n and bool(m) and m.group(1) == old_n
            and all(jcanon(old_o.get(k)) == jcanon(new_o.get(k))
                    for k in old_o if k != "AttributionNote")
            and set(old_o) == set(new_o))


_ADJ_PATH = HERE / "depth-below-target-adjudications-20260905.json"
ANCHOR_FIXES: dict[str, list] = {}
if _ADJ_PATH.is_file():
    ANCHOR_FIXES = json.loads(
        _ADJ_PATH.read_text(encoding="utf-8-sig")).get("anchorFixes") or {}


def occ_allowed(old_o: dict, new_o: dict, fix: dict | None = None) -> bool:
    if jcanon(old_o) == jcanon(new_o):
        return True
    diffs = {k for k in set(old_o) | set(new_o)
             if jcanon(old_o.get(k)) != jcanon(new_o.get(k))}
    if "AttributionNote" in diffs:
        if not prefix_normalized(old_o, new_o):
            return False
        diffs.discard("AttributionNote")
    if not diffs:
        return True
    if fix and diffs == {"FromLb", "ToLb"}:
        return (old_o.get("RelPath") == fix.get("relPath")
                and old_o.get("FromLb") == fix.get("oldFromLb")
                and old_o.get("ToLb") == fix.get("oldToLb")
                and new_o.get("FromLb") == fix.get("newFromLb")
                and new_o.get("ToLb") == fix.get("newToLb"))
    return False


LB_NAMES: dict[str, set] = {}


def lb_names(rel: str) -> set:
    if rel not in LB_NAMES:
        raw = (XML / rel).read_text(encoding="utf-8")
        LB_NAMES[rel] = set(re.findall(r'<lb[^>]*\bn="([^"]+)"', raw))
    return LB_NAMES[rel]


# ---- inputs -------------------------------------------------------------------
MATS.mkdir(parents=True, exist_ok=True)
plan = json.loads((FB / "fresh10k-r7-depth/depth-plan-20260905.json")
                  .read_text(encoding="utf-8-sig"))
plan = {p["id"]: p for p in plan["entries"] if p.get("inScope")}
pmap_doc = json.loads((LANE / "product-map.json").read_text(encoding="utf-8-sig"))
pmap = {p["id"]: p for p in pmap_doc["products"]}
registry = json.loads(REG_SRC.read_text(encoding="utf-8-sig"))
public_terms = sorted({e.get("SourceTerm") for e in
                       json.loads(CLONE_TB.read_text(encoding="utf-8"))
                       ["Entries"] if e.get("SourceTerm")})
REG = {e["RelPath"]: e for e in
       (registry.get("entries") or registry.get("Entries") or [])}
assert REG and set(plan) == set(pmap), "plan/product-map id mismatch"

(MATS / "plan.json").write_text(canon(list(plan.values())), encoding="utf-8")
(MATS / "product-map.json").write_text(canon(pmap), encoding="utf-8")
(MATS / "registry.json").write_text(canon(registry), encoding="utf-8")
(MATS / "public-terms.json").write_text(canon(public_terms), encoding="utf-8")

receipts: dict[str, dict] = {}
corpus_files: set[str] = set()

rows, problems = [], []
for eid, p in sorted(pmap.items()):
    term, d = p["term"], LANE / eid
    ebytes = (d / "entry.v2.json").read_bytes()
    wbytes = (d / "evidence.draft.json").read_bytes()
    kbytes = (d / "WORK.md").read_bytes()
    entry = json.loads(ebytes.decode("utf-8-sig"))
    draft = json.loads(wbytes.decode("utf-8-sig"))
    rep = json.loads((d / "evidence-compile-report.json")
                     .read_text(encoding="utf-8-sig"))
    receipts[eid] = rep

    base_bytes = (R7 / eid / "entry.v2.json").read_bytes()
    base = json.loads(base_bytes.decode("utf-8-sig"))
    terms_base = (BUILD / "terms" / eid / "entry.v2.json").read_bytes()
    baseline_sha = sha_bytes(terms_base)
    if terms_base != base_bytes:
        problems.append(f"{eid}: terms baseline != r7 product bytes")

    pins = {"entrySha256": sha_bytes(ebytes),
            "worksheetSha256": sha_bytes(wbytes),
            "workSha256": sha_bytes(kbytes)}
    for k, v in pins.items():
        if pmap[eid][k] != v:
            problems.append(f"{eid} {k} pin mismatch vs product-map")
    if pmap[eid].get("termsBaselineSha256") != baseline_sha:
        problems.append(f"{eid} map termsBaselineSha256 != disk")

    senses = entry.get("Senses") or []
    base_occs = {(si, oi): o for si, s in
                 enumerate(base.get("Senses") or [], 1) for oi, o in
                 enumerate(s.get("Occurrences") or [], 1)}
    occs = {(si, oi): o for si, s in enumerate(senses, 1) for oi, o in
            enumerate(s.get("Occurrences") or [], 1)}
    prefix_norm, anchor_fixed = [], []
    fixes = {f["occurrence"]: f for f in ANCHOR_FIXES.get(eid, [])}
    for key, o in base_occs.items():
        n = occs.get(key)
        if jcanon(n) == jcanon(o):
            continue
        label = f"s{key[0]}o{key[1]}"
        if n is not None and occ_allowed(o, n, fixes.get(label)):
            if (o.get("AttributionNote") or "") != (n.get("AttributionNote") or ""):
                prefix_norm.append(label)
            if o.get("FromLb") != n.get("FromLb") or o.get("ToLb") != n.get("ToLb"):
                anchor_fixed.append(label)
            continue
        problems.append(f"{eid} baseline occurrence {key} altered")
    added = {k: o for k, o in occs.items() if k not in base_occs}

    doccs = {(si, oi): o for si, s in
             enumerate(draft["Entry"].get("Senses") or [], 1) for oi, o in
             enumerate(s.get("Occurrences") or [], 1)}
    if set(doccs) != set(occs):
        problems.append(f"{eid} draft/entry occurrence misalignment")

    fams: dict[str, int] = {}
    for o in occs.values():
        r = REG.get(o["RelPath"])
        if r:
            fams.setdefault(r["work_id"], int(r.get("Tier")))
    base_works = {o["RelPath"] for o in base_occs.values()}

    added_windows = []
    for (si, oi), o in sorted(added.items()):
        rel = o["RelPath"]
        corpus_files.add(rel)
        kw = o.get("Kwic") or ""
        clause = ((doccs.get((si, oi)) or {}).get("DraftActorProof") or {}
                  ).get("ExactHeadwordClause") or ""
        tier = int((REG.get(rel) or {}).get("Tier", 3))
        clause_in = bool(clause) and strip_ws(clause) in strip_ws(kw)
        aa = o.get("ActorAttribution") or {}
        attributed = bool(o.get("MasterName")) or bool(
            aa.get("Status") and aa.get("ActorLabel"))
        ok = (tier < 3
              and strip_ws(kw) in doc_text(rel)
              and o.get("FromLb") in lb_names(rel)
              and o.get("ToLb") in lb_names(rel)
              and term in kw
              and bool(clause) and clause_in
              and attributed)
        if not ok:
            problems.append(f"{eid} s{si}o{oi} added-window law fails at build")
        added_windows.append({"si": si, "oi": oi, "relPath": rel, "tier": tier,
                              "fromLb": o.get("FromLb"), "toLb": o.get("ToLb"),
                              "kwicLen": len(kw), "kwic": kw,
                              "clauseInKwic": clause_in,
                              "isNewWork": rel not in base_works})

    if not (rep.get("hardPass") and rep.get("outputSha256") == pins["entrySha256"]
            and rep.get("worksheetSha256") == pins["worksheetSha256"]):
        problems.append(f"{eid} receipt chain mismatch at build time")
    if term not in set(public_terms):
        problems.append(f"{eid} term not public — replace contract broken")

    rows.append({
        "kind": "r7-depth-product",
        "entry": eid,
        "term": term,
        "pins": pins,
        "baselineEntrySha256": baseline_sha,
        "entryCanonical": ebytes == canon(entry).encode("utf-8"),
        "idMatchesDerivation": entry["Id"] == "t_" + hashlib.sha256(
            term.encode("utf-8")).hexdigest()[:12] and entry["SourceTerm"] == term,
        "senses": len(senses),
        "occurrencesBefore": len(base_occs),
        "occurrences": len(occs),
        "added": len(added),
        "target": pmap[eid].get("target"),
        "families": [{"workId": w, "tier": t} for w, t in sorted(fams.items())],
        "newWorks": sorted({o["RelPath"] for o in added.values()
                            if o["RelPath"] not in base_works}),
        "addedWindows": added_windows,
        "prefixNormalizedOccurrences": prefix_norm,
        "anchorFixedOccurrences": anchor_fixed,
        "attributionModel": "MasterName or ActorAttribution(Status+ActorLabel) — "
                            "34% of the public termbase uses the latter",
        "receipt": {"hardPass": bool(rep.get("hardPass")),
                    "outputSha256": rep.get("outputSha256"),
                    "worksheetSha256": rep.get("worksheetSha256"),
                    "mode": rep.get("mode")},
        "termInPublic": term in set(public_terms),
    })

assert not problems, problems[:10]
assert len(rows) == 123, len(rows)

(MATS / "receipts.json").write_text(canon(receipts), encoding="utf-8")
manifest = {rel: sha_bytes((XML / rel).read_bytes())
            for rel in sorted(corpus_files)}
(MATS / "corpus-manifest.json").write_text(canon(manifest), encoding="utf-8")
materials_pins = {f.name: sha_bytes(f.read_bytes())
                  for f in sorted(MATS.iterdir()) if f.is_file()}

# ---- plants (fresh delta-tuned set) -------------------------------------------
plants = []


def body_sha(body: dict) -> str:
    return hashlib.sha256(jcanon(body).encode("utf-8")).hexdigest()


def pick(pred, label):
    idx = next(i for i, r in enumerate(rows) if pred(r))
    return idx, json.loads(jcanon(rows[idx])), label


def mk(pred, mutate, label):
    idx, payload, label = pick(pred, label)
    mutate(payload)
    plants.append({"label": label, "rowIndex": idx, "payload": payload,
                   "bindPayloadSha256": body_sha(payload)})


def p_added_kwic_mut(r):
    w = r["addedWindows"][len(r["addedWindows"]) // 2]
    i = w["kwic"].find("。", 40) + 1
    w["kwic"] = w["kwic"][:i] + ("雲" if w["kwic"][i:i+1] != "雲" else "雨") \
        + w["kwic"][i + 1:]


def p_added_kwic_elide(r):
    w = max(r["addedWindows"], key=lambda x: x["kwicLen"])
    k = w["kwic"]
    cut = len(k) - 24
    w["kwic"] = k[:cut - 5] + k[cut + 5:]
    w["kwicLen"] = len(w["kwic"])


def p_baseline_lie(r):
    r["baselineEntrySha256"] = "0" * 8 + r["baselineEntrySha256"][8:]


def p_added_count_off(r):
    r["added"] += 1


def p_added_tier_lie(r):
    w = next(w for w in r["addedWindows"] if w["tier"] == 2)
    w["tier"] = 1


def p_added_clause_lie(r):
    w = next(w for w in reversed(r["addedWindows"]) if w["clauseInKwic"])
    w["clauseInKwic"] = False


mk(lambda r: len(r["addedWindows"]) >= 3
   and r["addedWindows"][len(r["addedWindows"]) // 2]["kwicLen"] > 150,
   p_added_kwic_mut, "added-kwic-mutation")
mk(lambda r: max(w["kwicLen"] for w in r["addedWindows"]) > 300,
   p_added_kwic_elide, "added-kwic-elision")
mk(lambda r: rows.index(r) == 30, p_baseline_lie, "baseline-sha-lie")
mk(lambda r: r["added"] >= 3, p_added_count_off, "added-count-off")
mk(lambda r: any(w["tier"] == 2 for w in r["addedWindows"]),
   p_added_tier_lie, "added-tier-lie")
mk(lambda r: any(w["clauseInKwic"] for w in r["addedWindows"]),
   p_added_clause_lie, "added-clause-lie")

for r in rows:
    r["rowSha"] = body_sha(r)

total = len(rows) + len(plants)
stride = total // (len(plants) + 1)
slots = [stride * (i + 1) for i in range(len(plants))]
assert len(set(slots)) == len(slots)
deck = list(rows)
for slot, p in zip(slots, plants):
    payload = dict(p["payload"])
    payload.pop("rowSha", None)
    payload["rowSha"] = body_sha(payload)
    deck.insert(slot, payload)
    p["slot"] = slot

for i, r in enumerate(deck):
    r["rowId"] = f"r{i:03d}"

rows_doc = {
    "cohort": "fresh10k-r7-depth",
    "round": ROUND,
    "builtUtc": "2026-09-05",
    "lawNote": (
        "Laws: A pins (row's 3 pins == product-map == product bytes); "
        "B canonical; C identity (Id == t_+sha256(SourceTerm)[:12]); "
        "R replace (termInPublic true; baselineEntrySha256 == sha256 of "
        "terms/<id>/entry.v2.json per corpus-manifest-era disk state — "
        "anchored, re-verified at authorize+install; occurrences == "
        "occurrencesBefore + added; baseline occurrences byte-equal "
        "except two permitted normalizations, both listed per row — "
        "prepending the compiler-mandated 'Source record (<RelPath>). ' "
        "AttributionNote prefix (prefixNormalizedOccurrences), and the "
        "adjudicated anchor correction on t_20373fb359ea s1o3 "
        "(anchorFixedOccurrences; coordinator-verified true lb bucket); "
        "D counts (senses; added windows count == added); E families "
        "(per-occurrence registry tiers; each addedWindow's tier equals "
        "the registry tier for its relPath and is < 3; families == the "
        "tier rollup of all occurrence works; "
        "newWorks == added RelPaths absent from the baseline works); "
        "F delta kwic (each "
        "addedWindow kwic byte-equals the product occurrence Kwic; "
        "kwicLen right; From/ToLb exist in the document; ws-stripped "
        "kwic verbatim inside the ws-stripped document-order corpus "
        "text; headword in kwic; clauseInKwic — clause from the draft "
        "proof, ws-stripped, contained in the kwic — must be true; "
        "attribution: MasterName or ActorAttribution with Status+ActorLabel); "
        "G receipt (hardPass; outputSha256 == sha(entry bytes); "
        "worksheetSha256 == sha(evidence.draft.json bytes)); H hygiene "
        "(term IS in public-terms.json — replace mode); Z rowSha == "
        "sha256(canonical-json of body minus rowId/rowSha)."),
    "publicTermsCount": len(public_terms),
    "materialsPins": materials_pins,
    "rows": deck,
}
rows_path = HERE / f"fresh10k-r7-depth-blind-{ROUND}-rows-{STAMP}.json"
rows_path.write_text(canon(rows_doc), encoding="utf-8")

plants_doc = {
    "cohort": "fresh10k-r7-depth",
    "round": ROUND,
    "honestRows": len(rows),
    "registry": [{"label": p["label"], "slot": p["slot"],
                  "bindPayloadSha256": p["bindPayloadSha256"]}
                 for p in plants],
}
(HERE / f"fresh10k-r7-depth-blind-{ROUND}-plants-{STAMP}.json").write_text(
    canon(plants_doc), encoding="utf-8")

print(json.dumps({
    "round": ROUND,
    "rows": len(deck), "honest": len(rows), "plants": len(plants),
    "plantSlots": slots, "corpusFiles": len(corpus_files),
    "addedWindows": sum(r["added"] for r in rows),
    "addedClauseWindows": sum(1 for r in rows for w in r["addedWindows"]
                              if w["clauseInKwic"]),
    "rowsSha256": sha_bytes(rows_path.read_bytes()),
    "materials": len(materials_pins),
}, indent=2))
