# GM evals — simple hill-climbing eval

**What is measured (the criterion, before any code):** the migration's one job is to
drive every backlog story to a green-gated PR, **in dependency order**. So the
fitness the run hill-climbs is `implemented_frac` — the fraction of backlog stories
in state `implemented`. That state is only ever set by the Commit node *after* the
story's acceptance-criteria tests + the real-terminal forge check pass, so the score
bakes in quality as a precondition: the harness cannot score by lowering the bar,
and `acknowledged` (gave up / human handoff) earns nothing — "do less" cannot score.

**The hill-climb property (the ratchet):** a healthy migration only climbs, and it
respects the plan. Three invariants:
1. `implemented_frac` is non-decreasing across successive backlog snapshots;
2. no story un-completes (`implemented` → `new`/`acknowledged`);
3. **sequence lookahead** stays small: backlog file order is the dependency
   linearization, so finishing a few stories out of order is healthy parallelism
   (≤ the lane cap, default 8), but leapfrogging far past the earliest unfinished
   story means the run is ignoring the migration plan — and fails.

Any violation is a regression / Goodhart tripwire and fails the eval.

## Loop 1 (verifier) mode

With `pipelines/verify.dot` in play the ledger gains the terminal state
`verified`, and the blind verifier may legally REOPEN an implemented row. Monitor
those runs with `--verifier`: the protected scalar becomes `verified_frac`, no row
may ever leave `verified`, and reopens are reported (↺) rather than failed.

## Run it

```sh
python3 evals/hillclimb.py --self-test   # detectors for BOTH modes     # the eval proves it detects regressions
python3 evals/hillclimb.py --fixture       # demo curve over a bundled 4-snapshot run
python3 evals/fitness.py <backlog.tsv>     # score one backlog state
python3 evals/hillclimb.py s0.tsv s1.tsv…  # evaluate a REAL run's snapshot series
python3 evals/hillclimb.py --max-lookahead 4 s0.tsv s1.tsv…   # stricter sequencing
```

## Evaluating a real run

Snapshot the backlog as the migration progresses (e.g. `cp $BACKLOG snaps/$(date +%s).tsv`
after each loop, or materialize versions from the backlog file's git history), then
feed the ordered snapshots to `hillclimb.py`. Exit 0 = climbed monotonically in
order; exit 1 = a regression or a sequence violation, with the offending step named.

## Honest limits

**Scope (sharpened after external review):** this is the INNER run monitor.
Because ledger rows only ever move forward, within-run monotonicity is close to
tautological — this eval detects broken runs, it cannot rank technique variants.
The technique-level objective function (frozen answer key, external grading,
v1-vs-v2 on identical tasks) is designed in `docs/EVALUATION.md`.

This eval scores the ATTRACTOR's convergence behavior — progress, monotonicity, and
sequence adherence. It does **not** re-judge an individual story's migration quality
beyond what its gates enforced (acceptance tests + forge are that judgment), and it
cannot detect a wrong-but-passing acceptance criterion (that is the inventory's
living-spec loop). One high-signal criterion beats ten noisy ones.
