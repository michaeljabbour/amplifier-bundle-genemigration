#!/usr/bin/env python3
"""Fitness function for the Gene-Migration attractor — the scalar the run hill-climbs.

WHAT IS BEING MEASURED: the migration's whole job is to drive every backlog story to
a GREEN-GATED PR (state=implemented), IN DEPENDENCY ORDER. A story reaches
`implemented` only after its acceptance-criteria tests + the forge check pass (the
Commit node marks it), so `implemented_frac` bakes in the gates as a precondition.
`acknowledged` (gave-up / human handoff) drains the queue but earns nothing — "do
less" cannot score.

GM adds a SEQUENCE dimension: backlog file order is the dependency linearization,
so we also measure `lookahead` — how far past the earliest still-`new` story any
implemented story sits. Small lookahead (≤ the parallel-lane cap) is healthy
parallelism; large lookahead means the run is ignoring the plan.

Backlog row: <story-id>\t<title-slug>\t<state>  state in {new, implemented, acknowledged}

Usage:
    python3 evals/fitness.py <backlog.tsv>
"""
from __future__ import annotations

import sys
from pathlib import Path


def read_rows(path: str) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 3:
            rows.append((parts[0], parts[1], parts[2]))
    return rows


def fitness(rows: list[tuple[str, str, str]]) -> dict:
    total = len(rows)
    denom = total or 1
    impl = sum(1 for r in rows if r[2] == "implemented")
    ack = sum(1 for r in rows if r[2] == "acknowledged")
    new = sum(1 for r in rows if r[2] == "new")
    # sequence lookahead: distance between the earliest unresolved story and the
    # furthest implemented one. 0 = strictly in order; small = healthy parallel
    # lanes; large = the run is ignoring the dependency sequence.
    first_new = next((i for i, r in enumerate(rows) if r[2] == "new"), None)
    last_impl = next((i for i in range(total - 1, -1, -1) if rows[i][2] == "implemented"), None)
    lookahead = 0
    if first_new is not None and last_impl is not None and last_impl > first_new:
        lookahead = last_impl - first_new
    return {
        "total": total,
        "implemented": impl,
        "acknowledged": ack,
        "new": new,
        "implemented_frac": round(impl / denom, 4),  # PROTECTED — climb this
        "resolved_frac": round((impl + ack) / denom, 4),  # queue drained
        "lookahead": lookahead,  # WATCH — sequence adherence (small is healthy)
        "score": round(impl / denom, 4),  # headline fitness
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: fitness.py <backlog.tsv>", file=sys.stderr)
        return 2
    for k, v in fitness(read_rows(argv[1])).items():
        print(f"{k}\t{v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
