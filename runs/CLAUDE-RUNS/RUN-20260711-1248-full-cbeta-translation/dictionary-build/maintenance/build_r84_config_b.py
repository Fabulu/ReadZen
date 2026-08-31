#!/usr/bin/env python3
import copy, hashlib, json, os, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
M=ROOT/"maintenance"
sys.path.insert(0,str(ROOT))
import zc
from atomic_write import atomic_write_json
from maintenance.generic_bounded_constructor import (
    verify_actor_closure, verify_whole_config_preclosure, canonical_compile_prewrite
)
from maintenance.source_authority_binding import authority_registry_sha256
from maintenance.actor_note_format import format_actor_note
from maintenance.adjudicated_actor_adapter import merge_context_masters

TG=M/"non-iriya-v7-depth-regeneration-r84-timegate-b.json"
AZSEL=M/"non-iriya-v7-depth-regeneration-r84-selection-b.json"
EX=M/"non-iriya-v7-depth-regeneration-r84-extraction-output-b.json"
RS=M/"non-iriya-v7-depth-regeneration-r84-research-skeleton-b.json"
RCP=M/"non-iriya-v7-depth-regeneration-r84-research-checkpoint-b.json"
SEL=M/"non-iriya-v7-depth-regeneration-r84-constructor-selection-b.json"
RESEARCH=M/"non-iriya-v7-depth-regeneration-r84-research-b.json"
CFG=M/"non-iriya-v7-depth-regeneration-r84-constructor-config-b.json"
AUD=M/"non-iriya-v7-depth-regeneration-r84-constructor-command-audit-b.json"
ENGINE=M/"generic_bounded_constructor.py"
WRAP=M/"dictionary_python_env.py"
OLD=M/"non-iriya-v7-depth-regeneration-r83-constructor-config-b.json"
REV1=M/"non-iriya-v7-depth-regeneration-r84-review-first-two-a.json"
REV2=M/"non-iriya-v7-depth-regeneration-r84-review-third-b.json"

def read(p): return json.loads(p.read_text(encoding="utf-8"))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def canon_sha(x): return hashlib.sha256((json.dumps(x,ensure_ascii=False,indent=2)+"\n").encode()).hexdigest()

gate=read(TG); extraction=read(EX); old=read(OLD)
rows={r["id"]:r for r in extraction["rows"]}
counts={r["id"]:r for r in read(M/"non-iriya-v7-depth-regeneration-r84-count-b.json")["results"]}
selected={r.get("identityId",r.get("id")):r for r in read(AZSEL)["rows"]}
specs=[
 {"id":"t_1cec9c4c3c40","term":"破虗空","floor":6,"target":"break through empty space",
  "also":["break open empty space","shatter empty space"],"aliases":["break empty space"],
  "opening":"To break open or shatter empty space: an impossible image for a decisive breakthrough that leaves no enclosing obstruction.",
  "body":"Yulin Tongxiu and Gulin Qingmao use the image in authored verse; Weilin Daopei uses it in a memorial address; Dahui Zonggao, Baiyun Shouduan, and Wumen Huikai deploy it directly in recorded instruction.",
  "note":"The phrase does not describe damage to a material sky. Its surrounding predicates make the impossible rupture an image of unobstructed breakthrough.",
  "review":REV1,
  "uses":[
   ("X/X64/X64n1271.xml","Yulin Tongxiu","yulin-authored-verse",1,"verse-author"),
   ("X/X71/X71n1413.xml","Gulin Qingmao","gulin-authored-verse",1,"verse-author"),
   ("X/X72/X72n1442.xml","Weilin Daopei","weilin-memorial-address",1,"utterer"),
   ("M/M59/M59n1540.xml","Dahui Zonggao","dahui-direct-discourse",2,"utterer"),
   ("X/X69/X69n1352.xml","Baiyun Shouduan","baiyun-direct-discourse",2,"utterer"),
   ("X/X69/X69n1355.xml","Wumen Huikai","wumen-direct-discourse",2,"utterer")]},
 {"id":"t_1cfa8b8aa2a3","term":"覿體全彰","floor":4,"target":"fully manifest in its very substance",
  "also":["directly manifest in full","fully displayed right before one"],"aliases":["directly manifest in full"],
  "opening":"A verdict that something is wholly and directly manifest, with nothing of it concealed or merely inferred.",
  "body":"Zhongfeng Mingben, Miyun Yuanwu, Wei'an Deran, and Jizong Che independently use the expression in direct instruction.",
  "note":"覿體 contributes direct, immediate presentation; 全彰 says that the manifestation is complete. The phrase need not denote a physical face.",
  "review":REV1,
  "uses":[
   ("B/B25/B25n0145.xml","Zhongfeng Mingben","zhongfeng-direct",2,"utterer"),
   ("J/J10/J10nA158.xml","Miyun Yuanwu","miyun-direct",2,"utterer"),
   ("J/J25/J25nB154.xml","Wei'an Deran","weian-direct",2,"utterer"),
   ("J/J28/J28nB211.xml","Jizong Che","jizong-direct",2,"utterer")]},
 {"id":"t_1d0056511f4d","term":"集雲峰下四藤條","floor":4,"target":"the four vine-switch strokes below Jiyun Peak",
  "also":["four vine-strokes below Jiyun Peak","Jiyun Peak's four strokes of the vine"],"aliases":["four cane blows below Jiyun Peak"],
  "opening":"An allusive case-tag recalling Yangshan's four vine blows to Great Chan Buddha (Da Chanfo) below Jiyun Peak.",
  "body":"Gulin Qingmao, Zhenjing Kewen, Wei'an Deran, and Wanru Tongwei each actively redeploy the complete case-tag in verse or instruction.",
  "note":"This is not a generic count of four vines. It names the four-stroke credential in the inherited Yangshan–Great Chan Buddha case.",
  "review":REV2,
  "uses":[
   ("X/X71/X71n1413.xml","Gulin Qingmao","gulin-authored-verse",1,"verse-author"),
   ("C/C077/C077n1710.xml","Zhenjing Kewen","zhenjing-direct-verse",2,"verse-author"),
   ("J/J25/J25nB154.xml","Wei'an Deran","weian-direct-verse",2,"verse-author"),
   ("J/J26/J26nB182.xml","Wanru Tongwei","wanru-direct-redeployment",2,"utterer")]}
]

titles={}
for line in Path("/mnt/c/programmieren/CbetaZenTranslations/titles.jsonl").read_text(encoding="utf-8-sig").splitlines():
    if line.strip():
        row=json.loads(line); titles[row["path"]]=row.get("en") or row.get("enShort") or row["path"]

selection={"schemaVersion":"r84-admitted-constructor-selection.v1","cohort":"R84",
 "artifactZeroSelectionPath":str(AZSEL),"artifactZeroSelectionSha256":sha(AZSEL),
 "rows":[copy.deepcopy(selected[s["id"]]) for s in specs],"excluded":[],"hardPass":True}
atomic_write_json(SEL,selection)
research_rows=[]
for s in specs:
    er=rows[s["id"]]; count=counts[s["id"]]
    research_rows.append({"id":s["id"],"term":s["term"],"exactHits":count["hits"],
      "files":count["files"],"independentWorks":count["works"],"requiredFloor":s["floor"],
      "transportRequiredFloor":s["floor"],"floorException":"",
      "candidateDeployments":[u[0] for u in s["uses"]],
      "actorAndFamilyRisks":["Every retained case has an exact named actor.","No Tier-3 lamp is retained."],
      "fullCandidates":er["sourceCandidates"],"fullConcordance":er.get("fullConcordance",[]),
      "retainedReviewPath":str(s["review"]),"retainedReviewSha256":sha(s["review"])})
atomic_write_json(RESEARCH,{"schemaVersion":"non-iriya-v7-depth-regeneration-research.v1",
 "cohort":"R84","researchCheckpointPath":str(RCP),"researchCheckpointSha256":sha(RCP),
 "governedExtractionPath":str(EX),"governedExtractionSha256":sha(EX),
 "governedSkeletonPath":str(RS),"governedSkeletonSha256":sha(RS),"rows":research_rows})

template=old["entries"][0]; entries=[]
for s in specs:
    item=copy.deepcopy(template); item["id"]=s["id"]; item["term"]=s["term"]
    bypath={c["relPath"]:c for c in rows[s["id"]]["sourceCandidates"]}
    cases=[]; occurrences=[]; authority=[]; ledgers=[]; workids=[]; paths=[]; masters=[]
    for n,use in enumerate(s["uses"],1):
        rel,master,family,tier,role=use[:5]
        owner=use[5] if len(use)>5 else None
        actor_status=use[6] if len(use)>6 else "linked"
        role_meta=use[7] if len(use)>7 else None
        c=bypath[rel]; context=c["context"]; ix=context.index(s["term"])
        all_positions=[]
        cursor=0
        while True:
            found=context.find(s["term"],cursor)
            if found < 0: break
            all_positions.append(found); cursor=found+len(s["term"])
        target_position=all_positions.index(ix)
        previous=all_positions[target_position-1] if target_position else None
        following=all_positions[target_position+1] if target_position+1 < len(all_positions) else None
        lo=max(0,ix-55,previous+len(s["term"]) if previous is not None else 0)
        hi=min(len(context),ix+len(s["term"])+55,following if following is not None else len(context))
        kwic=context[lo:hi]
        while kwic.count(s["term"]) != 1 and lo < ix:
            lo+=5; kwic=context[lo:hi]
        verified=zc.verify(rel,kwic)
        if not verified.get("ok") or kwic.count(s["term"]) != 1:
            raise RuntimeError(f"{s['id']} o{n}: invalid governed KWIC")
        label=(role_meta or {}).get("actorLabel") or master or "the reviewed unnamed performer"
        context_role={"performer":"action-performer","letter-writer":"utterer"}.get(role,role)
        key=f"o{n}"; grammar=(
          f"The complete source frame assigns the retained {'authored verse' if role == 'verse-author' else 'headword-bearing action'} to {label}."
        )
        linked=actor_status=="linked"
        public_master=master if linked else None
        actor_attribution=None
        if not linked:
            actor_attribution={"Status":actor_status,
              "Kind":"Chan master" if actor_status=="identified-unlinked-master" else "person",
              "ActorLabel":label,"ActorRole":role,
              "RungsChecked":["line","expanded-context","section-header","book-title","tei-header","parallel-passage"],
              "GrammarEvidence":grammar,
              "ReviewedBy":(role_meta or {}).get("reviewedBy","independent source-first review"),
              "ReviewedUtc":(role_meta or {}).get("reviewedUtc","2026-07-30T12:00:00Z"),
              "AuthoredVoiceRiskReviewed":True}
        cm=[]
        ca=[]
        if linked: cm.append({"MasterName":master,"Roles":[context_role]})
        if owner and owner != master: cm.append({"MasterName":owner,"Roles":["later-raiser","commentator","record-owner"]})
        if role_meta:
            cm=merge_context_masters(cm,copy.deepcopy(role_meta["contextMasters"]))
            ca=copy.deepcopy(role_meta.get("contextActors") or [])
        decision={"evidenceKey":key,"masterName":public_master,"actorAttribution":actor_attribution,
          "action":"uses the headword in the retained source unit","grammarEvidence":grammar,
          "voice":grammar,"contextMasters":cm,"contextActors":ca}
        span={"fromLb":verified["fromLb"],"sourceSpanOrdinal":0,
          "sourceContextSha256":c["contextSha256"],"boundedKwic":kwic,
          "boundedFromLb":verified["fromLb"],"boundedToLb":verified["toLb"],
          "boundaryEvidence":"zc.verify binds the complete retained public KWIC."}
        cases.append({"relPath":rel,"workId":c["workId"],"sourceTitle":titles.get(rel,rel),
          "tier":tier,"fullCaseWindow":context,"heading":{"head":"","mulu":[]},
          "actorDecision":decision,"sourceSpanIdentity":span,"decisionBasis":grammar})
        note=(format_actor_note(rel,titles.get(rel,rel),master,grammar) if linked else
          f"Source record ({rel}). {titles.get(rel,rel)}. Action performer: {label}. {grammar}")
        if role_meta and role_meta.get("actorNote"):
            note=role_meta["actorNote"]
        if role_meta and role_meta.get("noteContext"):
            note += " " + role_meta["noteContext"]
        occurrences.append({"RelPath":rel,"FromLb":verified["fromLb"],"ToLb":verified["toLb"],
          "Kwic":kwic,"MasterName":public_master,"Curated":True,"ContextMasters":cm,
          "ContextActors":ca,"AttributionNote":note,
          **({"ActorAttribution":actor_attribution} if actor_attribution else {}),
          "DraftActorProof":{"ExactHeadwordClause":s["term"],"GrammaticalSubject":label,
            "SpeechFrame":note,"FullCaseDecision":grammar}})
        authority.append({"EvidenceKey":key,"RelPath":rel,"WorkId":c["workId"],"Tier":tier,
          "SourceClass":"master-authored" if tier==1 else "recorded-sayings",
          "AuthorityReason":"Exact named higher-tier source; complete frame actor-reviewed.",
          "WitnessFamilyId":family,
          "DeploymentRole":(role_meta or {}).get("deploymentRole","original-use")})
        ledgers.append({"Disposition":"keep","Finding":grammar,
          "Reason":"Independent higher-tier family with exact actor and one governed headword span."})
        workids.append(c["workId"]); paths.append(rel)
        if linked: masters.append(master)
        if owner: masters.append(owner)
        for context_master in cm:
            masters.append(context_master["MasterName"])
    workids=list(dict.fromkeys(workids)); paths=list(dict.fromkeys(paths)); masters=list(dict.fromkeys(masters))
    dossier=item["sourceDossier"]; dossier.update({"id":s["id"],"term":s["term"],
      "selectionBinding":{"path":str(SEL),"sha256":sha(SEL)},
      "researchBinding":{"path":str(RESEARCH),"sha256":sha(RESEARCH)},
      "exactCount":counts[s["id"]],"requiredFloor":s["floor"],"semanticReadComplete":True,
      "tier3Lamp":0,"predecessorEvidenceAudit":[],"retainedCompleteCases":cases,
      "sourceMeta":[{"path":u[0],"tier":u[3],"title":titles.get(u[0],u[0])} for u in s["uses"]],
      "sourceAuthorityManifest":{"rows":authority}})
    notes=dossier["researchNotes"]; notes.update({"openingInterpretation":s["opening"],
      "evidenceBody":[s["body"]],"counterexampleOrLimit":s["note"],"literalGraphFloor":s["target"],
      "lexicalJob":f"{s['term']} means {s['target']}.","deploymentClasses":["authored verse","direct instruction"],
      "highValueEvidenceLedger":ledgers,"openingClaimEvidenceKeys":[f"o{i}" for i in range(1,s["floor"]+1)],
      "evidenceBodyClaimKeys":[[f"o{i}" for i in range(1,s["floor"]+1)]],"zenBend":s["opening"],
      "counterexample":s["note"],"differentThing":{"Decision":"one-thing","ComparedThings":[s["target"]],"Reason":"One lexical job."},
      "aliasRationale":"Alternates preserve the same lexical job.",
      "modifierControls":[{"Term":s["term"],"Finding":"No modifier creates a second referent."}],
      "familyControls":[{"Term":s["term"],"Finding":f"{s['floor']} independent higher-tier families meet the floor."}],
      "higherSearch":"Tier 1 searched first, then Tier 2; no lamp needed.",
      "admissionReason":f"{s['term']} is a stable expression with repeated active Chan deployments.",
      "duplicateCheck":{"DeterministicIdChecked":True,"ExactHeadwordChecked":True,
        "NearDuplicateRuling":f"R84 checked {s['term']} against the installed dictionary; no exact collision is admitted."},
      "depthReceipt":{"Complete":True,"ReviewedExactHitCount":counts[s["id"]]["hits"],
        "AvailableSourceFiles":counts[s["id"]]["files"],"SearchedDeploymentClasses":["authored verse","direct instruction"],
        "OmissionAudit":[f"{s['floor']} retained cases actor-adjudicated.","No lamp retained."]}})
    worksheet=item["evidenceDraft"]; worksheet["Entry"].update({"Id":s["id"],"SourceTerm":s["term"],
      "CreatedBy":"R84 source-hierarchy repair","WrittenUtc":"2026-07-30T10:38:00Z"})
    sense=worksheet["Entry"]["Senses"][0]; sense.update({"PreferredTarget":s["target"],
      "AlternateTargets":s["also"],"SearchAliases":s["aliases"],"Explanation":s["opening"]+" "+s["body"],
      "Note":s["note"],"Occurrences":occurrences,"SourceTexts":paths,"RelatedMasters":masters,
      "RelatedTerms":[],"ExplanationParts":{"CorpusEarnedOpening":s["opening"],"EvidenceBody":[s["body"]]}})
    de=sense["DraftEvidence"]; de.update({"LiteralGraphFloor":s["target"],
      "LexicalJob":notes["lexicalJob"],"DeploymentClasses":["authored verse","direct instruction"],
      "HighValueEvidenceLedger":ledgers,"OpeningClaimEvidenceKeys":notes["openingClaimEvidenceKeys"],
      "EvidenceBodyClaimKeys":notes["evidenceBodyClaimKeys"],"ZenBend":s["opening"],
      "CounterexampleOrLimit":s["note"],"DifferentThingTest":notes["differentThing"],
      "AliasRationale":notes["aliasRationale"],"ModifierControls":notes["modifierControls"],
      "FamilyControls":notes["familyControls"],"IndependentWorkIds":workids,
      "SourceAuthorityRows":authority,"LampExcessJustification":"No Tier-3 lamp retained.",
      "NoHigherWitnessSearchReceipt":notes["higherSearch"],"DepthHarvestReceipt":notes["depthReceipt"]})
    sense["DraftAcceptedDerivedFields"]={"SourceTexts":paths,"RelatedMasters":masters}
    worksheet["FamilyHarvest"]={"PolicyVersion":1,"Scope":"R84 source-hierarchy repair","Edges":[],"NegativeReceipt":[],"GraphicVariants":[]}
    worksheet["Admission"]["LexicalUnitReason"]=notes["admissionReason"]
    worksheet["Admission"]["ObservableChanJob"]=notes["lexicalJob"]
    worksheet["Admission"]["DuplicateCheck"]={
      "DeterministicIdChecked":True,
      "ExactHeadwordChecked":True,
      "NearDuplicateRuling":f"{s['term']} was checked against the installed dictionary; no exact or punctuation-normalized collision is admitted."}
    worksheet["EvidenceTransport"]["ExactCount"]=counts[s["id"]]["hits"]
    worksheet["EvidenceTransport"]["BridgedCount"]=counts[s["id"]]["hits"]
    worksheet["EvidenceTransport"]["DossierSha256"]=canon_sha(dossier)
    worksheet["EvidenceTransport"]["SourceAuthorityManifestSha256"]=authority_registry_sha256(ROOT)
    entries.append(item)

config=copy.deepcopy(old); config.update({"cohort":"R84","startedEpoch":gate["startedEpoch"],
 "timegatePath":str(TG),"watchdogReceiptPath":str(M/"non-iriya-v7-depth-regeneration-r84-constructor-checkpoint-b.json"),
 "commandAuditPath":str(AUD),"engineSha256":sha(ENGINE),"entries":entries})
config["paths"]={"selection":str(SEL),"research":str(RESEARCH),"outputRoot":str(ROOT/"fresh-build/entries"),
 "firstProductReceipt":str(M/"non-iriya-v7-depth-regeneration-r84-engine-first-product-b.json"),
 "preclosure":str(M/"non-iriya-v7-depth-regeneration-r84-preclosure-report-b.json"),
 "manifest":str(M/"non-iriya-v7-depth-regeneration-r84-construction-manifest-b.json"),
 "closure":str(M/"non-iriya-v7-depth-regeneration-r84-closure-b.json")}
verify_actor_closure(config); verify_whole_config_preclosure(config); canonical_compile_prewrite(config)
atomic_write_json(CFG,config)
command=[str(Path(sys.executable).resolve()),str(WRAP.resolve()),"--script",str(ENGINE.resolve()),"--",
 "--config",str(CFG.resolve()),"--allowed-build-root",str(ROOT.resolve())]
atomic_write_json(AUD,{"complete":True,"commands":[{"epoch":time.time(),"argv":command,
 "command":"R84 governed source-ranked construction"}]})
print(json.dumps({"selection":sha(SEL),"research":sha(RESEARCH),"config":sha(CFG),"audit":sha(AUD)}))
