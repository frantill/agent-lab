"""Tool dell'agente <NOME>. Ogni funzione = una capacità che l'LLM può invocare.

Linee guida:
- Funzioni piccole e pure quando possibile.
- Docstring chiara: l'LLM la legge per decidere quando/come chiamare il tool.
- Type hint sempre: Pydantic AI li usa per validare gli argomenti.
"""

from __future__ import annotations

from pathlib import Path


def read_text_file(path: str) -> str:
    """Legge e restituisce il contenuto di un file di testo dato il suo percorso."""
    return Path(path).read_text(encoding="utf-8")


# Aggiungi qui altri tool, poi registrali in agent.py.
