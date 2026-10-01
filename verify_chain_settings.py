#!/usr/bin/env python3
"""The Vote Coin Protocol - White Paper v2.0, Revision 4
Reader kit: the Cardano numbers stated "as of September 2026" (Sections 4.2, 12.1 and 12.2)

Recomputes, with the Python 3 standard library only:
  * the ada deposit (minimum ada) a Vote Coin output must carry, from the formula in CIP-55,
        deposit = (160 + size of the serialized output in bytes) x coinsPerUTxOByte,
    for a range of ways the output could be encoded, and
  * the chain's capacity from its block-size limit and average block interval, and
  * the chain load of per-voter Vote Coin burns at each phase (the table in Section 12.2), which is why the design
    moves to per-batch spent-tag lists from Phase III.

The protocol parameters below were read from Cardano mainnet on September 27, 2026 (epoch 658) through the Koios public
API (cli_protocol_params and epoch_params, read twice). Cardano's on-chain governance can change them: before relying on
these numbers, read the current values (any Cardano node prints them with `cardano-cli query protocol-parameters`) and
put them in PARAMS.

usage: python3 verify_chain_settings.py
"""
import json
PARAMS = {                          # Cardano mainnet, epoch 658, read September 27, 2026
    'utxoCostPerByte': 4310,        # lovelace per byte (1 ada = 1,000,000 lovelace)
    'maxTxSize': 16384,             # bytes
    'maxBlockBodySize': 90112,      # bytes
    'maxValueSize': 5000,           # bytes
}
GENESIS = {'activeSlotsCoeff': 0.05, 'slotLength': 1}   # mainnet Shelley genesis: one block per 20 slots on average
OVERHEAD = 160                                           # CIP-55: "constant overhead of 160 bytes"


# ---- minimal CBOR encoder (RFC 8949), enough for a Cardano transaction output -----------------------------------------
def _head(major, n):
    if n < 24:
        return bytes([major << 5 | n])
    for ai, size in ((24, 1), (25, 2), (26, 4), (27, 8)):
        if n < 1 << (8 * size):
            return bytes([major << 5 | ai]) + n.to_bytes(size, 'big')
    raise ValueError('integer too large')

def uint(n): return _head(0, n)
def bstr(b): return _head(2, len(b)) + b
def arr(*items): return _head(4, len(items)) + b''.join(items)
def cmap(pairs): return _head(5, len(pairs)) + b''.join(k + v for k, v in pairs)
def tag(t, item): return _head(6, t) + item


def output(address_len, name_len, datum, coin):
    """A post-Alonzo (map-form) output holding `coin` lovelace and one Vote Coin (quantity 1) under one policy."""
    address = bytes(address_len)                                # header byte + script hash (+ stake credential)
    value = arr(uint(coin), cmap([(bstr(bytes(28)), cmap([(bstr(bytes(name_len)), uint(1))]))]))
    pairs = [(uint(0), bstr(address)), (uint(1), value)]
    if datum == 'hash':                                         # [0, datum_hash]
        pairs.append((uint(2), arr(uint(0), bstr(bytes(32)))))
    elif datum == 'inline32':                                   # [1, #6.24(bytes .cbor plutus_data)], data = 32-byte string
        pairs.append((uint(2), arr(uint(1), tag(24, bstr(bstr(bytes(32)))))))
    return cmap(pairs)


def min_deposit(address_len, name_len, datum):
    """Smallest coin that satisfies CIP-55 for this output (the coin's own encoding size is part of the output)."""
    coin = 0
    while True:
        need = (OVERHEAD + len(output(address_len, name_len, datum, coin))) * PARAMS['utxoCostPerByte']
        if coin >= need:
            return coin, len(output(address_len, name_len, datum, coin))
        coin = need


results = []
def check(label, ok, detail=''):
    results.append(ok)
    print(('PASS  ' if ok else 'FAIL  ') + label + (f'  ({detail})' if detail else ''))


# 1. The encoder against known CBOR encodings (RFC 8949, Appendix A)
check('CBOR uint 0, 23, 24, 1000000', uint(0) == bytes.fromhex('00') and uint(23) == bytes.fromhex('17')
      and uint(24) == bytes.fromhex('1818') and uint(1000000) == bytes.fromhex('1a000f4240'))
check('CBOR byte string h\'01020304\'', bstr(bytes([1, 2, 3, 4])) == bytes.fromhex('4401020304'))
check('CBOR array [1, 2, 3] and map {1: 2, 3: 4}', arr(uint(1), uint(2), uint(3)) == bytes.fromhex('83010203')
      and cmap([(uint(1), uint(2)), (uint(3), uint(4))]) == bytes.fromhex('a201020304'))

# 2. The deposit for the ways a Vote Coin output could be encoded
print('\nDeposit for one Vote Coin output, at 4,310 lovelace per byte (September 2026):')
print('  address           token name  datum          output bytes   deposit (ada)')
cases = []
for addr_label, addr_len in (('script, no stake', 29), ('script + stake', 57)):
    for name_len in (0, 8, 32):
        for datum in ('none', 'hash', 'inline32'):
            coin, size = min_deposit(addr_len, name_len, datum)
            cases.append((addr_label, name_len, datum, size, coin))
            print(f'  {addr_label:<17} {name_len:>2} bytes    {datum:<13} {size:>6}         {coin / 1e6:.6f}')
lo = min(c[4] for c in cases); hi = max(c[4] for c in cases)
check('every case needs at least 1 ada and at most 1.5 ada ("about 1 to 1.5 ada")', 1_000_000 <= lo and hi <= 1_500_000,
      f'{lo / 1e6:.4f} to {hi / 1e6:.4f} ada')
check('4,310 lovelace per byte = 0.00431 ada per byte', PARAMS['utxoCostPerByte'] / 1e6 == 0.00431)
check('every output is far below maxValueSize (5,000 bytes)', max(c[3] for c in cases) < PARAMS['maxValueSize'])

# 3. Chain capacity (Section 12.1)
interval = GENESIS['slotLength'] / GENESIS['activeSlotsCoeff']
check('one block every 20 seconds on average (1 s slots, f = 0.05)', interval == 20, f'{interval:g} s')
rate = PARAMS['maxBlockBodySize'] / interval
check('90,112 bytes per 20 s = about 4.5 kilobytes a second', round(rate / 1000, 1) == 4.5, f'{rate:.1f} bytes/s')
check('a batch root (SHA-256) is 32 bytes, a small fraction of one 16,384-byte transaction',
      32 / PARAMS['maxTxSize'] < 0.01, f'{32 / PARAMS["maxTxSize"]:.2%}')

# 4. Chain load by phase (Section 12.2's table, Revision 4): per-voter burns against the chain's whole budget
print('\nChain load by phase, at September 2026 limits:')
BUDGET_PER_HOUR = rate * 3600                                       # bytes the whole chain can carry in an hour
BURN_BYTES = 100                                                    # planning figure per batched burn (generous; see below)
# what one batched burn actually adds to a transaction: one spending input plus one redeemer (CBOR, RFC 8949)
spend_input = arr(bstr(bytes(32)), uint(300))                       # [transaction id, output index]
redeemer = arr(uint(0), uint(300), _head(6, 121) + arr(), arr(uint(500_000), uint(200_000_000)))   # [tag, index, unit datum, [mem, steps]]
marginal = len(spend_input) + len(redeemer)
check(f'one batched burn adds about {marginal} bytes to a transaction, so 100 bytes a burn is a generous planning figure',
      40 <= marginal <= 60 and marginal < BURN_BYTES, f'{marginal} bytes')
phases = [('I', 'one municipal Node', 500), ('II', 'a county', 5_000), ('III', 'a state', 50_000)]
load = {}
for ph, who, peak in phases:
    burn_bytes = peak * BURN_BYTES
    load[ph] = {'peak_per_hour': peak, 'burn_bytes_per_hour': burn_bytes, 'share_of_chain': burn_bytes / BUDGET_PER_HOUR}
    print(f'  Phase {ph:<3} {who:<19} {peak:>7,} ballots/hour -> burns {burn_bytes / 1e3:>8,.0f} kB/hour = {100 * burn_bytes / BUDGET_PER_HOUR:5.1f}% of the chain')
IN_PERSON = 158_000_000 * 0.72                                      # EAC 2024 EAVS: more than 158 million ballots, over 72% in person
nat_bytes = IN_PERSON * BURN_BYTES
nat_days = nat_bytes / rate / 86400
load['IV'] = {'in_person_ballots': IN_PERSON, 'burn_bytes': nat_bytes, 'days_of_whole_chain': nat_days}
print(f'  Phase IV  the nation          {IN_PERSON / 1e6:.0f} million in-person ballots -> {nat_bytes / 1e9:.1f} GB = {nat_days:.0f} days of the whole chain')
roots_per_1000 = 1000 * 32
load['roots_per_1000_nodes'] = {'bytes_per_hour': roots_per_1000, 'share_of_chain': roots_per_1000 / BUDGET_PER_HOUR}
print(f'  Batch roots: 1,000 Nodes -> {roots_per_1000 / 1e3:.0f} kB/hour = {100 * roots_per_1000 / BUDGET_PER_HOUR:.1f}% of the chain')
check('the chain carries about 16.2 MB an hour and 389 MB a day', round(BUDGET_PER_HOUR / 1e6, 1) == 16.2 and round(rate * 86400 / 1e6) == 389,
      f'{BUDGET_PER_HOUR / 1e6:.1f} MB/hour, {rate * 86400 / 1e6:.0f} MB/day')
check('Phase I burns are under 1% of the chain; Phase III burns are about 31%', load["I"]["share_of_chain"] < 0.01 and round(100 * load["III"]["share_of_chain"]) == 31)
check('2024 in-person volume as per-voter burns is about 11.4 GB, about 29 days of the whole chain',
      round(nat_bytes / 1e9, 1) == 11.4 and round(nat_days) == 29, f'{nat_bytes / 1e9:.1f} GB, {nat_days:.1f} days')
json_out = {'params': PARAMS, 'budget_bytes_per_second': rate, 'budget_bytes_per_hour': BUDGET_PER_HOUR, 'burn_bytes_planning': BURN_BYTES,
            'burn_bytes_marginal': marginal, 'phases': load}
try:
    import os
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chainload.json'), 'w') as f:
        json.dump(json_out, f, indent=1)
except OSError:
    pass

print(f'\n{sum(results)} passed, {len(results) - sum(results)} failed')
