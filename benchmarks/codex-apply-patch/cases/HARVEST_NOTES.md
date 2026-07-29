# Harvest Notes -- codex apply-patch behavioral cases

Source of truth for every case in `cases.json`: `upstream/rs/lib.rs` (14
`#[cfg(test)]` tests in `mod tests`), `upstream/rs/parser.rs` (3 free-standing
`#[test]` fns), and `upstream/rs/seek_sequence.rs` (4 `#[test]` fns, all
pure-function tests with no filesystem interaction -- not CLI-observable, see
"Not harvested" below).

All 21 cases were calibrated against the real answer key
(`calibration/crates/codex-apply-patch`, a verbatim copy of `upstream/rs`)
via `calibration/shim`, which invokes `codex_apply_patch::apply_patch(patch,
stdout, stderr)` directly (see `calibration/shim/src/main.rs`). Every value
in `cases.json` (`files_after` content, `expect_exit_zero`) was captured
byte-for-byte from an actual run of that binary, not transcribed by hand from
reading the Rust assertions -- transcription was cross-checked against the
literal `assert_eq!` values in the source afterward and matched exactly.
**Final calibration run: `SCORE: 21/21`.**

## Test -> case mapping table

| Upstream test | Case(s) | Notes |
|---|---|---|
| `lib.rs::test_literal` | -- | Exercises `maybe_parse_apply_patch(argv)`, an argv-shape API, not the `apply_patch` stdin/CLI surface. No CLI-observable behavior to harvest. Not ported. |
| `lib.rs::test_heredoc` | -- | Same as above (bash heredoc argv-extraction path). Not CLI-observable. Not ported. |
| `lib.rs::test_add_file_hunk_creates_file_with_contents` | `add_file_creates_content` | Direct port. |
| `lib.rs::test_delete_file_hunk_removes_file` | `delete_file_removes_it` | Direct port. |
| `lib.rs::test_update_file_hunk_modifies_content` | `update_single_chunk_modifies_content` | Direct port. |
| `lib.rs::test_update_file_hunk_can_move_file` | `update_file_can_move` | Direct port (move/rename). |
| `lib.rs::test_multiple_update_chunks_apply_to_single_file` | `update_multiple_chunks_single_file` | Direct port. |
| `lib.rs::test_update_file_hunk_interleaved_changes` | `update_interleaved_changes_with_eof_append` | Direct port (3 chunks: replace, context-anchored replace, EOF append). |
| `lib.rs::test_update_line_with_unicode_dash` | `update_unicode_dash_fuzzy_match` | Direct port -- exercises `seek_sequence`'s Unicode-punctuation normalisation fallback pass. |
| `lib.rs::test_unified_diff` | -- (see below) | Calls `parse_patch` + `unified_diff_from_chunks` directly; never calls `apply_patch` and never writes to disk. Its fixture (file `multi.txt`, same 2-chunk patch) and expected resulting content are **identical** to `test_multiple_update_chunks_apply_to_single_file`, which *does* exercise `apply_patch`. Dropped as a duplicate CLI-observable scenario -- porting it would just be `update_multiple_chunks_single_file` again under a different name. |
| `lib.rs::test_unified_diff_first_line_replacement` | `update_first_line_replacement` | This test also only calls `unified_diff_from_chunks` (no disk write), but its patch/content combination is *not* covered by any other test (first-line replacement is a distinct edge in `compute_replacements`'s insertion-index logic). Ported as a fresh CLI scenario: same file/patch, but graded through `apply_patch` end-to-end instead of the diff-string API. |
| `lib.rs::test_unified_diff_last_line_replacement` | `update_last_line_replacement` | Same rationale as above (distinct edge: last-line replacement). |
| `lib.rs::test_unified_diff_insert_at_eof` | `update_insert_at_eof` | Same rationale -- this is the required "insert-at-EOF" case. |
| `lib.rs::test_unified_diff_interleaved_changes` | `update_interleaved_variant_narrow_context` | This one *does* call `apply_patch` at the end and assert on-disk content, so it is a genuine second interleaved-changes CLO case. Kept distinct from `update_interleaved_changes_with_eof_append` because its second chunk uses a single-line context (`d`) instead of two (`c`/`d`), independently exercising `seek_sequence`'s narrower-context path even though the final content happens to match. |
| `parser.rs::test_parse_patch` (`"bad"` assertion) | `invalid_missing_begin_patch_marker` | Parse-time `InvalidPatchError`, real non-zero exit. |
| `parser.rs::test_parse_patch` (`"*** Begin Patch\nbad"` assertion) | `invalid_missing_end_patch_marker` | Parse-time `InvalidPatchError`, real non-zero exit. |
| `parser.rs::test_parse_patch` (`"Update file hunk for path 'test.py' is empty"` assertion) | `invalid_empty_update_hunk` | Parse-time `InvalidHunkError`, real non-zero exit; adapted to a distinct filename/path only. |
| `parser.rs::test_parse_patch` (remaining assertions: happy-path multi-hunk parse, update-then-add-hunk parse, missing-`@@`-header parse) | -- | Pure `parse_patch(&str) -> Vec<Hunk>` structural assertions with no filesystem interaction and no case where the *parsed* result differs behaviorally from hunks already covered by other harvested cases. Not separately CLI-observable; not ported. |
| `parser.rs::test_parse_one_hunk` | `invalid_unknown_hunk_header` | Same code path (`Err(InvalidHunkError{ .. "is not a valid hunk header" .. })` in `parse_one_hunk`'s final fallthrough), adapted first-line text from `"bad"` to `"*** Frobnicate File: x.txt"` for a more realistic malformed-hunk-header patch; message shape is identical. |
| `parser.rs::test_update_file_chunk` (`"bad"`, `"@@"`, `"@@","*** End of File"` assertions) | -- | Internal `parse_update_file_chunk(&[&str], usize, bool)` unit-level assertions on the "missing `@@`" and "empty chunk" paths -- already covered end-to-end by `invalid_empty_update_hunk` and the parser's whole-patch validation; would be redundant sub-cases of the same `InvalidHunkError` family. Not separately ported. |
| `parser.rs::test_update_file_chunk` (`"Unexpected line found in update hunk"` assertion) | `invalid_unexpected_line_in_update_hunk` | Direct port -- distinct error message/code path (a line not starting with `' '`/`'+'`/`'-'`). |
| `seek_sequence.rs::*` (4 tests) | -- (indirectly exercised) | Pure-function tests on `seek_sequence` with no filesystem/CLI surface. Their behaviors (exact match, rstrip-tolerant match, trim-tolerant match, `pattern.len() > lines.len()` guard) are exercised indirectly through the update cases above (in particular the Unicode-normalisation pass is exercised by `update_unicode_dash_fuzzy_match`). Not separately portable to a CLI case since `seek_sequence` is a private (`pub(crate)`) function. |

Required coverage checklist (from the task brief): add file (✓ `add_file_creates_content`),
delete file (✓ `delete_file_removes_it`), update single chunk (✓
`update_single_chunk_modifies_content`), update multiple chunks (✓
`update_multiple_chunks_single_file`), interleaved changes (✓ two variants),
move/rename (✓ `update_file_can_move`), unicode-dash (✓
`update_unicode_dash_fuzzy_match`), insert-at-EOF (✓ `update_insert_at_eof`),
>= 3 invalid-patch cases with real non-zero exit (✓ five: see below).

## The central discovery: `apply_hunks` swallows `apply_hunks_to_files` errors

The task brief named three "invalid patch" categories and assumed all three
would exit non-zero: **malformed envelope**, **context that doesn't match**,
and **update to a nonexistent file**. Calibration proved only the first is
true for this answer key. Reading `upstream/rs/lib.rs::apply_hunks`:

```rust
pub fn apply_hunks(hunks: &[Hunk], stdout: &mut impl Write, stderr: &mut impl Write)
    -> Result<(), ApplyPatchError>
{
    let _existing_paths = /* ... unused ... */;
    match apply_hunks_to_files(hunks) {
        Ok(affected) => { print_summary(&affected, stdout)?; }
        Err(err)     => { writeln!(stderr, "{err:?}")?; }   // <-- message written, error NOT propagated
    }
    Ok(())   // <-- ALWAYS Ok, regardless of which arm above ran
}
```

`apply_hunks_to_files` returns `anyhow::Result<AffectedPaths>` and is the
function that actually calls `std::fs::write` / `std::fs::remove_file` /
`derive_new_contents_from_chunks` (which itself calls
`std::fs::read_to_string`) for each hunk. Any failure there -- file not
found, context/old-lines not found by `seek_sequence`, "No files were
modified" for an empty hunk list -- produces `Err(anyhow::Error)`. That `Err`
is caught in the `match` above, its message is written to **stderr**, and
`apply_hunks` unconditionally returns `Ok(())` on the next line regardless of
which arm executed. `apply_patch` (the public entry point our shim calls)
only returns `Err` when `parse_patch` itself fails -- i.e. a syntactic
problem with the patch envelope/hunk grammar. Every *runtime* application
failure is silently downgraded to a stderr message plus **exit 0**.

This was verified empirically (not just by reading the source) against the
built `calibration/shim` binary before any of the affected cases were written
into `cases.json` -- see the transcript in the session log: context-mismatch,
update-to-missing-file, delete-of-missing-file, and the empty-hunks-list
patch all produced `EXIT=0` with unchanged (or, for the empty-patch case,
literally absent) file trees.

### Adaptation of the three named "invalid" categories

- **malformed envelope**: behaves as assumed (real `ParseError`, real
  non-zero exit). Kept as `invalid_missing_begin_patch_marker` and
  `invalid_missing_end_patch_marker`, plus two more parse-time cases
  (`invalid_unknown_hunk_header`, `invalid_unexpected_line_in_update_hunk`)
  and one more (`invalid_empty_update_hunk`) to comfortably clear the ">= 3"
  bar with real, verified non-zero exits -- five parse-time-invalid cases in
  total, none weakened or guessed.
- **context that doesn't match**: real behavior is exit 0, file left
  untouched. Ported as `quirk_update_context_mismatch_silently_succeeds` with
  `expect_exit_zero: true` (not `false`) and `files_after: {}` (fully
  deterministic -- no `skip_tree_check` needed), explicitly named `quirk_*`
  to flag that this encodes a discovered silent-failure bug rather than the
  originally assumed "should fail loudly" behavior.
- **update to a nonexistent file**: same story. Ported as
  `quirk_update_nonexistent_file_silently_succeeds`, `expect_exit_zero: true`,
  `files_after: {}` (file provably never gets created).

Two further quirks turned up during the same calibration pass and were
ported for completeness, since they are the same bug class and are cheap,
fully-deterministic regression pins:

- `quirk_delete_nonexistent_file_silently_succeeds` -- deleting a file that
  isn't there: exit 0, no-op.
- `quirk_empty_patch_no_hunks_silently_succeeds` -- a syntactically valid
  patch with zero hunks (`*** Begin Patch\n*** End Patch`) parses fine (an
  empty `Vec<Hunk>` is a valid `parse_patch` result -- see
  `parser.rs::test_parse_patch`'s `Ok(Vec::new())` assertion) but then
  `apply_hunks_to_files` bails with `"No files were modified."`; same
  swallow-and-continue behavior, exit 0.

### Partial, non-atomic application across hunks (not named in the brief, discovered during calibration)

`apply_hunks_to_files` iterates `hunks: &[Hunk]` with a plain `for` loop and
uses `?` inside the loop body. A failing hunk (e.g. an `Update File` whose
target doesn't exist) **immediately returns** from `apply_hunks_to_files`,
so:

- every hunk *before* the failing one in patch order has already been
  written to disk and **stays written** (no rollback), and
- every hunk *after* the failing one is **never even attempted**.

Combined with the swallowed-error behavior above, the net effect for a
multi-hunk patch is: **partial application, non-atomic across hunks,
silently reported as success (exit 0)**. This is pinned by
`quirk_partial_application_across_hunks_non_atomic`: a 3-hunk patch (`Add
File: a.txt`, then `Update File: missing.txt` which fails, then `Add File:
c.txt`) results in `a.txt` created, `missing.txt` untouched (never existed),
and `c.txt` **never created** -- exit 0. `files_after` asserts exactly
`{"a.txt": "hello\n"}`, i.e. `c.txt` must be absent.

Within a single `Update File` hunk, by contrast, multiple internal `@@`
chunks *are* atomic with respect to that one file:
`derive_new_contents_from_chunks` computes all replacements via
`compute_replacements` before issuing a single `std::fs::write`, so a
mid-file chunk failure prevents any write to that file at all. Atomicity
here is per-hunk (per-file), not per-patch.

## `skip_tree_check`

Added to the schema as instructed, and implemented in `grade.py` (see the
`skip_tree_check` handling in `run_case`), but **no case in `cases.json`
currently sets it to `true`**. Every discovered failure mode -- including
the partial-application quirk above -- turned out to be fully deterministic
and directly assertable byte-for-byte, so there was no case where "assert
exit code only" was actually necessary. The field's behavior was validated
with a throwaway synthetic case during development (intentionally-wrong
`files_after` content + `skip_tree_check: true` -> grader still passes on
exit code alone; flipping `expect_exit_zero` on the same synthetic case ->
grader still fails on the exit-code assertion even with the tree check
skipped) to confirm the code path is live, not dead. That synthetic case was
not committed to `cases.json`.

## Dropped / not ported (summary)

| Source | Reason |
|---|---|
| `lib.rs::test_literal`, `lib.rs::test_heredoc` | argv-shape API (`maybe_parse_apply_patch`), not the stdin/CLI surface this benchmark grades. |
| `lib.rs::test_unified_diff` | Duplicate of `update_multiple_chunks_single_file`'s fixture/outcome; only exercises the (ungraded) diff-string API, not `apply_patch`. |
| `parser.rs::test_parse_patch` (multi-hunk / update-then-add / missing-`@@`-header assertions) | Pure parse-structure assertions with no distinct CLI-observable behavior beyond what's already covered. |
| `parser.rs::test_update_file_chunk` (`"bad"`, `"@@"`, `"@@","*** End of File"` assertions) | Sub-cases of the same `InvalidHunkError` family already covered by `invalid_empty_update_hunk`. |
| `seek_sequence.rs::*` (all 4 tests) | Pure-function tests on a private (`pub(crate)`) helper; no filesystem/CLI surface. Exercised indirectly through the update cases (notably the Unicode-normalisation path via `update_unicode_dash_fuzzy_match`). |

No case's grading logic in `grade.py` was ever weakened to make a case pass.
Every adaptation above changed a *case's expectation* (or dropped the case)
to match observed reality, never the comparison itself.
