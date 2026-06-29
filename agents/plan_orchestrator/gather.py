"""Gather deterministico per l'orchestratore piani.

Legge il registry (plans.toml), parsa ogni piano (checkbox, status frontmatter,
freschezza git), calcola il diff rispetto allo snapshot precedente e produce un
digest compatto da passare all'LLM. NESSUNA chiamata al modello qui dentro:
questa è la parte ripetibile, economica e testabile.
"""

from __future__ import annotations

import json
import re
import subprocess
import tomllib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROME = ZoneInfo("Europe/Rome")
HERE = Path(__file__).resolve().parent
REGISTRY = HERE / "plans.toml"
DATA_DIR = HERE.parents[1] / "data" / "plan-orchestrator"
STATE_FILE = DATA_DIR / "state.json"

CHECKBOX_RE = re.compile(r"^\s*[-*]\s+\[([ xX])\]\s+(.*\S)\s*$")
FRONTMATTER_STATUS_RE = re.compile(r"^status:\s*(.+?)\s*$", re.MULTILINE)
MAX_OPEN_IN_DIGEST = 6
MAX_DIFF_IN_DIGEST = 5


@dataclass
class PlanStat:
    label: str
    path: str
    exists: bool
    status: str | None
    done_tasks: list[str]
    open_tasks: list[str]
    last_commit: str | None
    stale_days: int | None
    newly_done: list[str]
    newly_added: list[str]

    @property
    def done(self) -> int:
        return len(self.done_tasks)

    @property
    def open(self) -> int:
        return len(self.open_tasks)


def load_registry() -> list[tuple[str, Path]]:
    data = tomllib.loads(REGISTRY.read_text(encoding="utf-8"))
    plans: list[tuple[str, Path]] = []
    seen: set[Path] = set()
    for entry in data.get("plan", []):
        p = Path(entry["path"]).expanduser()
        if p not in seen:
            seen.add(p)
            plans.append((entry["label"], p))
    for g in data.get("plan_glob", []):
        d = Path(g["dir"]).expanduser()
        for fp in sorted(d.glob(g.get("pattern", "*.md"))):
            if fp not in seen:
                seen.add(fp)
                plans.append((fp.stem, fp))
    return plans


def _parse_frontmatter_status(text: str) -> str | None:
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    m = FRONTMATTER_STATUS_RE.search(text[3:end])
    return m.group(1) if m else None


def _parse_checkboxes(text: str) -> tuple[list[str], list[str]]:
    done: list[str] = []
    open_: list[str] = []
    for line in text.splitlines():
        m = CHECKBOX_RE.match(line)
        if m:
            (done if m.group(1) in "xX" else open_).append(m.group(2).strip())
    return done, open_


def _git_last_commit(path: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(path.parent), "log", "-1", "--format=%cI", "--", str(path)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return out.stdout.strip() or None
    except Exception:
        return None


def _stale_days(iso: str | None) -> int | None:
    if not iso:
        return None
    try:
        d = datetime.fromisoformat(iso).astimezone(ROME).date()
        return (datetime.now(ROME).date() - d).days
    except Exception:
        return None


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def gather() -> list[PlanStat]:
    prev = _load_state().get("plans", {})
    stats: list[PlanStat] = []
    for label, path in load_registry():
        if not path.exists():
            stats.append(PlanStat(label, str(path), False, None, [], [], None, None, [], []))
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        done, open_ = _parse_checkboxes(text)
        last = _git_last_commit(path)
        prev_plan = prev.get(label)
        if prev_plan:
            prev_done = set(prev_plan.get("done", []))
            prev_all = prev_done | set(prev_plan.get("open", []))
            newly_done = [t for t in done if t not in prev_done]
            newly_added = [t for t in (done + open_) if t not in prev_all]
        else:
            newly_done, newly_added = [], []
        stats.append(
            PlanStat(
                label, str(path), True, _parse_frontmatter_status(text),
                done, open_, last, _stale_days(last), newly_done, newly_added,
            )
        )
    return stats


def build_digest(stats: list[PlanStat]) -> str:
    lines: list[str] = []
    for s in stats:
        if not s.exists:
            lines.append(f"PIANO: {s.label} — ⚠️ FILE NON TROVATO ({s.path})")
            lines.append("")
            continue
        fresh = f"fermo da {s.stale_days}g" if s.stale_days is not None else "freschezza n/d"
        st = f"status: {s.status}" if s.status else "status: n/d"
        lines.append(f"PIANO: {s.label} — {st} — {fresh}")
        lines.append(f"  task: {s.done} fatti / {s.open} aperti")
        nd = ", ".join(s.newly_done[:MAX_DIFF_IN_DIGEST]) or "—"
        na = ", ".join(s.newly_added[:MAX_DIFF_IN_DIGEST]) or "—"
        lines.append(f"  completati dall'ultima review: {nd}")
        lines.append(f"  task nuovi: {na}")
        for t in s.open_tasks[:MAX_OPEN_IN_DIGEST]:
            lines.append(f"    - [ ] {t}")
        if s.open > MAX_OPEN_IN_DIGEST:
            lines.append(f"    … e altri {s.open - MAX_OPEN_IN_DIGEST} task aperti")
        lines.append("")
    return "\n".join(lines).strip()


def read_plan_text(label: str) -> str:
    for lbl, path in load_registry():
        if lbl == label:
            return path.read_text(encoding="utf-8", errors="replace") if path.exists() else f"(file non trovato: {path})"
    return f"(nessun piano con label '{label}')"


def save_state(stats: list[PlanStat], mode: str) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    state = {
        "last_review": datetime.now(ROME).isoformat(),
        "last_mode": mode,
        "plans": {
            s.label: {"done": s.done_tasks, "open": s.open_tasks}
            for s in stats
            if s.exists
        },
    }
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
