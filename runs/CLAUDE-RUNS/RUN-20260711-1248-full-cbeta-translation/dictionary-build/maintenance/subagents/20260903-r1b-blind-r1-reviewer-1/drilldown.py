# Supplementary drill-down for byte-grounded flag reasons + un-rowed change audit.
import json, io, os
from collections import Counter

BASE = r'C:\programmieren\MergeWorkCbeta\CBETA-Translator\runs\CLAUDE-RUNS\RUN-20260711-1248-full-cbeta-translation\dictionary-build\maintenance'
ROWS = os.path.join(BASE, 'r1b-blind-r1-rows-20260903.json')
d = json.load(io.open(ROWS, encoding='utf-8'))
mdir = d['materialsDir']
rows = {r['rowId']: r for r in d['rows']}

def load(which, eid):
    return json.load(io.open(os.path.join(mdir, which, eid + '.json'), encoding='utf-8'))

def canon(o):
    return json.dumps(o, ensure_ascii=False, sort_keys=True)

def first_diff(a, b):
    if a == b:
        return 'IDENTICAL'
    i = 0
    while i < min(len(a), len(b)) and a[i] == b[i]:
        i += 1
    lo = max(0, i - 15)
    return 'first diff at char %d (len pre=%d row=%d): pre[...]=%r row[...]=%r' % (
        i, len(a), len(b), a[lo:i+25], b[lo:i+25])

print('==== 1. t_022d58242948 sense 1 tables ====')
pE = load('pre', 't_022d58242948'); qE = load('post', 't_022d58242948')
pS = pE['Senses'][0]; qS = qE['Senses'][0]
print('pre occs:')
for j, o in enumerate(pS['Occurrences'], 1):
    print('  [%d] %s | %s | kwic=%s...' % (j, o.get('RelPath'), o.get('MasterName'), (o.get('Kwic') or '')[:20]))
print('post occs:')
for j, o in enumerate(qS['Occurrences'], 1):
    print('  [%d] %s | %s | kwic=%s...' % (j, o.get('RelPath'), o.get('MasterName'), (o.get('Kwic') or '')[:20]))
for rid in ('R0000', 'R0001', 'R0048', 'R0013'):
    r = rows[rid]
    print(rid, 'entry=%s si=%s oi=%s rel=%s master=%s kwic=%s...' % (
        r['entry'], r['si'], r['oi'], r['relPath'], r['masterName'], r['removedKwic'][:20]))
# where in PRE does R0000's claimed (relPath, kwic, master) tuple actually live?
want = rows['R0000']
for si, s in enumerate(pE['Senses'], 1):
    for j, o in enumerate(s['Occurrences'], 1):
        if o.get('Kwic') == want['removedKwic']:
            print('R0000 removedKwic found in pre sense %d occ [%d]: rel=%s master=%s' % (si, j, o.get('RelPath'), o.get('MasterName')))

print()
print('==== 2. R0016 row + its entry pre/post ====')
r = rows['R0016']
print(json.dumps({k: v for k, v in r.items() if k != 'rowSha'}, ensure_ascii=False)[:700])
pE = load('pre', r['entry']); qE = load('post', r['entry'])
print('entry senses: pre=%d post=%d' % (len(pE['Senses']), len(qE['Senses'])))
for si, s in enumerate(pE['Senses'], 1):
    print('pre sense %d: %d occs: %s' % (si, len(s.get('Occurrences') or []), [o.get('RelPath') for o in (s.get('Occurrences') or [])]))
for si, s in enumerate(qE['Senses'], 1):
    print('post sense %d: %d occs: %s' % (si, len(s.get('Occurrences') or []), [o.get('RelPath') for o in (s.get('Occurrences') or [])]))
# does the row's relPath/kwic exist anywhere in this entry's pre?
found = False
for si, s in enumerate(pE['Senses'], 1):
    for j, o in enumerate(s.get('Occurrences') or [], 1):
        if o.get('RelPath') == r.get('relPath') or o.get('Kwic') == r.get('removedKwic'):
            print('R0016 target present in pre sense %d occ [%d]: rel=%s kwic-match=%s' % (si, j, o.get('RelPath'), o.get('Kwic') == r.get('removedKwic')))
            found = True
if not found:
    print('R0016 relPath/removedKwic NOT found anywhere in pre entry', r['entry'])
# does the claimed kwic live in any OTHER entry's pre?
hits = []
for f in sorted(os.listdir(os.path.join(mdir, 'pre'))):
    eid = f[:-5]
    e = load('pre', eid)
    for si, s in enumerate(e.get('Senses') or [], 1):
        for j, o in enumerate(s.get('Occurrences') or [], 1):
            if o.get('Kwic') == r.get('removedKwic'):
                hits.append((eid, si, j, o.get('RelPath')))
print('R0016 removedKwic found in pres:', hits)

print()
print('==== 3. R0032 kwic divergence ====')
r = rows['R0032']
pE = load('pre', r['entry'])
occ = pE['Senses'][r['si'] - 1]['Occurrences'][r['oi'] - 1]
print('R0032 entry=%s si=%s oi=%s rel=%s master=%s' % (r['entry'], r['si'], r['oi'], r['relPath'], r['masterName']))
print('pre occ rel=%s master=%s' % (occ.get('RelPath'), occ.get('MasterName')))
print(first_diff(occ.get('Kwic') or '', r['removedKwic']))

print()
print('==== 4. R0051 row + pre occ detail ====')
r = rows['R0051']
print(json.dumps({k: v for k, v in r.items() if k != 'rowSha'}, ensure_ascii=False)[:500])
pE = load('pre', r['entry']); qE = load('post', r['entry'])
occ = pE['Senses'][r['si'] - 1]['Occurrences'][r['oi'] - 1]
print('pre occ full keys:', sorted(occ.keys()))
print('pre occ: rel=%r master=%r kwic=%s...' % (occ.get('RelPath'), occ.get('MasterName'), (occ.get('Kwic') or '')[:30]))

print()
print('==== 5. duplicate-oi pairs (both passed) ====')
for eid in ('t_13951a5b5260', 't_5306489d35c6'):
    for rid, r in rows.items():
        if r['class'] == 'occ-remove-retired' and r['entry'] == eid:
            print(rid, 'oi=%s rel=%s master=%s' % (r['oi'], r['relPath'], r['masterName']))
    pE = load('pre', eid); qE = load('post', eid)
    print('  pre rels:', [o.get('RelPath') for o in pE['Senses'][0]['Occurrences']])
    print('  post rels:', [o.get('RelPath') for o in qE['Senses'][0]['Occurrences']])

print()
print('==== 6. un-rowed change audit over all 43 entries ====')
occ_rows = {}
note_rows = {}
for r in d['rows']:
    if r['class'] == 'occ-remove-retired':
        occ_rows.setdefault((r['entry'], r['si']), []).append(r['oi'])
    else:
        note_rows.setdefault((r['entry'], r['si']), []).append(r['rowId'])
anomalies = []
total_removed = 0
entries = sorted(f[:-5] for f in os.listdir(os.path.join(mdir, 'pre')))
for eid in entries:
    pE = load('pre', eid); qE = load('post', eid)
    ps, qs = pE.get('Senses') or [], qE.get('Senses') or []
    if len(ps) != len(qs):
        anomalies.append('%s: sense count pre=%d post=%d' % (eid, len(ps), len(qs)))
        continue
    for si in range(1, len(ps) + 1):
        pocc = ps[si-1].get('Occurrences') or []
        qocc = qs[si-1].get('Occurrences') or []
        pre_ms = Counter(canon(o) for o in pocc); post_ms = Counter(canon(o) for o in qocc)
        removed = list((pre_ms - post_ms).elements())
        added = list((post_ms - pre_ms).elements())
        n_removed = sum(removed.count(x) for x in set(removed))
        n_removed = len(removed); n_added = len(added)
        total_removed += n_removed
        claimed = len(occ_rows.get((eid, si), []))
        if n_removed != claimed:
            anomalies.append('%s s%d: material occurrence removals=%d, rows claimed=%d (ois %s)' % (eid, si, n_removed, claimed, occ_rows.get((eid, si))))
        if n_added:
            anomalies.append('%s s%d: %d occurrence(s) ADDED in post (not a removal!)' % (eid, si, n_added))
        # note changes not covered by a note row?
        pN = ps[si-1].get('Note') or ''; qN = qs[si-1].get('Note') or ''
        if pN != qN and (eid, si) not in note_rows:
            anomalies.append('%s s%d: Note changed in post but NO note-count-rewrite row (pre=%r post=%r)' % (eid, si, pN[:60], qN[:60]))
        # non-occurrence, non-note field changes in the sense?
        for k in ps[si-1]:
            if k in ('Occurrences', 'Note'):
                continue
            if ps[si-1].get(k) != qs[si-1].get(k):
                anomalies.append('%s s%d: sense field %r changed' % (eid, si, k))
    for k in pE:
        if k != 'Senses' and pE.get(k) != qE.get(k):
            anomalies.append('%s: entry-level field %r changed (%r -> %r)' % (eid, k, str(pE.get(k))[:40], str(qE.get(k))[:40]))
print('entries audited:', len(entries), 'total material occurrence removals:', total_removed, 'rows claiming removals:', sum(len(v) for v in occ_rows.values()))
for a in anomalies:
    print('  ANOMALY:', a)
