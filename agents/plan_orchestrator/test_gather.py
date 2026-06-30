"""Test deterministici per gather.py (parsing, no LLM)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gather  # noqa: E402

# Prosa con marcatori inline (NON deve generare task) + una vera tabella di stato.
SAMPLE = """---
status: building
---

# Doc di design

Nelle tabelle (✅ / ⬜ / ⚠️) distinguiamo pending/in-progress/done.
- Marcatori di tabella ✅/⬜: v1 li lascia stare.
- ✅ RISOLTE alcune decisioni nel testo.

## Tabella stato
| Deliverable | Stato |
|---|---|
| Setup launchd | ✅ Done |
| Deploy VPS | ⬜ Not implemented |
| Sync vault | ⚠️ Parziale |

## Task
- [x] Primo task
- [ ] Secondo task
"""


def run() -> None:
    done, open_ = gather._parse_markers(SAMPLE, already=set())
    # Dalla tabella: 1 done (Setup launchd), 2 open (Deploy VPS, Sync vault).
    assert done == ["Setup launchd"], f"done inatteso: {done}"
    assert open_ == ["Deploy VPS", "Sync vault"], f"open inatteso: {open_}"
    # La prosa con ✅/⬜/⚠️ NON deve comparire.
    joined = " ".join(done + open_)
    assert "RISOLTE" not in joined and "Marcatori" not in joined, "prosa contata come task"

    cb_done, cb_open = gather._parse_checkboxes(SAMPLE)
    assert cb_done == ["Primo task"] and cb_open == ["Secondo task"]

    print("done (tabella):", done)
    print("open (tabella):", open_)
    print("checkbox done/open:", cb_done, cb_open)
    print("\nTUTTI I TEST OK ✓")


if __name__ == "__main__":
    run()
