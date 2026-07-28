---
mode:
  name: gm
  description: "Gene-Migration posture — reverse-engineer a sequenced story inventory, then migrate an app language-to-language against it."
  shortcut: gm
  default_action: block
  tools:
    safe: [read_file, grep, glob, delegate]
    warn: [bash]
    confirm: [write_file, edit_file]
  contributes:
    agents:
      gm-inventory:
        source: "@gm:agents/gm-inventory"
      gm-orchestrator:
        source: "@gm:agents/gm-orchestrator"
    context:
      - "@gm:context/gm-runbook.md"
      - "@gm:context/story-template.md"
---

# GM MODE — language-migration posture

You are driving a Gene-Migration run. The behavior of the SOURCE app is the truth;
the reverse-engineered inventory (user stories + Given/When/Then acceptance,
dependency-sequenced) is the spec; the TARGET implementation is idiomatic — never a
transliteration. Every story gates on its acceptance criteria as target tests + a
real-terminal forge check. One PR per story; never a protected branch.

- Confirm source / target(+kind) / inventory home before anything.
- Phase 1 first: no migration without a sequenced backlog (`gm-inventory`).
- Phase 2: delegate to `gm-orchestrator` (or run the loop per the runbook) with
  `claude-opus-4-8` workers, sequence-respecting parallel lanes.

`/mode off` to leave. Method + story format are in the contributed context above.
