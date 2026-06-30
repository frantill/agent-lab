"""Modalità update — loop interattivo che mantiene i piani VERITIERI.

Per ogni piano (più fermi prima): mostra lo stato → l'LLM fa max 3 domande secche →
Francesco risponde → l'LLM traduce in operazioni di edit → si mostra il diff → si
applica al file solo con conferma esplicita. Chiude il loop dell'orchestratore:
prima `--mode update`, poi `--mode am/pm` ragiona su uno stato reale.
"""

from __future__ import annotations

import readline  # noqa: F401 — abilita line-editing (word-delete) in input()
from pathlib import Path

from pydantic import BaseModel, ValidationError
from pydantic_ai import Agent
from pydantic_ai.exceptions import UnexpectedModelBehavior

import apply
import gather
from shared.models import build_model

HERE = Path(__file__).resolve().parent
Q_PROMPT = (HERE / "prompt_update_q.md").read_text(encoding="utf-8")
E_PROMPT = (HERE / "prompt_update_e.md").read_text(encoding="utf-8")
STALE_THRESHOLD = 7  # giorni: oltre questa soglia un piano è "sospetto"
# Status che indicano un piano concluso/archiviato: l'updater non lo propone più.
DONE_STATUSES = {"archived", "archiviato", "done", "completato", "completata", "concluso"}


class PlanQuestions(BaseModel):
    questions: list[str]


_q_agent = Agent(build_model(), output_type=PlanQuestions, system_prompt=Q_PROMPT, retries=3)
_e_agent = Agent(build_model(), output_type=apply.PlanEdits, system_prompt=E_PROMPT, retries=3)


def _out(result: object):
    return getattr(result, "output", None) or getattr(result, "data")


def _select(stats: list[gather.PlanStat], all_plans: bool) -> list[gather.PlanStat]:
    # I reference (doc di strategia) e i piani già conclusi/archiviati non si
    # aggiornano a task: esclusi sempre, anche con --all.
    plans = [
        s
        for s in stats
        if s.exists
        and s.kind != "reference"
        and (s.status or "").strip().lower() not in DONE_STATUSES
    ]
    if not all_plans:
        plans = [s for s in plans if (s.stale_days or 0) >= STALE_THRESHOLD or s.open > 0]
    return sorted(plans, key=lambda s: (s.stale_days or 0), reverse=True)


def _plan_digest(s: gather.PlanStat) -> str:
    fresh = f"fermo da {s.stale_days}g" if s.stale_days is not None else "freschezza n/d"
    lines = [
        f"Piano: {s.label}",
        f"status: {s.status or 'n/d'} — {fresh} — {s.done} fatti / {s.open} aperti",
    ]
    if s.open_tasks:
        lines.append("Task aperti:")
        lines += [f"  - {t}" for t in s.open_tasks[:15]]
    if s.newly_done:
        lines.append("Completati dall'ultima review: " + ", ".join(s.newly_done[:8]))
    return "\n".join(lines)


def _process_plan(s: gather.PlanStat, dry_run: bool) -> bool:
    path = Path(s.path)
    digest = _plan_digest(s)
    print("=" * 72)
    print(digest)

    questions = _out(_q_agent.run_sync(f"Stato del piano:\n\n{digest}")).questions
    print("\nDomande:")
    for i, q in enumerate(questions, 1):
        print(f"  {i}. {q}")

    ans = input("\nRisposte (testo libero — invio vuoto o 'skip' per saltare): ")
    # Rimuove i caratteri di controllo (es. escape sequence da Option+Backspace)
    # che sporcherebbero il prompt passato all'LLM.
    ans = "".join(ch for ch in ans if ch.isprintable() or ch == " ").strip()
    if ans.lower() in ("", "skip"):
        print("→ saltato.\n")
        return False

    content = path.read_text(encoding="utf-8", errors="replace")
    e_prompt = (
        f"PIANO (markdown integrale):\n{content}\n\n"
        "DOMANDE poste:\n" + "\n".join(f"- {q}" for q in questions) + "\n\n"
        f"RISPOSTE di Francesco:\n{ans}\n\n"
        "Produci le operazioni di edit. Se una risposta è ambigua non inventare edit."
    )
    edits = _out(_e_agent.run_sync(e_prompt))
    if not edits.edits:
        print("→ nessuna modifica proposta.\n")
        return False

    new_text, log = apply.apply_edits(content, edits.edits)
    diff = apply.make_diff(content, new_text, s.path)

    print(f"\nProposta: {edits.summary}")
    print("Operazioni:")
    for line in log:
        print(f"  {line}")
    if not diff.strip():
        print("→ nessun cambiamento effettivo sul file.\n")
        return False

    print("\n--- DIFF ---")
    print(diff)

    if dry_run:
        print("\n[dry-run: non scrivo]\n")
        return False

    if input("\nApplico al file? [s/N]: ").strip().lower() == "s":
        path.write_text(new_text, encoding="utf-8")
        print(f"✓ scritto {s.path}\n")
        return True
    print("→ non applicato.\n")
    return False


def run_update(all_plans: bool, dry_run: bool) -> None:
    selected = _select(gather.gather(), all_plans)
    if not selected:
        print("Nessun piano da aggiornare.")
        return

    scope = "tutti" if all_plans else f"sospetti (fermi ≥{STALE_THRESHOLD}g o con task aperti)"
    print(f"Piani da rivedere: {len(selected)} — {scope}, più fermi prima.\n")

    updated: list[str] = []
    for s in selected:
        try:
            if _process_plan(s, dry_run):
                updated.append(s.label)
        except (KeyboardInterrupt, EOFError):
            print("\n\nInterrotto.")
            break
        except (UnexpectedModelBehavior, ValidationError) as exc:
            print(f"\n⚠ piano '{s.label}' saltato — errore del modello: {exc}\n")
            continue

    print("=" * 72)
    print(f"Aggiornati: {', '.join(updated) if updated else 'nessuno'}")
    if updated and not dry_run:
        print("Ora lancia: --mode am   (review su stato aggiornato)")
