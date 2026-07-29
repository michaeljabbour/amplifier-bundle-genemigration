# Pilot results — GM-v1, 2026-07-28

First end-to-end run of the frozen answer-key benchmark (Loop 2 validation).
One variant, K=1 — a LOOP validation, not yet a technique comparison.

## Run

- DTU `gene-bundles`; bundles at genetransfer `49889d5` / genemigration `194eba7`.
- Scenario materialized from `upstream/ts/` only; leak audit of the staged tree,
  instruction files, and ALL session logs: **zero** references to `upstream/rs`,
  `cases`, `grade.py`, `calibration` (the answer key sat unused in the DTU's
  bundle cache — see Caveats).
- Inventory: **17 stories** (session `6c7b2816…`), foundations-first.
- Migrate: **10/10 iterations, 10 implemented, 0 acknowledged, 0 retries**, then
  the iteration cap stopped the loop with 7 stories still `new` (~30 min short
  of quiescence). All 11 root sessions durable; `Session not found` count 0.
- Port: Rust crate, 8 modules, 118 tests passing, binary honors the contract.
  Wall time 63m36s (migrate loop 47m51s ≈ 260 s/story).

## Score (external, answer-key-derived, grader calibrated 21/21)

| Bucket | Score | Meaning |
|---|---|---|
| success-path | **9/11** | core add/delete/update/move/fuzzy behavior |
| parse-invalid | **4/5** | malformed envelopes must exit ≠ 0 |
| **HEADLINE** | **13/16 (81%)** | behavior both implementations agree on |
| quirk fidelity | **0/5** | resembles the answer key's edge semantics? |
| total | 13/21 | |

## What the failures actually say (the point of an external key)

- `add_file_creates_content`: port writes `ab\ncd`, answer key `ab\ncd\n` —
  trailing-newline semantics on Add File. Real divergence, invisible to the
  flow's own gates.
- `update_insert_at_eof`: port produced `…baz\n\nquux` (blank line, no trailing
  newline) vs key's `…baz\nquux\n`. Real divergence in EOF insertion.
- `invalid_empty_update_hunk`: port exits 0 where the key's parser rejects.
- All 5 `quirk_*` failures are the port exiting **1** on runtime failures where
  the real codex-rs silently exits **0**. Checked against the SOURCE: the TS
  original **throws `DiffError`** on exactly these cases (missing file, context
  mismatch) — so the port is **faithful to its source** and diverges precisely
  where the human Rust port itself diverged from the TS original. 0/5 here
  reads "resembles the source, not the rewrite" — for a migration tool, that is
  the defensible side of the fork. This is why the breakdown, not the total, is
  the report.

## Loop-2 design defects found by the pilot (fix before v1-vs-v2)

1. **Ledger under-reports.** The migrate instruction's scaffold rule forced
   iteration 1 to build the binary + pipeline skeleton, while the inventory had
   sequenced CLI stories last — the flow built ahead of its plan, so "7 stories
   `new`" ≠ "41% missing" (probe: update/delete/CLI all work). Fix: inventory
   must sequence the scaffold story first, or the scaffold rule must create a
   stub-only crate.
2. **Iteration cap vs story count.** 17 stories, cap 10. Budget quiescence
   (cap ≥ stories + retries) or grade-at-cap explicitly.
3. **Answer-key reachability.** The gm bundle's DTU cache contains this
   benchmark dir (incl. `upstream/rs/`). Audit found zero touches, but a
   benchmark-stripped bundle mirror would make it airtight.
4. **No Loop 1 in the pilot.** Rows are `implemented`, none `verified` — a full
   protocol run should insert the blind verifier between migrate and grading.

## Sessions

inventory `6c7b2816` · migrate `89ef418a` `de53475d` `e03ed44b` `610fa018`
`e9269169` `d5f51c07` `b219aebb` `8af53204` `7908bedf` `def67a17` · port at
`bench-apply-patch-target` branch `gm/port` HEAD `66b7496`.
