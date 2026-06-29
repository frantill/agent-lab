"""Hello agent — valida lo stack di Fase 0.

Verifica due cose in una sola run:
  1. che riusciamo a parlare con un modello open via OpenRouter;
  2. che il TOOL-CALLING funzioni (il vero discrimine sui modelli piccoli).

Run:  uv run python agents/hello/agent.py
"""

from __future__ import annotations

import datetime
import sys
from pathlib import Path

# Rende importabile la cartella root del repo (per `shared`).
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pydantic_ai import Agent  # noqa: E402

from shared.models import build_model  # noqa: E402

agent = Agent(
    build_model(),
    system_prompt=(
        "Sei un assistente di test. Quando l'utente chiede un calcolo o il giorno "
        "della settimana, DEVI usare gli strumenti disponibili invece di rispondere "
        "a memoria. Poi riassumi i risultati in una frase."
    ),
)


@agent.tool_plain
def add(a: int, b: int) -> int:
    """Somma due numeri interi e ne restituisce il risultato."""
    return a + b


@agent.tool_plain
def current_weekday() -> str:
    """Restituisce il giorno della settimana corrente (in inglese)."""
    return datetime.date.today().strftime("%A")


def _output(result: object) -> object:
    # Compatibilità tra versioni di pydantic-ai (.output nuove, .data vecchie).
    return getattr(result, "output", None) or getattr(result, "data", None)


def main() -> None:
    prompt = "Quanto fa 17 + 25? E che giorno della settimana è oggi? Usa gli strumenti."
    result = agent.run_sync(prompt)

    print("=== Output ===")
    print(_output(result))

    print("\n=== Tool effettivamente chiamati ===")
    found = False
    for msg in result.all_messages():
        for part in getattr(msg, "parts", []):
            if part.__class__.__name__ == "ToolCallPart":
                found = True
                print(f"- {part.tool_name}({getattr(part, 'args', '')})")
    if not found:
        print("(nessun tool chiamato — il modello potrebbe avere tool-calling debole)")


if __name__ == "__main__":
    main()
