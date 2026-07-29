# Evaluating GM — three loops, honestly scoped

Grounded in reviewer feedback (from the author of the reality-check / DTU /
evaluation bundles) that identified two real gaps, both conceded:

1. **The pipeline authors the acceptance artifacts it is graded against.**
   `PlanPort` writes the forge probe, `Implement` writes the unit tests — the
   same flow that must pass them — and `AnalyzeFailure` may amend story cards
   (`pipelines/migrate.dot`, the "living inventory"), i.e. the gradee can edit
   the rubric. The gate *execution* is deterministic and per-node contexts are
   fresh (`truncate` fidelity), but deterministic ≠ independent: the gate's
   *definition* comes from inside the loop.
2. **`evals/hillclimb.py` is near-tautological as a technique signal.** Ledger
   rows only ever move forward, so "up and to the right" within one run is
   close to guaranteed by construction. It cannot say GM-v2 beats GM-v1.

This doc scopes what exists and designs what closes the gaps.

## Loop 0 — what exists: the run monitor (inner)

`evals/fitness.py` + `hillclimb.py`: a ratchet over backlog snapshots. Honest
scope: detects a stalled, regressing, or sequence-violating **run** (and a
technique that gives up scores 0 via `acknowledged`), with quality baked in
only to the extent the in-loop gates are trustworthy. Keep it for what it is —
run health + Goodhart tripwires — not an objective function.

## Loop 1 — outer verification: grader independence (reality-check, adapted)

[amplifier-bundle-reality-check](https://github.com/microsoft/amplifier-bundle-reality-check)'s
shape: an `intent-analyzer` derives structured acceptance tests from the user's
intent (not from the builder); validators (terminal/browser/generic testers)
execute them against the software deployed in a DTU; a gap report follows.
The grader's criteria never come from the build loop.

Our adaptation exploits GM's 1:1 advantage — the ground truth is an
**executable app**, not a conversation:

- A **blind verifier** session derives its own acceptance from the SOURCE app
  (boots it via forge, observes real behavior) — it never reads `.ai/`, the
  story cards, or the builder's tests/probe — then validates the TARGET in a
  DTU and emits `verified | rejected(findings)` per story.
- `rejected` reopens the row (`implemented → new`, findings attached), bounded
  once, then `acknowledged` with the verifier's findings for a human.
- The ledger gains a terminal state **`verified`**; the eval's protected scalar
  becomes `verified_frac` (`implemented_frac` becomes intermediate).
- The living inventory keeps its value but loses its Goodhart hole: the fix
  loop may **propose** a story-card amendment; only the verifier may accept it.

Shape: a fourth graph `pipelines/verify.dot` (CheckImplemented →
DeriveChecks(blind) → ValidateTarget → Verdict → loop), or a Verify stage
between Commit and the ledger update. Deliberately not yet built — roadmap §.

## Loop 2 — the technique objective function: frozen answer key (outermost)

To hillclimb the **technique**, the number must come from outside the loop:

- **Scenario:** a real port that already happened. Freeze the repo at the
  commit *before* the port. Run GM on that state — the flow never sees the
  real port.
- **Grade:** run the real port's *behavioral* test suite against what GM
  produced, plus parity probes. Score = % answer-key checks passed (+ surface
  coverage as secondary).
- **Climb:** GM-v1 vs GM-v2 on the identical frozen scenario, K≥3 repeats per
  variant — our own two inventory runs of the same toy produced 3-story and
  6-story backlogs, so single-run numbers are noise. Then "moving the probe
  earlier bought 15 points" is a sentence with meaning.

**Worked candidate (verified from git history):** `openai/codex` TypeScript/Ink
→ Rust. At tag `rust-v0.0.2504301219` both `codex-cli/` (TypeScript — `ink`,
`react`, `ink-testing-library` in its package.json) and `codex-rs/` coexist in
the tree; today's `codex-rs` carries `cli/tests/` suites and e2e benches
(black-box candidates). Pilot on a **scoped slice** (e.g. `exec` +
`apply-patch`), not the whole app.

Threats, named up front:
- **Contamination.** codex is in every frontier model's training data; the
  model may recall the real Rust port. Mitigations: grade only on behavioral
  tests; treat v1-vs-v2 *deltas* on the same task as the primary number
  (recall inflates both arms); prefer obscure or private answer keys for
  trustworthy absolutes.
- **Test coupling.** Most cargo unit tests are structure-coupled and will not
  run against an independently-shaped port. Use the CLI/integration subset;
  where thin, derive black-box checks *from* the answer key's tests rather
  than running them verbatim.

## Roadmap

1. ✅ DELIVERED — `verify.dot` + blind-verifier agent; DTU-validated (2 positive,
   1 sabotage correctly rejected, blindness audit clean).
2. ✅ PILOT DELIVERED — `benchmarks/codex-apply-patch/`: grader calibrated 21/21
   vs the real codex-rs; GM-v1 scored externally (headline 13/16; see
   `benchmarks/codex-apply-patch/RESULTS.md` incl. the design defects to fix
   before any v1-vs-v2 comparison).
3. NEXT (not started): fix the pilot's Loop-2 defects, then v1-vs-v2 with K≥3 —
   only then tune the technique, with Loop 2 as arbiter.
