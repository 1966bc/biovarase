# Manuale Utente Biovarase

**Versione:** 4.2.0
**Data:** Gennaio 2026
**Stato:** Beta

---

## Indice

1. [Introduzione](#1-introduzione)
2. [Requisiti di Sistema](#2-requisiti-di-sistema)
3. [Organizzazione Logica](#3-organizzazione-logica)
4. [Avvio e Login](#4-avvio-e-login)
5. [Gestione Anagrafica](#5-gestione-anagrafica)
6. [Operatività Quotidiana](#6-operatività-quotidiana)
   - [6.5 Validazione Giornaliera (Daily Validation)](#65-validazione-giornaliera-daily-validation)
7. [Grafici e Analisi](#7-grafici-e-analisi)
8. [Export Dati](#8-export-dati)
9. [Amministrazione](#9-amministrazione)
10. [Integrazione Strumenti](#10-integrazione-strumenti)

---

## 1. Introduzione

Biovarase è un sistema professionale per la gestione del Controllo Qualità Interno (CQI) dei laboratori clinici, conforme agli standard ISO 15189:2022.

### Funzionalità principali

- Calcolo parametri statistici: media, deviazione standard (SD), coefficiente di variazione (CV%), bias, incertezza di misura
- Valutazione delle regole di Westgard multiregola
- Generazione grafici di Levey-Jennings
- Test di Youden per confronto tra livelli
- Calcolo dell'errore totale ammissibile (TEa) e della differenza critica
- Confronto accuratezza tra workstation diverse
- Gestione multi-sito per reti di laboratori
- Audit trail completo per tracciabilità

### Architettura multi-sito

Biovarase gestisce una gerarchia organizzativa:

```
Ente (es. Regione Lazio)
  └── Sito (es. Ospedale Sant'Andrea)
        └── Laboratorio (es. Laboratorio di Biochimica)
              └── Sezione (es. Spettrometria di Massa)
                    └── Workstation (es. QTRAP 5500)
                          └── Test/Batch/Risultati
```

---

## 2. Requisiti di Sistema

### Software

- Python 3.7 o superiore
- MariaDB 10.11 o superiore
- Sistema operativo: Linux (Debian/Ubuntu) o Windows 10/11

### Dipendenze Python

- `mariadb` - Connettore database
- `openpyxl` - Export Excel
- `Pillow` - Gestione immagini
- `bcrypt` - Crittografia password

### Avvio applicazione

**Linux:**
```bash
cd /percorso/biovarase
python3 biovarase.py
```

**Windows:**
```cmd
cd C:\percorso\biovarase
py biovarase.py
```

---

## 3. Organizzazione Logica

### Concetti fondamentali

**Test:** L'analita da misurare (es. Glucosio, Creatinina, TSH).

**Metodo:** La tecnica analitica usata per eseguire il test (es. Fotometria, Chemiluminescenza, LC-MS/MS). Un test può avere più metodi associati.

**Workstation:** Lo strumento fisico su cui viene eseguito il test, identificato da numero di serie e device ID univoco.

**Controllo:** Il materiale di controllo qualità fornito da un produttore (es. Biorad, Eureka Lab Division).

**Batch (Lotto):** Una specifica produzione del controllo, con data di scadenza e valori target certificati.

**Risultato:** Il valore misurato del controllo qualità in una data specifica.

### Flusso di configurazione

Per utilizzare un test nel CQI, seguire questo ordine:

1. Creare il test e assegnargli un metodo
2. Assegnare il test-metodo alla sezione che lo esegue
3. Assegnare il test-metodo alla workstation specifica
4. Creare il controllo e i suoi batch
5. Associare i batch alla workstation e al test
6. Inserire i risultati giornalieri

---

## 4. Avvio e Login

### Primo accesso

Al primo avvio, utilizzare le credenziali predefinite:

- **Login:** adm
- **Password:** adm

Si raccomanda di cambiare immediatamente la password dopo il primo accesso.

### Cambio password

`Menu → File → Cambia Password`

Compilare i campi:
- Password attuale
- Nuova password
- Ripeti nuova password

Premere Salva. Al prossimo accesso sarà richiesta la nuova password.

### Timeout automatico

Se configurato dall'amministratore, l'applicazione si chiude automaticamente dopo un periodo di inattività. Questo comportamento è configurabile per ogni utente.

---

## 5. Gestione Anagrafica

> **Nota sui permessi:**
> - Sezioni 5.1-5.6 (Siti, Lab, Sezioni, Equipment, Test): riservate al **Livello 0** (Amministratore)
> - Sezioni 5.7-5.9 (Metodi, Assegnazioni): accessibili a **Livello 0 e 1**
> - Sezioni 5.10-5.11 (Controlli, Batch): accessibili a **Livello 0 e 1**

### 5.1 Siti

`Menu → Admin → Sites`

Un sito rappresenta una struttura ospedaliera. Ogni sito è associato a un ente di appartenenza (es. Regione, ASL, Azienda privata).

**Creazione sito:**
1. Premere Add
2. Selezionare l'ente dal menu Companies
3. Selezionare la struttura dal menu Sites
4. Premere Save

### 5.2 Laboratori

`Menu → Admin → Labs`

I laboratori sono le unità organizzative all'interno di un sito.

**Creazione laboratorio:**
1. Selezionare il sito dalla lista a sinistra con doppio click
2. Nella finestra che si apre, selezionare l'ospedale
3. Selezionare il responsabile (Manager)
4. Inserire il nome del laboratorio
5. Premere Save

### 5.3 Sezioni (Medical Fields)

`Menu → Admin → Medical Fields`

Le sezioni rappresentano le aree specialistiche del laboratorio (es. Biochimica Clinica, Spettrometria di Massa, Ematologia).

**Creazione sezione:**
1. Selezionare il laboratorio dalla lista a sinistra con doppio click
2. Selezionare il responsabile
3. Inserire il nome della sezione
4. Opzionale: attivare "Set It" per impostare questa sezione come predefinita
5. Premere Save

### 5.4 Equipments

`Menu → Admin → Equipments`

Un equipment rappresenta il modello dello strumento (es. ARCHITECT c16000, QTRAP 5500).

**Creazione equipment:**
1. Premere Add
2. Inserire il nome del modello
3. Premere Save

### 5.5 Workstations

`Menu → Edit → Workstations`

Una workstation è lo strumento fisico installato in una sezione.

**Creazione workstation:**
1. Selezionare la sezione dalla lista a sinistra con doppio click
2. Selezionare l'equipment (modello)
3. Inserire Device ID (identificativo univoco)
4. Inserire descrizione
5. Inserire numero di serie
6. Impostare il Rank (ordine di visualizzazione)
7. Premere Save

### 5.6 Test

`Menu → Admin → Tests`

**Creazione test:**
1. Premere Add
2. Selezionare la specialità (categoria per la ricerca)
3. Inserire il nome del test
4. Premere Save

### 5.7 Metodi

`Menu → Edit → Tests Methods`

**Associare un metodo a un test:**
1. Selezionare il test dalla lista a sinistra con doppio click
2. Inserire il codice (univoco)
3. Selezionare il campione (Sample)
4. Selezionare il metodo analitico
5. Selezionare l'unità di misura
6. Opzionale: attivare Mandatory per segnalare l'assenza di risultati negli export
7. Premere Save

**Obiettivi analitici (Goals):**
Per i test con dati di variabilità biologica disponibili, premere il pulsante Goals e inserire:
- CVw (variabilità intra-individuale)
- CVb (variabilità inter-individuale)
- Imp% (imprecisione desiderabile)
- Bias%
- TEa% (errore totale ammissibile)

### 5.8 Assegnazione Test a Sezioni

`Menu → Edit → Tests Sections`

1. Espandere l'albero a sinistra fino alla sezione desiderata
2. Doppio click sulla sezione
3. Nella finestra che appare, doppio click sul test da assegnare
4. Il test compare nella lista di destra (test assegnati)

### 5.9 Assegnazione Test a Workstations

`Menu → Edit → Workstations Tests Methods`

1. Espandere l'albero a sinistra fino alla workstation desiderata
2. Doppio click sulla workstation
3. Nella finestra che appare, doppio click sul test da assegnare
4. Il test compare nella lista di destra

### 5.10 Controlli

`Menu → Edit → Controls`

**Creazione controllo:**
1. Premere Add
2. Selezionare il fornitore
3. Inserire la descrizione
4. Inserire il riferimento/codice prodotto
5. Premere Save

### 5.11 Batch (Lotti)

`Menu → File → Data`

**Creazione batch:**
1. Selezionare la workstation dalla lista Sites
2. Selezionare il test dalla lista Tests
3. Doppio click sul test per aprire la finestra di inserimento
4. Selezionare il controllo
5. Selezionare la workstation
6. Inserire il numero di lotto
7. Inserire la descrizione (es. "Livello 1", "Livello 2")
8. Impostare la data di scadenza
9. Inserire il Target (valore atteso)
10. Inserire Lower e Upper (valori minimo e massimo dal foglietto illustrativo)
11. SD mode: selezionare "Computed" per calcolo automatico della SD
12. Impostare il Rank (ordine di visualizzazione)
13. Premere Save

---

## 6. Operatività Quotidiana

> **Nota sui permessi:**
> - Inserimento e modifica risultati: **Livello 0, 1 e 2**
> - Eliminazione risultati: solo **Livello 0 e 1**
> - Livello 3 (Autologin): sola visualizzazione

### 6.1 Inserimento Risultati

**Dalla finestra principale:**

1. Selezionare il Test Type dal menu a tendina in alto a sinistra
2. Selezionare il test specifico dal menu sottostante
3. Nella lista "Workstation data source" appare la lista delle workstation
4. Selezionare la workstation
5. Nella lista "Batches" appaiono i lotti associati
6. Doppio click sul batch per inserire un nuovo risultato
7. Inserire il valore misurato
8. Verificare la data (proposta quella odierna)
9. Premere Save

**Dalla finestra Data:**

`Menu → File → Data`

Stesso procedimento, con in più la possibilità di vedere tutti i batch e risultati in una vista unica.

### 6.2 Modifica Risultati

Doppio click sul risultato nella lista per aprire la finestra di modifica.

- **Utenti livello 2:** possono modificare il valore e disattivare il risultato (Status)
- **Utenti livello 0-1:** possono anche eliminare il risultato (appare il pulsante Delete)

Un risultato disattivato (Status non selezionato) viene escluso dai calcoli statistici e dai grafici.

### 6.3 Note sui Risultati

Per documentare anomalie o azioni correttive:

1. Attivare la checkbox "Notes" nella barra di stato
2. Doppio click sul risultato
3. Premere Add nella finestra Notes
4. Selezionare un'azione predefinita
5. Inserire un commento descrittivo
6. Premere Save

Le azioni predefinite si gestiscono da `Menu → Edit → Actions`.

### 6.4 Valutazione Westgard

Il sistema valuta automaticamente le regole di Westgard multiregola nell'ordine:

1. **1:3S** - Un valore supera ±3 SD → Rifiuto immediato
2. **2:2S** - Due valori consecutivi superano ±2 SD dallo stesso lato → Rifiuto
3. **R:4S** - Range di 2 valori consecutivi ≥ 4 SD → Rifiuto
4. **4:1S** - Quattro valori consecutivi superano ±1 SD dallo stesso lato → Attenzione
5. **10:X** - Dieci valori consecutivi dallo stesso lato della media → Attenzione
6. **1:2S** - Un valore supera ±2 SD → Warning

La valutazione richiede almeno 10 risultati. Con meno risultati viene mostrato "NED" (Not Enough Data).

Il risultato della valutazione appare nella scheda "Other data" sotto il grafico:
- **Accept** (verde): nessuna violazione
- **Warning** (giallo): violazione 1:2S
- **Reject** (rosso): violazione regole di rifiuto

### 6.5 Validazione Giornaliera (Daily Validation)

`Menu → File → Daily Validation`

La finestra Daily Validation permette di approvare i risultati QC prima di iniziare la routine analitica giornaliera. È progettata per i validatori che devono verificare lo stato del QC senza doversi recare fisicamente davanti ad ogni workstation.

> **Nota sui permessi:**
> - Visualizzazione: tutti i livelli
> - Validazione risultati e approvazione workstation: solo **Livello 0 e 1**

**Struttura della vista:**

La finestra mostra una TreeView gerarchica:
- **Livello 1 (Workstations):** Elenco workstation con conteggi aggregati
- **Livello 2 (Risultati):** Singoli risultati QC (visibili espandendo la workstation)

| Colonna | Workstation | Risultato |
|---------|-------------|-----------|
| Nome | Nome workstation | Nome test-campione |
| Equipment/Batch | Modello strumento | Lotto e livello |
| Time | - | Orario arrivo QC |
| Counts/Result | Tot / Pending | Valore misurato |
| Problems/Z-Score | N. problemi | Scostamento in SD |
| Status | Stato approvazione | Stato validazione |

**Codice colori:**
- **Verde:** Workstation approvata / Risultato validato
- **Giallo:** In attesa (pending)
- **Rosso:** Problemi (risultato oltre ±3 SD)

**Flusso di lavoro:**

1. Selezionare la data dal calendario
2. Premere Load per caricare i dati
3. Espandere le workstation per vedere i singoli risultati
4. Validare i risultati singolarmente (doppio click o pulsante "Validate Result")
5. Quando tutti i risultati di una workstation sono validati, approvare la workstation

**Approvazione workstation:**

Selezionare la workstation e premere "Approve Workstation". Questo:
- Valida automaticamente tutti i risultati pending
- Registra chi ha approvato e quando (audit trail)
- Cambia il colore della riga in verde

Se si approva una workstation con risultati oltre ±3 SD, viene mostrato un avviso di conferma.

**Auto-approvazione:**

Quando si valida l'ultimo risultato pending di una workstation, il sistema propone automaticamente di approvare la workstation.

**Revoca approvazione:**

Se si invalida un risultato di una workstation già approvata:
- Viene mostrato un avviso
- L'approvazione della workstation viene revocata automaticamente

**Test Mandatory:**

In alto a destra viene mostrato un indicatore:
- **"✓ All mandatory OK"** (verde): Tutti i test obbligatori sono stati eseguiti
- **"⚠ Missing mandatory: N (click)"** (rosso): N test obbligatori mancanti

Cliccando sull'indicatore rosso viene mostrata la lista dei test mancanti.

I test mandatory si configurano da `Menu → Edit → Tests Methods`, attivando il flag "Mandatory".

**Export:**

Il pulsante Export genera il report Excel Quick Data Analysis per la data selezionata.

---

## 7. Grafici e Analisi

### 7.1 Levey-Jennings

Il grafico di Levey-Jennings viene visualizzato automaticamente nella finestra principale quando si seleziona un batch con risultati.

Mostra:
- Linea centrale: Target del batch
- Linee a ±1 SD, ±2 SD, ±3 SD
- Punti dei risultati nel tempo

Per generare grafici multipli per una workstation:
`Menu → Plots → Plots`

### 7.2 Youden

`Menu → Plots → Youden`

Richiede la selezione di due batch dello stesso test sulla stessa workstation, con lo stesso numero di risultati.

Il grafico di Youden permette di valutare errori sistematici confrontando due livelli di controllo.

### 7.3 TEa (Total Error)

`Menu → Plots → Tea`

Disponibile solo per test con obiettivi analitici configurati (CVw, CVb, TEa%).

Visualizza il posizionamento del laboratorio rispetto agli obiettivi di qualità desiderabili, ottimali e minimi.

### 7.4 Accuracy (Confronto tra Workstation)

`Menu → Plots → Accuracy`

Permette di confrontare i risultati di due workstation diverse per lo stesso test.

**Creazione esperimento:**
1. Premere Experiment
2. Selezionare il test di riferimento (Test) e la sua workstation
3. Selezionare il test di confronto (Compare) e la sua workstation
4. Premere Create

**Inserimento dati:**
1. Selezionare l'esperimento
2. Premere Result
3. Inserire la coppia di valori (Test Y e Comp X)
4. Premere Save

**Calcolo:**
1. Premere Compute per calcolare il PCC (Pearson Correlation Coefficient)
2. Premere Comparisions per il grafico di regressione
3. Premere Differences per il grafico Bland-Altman

PCC > 0.970: riga verde (buona correlazione)
PCC < 0.970: riga rossa (correlazione insufficiente)

---

## 8. Export Dati

`Menu → File → Exports`

### 8.1 Analytical Goals

Esporta in Excel i dati degli obiettivi analitici per i test configurati.

### 8.2 Quick Data Analysis

Esporta tutti i risultati CQI di una data specifica per la sezione corrente.

1. Selezionare la data
2. Premere Export
3. Il file Excel viene salvato nella directory dell'applicazione

### 8.3 Counts

Esporta il conteggio dei controlli eseguiti per ogni test.

### 8.4 Control List

Esporta l'elenco dei controlli in uso con date di scadenza e fornitori.

### 8.5 Notes

Esporta le note/commenti inseriti sui risultati a partire da una data specificata.

---

## 9. Amministrazione

> **Nota:** Tutte le funzioni di questa sezione sono riservate al **Livello 0** (Amministratore).

### 9.1 Gestione Utenti

`Menu → Admin → Users`

**Creazione utente:**
1. Premere Add
2. Inserire cognome e nome
3. Inserire il Nick (username per il login)
4. Impostare il Level (livello di accesso)
5. Impostare Log out time (minuti di inattività)
6. Opzionale: attivare Activate log out
7. Premere Save

**Livelli di accesso:**

| Livello | Ruolo | Descrizione |
|---------|-------|-------------|
| 0 | Amministratore | Accesso completo a tutte le funzioni |
| 1 | Superuser | Gestione operativa completa |
| 2 | Tecnico | Operatività quotidiana |
| 3 | Autologin | Sola consultazione |

### 9.2 Matrice dei Permessi

#### Menu Admin (riservato Livello 0)

| Funzione | Liv. 0 | Liv. 1 | Liv. 2 | Liv. 3 |
|----------|--------|--------|--------|--------|
| Users | ✓ | - | - | - |
| Sites | ✓ | - | - | - |
| Labs | ✓ | - | - | - |
| Medical Fields | ✓ | - | - | - |
| Equipments | ✓ | - | - | - |
| Tests | ✓ | - | - | - |
| Suppliers | ✓ | - | - | - |
| Audit Trails | ✓ | - | - | - |

#### Menu Edit (Livello 0 e 1)

| Funzione | Liv. 0 | Liv. 1 | Liv. 2 | Liv. 3 |
|----------|--------|--------|--------|--------|
| Tests Methods | ✓ | ✓ | - | - |
| Tests Sections | ✓ | ✓ | - | - |
| Workstations | ✓ | ✓ | - | - |
| Workstations Tests Methods | ✓ | ✓ | - | - |
| Controls | ✓ | ✓ | - | - |
| Actions | ✓ | ✓ | - | - |

#### Menu File → Data (Livello 0, 1 e 2)

| Funzione | Liv. 0 | Liv. 1 | Liv. 2 | Liv. 3 |
|----------|--------|--------|--------|--------|
| Visualizza batch/risultati | ✓ | ✓ | ✓ | ✓ |
| Crea batch | ✓ | ✓ | - | - |
| Modifica batch | ✓ | ✓ | - | - |
| Inserisci risultato | ✓ | ✓ | ✓ | - |
| Modifica risultato | ✓ | ✓ | ✓ | - |
| Elimina risultato | ✓ | ✓ | - | - |
| Disattiva risultato (Status) | ✓ | ✓ | ✓ | - |

#### Menu File → Daily Validation

| Funzione | Liv. 0 | Liv. 1 | Liv. 2 | Liv. 3 |
|----------|--------|--------|--------|--------|
| Visualizza workstation/risultati | ✓ | ✓ | ✓ | ✓ |
| Valida risultato | ✓ | ✓ | - | - |
| Invalida risultato | ✓ | ✓ | - | - |
| Approva workstation | ✓ | ✓ | - | - |
| Export | ✓ | ✓ | ✓ | ✓ |

#### Finestra Principale

| Funzione | Liv. 0 | Liv. 1 | Liv. 2 | Liv. 3 |
|----------|--------|--------|--------|--------|
| Visualizza grafici | ✓ | ✓ | ✓ | ✓ |
| Inserisci risultato | ✓ | ✓ | ✓ | - |
| Modifica risultato | ✓ | ✓ | ✓ | - |
| Elimina risultato | ✓ | ✓ | - | - |
| Aggiungi note | ✓ | ✓ | ✓ | - |

#### Export e Grafici

| Funzione | Liv. 0 | Liv. 1 | Liv. 2 | Liv. 3 |
|----------|--------|--------|--------|--------|
| Tutti gli export | ✓ | ✓ | ✓ | ✓ |
| Tutti i grafici | ✓ | ✓ | ✓ | ✓ |
| Accuracy (crea esperimento) | ✓ | ✓ | - | - |
| Accuracy (inserisci dati) | ✓ | ✓ | ✓ | - |

**Reset password:**
Selezionare l'utente e premere Reset. La password viene reimpostata a "pass".

### 9.3 Audit Trails

`Menu → Admin → Audit Trails`

Mostra lo storico di tutte le modifiche a batch e risultati:
- Chi ha effettuato la modifica
- Quando
- Da quale postazione (indirizzo IP)
- Valori prima e dopo

### 9.4 Database

`Menu → File → Database`

- **Vacuum:** Ottimizza il database (per SQLite)
- **Dump:** Crea un backup in formato SQL

Il file di backup viene salvato nella directory dell'applicazione con nome nel formato `yyyymmddhhmmss.sql`.

---

## 10. Integrazione Strumenti

### 10.1 Codici Esterni

Biovarase supporta l'integrazione con sistemi esterni (middleware, LIS) attraverso codici identificativi configurabili per ogni associazione workstation-test.

`Menu → Edit → Workstations Tests Methods`

Per ogni test assegnato a una workstation è possibile configurare un "External Code" che permette il mapping con i codici utilizzati dai sistemi del fornitore (Abbott, Siemens, Roche, ecc.).

### 10.2 Formato Export AMS (Abbott)

Per l'integrazione con Abbott AMS, Biovarase può esportare i dati nel formato richiesto:
- Formato: pipe-delimited (|)
- Campi: codice test, risultato, data, batch, ecc.

La configurazione specifica dipende dall'installazione e viene concordata con il referente IT.

---

## Appendice A: Glossario

| Termine | Definizione |
|---------|-------------|
| CQI | Controllo Qualità Interno |
| SD | Standard Deviation (Deviazione Standard) |
| CV% | Coefficiente di Variazione percentuale |
| TEa | Total Error allowable (Errore Totale Ammissibile) |
| Bias | Errore sistematico |
| PCC | Pearson Correlation Coefficient |
| Batch | Lotto di produzione del controllo |
| Target | Valore atteso/certificato del controllo |

---

## Appendice B: Regole di Westgard

| Regola | Descrizione | Tipo Errore | Azione |
|--------|-------------|-------------|--------|
| 1:3S | 1 valore > ±3 SD | Random/Sistematico | Rifiuto |
| 2:2S | 2 consecutivi > ±2 SD stesso lato | Sistematico | Rifiuto |
| R:4S | Range 2 consecutivi ≥ 4 SD | Random | Rifiuto |
| 4:1S | 4 consecutivi > ±1 SD stesso lato | Sistematico | Attenzione |
| 10:X | 10 consecutivi stesso lato media | Sistematico | Attenzione |
| 1:2S | 1 valore > ±2 SD | Warning | Attenzione |

---

## Appendice C: Contatti e Supporto

Per segnalazioni e richieste di supporto:
- Repository: https://github.com/1966bc/Biovarase
- Issues: https://github.com/1966bc/Biovarase/issues

---

*Documento generato per Biovarase 4.2.0 - Gennaio 2026*
