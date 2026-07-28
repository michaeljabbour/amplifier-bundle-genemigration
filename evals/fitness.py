#!/usr/bin/env python3
"""Fitness function for the Gene-Migration attractor — run-monitor scalars.

WHAT IS BEING MEASURED: the migration drives every backlog story to a green-gated PR
(`implemented`) IN DEPENDENCY ORDER, and Loop 1 (the blind verifier,
pipelines/verify.dot) then drives it to `verified` — independently confirmed against
the SOURCE app's real behavior. `implemented` bakes in the builder's own gates;
`verified` bakes in an INDEPENDENT rubric. `acknowledged` earns nothing.

Backlog row: <story-id>\t<title-slug>\t<state>  state in {new, implemented, verified, acknowledged}

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
    ver = sum(1 for r in rows if r[2] == "verified")
    ack = sum(1 for r in rows if r[2] == "acknowledged")
    new = sum(1 for r in rows if r[2] == "new")
    # sequence lookahead: an "unfinished" row is new OR reopened; landed = implemented|verified.
    landed_states = ("implemented", "verified")
    first_unfinished = next((i for i, r in enumerate(rows) if r[2] == "new"), None)
    last_landed = next((i for i in range(total - 1, -1, -1) if rows[i][2] in landed_states), None)
    lookahead = 0
    if first_unfinished is not None and last_landed is not None and last_landed > first_unfinished:
        lookahead = last_landed - first_unfinished
    return {
        "total": total,
        "implemented": impl,
        "verified": ver,
        "acknowledged": ack,
        "new": new,
        "implemented_frac": round(impl / denom, 4),
        "verified_frac": round(ver / denom, 4),  # Loop-1 PROTECTED scalar
        "landed_frac": round((impl + ver) / denom, 4),  # legacy PROTECTED scalar
        "resolved_frac": round((impl + ver + ack) / denom, 4),
        "lookahead": lookahead,  # WATCH — sequence adherence (small is healthy)
        "score": round((impl + ver) / denom, 4),
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
