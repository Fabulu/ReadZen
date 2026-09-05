# Follow-up grounding for flagged rows: joint-removal consistency per entry,
# exact kwic diff position, and pre/post rel dumps for flagged entries.
import io
import json
import os
from collections import defaultdict

ROWS_PATH = r"C:\programmieren\MergeWorkCbeta\CBETA-Translator\runs\CLAUDE-RUNS\RUN-20260711-1248-full-cbeta-translation\dictionary-build\maintenance\r1b-blind-r1-rows-20260903.json"
MAT = r"C:\programmieren\MergeWorkCbeta\CBETA-Translator\runs\CLAUDE-RUNS\RUN-20260711-1248-full-cbeta-translation\dictionary-build\maintenance\r1b-blind-r1-materials"


def load(path):
    with io.open(path, "r", encoding="utf-8") as f:
        return json.load(f)


doc = load(ROWS_PATH)
rows = doc["rows"]

by_entry = defaultdict(list)
for r in rows:
    by_entry[r["entry"]].append(r)

print("=== joint-removal consistency per multi-row entry ===")
for entry, rs in sorted(by_entry.items()):
    if len(rs) < 2:
        continue
    pre = load(os.path.join(MAT, "pre", entry + ".json"))
    post = load(os.path.join(MAT, "post", entry + ".json"))
    rem = defaultdict(list)  # si -> [oi,...] claimed
    for r in rs:
        if r["class"] == "occ-remove-retired":
            rem[r["si"]].append((r["oi"], r["rowId"]))
    for si, ois in sorted(rem.items()):
        pre_l = pre["Senses"][si - 1]["Occurrences"]
        post_l = post["Senses"][si - 1]["Occurrences"]
        keep = [o for j, o in enumerate(pre_l, 1) if j not in {oi for oi, _ in ois}]
        print("%s si=%d claimed_removals=%s pre_len=%d post_len=%d joint_consistent=%s" % (
            entry, si, [(rid, oi) for oi, rid in ois], len(pre_l), len(post_l), keep == post_l))

print()
print("=== R0032 exact kwic diff ===")
r32 = [r for r in rows if r["rowId"] == "R0032"][0]
pre = load(os.path.join(MAT, "pre", r32["entry"] + ".json"))
occ = pre["Senses"][r32["si"] - 1]["Occurrences"][r32["oi"] - 1]
mat_kwic = occ["Kwic"]
row_kwic = r32["removedKwic"]
print("material len=%d row len=%d equal=%s" % (len(mat_kwic), len(row_kwic), mat_kwic == row_kwic))
i = 0
while i < min(len(mat_kwic), len(row_kwic)) and mat_kwic[i] == row_kwic[i]:
    i += 1
print("first diff at char %d: material=%r row=%r" % (i, mat_kwic[i - 15:i + 15], row_kwic[i - 15:i + 15]))
print("identical to R0006 kwic:", mat_kwic == [r for r in rows if r["rowId"] == "R0006"][0]["removedKwic"])

print()
print("=== R0000 vs R0001 (t_022d58242948 si1) ===")
pre022 = load(os.path.join(MAT, "pre", "t_022d58242948.json"))
post022 = load(os.path.join(MAT, "post", "t_022d58242948.json"))
pre_l = pre022["Senses"][0]["Occurrences"]
post_l = post022["Senses"][0]["Occurrences"]
print("pre rels:", [o["RelPath"] for o in pre_l])
print("post rels:", [o["RelPath"] for o in post_l])
print("pre[4] (oi=5):", pre_l[4]["RelPath"], "| master:", pre_l[4]["MasterName"], "| kwic head:", pre_l[4]["Kwic"][:30])
print("pre[0] (oi=1):", pre_l[0]["RelPath"], "| master:", pre_l[0]["MasterName"])
print("post == pre minus oi4:", post_l == [o for j, o in enumerate(pre_l, 1) if j != 4])

print()
print("=== R0016 (t_0c53a5a2243b si2) ===")
pre16 = load(os.path.join(MAT, "pre", "t_0c53a5a2243b.json"))
post16 = load(os.path.join(MAT, "post", "t_0c53a5a224c.json")) if os.path.exists(os.path.join(MAT, "post", "t_0c53a5a224c.json")) else load(os.path.join(MAT, "post", "t_0c53a5a2243b.json"))
print("pre senses:", len(pre16["Senses"]), "| si2 occ count:", len(pre16["Senses"][1]["Occurrences"]))
print("post si2 rels:", [o["RelPath"] for o in post16["Senses"][1]["Occurrences"]])
print("post si1 rels:", [o["RelPath"] for o in post16["Senses"][0]["Occurrences"]])

print()
print("=== R0048 vs R0001 postOccurrenceRels sanity ===")
r48 = [r for r in rows if r["rowId"] == "R0048"][0]
print("R0048 relPath:", r48["relPath"], "| in retiredRels:", r48["relPath"] in doc["retiredRels"])
print("pre[0] kwic head:", pre_l[0]["Kwic"][:40])
print("R0048 removedKwic head:", r48["removedKwic"][:40])
print("pre[0] kwic == R0048 kwic:", pre_l[0]["Kwic"] == r48["removedKwic"])

print()
print("=== note rows (t_50d75aeeeef1) ===")
pre50 = load(os.path.join(MAT, "pre", "t_50d75aeeeef1.json"))
post50 = load(os.path.join(MAT, "post", "t_50d75aeeeef1.json"))
print("pre Note:", pre50["Senses"][0]["Note"])
print("post Note:", post50["Senses"][0]["Note"])
print("post occ rels:", [o["RelPath"] for o in post50["Senses"][0]["Occurrences"]])

print()
print("=== R0051 (t_5306489d35c6) master grounding ===")
pre51 = load(os.path.join(MAT, "pre", "t_5306489d35c6.json"))
occ51 = pre51["Senses"][0]["Occurrences"][1]
print("pre si1 oi2 RelPath:", occ51["RelPath"], "| MasterName:", repr(occ51["MasterName"]), "| Kwic == row:", occ51["Kwic"] == [r for r in rows if r["rowId"] == "R0051"][0]["removedKwic"])

print()
print("=== rows per entry summary ===")
print("entries referenced:", len(by_entry), "| rows:", len(rows))
