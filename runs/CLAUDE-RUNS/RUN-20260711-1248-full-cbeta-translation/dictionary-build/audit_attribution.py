#!/usr/bin/env python3
"""Hard attribution/quotation gate for dictionary entry.v2.json files.

The default scope is every STATUS=done entry. Pass entry files or term
directories explicitly to audit unmerged drafts. This script only reports;
it never edits entries or generated termbase artifacts.
"""

from __future__ import annotations

import argparse
import os
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
ROSTER_PATH = REPO / "Assets" / "Data" / "lineage-masters.json"
PENDING_ROSTER_PATH = HERE / "fresh-build" / "pending-roster.json"

CJK_RE = re.compile(r"[\u3400-\u9fff\uf900-\ufaff]+")
VAGUE_RE = re.compile(
    r"\b(?:a|the|another|one)\s+(?:Chan\s+|Zen\s+)?(?:master|monk|teacher|speaker)\b"
    r"|\bthe text (?:says|asks|calls|describes|records|presents)\b",
    re.IGNORECASE,
)
PLACEHOLDER_ACTOR_RE = re.compile(
    r"\bsection\s+master\s*:"
    r"|\bsection\s+master\b|"
    r"\b(?:the\s+)?(?:fully\s+)?reviewed\s+(?:source\s+)?voice\b"
    r"|\b(?:the\s+)?case-specific\s+unnamed\s+voice\b"
    r"|\b(?:the\s+)?reviewed\s+compilation\s+voice\b"
    r"|\b(?:the\s+)?named\s+section\s+speaker\s+or\s+quoted\s+case\s+voice\b"
    r"|\b(?:the\s+)?verse\s+or\s+address\s+invoking\b"
    r"|\b(?:the\s+)?record[’']s\s+named-book\s+discussion\b"
    r"|\b(?:the\s+)?cited\s+(?:voice|figure|participant)\b"
    r"|\b(?:the\s+)?identified\s+master\b"
    r"|\b(?:the\s+)?presiding\s+speaker\b"
    r"|\b(?:the\s+)?verse\s+voice\b"
    r"|\b(?:the\s+)?case\s+or\s+verse\s+narrator\b"
    r"|\b(?:the\s+)?unresolved\s+(?:quoted\s+)?speaker\b"
    r"|\b(?:the\s+)?generic\s+(?:case\s+)?narrator\b"
    r"|\b(?:the\s+)?source-identified\s+speaker\b"
    r"|\b[A-Z][A-Za-z’' -]{1,80}\s+address\s+master\b"
    r"|\[quoted\s+Chinese\s+marker/clause\]"
    r"|\butters\s+or\s+raises\s+the\s+exact\s+headword-bearing\s+wording\b"
    r"|\b[A-Z]\d+n[A-Z0-9]+\s+section\s+master\b",
    re.IGNORECASE,
)
DUPLICATED_NOTE_PREFIX_RE = re.compile(r"(?:^|[.!?]\s+)([^:.\n]{1,100}):\s*\1:")
DUPLICATED_SOURCE_PREFIX_RE = re.compile(
    r"(?:\bSource\s+(?:record|text)\s*\([^)]*\)\.?\s*){2,}",
    re.IGNORECASE,
)
MALFORMED_UNNAMED_RE = re.compile(r"\bdoes not name\s+(?:an?\s+)?unnamed\b", re.IGNORECASE)
# A full stop immediately before a closing parenthesis is legitimate in
# abbreviations such as ``(Abr.)``.  The old character class treated every
# such source title as broken prose; retain the actual doubled separators.
MALFORMED_NOTE_PUNCTUATION_RE = re.compile(r"(?:\.\s*[:;]+|:\s*,|\)\s*\)\s*\)|\(\s*\))")
ORPHAN_XML_TAIL_RE = re.compile(r"(?<!\()\b[A-Z]/[A-Z0-9/]+\.xml\)\.", re.IGNORECASE)
HEADING_TYPES = {"biography", "poem", "portrait", "raised-case", "section"}
HEADING_DUPLICATION_RE = re.compile(
    r"\b(?:biograph(?:y|ical(?:\s+section)?)|poem|portrait|raised[- ]case|section)\s+heading\s+heading\b",
    re.IGNORECASE,
)


ACTION_PERFORMER_PROOF_RE = re.compile(
    r"\bAction performer:\s*[^.;]{3,100}\s*\((?:identified-unlinked-master|identified-non-master|reviewed-unnamed)\)",
    re.IGNORECASE,
)
CASE_FIGURE_ACTION_PROOF_RE = re.compile(
    r"\b(?:described performer|whose .{0,40}(?:action|gesture)|"
    r"person .{0,40}(?:action|gesture)|performs? (?:the|this|that))\b",
    re.IGNORECASE,
)
NARRATED_PHYSICAL_ACTION_HEADWORD_RE = re.compile(
    r"(?:提起|舉起|拈起|驀?[豎竪]|擲(?:下)?|放下|卓(?:一下)?|拍(?:手|掌)?|"
    r"打|喝|拂|作禮|禮拜|起身|下座|趺坐|端坐|正身端坐|坐|臥|行)"
)


def has_governed_action_performer_context(context_masters, context_actors, grammar_evidence="") -> bool:
    """Require a closed performer identity distinct from the narration voice."""
    roles = {"performer", "action-performer"}
    def performer_context(context):
        if not isinstance(context, dict):
            return False
        assigned = set(context.get("Roles") or [])
        proof = str(context.get("GrammarEvidence") or "")
        return bool(assigned & roles) or (
            "case-figure" in assigned and bool(CASE_FIGURE_ACTION_PROOF_RE.search(proof)))
    if any(performer_context(context) for context in context_masters):
        return True
    return any(
        isinstance(context, dict)
        and context.get("Status") in {
            "identified-unlinked-master", "identified-non-master", "reviewed-unnamed"}
        and bool(str(context.get("ActorLabel") or "").strip())
        and performer_context(context)
        and len(str(context.get("GrammarEvidence") or "").strip()) >= 24
        for context in context_actors
    ) or bool(ACTION_PERFORMER_PROOF_RE.search(str(grammar_evidence or "")))


def narrated_action_performer_missing(term, actor, context_masters, context_actors) -> bool:
    """Flag action headwords whose narrator proof omits the recoverable performer."""
    return bool(
        isinstance(actor, dict)
        and actor.get("Status") == "narrated"
        and NARRATED_PHYSICAL_ACTION_HEADWORD_RE.search(str(term or ""))
        and not has_governed_action_performer_context(
            context_masters, context_actors, actor.get("GrammarEvidence")
        )
    )


def attribution_note_hygiene_failures(note: str, rel: str) -> list[str]:
    """Return deterministic reader-visible scaffolding defects.

    This deliberately checks shape, not actor truth; full-case review remains
    the authority for the latter.  The checks make normalization idempotence
    and one-source-prefix prose enforceable before an expensive review.
    """
    failures = []
    canonical = f"Source record ({rel})."
    if not note.startswith(canonical):
        failures.append("noncanonical-source-opening")
    if len(re.findall(r"\bSource\s+(?:record|text)\b", note, re.IGNORECASE)) != 1:
        failures.append("source-prefix-count")
    if MALFORMED_UNNAMED_RE.search(note):
        failures.append("malformed-unnamed-actor")
    if MALFORMED_NOTE_PUNCTUATION_RE.search(note):
        failures.append("malformed-punctuation")
    if note.count("(") != note.count(")") or note.count("（") != note.count("）"):
        failures.append("unbalanced-parentheses")
    if ORPHAN_XML_TAIL_RE.search(note):
        failures.append("orphan-relpath-tail")
    if re.search(r"\bThe\s+the\b", note):
        failures.append("duplicated-article")
    if HEADING_DUPLICATION_RE.search(note):
        failures.append("duplicated-heading-type")
    # Translation-repair recursion leaves the same phrase immediately nested
    # many times: ``the question says (the question says (...``. Two can occur
    # naturally in quoted prose; three is generated scaffolding, never prose.
    lowered = re.sub(r"\s+", " ", note.lower())
    if re.search(r"([a-z][a-z /'-]{3,60}?)\s*\(\s*\1\s*\(\s*\1\s*\(", lowered):
        failures.append("recursive-translation-expansion")
    return failures


def heading_attribution_failures(row: dict) -> list[str]:
    """Fail closed on typed editorial-heading roles without judging actor truth."""
    actor = row.get("ActorAttribution") or {}
    kind = str(actor.get("Kind") or "").casefold()
    label = str(actor.get("ActorLabel") or "").casefold()
    if "heading" not in kind and "heading" not in label:
        return []
    heading_type = actor.get("HeadingType")
    if heading_type not in HEADING_TYPES:
        return ["heading-type-missing-or-invalid"]
    failures = []
    roles = {
        role
        for context in (row.get("ContextMasters") or []) if isinstance(context, dict)
        for role in (context.get("Roles") or [])
    }
    if "verse-author" in roles and heading_type not in {"poem", "portrait"}:
        failures.append("verse-author-incompatible-with-heading-type")
    if heading_type == "biography" and "verse-author" in roles:
        failures.append("biography-heading-requires-subject-role")
    return failures


def has_english_source_label(note: str, rel: str, actor_markers: list[str]) -> bool:
    """Require visible source identification between the path and actor prose."""
    canonical = f"Source record ({rel})."
    if not note.startswith(canonical):
        return False
    tail = note[len(canonical):].strip()
    # Actor names commonly occur inside an English book title (for example,
    # ``Chushi Fanqi: Sayings``).  Prefer the explicit prose separator so the
    # title's owner is not mistaken for the start of the speaker clause.
    actor_clause = re.search(
        r"\.(?:\s+)(?:Speaker|Compiler narration|Editorial or procedural text|The actor is unnamed|The .+? is unnamed):?\s*",
        tail,
        re.I,
    )
    if actor_clause:
        lead = tail[:actor_clause.start()].strip(" :;,.()")
        words = re.findall(r"[A-Za-z][A-Za-z'-]{2,}", lead)
        return len(words) >= 2 and not re.match(
            r"^(?:the )?(?:source|cited) (?:record|text|title)\b", lead, re.I
        )
    positions = [
        tail.casefold().find(marker.casefold())
        for marker in actor_markers if marker and tail.casefold().find(marker.casefold()) >= 0
    ]
    lead = tail[:min(positions)].strip(" :;,.()") if positions else tail.split(":", 1)[0].strip()
    words = re.findall(r"[A-Za-z][A-Za-z'-]{2,}", lead)
    return len(words) >= 2 and not re.match(r"^(?:the )?(?:source|cited) (?:record|text|title)\b$", lead, re.I)
sys.path.insert(0, str(HERE))
import zc  # noqa: E402

ATTRIBUTION_RUNGS = [
    "line",
    "expanded-context",
    "section-header",
    "book-title",
    "tei-header",
    "parallel-passage",
]
ACTOR_STATUSES = {"identified-non-master", "identified-unlinked-master", "reviewed-unnamed", "narrated", "impersonal"}
EXPLICIT_MASTER_TURN = re.compile(
    r"師(?:(?:示眾|上堂|小參)(?:云|曰|道)"
    r"|(?:乃|遂|復)?(?:云|曰|道|問|答|謂)"
    r"|(?:乃|遂|復)?(?:拈|豎|竪)(?:起拂子)?[，,]?(?:云|曰|道))"
)
# A singular 師 in a case frame identifies a performer who must be resolved.
# Generic plurals such as 諸師拈提語 and 眾師舉揚 do not identify one nameable
# performer and must instead be adjudicated through ActorAttribution.
# 請師舉唱 is a request addressed to a master, not a narrated master action.
EXPLICIT_MASTER_ACTION = re.compile(
    r"(?<![諸眾請])師(?:乃|遂|復)?"
    r"(?:拈|舉|喝|打|指|示|竪|豎|卓|下座|歸方丈|坐|趺坐|端坐|正身端坐|立|行|臥|終|化)"
)
NARRATOR_REPORT_NOTE = re.compile(
    r"\b(?:the\s+)?(?:record narrator|hall record|biographical section|case narrator|compiler)"
    r"\b.{0,100}\breports?\b",
    re.I,
)
RAISED_RECORD_NOTE = re.compile(r"\braises?\s+(?:the\s+)?record\s+of\b", re.I)
ANONYMOUS_MONK_QUESTION = re.compile(r"僧(?:進)?問")
COMPACT_SPEAKER_CUE = re.compile(
    r"(?:師|祖|[一-龥]{1,6})(?:乃|遂|復)?(?:云|曰|道)[：:]?[「『\"]?"
)
RAISED_OLD_SAYING = re.compile(r"(?:古人|古德|先德|祖師)(?:有言|云|曰)")
CLOSED_ROLES = {
    "utterer", "respondent", "questioner", "interlocutor", "addressee",
    "section-subject", "record-owner", "person-described", "person-discussed",
    "commentator", "later-raiser", "later-quoter", "teacher", "student",
    "compiler", "verse-author", "invitation-writer", "case-figure", "performer", "action-performer",
}


def has_evidence_bound_later_quoter(actor: dict | None) -> bool:
    """Do not let a bare ``ActorRole=later-quoter`` launder an old saying.

    A non-master quoter can be the exact surface utterer, but that conclusion
    must carry the same actor identity, six-rung investigation, and grammatical
    turn evidence required elsewhere.  The role string by itself is not proof.
    """
    if not isinstance(actor, dict) or actor.get("ActorRole") != "later-quoter":
        return False
    if actor.get("Status") not in {"reviewed-unnamed", "identified-non-master"}:
        return False
    if not str(actor.get("Kind") or "").strip() or not str(actor.get("ActorLabel") or "").strip():
        return False
    rungs = actor.get("RungsChecked") or []
    if list(rungs) != ATTRIBUTION_RUNGS:
        return False
    grammar = str(actor.get("GrammarEvidence") or "")
    return bool(re.search(
        r"(?:(?:僧|典座|栖|其人|居士|公|士|者)[^，。；]{0,12}(?:問|云|曰|道)"
        r"|assigns|voices|utters|speaks)",
        grammar,
        re.I,
    ))


def note_identifies_named_later_quoter(master: str, note: str) -> bool:
    """Distinguish quotation-raising from physical 拈起/舉起 actions."""
    subject = rf"\b{re.escape(master)}\s+(?:explicitly\s+)?"
    if re.search(subject + r"(?:quotes|cites)\b", note, re.IGNORECASE):
        return True
    return bool(re.search(
        subject + r"raises\s+(?:an?\s+|the\s+)?(?:old\s+|earlier\s+|quoted\s+|inherited\s+)?"
        r"(?:saying|case|verse|words?|statement|question|reply|exchange)\b",
        note,
        re.IGNORECASE,
    ))


def explicit_master_turns_before_headword(term: str, kwic_text: str) -> list[str]:
    """Return only master speech cues that govern text before the headword.

    A cue in the lexical item itself (for example 答話) is not syntax, and a
    following 師云 belongs to the response rather than backward to a question.
    """
    clauses = [
        clause for clause in re.split(r"[。！？；\n]", kwic_text)
        if term and term in clause
    ]
    return sorted({
        match.group(0)
        for clause in clauses
        for match in EXPLICIT_MASTER_TURN.finditer(clause[:clause.find(term)].replace(term, ""))
    })


def anonymous_monk_question_governs_headword(term: str, clause: str) -> bool:
    """Return true only when the monk's question is the nearest speech turn.

    Punctuation-poor records can place several complete exchanges in one
    apparent clause.  A bare ``僧問`` anywhere before the headword therefore
    cannot bind the headword backward across an intervening ``師云`` or compact
    named cue such as ``祖云`` / ``頭云``.  This nearest-turn rule preserves a
    genuine ``僧問 ... HEADWORD`` while preventing distant questions from
    stealing a later master's response.
    """
    headword_at = clause.find(term)
    if headword_at < 0:
        return False
    prefix = clause[:headword_at]
    questions = list(ANONYMOUS_MONK_QUESTION.finditer(prefix))
    if not questions:
        return False
    last_question = questions[-1]
    return not any(
        cue.start() > last_question.start()
        for cue in COMPACT_SPEAKER_CUE.finditer(prefix)
    )


def has_exact_actor_context(master: str | None, context_masters: object) -> bool:
    """Accept a named headword actor only under its exact closed actor role."""
    return bool(master and isinstance(context_masters, list) and any(
        isinstance(context, dict)
        and context.get("MasterName") == master
        and set(context.get("Roles") or []) & {
            "utterer", "verse-author", "performer", "action-performer"
        }
        for context in context_masters
    ))


def ambiguous_headword_span(term: str, kwic: str, review: object = None) -> bool:
    """Multi-graph terms need one target span or a proved one-turn repetition."""
    count = kwic.count(term)
    if len(term) < 2 or count == 1:
        return False
    if count > 1 and isinstance(review, dict):
        return not (
            review.get("Count") == count
            and review.get("Disposition") == "single-actor-single-turn-repetition"
            and bool(str(review.get("GrammarEvidence") or "").strip())
        )
    return True


def valid_governed_variant(occurrence: dict) -> bool:
    """A variant exemption is explicit and its exact governed surface is visible."""
    variant = str(occurrence.get("VariantForm") or "")
    return bool(
        occurrence.get("EvidenceRole") == "variant"
        and occurrence.get("VariantKind") in {"editorial-punctuation", "governed-graphic"}
        and variant
        and variant in str(occurrence.get("Kwic") or "")
    )


def public_actor_label(value: object) -> str:
    text = CJK_RE.sub("", str(value or ""))
    return re.sub(r"\s+", " ", text).strip(" ,;:-")


def roster_names() -> set[str]:
    data = json.loads(ROSTER_PATH.read_text(encoding="utf-8"))
    masters = data if isinstance(data, list) else data["masters"]
    return {m["names"][0] for m in masters}


def roster_aliases() -> dict[str, str]:
    """Map every exact roster alias to names[0] without mutating the roster."""
    data = json.loads(ROSTER_PATH.read_text(encoding="utf-8"))
    masters = data if isinstance(data, list) else data["masters"]
    aliases = {}
    for master in masters:
        canonical = master["names"][0]
        for name in master.get("names") or []:
            aliases[str(name).strip().casefold()] = canonical
    return aliases


def pending_roster_names(path: Path = PENDING_ROSTER_PATH) -> set[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return set()
    valid = set()
    for row in data.get("candidates") or []:
        if (row.get("status") != "awaiting-roster-integration"
                or not row.get("canonicalName") or not row.get("aliases")
                or not row.get("evidence") or not row.get("reviewedBy")
                or not row.get("reviewReport")
                or CJK_RE.search(str(row.get("canonicalName")))):
            continue
        evidence_ok = True
        for evidence in row.get("evidence") or []:
            verification = zc.verify(str(evidence.get("RelPath") or ""), str(evidence.get("Kwic") or ""))
            if (not verification.get("ok")
                    or verification.get("fromLb") != evidence.get("FromLb")
                    or (evidence.get("ToLb") and verification.get("toLb") != evidence.get("ToLb"))):
                evidence_ok = False
                break
        if evidence_ok:
            valid.add(str(row["canonicalName"]))
    return valid


def default_files() -> list[Path]:
    out = []
    for entry in HERE.glob("terms/*/entry.v2.json"):
        status = entry.parent / "STATUS"
        if status.exists() and status.read_text(encoding="utf-8").strip() == "done":
            out.append(entry)
    return sorted(out)


def resolve_files(args: list[str]) -> list[Path]:
    if not args:
        return default_files()
    out = []
    for raw in args:
        path = Path(raw)
        if path.is_dir():
            direct = path / "entry.v2.json"
            if direct.exists():
                out.append(direct.resolve())
                continue
            for entry in path.glob("*/entry.v2.json"):
                status = entry.parent / "STATUS"
                if status.exists() and status.read_text(encoding="utf-8-sig").strip() == "done":
                    out.append(entry.resolve())
            continue
        out.append(path.resolve())
    return sorted(set(out))


def chinese_strings(text: str) -> set[str]:
    """Return Chinese strings presented as prose evidence.

    Single-character strings are included: entries for graphs such as 佛 and
    無 may rely on them. A string is considered anchored when it occurs in a
    stored KWIC (or contains a stored KWIC phrase), with punctuation ignored
    by the maximal-CJK extraction.
    """
    return set(CJK_RE.findall(text or ""))


def uniform_actor_placeholder_failure(
    entry_count: int,
    named_count: int,
    signatures: Counter,
) -> dict[str, object] | None:
    """Reject cohort-wide actor defaults before independent review pays for them.

    This is deliberately a cohort canary, not an actor classifier. A uniform
    result across five or more independently selected headwords can be real,
    but it is too dangerous to accept without an explicit batch-level review.
    """
    total = sum(signatures.values())
    if entry_count < 5 or named_count or not total or len(signatures) != 1:
        return None
    signature, amount = signatures.most_common(1)[0]
    return {
        "kind": "batch-uniform-actor-placeholder",
        "entry": "<cohort>",
        "detail": (
            f"{entry_count} entries / {amount} occurrences share one actor signature "
            f"{signature!r} and contain no named utterer"
        ),
    }


def anonymous_actor_collapse_failure(
    entry_count: int,
    named_count: int,
    signatures: Counter,
) -> dict[str, object] | None:
    """Flag large cohorts whose actor adjudication collapses into anonymity.

    A token handful of names must not disable the canary for hundreds of
    narrator/default labels.  This is a review stop, not a claim that any
    individual occurrence must have a named utterer.
    """
    total = sum(signatures.values())
    narrated = sum(amount for signature, amount in signatures.items() if signature and signature[0] == "narrated")
    all_occurrences = total + named_count
    named_share = named_count / all_occurrences if all_occurrences else 0.0
    if entry_count < 10 or total < 30 or named_share >= 0.15:
        return None
    return {
        "kind": "batch-anonymous-actor-collapse",
        "entry": "<cohort>",
        "detail": (
            f"{entry_count} entries / {all_occurrences} occurrences contain only {named_count} named "
            f"utterers ({named_share:.1%}); "
            f"status labels cannot substitute for full-case name resolution "
            f"({narrated} narrated, {total - narrated} other anonymous)"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", help="entry.v2.json files or term dirs")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--output", type=Path, help="also write the complete JSON result atomically")
    parser.add_argument("--exclude-id", action="append", default=[], help="omit an entry Id (repeatable)")
    parser.add_argument("--strict-roster", action="store_true", help="fail every MasterName/ContextMasters value not equal to roster names[0]")
    parser.add_argument("--strict-roster-id", action="append", default=[], help="apply strict roster linking only to these repaired entry IDs")
    parser.add_argument("--pending-roster", type=Path, default=PENDING_ROSTER_PATH,
                        help="validated pending-roster candidate packet (defaults to the shared packet)")
    ns = parser.parse_args()

    files = resolve_files(ns.paths)
    if ns.exclude_id:
        excluded = set(ns.exclude_id)
        files = [p for p in files if p.parent.name not in excluded]
    roster = roster_names()
    roster_alias_map = roster_aliases()
    roster_name_pattern = re.compile(
        "|".join(re.escape(name) for name in sorted(roster, key=len, reverse=True))
    ) if roster else None
    pending_roster = pending_roster_names(ns.pending_roster)
    strict_ids = set(ns.strict_roster_id)
    title_cache: dict[str, str | None] = {}
    failures: list[dict[str, object]] = []
    counts = Counter(entries=len(files))
    batch_actor_signatures = Counter()
    batch_named = 0

    def fail(kind: str, entry: Path, detail: str) -> None:
        failures.append({"kind": kind, "entry": str(entry), "detail": detail})
        counts[kind] += 1

    for entry in files:
        data = json.loads(entry.read_text(encoding="utf-8"))
        # Fresh construction is reader-link production, not legacy diagnosis:
        # every link-bearing master field must already equal roster names[0].
        # A source-attested but unlinked master belongs in ActorAttribution or
        # other descriptive prose, never in MasterName/ContextMasters.
        strict_roster_here = (
            ns.strict_roster
            or data.get("Id") in strict_ids
            or "fresh-build" in entry.parts
        )
        term = data.get("SourceTerm", entry.parent.name)
        for si, sense in enumerate(data.get("Senses", []), 1):
            counts["senses"] += 1
            for related in sense.get("RelatedMasters") or []:
                if not isinstance(related, str) or not related.strip():
                    fail(
                        "invalid_related_master",
                        entry,
                        f"{term} s{si}: RelatedMasters values must be nonempty master-name strings, got {related!r}",
                    )
                    continue
                if strict_roster_here and related not in roster:
                    fail(
                        "noncanonical_related_master",
                        entry,
                        f"{term} s{si}: RelatedMasters value {related!r} is not roster-canonical",
                    )
            occs = sense.get("Occurrences") or []
            anchors = sense.get("ClaimAnchors") or []
            evidence_rows = [("o", o) for o in occs] + [("a", o) for o in anchors]
            kwics = [o.get("Kwic") or "" for _, o in evidence_rows]
            for oi, (evidence_kind, occ) in enumerate(evidence_rows, 1):
                counts["occurrences" if evidence_kind == "o" else "claim_anchors"] += 1
                evidence_label = f"{evidence_kind}{oi}"
                if evidence_kind == "a":
                    verification = zc.verify(str(occ.get("RelPath") or ""), str(occ.get("Kwic") or ""))
                    if (not verification.get("ok")
                            or verification.get("fromLb") != occ.get("FromLb")
                            or verification.get("toLb") != occ.get("ToLb")):
                        fail("invalid_claim_anchor", entry, f"{term} s{si} {evidence_label}: {verification}")
                master = occ.get("MasterName")
                actor = occ.get("ActorAttribution")
                if master:
                    batch_named += 1
                    counts["named_occurrences"] += 1
                    if actor:
                        fail("conflicting_actor_state", entry, f"{term} s{si} {evidence_label}: named actor also has ActorAttribution")
                    if master not in roster:
                        # Roster expansion is owned by a parallel agent. Preserve
                        # source-attested names and report them without blocking
                        # entry remediation; re-enable the roster gate after the
                        # expanded roster is integrated.
                        counts["deferred_non_roster"] += 1
                        if strict_roster_here:
                            fail("noncanonical_master_name", entry, f"{term} s{si} {evidence_label}: {master!r} is not roster names[0]")
                        elif master in pending_roster:
                            counts["pending_roster_master"] += 1
                elif isinstance(actor, dict):
                    batch_actor_signatures[(actor.get("Status"), actor.get("Kind"), actor.get("ActorLabel"), actor.get("ActorRole"))] += 1
                    status = actor.get("Status")
                    if status not in ACTOR_STATUSES:
                        fail("invalid_actor_status", entry, f"{term} s{si} o{oi}: {status!r}")
                    else:
                        counts[f"actor_{status.replace('-', '_')}"] += 1
                    for field in ("Kind", "ActorLabel", "ActorRole", "ReviewedBy", "ReviewedUtc"):
                        if not actor.get(field):
                            fail("incomplete_actor_attribution", entry, f"{term} s{si} o{oi}: missing {field}")
                    for field in ("Kind", "ActorLabel", "GrammarEvidence"):
                        value = str(actor.get(field) or "")
                        if PLACEHOLDER_ACTOR_RE.search(value):
                            fail("placeholder_actor_forbidden", entry, f"{term} s{si} {evidence_label} {field}: {value!r}")
                    if actor.get("ActorRole") and actor.get("ActorRole") not in CLOSED_ROLES:
                        fail("invalid_actor_role", entry, f"{term} s{si} o{oi}: {actor.get('ActorRole')!r}")
                    if status not in {"identified-unlinked-master", "identified-non-master"} and re.search(
                        r"master|teacher|禪師|和尚",
                        " ".join(str(actor.get(field) or "") for field in ("Kind", "ActorLabel")),
                        re.IGNORECASE,
                    ):
                        fail("unnamed_master_forbidden", entry, f"{term} s{si} o{oi}: every master must be named")
                    if status == "identified-non-master" and re.search(
                        r"record[- ]owner|record owner|語錄主", " ".join(
                            str(actor.get(field) or "") for field in ("Kind", "ActorLabel", "GrammarEvidence")
                        ), re.IGNORECASE
                    ):
                        fail("record_owner_misclassified_non_master", entry,
                             f"{term} s{si} o{oi}: resolve the named record owner against the roster and exact turn")
                    if re.search(
                        r"speaking\s+record[- ]owner|current\s+record[- ]owner(?:['’]s)?\s+address",
                        " ".join(str(actor.get(field) or "") for field in
                                 ("Kind", "ActorLabel", "GrammarEvidence")),
                        re.IGNORECASE,
                    ):
                        fail("record_owner_utterer_unresolved", entry,
                             f"{term} s{si} o{oi}: a speaking record owner is a master; resolve the exact name")
                    if status == "identified-non-master" and re.match(
                        r"^(?:the|an?|one|some)\b", str(actor.get("ActorLabel") or "").strip(), re.IGNORECASE
                    ):
                        fail(
                            "identified_actor_not_named", entry,
                            f"{term} s{si} o{oi}: identified-non-master requires the actor's actual name; "
                            f"use reviewed-unnamed plus all six rungs when the source supplies only a role: "
                            f"{actor.get('ActorLabel')!r}",
                        )
                    if status == "identified-unlinked-master":
                        label = str(actor.get("ActorLabel") or "").strip()
                        alias_key = label.casefold()
                        public_key = public_actor_label(label).casefold()
                        canonical_alias = roster_alias_map.get(alias_key) or roster_alias_map.get(public_key)
                        if canonical_alias:
                            fail("roster_alias_used_as_unlinked", entry,
                                 f"{term} s{si} o{oi}: {label!r} resolves to roster names[0] {canonical_alias!r}; use the canonical MasterName")
                        if re.match(r"^(?:the|an?|one|some|unnamed)\b", label, re.IGNORECASE):
                            fail("identified_unlinked_master_not_named", entry,
                                 f"{term} s{si} o{oi}: explicit Chinese/English source identity required: {label!r}")
                        if actor.get("RungsChecked") != ATTRIBUTION_RUNGS:
                            fail("identified_unlinked_master_incomplete_rungs", entry,
                                 f"{term} s{si} o{oi}: all six ordered rungs required")
                        # DraftActorProof is compiler-validated and intentionally
                        # omitted from the public product. GrammarEvidence is the
                        # surviving, reader-auditable exact-turn proof.
                        proof_text = str(actor.get("GrammarEvidence") or "")
                        if not label or label not in proof_text:
                            fail("identified_unlinked_master_unsupported_identity", entry,
                                 f"{term} s{si} o{oi}: ActorLabel must be repeated in surviving exact-turn GrammarEvidence")
                    if status == "reviewed-unnamed" and actor.get("RungsChecked") != ATTRIBUTION_RUNGS:
                        fail("incomplete_actor_rungs", entry, f"{term} s{si} o{oi}: expected all six ordered rungs")
                    if status == "reviewed-unnamed" and actor.get("ActorRole") == "utterer" and not re.search(
                        r"僧|客|居士|官|婆|童|侍者|問者|行者|沙彌|lay(?:man|woman|person)?|monk|questioner|official|visitor|woman|child|attendant|novice|verse author|compiler",
                        str(actor.get("GrammarEvidence") or ""), re.IGNORECASE,
                    ):
                        fail(
                            "unnamed_utterer_nonmaster_cue_missing", entry,
                            f"{term} s{si} o{oi}: reviewed-unnamed utterer lacks concrete evidence that the source presents a non-master actor",
                        )
                    if status == "reviewed-unnamed" and not re.search(
                        r"\bunnamed\b|does not name", str(actor.get("ActorLabel") or ""), re.IGNORECASE
                    ):
                        fail("reviewed_unnamed_label_not_explicit", entry,
                             f"{term} s{si} o{oi}: reviewed-unnamed ActorLabel must explicitly say unnamed")
                    if status in {"identified-non-master", "identified-unlinked-master", "narrated", "impersonal"} and not actor.get("GrammarEvidence"):
                        fail("missing_grammar_evidence", entry, f"{term} s{si} o{oi}")
                else:
                    fail("unresolved_actor", entry, f"{term} s{si} o{oi} {occ.get('RelPath')}:{occ.get('FromLb')}")

                kwic_text = str(occ.get("Kwic") or "")
                if "fresh-build" in entry.parts and len(kwic_text) > 600:
                    fail(
                        "overbroad_fresh_kwic",
                        entry,
                        f"{term} s{si} o{oi}: {len(kwic_text)} characters; recut to the bounded "
                        "headword-bearing turn before exact verification",
                    )
                declared_variant = str(occ.get("VariantForm") or "")
                valid_variant = valid_governed_variant(occ)
                if evidence_kind == "o" and not valid_variant and ambiguous_headword_span(
                    term, kwic_text, occ.get("HeadwordSpanReview")
                ):
                    fail(
                        "ambiguous_headword_span_in_kwic", entry,
                        f"{term} s{si} o{oi}: expected exactly one headword span in the reader KWIC, "
                        f"found {kwic_text.count(term)}; re-cut the exact turn before assigning its actor",
                    )
                headword_clauses = [
                    clause for clause in re.split(r"[。！？；\n]", kwic_text)
                    if term and term in clause
                ]
                explicit_turns = explicit_master_turns_before_headword(term, kwic_text)
                # Long punctuation-poor lamp-record KWICs may contain an
                # earlier 師云/師曰 before a later narrator clause or an
                # explicitly introduced monk's question.  A completed human
                # grammar adjudication for those two actor classes outranks
                # that coarse cue; this is not available to generic unnamed
                # speech and therefore cannot launder an unnamed master.
                reviewed_grammar_override = bool(
                    isinstance(actor, dict)
                    and actor.get("ReviewedBy")
                    and actor.get("GrammarEvidence")
                    and (
                        actor.get("Status") == "narrated"
                        or (
                            actor.get("Status") == "identified-unlinked-master"
                            and str(actor.get("ActorLabel") or "").strip()
                            and list(actor.get("RungsChecked") or []) == ATTRIBUTION_RUNGS
                            and str(actor.get("ActorLabel"))
                                in str(actor.get("GrammarEvidence") or "")
                        )
                        or (
                            actor.get("Status") == "reviewed-unnamed"
                            and actor.get("ActorRole") == "questioner"
                            and re.search(r"(?:僧問|問 introduces|headword-bearing question)",
                                          str(actor.get("GrammarEvidence") or ""), re.IGNORECASE)
                        )
                        or (
                            actor.get("Status") == "identified-non-master"
                            and actor.get("ActorRole") == "case-figure"
                            and str(actor.get("ActorLabel") or "").strip()
                            and list(actor.get("RungsChecked") or []) == ATTRIBUTION_RUNGS
                            and str(actor.get("ActorLabel"))
                                in str(actor.get("GrammarEvidence") or "")
                            and re.search(r"(?:曰|云|quoted answer containing)",
                                          str(actor.get("GrammarEvidence") or ""), re.IGNORECASE)
                        )
                    )
                )
                if explicit_turns and not master and not reviewed_grammar_override:
                    fail(
                        "explicit_master_turn_left_anonymous",
                        entry,
                        f"{term} s{si} o{oi}: {explicit_turns}; read the complete case and name the exact master",
                    )

                explicit_actions = sorted({
                    match.group(0)
                    for clause in headword_clauses
                    for match in EXPLICIT_MASTER_ACTION.finditer(clause)
                })
                if explicit_actions and not explicit_turns and master:
                    fail(
                        "action_performer_in_utterer_field",
                        entry,
                        f"{term} s{si} o{oi}: {explicit_actions}; MasterName is utterer-only, "
                        "so represent the narrated performer in ContextMasters",
                    )

                anonymous_question = any(
                    anonymous_monk_question_governs_headword(term, clause)
                    for clause in headword_clauses
                )
                if anonymous_question and master:
                    fail(
                        "anonymous_monk_question_assigned_to_master",
                        entry,
                        f"{term} s{si} o{oi}: 僧問 owns the headword-bearing question; "
                        "the responding master belongs in ContextMasters",
                    )

                # A common compact record frame assigns the headword to the
                # anonymous participant and introduces the master's response
                # only afterwards: 僧云/問 ... HEADWORD ... 師云.  Do not let
                # record ownership or the trailing 師云 bind backward.
                nonmaster_before_master_reply = any(
                    (
                        re.search(r"(?:僧(?:云|曰)|(?:^|[。；])問[：:]?[「『\"]?)", clause[:clause.find(term)])
                        and re.search(r"師(?:云|曰|道)", clause[clause.find(term) + len(term):])
                        and not explicit_master_turns_before_headword(term, clause)
                    )
                    for clause in headword_clauses
                )
                if nonmaster_before_master_reply and master:
                    fail(
                        "nonmaster_turn_assigned_backward_to_master",
                        entry,
                        f"{term} s{si} o{oi}: 僧云/問 owns the headword-bearing turn; "
                        "the master introduced afterward belongs in ContextMasters",
                    )

                # Reader prose often states the decisive distinction more
                # clearly than compact punctuation: ``X quotes Y's verdict``
                # means X is the later quoter/commentator, not the original
                # utterer of the quoted headword.  Never allow the quoter's
                # roster link to overwrite the named quoted speaker merely
                # because the quotation appears inside X's record.
                note = str(occ.get("AttributionNote") or "")
                if master and (NARRATOR_REPORT_NOTE.search(note) or RAISED_RECORD_NOTE.search(note)):
                    fail(
                        "narrated_action_in_utterer_field",
                        entry,
                        f"{term} s{si} o{oi}: AttributionNote assigns the headword-bearing "
                        "action to narration or a raised record; MasterName is utterer-only",
                    )
                named_quoter_in_master = bool(master and note_identifies_named_later_quoter(master, note))
                if named_quoter_in_master:
                    fail(
                        "named_quoter_in_utterer_field",
                        entry,
                        f"{term} s{si} o{oi}: AttributionNote identifies {master} as the later "
                        "quoter/raiser; resolve the quoted speaker as MasterName and retain the "
                        "present master in ContextMasters",
                    )

                raised_old_saying = any(
                    RAISED_OLD_SAYING.search(clause[:clause.find(term)])
                    for clause in headword_clauses
                )

                context_masters = occ.get("ContextMasters") or []
                if not isinstance(context_masters, list):
                    fail("invalid_context_masters", entry, f"{term} s{si} o{oi}: not a list")
                    context_masters = []
                for ci, context in enumerate(context_masters, 1):
                    if not isinstance(context, dict) or not context.get("MasterName") or not context.get("Roles"):
                        fail("invalid_context_master", entry, f"{term} s{si} o{oi} c{ci}")
                        continue
                    counts["context_master_links"] += 1
                    invalid_roles = sorted(set(context.get("Roles") or []) - CLOSED_ROLES)
                    if invalid_roles:
                        fail("invalid_context_roles", entry, f"{term} s{si} o{oi} c{ci}: {invalid_roles}")
                    if context["MasterName"] not in roster:
                        counts["deferred_non_roster_context"] += 1
                        if strict_roster_here:
                            fail("noncanonical_context_master_name", entry, f"{term} s{si} o{oi} c{ci}: {context['MasterName']!r} is not roster names[0]")
                        elif context["MasterName"] in pending_roster:
                            counts["pending_roster_context_master"] += 1
                context_actors = occ.get("ContextActors") or []
                if not isinstance(context_actors, list):
                    fail("invalid_context_actors", entry, f"{term} s{si} o{oi}: not a list")
                    context_actors = []
                for ci, context in enumerate(context_actors, 1):
                    if not isinstance(context, dict):
                        fail("invalid_context_actor", entry, f"{term} s{si} o{oi} a{ci}: object required")
                        continue
                    label = str(context.get("ActorLabel") or "").strip()
                    status = context.get("Status")
                    roles = context.get("Roles") or []
                    proof = str(context.get("GrammarEvidence") or "").strip()
                    counts["context_actor_identities"] += 1
                    if status not in {
                            "identified-unlinked-master", "identified-non-master",
                            "reviewed-unnamed"} or not label:
                        fail("invalid_context_actor", entry, f"{term} s{si} o{oi} a{ci}: closed status and explicit label required")
                    if status == "identified-unlinked-master" and label in roster:
                        fail("linked_identity_in_context_actors", entry, f"{term} s{si} o{oi} a{ci}: {label!r} belongs in ContextMasters")
                    canonical_alias = roster_alias_map.get(label.casefold()) or roster_alias_map.get(public_actor_label(label).casefold())
                    if status == "identified-unlinked-master" and canonical_alias:
                        fail("roster_alias_used_in_context_actors", entry,
                             f"{term} s{si} o{oi} a{ci}: {label!r} resolves to roster names[0] {canonical_alias!r}; use ContextMasters")
                    invalid_roles = sorted(set(roles) - CLOSED_ROLES)
                    if not roles or invalid_roles or "utterer" in roles:
                        fail("invalid_context_actor_roles", entry, f"{term} s{si} o{oi} a{ci}: {roles!r}")
                    if len(proof) < 24:
                        fail("context_actor_proof_missing", entry, f"{term} s{si} o{oi} a{ci}: case-specific proof required")
                    public_label = re.sub(r"[\u3400-\u9fff\uf900-\ufaff]+", "", label).strip(" ,;:-") or label
                    if public_label.casefold() not in note.casefold():
                        fail("context_actor_missing_from_note", entry, f"{term} s{si} o{oi} a{ci}: {public_label!r} must appear in AttributionNote")
                if raised_old_saying and not has_evidence_bound_later_quoter(actor) and not any(
                    "later-raiser" in (context.get("Roles") or [])
                    for context in context_masters if isinstance(context, dict)
                ):
                    fail(
                        "raised_old_saying_lacks_raiser",
                        entry,
                        f"{term} s{si} o{oi}: 古人/古德/先德/祖師云 marks quoted precedent; "
                        "name the present speaker as later-raiser and resolve the quoted utterer separately",
                    )
                if explicit_actions and not explicit_turns and not has_governed_action_performer_context(
                    context_masters, context_actors, actor.get("GrammarEvidence") if isinstance(actor, dict) else ""
                ):
                    fail(
                        "action_performer_context_missing",
                        entry,
                        f"{term} s{si} o{oi}: explicit master action requires the named performer as "
                        "person-described or case-figure; finer action detail belongs in GrammarEvidence",
                    )
                if narrated_action_performer_missing(term, actor, context_masters, context_actors):
                    fail(
                        "narrated_action_performer_missing",
                        entry,
                        f"{term} s{si} o{oi}: narrated physical action records only the narrator/recorder; "
                        "bind the recoverable performer separately as ContextMasters/ContextActors or with "
                        "an explicit closed Action performer proof in GrammarEvidence",
                    )
                if master and not has_exact_actor_context(master, context_masters):
                    fail("missing_utterer_context", entry, f"{term} s{si} o{oi}: {master}")

                if evidence_kind == "o" and term not in str(occ.get("Kwic") or ""):
                    counts["supporting_occurrences"] += 1
                    variant = str(occ.get("VariantForm") or "")
                    if valid_governed_variant(occ):
                        counts["governed_variant_occurrences"] += 1
                    else:
                        fail("headword_absent_from_kwic", entry, f"{term} s{si} o{oi}: re-cut or replace; only an exact declared VariantForm with EvidenceRole=variant is exempt")
                if evidence_kind == "a":
                    claim_text = str(occ.get("ClaimText") or "")
                    if not claim_text:
                        fail("claim_anchor_missing_claim_text", entry, f"{term} s{si} {evidence_label}")
                    elif claim_text not in str(occ.get("Kwic") or ""):
                        fail("claim_text_absent_from_kwic", entry, f"{term} s{si} {evidence_label}: {claim_text}")
                    if term and term in claim_text:
                        fail("claim_anchor_contains_headword", entry, f"{term} s{si} {evidence_label}: evidence containing the headword must be an Occurrence")

                note = (occ.get("AttributionNote") or "").strip()
                if not note:
                    fail("missing_attribution_note", entry, f"{term} s{si} o{oi}")
                else:
                    counts["attribution_notes"] += 1
                    for hygiene_failure in attribution_note_hygiene_failures(note, str(occ.get("RelPath") or "")):
                        fail("attribution_note_prose_hygiene", entry,
                             f"{term} s{si} {evidence_label} {hygiene_failure}: {note!r}")
                    for heading_failure in heading_attribution_failures(occ):
                        fail("heading_attribution_role_hygiene", entry,
                             f"{term} s{si} {evidence_label} {heading_failure}")
                    actor_marker = str(master or "").strip()
                    if isinstance(actor, dict):
                        status = actor.get("Status")
                        label = str(actor.get("ActorLabel") or "").strip()
                        if status == "reviewed-unnamed" and label:
                            subject = re.sub(r"^(?:the\s+)?unnamed\s+", "", label, flags=re.I).strip()
                            actor_marker = f"The {subject} is unnamed" if subject != label else "The actor is unnamed"
                        elif status == "narrated":
                            # The guide's note law bans publishing the
                            # "Compiler narration:" label; guide-compliant
                            # notes name the narrator-class actor in prose.
                            # When the banned label is absent, fall back to
                            # the actor label so the marker-offset scan still
                            # excludes the work title; the fail-closed
                            # whole-note scan then only triggers when the
                            # note genuinely fails to name its actor.
                            actor_marker = "Compiler narration"
                            if actor_marker not in note:
                                actor_marker = (
                                    label if label and label in note
                                    else public_actor_label(label)
                                )
                        elif status == "impersonal":
                            actor_marker = "Editorial or procedural text"
                        else:
                            actor_marker = label if label in note else public_actor_label(label)
                    if not has_english_source_label(
                        note, str(occ.get("RelPath") or ""), [str(master or ""), actor_marker, "Exact actor"]
                    ):
                        fail("note_missing_english_source_label", entry,
                             f"{term} s{si} {evidence_label}: name the source in English between RelPath and actor: {note!r}")
                    if DUPLICATED_NOTE_PREFIX_RE.search(note) or DUPLICATED_SOURCE_PREFIX_RE.search(note):
                        fail("duplicated_attribution_note_prefix", entry,
                             f"{term} s{si} {evidence_label} AttributionNote: {note!r}")
                    if PLACEHOLDER_ACTOR_RE.search(note):
                        fail("placeholder_actor_forbidden", entry, f"{term} s{si} {evidence_label} AttributionNote: {note!r}")
                    represented = {str(master)} if master else set()
                    represented.update(
                        str(context.get("MasterName"))
                        for context in context_masters if isinstance(context, dict) and context.get("MasterName")
                    )
                    actor_text = json.dumps(actor, ensure_ascii=False) if isinstance(actor, dict) else ""
                    actor_label = str((actor or {}).get("ActorLabel") or "").strip()
                    # The authoritative work-title segment can itself contain
                    # a master's name (for example, "Recorded Sayings of Chan
                    # Master Huqiu Shaolong").  That names the work, not a
                    # participant in this evidence row.  Search only from the
                    # already-computed actor marker onward; structured actor
                    # JSON remains in scope.  Falling back to the whole note is
                    # deliberately fail-closed when the note has no marker.
                    actor_note = note
                    if actor_marker:
                        marker_at = note.casefold().find(actor_marker.casefold())
                        if marker_at >= 0:
                            actor_note = note[marker_at:]
                    named_in_prose = set(roster_name_pattern.findall(actor_note + " " + actor_text)) if roster_name_pattern else set()
                    missing_named_context = sorted(
                        name for name in (named_in_prose - represented)
                        # A named lay/official/non-master must be printed in
                        # ActorLabel and the reader note, but must never be
                        # smuggled into MasterName/ContextMasters merely
                        # because a broad roster alias table also contains the
                        # string.  The XOR branch itself is the structured
                        # representation for this actor class.
                        if not (
                            isinstance(actor, dict)
                            and actor.get("Status") in {"identified-non-master", "identified-unlinked-master"}
                            and name in actor_label
                        )
                        if not any(
                            len(linked) > len(name) and name in linked
                            and (linked in note or linked in actor_text)
                            for linked in represented
                        )
                    )
                    for missing_name in missing_named_context:
                        fail(
                            "named_master_missing_structured_link",
                            entry,
                            f"{term} s{si} {evidence_label}: {missing_name} appears in attribution prose "
                            "but not in MasterName or ContextMasters",
                        )
                    # Unicode ``\b`` has no useful boundary between Han graphs;
                    # source-attested Chinese roster candidates therefore looked
                    # absent even when the exact full name was printed in the note.
                    speaker_named = bool(master and (
                        master in note if CJK_RE.search(str(master))
                        else re.search(rf"\b{re.escape(master)}\b", note)
                    ))
                    rel = occ.get("RelPath") or ""
                    if rel not in title_cache:
                        title_cache[rel] = zc.title(rel)
                    title = title_cache[rel]
                    # Attribution notes are public English prose. Requiring the
                    # exact Chinese manifest title here contradicted the
                    # English-first/CJK prose gate. An exact RelPath is an
                    # unambiguous, linkable source identity and is therefore the
                    # preferred proof; legacy parenthesized Chinese titles remain
                    # accepted during migration.
                    source_named = bool((title and title in note) or (rel and rel in note))
                    # The reviewed non-master branch also covers a personally
                    # named lay/questioning actor whom MasterName cannot link as
                    # a roster master. In that outcome the reader note must name
                    # the ActorLabel rather than falsely calling the person
                    # anonymous.
                    exception_named = bool(actor and (
                        (actor_label and re.search(re.escape(actor_label), note, re.IGNORECASE))
                        or (
                            actor.get("Status") == "reviewed-unnamed"
                            and re.search(r"\bunnamed\b|does not name", note, re.IGNORECASE)
                        )
                        or (
                            actor.get("Status") in {"narrated", "impersonal"}
                            and re.search(
                                r"interval|elapsed|nonresponse|scene|narrat|document|scripture|voice|"
                                r"heading|procedur|biograph|editorial|commentator|preface|monastic-rule",
                                note, re.IGNORECASE,
                            )
                        )
                        or (
                            actor.get("Status") == "identified-unlinked-master"
                            and actor_label
                            and re.search(re.escape(public_actor_label(actor_label)), note, re.IGNORECASE)
                        )
                    ))
                    if not speaker_named and not exception_named:
                        fail("note_missing_speaker", entry, f"{term} s{si} o{oi}: {note}")
                    if not source_named:
                        fail(
                            "note_missing_source",
                            entry,
                            f"{term} s{si} o{oi} expected exact RelPath {rel!r} "
                            f"(preferred) or legacy title {title!r}: {note}",
                        )

            prose = "\n".join(str(sense.get(k) or "") for k in ("Explanation", "Note"))
            for match in PLACEHOLDER_ACTOR_RE.finditer(prose):
                fail("placeholder_actor_forbidden", entry, f"{term} s{si}: {match.group(0)!r}")
            for match in VAGUE_RE.finditer(prose):
                # A lexical gloss or description may honestly say "a monk"
                # when this sense stores a fully reviewed unnamed non-master
                # actor. This exception never applies to master/teacher.
                if "monk" in match.group(0).lower() and any(
                    (o.get("ActorAttribution") or {}).get("Status") == "reviewed-unnamed"
                    and str((o.get("ActorAttribution") or {}).get("Kind") or "").lower() == "monk"
                    for _, o in evidence_rows
                ):
                    counts["reviewed_unnamed_prose"] += 1
                    continue
                fail("vague_attributor", entry, f"{term} s{si}: {match.group(0)!r}")

            for quote in sorted(chinese_strings(prose)):
                counts["chinese_strings"] += 1
                if not any(quote in kwic or kwic in quote for kwic in kwics if kwic):
                    fail("dangling_chinese", entry, f"{term} s{si}: {quote}")
                else:
                    counts["anchored_chinese"] += 1

    uniform_failure = uniform_actor_placeholder_failure(
        len(files), batch_named, batch_actor_signatures
    )
    if uniform_failure:
        failures.append(uniform_failure)
        counts["batch_uniform_actor_placeholder"] += 1
    collapse_failure = anonymous_actor_collapse_failure(
        len(files), batch_named, batch_actor_signatures
    )
    if collapse_failure:
        failures.append(collapse_failure)
        counts["batch_anonymous_actor_collapse"] += 1
    report = {
        "counts": dict(counts),
        "hardFailures": len(failures),
        "failures": failures,
    }
    if ns.output:
        ns.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = ns.output.with_suffix(ns.output.suffix + ".tmp")
        temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, ns.output)
    if ns.as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(report["counts"], ensure_ascii=False, indent=2, sort_keys=True))
        print(f"hardFailures: {len(failures)}")
        for item in failures:
            print(f"{item['kind']}: {item['detail']} [{item['entry']}]")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
