#!/usr/bin/env python3
"""Derive readable documentation diagrams from the executable pipeline .dot files.

The executable graphs in pipelines/*.dot are engine-parsed (loop-pipeline): their
routing lives in `condition=` attrs, which graphviz does not render, so a raw
render shows unlabeled edges. This script derives a documentation twin per graph:
same nodes and edges, with human-readable edge labels (pass/fail/retry/…, loop ↺),
role colors, and a legend — WITHOUT touching the executable files.

Run from the repo root:  python3 docs/diagrams/generate.py
Regenerate whenever a pipeline graph changes (AGENTS.md verification gradient).
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent

NODE_RE = re.compile(r"^\s*(\w+)\s*\[shape=(\w+)")
EDGE_RE = re.compile(r"^\s*(\w+)\s*->\s*(\w+)\s*(?:\[([^\]]*)\])?")
COND_RE = re.compile(r'condition="context\.tool\.last_line=(\w+)"')

STYLE = {
    "Mdiamond": 'shape=Mdiamond, style=filled, fillcolor="#c8e6c9"',
    "Msquare": 'shape=Msquare, style=filled, fillcolor="#ffcdd2"',
    "box": 'shape=box, style="rounded,filled", fillcolor="#bbdefb"',
    "parallelogram": 'shape=parallelogram, style=filled, fillcolor="#fff9c4"',
}

def derive(src: Path) -> Path:
    nodes: dict[str, str] = {}
    edges: list[tuple[str, str, str]] = []
    for line in src.read_text().splitlines():
        if line.strip().startswith("//"):
            continue
        m = NODE_RE.match(line)
        if m and m.group(2) in STYLE:
            nodes[m.group(1)] = m.group(2)
            continue
        m = EDGE_RE.match(line)
        if m and m.group(1) in nodes:
            attrs = m.group(3) or ""
            cond = COND_RE.search(attrs)
            label = cond.group(1) if cond else ("loop ↺" if "loop_restart" in attrs else "")
            edges.append((m.group(1), m.group(2), label))

    name = src.stem
    out = [f'digraph {name}_doc {{']
    out.append('  rankdir=TB; fontname="Helvetica"; labelloc=t;')
    out.append(f'  label="{name}.dot — documentation view (derived; the executable graph is pipelines/{name}.dot)";')
    out.append('  node [fontname="Helvetica", fontsize=11]; edge [fontname="Helvetica", fontsize=10, color="#546e7a"];')
    for n, shape in nodes.items():
        out.append(f'  {n} [{STYLE[shape]}];')
    for a, b, label in edges:
        attr = f' [label="{label}"' + (', style=dashed' if label == "loop ↺" else "") + "]" if label else ""
        out.append(f"  {a} -> {b}{attr};")
    out.append("""  subgraph cluster_legend {
    label="legend"; fontsize=10; style=dashed; color="#90a4ae";
    l1 [shape=box, style="rounded,filled", fillcolor="#bbdefb", label="LLM agent node"];
    l2 [shape=parallelogram, style=filled, fillcolor="#fff9c4", label="deterministic gate/tool\\n(routes on last stdout line)"];
    l1 -> l2 [label="edge label = routing value", style=invis];
  }""")
    out.append("}")
    dst = OUT / f"{name}.dot"
    dst.write_text("\n".join(out) + "\n")
    subprocess.run(["dot", "-Tpng", str(dst), "-o", str(OUT / f"{name}.png")], check=True)
    return dst

def main() -> int:
    srcs = sorted((ROOT / "pipelines").glob("*.dot"))
    for s in srcs:
        d = derive(s)
        print(f"derived {d.relative_to(ROOT)} + .png from pipelines/{s.name}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
