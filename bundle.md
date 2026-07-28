---
bundle:
  name: gm
  version: 0.1.0
  description: >
    GM (Gene Migration) — a two-phase attractor that migrates a whole app from one
    language to another. Phase 1 reverse-engineers the source app into robust,
    dependency-sequenced user stories + testable acceptance criteria (the inventory);
    Phase 2 migrates the code story-by-story into the target language, each story
    gated by its acceptance criteria (as target tests) + a real-terminal forge check,
    one PR per story.

# Self-contained: every source is a full git+https URL; only the `gm:` namespace.
includes:
  - bundle: gm:behaviors/gm-core

session:
  orchestrator:
    module: loop-streaming
    source: git+https://github.com/microsoft/amplifier-module-loop-streaming@main
  context:
    module: context-simple
    source: git+https://github.com/microsoft/amplifier-module-context-simple@main
---

# GM — Gene Migration

Migrate a whole application from **language A to language B**, driven by a
reverse-engineered **inventory** of user stories + acceptance criteria, properly
sequenced so the attractor rebuilds the app feature-by-feature — each feature
verified against its own derived acceptance criteria.

- **Phase 1 — inventory:** `gm:pipelines/inventory.dot` + the `gm-inventory` agent
  study the source (code + observed behavior via forge) and emit a dependency-
  sequenced backlog of user stories with Given/When/Then acceptance.
- **Phase 2 — migration:** `gm:pipelines/migrate.dot` + the `gm-orchestrator` agent
  migrate the code story-by-story in sequence, gated by the acceptance criteria
  (target-language tests) + a real-terminal forge check, one PR per story.

Also on board: the `/gm` mode (migration posture) and `gm-expert` (plan an
instance before running one). See `README.md` for the knobs and `PRINCIPLES.md`
for the non-negotiables.
