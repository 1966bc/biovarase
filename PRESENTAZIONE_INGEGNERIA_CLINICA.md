---
title: "Biovarase - Sistema di Gestione Controllo Qualità"
subtitle: |
  **Presentazione per Ingegneria Clinica**\
  **Ospedale Sant'Andrea - Università La Sapienza, Roma**
author: Giuseppe Costanzi
date: Dicembre 2025
toc: true
toc-title: Indice
---

**Versione:** 4.2 Professional Edition\
**Contatto:** gcostanzi@ospedalesantandrea.it

---

## 1. Preludio

**Biovarase** è un sistema software professionale per la gestione del Controllo 
Qualità (CQ) di laboratorio, progettato per automatizzare il monitoraggio della 
qualità analitica secondo gli standard **ISO 15189:2022**.

### Caratteristiche Principali

- Implementazione completa delle **regole Westgard multirule**
- Grafici **Levey-Jennings** in tempo reale
- Calcolo automatico di **bias, incertezza di misura, sigma metrics**
- Architettura **multi-sito, multi-laboratorio, multi-sezione**
- Integrazione con analizzatori **Abbott Alinity** (in corso)
- **89 test automatizzati** con 100% pass rate

### Valore per il Sant'Andrea

| Aspetto | Beneficio |
|---------|-----------|
| **Costo** | Zero costi di licenza (sviluppo interno) |
| **Conformità** | ISO 15189:2022 compliant |
| **Personalizzazione** | Adattabile alle esigenze specifiche |
| **Integrazione** | Compatibile con infrastruttura Abbott esistente |
| **Supporto** | Sviluppatore interno al laboratorio |

---

## 2. Contesto e Problema

### Situazione Attuale nei Laboratori

I laboratori di analisi cliniche devono:

1. **Monitorare la qualità analitica** di ogni analizzatore
2. **Validare i risultati CQ** secondo regole statistiche (Westgard)
3. **Documentare la conformità** per accreditamenti ISO 15189
4. **Tracciare lotti di controllo** e reagenti
5. **Generare report** per audit e ispezioni

### Problemi delle Soluzioni Esistenti

| Soluzione | Problema |
|-----------|----------|
| **Unity (BioRad)** | Costi elevati (€20-70K/anno), vendor lock-in |
| **Fogli Excel** | Errori manuali, nessuna automazione, non conforme |
| **Software proprietari** | Costosi, chiusi, difficili da personalizzare |

### Soluzione Proposta

**Biovarase** elimina questi problemi offrendo:
- Zero costi di licenza
- Automazione completa del workflow CQ
- Personalizzazione illimitata
- Integrazione diretta con Abbott

---

## 3. Architettura Tecnica

### Stack Tecnologico

| Componente | Tecnologia | Versione |
|------------|------------|----------|
| **Linguaggio** | Python | 3.7+ |
| **GUI** | Tkinter (ttk themed) | Nativo |
| **Database** | MariaDB | 10.11+ |
| **Crittografia** | Fernet (AES-128-CBC) | cryptography 38+ |
| **Hashing Password** | bcrypt | Cost factor 12 |
| **Test Framework** | pytest | 7.2+ |

\newpage

### Diagramma Architetturale

```
┌─────────────────────────────────────────────────────────────┐
│                    LIVELLO PRESENTAZIONE                     │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │  Login  │ │  Main   │ │ Batches │ │ Results │  ...      │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘           │
│       │           │           │           │                  │
│       └───────────┴───────────┴───────────┘                  │
│                           │                                  │
└───────────────────────────┼──────────────────────────────────┘
                            │
┌───────────────────────────┼──────────────────────────────────┐
│                    LIVELLO BUSINESS                          │
│                           │                                  │
│  ┌────────────────────────▼────────────────────────────┐    │
│  │                      ENGINE                          │    │
│  │  ┌─────────┐ ┌────────────┐ ┌──────────┐           │    │
│  │  │   QC    │ │ Westgards  │ │  Tools   │  ...      │    │
│  │  │ (stats) │ │  (rules)   │ │ (utils)  │           │    │
│  │  └─────────┘ └────────────┘ └──────────┘           │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
│  ┌────────────────────────▼────────────────────────────┐    │
│  │                   CONTROLLER                         │    │
│  │            (SQL Builder, Domain Logic)               │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
└───────────────────────────┼──────────────────────────────────┘
                            │
┌───────────────────────────┼──────────────────────────────────┐
│                    LIVELLO DATI                              │
│                           │                                  │
│  ┌────────────────────────▼────────────────────────────┐    │
│  │                      DBMS                            │    │
│  │         (Connection, Query Execution)                │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
│  ┌────────────────────────▼────────────────────────────┐    │
│  │                    MariaDB                           │    │
│  │              (Database Server)                       │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

\newpage

### Schema Database (Semplificato)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    SITES    │────<│    LABS     │────<│  SECTIONS   │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                    ┌──────────────────────────┤
                    │                          │
              ┌─────▼─────┐            ┌───────▼───────┐
              │WORKSTATIONS│            │TEST_METHODS   │
              └─────┬─────┘            └───────┬───────┘
                    │                          │
                    │    ┌─────────────┐       │
                    └───>│   BATCHES   │<──────┘
                         └──────┬──────┘
                                │
                         ┌──────▼──────┐
                         │   RESULTS   │
                         └─────────────┘
```

### Sicurezza

| Misura | Implementazione |
|--------|-----------------|
| **Autenticazione** | bcrypt (cost factor 12) |
| **Crittografia config** | AES-128-CBC + HMAC-SHA256 |
| **SQL Injection** | Query parametrizzate (100%) |
| **Hardware Lock** | Credenziali legate a MAC + machine-id |
| **Audit Trail** | Log completo operazioni |
| **Ruoli Utente** | Admin, Superuser, Technician, Viewer |

---

## 4. Funzionalità

### 4.1 Gestione Controllo Qualità

#### Regole Westgard Implementate

| Regola | Descrizione | Tipo Errore |
|--------|-------------|-------------|
| **1:3S** | 1 valore > 3 SD | Random (reiezione) |
| **2:2S** | 2 valori consecutivi > 2 SD stesso lato | Sistematico |
| **R:4S** | Range di 2 valori ≥ 4 SD | Random |
| **4:1S** | 4 valori consecutivi > 1 SD stesso lato | Trending |
| **10:X** | 10 valori consecutivi stesso lato della media | Bias persistente |
| **1:2S** | 1 valore > 2 SD | Warning |

#### Calcoli Statistici (ISO 15189:2022)

- **Media** (Mean)
- **Deviazione Standard** (SD) con ddof configurabile
- **Coefficiente di Variazione** (CV%)
- **Bias** (%)
- **Errore Totale** (TE = Bias + z × CV)
- **Incertezza di Misura** (ISO/TS 20914:2019)
- **Sigma Metrics** (indicatore performance)

#### Grafici

- **Levey-Jennings**: Trend temporale con limiti di controllo
- **Youden Plot**: Confronto inter-laboratorio
- **Bias Chart**: Visualizzazione scostamento da target
- **Istogrammi**: Distribuzione frequenze

### 4.2 Gestione Batch e Lotti

- Tracciabilità completa lotti CQ
- Date di scadenza con alert
- Assegnazione a workstation
- Target e SD configurabili per lotto
- Storico completo modifiche

### 4.3 Validazione Risultati

- Workflow di validazione strutturato
- Firma elettronica validatore
- Storico validazioni (audit trail)
- Alert per violazioni Westgard
- Report giornalieri automatici

\newpage

### 4.4 Multi-Sito

```
OSPEDALE SANT'ANDREA
    │
    ├── LABORATORIO ANALISI
    │       │
    │       ├── Chimica Clinica
    │       │       ├── Alinity 1
    │       │       └── Alinity 2
    │       │
    │       ├── Spettrometria di Massa
    │       │       └── Mass Spec 1
    │       │
    │       └── Ematologia
    │               └── ...
    │
    └── [Altri Laboratori]
```

### 4.5 Import/Export

| Formato | Import | Export |
|---------|--------|--------|
| **Excel (.xlsx)** | SI | SI |
| **CSV** | SI | SI |
| **Abbott QC Files** | SI (in sviluppo) | - |
| **PDF Report** | - | SI |

---

## 5. Partnership Abbott - Incubatore Tecnologico

### Il Ruolo di Abbott

La collaborazione con **Abbott Diagnostics Italia** rappresenta un **incubatore tecnologico** per il progetto Biovarase:

| Aspetto | Valore |
|---------|--------|
| **Accesso ai dati** | Abbott fornisce specifiche formato file QC e accesso alla cartella condivisa |
| **Test sul campo** | Possibilità di testare l'integrazione con analizzatori reali in produzione |
| **Know-how** | Apprendimento delle best practice di integrazione strumentale |
| **Validazione** | Il successo dell'integrazione valida l'architettura per altri vendor |

### Visione Strategica: Scalabilità Regionale

Essendo il **Sant'Andrea un'Azienda Ospedaliero-Universitaria**, il successo del progetto potrebbe avere ricadute importanti:

```
FASE 1 (Attuale)                    FASE 2 (Futura)
─────────────────                   ──────────────────────────────────────

  Sant'Andrea                         Server Cloud Regionale
       │                                      │
       ▼                              ┌───────┼───────┐
  ┌─────────┐                         │       │       │
  │Biovarase│                         ▼       ▼       ▼
  │ (locale)│                    Ospedale Ospedale Ospedale
  └─────────┘                       A       B       C
                                    │       │       │
                                    └───────┴───────┘
                                            │
                                            ▼
                                    ┌──────────────┐
                                    │  Dashboard   │
                                    │  Regionale   │
                                    │  Comparativa │
                                    └──────────────┘
```

**Scenario Regione Lazio** (potenziale futuro):

| Parametro | Stima |
|-----------|-------|
| Ospedali pubblici principali | ~20-25 |
| Strutture ASL con laboratorio | ~50+ |
| Costo Unity per struttura | €30-50K/anno |
| **Risparmio potenziale** | **€1-2.5M/anno** |

**Nota**: Il database Biovarase è già progettato con architettura multi-sito 
(tabelle `sites` → `labs` → `sections`), predisposta per questa evoluzione.

\newpage

### Architettura Integrazione Abbott (File-Based)

```
┌─────────────────────┐
│  Abbott Alinity     │
│  Analyzers          │
└──────────┬──────────┘
           │
           │ QC Data Files (CSV/TXT)
           ▼
┌─────────────────────┐
│  Shared Folder      │
│  (SMB/NFS mount)    │
└──────────┬──────────┘
           │
           │ File Monitoring (~10 sec)
           ▼
┌─────────────────────┐
│  Biovarase Poller   │
│  (Python daemon)    │
└──────────┬──────────┘
           │
           │ Parse & Validate
           ▼
┌─────────────────────┐
│  MariaDB Import     │
│  (automated)        │
└──────────┬──────────┘
           │
           │ Real-time Processing
           ▼
┌─────────────────────┐
│  Westgard Rules     │
│  + Charts           │
└─────────────────────┘
```

### Status Integrazione

| Componente | Status | Note |
|------------|--------|------|
| Formato file Abbott | [IN ATTESA] | Specifiche da Abbott IT |
| Mount cartella condivisa | [IN ATTESA] | Credenziali da Abbott |
| Parser file | [DA FARE] | 2-3 giorni lavoro |
| Poller automatico | [DA FARE] | 1-2 giorni lavoro |
| Test integrazione | [DA FARE] | Post-sviluppo |

### Timeline Prevista

| Settimana | Attività |
|-----------|----------|
| **1** | Ricezione formato file e credenziali |
| **2** | Sviluppo parser e poller |
| **3** | Test integrazione con dati reali |
| **4** | Go-live pilot (2 Alinity) |

---

## 6. Requisiti Tecnici

### Server (GIÀ OPERATIVO)

Il server per Biovarase è già installato e operativo presso il Laboratorio Analisi:

| Componente | Configurazione Attuale |
|------------|------------------------|
| **Indirizzo IP** | 172.16.149.100 |
| **Sistema Operativo** | Debian 10 |
| **Database** | MariaDB |
| **Python** | 3.7+ |
| **Applicazione** | Biovarase 4.2 in produzione |

**Nota**: Non sono richieste nuove installazioni hardware o software lato server.

### Client (Workstation)

| Componente | Requisito |
|------------|-----------|
| **OS** | Windows 10/11 |
| **Network** | Accesso al server MariaDB (porta 3306) |
| **Display** | 1280x720 minimo |
| **Installazione** | Singolo eseguibile (`biovarase.exe`) |

**Compilazione**: Il client è compilato in **codice nativo C** tramite **Nuitka**, 
una suite di compilazione che converte Python in eseguibile standalone.

**Vantaggi della compilazione Nuitka**:
- **Nessuna installazione Python** richiesta sui client
- **Singolo file eseguibile** (~50 MB) facile da distribuire
- **Performance migliorate** rispetto a Python interpretato
- **Protezione del codice sorgente**

### Porte di Rete

| Porta | Servizio | Direzione |
|-------|----------|-----------|
| **3306** | MariaDB | Client → Server |
| **445** | SMB (cartella condivisa) | Server → Abbott |

### Configurazione Rete Richiesta

Per l'integrazione con Abbott è necessario abilitare la comunicazione tra:

| Ruolo | Indirizzo IP | Descrizione |
|-------|--------------|-------------|
| **Server Laboratorio** | 172.16.149.100 | Server Biovarase |
| **Server Abbott** | 172.16.145.11 | Cartella condivisa QC |

**Requisito firewall**: Abilitare porta **445/TCP (SMB)** per montaggio CIFS della share.

```
┌─────────────────────┐         porta 445/TCP         ┌─────────────────────┐
│  Server Laboratorio │ ──────────────────────────── │    Server Abbott    │
│   172.16.149.100    │           (SMB/CIFS)          │   172.16.145.11     │
│                     │                               │                     │
│   - Biovarase       │         ◄─────────────        │   - Cartella QC     │
│   - Poller Python   │         File QC Abbott        │   - Dati Alinity    │
└─────────────────────┘                               └─────────────────────┘
```

**Nota**: La ditta Abbott ha già predisposto una cartella condivisa dedicata ai 
file di controllo qualità, accessibile per il nostro utente e destinata ai test 
di integrazione.

---

## 7. Sicurezza e Conformità

### Conformità Normativa

| Standard | Status | Note |
|----------|--------|------|
| **ISO 15189:2022** | Conforme | Requisiti CQ implementati |
| **ISO/TS 20914:2019** | Conforme | Calcolo incertezza misura |
| **GDPR** | Conforme | Nessun dato paziente trattato |
| **FDA 21 CFR Part 11** | Parziale | Audit trail presente, e-signature in roadmap |

### Misure di Sicurezza Implementate

1. **Autenticazione**
   - Password hashate con bcrypt (cost factor 12)
   - Nessuna password in chiaro nel sistema
   - Blocco dopo N tentativi falliti (configurabile)

2. **Autorizzazione**
   - 4 ruoli gerarchici (Admin → Viewer)
   - Permessi granulari per operazione
   - Logging accessi

3. **Crittografia**
   - Credenziali DB crittografate (AES-128)
   - Chiave derivata da hardware (non trasferibile)
   - PBKDF2 con 100.000 iterazioni

4. **Database**
   - Query parametrizzate (zero SQL injection)
   - Validazione identificatori SQL (regex)
   - Constraint di integrità referenziale

5. **Audit Trail**
   - Log completo in `log.txt`
   - Rotazione automatica (10 MB, 5 file)
   - Tracciamento: utente, azione, timestamp, IP

### Backup e Disaster Recovery

| Componente | Strategia |
|------------|-----------|
| **Database** | mysqldump giornaliero |
| **Configurazione** | Backup file .enc |
| **Log** | Rotazione automatica + archivio |
| **Codice** | Versioning (backup manuale) |

---

## 8. Test e Qualità

### Suite di Test Automatizzati

| Modulo | Test | Copertura | Status |
|--------|------|-----------|--------|
| **Security** | 27 | 100% | OK |
| **Westgard Rules** | 29 | 100% | OK |
| **QC Statistics** | 33 | 100% | OK |
| **TOTALE** | **89** | **100%** | **OK** |

### Esecuzione Test

```bash
# Attivare virtual environment
source venv/bin/activate

# Eseguire tutti i test
pytest tests/test_security.py tests/test_westgards.py tests/test_qc.py -v

# Output atteso: 89 passed
```

### Categorie Test

- **@pytest.mark.critical** - Sicurezza medica
- **@pytest.mark.security** - Crittografia e hashing
- **@pytest.mark.westgard** - Regole Westgard
- **@pytest.mark.qc** - Calcoli statistici

---

## 9. Deployment Sant'Andrea

### Infrastruttura Esistente

| Componente | Dettagli | Status |
|------------|----------|--------|
| **Server** | 172.16.149.100 | Operativo |
| **Sistema Operativo** | Debian 10 | Installato |
| **Database** | MariaDB | Operativo |
| **Applicazione** | Biovarase 4.2 | In produzione |

### Status Attuale

| Aspetto | Status |
|---------|--------|
| **Deployment** | Operativo |
| **Reparto** | Spettrometria di Massa + Laboratorio Analisi |
| **Utenti** | ~30 (tecnici, biologi, medici) |
| **Sponsor** | Primario Laboratorio Analisi |
| **Import dati** | Manuale (automatico in sviluppo) |

### Prossimi Passi

1. **Settimana 1-2**: Integrazione Abbott Alinity
2. **Settimana 3-4**: Pilot automatico (2 analizzatori)
3. **Mese 2**: Estensione a tutti gli analizzatori
4. **Mese 3**: Valutazione e ottimizzazione

### Requisiti per Completare Integrazione

| Requisito | Responsabile | Status |
|-----------|--------------|--------|
| Formato file QC Abbott | Abbott IT | In attesa |
| Credenziali cartella condivisa | Abbott IT | In attesa |
| Mount su server Linux | IT Ospedale | Post-credenziali |
| Sviluppo poller | Giuseppe | Post-formato file |
| Test integrazione | Giuseppe + Laboratorio | Post-sviluppo |

---

## 10. Supporto e Manutenzione

### Canali di Supporto

| Tipo | Contatto |
|------|----------|
| **Email** | gcostanzi@ospedalesantandrea.it |
| **Presenza** | Laboratorio Sant'Andrea |
| **Documentazione** | Inclusa nel software |

### Manutenzione

| Attività | Frequenza |
|----------|-----------|
| Backup database | Giornaliero (automatico) |
| Aggiornamenti software | Mensile (o su richiesta) |
| Log rotation | Automatico |
| Security patches | Immediato (se critico) |

### SLA Proposto (Informale)

| Priorità | Tempo Risposta | Tempo Risoluzione |
|----------|----------------|-------------------|
| **Critico** (sistema down) | 4 ore | 24 ore |
| **Alto** (funzionalità bloccata) | 8 ore | 48 ore |
| **Medio** (problema parziale) | 24 ore | 1 settimana |
| **Basso** (enhancement) | 1 settimana | Da pianificare |

---

## 11. Conclusioni

### Vantaggi Chiave

1. **Zero costi di licenza** vs soluzioni commerciali (€20-70K/anno)
2. **Conformità ISO 15189:2022** out-of-the-box
3. **Personalizzazione illimitata** per esigenze specifiche
4. **Supporto locale** (sviluppatore in sede)
5. **Integrazione Abbott nativa** (in sviluppo)
6. **89 test automatizzati** per affidabilità

### Prossimi Passi Richiesti

| Azione | Responsabile | Priorità |
|--------|--------------|----------|
| Approvazione progetto | Ingegneria Clinica | Alta |
| Fornitura credenziali Abbott | Abbott IT | Alta |
| Allocazione risorse server | IT Ospedale | Media |
| Pianificazione go-live | Tutti | Media |

### Contatti

**Sviluppatore**: Giuseppe Costanzi\
**Email**: gcostanzi@ospedalesantandrea.it\
**Laboratorio**: Azienda Ospedaliero-Universitaria Sant'Andrea, Roma\
UOC Biochimica e Biologia Molecolare Clinica - Sezione Spettrometria di Massa

---

## Appendici

### A. Glossario

| Termine | Definizione |
|---------|-------------|
| **CQ** | Controllo Qualità |
| **SD** | Deviazione Standard |
| **CV** | Coefficiente di Variazione |
| **Westgard** | Sistema di regole statistiche per CQ |
| **Levey-Jennings** | Grafico di controllo temporale |
| **ISO 15189** | Standard internazionale per laboratori medici |

\newpage

### B. Riferimenti

- ISO 15189:2022 - Medical laboratories - Requirements for quality and competence
- ISO/TS 20914:2019 - Medical laboratories - Practical guidance for estimation of measurement uncertainty
- Westgard JO. Basic QC Practices, 4th Edition. 2016
- CLSI EP05-A3 - Evaluation of Precision Performance

---

**Documento preparato per Ingegneria Clinica - Ospedale Sant'Andrea**

*Versione 1.0 - Dicembre 2025*
