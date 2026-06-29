# agent-lab

Lab per costruire **agenti AI piccoli, mirati e replicabili** — per dogfood quotidiano
e per POC/demo a clienti. Stack scelto: **Pydantic AI** (Python, tipizzato, model-agnostic)
+ **OpenRouter** (un'unica key per provare GLM / Kimi / DeepSeek / MiniMax / Qwen).

> Documento di design (bisogno, decisioni, piano): vedi
> `second-brain-demo/SecondBrain/Memory/projects/agent-factory.md`.

## Setup

```bash
uv sync                 # crea .venv e installa le dipendenze
```

Poi crea il file `.env` nella root con la tua chiave OpenRouter
(genera la chiave su <https://openrouter.ai/settings/keys>):

```dotenv
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxx
AGENT_MODEL=z-ai/glm-4.6
```

- `OPENROUTER_API_KEY` — la tua chiave (mai committata: `.env` è in `.gitignore`).
- `AGENT_MODEL` — slug del modello OpenRouter. Cambialo per fare A/B tra provider,
  il codice resta identico. Slug aggiornati: <https://openrouter.ai/models>.

## Validare lo stack (Fase 0)

```bash
uv run python agents/hello/agent.py
```

Deve stampare l'output **e** la lista dei tool effettivamente chiamati (`add`,
`current_weekday`). Se i tool vengono chiamati, il modello ha tool-calling
sufficiente per gli agenti L1-2.

## Creare un nuovo agente

```bash
cp -r agents/_template agents/<nome>
# riempi prompt.md + tools.py, registra i tool in agent.py
uv run python agents/<nome>/agent.py
```

## Struttura

```
agent-lab/
├── pyproject.toml          # progetto uv (pydantic-ai, python-dotenv)
├── shared/
│   └── models.py           # build_model(): modello via OpenRouter (swap con AGENT_MODEL)
└── agents/
    ├── _template/          # scaffold clonabile (la "fabbrica")
    ├── hello/              # validazione stack Fase 0
    └── plan_orchestrator/  # gestore piani: --mode am|pm (review) | update (aggiorna)
```

## Gestore piani di lavoro

```bash
uv run python agents/plan_orchestrator/agent.py --mode update            # aggiorna i piani fermi (interattivo)
uv run python agents/plan_orchestrator/agent.py --mode update --dry-run  # mostra i diff senza scrivere
uv run python agents/plan_orchestrator/agent.py --mode am                # review mattutina (read-only)
uv run python agents/plan_orchestrator/agent.py --mode pm                # review serale
```

Flusso consigliato: prima `update` (rende i piani veritieri), poi `am`/`pm`
(review su stato reale). Registry dei piani in `agents/plan_orchestrator/plans.toml`.

## Roadmap

1. ✅ Fase 0 — setup stack + hello agent (tool-calling check).
2. ✅ Fase 1 — scaffold template consolidato.
3. ✅ Fase 2 — gestore piani: orchestratore (am/pm) + plan-updater (update).
4. ⬜ Fase 3 — schedulazione AM/PM; diagrammi di processo / content; meta-agente.
