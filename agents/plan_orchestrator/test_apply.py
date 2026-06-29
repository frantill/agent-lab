"""Test deterministici per apply.py (no LLM). Run: uv run python .../test_apply.py"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import apply  # noqa: E402

SAMPLE = """---
title: Demo
status: shaping
---

# Piano

## Fase 1
- [ ] Configurare OpenRouter
- [ ] Scrivere hello agent
- [x] Creare repo
"""


def run() -> None:
    edits = [
        apply.EditOp(op="check", target="Configurare OpenRouter"),
        apply.EditOp(op="add_task", target="Fase 1", value="Aggiungere test"),
        apply.EditOp(op="set_status", value="building"),
        apply.EditOp(op="uncheck", target="Creare repo"),
        apply.EditOp(op="check", target="task inesistente xyz"),  # deve SKIP
    ]
    new_text, log = apply.apply_edits(SAMPLE, edits)

    assert "- [x] Configurare OpenRouter" in new_text, "check fallito"
    assert "- [ ] Aggiungere test" in new_text, "add_task fallito"
    assert "status: building" in new_text, "set_status fallito"
    assert "- [ ] Creare repo" in new_text, "uncheck fallito"
    assert "SKIP check: task inesistente xyz" in "\n".join(log), "skip non loggato"
    # add_task inserito subito sotto l'heading Fase 1
    lines = new_text.split("\n")
    idx_h = lines.index("## Fase 1")
    assert lines[idx_h + 1] == "- [ ] Aggiungere test", "add_task non sotto l'heading"

    diff = apply.make_diff(SAMPLE, new_text, "demo.md")
    assert diff.strip(), "diff vuoto"

    print("log operazioni:")
    for line in log:
        print("  " + line)
    print("\n--- diff ---")
    print(diff)
    print("\nTUTTI I TEST OK ✓")


if __name__ == "__main__":
    run()
