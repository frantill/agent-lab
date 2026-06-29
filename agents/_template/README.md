# Template agente

Scaffold minimo da clonare per ogni nuovo agente del lab.

```bash
cp -r agents/_template agents/<nome>
# poi: riempi prompt.md, scrivi i tool in tools.py, registrali in agent.py
uv run python agents/<nome>/agent.py
```

File:
- `prompt.md` — system prompt in linguaggio naturale (advisor mode).
- `tools.py` — le capacità che l'LLM può invocare (una funzione = un tool).
- `agent.py` — assembla modello + prompt + tool e fa girare l'agente.

Il modello arriva da `shared/models.py` (OpenRouter, swap via `AGENT_MODEL`).
