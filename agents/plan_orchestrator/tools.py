"""Tool dell'orchestratore piani.

Quasi tutto il contesto arriva già pre-calcolato nel prompt (digest deterministico
da gather.py). Qui esponiamo solo il "drill" su un singolo piano, da usare quando
serve approfondire oltre al digest.
"""

from __future__ import annotations

import gather


def read_plan(label: str) -> str:
    """Restituisce il contenuto integrale del piano con la label indicata.

    Usa SOLO se il digest non basta e devi approfondire un piano specifico.
    """
    return gather.read_plan_text(label)
