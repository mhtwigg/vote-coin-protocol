The Vote Coin Protocol

A Multi-Layered, Verifiable Voting Framework — White Paper v2.0, Revision 4

Michael Twigg, PhD · ORCID 0009-0002-4607-6919

DOI

The permanent, citable copy of this work is archived on Zenodo: https://doi.org/10.5281/zenodo.23087313

What it is

A design for a paper-ballot voting system with a public, per-ballot audit trail.

The voter-verified paper ballot is the ballot of record.
Every tablet-printed ballot is reconciled against its digital record when cast.
The Cardano blockchain holds only salted fingerprints of ballots, anchored as one Merkle root per polling facility per hour — never a vote, a name, or personal data.
Voting is in person only, in an air-gapped facility, with no barcode or QR code on the ballot.

The paper covers architecture, threat model, three-institution governance, a privacy impact assessment, legal compliance (HAVA, VVSG 2.0, draft VVSG 2.1, Executive Order 14248), scaling arithmetic, a four-phase testing plan, and fifty objections with answers.

It is a design offered for public review and an early technology consultation with the U.S. Election Assistance Commission. It is not certified or deployed.

What is in this repository
File	What it is
Vote Coin Protocol - White Paper v2.0 Rev 4 (2026-10-01).pdf	The white paper (94 pages, 27 figures). Start here.
Vote Coin Protocol - Figures Worked Examples - Rev 4 (2026-10-01).pdf	Every number in the figures and on the cover, with the inputs needed to recompute it
verify_figures.py, figdata.json	Recomputes every figure value (71 checks)
verify_chain_settings.py, chainload.json	Recomputes the dated Cardano settings and chain-load table (13 checks)
README.txt	What each check covers
Check the numbers yourself

Requires Python 3 only — standard library, nothing to install, nothing downloaded. Download the repository (green Code button → Download ZIP), unzip it, open a terminal in that folder, and run:

bash
python3 verify_figures.py          # expect: 71 passed, 0 failed
python3 verify_chain_settings.py   # expect: 13 passed, 0 failed

See README.txt for what each check covers. The sample ballots in the figures (including ballot 0515 0293) are illustrative, not real votes.

Why Cardano?

Cardano was chosen on engineering merits: deterministic transactions that cannot half-succeed, ledger-native tokens with one small audited validator as the only custody code, a formal-methods research culture, and low energy use. The design is not tied to one chain. It touches the ledger only to anchor 32-byte batch fingerprints, so anchors can be re-published to any public ledger without touching a single ballot, and the Vote Coin token can move to any ledger with equivalent token features. The paper ballot, not the blockchain, is the record (Objection 15).

How to cite

Twigg, M. (2026). The Vote Coin Protocol — White Paper v2.0 Revision 4 (Version 2.0). Zenodo. https://doi.org/10.5281/zenodo.23087313

GitHub's "Cite this repository" button gives the same citation in APA and BibTeX.

Feedback

Questions, corrections and critique are welcome — please open an Issue on this repository.

License

© 2026 Michael Twigg. Licensed under Creative Commons Attribution 4.0 International (CC BY 4.0). You may share and adapt this work, including commercially, as long as you give credit.

The protocol is not affiliated with the unrelated "VoteCoin (VOT)" cryptocurrency.
