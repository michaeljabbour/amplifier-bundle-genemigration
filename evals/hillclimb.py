#!/usr/bin/env python3
"""Hill-climbing eval for the Gene-Migration attractor.

Reads an ORDERED series of backlog snapshots (successive states of one migration
run), prints the fitness curve, and asserts the RATCHET:

  1. implemented_frac is non-decreasing across consecutive snapshots,
  2. no story un-completes (implemented -> new/acknowledged), and
  3. sequence lookahead never exceeds --max-lookahead (default 8 ≈ the parallel
     lane cap): stories may finish slightly out of file order under healthy
     parallelism, but a run that leapfrogs the dependency sequence fails.

Any violation is a Goodhart / regression tripwire and fails the eval (exit 1).

Usage:
    python3 evals/hillclimb.py <snap0.tsv> <snap1.tsv> ...   # explicit series
    python3 evals/hillclimb.py --fixture                     # bundled demo climb
    python3 evals/hillclimb.py --self-test                   # climb + regression cases
    python3 evals/hillclimb.py --max-lookahead N <snaps...>
"""
from __future__ import annotations

import sys
from pathlib import Path

from fitness import fitness, read_rows

HERE = Path(__file__).parent
FIXTURE = sorted((HERE / "fixtures" / "run").glob("*.tsv"))
DEFAULT_MAX_LOOKAHEAD = 8


def _bar(frac: float, width: int = 24) -> str:
    n = round(frac * width)
    return "█" * n + "·" * (width - n)


def check(
    series: list[list[tuple[str, str, str]]], max_lookahead: int = DEFAULT_MAX_LOOKAHEAD
) -> tuple[bool, list[str]]:
    """Return (climbing?, notes). Climbing = no ratchet/sequence violation."""
    notes: list[str] = []
    ok = True
    prev_f = None
    prev_state: dict[str, str] = {}
    for i, rows in enumerate(series):
        f = fitness(rows)
        notes.append(
            f"  step {i}: {_bar(f['implemented_frac'])} "
            f"impl={f['implemented']}/{f['total']} frac={f['implemented_frac']:.2f} "
            f"resolved={f['resolved_frac']:.2f} lookahead={f['lookahead']}"
        )
        if prev_f is not None and f["implemented_frac"] < prev_f["implemented_frac"] - 1e-9:
            ok = False
            notes.append(
                f"    ✗ REGRESSION: implemented_frac fell "
                f"{prev_f['implemented_frac']:.2f} -> {f['implemented_frac']:.2f}"
            )
        if f["lookahead"] > max_lookahead:
            ok = False
            notes.append(
                f"    ✗ SEQUENCE: lookahead {f['lookahead']} > {max_lookahead} — "
                f"the run is ignoring the dependency order"
            )
        state = {r[0]: r[2] for r in rows}
        for sid, st in prev_state.items():
            if st == "implemented" and state.get(sid) in ("new", "acknowledged"):
                ok = False
                notes.append(f"    ✗ REGRESSION: '{sid}' un-completed ({st} -> {state.get(sid)})")
        prev_f, prev_state = f, state
    return ok, notes


def _self_test() -> int:
    good = [
        [("s1", "core", "new"), ("s2", "loop", "new"), ("s3", "composer", "new")],
        [("s1", "core", "implemented"), ("s2", "loop", "new"), ("s3", "composer", "new")],
        [("s1", "core", "implemented"), ("s2", "loop", "implemented"), ("s3", "composer", "new")],
    ]
    bad_uncomplete = [
        [("s1", "core", "implemented"), ("s2", "loop", "implemented")],
        [("s1", "core", "new"), ("s2", "loop", "implemented")],
    ]
    # story 11 implemented while story 1 is still new -> lookahead 10 > 8
    bad_sequence = [
        [(f"s{i}", f"t{i}", "new") for i in range(1, 12)],
        [(f"s{i}", f"t{i}", "new") for i in range(1, 11)] + [("s11", "t11", "implemented")],
    ]
    ok_good, _ = check(good)
    ok_bad1, _ = check(bad_uncomplete)
    ok_bad2, _ = check(bad_sequence)
    passed = ok_good and not ok_bad1 and not ok_bad2
    print("self-test: climbing series detected as CLIMBING:", ok_good)
    print("self-test: un-complete detected as REGRESSION:", not ok_bad1)
    print("self-test: sequence leapfrog detected as violation:", not ok_bad2)
    print("SELF-TEST", "PASS" if passed else "FAIL")
    return 0 if passed else 1


def main(argv: list[str]) -> int:
    max_lookahead = DEFAULT_MAX_LOOKAHEAD
    if argv[:1] == ["--max-lookahead"] and len(argv) >= 2:
        max_lookahead = int(argv[1])
        argv = argv[2:]
    if argv == ["--self-test"]:
        return _self_test()
    if argv == ["--fixture"] or not argv:
        if not FIXTURE:
            print("no fixtures found", file=sys.stderr)
            return 2
        paths = [str(p) for p in FIXTURE]
    else:
        paths = argv
    print(f"GM hill-climb over {len(paths)} snapshot(s), max_lookahead={max_lookahead}:")
    ok, notes = check([read_rows(p) for p in paths], max_lookahead)
    print("\n".join(notes))
    print("VERDICT:", "CLIMBING ✓" if ok else "REGRESSION ✗")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
