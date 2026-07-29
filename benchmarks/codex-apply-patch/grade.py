#!/usr/bin/env python3
"""Deterministic grader for the codex apply-patch black-box benchmark.

Contract exercised (see cases/HARVEST_NOTES.md for the full derivation):
  - the candidate binary reads the entire patch text from STDIN (the codex
    "*** Begin Patch ... *** End Patch" envelope format)
  - it applies file changes relative to its current working directory
  - it exits 0 iff the patch fully applied, non-zero otherwise
  - stdout/stderr content is NOT graded (formats differ across implementations)

Each case in cases.json describes:
  - name:               unique case identifier
  - files_before:        {relpath: content} to seed a fresh tmpdir with
  - patch:               the patch text piped to the candidate binary on stdin
  - expect_exit_zero:    bool, whether the binary is expected to exit 0
  - files_after:         {relpath: content-or-null} delta from files_before;
                         null means "must not exist after". Keys absent from
                         files_after are expected to be unchanged from
                         files_before.
  - skip_tree_check:     optional bool (default false). When true, only the
                         exit-code expectation is graded -- the resulting file
                         tree is not asserted. Reserved for cases where the
                         real implementation's post-failure mutation state is
                         not fully deterministic/assertable (see
                         cases/HARVEST_NOTES.md; none of the current cases
                         require it, but the grader honors it if present).

Usage:
    python3 grade.py --bin <candidate-binary> [--cases cases/cases.json] [--json <out>]

Stdlib only. No third-party dependencies.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_TIMEOUT_SECONDS = 30


def default_cases_path() -> Path:
    """cases/cases.json next to this script, so `python3 grade.py --bin X`
    works regardless of the caller's current working directory."""
    return Path(__file__).resolve().parent / "cases" / "cases.json"


def load_cases(cases_path: Path) -> list[dict]:
    with open(cases_path, encoding="utf-8") as f:
        cases = json.load(f)
    if not isinstance(cases, list):
        raise ValueError(f"{cases_path}: expected a JSON list of cases")
    return cases


def write_files_before(root: Path, files_before: dict[str, str]) -> None:
    for relpath, content in files_before.items():
        dest = root / relpath
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "w", encoding="utf-8", newline="") as f:
            f.write(content)


def snapshot_tree(root: Path) -> dict[str, str] | dict[str, str | None]:
    """Walk root and return {relpath (posix-style): content}. Binary/unreadable
    files are recorded with a sentinel marker rather than raising, so a
    mismatch is reported instead of crashing the grader."""
    tree: dict[str, str] = {}
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            full = Path(dirpath) / name
            rel = full.relative_to(root).as_posix()
            try:
                with open(full, encoding="utf-8", newline="") as f:
                    tree[rel] = f.read()
            except (UnicodeDecodeError, OSError) as e:
                tree[rel] = f"<<unreadable: {e}>>"
    return tree


def expected_tree(files_before: dict[str, str], files_after: dict[str, str | None]) -> dict[str, str]:
    expected = dict(files_before)
    for relpath, content in files_after.items():
        if content is None:
            expected.pop(relpath, None)
        else:
            expected[relpath] = content
    return expected


def run_case(binary: str, case: dict) -> dict:
    """Run a single case in a fresh tmpdir. Returns a result dict (never
    raises for expected failure modes -- timeouts and missing binaries are
    captured as a failing result, not an unhandled exception)."""
    name = case["name"]
    files_before = case.get("files_before", {})
    files_after = case.get("files_after", {})
    patch = case["patch"]
    expect_exit_zero = bool(case["expect_exit_zero"])
    skip_tree_check = bool(case.get("skip_tree_check", False))

    with tempfile.TemporaryDirectory(prefix="apply-patch-grade-") as tmpdir:
        root = Path(tmpdir)
        write_files_before(root, files_before)

        reasons: list[str] = []
        exit_code = None
        timed_out = False
        launch_error = None

        try:
            proc = subprocess.run(
                [binary],
                input=patch.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(root),
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )
            exit_code = proc.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
        except OSError as e:
            launch_error = str(e)

        if launch_error is not None:
            reasons.append(f"failed to launch binary: {launch_error}")
            return {
                "name": name,
                "passed": False,
                "reasons": reasons,
                "exit_code": None,
                "expect_exit_zero": expect_exit_zero,
            }

        if timed_out:
            reasons.append(f"timed out after {DEFAULT_TIMEOUT_SECONDS}s")
            return {
                "name": name,
                "passed": False,
                "reasons": reasons,
                "exit_code": None,
                "expect_exit_zero": expect_exit_zero,
            }

        actual_exit_zero = exit_code == 0
        exit_ok = actual_exit_zero == expect_exit_zero
        if not exit_ok:
            reasons.append(
                f"exit code mismatch: expected exit_zero={expect_exit_zero}, "
                f"got exit_code={exit_code} (exit_zero={actual_exit_zero})"
            )

        tree_ok = True
        actual_tree: dict[str, str] | None = None
        expected: dict[str, str] | None = None
        if not skip_tree_check:
            actual_tree = snapshot_tree(root)
            expected = expected_tree(files_before, files_after)
            if actual_tree != expected:
                tree_ok = False
                missing = {k: v for k, v in expected.items() if k not in actual_tree}
                extra = {k: v for k, v in actual_tree.items() if k not in expected}
                changed = {
                    k: (expected[k], actual_tree[k])
                    for k in expected
                    if k in actual_tree and expected[k] != actual_tree[k]
                }
                if missing:
                    reasons.append(f"missing expected files/content: {missing!r}")
                if extra:
                    reasons.append(f"unexpected extra files: {extra!r}")
                if changed:
                    reasons.append(f"content mismatch: {changed!r}")

        passed = exit_ok and (skip_tree_check or tree_ok)
        return {
            "name": name,
            "passed": passed,
            "reasons": reasons,
            "exit_code": exit_code,
            "expect_exit_zero": expect_exit_zero,
            "skip_tree_check": skip_tree_check,
        }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--bin", required=True, help="Path to the candidate binary")
    parser.add_argument("--cases", default=None, help="Path to cases.json (default: cases/cases.json next to grade.py)")
    parser.add_argument("--json", default=None, help="Optional path to write machine-readable JSON results")
    args = parser.parse_args(argv)

    cases_path = Path(args.cases) if args.cases else default_cases_path()
    if not cases_path.is_file():
        print(f"ERROR: cases file not found: {cases_path}", file=sys.stderr)
        return 2

    binary = str(Path(args.bin).expanduser().resolve())
    if not Path(binary).is_file():
        print(f"ERROR: candidate binary not found: {binary}", file=sys.stderr)
        return 2

    cases = load_cases(cases_path)
    if not cases:
        print("ERROR: no cases loaded", file=sys.stderr)
        return 2

    results = []
    passed_count = 0
    for case in cases:
        result = run_case(binary, case)
        results.append(result)
        if result["passed"]:
            passed_count += 1
            print(f"PASS  {result['name']}")
        else:
            print(f"FAIL  {result['name']}")
            for reason in result["reasons"]:
                print(f"        - {reason}")

    total = len(cases)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "binary": binary,
                    "cases_file": str(cases_path),
                    "total": total,
                    "passed": passed_count,
                    "results": results,
                },
                f,
                indent=2,
            )
            f.write("\n")

    print(f"SCORE: {passed_count}/{total}")
    return 0 if passed_count == total else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
