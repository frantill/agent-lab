"""Applicazione deterministica delle operazioni di edit ai piani + diff unificato.

Nessuna chiamata LLM: pura trasformazione di testo, completamente testabile.
L'LLM (in updater.py) decide *cosa* cambiare e restituisce `PlanEdits`; qui si
applica in modo chirurgico, così il file non viene mai riscritto/manglato.
"""

from __future__ import annotations

import difflib
import re
from typing import Literal

from pydantic import BaseModel

CHECKBOX_LINE_RE = re.compile(r"^(\s*[-*]\s+\[)([ xX])(\]\s+)(.*\S)\s*$")
HEADING_RE = re.compile(r"^#{1,6}\s+(.*\S)\s*$")
STATUS_RE = re.compile(r"^status:\s*")


class EditOp(BaseModel):
    op: Literal["check", "uncheck", "add_task", "set_status"]
    target: str | None = None  # testo task esistente (check/uncheck) o heading (add_task)
    value: str | None = None  # testo nuovo task (add_task) o nuovo status (set_status)


class PlanEdits(BaseModel):
    summary: str
    edits: list[EditOp]


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def _match(target_norm: str, text_norm: str) -> bool:
    if not target_norm:
        return False
    return target_norm == text_norm or target_norm in text_norm or text_norm in target_norm


def _flip_checkbox(lines: list[str], target: str, to_checked: bool) -> bool:
    tnorm = _norm(target)
    for i, line in enumerate(lines):
        m = CHECKBOX_LINE_RE.match(line)
        if not m:
            continue
        already = m.group(2) in "xX"
        if already == to_checked:
            continue  # già nello stato desiderato
        if _match(tnorm, _norm(m.group(4))):
            mark = "x" if to_checked else " "
            lines[i] = f"{m.group(1)}{mark}{m.group(3)}{m.group(4)}"
            return True
    return False


def _add_task(lines: list[str], target: str | None, value: str) -> bool:
    new_line = f"- [ ] {value}"
    if target:
        tnorm = _norm(target)
        for i, line in enumerate(lines):
            hm = HEADING_RE.match(line)
            if hm and _match(tnorm, _norm(hm.group(1))):
                lines.insert(i + 1, new_line)
                return True
    lines.append(new_line)
    return True


def _set_status(lines: list[str], value: str) -> bool:
    if not lines or lines[0].strip() != "---":
        return False
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return False  # fine frontmatter senza status
        if STATUS_RE.match(lines[i]):
            lines[i] = f"status: {value}"
            return True
    return False


def apply_edits(text: str, edits: list[EditOp]) -> tuple[str, list[str]]:
    """Applica le operazioni e ritorna (nuovo_testo, log per-operazione)."""
    lines = text.split("\n")
    log: list[str] = []
    for e in edits:
        if e.op == "check" and e.target:
            ok = _flip_checkbox(lines, e.target, True)
        elif e.op == "uncheck" and e.target:
            ok = _flip_checkbox(lines, e.target, False)
        elif e.op == "add_task" and e.value:
            ok = _add_task(lines, e.target, e.value)
        elif e.op == "set_status" and e.value:
            ok = _set_status(lines, e.value)
        else:
            ok = False
        label = e.target or e.value or ""
        log.append(f"{'OK  ' if ok else 'SKIP'} {e.op}: {label}")
    return "\n".join(lines), log


def make_diff(old: str, new: str, path: str) -> str:
    diff = difflib.unified_diff(
        old.splitlines(),
        new.splitlines(),
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
        lineterm="",
    )
    return "\n".join(diff)
