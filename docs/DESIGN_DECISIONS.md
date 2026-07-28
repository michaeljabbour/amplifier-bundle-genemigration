# Gene-Migration Design Decisions

Why the bundle and graphs are shaped this way. Shares an engine lineage with
`amplifier-bundle-genetransfer` (HGT); the deltas below are what migration adds.

## 0. GM vs HGT — different jobs
HGT (genetransfer) **cherry-picks capabilities** from a donor and re-expresses each
into existing host(s) — inventory is a triage table, loop is per capability, "never
read the donor deeply." GM **migrates a whole app** A→B — inventory is a reverse-
engineered, dependency-sequenced story backlog, loop is per story, and you DO read
the source deeply (fidelity is the goal) but re-implement idiomatically. One source,
one target. Same loop-pipeline engine and the same footgun fixes below.

## 1. Two graphs, one ledger tool
`inventory.dot` (Phase 1) emits the sequenced backlog; `migrate.dot` (Phase 2)
consumes it. Both use the single stdlib `ledger.py` over different TSVs
(`surfaces.tsv`, `backlog.tsv`) via `LEDGER_FILE`. Sequencing needs a global view, so
`inventory.dot` mines surfaces in a loop then runs ONE `SequenceBacklog` finalizer
that orders every story — you cannot sequence incrementally.

## 2. Sequence encoded as file order (not a priority column)
`SequenceBacklog` appends backlog rows in dependency order; `ledger.py earliest`
returns the first `new` row in file order. So "next story to migrate" = "next in the
plan" with zero extra machinery. Dependencies migrate before dependents because they
were written first.

## 3. LEDGER_TOOL is a param (decoupled from both repos)
The tool nodes call `python3 "$LEDGER_TOOL"` — an absolute path to THIS bundle's
`pipelines/ledger.py` — not `pipelines/ledger.py` relative to a repo. The source and
target repos need not contain the tool. (HGT instance #1 assumed the tool lived in
the host repo; GM fixes that coupling.)

## 4. Params via ENV VARS / run_pipeline, never mounted config.params
Same engine limitation HGT documented: a mounted orchestrator substitutes params into
prompts only, not `tool_command`. Both graphs read UPPERCASE env vars with `${VAR:?}`
fail-loud guards at the loop head — correct under run_pipeline (flat context keys) and
env-export. `bundles/gm-interactive.yaml` (run_pipeline) is the recommended path;
`bundles/gm-pipeline.yaml` requires exported env vars and CWD == repo root (the
engine resolves `dot_file` against the process CWD via a bare `open()`).

## 5. `... && printf pass || printf fail` is load-bearing
Routing is EXACT-string match on the last stdout line; a non-zero exit leaves
`tool.last_line` STALE and condition edges still fire. Every gate forces exit 0 with
an explicit `|| printf fail`. Diagnostics go to `/tmp` files.

## 6. Acceptance criteria are a LIVING artifact
`AnalyzeFailure` may conclude the failure is an inventory defect (a wrong/untestable
criterion), not a code defect — in which case the fix amends the story card in
`inventory/stories/`, not just the target code. Reverse-engineered specs are
hypotheses until the terminal proves them; the loop is allowed to correct them
(but never to force-green).

## 7. inventory/ lives in the TARGET repo (the instance), not the bundle
The backlog, surfaces, and story cards are per-migration artifacts and the living
migration plan — they belong in the target repo (like a PARITY.md/MIGRATION.md),
committed alongside the rewrite. The bundle ships the machinery, not any instance's
inventory.

## 8. Agents declare inline non-pipeline orchestrators
`gm-inventory` and `gm-orchestrator` each declare `loop-streaming` inline so that if
either is ever spawned as a pipeline node it does not inherit loop-pipeline and
recurse (foundation guidance).

## 9. Two retry budgets, orthogonal
`.ai/gm_retries` bounds the fix loop at 3 (a gate printing `fail` at exit 0 is a
SUCCESS outcome, not engine-retried); the engine's `default_max_retry=3` covers
transient in-node exceptions on box nodes. Different failures; both kept.

## 10. Session durability requires the logging hook (DTU reality-check finding)
Same finding as genetransfer §9: without `hooks-logging` the session directory is
never created, the CLI finalizer raises `Session '<id>' not found`, and nothing
persists (no resume/events). For an attractor bundle whose runbook promises
resumable multi-hour runs this is disqualifying — `hooks-logging` is part of
gm-core, config mirroring foundation `behaviors/logging.yaml`.
