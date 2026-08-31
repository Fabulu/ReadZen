#!/usr/bin/env python3
"""Compile an evidence-first worksheet into the unchanged entry.v2 schema.

The worksheet contains research/admission fields that never reach readers.
Compilation strips those fields, joins explicitly separated explanation parts,
and refuses generic template filler before the expensive cohort gates run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from functools import lru_cache
from pathlib import Path
from source_authority_contract import validate_source_row


GENERIC = re.compile(
    r"(?:^|\b)(?:TODO|TBD|placeholder|expanded context establishes|"
    r"full context establishes|full surrounding context was checked|"
    r"the quoted clause supplies the anchored wording|"
    r"in the selected records, the headword is rendered as|"
    r"its stored turns define the scope of this sense|"
    r"the evidence rows preserve the headword|"
    r"the selected contrasts and deployments remain bounded|"
    r"is the corpus expression for the action, image, or judgment described by the stored cases|"
    r"the witnesses place it in direct answers, challenges, verses, appraisals, and narrative controls|"
    r"the entry follows those predicates rather than an outside interpretation|"
    r"is the figure the records place inside zen cases, quotations, and public questions|"
    r"the selected witnesses define this figure by what masters ask, quote, praise, rebuke, or reenact|"
    r"names a concrete implement, office, rite, or communal act in the public life of a zen monastery|"
    r"the selected witnesses show who performs it, where it enters the hall sequence, and how masters bring it into encounters|"
    r"is the plain-English referent tested by the selected Chan records|"
    r"the selected cases place .{0,160} inside lineage records, public addresses, institutional narration, or inherited cases|"
    r"the exact surrounding predicates delimit how the records use it rather than importing an external definition|"
    r"names the referent or formula used in the selected zen records|"
    r"complete-case reading shows how .{0,160} functions in exchanges, formal addresses, institutional records, or inherited cases|"
    r"the entry follows those predicates and speakers rather than an outside interpretation|"
    r"complete-unit reading separates direct speech, quoted verse, authored exposition, invitation or memorial prose, action narration, and duplicate recensions|"
    r"the expression .{0,120} occurs in the cited questions, answers, actions, narration, or verse|"
    r"this sense remains limited to those deployments)(?:\b|$)", re.I
)
SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+")


def redundant_consecutive_opening_definition(term: str, explanation: str) -> bool:
    """Detect only adjacent headword definitions at the prose opening."""
    sentences = [part.strip() for part in SENTENCE_BREAK.split(explanation.strip()) if part.strip()]
    if len(sentences) < 2 or not term:
        return False
    definitional = re.compile(
        rf"^{re.escape(term)}\s+(?:means\b|is\s+(?:an?\s+|the\s+)?|names\b|denotes\b|refers\s+to\b)",
        re.IGNORECASE,
    )
    return bool(definitional.match(sentences[0]) and definitional.match(sentences[1]))
CALQUE_FIRST = re.compile(r"^\s*(?:literally|word[- ]for[- ]word|the graphs? (?:mean|say|name))\b", re.I)
FORBIDDEN = re.compile(r"\b(?:Buddhism|meditation|Bodhiteaching)\b", re.I)
ALLOWED_ACTOR_STATUSES = {"reviewed-unnamed", "identified-non-master", "identified-unlinked-master", "narrated", "impersonal"}
FORBIDDEN_ANONYMOUS_KINDS = {"master", "zen master", "teacher", "禪師", "和尚"}
NON_NAME_MASTER_LABEL = re.compile(
    r"^(?:師(?:乃|斥|以|云|曰|問|答|指|舉|拈|喝|打|示|語)|謂(?:弟子|僧|眾)|"
    r"示眾|作.+偈|指(?:座|杖)|藏語之|如意子鞠躬)"
)
ALLOWED_CONTEXT_ROLES = {
    "utterer", "respondent", "questioner", "interlocutor", "addressee",
    "section-subject", "record-owner", "person-described", "person-discussed",
    "commentator", "later-raiser", "later-quoter", "teacher", "student",
    "compiler", "verse-author", "case-figure", "action-performer",
}


@lru_cache(maxsize=1)
def canonical_roster_names() -> frozenset[str]:
    """Return every exact public name in the read-only lineage roster."""
    repo = Path(__file__).resolve().parent.parents[3]
    roster = json.loads(
        (repo / "Assets" / "Data" / "lineage-masters.json").read_text(
            encoding="utf-8-sig"
        )
    )
    return frozenset(
        str(name).strip()
        for row in roster
        for name in (row.get("names") or [])
        if str(name).strip()
    )


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def required_text(value, coordinate: str, errors: list[str]) -> str:
    text = str(value or "").strip()
    if not text:
        errors.append(f"{coordinate}: required text is empty")
    elif GENERIC.search(text):
        errors.append(f"{coordinate}: generic template filler is forbidden")
    return text


def required_depth_floor(hit_count: int) -> int:
    """Return the guide's mechanical occurrence floor for an exact hit count."""
    if hit_count <= 0:
        return 0
    if hit_count < 3:
        return hit_count
    if hit_count < 20:
        return 3
    if hit_count < 100:
        return 4
    if hit_count < 500:
        return 6
    if hit_count < 2_000:
        return 7
    if hit_count < 10_000:
        return 8
    return 10


def occurrence_identity(occurrence: dict) -> tuple[str, str, str, str]:
    """Identity used to stop a copied witness from being counted twice."""
    return tuple(
        str(occurrence.get(field) or "").strip()
        for field in ("RelPath", "FromLb", "ToLb", "Kwic")
    )


def validate_new_entry_depth(
    transport: dict, sense: dict, index: int, errors: list[str]
) -> None:
    """Fail closed on quota drafting and incomplete deployment harvesting.

    A false-substring override remains a root-reviewed exception handled by the
    dedicated depth auditor. The construction compiler deliberately uses the
    worksheet's frozen exact count and refuses undocumented local exceptions.
    """
    occurrences = sense.get("Occurrences") or []
    identities = [occurrence_identity(row) for row in occurrences]
    if len(set(identities)) != len(identities):
        errors.append(
            f"sense {index}.Occurrences: duplicate retained witness identity is forbidden; "
            "a copied occurrence cannot manufacture depth or independence"
        )

    exact_count = transport.get("ExactCount")
    if (
        isinstance(exact_count, int)
        and exact_count >= 0
        and transport.get("DepthFloorScope") != "entry"
    ):
        floor = required_depth_floor(exact_count)
        unique_count = len(set(identities))
        exception = ((sense.get("DraftEvidence") or {}).get("DepthHarvestReceipt") or {}).get(
            "AuthorizedFloorException"
        )
        exception_valid = (
            isinstance(exception, dict)
            and exception.get("Decision") == "FROZEN_CANDIDATE_EXHAUSTION"
            and exception.get("AuthorizedBy") == "root"
            and exception.get("FrozenCandidateExhausted") is True
            and exception.get("RetainedIndependentFamilies") == unique_count
            and isinstance(exception.get("ExcludedReserve"), list)
            and len(exception["ExcludedReserve"]) >= 1
        )
        if unique_count < floor and not exception_valid:
            errors.append(
                f"sense {index}.Occurrences: {unique_count} unique exact witnesses retained "
                f"for {exact_count} frozen hits; guide depth floor is {floor}"
            )

        authority_rows = (sense.get("DraftEvidence") or {}).get("SourceAuthorityRows") or []
        available_files = None
        harvest = (sense.get("DraftEvidence") or {}).get("DepthHarvestReceipt") or {}
        if isinstance(harvest.get("AvailableSourceFiles"), int):
            available_files = harvest["AvailableSourceFiles"]
        if exact_count >= 100 and (available_files is None or available_files >= 4):
            work_ids = {
                str(row.get("WorkId") or "").strip()
                for row in authority_rows
                if str(row.get("WorkId") or "").strip()
            }
            if len(work_ids) < 4:
                errors.append(
                    f"sense {index}.DraftEvidence.SourceAuthorityRows: {exact_count} hits "
                    "require four source works when four exist"
                )

    draft = sense.get("DraftEvidence") or {}
    harvest = draft.get("DepthHarvestReceipt")
    coordinate = f"sense {index}.DraftEvidence.DepthHarvestReceipt"
    if not isinstance(harvest, dict):
        errors.append(f"{coordinate}: completed deployment-harvest receipt required")
        return
    if harvest.get("Complete") is not True:
        errors.append(f"{coordinate}.Complete: true required before compilation")
    searched = harvest.get("SearchedDeploymentClasses")
    if (
        not isinstance(searched, list)
        or not searched
        or any(not str(item).strip() for item in searched)
    ):
        errors.append(f"{coordinate}.SearchedDeploymentClasses: nonempty inventory required")
    omission_audit = harvest.get("OmissionAudit")
    if (
        not isinstance(omission_audit, list)
        or not omission_audit
        or any(not str(item).strip() for item in omission_audit)
    ):
        errors.append(f"{coordinate}.OmissionAudit: nonempty final omission audit required")
    if harvest.get("ReviewedExactHitCount") != transport.get("ExactCount"):
        errors.append(
            f"{coordinate}.ReviewedExactHitCount: must equal EvidenceTransport.ExactCount"
        )


def validate_entry_scoped_depth(
    transport: dict, senses: list[dict], errors: list[str]
) -> None:
    """Apply the immutable dynamic floor once across a multi-sense entry."""
    exact_count = transport.get("ExactCount")
    identities = [
        occurrence_identity(row)
        for sense in senses
        for row in (sense.get("Occurrences") or [])
    ]
    if len(set(identities)) != len(identities):
        errors.append("Entry.Senses: duplicate witness identity across senses is forbidden")
    if isinstance(exact_count, int) and exact_count >= 0:
        floor = required_depth_floor(exact_count)
        if len(set(identities)) < floor:
            errors.append(
                f"Entry.Senses: {len(set(identities))} unique exact witnesses retained "
                f"for {exact_count} frozen hits; entry-scoped guide depth floor is {floor}"
            )
        available_files = max(
            (
                int((sense.get("DraftEvidence") or {}).get(
                    "DepthHarvestReceipt", {}
                ).get("AvailableSourceFiles"))
                for sense in senses
                if isinstance(
                    (sense.get("DraftEvidence") or {}).get(
                        "DepthHarvestReceipt", {}
                    ).get("AvailableSourceFiles"),
                    int,
                )
            ),
            default=0,
        )
        work_ids = {
            str(row.get("WorkId") or "").strip()
            for sense in senses
            for row in (
                (sense.get("DraftEvidence") or {}).get("SourceAuthorityRows") or []
            )
            if str(row.get("WorkId") or "").strip()
        }
        if exact_count >= 100 and available_files >= 4 and len(work_ids) < 4:
            errors.append(
                f"Entry.Senses: {exact_count} hits require four source works "
                "across entry-scoped senses when four exist"
            )


def validate_new_entry_pipeline(
    payload: dict, errors: list[str], worksheet_path: Path | None = None
) -> None:
    """Require the integrated v2 decisions for fresh acquisition only.

    Repair compilation intentionally remains compatible with historical worksheets;
    callers authoring a new article must opt into this gate with --new-entry.
    """
    if payload.get("ConstructionPipelineVersion") != 2:
        errors.append("ConstructionPipelineVersion: new entries require version 2")

    admission = payload.get("Admission") or {}
    if admission.get("Decision") != "admit":
        errors.append("Admission.Decision: new entry compilation requires admit")
    required_text(admission.get("LexicalUnitReason"), "Admission.LexicalUnitReason", errors)
    required_text(admission.get("ObservableChanJob"), "Admission.ObservableChanJob", errors)
    duplicate = admission.get("DuplicateCheck") or {}
    if duplicate.get("DeterministicIdChecked") is not True:
        errors.append("Admission.DuplicateCheck.DeterministicIdChecked: true required")
    if duplicate.get("ExactHeadwordChecked") is not True:
        errors.append("Admission.DuplicateCheck.ExactHeadwordChecked: true required")
    required_text(
        duplicate.get("NearDuplicateRuling"),
        "Admission.DuplicateCheck.NearDuplicateRuling", errors,
    )

    transport = payload.get("EvidenceTransport") or {}
    dossier_text = required_text(
        transport.get("DossierPath"), "EvidenceTransport.DossierPath", errors
    )
    dossier_sha = str(transport.get("DossierSha256") or "").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", dossier_sha):
        errors.append("EvidenceTransport.DossierSha256: 64 lowercase hexadecimal characters required")
    elif dossier_text and worksheet_path is not None:
        dossier_path = Path(dossier_text)
        if not dossier_path.is_absolute():
            dossier_path = worksheet_path.parent / dossier_path
        if not dossier_path.is_file():
            errors.append("EvidenceTransport.DossierPath: referenced dossier does not exist")
        elif sha(dossier_path.read_bytes()) != dossier_sha:
            errors.append("EvidenceTransport.DossierSha256: does not match referenced dossier bytes")
    methods = transport.get("DiscoveryMethods")
    if not isinstance(methods, list) or not methods or any(not str(item).strip() for item in methods):
        errors.append("EvidenceTransport.DiscoveryMethods: nonempty method list required")
    for field in ("ExactCount", "BridgedCount"):
        value = transport.get(field)
        if not isinstance(value, int) or value < 0:
            errors.append(f"EvidenceTransport.{field}: nonnegative integer required")

    entry = payload.get("Entry") or {}
    headword = str(entry.get("SourceTerm") or "").strip()
    harvest = payload.get("FamilyHarvest") or {}
    for receipt_number, receipt in enumerate(harvest.get("NegativeReceipt") or [], 1):
        for disposition_number, disposition in enumerate(
            (receipt or {}).get("dispositions") or [], 1
        ):
            coordinate = (
                f"FamilyHarvest.NegativeReceipt[{receipt_number}]"
                f".dispositions[{disposition_number}]"
            )
            candidate = str((disposition or {}).get("candidate") or "").strip()
            candidate_id = str((disposition or {}).get("candidateId") or "").strip()
            if candidate == headword:
                errors.append(
                    f"{coordinate}.candidate: family candidate cannot equal the source headword"
                )
            if not candidate_id:
                errors.append(
                    f"{coordinate}.candidateId: nonempty candidate identity required "
                    "when a disposition row exists"
                )
    if transport.get("CorpusBaselineSha256") != entry.get("CorpusBaselineSha256"):
        errors.append("EvidenceTransport.CorpusBaselineSha256: must equal Entry.CorpusBaselineSha256")
    source_registry = None
    if worksheet_path is not None:
        repo = Path(__file__).resolve().parent.parents[3]
        registry_path = repo / "Assets" / "Data" / "zen-source-authority.json"
        if not registry_path.is_file():
            errors.append("EvidenceTransport.SourceAuthorityManifestSha256: authority registry is missing")
        else:
            registry_sha = sha(registry_path.read_bytes())
            if transport.get("SourceAuthorityManifestSha256") != registry_sha:
                errors.append(
                    "EvidenceTransport.SourceAuthorityManifestSha256: "
                    "must match the current authority registry bytes"
                )
            registry = json.loads(registry_path.read_text(encoding="utf-8-sig"))
            if registry.get("corpusManifestSha256") != entry.get("CorpusBaselineSha256"):
                errors.append(
                    "EvidenceTransport.SourceAuthorityManifestSha256: "
                    "registry is not bound to the entry corpus baseline"
                )
            source_registry = {row["RelPath"]: row for row in registry.get("entries") or []}
    senses = entry.get("Senses") or []
    entry_scoped_depth = transport.get("DepthFloorScope") == "entry"
    if entry_scoped_depth:
        validate_entry_scoped_depth(transport, senses, errors)
    for index, sense in enumerate(senses, 1):
        validate_new_entry_depth(transport, sense, index, errors)
        draft = sense.get("DraftEvidence") or {}
        required_text(draft.get("LiteralGraphFloor"), f"sense {index}.DraftEvidence.LiteralGraphFloor", errors)
        required_text(draft.get("LexicalJob"), f"sense {index}.DraftEvidence.LexicalJob", errors)
        deployments = draft.get("DeploymentClasses")
        if not isinstance(deployments, list) or not deployments:
            errors.append(f"sense {index}.DraftEvidence.DeploymentClasses: nonempty decision list required")
        high_value = draft.get("HighValueEvidenceLedger")
        if not isinstance(high_value, list) or not high_value:
            errors.append(f"sense {index}.DraftEvidence.HighValueEvidenceLedger: nonempty keep/reject/unresolved ledger required")
        else:
            for row_number, row in enumerate(high_value, 1):
                if not isinstance(row, dict) or row.get("Disposition") not in {"keep", "reject", "unresolved"}:
                    errors.append(
                        f"sense {index}.DraftEvidence.HighValueEvidenceLedger[{row_number}]: "
                        "object with keep/reject/unresolved Disposition required"
                    )
                    continue
                required_text(
                    row.get("Finding"),
                    f"sense {index}.DraftEvidence.HighValueEvidenceLedger[{row_number}].Finding", errors,
                )
                required_text(
                    row.get("Reason"),
                    f"sense {index}.DraftEvidence.HighValueEvidenceLedger[{row_number}].Reason", errors,
                )
        authority_rows = draft.get("SourceAuthorityRows")
        occurrence_count = len(sense.get("Occurrences") or [])
        if not isinstance(authority_rows, list) or len(authority_rows) != occurrence_count:
            errors.append(
                f"sense {index}.DraftEvidence.SourceAuthorityRows: one row per retained occurrence required"
            )
            authority_rows = []
        allowed_roles = {
            "original-use", "active-quotation", "commentary",
            "passive-quotation", "recension",
        }
        keys = set()
        families = set()
        higher_tier_families = set()
        tiers = []
        hierarchy_invalid = False
        for row_number, row in enumerate(authority_rows, 1):
            coordinate = f"sense {index}.DraftEvidence.SourceAuthorityRows[{row_number}]"
            if not isinstance(row, dict):
                errors.append(f"{coordinate}: object required")
                continue
            key = str(row.get("EvidenceKey") or "").strip()
            if not re.fullmatch(r"o[1-9][0-9]*", key):
                errors.append(f"{coordinate}.EvidenceKey: retained occurrence key oN required")
            elif key in keys:
                errors.append(f"{coordinate}.EvidenceKey: duplicate {key}")
            keys.add(key)
            tier = row.get("Tier")
            source_class = row.get("SourceClass")
            if not validate_source_row(
                tier, source_class, row.get("RawSourceClass"),
                row.get("SourceClassNormalization"),
            ):
                errors.append(f"{coordinate}: Tier and SourceClass do not match the closed hierarchy")
                hierarchy_invalid = True
            else:
                tiers.append(tier)
            occurrence_number = int(key[1:]) if re.fullmatch(r"o[1-9][0-9]*", key) else None
            if source_registry is not None and occurrence_number is not None and occurrence_number <= occurrence_count:
                rel_path = (sense.get("Occurrences") or [])[occurrence_number - 1].get("RelPath")
                if row.get("RelPath") != rel_path:
                    errors.append(
                        f"{coordinate}.RelPath: {row.get('RelPath')!r} must match "
                        f"retained occurrence {key} source {rel_path!r}"
                    )
                authority = source_registry.get(rel_path)
                if authority is None:
                    errors.append(f"{coordinate}: occurrence source is absent from the authority registry")
                elif authority.get("Tier") != tier:
                    container_tier = row.get("ContainerTier")
                    override_reason = str(row.get("CoordinateTierOverrideReason") or "").strip()
                    valid_coordinate_downgrade = (
                        container_tier == authority.get("Tier")
                        and tier == 3
                        and authority.get("Tier") in {1, 2}
                        and bool(override_reason)
                    )
                    if not valid_coordinate_downgrade:
                        errors.append(
                            f"{coordinate}.Tier: declared {tier!r} does not match "
                            f"registry tier {authority.get('Tier')!r} for {rel_path}; "
                            "a coordinate downgrade requires the matching ContainerTier, "
                            "Tier 3, and a nonempty CoordinateTierOverrideReason"
                        )
            required_text(row.get("AuthorityReason"), f"{coordinate}.AuthorityReason", errors)
            family = required_text(row.get("WitnessFamilyId"), f"{coordinate}.WitnessFamilyId", errors)
            if family:
                families.add(family)
                if tier in {1, 2} and row.get("DeploymentRole") not in {"passive-quotation", "recension"}:
                    higher_tier_families.add(family)
            if row.get("DeploymentRole") not in allowed_roles:
                errors.append(f"{coordinate}.DeploymentRole: closed deployment role required")
        expected_keys = {f"o{number}" for number in range(1, occurrence_count + 1)}
        if keys != expected_keys:
            errors.append(
                f"sense {index}.DraftEvidence.SourceAuthorityRows: keys {sorted(keys)} "
                f"must equal {sorted(expected_keys)}"
            )
        authority_work_ids = [
            row.get("WorkId") for row in authority_rows
            if isinstance(row, dict) and row.get("WorkId")
        ]
        if set(draft.get("IndependentWorkIds") or []) != set(authority_work_ids):
            errors.append(
                f"sense {index}.IndependentWorkIds: must exactly match the current retained "
                "SourceAuthorityRows work inventory"
            )
        validation = sense.get("Validation")
        if validation == "multi-source":
            if len(higher_tier_families) < 2:
                errors.append(
                    f"sense {index}.Validation: multi-source requires two independent Tier 1/2 "
                    "deployment families; supplementary lamps do not count"
                )
            if not hierarchy_invalid and not any(tier in {1, 2} for tier in tiers):
                errors.append(
                    f"sense {index}.Validation: lamp-only evidence cannot earn multi-source"
                )
        if tiers and all(tier == 3 for tier in tiers):
            required_text(
                draft.get("NoHigherWitnessSearchReceipt"),
                f"sense {index}.DraftEvidence.NoHigherWitnessSearchReceipt", errors,
            )
            if validation != "provisional":
                errors.append(f"sense {index}.Validation: lamp-only evidence must remain provisional")
        lamp_count = sum(tier == 3 for tier in tiers)
        if lamp_count > 2 or (tiers and lamp_count * 3 > len(tiers)):
            required_text(
                draft.get("LampExcessJustification"),
                f"sense {index}.DraftEvidence.LampExcessJustification", errors,
            )


def compile_occurrence(value: dict, coordinate: str, errors: list[str]) -> dict:
    occurrence = dict(value)
    proof = occurrence.pop("DraftActorProof", None)
    actor_decision = proof.get("ActorDecision") if isinstance(proof, dict) else None
    if actor_decision is not None:
        if not isinstance(actor_decision, dict):
            errors.append(f"{coordinate}.DraftActorProof.ActorDecision: object required")
        else:
            pointer = actor_decision.get("casePointer")
            transport_identity = pointer.get("transportIdentitySha256") or pointer.get("transportSha256") if isinstance(pointer, dict) else None
            if not isinstance(pointer, dict) or not pointer.get("transportRowId") or not isinstance(pointer.get("candidateCaseIndex"), int) or not transport_identity:
                errors.append(f"{coordinate}.DraftActorProof.ActorDecision.casePointer: complete immutable pointer required")
            required_text(actor_decision.get("literalFragment"), f"{coordinate}.DraftActorProof.ActorDecision.literalFragment", errors)
            boundary = actor_decision.get("governingBoundary")
            if not isinstance(boundary, dict) or boundary.get("kind") not in {"speech", "question", "answer", "quotation", "verse", "narration", "impersonal"}:
                errors.append(f"{coordinate}.DraftActorProof.ActorDecision.governingBoundary: closed kind required")
            elif not str(boundary.get("literal") or "").strip():
                errors.append(f"{coordinate}.DraftActorProof.ActorDecision.governingBoundary.literal: required")
            if actor_decision.get("voiceLayer") not in {"direct-turn", "question-turn", "quoted-original", "transmitted-verse", "compiler-narration", "embedded-copy", "impersonal"}:
                errors.append(f"{coordinate}.DraftActorProof.ActorDecision.voiceLayer: closed value required")
            if actor_decision.get("rationaleCode") not in {"direct-speech-marker", "section-address-continuity", "bounded-dialogue-turn", "named-quotation", "attributed-verse", "compiler-narration", "impersonal-construction"}:
                errors.append(f"{coordinate}.DraftActorProof.ActorDecision.rationaleCode: closed value required")
            if not isinstance(actor_decision.get("utterer"), dict) or not actor_decision["utterer"].get("type"):
                errors.append(f"{coordinate}.DraftActorProof.ActorDecision.utterer: explicit status required")
    kwic = required_text(occurrence.get("Kwic"), f"{coordinate}.Kwic", errors)
    rel_path = required_text(occurrence.get("RelPath"), f"{coordinate}.RelPath", errors)
    required_text(occurrence.get("FromLb"), f"{coordinate}.FromLb", errors)
    attribution_note = required_text(
        occurrence.get("AttributionNote"), f"{coordinate}.AttributionNote", errors
    )
    expected_note_prefix = f"Source record ({rel_path}). "
    if attribution_note and rel_path and not attribution_note.startswith(expected_note_prefix):
        errors.append(
            f"{coordinate}.AttributionNote: must begin exactly {expected_note_prefix!r}"
        )
    span_review = occurrence.get("HeadwordSpanReview")
    if span_review is not None:
        if not isinstance(span_review, dict):
            errors.append(f"{coordinate}.HeadwordSpanReview: must be an object")
        else:
            if not isinstance(span_review.get("Count"), int) or span_review.get("Count", 0) < 2:
                errors.append(f"{coordinate}.HeadwordSpanReview.Count: integer >=2 required")
            if span_review.get("Disposition") != "single-actor-single-turn-repetition":
                errors.append(
                    f"{coordinate}.HeadwordSpanReview.Disposition: use single-actor-single-turn-repetition"
                )
            required_text(
                span_review.get("GrammarEvidence"),
                f"{coordinate}.HeadwordSpanReview.GrammarEvidence", errors,
            )
    # Reader-facing attribution must name the actor once. A prior formatter
    # prepended the actor to prose which already began with that actor, yielding
    # visible strings such as "Foyan Qingyuan: Foyan Qingyuan: ...". Catch the
    # duplicate structurally before an otherwise expensive semantic review.
    note_tail = attribution_note.split("). ", 1)[-1]
    note_parts = note_tail.split(": ", 2)
    if len(note_parts) >= 3 and note_parts[0].strip().casefold() == note_parts[1].strip().casefold():
        errors.append(f"{coordinate}.AttributionNote: duplicated actor prefix is forbidden")
    # Exact actor ownership is an XOR.  A populated MasterName is already the
    # headword-bearing actor decision; retaining ActorAttribution beside it can
    # silently preserve a contradictory actor from an earlier adjudication.
    if occurrence.get("MasterName") and occurrence.get("ActorAttribution"):
        master = str(occurrence.get("MasterName") or "").strip()
        actor = occurrence.get("ActorAttribution") or {}
        label = str(actor.get("ActorLabel") or "").strip()
        if label and label != master:
            errors.append(
                f"{coordinate}.ActorAttribution: contradicts populated MasterName "
                f"{master!r} by assigning the headword-bearing action to {label!r}"
            )
        else:
            errors.append(
                f"{coordinate}.ActorAttribution: forbidden when MasterName is populated; "
                "exact actor ownership must use one representation"
            )
    if occurrence.get("MasterName"):
        if NON_NAME_MASTER_LABEL.search(str(occurrence.get("MasterName") or "").strip()):
            errors.append(
                f"{coordinate}.MasterName: speech/action syntax is not a person's canonical roster name"
            )
        if not isinstance(proof, dict):
            errors.append(f"{coordinate}.DraftActorProof: required for named exact utterer")
        elif actor_decision is None:
            required_text(proof.get("ExactHeadwordClause"), f"{coordinate}.DraftActorProof.ExactHeadwordClause", errors)
            required_text(proof.get("SpeechFrame"), f"{coordinate}.DraftActorProof.SpeechFrame", errors)
            required_text(proof.get("FullCaseDecision"), f"{coordinate}.DraftActorProof.FullCaseDecision", errors)
            clause = re.sub(r"\s+", "", str(proof.get("ExactHeadwordClause") or ""))
            if clause and clause not in re.sub(r"\s+", "", kwic):
                errors.append(f"{coordinate}: exact headword clause is not contained in KWIC")
    else:
        actor = occurrence.get("ActorAttribution") or {}
        status = actor.get("Status")
        if status not in ALLOWED_ACTOR_STATUSES:
            errors.append(f"{coordinate}.ActorAttribution.Status: closed status required")
        if str(actor.get("Kind") or "").strip().casefold() in FORBIDDEN_ANONYMOUS_KINDS:
            errors.append(f"{coordinate}.ActorAttribution.Kind: a master must be roster-named or the occurrence rejected")
        grammar = required_text(actor.get("GrammarEvidence"), f"{coordinate}.ActorAttribution.GrammarEvidence", errors)
        if grammar and len(grammar) < 24:
            errors.append(f"{coordinate}.ActorAttribution.GrammarEvidence: too short to record grammatical proof")
        if status == "identified-unlinked-master":
            if actor.get("RungsChecked") != ["line", "expanded-context", "section-header", "book-title", "tei-header", "parallel-passage"]:
                errors.append(f"{coordinate}.ActorAttribution.RungsChecked: identified-unlinked-master requires all six ordered rungs")
            label = str(actor.get("ActorLabel") or "").strip()
            if not label or re.match(r"^(?:the|an?|one|some|unnamed)\b", label, re.I):
                errors.append(f"{coordinate}.ActorAttribution.ActorLabel: identified-unlinked-master requires an explicit source identity")
            elif label in canonical_roster_names():
                errors.append(
                    f"{coordinate}.ActorAttribution.ActorLabel: roster-canonical identity "
                    f"{label!r} must populate MasterName and cannot remain identified-unlinked-master"
                )
        if status in {"reviewed-unnamed", "identified-unlinked-master"}:
            if actor.get("RungsChecked") != ["line", "expanded-context", "section-header", "book-title", "tei-header", "parallel-passage"]:
                errors.append(
                    f"{coordinate}.ActorAttribution.RungsChecked: {status} requires all six ordered rungs"
                )
            required_text(actor.get("ReviewedBy"), f"{coordinate}.ActorAttribution.ReviewedBy", errors)
            required_text(actor.get("ReviewedUtc"), f"{coordinate}.ActorAttribution.ReviewedUtc", errors)
        # A machine may flag authored-voice risk but may not decide the actor. Generic
        # "compiler narration" is forbidden when the stored cut contains strong
        # first-person, direct-address, answer, or quotation cues unless the worksheet
        # records an explicit human full-case adjudication.
        voice_risk = bool(re.search(r"(?:余|山僧|我|汝|你|答[:：]|荅[:：]|云[:：]|曰[:：])", kwic))
        generic_compiler = (
            status == "narrated"
            and str(actor.get("Kind") or "").casefold() == "compiler narrative"
            and "compiler narrating the headword-bearing clause" in str(actor.get("ActorLabel") or "").casefold()
        )
        if voice_risk and generic_compiler and not actor.get("AuthoredVoiceRiskReviewed"):
            errors.append(
                f"{coordinate}.ActorAttribution: authored-speech/quote/verse risk requires explicit full-case human adjudication; automation does not prove the actor"
            )
        if not isinstance(proof, dict):
            errors.append(f"{coordinate}.DraftActorProof: required for non-named actor decision")
        elif actor_decision is None:
            required_text(proof.get("FullCaseDecision"), f"{coordinate}.DraftActorProof.FullCaseDecision", errors)
            required_text(proof.get("GrammaticalSubject"), f"{coordinate}.DraftActorProof.GrammaticalSubject", errors)
    for ci, context in enumerate(occurrence.get("ContextMasters") or [], 1):
        roles = context.get("Roles") or []
        if not roles or any(role not in ALLOWED_CONTEXT_ROLES for role in roles):
            errors.append(f"{coordinate}.ContextMasters[{ci}]: use only closed, nonempty roles")
        if (
            not occurrence.get("MasterName")
            and not occurrence.get("ActorAttribution")
            and "utterer" in roles
        ):
            errors.append(f"{coordinate}.ContextMasters[{ci}]: utterer role contradicts null MasterName")
    for ci, context in enumerate(occurrence.get("ContextActors") or [], 1):
        if not isinstance(context, dict):
            errors.append(f"{coordinate}.ContextActors[{ci}]: object required")
            continue
        if context.get("Status") not in {
                "identified-unlinked-master", "identified-non-master", "reviewed-unnamed"}:
            errors.append(f"{coordinate}.ContextActors[{ci}].Status: closed contextual identity type required")
        required_text(context.get("ActorLabel"), f"{coordinate}.ContextActors[{ci}].ActorLabel", errors)
        roles = context.get("Roles") or []
        if not roles or any(role not in ALLOWED_CONTEXT_ROLES for role in roles) or "utterer" in roles:
            errors.append(f"{coordinate}.ContextActors[{ci}].Roles: closed non-utterer roles required")
        proof = required_text(context.get("GrammarEvidence"), f"{coordinate}.ContextActors[{ci}].GrammarEvidence", errors)
        if proof and len(proof) < 24:
            errors.append(f"{coordinate}.ContextActors[{ci}].GrammarEvidence: case-specific proof required")
    occurrence["Curated"] = True
    return occurrence


def compile_claim_anchor(
    value: dict, coordinate: str, source_term: str, errors: list[str]
) -> dict:
    """Compile an auxiliary claim anchor without letting it impersonate evidence.

    Claim anchors support reader-facing contextual claims.  They are not
    occurrences of the entry headword and therefore must preserve a real claim
    from their quoted span rather than merely copying the headword into
    ``ClaimText``.  This is deliberately a local syntactic check: source
    selection and semantic adequacy remain author/reviewer decisions.
    """
    anchor = compile_occurrence(value, coordinate, errors)
    claim_text = required_text(anchor.get("ClaimText"), f"{coordinate}.ClaimText", errors)
    normalized_claim = re.sub(r"\s+", "", claim_text)
    normalized_headword = re.sub(r"\s+", "", str(source_term or ""))
    if normalized_claim and normalized_headword and normalized_claim == normalized_headword:
        errors.append(
            f"{coordinate}.ClaimText: must contain contextual claim text, not only the source headword"
        )
    kwic = str(anchor.get("Kwic") or "")
    if claim_text and claim_text not in kwic:
        errors.append(f"{coordinate}.ClaimText: must be an exact substring of Kwic")
    return anchor


def compile_sense(value: dict, index: int, errors: list[str], require_pipeline_v2: bool = False) -> dict:
    sense = dict(value)
    parts = sense.pop("ExplanationParts", None) or {}
    draft = sense.pop("DraftEvidence", None) or {}
    accepted_derived = sense.pop("DraftAcceptedDerivedFields", None) or {}
    accepted_legacy_validation = sense.pop("DraftAcceptedLegacyValidation", None)
    omit_empty_anchors = bool(sense.pop("DraftOmitEmptyClaimAnchors", False))
    opening = required_text(parts.get("CorpusEarnedOpening"), f"sense {index}.opening", errors)
    if CALQUE_FIRST.search(opening):
        errors.append(f"sense {index}.opening: must begin with corpus-earned interpretation, not a calque")
    body = parts.get("EvidenceBody") or []
    if not isinstance(body, list) or not body:
        errors.append(f"sense {index}.EvidenceBody: at least one evidence paragraph is required")
        body = []
    body = [required_text(item, f"sense {index}.EvidenceBody[{n}]", errors) for n, item in enumerate(body, 1)]
    if require_pipeline_v2:
        body_keys = draft.get("EvidenceBodyClaimKeys")
        if not isinstance(body_keys, list) or len(body_keys) != len(body):
            errors.append(
                f"sense {index}.DraftEvidence.EvidenceBodyClaimKeys: one evidence-key list per body paragraph required"
            )
        elif any(not isinstance(keys, list) or not keys for keys in body_keys):
            errors.append(
                f"sense {index}.DraftEvidence.EvidenceBodyClaimKeys: every body paragraph requires at least one evidence key"
            )
    normalized_opening = re.sub(r"\s+", " ", opening).strip().casefold()
    for n, paragraph in enumerate(body, 1):
        if normalized_opening and re.sub(r"\s+", " ", paragraph).strip().casefold() == normalized_opening:
            errors.append(
                f"sense {index}.EvidenceBody[{n}]: duplicates the corpus-earned opening verbatim"
            )
    sense["Explanation"] = " ".join([opening, *body]).strip()
    source_term = str(value.get("SourceTerm") or "")
    # Sense worksheets do not normally repeat the entry headword, so recover
    # it from the opening's initial CJK token when necessary.
    if not source_term:
        match = re.match(r"^(\S+)\s+", opening)
        source_term = match.group(1) if match else ""
    if redundant_consecutive_opening_definition(source_term, sense["Explanation"]):
        errors.append(f"sense {index}.Explanation: redundant consecutive opening definition")
    required_text(sense.get("PreferredTarget"), f"sense {index}.PreferredTarget", errors)
    aliases = sense.get("SearchAliases")
    if not isinstance(aliases, list) or not aliases or any(not str(alias).strip() for alias in aliases):
        errors.append(f"sense {index}.SearchAliases: nonempty controlled aliases are required")
    required_text(draft.get("ZenBend"), f"sense {index}.DraftEvidence.ZenBend", errors)
    required_text(draft.get("CounterexampleOrLimit"), f"sense {index}.DraftEvidence.CounterexampleOrLimit", errors)
    required_text(draft.get("AliasRationale"), f"sense {index}.DraftEvidence.AliasRationale", errors)
    split = draft.get("DifferentThingTest") or {}
    decision = required_text(split.get("Decision"), f"sense {index}.DifferentThingTest.Decision", errors)
    if decision not in {"one-thing", "different-thing"}:
        errors.append(f"sense {index}.DifferentThingTest.Decision: use one-thing or different-thing")
    required_text(split.get("Reason"), f"sense {index}.DifferentThingTest.Reason", errors)
    for field in ("ModifierControls", "FamilyControls"):
        controls = draft.get(field)
        if not isinstance(controls, list) or not controls:
            errors.append(f"sense {index}.DraftEvidence.{field}: explicit controls or a reasoned not-applicable row required")
    validation = sense.get("Validation")
    if validation not in {"provisional", "multi-source", "disputed"} and accepted_legacy_validation != validation:
        errors.append(
            f"sense {index}.Validation: use provisional, multi-source, or disputed; "
            f"legacy values such as single-source are merge-unstable"
        )
    work_ids = draft.get("IndependentWorkIds") or []
    if validation == "multi-source" and len(set(work_ids)) < 2:
        errors.append(f"sense {index}.IndependentWorkIds: multi-source requires two distinct works")
    evidence_keys = set(draft.get("OpeningClaimEvidenceKeys") or [])
    if not evidence_keys:
        errors.append(f"sense {index}.OpeningClaimEvidenceKeys: opening must name its stored evidence rows")
    occurrences = [compile_occurrence(row, f"sense {index}.occurrence {oi}", errors)
                   for oi, row in enumerate(sense.get("Occurrences") or [], 1)]
    anchors = [compile_claim_anchor(
        row, f"sense {index}.claim anchor {ai}", source_term, errors
    )
               for ai, row in enumerate(sense.get("ClaimAnchors") or [], 1)]
    available = {f"o{n}" for n in range(1, len(occurrences) + 1)} | {f"a{n}" for n in range(1, len(anchors) + 1)}
    unknown = evidence_keys - available
    if unknown:
        errors.append(f"sense {index}.OpeningClaimEvidenceKeys: unknown keys {sorted(unknown)}")
    sense["Occurrences"] = occurrences
    current_authority_rows = draft.get("SourceAuthorityRows") or []
    if len(current_authority_rows) == len(occurrences):
        for oi, (occurrence, authority_row) in enumerate(
            zip(occurrences, current_authority_rows), 1
        ):
            if not isinstance(authority_row, dict) or authority_row.get("RelPath") != occurrence.get("RelPath"):
                errors.append(
                    f"sense {index}.DraftEvidence.SourceAuthorityRows[{oi}].RelPath: "
                    "must match the current retained occurrence source"
                )
        current_work_ids = {
            row.get("WorkId") for row in current_authority_rows
            if isinstance(row, dict) and row.get("WorkId")
        }
        if set(draft.get("IndependentWorkIds") or []) != current_work_ids:
            errors.append(
                f"sense {index}.IndependentWorkIds: must exactly match the current retained "
                "SourceAuthorityRows work inventory"
            )
        current_families = {
            row.get("WitnessFamilyId") for row in current_authority_rows
            if isinstance(row, dict) and row.get("WitnessFamilyId")
        }
        stale_family_findings = [
            row.get("Finding") for row in (draft.get("HighValueEvidenceLedger") or [])
            if isinstance(row, dict)
            and row.get("Disposition") == "keep"
            and isinstance(row.get("Finding"), str)
            and ":" in row["Finding"]
            and row["Finding"] not in current_families
        ]
        if stale_family_findings:
            errors.append(
                f"sense {index}.DraftEvidence.HighValueEvidenceLedger: retained family ids "
                f"absent from current SourceAuthorityRows: {stale_family_findings!r}"
            )
    if anchors or not omit_empty_anchors:
        sense["ClaimAnchors"] = anchors
    else:
        sense.pop("ClaimAnchors", None)
    # Link inventories are derived from structured evidence, not hand-maintained
    # parallel lists. Explicit names must remain grounded in the current retained
    # actor/context rows; stale actors from superseded evidence fail closed.
    explicit_related = sense.get("RelatedMasters") or []
    if not isinstance(explicit_related, list):
        errors.append(f"sense {index}.RelatedMasters: must be a list of master-name strings")
        explicit_related = []
    invalid_related = [name for name in explicit_related if not isinstance(name, str) or not name.strip()]
    if invalid_related:
        errors.append(
            f"sense {index}.RelatedMasters: values must be nonempty master-name strings; "
            f"got {invalid_related!r}"
        )
    evidence_related = []
    for row in [*occurrences, *anchors]:
        names = [row.get("MasterName")]
        names.extend(
            context.get("MasterName")
            for context in row.get("ContextMasters") or []
            if isinstance(context, dict)
        )
        for name in names:
            if name and name not in evidence_related:
                evidence_related.append(name)
    stale_related = [
        name for name in explicit_related
        if isinstance(name, str) and name.strip() and name not in evidence_related
    ]
    if stale_related:
        errors.append(
            f"sense {index}.RelatedMasters: names absent from current retained actor/context "
            f"evidence: {stale_related!r}"
        )
    related = evidence_related
    sense["RelatedMasters"] = related
    derived_source_texts = list(dict.fromkeys(
        row.get("RelPath") for row in [*occurrences, *anchors] if row.get("RelPath")
    ))
    sense["SourceTexts"] = derived_source_texts
    # Independently accepted legacy entries can contain reviewed link inventories
    # that predate derivation from evidence order. A repair worksheet may preserve
    # those exact accepted bytes explicitly; this is opt-in and research-only.
    for field in ("SourceTexts", "RelatedMasters"):
        if field in accepted_derived:
            if require_pipeline_v2 and accepted_derived[field] != sense[field]:
                errors.append(
                    f"sense {index}.DraftAcceptedDerivedFields.{field}: "
                    "pipeline-v2 accepted bytes must equal the mechanically derived evidence inventory"
                )
            sense[field] = accepted_derived[field]
    return sense


def compile_draft(
    payload: dict,
    require_pipeline_v2: bool = False,
    worksheet_path: Path | None = None,
) -> tuple[dict, list[str]]:
    errors = []
    if payload.get("SchemaVersion") != 1:
        errors.append("SchemaVersion must be 1")
    if require_pipeline_v2:
        validate_new_entry_pipeline(payload, errors, worksheet_path=worksheet_path)
    source = json.loads(json.dumps(payload.get("Entry") or {}, ensure_ascii=False))
    # A post-draft reviewer may adjudicate and write exact RelatedTerms directly
    # into the worksheet.  FamilyHarvest remains authoritative when it actually
    # carries accepted or grandfathered terms, but an empty harvest must not
    # erase those reviewed worksheet links during canonical rendering.
    harvest = payload.get("FamilyHarvest") or {}
    if isinstance(harvest, dict) and harvest.get("PolicyVersion") == 1:
        accepted = {}
        for edge in harvest.get("Edges") or []:
            if isinstance(edge, dict) and edge.get("decision") == "accept" and isinstance(edge.get("SourceSenseIndex"), int):
                accepted.setdefault(edge["SourceSenseIndex"], []).append(edge.get("targetTerm"))
        inherited = {}
        for row in harvest.get("GrandfatheredRelatedTerms") or []:
            if isinstance(row, dict) and isinstance(row.get("SourceSenseIndex"), int):
                inherited.setdefault(row["SourceSenseIndex"], []).extend(row.get("Terms") or [])
        for index, sense in enumerate(source.get("Senses") or []):
            terms = [term for term in [*accepted.get(index, []), *inherited.get(index, [])] if isinstance(term, str) and term.strip()]
            if terms:
                sense["RelatedTerms"] = list(dict.fromkeys(terms))
    entry = {key: value for key, value in source.items() if key != "Senses"}
    for field in ("Id", "SourceTerm", "CorpusBaselineSha256", "CreatedBy"):
        required_text(entry.get(field), field, errors)
    entry["Senses"] = [compile_sense(sense, index, errors, require_pipeline_v2=require_pipeline_v2)
                       for index, sense in enumerate(source.get("Senses") or [], 1)]
    if not entry["Senses"]:
        errors.append("Entry.Senses: at least one sense is required")
    def strip_research(value):
        if isinstance(value, list):
            return [strip_research(item) for item in value]
        if isinstance(value, dict):
            return {key: strip_research(item) for key, item in value.items() if not key.startswith("Draft")}
        return value

    accepted_published_actor_proofs = payload.get("DraftAcceptedPublishedActorProofs") or []
    entry = strip_research(entry)
    for accepted in accepted_published_actor_proofs:
        si = accepted["sense"]
        field = accepted["field"]
        oi = accepted["index"]
        entry["Senses"][si][field][oi]["DraftActorProof"] = accepted["value"]
    if FORBIDDEN.search(json.dumps(entry, ensure_ascii=False)):
        errors.append("reader-facing entry contains forbidden English")
    return entry, errors


def atomic_write(path: Path, data: bytes) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(data)
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("worksheet", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument(
        "--new-entry",
        action="store_true",
        help="Require the integrated construction-pipeline-v2 admission, dossier, semantic, actor, and claim decisions.",
    )
    parser.add_argument(
        "--preserve-existing-bytes",
        action="store_true",
        help="After all controls pass, preserve an existing output's bytes only when its parsed JSON deep-equals the compiled entry.",
    )
    args = parser.parse_args()
    raw = args.worksheet.read_bytes()
    payload = json.loads(raw.decode("utf-8-sig"))
    entry, errors = compile_draft(
        payload,
        require_pipeline_v2=args.new_entry,
        worksheet_path=args.worksheet,
    )
    output = args.output or args.worksheet.with_name("entry.v2.json")
    rendered = (json.dumps(entry, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    semantic_parity = None
    preserved_sha = None
    if args.preserve_existing_bytes:
        if not output.exists():
            errors.append("--preserve-existing-bytes requires an existing output")
        elif not errors:
            existing = output.read_bytes()
            try:
                existing_entry = json.loads(existing.decode("utf-8-sig"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                errors.append(f"existing output is not valid JSON: {exc}")
            else:
                semantic_parity = existing_entry == entry
                if not semantic_parity:
                    errors.append("compiled JSON differs semantically from existing output; bytes not preserved")
                else:
                    rendered = existing
                    preserved_sha = sha(existing)
    report = {
        "hardPass": not errors,
        "worksheet": str(args.worksheet),
        "worksheetSha256": sha(raw),
        "output": str(output),
        "outputSha256": sha(rendered) if not errors else None,
        "errors": errors,
        "mode": "preserve-existing-bytes" if args.preserve_existing_bytes else "canonical-render",
        "semanticParityWithExistingOutput": semantic_parity,
        "preservedExistingByteSha256": preserved_sha,
        "newEntryPipelineRequired": args.new_entry,
        "constructionPipelineVersion": payload.get("ConstructionPipelineVersion"),
    }
    report_path = args.report or args.worksheet.with_name("evidence-compile-report.json")
    atomic_write(report_path, (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    if errors:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2
    atomic_write(output, rendered)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
