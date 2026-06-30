# agent-lab — STATUS · aggiornato 2026-06-30

> Plancia tattica. Strategia/design: second-brain → `agent-factory.md`. Storico: `git log`.
> **Come si usa:** conversa con Claude leggendo questo file (diverge: brainstorm, calibra) →
> aggiorna via chat o `--mode update` (converge: fissa lo stato). Tienilo sotto ~50 righe;
> il "Done" vecchio si pota e resta in git.

## ▶️ Riprendi da qui
- Next: chiudere il fix di robustezza di `--mode update` e ri-testarlo end-to-end.

## 🔧 Work in progress
- Hardening `--mode update` (in un'altra sessione): `retries` sugli agenti, pulizia
  control-char nell'input, gestione errori per-piano (UnexpectedModelBehavior/ValidationError),
  coercizione `edits` quando il modello li serializza come stringa JSON.

## ⏭️ Next — deciso, da fare (prioritizzato)
1. Verificare il fix del crash con un run reale completo di `--mode update`.
2. Aggiungere `agent-lab/STATUS.md` al `plans.toml` → dogfooding (`am`/`update` su sé stesso).
3. Schedulazione launchd: `update` serale + `am` mattino.
4. Pulizia registry / `kind: reference` per i doc strategici.

## 💡 Nice-to-have / parcheggiati
- Editare anche celle di tabella ✅/⬜ (oltre ai checkbox).
- Comando `plans add <path>` per il registry.
- A/B costo-qualità GLM vs DeepSeek vs Kimi.
- "Status copilot" conversazionale dedicato (skill/prompt) — solo se il pattern chat+STATUS si rivela ripetitivo.

## ❓ Decisioni aperte
- Rinominare `plan_orchestrator/` → `plan_manager/`?
- Modelli locali (Ollama) per demo a costo zero?

## 🐞 Known issues
- #1 crash `--mode update` dopo alcuni piani — mitigazioni in corso (vedi WIP).

## ✅ Done recenti (dettaglio in git log)
- Plan-updater `--mode update` (edit ops → diff → conferma per file).
- Orchestratore `--mode am/pm` + fix parser marcatori di tabella.
- Scaffold clonabile + stack Pydantic AI / OpenRouter (GLM-4.6) validato.
