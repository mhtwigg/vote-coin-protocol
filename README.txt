The Vote Coin Protocol - White Paper v2.0, Revision 4
DOI: https://doi.org/10.5281/zenodo.23087313
Reader kit: recompute every number in the figures, and the dated Cardano numbers
=================================================================================

What is here
  figdata.json        Every value printed on the cover and in the 27 figures: the sample batch of
                      8 ballots (records, salts, fingerprints, leaves), the tree and its root, the
                      inclusion proof for ballot 0515 0293, and the arithmetic behind the figures
                      (proof sizes, finality, capacity, the Phase I gate, index repeats,
                      Objection 7, throughput, salts, and the one hypothetical example).
  verify_figures.py   Recomputes all of it using only the Python 3 standard library
                      (hashlib, json, math). Nothing is installed and nothing is downloaded.
  verify_chain_settings.py
                      Recomputes the Cardano numbers the paper states "as of September 2026"
                      (Sections 4.2 and 12.1): the ada deposit one Vote Coin output needs, from
                      CIP-55's formula, for 18 ways the output could be encoded (1.0085 to 1.4482
                      ada, "about 1 to 1.5 ada"), the chain's capacity (90,112 bytes about
                      every 20 seconds, about 4.5 kilobytes a second), and the chain load of
                      per-voter burns at each phase (the table in Section 12.2: about 29 days
                      of the whole chain at 2024 in-person volume). Standard library only.
                      The protocol parameters were read from Cardano mainnet on September 27,
                      2026 (epoch 658); governance can change them, so put the current values
                      in PARAMS at the top of the file before relying on the result.

How to run
  python3 verify_figures.py

  python3 verify_chain_settings.py

  Each line prints PASS or FAIL. The last lines should read:
      71 passed, 0 failed          (verify_figures.py)
      13 passed, 0 failed          (verify_chain_settings.py)

What it checks
  0     SHA-256 against NIST's published example value, and the tree code against the
        eight published RFC 9162 reference roots (trees of 1 to 8 leaves)
  1     Each ballot's record, salt, fingerprint and leaf; the two orders (the archive box
        by index, the tree by fingerprint)
  2     The tree, level by level, and again by the recursive RFC 9162 definition
  3     Ballot 0515 0293 step by step, and the what-if tablet that records a different choice
  4     The three-step inclusion proof, ending at the anchored root
  5-12  The arithmetic behind Figures 7, 16, 17, 18, 21, 23 and 26

The ballots are samples, not votes. Their salts are published only because they are
samples: a real salt never leaves a Secure Node's sealed audit log.

"Figures: Worked Examples" explains every value, its source, and where it appears.
