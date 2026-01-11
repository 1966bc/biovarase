# Manuale di Programmazione

> Raccolta di concetti appresi durante lo sviluppo di Biovarase.
> Questo documento cresce con ogni sessione di lavoro.

---

## Indice

1. [Edge Cases (Casi Limite)](#edge-cases-casi-limite)
2. [Design Patterns](#design-patterns)
   - [Observer Pattern](#observer-pattern)
   - [Singleton Pattern](#singleton-pattern)
   - [Mixin Pattern](#mixin-pattern)
3. [Testing](#testing)
   - [Unit Test vs Integration Test](#unit-test-vs-integration-test)
   - [Test Coverage](#test-coverage)
   - [Mock e Stub](#mock-e-stub)
4. [Sicurezza](#sicurezza)
   - [SQL Injection](#sql-injection)
   - [Bcrypt e Hashing](#bcrypt-e-hashing)
5. [Architettura](#architettura)
   - [Separazione delle Responsabilità](#separazione-delle-responsabilità)
   - [Multi-Tenant](#multi-tenant)
6. [Python Avanzato](#python-avanzato)
   - [Decoratori](#decoratori)
   - [Context Manager](#context-manager)
   - [hasattr e Introspezione](#hasattr-e-introspezione)
7. [Database](#database)
   - [Gestione delle Transazioni](#gestione-delle-transazioni)
8. [Concorrenza](#concorrenza)
   - [Threading e Race Conditions](#threading-e-race-conditions)
   - [Queue per Comunicazione Thread](#queue-per-comunicazione-thread)

---

## Edge Cases (Casi Limite)

### Cosa sono

Gli **edge cases** sono situazioni che si verificano ai confini delle condizioni normali di funzionamento. Sono i casi "estremi" che spesso non vengono considerati durante lo sviluppo ma che possono causare crash o comportamenti inattesi.

Il termine viene dall'inglese "edge" (bordo) - sono i casi che stanno sul bordo, al limite delle condizioni previste.

### Categorie comuni

#### 1. Valori numerici estremi

| Edge Case | Problema | Soluzione |
|-----------|----------|-----------|
| Valore = 0 | Divisione per zero | Controllo preventivo |
| Valore negativo | Calcoli non previsti | Validazione input |
| Valore molto grande | Overflow | Limiti di range |
| NaN o Infinity | Propagazione errore | Controlli matematici |

**Esempio in Biovarase - Calcolo CV:**
```python
def get_cv(self, series):
    mean = self.get_mean(series)
    sd = self.get_sd(series)

    # Edge case: media = 0 causerebbe divisione per zero
    if mean == 0:
        return None

    return round((sd / mean) * 100, 2)
```

#### 2. Collezioni vuote o con un solo elemento

| Edge Case | Problema | Soluzione |
|-----------|----------|-----------|
| Lista vuota `[]` | Nessun elemento su cui operare | Return valore default |
| Un solo elemento | SD non calcolabile | Gestione speciale |
| Esattamente N elementi | Soglie minime | Controllo len() |

**Esempio in Biovarase - Westgard richiede minimo 10 valori:**
```python
def get_westgard_violation_rule(self, target, sd, series, ...):
    # Edge case: serie troppo corta per Westgard
    if len(series) < 10:
        return "NED"  # Not Enough Data

    # Procedi con valutazione regole...
```

#### 3. Stringhe problematiche

| Edge Case | Problema | Soluzione |
|-----------|----------|-----------|
| Stringa vuota `""` | Campo obbligatorio vuoto | Validazione |
| Solo spazi `"   "` | Sembra vuota ma non lo è | `.strip()` |
| Caratteri speciali | `β-HCG`, `Vitamina B₁₂` | Encoding UTF-8 |
| Lunghezza eccessiva | Supera limite DB | Troncamento |

**Esempio in Biovarase - Validazione campi:**
```python
# Edge case: nickname con solo spazi
nickname = nickname.strip()
if not nickname:
    raise ValueError("Nickname obbligatorio")
```

#### 4. Date ai limiti

| Edge Case | Problema | Soluzione |
|-----------|----------|-----------|
| Oggi (0 giorni) | Scaduto o no? | Definire regola chiara |
| Data futura | Errore inserimento? | Validazione |
| 29 febbraio | Esiste solo anni bisestili | Usare librerie date |
| Fuso orario | Mezzanotte dove? | UTC o timezone esplicito |

**Esempio in Biovarase - Scadenza lotti:**
```python
def _highlight_expiration(self, ws, row_idx, expiration_date, received_date, ...):
    days = (expiration_date - received_date).days

    if days <= 0:      # Edge case: scaduto o scade oggi
        color = "red"
    elif days <= 15:   # Edge case: vicino a scadenza
        color = "yellow"
```

#### 5. Concorrenza e stato

| Edge Case | Problema | Soluzione |
|-----------|----------|-----------|
| Due utenti stesso record | Chi vince? | Lock o versioning |
| Operazione interrotta | Stato inconsistente | Transazioni |
| Connessione persa | Dati non salvati | Retry + feedback |

### Perché sono difficili da trovare

1. **Non ci pensi** - Sviluppi pensando al caso normale
2. **Rari** - Capitano 1 volta su 1000, ma quando capitano...
3. **Combinazioni** - SD=0 AND risultato negativo AND lotto scaduto
4. **Dipendono dai dati** - Solo dati reali li rivelano

### Strategia per gestirli

```
1. ANTICIPA - Pensa "cosa succede se...?" durante lo sviluppo
2. VALIDA - Controlla gli input prima di usarli
3. TESTA - Scrivi test specifici per edge cases
4. MONITORA - Log e alert per casi anomali in produzione
5. DOCUMENTA - Scrivi cosa succede nei casi limite
```

---

## Design Patterns

I **design patterns** (schemi di progettazione) sono soluzioni riutilizzabili a problemi comuni nella progettazione software. Non sono codice pronto, ma template che puoi adattare.

### Observer Pattern

#### Problema che risolve

Quando un oggetto cambia stato, altri oggetti devono essere notificati e aggiornarsi automaticamente, **senza che l'oggetto sorgente debba conoscerli direttamente**.

#### Esempio pratico

Immagina un giornale (Publisher) e i suoi abbonati (Subscribers):
- Il giornale non sa chi sono gli abbonati
- Gli abbonati si iscrivono/disiscrivono liberamente
- Quando esce un nuovo numero, tutti gli abbonati vengono notificati

#### Implementazione in Biovarase

```python
# In engine.py - Il "Publisher"
class Engine:
    def __init__(self):
        self._subscribers = {}  # evento -> [callbacks]

    def subscribe(self, event: str, callback) -> None:
        """Un subscriber si registra per un evento."""
        if event not in self._subscribers:
            self._subscribers[event] = []
        if callback not in self._subscribers[event]:
            self._subscribers[event].append(callback)

    def unsubscribe(self, event: str, callback) -> None:
        """Un subscriber si cancella."""
        if event in self._subscribers:
            try:
                self._subscribers[event].remove(callback)
            except ValueError:
                pass

    def notify(self, event: str, data=None) -> None:
        """Notifica tutti i subscribers di un evento."""
        for callback in self._subscribers.get(event, []):
            try:
                callback(data)
            except Exception:
                pass  # Un subscriber fallito non blocca gli altri
```

```python
# In una View - Il "Subscriber"
class BatchesView:
    def __init__(self, parent):
        # Mi iscrivo all'evento "batch_changed"
        self.engine.subscribe("batch_changed", self.on_batch_changed)

    def on_batch_changed(self, batch_id):
        """Callback chiamato quando un batch cambia."""
        self.refresh_list()

    def on_cancel(self):
        # IMPORTANTE: disiscriversi prima di chiudere!
        self.engine.unsubscribe("batch_changed", self.on_batch_changed)
        self.destroy()
```

```python
# In un Editor - Chi scatena l'evento
class BatchEditor:
    def on_save(self):
        # Salvo il batch...
        self.engine.write(sql, args)

        # Notifico tutti che il batch è cambiato
        self.engine.notify("batch_changed", batch_id)
```

#### Vantaggi

| Vantaggio | Spiegazione |
|-----------|-------------|
| **Disaccoppiamento** | L'editor non sa chi sta ascoltando |
| **Flessibilità** | Aggiungi/rimuovi observers senza modificare il publisher |
| **Scalabilità** | N finestre possono reagire allo stesso evento |

#### Eventi in Biovarase

```python
# Eventi disponibili
"batch_changed"      # Un batch è stato modificato
"result_changed"     # Un risultato QC è cambiato
"section_changed"    # L'utente ha cambiato sezione
"supplier_changed"   # Un fornitore è stato modificato
"equipment_changed"  # Un'attrezzatura è stata modificata
"test_method_changed" # Un metodo di test è cambiato
```

#### Attenzione: Memory Leaks

Se dimentichi di fare `unsubscribe()`, il callback rimane in memoria anche dopo che la finestra è chiusa:

```python
# SBAGLIATO - Memory leak!
def on_cancel(self):
    self.destroy()  # La finestra si chiude ma il callback resta

# CORRETTO
def on_cancel(self):
    self.engine.unsubscribe("batch_changed", self.on_batch_changed)
    self.destroy()
```

---

### Singleton Pattern

#### Problema che risolve

Garantire che una classe abbia **una sola istanza** in tutta l'applicazione, e fornire un punto di accesso globale a essa.

#### Quando usarlo

- Connessione database (una sola connessione condivisa)
- Configurazione applicazione
- Logger
- Cache

#### Implementazione in Biovarase

```python
# engine.py
class _EngineMeta(type):
    """Metaclass che garantisce una sola istanza di Engine."""
    _instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            # Prima chiamata: crea l'istanza
            cls._instance = super().__call__(*args, **kwargs)
        # Chiamate successive: ritorna l'istanza esistente
        return cls._instance


class Engine(DBMS, Controller, QC, Westgards, ..., metaclass=_EngineMeta):
    pass
```

```python
# Uso - ovunque nell'applicazione
engine1 = Engine("user", "pass", "db")
engine2 = Engine("altro", "altro", "altro")

# engine1 e engine2 sono lo STESSO oggetto!
print(engine1 is engine2)  # True
```

#### Vantaggi e Svantaggi

| Vantaggi | Svantaggi |
|----------|-----------|
| Una sola connessione DB | Difficile da testare (stato globale) |
| Stato condiviso facile | Nasconde le dipendenze |
| Accesso globale | Può diventare un "God Object" |

---

### Mixin Pattern

#### Problema che risolve

Aggiungere funzionalità a una classe senza usare l'ereditarietà tradizionale. Permette di **comporre** comportamenti da più sorgenti.

#### Esempio in Biovarase

```python
# Ogni mixin fornisce un "pezzo" di funzionalità
class DBMS:
    """Connessione e query database."""
    def read(self, ...): ...
    def write(self, ...): ...

class Controller:
    """Logica di dominio e SQL builders."""
    def get_selected(self, ...): ...
    def on_login(self, ...): ...

class QC:
    """Calcoli statistici."""
    def get_mean(self, ...): ...
    def get_sd(self, ...): ...
    def get_cv(self, ...): ...

class Westgards:
    """Regole Westgard per QC."""
    def get_westgard_violation_rule(self, ...): ...

class Exporter:
    """Export Excel."""
    def quick_data_analysis(self, ...): ...

class Importer:
    """Import dati."""
    def get_generic_file_auto(self, ...): ...

# Engine combina TUTTI i mixin
class Engine(DBMS, Controller, QC, Westgards, Exporter, Importer, Tools, Launcher):
    """Orchestratore principale - ha TUTTE le funzionalità."""
    pass
```

#### Method Resolution Order (MRO)

Python cerca i metodi da sinistra a destra:

```python
Engine.__mro__
# (Engine, DBMS, Controller, QC, Westgards, Exporter, Importer, Tools, Launcher, object)

# Se due mixin hanno lo stesso metodo, vince il primo (più a sinistra)
```

#### Vantaggi

| Vantaggio | Spiegazione |
|-----------|-------------|
| **Riusabilità** | Ogni mixin è indipendente e riutilizzabile |
| **Separazione** | Ogni file ha una responsabilità specifica |
| **Flessibilità** | Puoi creare classi con diversi "mix" di funzionalità |
| **Testabilità** | Puoi testare ogni mixin separatamente |

---

## Testing

### Unit Test vs Integration Test

| Aspetto | Unit Test | Integration Test |
|---------|-----------|------------------|
| **Cosa testa** | Singola funzione/metodo | Più componenti insieme |
| **Database** | Mock (finto) | Reale (test DB) |
| **Velocità** | Molto veloce (ms) | Più lento (secondi) |
| **Isolamento** | Totale | Parziale |
| **Quando fallisce** | Sai esattamente cosa è rotto | Devi investigare |

**Esempio Unit Test:**
```python
def test_get_mean_with_valid_series():
    """Testa solo il calcolo della media, senza database."""
    qc = QC()
    series = [10.0, 20.0, 30.0]

    result = qc.get_mean(series)

    assert result == 20.0
```

**Esempio Integration Test:**
```python
def test_get_series_from_database(db_connection):
    """Testa che get_series legga correttamente dal DB reale."""
    controller = Controller(db_connection)

    # Questo va a leggere dal database di test
    series = controller.get_series(batch_id=1, workstation_id=1, limit=10)

    assert isinstance(series, list)
```

---

### Test Coverage

La **copertura dei test** misura quale percentuale del codice viene eseguita durante i test.

```
Copertura = (Righe eseguite dai test / Righe totali) × 100
```

#### Interpretazione

| Copertura | Significato |
|-----------|-------------|
| 0-20% | Quasi nessun test |
| 20-50% | Test basilari |
| 50-80% | Buona copertura |
| 80-100% | Ottima (ma attenzione!) |

#### Attenzione: Alta copertura ≠ Buoni test

```python
# Questo test ha 100% di copertura ma non testa NULLA di utile
def test_inutile():
    result = calcola_media([1, 2, 3])
    assert True  # Passa sempre!
```

#### Comando per misurare la copertura

```bash
pytest tests/ --cov=. --cov-report=term
```

---

### Mock e Stub

Quando testi un componente, vuoi isolarlo dalle sue dipendenze.

#### Mock

Un **mock** è un oggetto finto che simula il comportamento di uno reale:

```python
from unittest.mock import MagicMock

def test_save_calls_database():
    # Creo un mock del database
    mock_db = MagicMock()
    mock_db.write.return_value = 42  # Simulo che ritorni ID 42

    editor = BatchEditor(database=mock_db)
    editor.save({"name": "Test"})

    # Verifico che write() sia stato chiamato
    mock_db.write.assert_called_once()
```

#### Stub

Uno **stub** fornisce risposte predefinite:

```python
from unittest.mock import patch

def test_get_language_default():
    # "Fingo" che il file non esista
    with patch("builtins.open", side_effect=FileNotFoundError):
        result = engine.get_language()

    assert result == "en"  # Default quando file manca
```

---

## Sicurezza

### SQL Injection

#### Cos'è

Un attacco dove l'utente inserisce codice SQL malevolo in un campo di input.

#### Esempio di attacco

```python
# VULNERABILE - Mai fare così!
username = input("Username: ")  # L'utente inserisce: admin'; DROP TABLE users; --
sql = f"SELECT * FROM users WHERE username = '{username}'"
# Risultato: SELECT * FROM users WHERE username = 'admin'; DROP TABLE users; --'
# La tabella users viene cancellata!
```

#### Soluzione: Query Parametrizzate

```python
# SICURO - Usa sempre i placeholder ?
username = input("Username: ")
sql = "SELECT * FROM users WHERE username = ?"
cursor.execute(sql, (username,))
# Il driver escapa automaticamente i caratteri pericolosi
```

#### Validazione identificatori

Per nomi di tabelle e colonne (che non possono usare placeholder):

```python
import re

def _validate_sql_identifier(self, identifier: str) -> bool:
    """Valida che sia un nome SQL sicuro."""
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    return bool(re.match(pattern, identifier))

# Uso
if not self._validate_sql_identifier(table_name):
    raise ValueError(f"Nome tabella non valido: {table_name}")
```

---

### Bcrypt e Hashing

#### Perché non salvare password in chiaro

Se il database viene rubato, tutte le password sono compromesse.

#### Cos'è l'hashing

Una funzione **one-way** che trasforma la password in una stringa fissa:

```
"password123" → "$2b$12$LQv3c1yqBw..."
```

**Non è reversibile** - non puoi tornare da hash a password.

#### Perché bcrypt

| Caratteristica | Spiegazione |
|----------------|-------------|
| **Salt automatico** | Ogni hash è diverso anche per stessa password |
| **Cost factor** | Puoi rallentarlo per resistere a brute force |
| **Progettato per password** | Non per velocità come MD5/SHA |

#### Uso in Biovarase

```python
import bcrypt

# Creazione hash (registrazione/cambio password)
password = b"la_mia_password"
salt = bcrypt.gensalt(rounds=12)  # Cost factor 12
hashed = bcrypt.hashpw(password, salt)
# Salva 'hashed' nel database

# Verifica (login)
password_inserita = b"la_mia_password"
password_dal_db = user["pswrd"].encode('utf-8')

if bcrypt.checkpw(password_inserita, password_dal_db):
    print("Login OK")
else:
    print("Password errata")
```

---

## Architettura

### Separazione delle Responsabilità

Ogni modulo dovrebbe avere **una sola responsabilità**.

#### Struttura Biovarase

```
┌─────────────────────────────────────────────────────────┐
│                        views/                            │
│              (GUI - Presentazione)                       │
│    Responsabilità: Mostrare dati, gestire input utente  │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                       engine.py                          │
│              (Orchestratore - Coordinamento)             │
│    Responsabilità: Connettere tutti i componenti        │
└─────────────────────────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ controller  │    │    qc.py    │    │ westgards   │
│ (Dominio)   │    │ (Calcoli)   │    │ (Regole QC) │
└─────────────┘    └─────────────┘    └─────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│                        dbms.py                           │
│                   (Accesso Database)                     │
│    Responsabilità: Connessione, query, transazioni      │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│                       MariaDB                            │
│                    (Database)                            │
└─────────────────────────────────────────────────────────┘
```

---

### Multi-Tenant

#### Cos'è

Un'architettura dove **una singola istanza** dell'applicazione serve **più clienti** (tenant), mantenendo i dati isolati.

#### Implementazione in Biovarase

Ogni utente vede solo i dati della propria organizzazione:

```python
# All'accesso, si imposta il contesto
engine.current_ids = {
    "lab_id": 2002,      # Laboratorio dell'utente
    "section_id": 6,     # Sezione corrente
    "site_id": 2001,     # Regione/Sito
}

# Ogni query filtra per lab_id
sql = """
    SELECT * FROM batches
    WHERE lab_id = ?
    AND status = 1
"""
rows = engine.read(True, sql, (engine.current_ids["lab_id"],))
```

#### Gerarchia Organizzazioni

```
organizations (tabella singola con parent_id)
├── Italia (country)
│   ├── Lazio (region)
│   │   ├── Ospedale San Camillo (lab)
│   │   │   ├── Chimica Clinica (section)
│   │   │   └── Ematologia (section)
│   │   └── Policlinico Umberto I (lab)
│   └── Lombardia (region)
└── France (country)
```

---

## Python Avanzato

### Decoratori

#### Cosa sono

I **decoratori** sono funzioni che modificano il comportamento di altre funzioni o metodi. Usano la sintassi `@nome_decoratore` sopra la definizione della funzione.

#### Decoratori built-in più comuni

| Decoratore | Scopo | Quando usarlo |
|------------|-------|---------------|
| `@property` | Trasforma un metodo in attributo | Accesso controllato ai dati |
| `@staticmethod` | Metodo senza accesso a `self` | Utility functions nella classe |
| `@classmethod` | Metodo con accesso alla classe | Factory methods, costruttori alternativi |

#### @property - Attributi calcolati

Permette di accedere a un metodo come se fosse un attributo:

```python
# In calendarium.py
class Calendarium:
    @property
    def date(self):
        """Ritorna la data selezionata."""
        return self._date

# Uso - sembra un attributo, ma è un metodo!
cal = Calendarium()
data = cal.date  # NON cal.date() - niente parentesi
```

**Vantaggi:**
- Sintassi pulita per l'utente della classe
- Puoi aggiungere logica (validazione, calcolo) senza cambiare l'interfaccia
- Lazy evaluation - calcola solo quando richiesto

#### @staticmethod - Metodi utility

Metodo che non ha bisogno di `self` o della classe:

```python
# In ljcanvas.py
class LJCanvas:
    @staticmethod
    def _format_value(value, decimals=2):
        """Formatta un valore numerico."""
        if value is None:
            return "N/A"
        return f"{value:.{decimals}f}"

# Uso - può essere chiamato sulla classe o sull'istanza
formatted = LJCanvas._format_value(3.14159, 2)  # "3.14"
```

**Quando usarlo:**
- Funzioni di utilità che logicamente appartengono alla classe
- Non accedono a dati dell'istanza (`self`) o della classe (`cls`)

#### @classmethod - Metodi di classe

Metodo che riceve la classe come primo argomento (`cls`):

```python
# Esempio tipico - factory method
class DatabaseConnection:
    @classmethod
    def from_config(cls, config_path):
        """Crea connessione da file di configurazione."""
        config = load_config(config_path)
        return cls(config['host'], config['user'], config['password'])

# Uso
conn = DatabaseConnection.from_config("config.enc")
```

**Quando usarlo:**
- Costruttori alternativi
- Metodi che devono funzionare con sottoclassi

---

### Context Manager

#### Cosa sono

I **context manager** gestiscono risorse che devono essere acquisite e rilasciate (file, connessioni, lock). Usano la sintassi `with ... as ...`.

#### Il problema che risolvono

```python
# SBAGLIATO - se c'è un errore, il file resta aperto!
f = open("log.txt", "w")
f.write("messaggio")
# Se qui c'è un'eccezione, f.close() non viene mai chiamato
f.close()

# CORRETTO - with garantisce la chiusura
with open("log.txt", "w") as f:
    f.write("messaggio")
# File chiuso automaticamente, anche se c'è un'eccezione
```

#### Esempi in Biovarase

```python
# In engine.py - Lettura file configurazione
with open(path, "r", encoding="utf-8") as f:
    content = f.read()
# File chiuso automaticamente

# In security.py - Scrittura file criptato
with open(config_path, 'wb') as f:
    f.write(encrypted_data)

# In importer.py - Lettura file dati
with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
    for line in fh:
        process(line)
```

#### Come funziona internamente

```python
# Questo:
with open("file.txt") as f:
    data = f.read()

# È equivalente a:
f = open("file.txt")
try:
    data = f.read()
finally:
    f.close()  # Sempre eseguito, anche con eccezioni
```

#### Vantaggi

| Vantaggio | Spiegazione |
|-----------|-------------|
| **Sicurezza** | Risorse sempre rilasciate |
| **Leggibilità** | Codice più pulito |
| **Eccezioni** | Gestite correttamente |
| **Scope chiaro** | Vedi dove la risorsa è usata |

---

### hasattr e Introspezione

#### Cos'è l'introspezione

L'**introspezione** è la capacità di un programma di esaminare se stesso - scoprire quali attributi e metodi ha un oggetto a runtime.

#### hasattr() - Verificare se un attributo esiste

```python
hasattr(oggetto, "nome_attributo")  # Ritorna True o False
```

#### Perché è utile

1. **Evitare errori AttributeError**
2. **Duck typing** - "Se cammina come un'anatra e fa quack come un'anatra..."
3. **Compatibilità** - Codice che funziona con diverse versioni di oggetti
4. **Plugin/Estensioni** - Verificare funzionalità opzionali

#### Esempi in Biovarase

```python
# In controller.py - Chiamare metodo solo se esiste
if method_name and hasattr(win, method_name):
    getattr(win, method_name)()  # Chiama il metodo dinamicamente

# In biovarase.py - Feature detection
if not hasattr(self.engine, 'get_autologin_flag'):
    return  # Vecchia versione, funzionalità non disponibile

# In views/organization.py - Callback opzionale al parent
if hasattr(self.parent, "reload_and_reselect"):
    self.parent.reload_and_reselect()
elif hasattr(self.parent, "on_open"):
    self.parent.on_open()

# In views/notes.py - Verificare tipo prima di formattare
if hasattr(received, "strftime"):
    # È un oggetto datetime, posso formattarlo
    date_str = received.strftime("%d/%m/%Y")
else:
    # È già una stringa
    date_str = str(received)

# In views/batches.py - Verificare esistenza finestra child
if hasattr(self, "child") and self.child is not None and self.child.winfo_exists():
    self.child.focus_set()
```

#### Pattern comune: Callback opzionale

```python
def on_save(self):
    # Salva i dati...
    self.engine.write(sql, args)

    # Notifica il parent SE ha il metodo appropriato
    if hasattr(self.parent, "on_data_changed"):
        self.parent.on_data_changed()
    elif hasattr(self.parent, "on_open"):
        self.parent.on_open()
    # Se non ha nessuno dei due, non fare nulla
```

#### Funzioni correlate

| Funzione | Scopo | Esempio |
|----------|-------|---------|
| `hasattr(obj, name)` | Verifica esistenza | `hasattr(self, "child")` |
| `getattr(obj, name)` | Ottiene valore | `getattr(self, "child")` |
| `getattr(obj, name, default)` | Con default | `getattr(self, "child", None)` |
| `setattr(obj, name, value)` | Imposta valore | `setattr(self, "child", win)` |
| `delattr(obj, name)` | Elimina attributo | `delattr(self, "child")` |

#### hasattr vs try/except

```python
# Approccio LBYL (Look Before You Leap) - hasattr
if hasattr(obj, "metodo"):
    obj.metodo()

# Approccio EAFP (Easier to Ask Forgiveness) - try/except
try:
    obj.metodo()
except AttributeError:
    pass

# In Python, entrambi sono validi. hasattr è più leggibile
# per controlli semplici, try/except per logica complessa.
```

---

## Database

### Gestione delle Transazioni

#### Cos'è una transazione

Una **transazione** è un gruppo di operazioni che devono essere eseguite tutte insieme o nessuna. È il principio "tutto o niente".

#### ACID

| Proprietà | Significato |
|-----------|-------------|
| **A**tomicity | Tutto o niente |
| **C**onsistency | DB sempre in stato valido |
| **I**solation | Transazioni non interferiscono |
| **D**urability | Dati persistenti dopo commit |

#### commit() e rollback()

```python
# commit() - Rende permanenti le modifiche
self.con.commit()

# rollback() - Annulla le modifiche
self.con.rollback()
```

#### Esempio in Biovarase - dbms.py

```python
def write(self, commit: bool, sql: str, args: tuple = ()) -> int:
    """Esegue INSERT/UPDATE/DELETE."""
    try:
        cursor = self.con.cursor()
        cursor.execute(sql, args)

        if commit:
            self.con.commit()  # Rende permanente

        return cursor.lastrowid or cursor.rowcount

    except Exception as e:
        if commit:
            self.con.rollback()  # Annulla tutto!
        raise
```

#### Pattern: Transazione con più operazioni

```python
# In views/main.py - Test data insertion
try:
    # Operazione 1
    self.engine.write(False, sql1, args1)  # commit=False

    # Operazione 2
    self.engine.write(False, sql2, args2)  # commit=False

    # Operazione 3
    self.engine.write(False, sql3, args3)  # commit=False

    # Tutto OK? Conferma tutto insieme
    self.engine.con.commit()

except Exception as e:
    # Qualcosa è fallito? Annulla tutto
    self.engine.con.rollback()
    raise
```

#### Perché è importante

Immagina di trasferire soldi:

```python
# SENZA transazione - PERICOLOSO!
subtract_from_account_a(100)  # OK
# <-- Se qui c'è un crash, i soldi sono persi!
add_to_account_b(100)

# CON transazione - SICURO
try:
    subtract_from_account_a(100)
    add_to_account_b(100)
    connection.commit()  # Entrambe o nessuna
except:
    connection.rollback()  # Annulla tutto
```

#### In Biovarase: Abbott Import

```python
# In abbott_import_v2.py
try:
    for record in records:
        self.insert_result(record)

    # Tutti i record inseriti? Commit!
    self.con.commit()

except Exception as e:
    # Errore? Rollback di tutto
    self.con.rollback()
    log_error(e)
```

---

## Concorrenza

### Threading e Race Conditions

#### Cos'è un Thread

Un **thread** è un flusso di esecuzione indipendente. Più thread possono eseguire codice "contemporaneamente" nello stesso programma.

#### Perché usare i thread in GUI

La GUI (Tkinter) gira sul **main thread**. Se fai operazioni lunghe (query DB, download), la GUI si blocca ("Not Responding").

**Soluzione:** Esegui operazioni lunghe in un thread separato.

#### Esempi in Biovarase

```python
# In views/daily_validation.py
def _fetch_pending_validations(self):
    def fetch_data():
        # Operazione lenta in background
        data = self.engine.get_pending_validations()
        # Aggiorna GUI dal main thread
        self.after(0, lambda: self._display_data(data))

    # Lancia thread daemon (muore con l'app)
    thread = threading.Thread(target=fetch_data, daemon=True)
    thread.start()

# In monitor.py - Thread per monitoraggio
class Monitor(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True  # Muore quando l'app chiude

    def run(self):
        while self.running:
            self.check_something()
            time.sleep(1)

# In launcher.py - Aprire file esterni
thread = Thread(target=self._open_file, args=(path,))
thread.start()
```

#### Race Condition

Una **race condition** si verifica quando due thread accedono agli stessi dati e il risultato dipende dall'ordine di esecuzione.

```python
# PROBLEMA: Race condition
counter = 0

def increment():
    global counter
    temp = counter      # Thread 1: temp = 0
    temp = temp + 1     # Thread 1: temp = 1
                        # Thread 2: temp = 0 (legge prima che 1 scriva!)
    counter = temp      # Thread 1: counter = 1
                        # Thread 2: counter = 1 (sovrascrive!)

# Risultato atteso con 2 thread: counter = 2
# Risultato possibile: counter = 1 (race condition!)
```

#### Protezione con Lock

```python
import threading

counter = 0
lock = threading.Lock()

def increment():
    global counter
    with lock:  # Solo un thread alla volta può entrare
        temp = counter
        temp = temp + 1
        counter = temp
```

#### In Biovarase: Evitare race conditions

```python
# In views/bland_altman_alert.py
def on_cancel(self):
    # Ferma il thread prima di chiudere
    if hasattr(self, '_scan_thread') and self._scan_thread.is_alive():
        self._stop_scan = True
        self._scan_thread.join(timeout=1)

    self.destroy()
```

#### Thread daemon vs non-daemon

| Tipo | Comportamento | Uso |
|------|---------------|-----|
| `daemon=True` | Muore quando l'app chiude | Background tasks |
| `daemon=False` | L'app aspetta che finisca | Task critici |

```python
# Daemon - per operazioni che possono essere interrotte
thread = threading.Thread(target=background_task, daemon=True)

# Non-daemon - per operazioni che DEVONO completare
thread = threading.Thread(target=save_critical_data, daemon=False)
```

#### Best Practices

1. **Usa daemon=True** per thread di background
2. **Non toccare la GUI** da thread secondari (usa `after()`)
3. **Usa Lock** per dati condivisi
4. **Gestisci la chiusura** - ferma i thread prima di chiudere finestre

---

### Queue per Comunicazione Thread

#### Il problema

Come passare dati in modo sicuro da un thread worker al main thread (GUI)?

```python
# SBAGLIATO - Race condition!
self.results = []  # Condiviso tra thread

def worker():
    for item in items:
        result = process(item)
        self.results.append(result)  # Thread worker scrive

def check():
    for r in self.results:  # Main thread legge
        update_gui(r)       # Mentre worker scrive!
```

#### La soluzione: queue.Queue

`Queue` è una struttura dati **thread-safe** progettata per la comunicazione tra thread.

```python
from queue import Queue, Empty

q = Queue()

# Thread worker - produce dati
def worker():
    for item in items:
        result = process(item)
        q.put(result)  # Thread-safe
    q.put(None)  # Segnale di fine (sentinel)

# Main thread - consuma dati
def check_queue():
    try:
        while True:
            result = q.get_nowait()  # Non bloccante
            if result is None:
                return  # Fine
            update_gui(result)
    except Empty:
        pass  # Coda vuota, riprova dopo

    self.after(50, check_queue)  # Polling
```

#### Implementazione in Biovarase

```python
# In views/bland_altman_alert.py

def _on_scan(self):
    """Avvia scansione con Queue."""
    # Crea coda per risultati
    self._result_queue = Queue()

    # Lancia thread con riferimento alla coda
    self._scan_thread = threading.Thread(
        target=self._do_scan,
        args=(threshold, self._result_queue),  # Passa la coda
        daemon=True
    )
    self._scan_thread.start()

    # Avvia polling della coda
    self._process_result_queue()

def _do_scan(self, threshold, result_queue):
    """Thread worker - mette risultati in coda."""
    try:
        for combo in combinations:
            result = self._compare(combo, threshold)
            if result:
                result_queue.put(result)  # Invia al main thread
    finally:
        result_queue.put(None)  # Segnale di completamento

def _process_result_queue(self):
    """Main thread - legge dalla coda e aggiorna GUI."""
    try:
        while True:
            try:
                result = self._result_queue.get_nowait()
            except Empty:
                break  # Coda vuota

            if result is None:
                # Scan completato
                self._show_final_status()
                return

            # Aggiorna GUI progressivamente
            self._add_result_to_tree(result)
            self._update_status()

    except tk.TclError:
        return  # Finestra chiusa

    # Continua polling
    self.after(50, self._process_result_queue)
```

#### Metodi di Queue

| Metodo | Comportamento | Uso |
|--------|---------------|-----|
| `put(item)` | Aggiunge item (bloccante se piena) | Thread worker |
| `get()` | Preleva item (bloccante se vuota) | Consumer |
| `get_nowait()` | Preleva senza bloccare (raise Empty) | GUI polling |
| `put_nowait()` | Aggiunge senza bloccare (raise Full) | Non bloccante |
| `empty()` | True se vuota (approssimativo) | Check veloce |
| `qsize()` | Numero elementi (approssimativo) | Debug |

#### Pattern: Sentinel per fine stream

```python
# Il worker segnala la fine con un valore speciale
result_queue.put(None)  # None = "ho finito"

# Il consumer riconosce il segnale
result = queue.get()
if result is None:
    print("Stream completato")
    return
```

#### Vantaggi rispetto a variabili condivise

| Variabile condivisa | Queue |
|---------------------|-------|
| Race condition possibili | Thread-safe by design |
| Serve Lock manuale | Lock interno automatico |
| Polling su flag | Metodi bloccanti disponibili |
| Dati possono perdersi | FIFO garantito |

#### Quando usare Queue

| Scenario | Usa Queue? |
|----------|------------|
| Thread produce dati incrementali | ✅ Sì |
| Thread fa una singola operazione | ❌ No, usa `after()` |
| Più producer, un consumer | ✅ Sì |
| Risultati devono essere ordinati | ✅ Sì (FIFO) |
| GUI deve aggiornarsi progressivamente | ✅ Sì |

#### Cleanup alla chiusura

```python
def on_cancel(self):
    """Pulisci risorse prima di chiudere."""
    # Svuota la coda per sbloccare thread in attesa
    if hasattr(self, '_result_queue'):
        try:
            while not self._result_queue.empty():
                self._result_queue.get_nowait()
        except Empty:
            pass

    super().on_cancel()
```

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **ACID** | Atomicity, Consistency, Isolation, Durability - Proprietà delle transazioni |
| **API** | Application Programming Interface - Interfaccia per comunicare tra software |
| **Callback** | Funzione passata come argomento, chiamata in seguito |
| **Context Manager** | Oggetto che gestisce risorse con `with` statement |
| **CRUD** | Create, Read, Update, Delete - Operazioni base sui dati |
| **Daemon** | Thread/processo che gira in background e muore con l'app |
| **Decoratore** | Funzione che modifica il comportamento di altre funzioni |
| **DRY** | Don't Repeat Yourself - Non duplicare codice |
| **Duck Typing** | "Se cammina come un'anatra..." - Tipo basato su comportamento |
| **EAFP** | Easier to Ask Forgiveness than Permission - try/except |
| **Fixture** | Setup predefinito per i test |
| **Hash** | Trasformazione one-way di dati |
| **Introspezione** | Capacità del codice di esaminare se stesso a runtime |
| **LBYL** | Look Before You Leap - Controllare prima di agire (hasattr) |
| **Lock** | Meccanismo per sincronizzare accesso a risorse condivise |
| **MRO** | Method Resolution Order - Ordine ricerca metodi in ereditarietà |
| **ORM** | Object-Relational Mapping - Mappa oggetti a tabelle DB |
| **Queue** | Struttura dati thread-safe per comunicazione tra thread |
| **Race Condition** | Bug da accesso concorrente non sincronizzato |
| **Sentinel** | Valore speciale che segnala fine di uno stream |
| **Refactoring** | Migliorare codice senza cambiare comportamento |
| **Salt** | Valore random aggiunto prima dell'hashing |
| **Scope** | Ambito di visibilità di variabili/funzioni |
| **Stack trace** | Percorso delle chiamate che ha portato a un errore |
| **Thread** | Flusso di esecuzione indipendente in un processo |
| **Transazione** | Gruppo di operazioni atomiche (tutto o niente) |

---

*Ultimo aggiornamento: Gennaio 2025*
