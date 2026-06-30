# agent-lab — STATUS · aggiornato 2026-06-30

> Plancia tattica. Strategia/design: second-brain → `agent-factory.md`. Storico: `git log`.
> **Come si usa:** conversa con Claude leggendo questo file (diverge: brainstorm, calibra) →
> aggiorna via chat o `--mode update` (converge: fissa lo stato). Tienilo sotto ~50 righe.

## ▶️ Riprendi da qui
- Rivedere la **PR #2** (draft) su `agent-lab` e marcarla ready / merge quando ok.

## 🔧 Work in progress
- (nessuno) — i fix updater/registry sono nella **PR #2**, in attesa di tua review.

## ⏭️ Next — deciso, da fare (prioritizzato)
1. Review + merge **PR #2** (robustezza updater + kind/reference).
2. Dopo merge: ri-test `--mode update` su un piano reale, poi `--mode am`.
3. Schedulazione launchd: `update` serale + `am` mattino.
4. Secondo use case sullo scaffold: diagrammi di processo (#4) o content (#2).

## 💡 Nice-to-have / parcheggiati
- Editare anche celle di tabella ✅/⬜ (oltre ai checkbox).
- Comando `plans add <path>` per il registry.
- A/B costo-qualità GLM vs DeepSeek vs Kimi.
- "Status copilot" conversazionale dedicato — solo se il pattern chat+STATUS si rivela ripetitivo.
- Dogfood: `STATUS.md` nel registry (richiede struttura a checkbox o handling reference).

## ❓ Decisioni aperte
- Rinominare `plan_orchestrator/` → `plan_manager/`?
- Modelli locali (Ollama) per demo a costo zero?

## 🐞 Known issues
- (nessuno aperto) — crash `--mode update` mitigato; set_status / marker / registry risolti in PR #2.

## ✅ Done recenti (dettaglio in git log)
- **PR #2:** set_status robusto, marker solo-tabella, registry `kind/reference`, pulizia piani morti.
- Plan-updater `--mode update` + orchestratore `--mode am/pm` (loop chiuso).
- Scaffold clonabile + stack Pydantic AI / OpenRouter (GLM-4.6).
