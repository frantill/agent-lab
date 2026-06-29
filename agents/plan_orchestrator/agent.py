"""Gestore piani di lavoro — CLI dispatcher.

Un solo entry point, tre modalità (registry e gather condivisi):
  --mode am | pm   → review advisor, read-only sui piani (review.py)
  --mode update    → aggiornamento interattivo dei piani, scrive con conferma (updater.py)

Esempi:
  uv run python agents/plan_orchestrator/agent.py --mode am
  uv run python agents/plan_orchestrator/agent.py --mode update
  uv run python agents/plan_orchestrator/agent.py --mode update --all --dry-run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Rende importabili la root del repo (per `shared`) e questa cartella (gather/tools/…).
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))


def main() -> None:
    ap = argparse.ArgumentParser(description="Gestore piani di lavoro")
    ap.add_argument("--mode", choices=["am", "pm", "update"], default="am")
    ap.add_argument("--dry-run", action="store_true", help="non scrive nulla su disco")
    ap.add_argument(
        "--all",
        action="store_true",
        help="(solo update) rivedi tutti i piani, non solo quelli fermi/sospetti",
    )
    args = ap.parse_args()

    if args.mode == "update":
        import updater

        updater.run_update(all_plans=args.all, dry_run=args.dry_run)
    else:
        import review

        review.run_review(mode=args.mode, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
