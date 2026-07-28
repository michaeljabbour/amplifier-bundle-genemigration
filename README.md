# amplifier-bundle-genemigration

**GM — the Gene-Migration attractor.** A self-contained Amplifier bundle that
migrates a whole application from **one language to another**, driven by a
reverse-engineered **inventory** of user stories + acceptance criteria, properly
sequenced so the attractor rebuilds the app feature-by-feature — each feature
verified against its own derived acceptance criteria + a real-terminal
[forge](https://github.com/michaeljabbour/amplifier-skill-forge) check.

Sibling to [`amplifier-bundle-genetransfer`](https://github.com/michaeljabbour/amplifier-bundle-genetransfer)
(HGT): where HGT *cherry-picks capabilities* from a donor into existing hosts, GM
*rebuilds a whole app* in a new language. Same engine, different job.

## Two phases

1. **Inventory (reverse requirements engineering).** Study the source app — its code
   AND its live behavior via forge — and emit dependency-**sequenced** user stories
   with testable Given/When/Then acceptance criteria. The inventory is the assist:
   it's the spec and the migration order. (`gm-inventory` · `pipelines/inventory.dot`.)
2. **Migration (the attractor loop).** Rebuild the app story-by-story in sequence,
   each story implemented idiomatically in the target language, gated by its
   acceptance criteria (as target tests) + a forge boot of the migrated app, one PR
   per story. (`gm-orchestrator` · `pipelines/migrate.dot`.)

## Knobs

| Knob | What |
|---|---|
| **source** | `SOURCE_PATH` + `SOURCE_KIND` — the app being migrated (language A). Read + observe only. |
| **target** | `TARGET_PATH` + `TARGET_KIND` (`python`/`rust`/`new:<lang>`) — the migration home (language B). May be a **new/empty repo**; story #1 scaffolds its CI. |
| **inventory** | `<target>/inventory/` — the reverse-engineered plan, committed to the target repo as the living migration doc. |

## What makes it distinct

- **Reverse-engineered, sequenced spec.** Robust user stories + acceptance criteria,
  ordered by dependency — the sequence IS the migration plan.
- **Behavior fidelity, idiomatic rebuild.** Study the source deeply; re-implement in
  the target's own idioms; never transliterate. Acceptance criteria are the oracle.
- **Living inventory.** A gate failure that exposes a wrong criterion amends the
  story card — the spec is corrected, never force-greened.
- **Forge-woven QA + gate == CI**, same as HGT.

## Install & run

```sh
amplifier bundle add git+https://github.com/michaeljabbour/amplifier-bundle-genemigration@main
amplifier bundle use gm            # /gm mode + gm-inventory / gm-orchestrator / gm-expert
```

- **Orchestrator-as-engine (recommended):** `/gm`, then `gm-inventory` (Phase 1) →
  review the backlog → `gm-orchestrator` (Phase 2).
- **run_pipeline engine:** `bundles/gm-interactive.yaml`; pass `SOURCE_PATH`,
  `TARGET_PATH`, `TARGET_KIND`, `BACKLOG`, … See `context/gm-runbook.md`.

## Layout

| Path | What |
|---|---|
| `bundle.md` · `behaviors/gm-core.yaml` | Root bundle + composable capability set |
| `bundles/` | `gm-pipeline` (headless) · `gm-interactive` (run_pipeline) launchers |
| `agents/` | `gm-inventory` · `gm-orchestrator` · `gm-expert` |
| `modes/gm.md` | `/gm` migration posture |
| `context/` | `gm-awareness.md` (thin) · `gm-runbook.md` (method) · `story-template.md` |
| `pipelines/` | `inventory.dot` · `migrate.dot` · `ledger.py` |
| `examples/newtui-to-rust/` | Worked instance (Python/Textual → Rust/ratatui) |
| `PRINCIPLES.md` · `docs/DESIGN_DECISIONS.md` | Non-negotiables · why it's shaped this way |

## Principles (full list in `PRINCIPLES.md`)

Behavior is the truth, the inventory is the spec · study deeply, rebuild idiomatically,
never transliterate · sequence is the plan · acceptance criteria are the oracle (and
alive) · the terminal proves parity · gate == CI · never a protected branch · bounded
& never stalled · the source is read-only.
