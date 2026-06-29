"""Orchestratore piani di lavoro — Agente #1.

Review AM/PM dei piani sparsi su più repo: stato, next action, e challenge decise
su cosa deprioritizzare o cancellare. Advisor mode.

Run:
  uv run python agents/plan_orchestrator/agent.py --mode am
  uv run python agents/plan_orchestrator/agent.py --mode pm --dry-run
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

# Rende importabili la root del repo (per `shared`) e questa cartella (gather, tools).
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pydantic import BaseModel  # noqa: E402
from pydantic_ai import Agent  # noqa: E402

import gather  # noqa: E402
import tools  # noqa: E402
from shared.models import build_model  # noqa: E402

ROME = ZoneInfo("Europe/Rome")
HERE = Path(__file__).resolve().parent
PROMPT = (HERE / "prompt.md").read_text(encoding="utf-8")
REVIEW_DIR = HERE.parents[1] / "data" / "plan-orchestrator" / "reviews"
DAILY_DIR = Path(
    "/Users/francesco/tech/code/second-brain-demo/SecondBrain/Memory/daily"
)


class PlanReport(BaseModel):
    label: str
    summary: str
    changed_since_last: str
    suggested_next_action: str


class Challenge(BaseModel):
    label: str
    issue: str
    recommendation: Literal["deprioritize", "kill", "revive", "keep"]
    rationale: str


class Review(BaseModel):
    top_next_actions: list[str]
    per_plan: list[PlanReport]
    challenges: list[Challenge]
    questions: list[str]


agent = Agent(build_model(), output_type=Review, system_prompt=PROMPT)
agent.tool_plain(tools.read_plan)


def build_user_prompt(mode: str, digest: str) -> str:
    focus = (
        "È MATTINA. Concentrati sul futuro: cosa fare oggi, come prioritizzare tra i "
        "piani, quali domande aperte risolvere."
        if mode == "am"
        else "È SERA. Concentrati sul passato: cosa si è mosso oggi, quali piani sono "
        "fermi, dove serve deprioritizzare o cancellare."
    )
    today = datetime.now(ROME).strftime("%Y-%m-%d")
    return (
        f"Data: {today} — modalità: {mode.upper()}.\n{focus}\n\n"
        "Digest deterministico dei piani (conteggi, status, freschezza, diff vs ultima review):\n\n"
        f"{digest}\n\n"
        "Produci la review. Sii deciso e secco: se un piano è fermo o non più rilevante, "
        "dillo e raccomanda deprioritize/kill con motivazione. Niente morbidezza. Poche "
        "next action, concrete."
    )


def _output(result: object) -> Review:
    return getattr(result, "output", None) or getattr(result, "data")


def render_md(review: Review, mode: str) -> str:
    today = datetime.now(ROME).strftime("%Y-%m-%d")
    out: list[str] = [f"## 🧭 Plan review — {today} ({mode.upper()})", ""]

    out.append("### Top next actions")
    out += [f"{i}. {a}" for i, a in enumerate(review.top_next_actions, 1)] or ["—"]
    out.append("")

    out.append("### Per piano")
    for p in review.per_plan:
        out.append(f"- **{p.label}** — {p.summary}")
        out.append(f"  - cambiato: {p.changed_since_last}")
        out.append(f"  - next: {p.suggested_next_action}")
    out.append("")

    if review.challenges:
        out.append("### ⚔️ Challenge")
        for c in review.challenges:
            out.append(f"- **{c.label}** → `{c.recommendation}` — {c.issue}")
            out.append(f"  - perché: {c.rationale}")
        out.append("")

    if review.questions:
        out.append("### ❓ Domande per te")
        out += [f"- {q}" for q in review.questions]
        out.append("")

    return "\n".join(out)


def save_outputs(md: str, mode: str) -> tuple[Path, Path]:
    today = datetime.now(ROME).strftime("%Y-%m-%d")

    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    review_path = REVIEW_DIR / f"{today}-{mode}.md"
    review_path.write_text(md + "\n", encoding="utf-8")

    DAILY_DIR.mkdir(parents=True, exist_ok=True)
    daily_path = DAILY_DIR / f"{today}.md"
    new_file = not daily_path.exists()
    with daily_path.open("a", encoding="utf-8") as f:
        if new_file:
            f.write(f"# {today}\n\n")
        f.write("\n" + md + "\n")
    return review_path, daily_path


def main() -> None:
    ap = argparse.ArgumentParser(description="Orchestratore piani di lavoro")
    ap.add_argument("--mode", choices=["am", "pm"], default="am")
    ap.add_argument("--dry-run", action="store_true", help="non scrive nulla su disco")
    args = ap.parse_args()

    stats = gather.gather()
    digest = gather.build_digest(stats)
    result = agent.run_sync(build_user_prompt(args.mode, digest))
    review = _output(result)
    md = render_md(review, args.mode)

    print(md)
    if args.dry_run:
        print("\n[dry-run: nessun file scritto, stato non aggiornato]")
        return

    review_path, daily_path = save_outputs(md, args.mode)
    gather.save_state(stats, args.mode)
    print(f"\n[salvato: {review_path}]")
    print(f"[appeso a: {daily_path}]")


if __name__ == "__main__":
    main()
