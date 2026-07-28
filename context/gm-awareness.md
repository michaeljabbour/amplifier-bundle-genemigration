# GM — Gene Migration (awareness)

This session can migrate a whole app from **one language to another**, driven by a
reverse-engineered inventory. Two phases:

1. **Inventory** — study the source app (code + observed behavior via forge) and
   emit dependency-**sequenced** user stories with testable Given/When/Then
   acceptance criteria. (`gm-inventory` agent · `gm:pipelines/inventory.dot`.)
2. **Migration** — rebuild the app story-by-story in the target language, in
   sequence, each story gated by its acceptance criteria (target tests) + a
   real-terminal forge check, one PR per story. (`gm-orchestrator` agent ·
   `gm:pipelines/migrate.dot`.)

**Ways in:** `/gm` mode · `delegate(agent="gm:gm-orchestrator", …)` to run the
migration · `gm:gm-inventory` to build/refresh the inventory · `gm:gm-expert` to
plan an instance. **When to reach for it:** "migrate this app from X to Y",
"rebuild the Python app in Rust", keeping a rewrite faithful to the original's
behavior. The inventory is the assist: it's the spec and the sequence. Read
`PRINCIPLES.md` before a run.
