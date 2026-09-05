# Blind reviewer 1 verification of r1b rows against frozen materials.
# Laws applied exactly as specified in the review brief.
import json, io, hashlib, os, re, sys
from collections import Counter

BASE = r'C:\programmieren\MergeWorkCbeta\CBETA-Translator\runs\CLAUDE-RUNS\RUN-20260711-1248-full-cbeta-translation\dictionary-build\maintenance'
ROWS = os.path.join(BASE, 'r1b-blind-r1-rows-20260903.json')
OUTDIR = os.path.join(BASE, 'subagents', '20260903-r1b-blind-r1-reviewer-1')

d = json.load(io.open(ROWS, encoding='utf-8'))
retired = set(d['retiredRels'])
pins = d['materials']
mdir = d['materialsDir']

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

# ---------- STEP 1: materials integrity ----------
pin_problems = []
actual = {}
for root, dirs, files in os.walk(mdir):
    for fn in files:
        p = os.path.join(root, fn)
        rel = os.path.relpath(p, mdir).replace('\\', '/')
        actual[rel] = sha256_file(p)
for rel in sorted(pins):
    want = pins[rel].lower()
    got = actual.get(rel)
    if got is None:
        pin_problems.append('pinned file missing from materialsDir: %s' % rel)
    elif got != want:
        pin_problems.append('sha256 mismatch %s: header=%s actual=%s' % (rel, want, got))
for rel in sorted(actual):
    if rel not in pins:
        pin_problems.append('unpinned file present under materialsDir: %s' % rel)
materialsPinsOk = len(pin_problems) == 0

# ---------- material cache ----------
_cache = {}
def load(which, eid):
    key = (which, eid)
    if key not in _cache:
        p = os.path.join(mdir, which, eid + '.json')
        with io.open(p, encoding='utf-8') as f:
            _cache[key] = json.load(f)
    return _cache[key]

def get_sense(e, si):
    senses = e.get('Senses') or []
    if not (1 <= si <= len(senses)):
        return None
    return senses[si - 1]

def canon(o):
    return json.dumps(o, ensure_ascii=False, sort_keys=True)

def trunc(s, n=80):
    if s is None:
        return 'None'
    s = str(s)
    return s if len(s) <= n else s[:n] + '...(%d chars)' % len(s)

def removed_indices(pre_occs, post_occs):
    """Return sorted 1-based pre indices whose parsed objects are absent from post (multiset)."""
    post_ms = Counter(canon(o) for o in post_occs)
    removed = []
    for j, o in enumerate(pre_occs, 1):
        c = canon(o)
        if post_ms[c] > 0:
            post_ms[c] -= 1
        else:
            removed.append(j)
    return removed

# ---------- STEP 2: verify every row ----------
rows = d['rows']
flags = []
ok_count = 0
per_class = Counter()

# group sibling rows per (entry, si) for composed-removal diagnosis
sib = {}
for r in rows:
    if r['class'] == 'occ-remove-retired':
        sib.setdefault((r['entry'], r['si']), []).append(r)

for row in rows:
    rid = row['rowId']
    cls = row['class']
    per_class[cls] += 1
    entry, si = row['entry'], row['si']
    try:
        pE = load('pre', entry)
        qE = load('post', entry)
    except Exception as ex:
        flags.append({'rowId': rid, 'reason': 'material load failed for entry %s: %r' % (entry, ex)})
        continue
    problems = []
    pS = get_sense(pE, si)
    qS = get_sense(qE, si)

    if cls == 'occ-remove-retired':
        oi = row['oi']
        if pS is None:
            problems.append('law a fail: pre Senses[%d] does not exist (pre has %d senses)' % (si - 1, len(pE.get('Senses') or [])))
        else:
            occs = pS.get('Occurrences') or []
            if not (1 <= oi <= len(occs)):
                problems.append('law a fail: pre occurrence index oi=%d out of range; pre sense %d has %d occurrences' % (oi, si, len(occs)))
            else:
                occ = occs[oi - 1]
                if occ.get('RelPath') != row['relPath']:
                    problems.append('law b fail: pre occ[oi=%d].RelPath=%r != row.relPath=%r' % (oi, occ.get('RelPath'), row['relPath']))
                if row['relPath'] not in retired:
                    problems.append('law b fail: row.relPath=%r not in header retiredRels %s' % (row['relPath'], sorted(retired)))
                if (occ.get('Kwic') or '') != (row['removedKwic'] or ''):
                    problems.append('law c fail Kwic mismatch: pre=%s ; row=%s' % (trunc(occ.get('Kwic')), trunc(row['removedKwic'])))
                if occ.get('MasterName') != row['masterName']:
                    problems.append('law c fail: pre occ.MasterName=%r != row.masterName=%r' % (occ.get('MasterName'), row['masterName']))
        # law d + e need post sense
        if qS is None:
            problems.append('law d/e fail: post Senses[%d] does not exist (post has %d senses)' % (si - 1, len(qE.get('Senses') or [])))
        else:
            qoccs = qS.get('Occurrences') or []
            if pS is not None:
                poccs = pS.get('Occurrences') or []
                expected = [o for j, o in enumerate(poccs, 1) if j != oi]
                if qoccs != expected:
                    rem = removed_indices(poccs, qoccs)
                    sibids = [x['rowId'] for x in sib.get((entry, si), []) if x['rowId'] != rid]
                    problems.append(
                        'law d fail: post occurrences (%d) != pre-minus-oi=%d (%d pre occurrences). '
                        'Post == pre minus 1-based indices %s (sibling rows in same sense: %s)' % (
                            len(qoccs), oi, len(poccs), rem, ','.join(sibids) or 'none'))
            qrels = [o.get('RelPath') for o in qoccs]
            if row.get('postOccurrenceRels') != qrels:
                problems.append('law e fail: row.postOccurrenceRels=%s != post material RelPaths in order=%s' % (row.get('postOccurrenceRels'), qrels))
            if row.get('postOccurrenceCount') != len(qoccs):
                problems.append('law e fail: row.postOccurrenceCount=%r != len(post occurrences)=%d' % (row.get('postOccurrenceCount'), len(qoccs)))

    elif cls == 'note-count-rewrite':
        if pS is None:
            problems.append('law a fail: pre Senses[%d] does not exist (pre has %d senses)' % (si - 1, len(pE.get('Senses') or [])))
        if qS is None:
            problems.append('law a-e fail: post Senses[%d] does not exist (post has %d senses)' % (si - 1, len(qE.get('Senses') or [])))
        else:
            pN = (pS.get('Note') if pS else None) or ''
            qN = qS.get('Note') or ''
            before, after = row['before'], row['after']
            if before not in pN:
                problems.append('law a fail: pre Note does not contain row.before=%r; pre Note=%s' % (before, trunc(pN, 200)))
            if after not in qN:
                problems.append('law a fail: post Note does not contain row.after=%r; post Note=%s' % (after, trunc(qN, 200)))
            if before in qN:
                problems.append('law a fail: post Note still contains row.before=%r' % before)
            qoccs = qS.get('Occurrences') or []
            n = len(qoccs)
            m = len(set(o.get('RelPath') for o in qoccs))
            if row.get('postOccurrences') != n:
                problems.append('law b fail: row.postOccurrences=%r != live post occurrence count=%d' % (row.get('postOccurrences'), n))
            if row.get('postDistinctRels') != m:
                problems.append('law b fail: row.postDistinctRels=%r != live distinct post RelPath count=%d' % (row.get('postDistinctRels'), m))
            mm = re.search(r'(\d+)\s+exact occurrences\s+from\s+(\d+)\s+distinct works', after)
            if not mm:
                problems.append('law c fail: cannot parse "N exact occurrences from M distinct works" from row.after=%r' % after)
            else:
                N, M = int(mm.group(1)), int(mm.group(2))
                if (N, M) != (n, m):
                    problems.append('law c fail: row.after states %d occurrences / %d distinct works but live post counts are %d / %d' % (N, M, n, m))
    else:
        problems.append('unknown row class %r' % cls)

    if problems:
        flags.append({'rowId': rid, 'reason': ' | '.join(problems)})
    else:
        ok_count += 1

# ---------- summary notes ----------
note_bits = []
note_bits.append('Materials: %d pinned files, %d files on disk, pins %s.' % (len(pins), len(actual), 'all match' if materialsPinsOk else 'MISMATCH: ' + '; '.join(pin_problems[:5])))
rel_in_rows = Counter(r['relPath'] for r in rows if r['class'] == 'occ-remove-retired')
note_bits.append('Removals by retired rel: %s.' % ', '.join('%s=%d' % kv for kv in sorted(rel_in_rows.items())))
# composed-removal audit for multi-row senses
comp = []
for (entry, si), rs in sorted(sib.items()):
    if len(rs) < 2:
        continue
    try:
        pS = get_sense(load('pre', entry), si)
        qS = get_sense(load('post', entry), si)
        rem = removed_indices(pS.get('Occurrences') or [], qS.get('Occurrences') or [])
        ois = sorted(x['oi'] for x in rs)
        comp.append('%s s%d: %d rows ois=%s, material removed idx=%s, %s' % (
            entry, si, len(rs), ois, rem,
            'composed-consistent' if rem == ois else 'COMPOSED MISMATCH'))
    except Exception as ex:
        comp.append('%s s%d: audit error %r' % (entry, si, ex))
note_bits.append('Multi-removal senses vs law d literal: ' + ' ; '.join(comp))
note_bits.append('Rows OK: %d/%d; flags: %d. Classes: %s.' % (ok_count, len(rows), len(flags), dict(per_class)))

verdict = {
    'reviewer': 1,
    'materialsPinsOk': materialsPinsOk,
    'rowsChecked': len(rows),
    'flags': flags,
    'notes': ' '.join(note_bits),
}

with io.open(os.path.join(OUTDIR, 'verdicts.json'), 'w', encoding='utf-8') as f:
    json.dump(verdict, f, ensure_ascii=False, indent=2)

print('materialsPinsOk:', materialsPinsOk)
if pin_problems:
    print('PIN PROBLEMS:')
    for x in pin_problems:
        print('  ', x)
print('rowsChecked:', len(rows), 'ok:', ok_count, 'flags:', len(flags))
for fl in flags:
    print('FLAG', fl['rowId'], '::', fl['reason'])
print()
print('NOTES:', verdict['notes'])
