//! Tiny CLI shim around the frozen `codex_apply_patch` answer-key crate.
//!
//! Contract (see benchmark README): reads the entire patch text from stdin,
//! applies it relative to the current working directory, exits 0 iff the
//! patch fully applied, non-zero otherwise. stdout/stderr content is not
//! part of the grading contract.
//!
//! This calls the crate's public `apply_patch(patch, stdout, stderr)` API
//! (see upstream/rs/lib.rs around line 211) verbatim -- no reimplementation
//! of any apply/parse logic lives here.

use std::io::Read;
use std::process::ExitCode;

fn main() -> ExitCode {
    let mut patch = String::new();
    if let Err(e) = std::io::stdin().read_to_string(&mut patch) {
        eprintln!("shim: failed to read stdin: {e}");
        return ExitCode::FAILURE;
    }

    let mut stdout = std::io::stdout();
    let mut stderr = std::io::stderr();

    match codex_apply_patch::apply_patch(&patch, &mut stdout, &mut stderr) {
        Ok(()) => ExitCode::SUCCESS,
        Err(e) => {
            eprintln!("shim: apply_patch failed: {e}");
            ExitCode::FAILURE
        }
    }
}
