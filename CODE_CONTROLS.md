# CODE_CONTROLS.md

Checklist per la revisione del codice di Biovarase. Dare in pasto a Claude quando serve un controllo.

---

## 1. Codice Morto e Duplicati

- [ ] Funzioni/metodi mai chiamati
- [ ] Import non utilizzati
- [ ] Variabili assegnate ma mai lette
- [ ] Attributi di classe non usati
- [ ] Codice commentato da rimuovere
- [ ] Metodi duplicati tra mixin/classi

**Comando:** `pylint --disable=all --enable=W0611,W0612,W0613,W0614 *.py`

---

## 2. Sicurezza (Critico per dati medici)

- [ ] SQL injection: tutte le query usano parametri `?`
- [ ] Nessuna concatenazione di stringhe SQL
- [ ] Password hashate con bcrypt (cost factor >= 12)
- [ ] File sensibili in `.gitignore` (.env, credentials, config.enc)
- [ ] Validazione input utente
- [ ] Controlli RBAC su tutte le operazioni sensibili

**Pattern corretto:**
```python
self.engine.read(True, "SELECT * FROM users WHERE user_id = ?", (user_id,))
```

---

## 3. Accesso ai Dati (Multi-site)

- [ ] Query filtrate per `site_id`, `lab_id`, `section_id` dove necessario
- [ ] Rispetto gerarchia: Site → Lab → Section → Workstation → Batch → Result
- [ ] Controllo ruoli prima di operazioni:
  - `can_validate_qc()` per Admin/Superuser
  - `can_configure_system()` per Admin only
  - `is_read_only()` per bloccare Autologin

---

## 4. Gestione Errori

- [ ] Nessun `except:` generico (bare except)
- [ ] Tutti gli errori loggati via `self.on_log()`
- [ ] Eccezioni specifiche catturate
- [ ] Messaggi di errore user-friendly (non stack trace)

**Pattern corretto:**
```python
try:
    # operation
except (SpecificError, AnotherError) as e:
    self.on_log(inspect.stack()[0][3], sys.exc_info()[1], sys.exc_info()[0], sys.modules[__name__])
```

---

## 5. Accesso Database

- [ ] Solo accesso dizionario: `row["field"]` mai `row[0]`
- [ ] Connessione gestita da Engine (singleton)
- [ ] Transazioni per operazioni multiple
- [ ] Cursori chiusi correttamente

---

## 6. Pattern GUI (Tkinter)

- [ ] Master windows usano `ParentView` (singleton)
- [ ] Editor dialogs usano `ChildView`
- [ ] `on_cancel()` chiama `super().on_cancel()`
- [ ] Observer pattern per aggiornamenti cross-window
- [ ] Nessuna navigazione diretta `self.parent.parent`
- [ ] `on_open()` mai chiamato dentro `__init__()`

---

## 7. Internazionalizzazione (i18n)

- [ ] Tutte le stringhe UI wrapped con `_()`
- [ ] Traduzioni presenti in `i18n.py`
- [ ] Nessuna stringa hardcoded visibile all'utente

**Cerca stringhe non tradotte:**
```bash
grep -rn "text=" views/ | grep -v "_("
grep -rn "messagebox" views/ | grep -v "_("
```

---

## 8. Calcoli QC (Critici per dominio medico)

- [ ] Formule statistiche corrette (mean, SD, CV, bias)
- [ ] Westgard rules nell'ordine corretto (1:3S → 2:2S → R:4S → 4:1S → 10:X → 1:2S)
- [ ] Minimo 10 valori per valutazione Westgard
- [ ] DDOF (degrees of freedom) gestito correttamente
- [ ] Uncertainty calculation conforme ISO/TS 20914

---

## 9. Performance

- [ ] Query con LIMIT dove appropriato
- [ ] Nessun SELECT * in produzione (solo campi necessari)
- [ ] Index su campi filtrati frequentemente
- [ ] Nessun loop N+1 (query dentro cicli)

---

## 10. Consistenza Codice

- [ ] Naming convention: snake_case per funzioni/variabili, PascalCase per classi
- [ ] Metodi UI chiamati `_build_ui()` (non `init_ui`)
- [ ] Docstrings per metodi pubblici
- [ ] Type hints dove possibile
- [ ] PEP 8 compliance

---

## 11. Test

- [ ] Test per calcoli QC critici (`@pytest.mark.critical`)
- [ ] Test per regole Westgard (`@pytest.mark.westgard`)
- [ ] Test per sicurezza (`@pytest.mark.security`)
- [ ] Coverage minima su moduli critici

**Comandi:**
```bash
pytest tests/ -v
pytest -m critical -v
pytest --cov=. --cov-report=term
```

---

## 12. Documentazione

- [ ] CLAUDE.md aggiornato con modifiche significative
- [ ] Commenti solo dove la logica non è ovvia
- [ ] TODO/FIXME con contesto sufficiente

---

## Come Usare

Dire a Claude:
- "Esegui controllo X" (dove X = numero sezione)
- "Controlla sicurezza" (sezione 2)
- "Controlla tutto" (tutte le sezioni)
- "Controlla file Y" (applica checklist a file specifico)

---

*Ultimo aggiornamento: Gennaio 2026*
