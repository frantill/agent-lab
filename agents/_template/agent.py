"""Agente <NOME>.

Per creare un nuovo agente:
  1. copia questa cartella:  cp -r agents/_template agents/<nome>
  2. riempi prompt.md e tools.py
  3. registra i tool qui sotto
  4. run:  uv run python agents/<nome>/agent.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Rende importabili la root del repo (per `shared`) e questa cartella (per `tools`).
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pydantic_ai import Agent  # noqa: E402

from shared.models import build_model  # noqa: E402

import tools  # noqa: E402

PROMPT = (Path(__file__).parent / "prompt.md").read_text(encoding="utf-8")

agent = Agent(build_model(), system_prompt=PROMPT)

# Registra i tool definiti in tools.py:
agent.tool_plain(tools.read_text_file)


def _output(result: object) -> object:
    return getattr(result, "output", None) or getattr(result, "data", None)


def main() -> None:
    result = agent.run_sync("Presentati e dimmi cosa sai fare.")
    print(_output(result))


if __name__ == "__main__":
    main()
