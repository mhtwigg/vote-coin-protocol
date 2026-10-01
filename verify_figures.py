#!/usr/bin/env python3
"""The Vote Coin Protocol, White Paper v2.0, Revision 2: reader kit.

Recomputes every value printed on the cover and in the 27 figures from figdata.json, using only
the Python 3 standard library (hashlib, json, math). Nothing is installed and nothing is fetched.

    python3 verify_figures.py                  (figdata.json next to this script)
    python3 verify_figures.py path/to/figdata.json

Each check prints PASS or FAIL, and the last line gives the totals. The exit status is 0 only when
every check passes. The companion "Figures: Worked Examples" explains each value and its source.

The eight ballots are samples, not votes. Their salts are published only because they are samples:
a real salt never leaves the Secure Node's sealed audit log.
"""
import hashlib, json, math, os, sys

H = lambda b: hashlib.sha256(b).digest()
here = os.path.dirname(os.path.abspath(__file__))
path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, 'figdata.json')
with open(path, encoding='utf-8') as f:
    D = json.load(f)

passed = failed = 0
def check(label, ok, shown=''):
    global passed, failed
    if ok:
        passed += 1
    else:
        failed += 1
    print(('PASS  ' if ok else 'FAIL  ') + label + (f'   [{shown}]' if shown else ''))

def close(a, b, rel=1e-12):
    return abs(a - b) <= rel * max(1.0, abs(a), abs(b))

def section(title):
    print('\n' + title + '\n' + '-' * len(title))

def short(h):
    return h[:8] + '…' + h[-8:]

# ------------------------------------------------------------------------------------------------
section('0. The tools themselves')
# FIPS 180-4 example: SHA-256("abc")
check('SHA-256("abc") matches the NIST example',
      hashlib.sha256(b'abc').hexdigest() == 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')

def mth(leaves):
    """RFC 9162, section 2.1.1: the Merkle Tree Hash of a list of byte strings."""
    n = len(leaves)
    if n == 0:
        return H(b'')
    if n == 1:
        return H(b'\x00' + leaves[0])
    k = 1
    while k * 2 < n:
        k *= 2                      # the largest power of two smaller than n
    return H(b'\x01' + mth(leaves[:k]) + mth(leaves[k:]))

# Certificate Transparency reference inputs and roots for trees of 1 to 8 leaves
# (transparency-dev/merkle, testonly/constants.go)
ct = [b'', b'\x00', b'\x10', b'\x20\x21', b'\x30\x31', b'\x40\x41\x42\x43',
      bytes(range(0x50, 0x58)), bytes(range(0x60, 0x70))]
ct_roots = ['6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d',
            'fac54203e7cc696cf0dfcb42c92a1d9dbaf70ad9e621f4bd8d98662f00e3c125',
            'aeb6bcfe274b70a14fb067a5e5578264db0fa9b51af5e0ba159158f329e06e77',
            'd37ee418976dd95753c1c73862b9398fa2a2cf9b4ff0fdfe8b30cd95209614b7',
            '4e3bbb1f7b478dcfe71fb631631519a3bca12c9aefca1612bfce4c13a86264d4',
            '76e67dadbcdf1e10e1b74ddc608abd2f98dfb16fbce75277b5232a127f2087ef',
            'ddb89be403809e325750d3d263cd78929c2942b7942a34b77e122c9594a74c8c',
            '5dc9da79a70659a9ad559cb701ded9a2ab9d823aad2f4960cfe370eff4604328']
check('the tree code reproduces the 8 published RFC 9162 reference roots',
      all(mth(ct[:n]).hex() == ct_roots[n - 1] for n in range(1, 9)))

# ------------------------------------------------------------------------------------------------
section('1. The sample batch (every figure; Figure 27 in full)')
S, B = D['sample'], D['batch']
check('the batch holds ' + str(len(B)) + ' ballots, as its label says', S['n'] == len(B) == 8,
      f"{S['node']} · batch {S['batch_label']} · {S['window']} · {S['n']} ballots (sample)")
check('batch label is the sequence number in four digits', S['batch_label'] == f"{S['batch_seq']:04d}")

def record(index, selections):
    """Section 8.1: the ballot record R, UTF-8 text, one field per line, each line ending in a line feed."""
    return ('INDEX: ' + index + '\n' + ''.join(f'{c}: {v}\n' for c, v in selections)).encode('utf-8')

for b in B:
    R = record(b['index'], b['selections'])
    s = bytes.fromhex(b['salt'])
    fp = H(R + s)
    ok = (R.decode('utf-8') == b['R_text'] and len(R) == b['R_bytes'] and len(s) == 32 and len(b['index']) == 8
          and b['printed'] == b['index'][:4] + ' ' + b['index'][4:] and fp.hex() == b['fingerprint']
          and H(b'\x00' + fp).hex() == b['leaf'])
    check(f"ballot {b['printed']}: record ({len(R)} bytes), 32-byte salt, fingerprint and leaf", ok,
          'fingerprint ' + short(b['fingerprint']))

# two orders: the tree sorts by fingerprint; the archive box files by validation index
by_fp = sorted(B, key=lambda b: b['fingerprint'])
check('tree order = fingerprints in ascending order (positions 1 to 8)',
      [b['pos'] for b in by_fp] == list(range(1, 9)) and by_fp == B,
      ' < '.join(b['fingerprint'][:4] for b in by_fp))
by_idx = sorted(B, key=lambda b: b['index'])
check('box order = validation indices in ascending order (Figure 7)',
      [b['index'] for b in by_idx] == D['box_order'] and all(b['box_pos'] == i + 1 for i, b in enumerate(by_idx)),
      ', '.join(b['printed'] for b in by_idx))

# ------------------------------------------------------------------------------------------------
section('2. The tree (cover; Figures 12, 16, 27)')
leaves = [bytes.fromhex(b['leaf']) for b in B]
l1 = [H(b'\x01' + leaves[i] + leaves[i + 1]) for i in range(0, 8, 2)]
l2 = [H(b'\x01' + l1[i] + l1[i + 1]) for i in range(0, 4, 2)]
root = H(b'\x01' + l2[0] + l2[1])
check('level 1: four nodes, SHA-256(0x01 ‖ left ‖ right)', [x.hex() for x in l1] == D['level1'],
      ' '.join(x.hex()[:8] for x in l1))
check('level 2: two nodes', [x.hex() for x in l2] == D['level2'], ' '.join(x.hex()[:8] for x in l2))
check('root, built level by level', root.hex() == D['root'], D['root'])
check('root, rebuilt by the RFC 9162 recursive definition from the eight fingerprints',
      mth([bytes.fromhex(b['fingerprint']) for b in B]).hex() == D['root'])

# ------------------------------------------------------------------------------------------------
section('3. Ballot 0515 0293, step by step (Figures 1, 2, 11, 25)')
b0 = D['ballot_0293']
R = record(b0['index'], b0['selections'])
s = bytes.fromhex(b0['salt'])
Vd = H(R + s)                                                      # from the tablet's record
check('record R: ' + str(len(R)) + ' bytes, byte for byte', R.hex() == b0['R_hex'] and len(R) == b0['R_bytes'])
check('hash input R ‖ s: ' + str(len(R + s)) + ' bytes', len(R + s) == b0['hash_input_bytes'])
check('Vd = SHA-256(R ‖ s), from the tablet', Vd.hex() == b0['Vd'], b0['Vd'])
# the paper: OCR reads the printed characters; the record is rebuilt from them, joined to the same salt
printed_lines = [b0['printed']] + [f'{c}: {v}' for c, v in b0['selections']]
R_ocr = ('INDEX: ' + printed_lines[0].replace(' ', '') + '\n' + ''.join(l + '\n' for l in printed_lines[1:])).encode()
Vp = H(R_ocr + s)
check('Vp = SHA-256(R ‖ s), rebuilt from the printed ballot', Vp.hex() == b0['Vp'])
check('S = 1: the paper and the record agree', int(Vd == Vp) == b0['S'] == 1)
check('the receipt\'s tracking code is the fingerprint itself', b0['tracking_code'] == Vd.hex() == B[b0['pos'] - 1]['fingerprint'])
check('0293 is 4 of 8 by fingerprint and 1 of 8 by index', (b0['pos'], b0['box_pos']) == (4, 1)
      and B[b0['pos'] - 1]['index'] == b0['index'] and by_idx[b0['box_pos'] - 1]['index'] == b0['index'])
# what if the tablet had recorded CONTEST 2: CHOICE B while printing CHOICE A (Figure 11)
ce = D['counterexample']
sel_bad = [(c, 'CHOICE B' if c == 'CONTEST 2' else v) for c, v in b0['selections']]
R_bad = record(b0['index'], sel_bad)
Vd_bad = H(R_bad + s)
check("what if: a tablet that records CHOICE B gives a different Vd", R_bad.decode() == ce['recorded_R_text']
      and Vd_bad.hex() == ce['Vd_bad'] and Vd_bad != Vp, short(ce['Vd_bad']))
check('what if: S = 0, the mismatch is caught', int(Vd_bad == Vp) == ce['S'] == 0)

# ------------------------------------------------------------------------------------------------
section('4. The inclusion proof for 0515 0293 (Figure 16)')
cur = H(b'\x00' + Vd)
ok = cur.hex() == b0['leaf']
for i, (step, rec) in enumerate(zip(D['proof_0293'], D['proof_steps']), 1):
    sib = bytes.fromhex(step['hash'])
    left, right = (sib, cur) if step['side'] == 'left' else (cur, sib)
    cur = H(b'\x01' + left + right)
    ok_step = left.hex() == rec['input_left'] and right.hex() == rec['input_right'] and cur.hex() == rec['output']
    check(f"step {i}: sibling on the {step['side']}", ok_step, short(cur.hex()))
    ok = ok and ok_step
check('the proof ends at the anchored root', cur.hex() == D['root'], short(D['root']))
check(f"proof size: {len(D['proof_0293'])} hashes x 32 bytes = {32 * len(D['proof_0293'])} bytes",
      D['proof_bytes'] == 32 * len(D['proof_0293']) == 96)

# ------------------------------------------------------------------------------------------------
section('5. Proof sizes (Figures 16, 17)')
def path_len(m, n):
    """RFC 9162 section 2.1.3.1: the audit-path length for leaf m of a tree with n leaves."""
    if n <= 1:
        return 0
    k = 1
    while k * 2 < n:
        k *= 2
    return 1 + (path_len(m, k) if m < k else path_len(m - k, n - k))
for row in D['proof_sizes']:
    n = row['n']
    k = math.ceil(math.log2(n))
    ok = row['max_hashes'] == k and row['max_bytes'] == 32 * k
    if n <= 4096:                                                  # build the real paths and take the longest
        ok = ok and max(path_len(m, n) for m in range(n)) == k
    check(f"n = {n:,}: at most ⌈log2 n⌉ = {k} hashes, {32 * k} bytes", ok)

# ------------------------------------------------------------------------------------------------
section('6. Batch rules and finality (Figures 2, 12, 17; Section 8.1)')
r = D['batch_rules']; g = r['genesis']
depth = 3 * g['securityParam'] / g['activeSlotsCoeff']
check(f"3k/f = 3 × {g['securityParam']:,} ÷ {g['activeSlotsCoeff']} = {depth:,.0f} slots", depth == r['finality_slots'] == 129600)
check(f"{depth:,.0f} slots × {g['slotLength_s']} s = {depth * g['slotLength_s'] / 3600:g} hours",
      depth * g['slotLength_s'] / 3600 == r['finality_hours'] == 36)
check(f"a batch closes after {r['T_minutes']} minutes or {r['B_max']:,} ballots, never with fewer than {r['n_min']}",
      (r['T_minutes'], r['B_max'], r['n_min']) == (60, 4096, 100))
check(f"anchored within 36 hours of poll close, final within {int(r['finality_hours'] * 2)}: the {r['dashboard_hours']}-hour dashboard window",
      2 * r['finality_hours'] <= r['dashboard_hours'])

# ------------------------------------------------------------------------------------------------
section('7. Capacity per Node (Figure 18; Sections 12.2-12.3)')
c = D['capacity']
for row in c['table']:
    ok = row['working'] == c['printers'] - row['failed'] and row['per_hour'] == row['working'] * c['per_printer'] \
         and row['meets_peak'] == (row['per_hour'] >= c['phase1_peak'][1])
    check(f"{row['failed']} printers failed: {row['working']} × {c['per_printer']} = {row['per_hour']:,} an hour"
          f"{' (meets the peak of 500)' if row['meets_peak'] else ' (below the peak)'}", ok)
T = min(c['printing_per_hour'], c['filing_per_hour'])
check(f"T = min({c['printing_per_hour']:,}, {c['filing_per_hour']:,}) = {T:,} an hour", T == c['throughput'] == 1000)
check(f"headroom over the Phase I peak: filing {c['filing_per_hour'] / c['phase1_peak'][1]:g}×, printing "
      f"{c['printing_per_hour'] / c['phase1_peak'][1]:g}×",
      (c['filing_headroom'], c['printing_headroom']) == (c['filing_per_hour'] / 500, c['printing_per_hour'] / 500) == (2, 3))
check(f"printers needed for the peak: ⌈500 ÷ 300⌉ = {math.ceil(500 / c['per_printer'])}; failures tolerated: "
      f"{c['printers'] - math.ceil(500 / c['per_printer'])}",
      (c['min_printers_for_peak'], c['failures_tolerated_at_peak']) == (2, 3))
check(f"stress test: {c['stress_test_per_hour']:,} an hour × {c['stress_test_hours']} hours = {c['stress_test_total']:,}",
      c['stress_test_per_hour'] * c['stress_test_hours'] == c['stress_test_total'] == 8000)

# ------------------------------------------------------------------------------------------------
section('8. The Phase I gate: the rule of three (Figure 23; Hanley & Lippman-Hand, 1983)')
q = D['rule_of_three']
n_exact = math.log(0.05) / math.log(1 - q['p_gate'])
check(f"n ≥ ln 0.05 ÷ ln(1 − 0.00001) = {n_exact:,.1f}, rounded up to {math.ceil(n_exact):,}",
      math.ceil(n_exact) == q['n_needed_exact'] == 299572)
check(f"so the gate asks for at least {q['n_gate']:,}", q['n_gate'] >= q['n_needed_exact'] and q['n_gate'] == 300000)
ub8 = 1 - 0.05 ** (1 / 8000)
check(f"8,000 ballots alone: 1 − 0.05^(1/8,000) = {ub8:.7f} = {ub8 * 100:.4f}%", close(ub8, q['ub_8000']))
ub3 = 1 - 0.05 ** (1 / 300000)
check(f"300,000 ballots: 1 − 0.05^(1/300,000) = {ub3:.4e}, below 0.001%", close(ub3, q['ub_300000']) and ub3 < 1e-5)
check(f"300,000 at 1,000 an hour = {300000 / 1000:g} hours of robotic testing", q['hours_at_1000'] == 300)

# ------------------------------------------------------------------------------------------------
section('9. Validation-index repeats (Figure 7; Section 8.1)')
N = D['index_space']
check('eight digits give 10^8 = 100,000,000 possible indices', N == 10 ** 8)
for n_s, v in D['index_repeats'].items():
    n = int(n_s)
    approx = 1 - math.exp(-n * (n - 1) / (2 * N))
    exact = 1 - math.exp(sum(math.log1p(-j / N) for j in range(n)))
    check(f"{n:,} draws: chance of at least one repeat ≈ {approx:.1%} (exact {exact:.4%})",
          close(approx, v['p_any_repeat']) and close(exact, v['p_any_repeat_exact'], 1e-9)
          and close(n * (n - 1) / (2 * N), v['expected_repeats']))

# ------------------------------------------------------------------------------------------------
section('10. Objection 7: the arithmetic of being noticed (Figure 26; Bernhard et al., 2020)')
o = D['obj7']
for n_s, v in o['p_at_least_one_report'].items():
    n = int(n_s)
    p = 1 - (1 - o['d']) ** n
    check(f"n = {n}: 1 − (1 − {o['d']})^{n} = {p:.1%}", close(p, v))
check(f"a {o['margin_example']}-vote margin is overturned by {o['margin_example'] // 2 + 1} flips (each moves it by 2)",
      o['flips_to_overturn'] == o['margin_example'] // 2 + 1 == 11)

# ------------------------------------------------------------------------------------------------
section('11. Throughput and salts (Figures 11, 14, 17)')
cd = D['cardano']
check(f"{cd['tps_observed']} transactions a second × 3,600 = {cd['tps_observed'] * 3600:,.0f} an hour",
      cd['tps_observed'] * 3600 == cd['tx_per_hour'] == 12600)
sl = D['salt']
check(f"a 32-byte salt has 2^256 = {2 ** 256:.2e} possible values", sl['bits'] == 8 * sl['bytes'] == 256
      and int(sl['values']) == 2 ** 256)

# ------------------------------------------------------------------------------------------------
section('12. The one hypothetical example (Figure 21)')
nd = D['illustrations']['node_day']
check(f"{nd['burns']:,} burned + {nd['provisional']} provisional + {nd['no_card']} without the card = "
      f"{nd['burns'] + nd['provisional'] + nd['no_card']:,} cast (spoiled, {nd['spoiled']}, stay outside the sum)",
      nd['burns'] + nd['provisional'] + nd['no_card'] == nd['cast'])

print(f'\n{passed} passed, {failed} failed')
sys.exit(0 if failed == 0 else 1)
