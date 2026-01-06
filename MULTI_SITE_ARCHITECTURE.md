   # Biovarase - Architettura Multi-Sito

**Documento Tecnico per Evoluzione Multi-Ospedale**

---

**Versione:** 1.0
**Data:** Dicembre 2025
**Autore:** Giuseppe Costanzi
**Stato:** In Sviluppo

---

## Indice

1. [Visione Strategica](#1-visione-strategica)
2. [Architettura Attuale vs Futura](#2-architettura-attuale-vs-futura)
3. [Normalizzazione Database](#3-normalizzazione-database)
4. [Multi-Tenancy](#4-multi-tenancy)
5. [API REST](#5-api-rest)
6. [Piano di Implementazione](#6-piano-di-implementazione)
7. [Impatto sul Codice](#7-impatto-sul-codice)

---

## 1. Visione Strategica

### Obiettivo

Trasformare Biovarase da applicazione single-site a piattaforma multi-ospedale regionale,
mantenendo la retrocompatibilità con l'installazione esistente al Sant'Andrea.

### Scenario Target: Regione Lazio

```
                            +----------------------------------+
                            |      CLOUD REGIONE LAZIO         |
                            |                                  |
                            |  +-----------+   +-----------+   |
                            |  | API REST  |-->|  MariaDB  |   |
                            |  |  (Flask)  |   |           |   |
                            |  +-----+-----+   +-----------+   |
                            |        |                         |
                            +--------+-------------------------+
                                     | HTTPS (porta 443)
              +----------------------+----------------------+
              |                      |                      |
              v                      v                      v
     +-----------------+    +-----------------+    +-----------------+
     |  Sant'Andrea    |    |  San Camillo    |    |  Policlinico    |
     |  site_id = 1    |    |  site_id = 2    |    |  site_id = 3    |
     |  (10 client)    |    |  (15 client)    |    |  (20 client)    |
     +-----------------+    +-----------------+    +-----------------+
```

### Stima Risparmio Economico

| Parametro | Valore |
|-----------|--------|
| Ospedali pubblici Lazio | ~20-25 |
| Strutture ASL con laboratorio | ~50+ |
| Costo Unity/BioRad per struttura | 30.000 - 50.000 EUR/anno |
| **Risparmio potenziale annuo** | **1.000.000 - 2.500.000 EUR** |

---

## 2. Architettura Attuale vs Futura

### 2.1 Architettura Attuale (Single-Site)

```
+------------------+                      +------------------+
|  Client Windows  | ---- porta 3306 ---> |  Server MariaDB  |
|  (biovarase.exe) |      SQL diretto     |  172.16.149.100  |
+------------------+                      +------------------+
        |                                         |
        |  Connessione diretta al database        |
        |  - Client ha credenziali DB             |
        |  - Query SQL inviate direttamente       |
        |  - Funziona solo in rete locale         |
        +-----------------------------------------+
```

**Caratteristiche:**
- Connessione diretta MariaDB (porta 3306)
- Credenziali database nel client
- Funziona solo in rete locale (o VPN)
- Semplice ma non scalabile

### 2.2 Architettura Futura (Multi-Site con Dual Mode)

```
+------------------+                      +------------------+                      +------------------+
|  Client Windows  | ---- porta 443 ----> |   Server API     | ---- localhost ----> |  Server MariaDB  |
|  (biovarase.exe) |      HTTPS/REST      |   (Flask)        |      porta 3306      |                  |
+------------------+                      +------------------+                      +------------------+
        |                                         |                                         |
        |  DUAL MODE: Il client supporta          |                                         |
        |  entrambe le modalita'                  |                                         |
        |                                         |                                         |
        |  Modalita' 1: API REST (remoto)         |                                         |
        |  - HTTPS porta 443                      |                                         |
        |  - Token JWT per autenticazione         |                                         |
        |  - Passa qualsiasi firewall             |                                         |
        |                                         |                                         |
        |  Modalita' 2: DB Diretto (locale)       |                                         |
        |  - Porta 3306 (come adesso)             |                                         |
        |  - Per rete locale Sant'Andrea          |                                         |
        |  - Retrocompatibilita' garantita        |                                         |
        +-----------------------------------------+-----------------------------------------+
```

### 2.3 Vantaggi del Dual Mode

| Aspetto | DB Diretto (Locale) | API REST (Remoto) |
|---------|---------------------|-------------------|
| **Velocita'** | Massima | Leggermente inferiore |
| **Firewall** | Richiede porta 3306 | Solo porta 443 (standard) |
| **Sicurezza** | Credenziali DB sul client | Solo token JWT |
| **Uso** | Rete locale ospedale | Ovunque (cloud) |
| **Manutenzione** | Nessuna modifica | Richiede server API |

**Strategia**: Mantenere entrambe le modalita'. Il client sceglie in base alla configurazione:
- `connection_mode = "direct"` -> Connessione DB diretta (attuale)
- `connection_mode = "api"` -> Connessione via API REST (nuova)

---

## 3. Normalizzazione Database

### 3.1 Problemi Attuali

| Tabella | Campo | Tipo Attuale | Limite | Problema |
|---------|-------|--------------|--------|----------|
| `sites` | `site_id` | TINYINT UNSIGNED | 255 | Pochi ospedali |
| `labs` | `site_id` | TINYINT UNSIGNED | 255 | FK incoerente |
| `sections` | `section_id` | TINYINT UNSIGNED | 255 | Poche sezioni totali |
| `sections` | `lab_id` | TINYINT | 127 | Non matcha labs.lab_id (INT) |
| `users` | `user_id` | TINYINT UNSIGNED | 255 | Pochi utenti totali |
| `users` | `site_id` | **MANCANTE** | - | Utente non associato a sito |

### 3.2 Schema Target

```
+------------------+
|      sites       |
+------------------+
| site_id (SMALL)  |<--+
| description      |   |
| status           |   |
+------------------+   |
         |             |
         | 1:N         |
         v             |
+------------------+   |
|      labs        |   |
+------------------+   |
| lab_id (INT)     |<--+--+
| site_id (SMALL)  |---+  |
| description      |      |
| status           |      |
+------------------+      |
         |                |
         | 1:N            |
         v                |
+------------------+      |
|    sections      |      |
+------------------+      |
| section_id (SMALL)|<-+  |
| lab_id (INT)     |--+  |
| description      |     |
| status           |     |
+------------------+     |
         |               |
         | 1:N           |
         v               |
+------------------+     |
|   workstations   |     |
+------------------+     |
| workstation_id   |     |
| section_id (SMALL)|----+
| description      |
| status           |
+------------------+
         |
         | 1:N
         v
+------------------+     +------------------+
|     batches      |     |      users       |
+------------------+     +------------------+
| batch_id         |     | user_id (SMALL)  |
| lab_id (INT)     |     | site_id (SMALL)  |----> sites.site_id
| ...              |     | nickname         |
+------------------+     | role             |
         |               +------------------+
         | 1:N
         v
+------------------+
|     results      |
+------------------+
| result_id        |
| batch_id         |
| ...              |
+------------------+
```

### 3.3 Script SQL di Migrazione

**IMPORTANTE**: Eseguire SEMPRE un backup prima della migrazione!

```bash
# Backup database
mysqldump -u root -p biovarase > backups/biovarase_pre_multisite_$(date +%Y%m%d_%H%M%S).sql
```

#### Migrazione 008: Normalizzazione Tipi e Multi-Tenancy

```sql
-- ============================================================================
-- MIGRAZIONE 008: Normalizzazione Database per Multi-Sito
-- ============================================================================
-- Data: Dicembre 2025
-- Autore: Giuseppe Costanzi
-- Descrizione: Allarga tipi di dati e aggiunge multi-tenancy
-- ============================================================================

-- Disabilita controlli FK temporaneamente
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================================
-- FASE 1: Allargamento tipi di dati
-- ============================================================================

-- 1.1 Tabella SITES: site_id da TINYINT a SMALLINT
ALTER TABLE sites
    MODIFY COLUMN site_id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT;

-- 1.2 Tabella LABS: site_id da TINYINT a SMALLINT (per FK coerente)
ALTER TABLE labs
    MODIFY COLUMN site_id SMALLINT UNSIGNED DEFAULT NULL;

-- 1.3 Tabella SECTIONS: section_id da TINYINT a SMALLINT
ALTER TABLE sections
    MODIFY COLUMN section_id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT;

-- 1.4 Tabella SECTIONS: lab_id da TINYINT a INT (per matchare labs.lab_id)
ALTER TABLE sections
    MODIFY COLUMN lab_id INT UNSIGNED DEFAULT NULL;

-- 1.5 Tabella USERS: user_id da TINYINT a SMALLINT
ALTER TABLE users
    MODIFY COLUMN user_id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT;

-- 1.6 Tabella WORKSTATIONS: section_id coerente con sections
ALTER TABLE workstations
    MODIFY COLUMN section_id SMALLINT UNSIGNED NOT NULL DEFAULT 1;

-- ============================================================================
-- FASE 2: Aggiunta campo site_id a users (Multi-Tenancy)
-- ============================================================================

-- 2.1 Aggiunge colonna site_id alla tabella users
ALTER TABLE users
    ADD COLUMN site_id SMALLINT UNSIGNED DEFAULT NULL
    COMMENT 'FK to sites.site_id - NULL means super-admin (all sites)'
    AFTER role;

-- 2.2 Aggiunge indice per performance
ALTER TABLE users
    ADD INDEX idx_users_site (site_id);

-- 2.3 Imposta site_id = 1 per tutti gli utenti esistenti (Sant Andrea)
UPDATE users SET site_id = 1 WHERE site_id IS NULL;

-- NOTA: Lasciare site_id = NULL per super-admin che vedono tutti i siti

-- ============================================================================
-- FASE 3: Aggiunta Foreign Keys mancanti
-- ============================================================================

-- 3.1 FK: users.site_id -> sites.site_id
ALTER TABLE users
    ADD CONSTRAINT fk_users_site
    FOREIGN KEY (site_id) REFERENCES sites(site_id)
    ON UPDATE CASCADE ON DELETE SET NULL;

-- 3.2 FK: sections.lab_id -> labs.lab_id
ALTER TABLE sections
    ADD CONSTRAINT fk_sections_lab
    FOREIGN KEY (lab_id) REFERENCES labs(lab_id)
    ON UPDATE CASCADE ON DELETE SET NULL;

-- 3.3 FK: workstations.section_id -> sections.section_id
ALTER TABLE workstations
    ADD CONSTRAINT fk_workstations_section
    FOREIGN KEY (section_id) REFERENCES sections(section_id)
    ON UPDATE CASCADE ON DELETE RESTRICT;

-- 3.4 FK: batches.lab_id -> labs.lab_id
ALTER TABLE batches
    ADD CONSTRAINT fk_batches_lab
    FOREIGN KEY (lab_id) REFERENCES labs(lab_id)
    ON UPDATE CASCADE ON DELETE RESTRICT;

-- ============================================================================
-- FASE 4: Aggiunta campo description a sites (mancante)
-- ============================================================================

-- 4.1 Aggiunge colonna description se non esiste
ALTER TABLE sites
    ADD COLUMN description VARCHAR(255) DEFAULT NULL
    COMMENT 'Nome ospedale/struttura'
    AFTER site_id;

-- 4.2 Imposta descrizione per site esistente
UPDATE sites SET description = 'AOU Sant''Andrea Roma' WHERE site_id = 1;

-- ============================================================================
-- FASE 5: Riabilita controlli FK
-- ============================================================================

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================================
-- VERIFICA
-- ============================================================================

-- Verifica struttura sites
DESCRIBE sites;

-- Verifica struttura users (deve avere site_id)
DESCRIBE users;

-- Verifica FK
SELECT
    TABLE_NAME,
    COLUMN_NAME,
    CONSTRAINT_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'biovarase'
AND REFERENCED_TABLE_NAME IS NOT NULL
ORDER BY TABLE_NAME;

-- Conta FK totali
SELECT COUNT(*) AS total_foreign_keys
FROM information_schema.TABLE_CONSTRAINTS
WHERE CONSTRAINT_SCHEMA = 'biovarase'
AND CONSTRAINT_TYPE = 'FOREIGN KEY';
```

#### Script di Rollback (se necessario)

```sql
-- ============================================================================
-- ROLLBACK MIGRAZIONE 008
-- ============================================================================
-- ATTENZIONE: Usare solo se necessario! Potrebbe causare perdita dati.
-- ============================================================================

SET FOREIGN_KEY_CHECKS = 0;

-- Rimuovi FK aggiunte
ALTER TABLE users DROP FOREIGN KEY fk_users_site;
ALTER TABLE sections DROP FOREIGN KEY fk_sections_lab;
ALTER TABLE workstations DROP FOREIGN KEY fk_workstations_section;
ALTER TABLE batches DROP FOREIGN KEY fk_batches_lab;

-- Rimuovi colonna site_id da users
ALTER TABLE users DROP COLUMN site_id;

-- Rimuovi colonna description da sites
ALTER TABLE sites DROP COLUMN description;

-- Ripristina tipi originali (ATTENZIONE: potrebbe fallire se ci sono valori > 255)
ALTER TABLE sites MODIFY COLUMN site_id TINYINT UNSIGNED NOT NULL AUTO_INCREMENT;
ALTER TABLE labs MODIFY COLUMN site_id TINYINT UNSIGNED DEFAULT NULL;
ALTER TABLE sections MODIFY COLUMN section_id TINYINT UNSIGNED NOT NULL AUTO_INCREMENT;
ALTER TABLE sections MODIFY COLUMN lab_id TINYINT DEFAULT NULL;
ALTER TABLE users MODIFY COLUMN user_id TINYINT UNSIGNED NOT NULL AUTO_INCREMENT;
ALTER TABLE workstations MODIFY COLUMN section_id SMALLINT UNSIGNED NOT NULL DEFAULT 1;

SET FOREIGN_KEY_CHECKS = 1;
```

---

## 4. Multi-Tenancy

### 4.1 Concetto

**Multi-tenancy** significa che piu' "inquilini" (ospedali) condividono lo stesso database,
ma ognuno vede SOLO i propri dati.

```
Database Biovarase (condiviso)
+-----------------------------------------------------------------------+
|                                                                       |
|  site_id = 1 (Sant'Andrea)     |  site_id = 2 (San Camillo)          |
|  +---------------------------+ |  +---------------------------+       |
|  | Labs: Biochimica, Emato   | |  | Labs: Analisi, Micro      |       |
|  | Users: Mario, Lucia       | |  | Users: Giuseppe, Anna     |       |
|  | Results: 10.000 record    | |  | Results: 15.000 record    |       |
|  +---------------------------+ |  +---------------------------+       |
|                                                                       |
|  Mario (site_id=1) vede SOLO   |  Giuseppe (site_id=2) vede SOLO     |
|  i dati del Sant'Andrea        |  i dati del San Camillo             |
|                                                                       |
+-----------------------------------------------------------------------+
```

### 4.2 Regole di Visibilita'

| Ruolo | site_id | Visibilita' |
|-------|---------|-------------|
| Super-Admin Regionale | NULL | Tutti i siti |
| Admin Ospedale | 1 | Solo site_id = 1 |
| Tecnico | 1 | Solo site_id = 1 |
| Viewer | 1 | Solo site_id = 1 (read-only) |

### 4.3 Implementazione nel Codice

Ogni query deve filtrare per `site_id` dell'utente loggato:

```python
# PRIMA (single-site)
sql = "SELECT * FROM labs WHERE status = 1"

# DOPO (multi-site)
if self.engine.log_user_site_id is None:
    # Super-admin: vede tutto
    sql = "SELECT * FROM labs WHERE status = 1"
else:
    # Utente normale: vede solo il suo sito
    sql = "SELECT * FROM labs WHERE site_id = ? AND status = 1"
    args = (self.engine.log_user_site_id,)
```

---

## 5. API REST

### 5.1 Cos'e' una API REST?

**REST** (Representational State Transfer) e' uno standard per comunicare via HTTP/HTTPS.

Invece di inviare query SQL direttamente al database, il client invia richieste HTTP
a un server intermedio (API), che esegue le operazioni e restituisce i risultati in formato JSON.

### 5.2 Confronto: DB Diretto vs API REST

```
MODALITA' 1: Connessione DB Diretta (attuale)
+------------------+                      +------------------+
|  Client          |  SQL:                |  MariaDB         |
|  biovarase.exe   |  SELECT * FROM       |  porta 3306      |
|                  |  results WHERE...    |                  |
+------------------+  ------------------> +------------------+

MODALITA' 2: API REST (nuova)
+------------------+                      +------------------+                      +------------------+
|  Client          |  HTTPS:              |  Server API      |  SQL locale:         |  MariaDB         |
|  biovarase.exe   |  GET /api/results    |  Flask/Python    |  SELECT * FROM...    |  porta 3306      |
|                  |  ?batch_id=123       |  porta 443       |                      |  (solo localhost)|
+------------------+  ------------------> +------------------+  ------------------> +------------------+
                      Token JWT                                 Credenziali sicure
```

### 5.3 Verbi HTTP (CRUD)

| Operazione | Verbo HTTP | Esempio | SQL Equivalente |
|------------|------------|---------|-----------------|
| **C**reate | POST | `POST /api/results` | INSERT INTO results... |
| **R**ead | GET | `GET /api/results/123` | SELECT * FROM results WHERE id=123 |
| **U**pdate | PUT | `PUT /api/results/123` | UPDATE results SET... WHERE id=123 |
| **D**elete | DELETE | `DELETE /api/results/123` | DELETE FROM results WHERE id=123 |

### 5.4 Esempio Pratico

**Richiesta (Client -> API):**
```http
POST /api/results HTTP/1.1
Host: api.biovarase.lazio.it
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json

{
    "batch_id": 123,
    "workstation_id": 5,
    "result": 4.56,
    "received": "2025-12-09T10:30:00"
}
```

**Risposta (API -> Client):**
```http
HTTP/1.1 201 Created
Content-Type: application/json

{
    "status": "success",
    "data": {
        "result_id": 4280,
        "batch_id": 123,
        "result": 4.56,
        "westgard_status": "Accept"
    }
}
```

### 5.5 Architettura Server API

```
Server Debian 10 (172.16.149.100)
+------------------------------------------------------------------+
|                                                                  |
|  +-------------------+     +-------------------+                 |
|  |      Nginx        |     |      MariaDB      |                 |
|  |  (Reverse Proxy)  |     |   (Database)      |                 |
|  |   porta 443 SSL   |     |   porta 3306      |                 |
|  +--------+----------+     +--------+----------+                 |
|           |                         ^                            |
|           | proxy_pass              | SQL                        |
|           v                         |                            |
|  +-------------------+              |                            |
|  |   Gunicorn        +--------------+                            |
|  |   (WSGI Server)   |                                           |
|  |   porta 8000      |                                           |
|  +--------+----------+                                           |
|           |                                                      |
|           | Python                                               |
|           v                                                      |
|  +-------------------+                                           |
|  |   Flask App       |                                           |
|  |   (API REST)      |                                           |
|  |   - /api/auth     |                                           |
|  |   - /api/results  |                                           |
|  |   - /api/batches  |                                           |
|  |   - /api/...      |                                           |
|  +-------------------+                                           |
|                                                                  |
+------------------------------------------------------------------+
```

### 5.6 Struttura Progetto API

```
biovarase/
+-- api/
    +-- __init__.py
    +-- app.py              # Flask application factory
    +-- config.py           # Configurazione (DB, JWT secret, etc.)
    +-- routes/
    |   +-- __init__.py
    |   +-- auth.py         # POST /api/auth/login, /api/auth/logout
    |   +-- results.py      # CRUD /api/results
    |   +-- batches.py      # CRUD /api/batches
    |   +-- users.py        # CRUD /api/users (admin only)
    |   +-- reports.py      # GET /api/reports/...
    +-- models/
    |   +-- __init__.py
    |   +-- user.py         # User model con validazione
    |   +-- result.py       # Result model
    |   +-- batch.py        # Batch model
    +-- middleware/
    |   +-- __init__.py
    |   +-- auth.py         # JWT validation middleware
    |   +-- site_filter.py  # Multi-tenancy filter
    +-- utils/
        +-- __init__.py
        +-- db.py           # Database connection pool
        +-- westgard.py     # Westgard rules (riuso da westgards.py)
```

### 5.7 Endpoints API (Prima Versione)

| Endpoint | Metodo | Descrizione | Autenticazione |
|----------|--------|-------------|----------------|
| `/api/auth/login` | POST | Login, ritorna JWT token | No |
| `/api/auth/logout` | POST | Invalida token | Si |
| `/api/auth/refresh` | POST | Rinnova token | Si |
| `/api/results` | GET | Lista risultati (filtri) | Si |
| `/api/results` | POST | Nuovo risultato | Si |
| `/api/results/{id}` | GET | Singolo risultato | Si |
| `/api/results/{id}` | PUT | Modifica risultato | Si |
| `/api/results/{id}` | DELETE | Elimina risultato | Si (admin) |
| `/api/batches` | GET | Lista batch | Si |
| `/api/batches` | POST | Nuovo batch | Si |
| `/api/batches/{id}` | GET | Singolo batch | Si |
| `/api/batches/{id}/results` | GET | Risultati di un batch | Si |
| `/api/westgard/evaluate` | POST | Valuta serie Westgard | Si |
| `/api/reports/daily` | GET | Report giornaliero | Si |
| `/api/sites` | GET | Lista siti (super-admin) | Si (super-admin) |
| `/api/users` | GET | Lista utenti | Si (admin) |

### 5.8 Autenticazione JWT

**JWT** (JSON Web Token) e' uno standard per autenticazione stateless.

```
1. Login
+--------+                           +--------+
| Client | -- POST /api/auth/login ->| Server |
|        |    {user, password}       |        |
|        | <-- JWT Token ----------- |        |
+--------+                           +--------+

2. Richieste successive
+--------+                           +--------+
| Client | -- GET /api/results ----->| Server |
|        |    Authorization: Bearer  |        |
|        |    eyJhbGciOiJIUzI1NiI... |        |
|        | <-- JSON Response ------- |        |
+--------+                           +--------+
```

**Struttura Token JWT:**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.
eyJ1c2VyX2lkIjoxLCJzaXRlX2lkIjoxLCJyb2xlIjowLCJleHAiOjE3MzM4MzYwMDB9.
SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

Decodificato:
```json
{
  "user_id": 1,
  "site_id": 1,
  "role": 0,
  "exp": 1733836000
}
```

### 5.9 Installazione Server API (Debian 10)

```bash
# 1. Installa dipendenze sistema
sudo apt update
sudo apt install -y python3-pip python3-venv nginx

# 2. Crea virtual environment per API
cd /home/bc/Documents/projects/biovarase
python3 -m venv venv_api
source venv_api/bin/activate

# 3. Installa dipendenze Python
pip install flask flask-cors flask-jwt-extended gunicorn mariadb

# 4. Crea file requirements_api.txt
cat > requirements_api.txt << 'EOF'
flask>=2.0.0
flask-cors>=3.0.0
flask-jwt-extended>=4.0.0
gunicorn>=20.0.0
mariadb>=1.0.0
python-dotenv>=0.19.0
EOF

# 5. Configura Nginx come reverse proxy
sudo tee /etc/nginx/sites-available/biovarase-api << 'EOF'
server {
    listen 443 ssl;
    server_name api.biovarase.local;

    # SSL certificates (generare con certbot o self-signed per test)
    ssl_certificate /etc/nginx/ssl/biovarase.crt;
    ssl_certificate_key /etc/nginx/ssl/biovarase.key;

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# 6. Abilita sito
sudo ln -s /etc/nginx/sites-available/biovarase-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 7. Crea servizio systemd per Gunicorn
sudo tee /etc/systemd/system/biovarase-api.service << 'EOF'
[Unit]
Description=Biovarase API Server
After=network.target mariadb.service

[Service]
User=bc
Group=bc
WorkingDirectory=/home/bc/Documents/projects/biovarase
Environment="PATH=/home/bc/Documents/projects/biovarase/venv_api/bin"
ExecStart=/home/bc/Documents/projects/biovarase/venv_api/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:8000 \
    --access-logfile /var/log/biovarase/api_access.log \
    --error-logfile /var/log/biovarase/api_error.log \
    api.app:create_app()

[Install]
WantedBy=multi-user.target
EOF

# 8. Crea directory log
sudo mkdir -p /var/log/biovarase
sudo chown bc:bc /var/log/biovarase

# 9. Abilita e avvia servizio
sudo systemctl daemon-reload
sudo systemctl enable biovarase-api
sudo systemctl start biovarase-api

# 10. Verifica
sudo systemctl status biovarase-api
curl -k https://localhost/api/health
```

---

## 6. Piano di Implementazione

### Fase 1: Normalizzazione Database (Immediato)

| Attivita' | Tempo | Priorita' |
|-----------|-------|-----------|
| Backup database | 5 min | CRITICO |
| Esegui migrazione 008 | 10 min | CRITICO |
| Verifica FK e tipi | 5 min | CRITICO |
| Test applicazione esistente | 30 min | ALTA |

### Fase 2: Aggiornamento Codice Python (1 settimana)

| File | Modifica | Priorita' |
|------|----------|-----------|
| `engine.py` | Aggiungere `log_user_site_id` | ALTA |
| `controller.py` | Filtro site_id nelle query | ALTA |
| `frames/users.py` | Campo site_id in form | MEDIA |
| `frames/sites.py` | Campo description | MEDIA |
| Tutti i frame | Verificare query per multi-site | MEDIA |

### Fase 3: Sviluppo API REST (2-3 settimane)

| Settimana | Attivita' |
|-----------|-----------|
| 1 | Setup Flask, autenticazione JWT, endpoint auth |
| 2 | Endpoint CRUD results, batches |
| 3 | Endpoint reports, test integrazione |

### Fase 4: Dual Mode Client (1 settimana)

| Attivita' | Descrizione |
|-----------|-------------|
| Classe `ApiClient` | Client HTTP per chiamate API |
| Configurazione | Switch DB diretto / API |
| Test | Verificare entrambe le modalita' |

### Fase 5: Test e Deploy (1 settimana)

| Attivita' | Descrizione |
|-----------|-------------|
| Test locale | API + Client in modalita' API |
| Test Sant'Andrea | Retrocompatibilita' DB diretto |
| Documentazione | Aggiornare manuali |

---

## 7. Impatto sul Codice

### 7.1 File da Modificare per Migrazione DB

Dopo la migrazione SQL, verificare che il codice Python gestisca correttamente
i nuovi tipi di dati. In teoria non dovrebbero esserci problemi perche'
SMALLINT e INT sono gestiti automaticamente da MariaDB Connector.

**File da controllare:**

| File | Motivo |
|------|--------|
| `engine.py` | Aggiungere attributo `log_user_site_id` |
| `controller.py` | Verificare query con site_id |
| `frames/users.py` | Aggiungere campo site_id al form |
| `frames/login.py` | Caricare site_id dell'utente al login |

### 7.2 Modifica engine.py

```python
# In Engine.__init__() aggiungere:
self.log_user_site_id = None  # Site ID dell'utente loggato (None = super-admin)

# In metodo di login, dopo autenticazione:
def set_logged_user(self, user_data):
    self.log_user = user_data["user_id"]
    self.log_user_site_id = user_data.get("site_id")  # None se super-admin
```

### 7.3 Modifica controller.py

```python
# Esempio: get_labs() con filtro site_id
def get_labs(self):
    if self.log_user_site_id is None:
        # Super-admin: vede tutti i laboratori
        sql = """SELECT * FROM labs
                 WHERE status = 1
                 ORDER BY description"""
        return self.read(True, sql, ())
    else:
        # Utente normale: vede solo il suo sito
        sql = """SELECT * FROM labs
                 WHERE site_id = ? AND status = 1
                 ORDER BY description"""
        return self.read(True, sql, (self.log_user_site_id,))
```

### 7.4 Checklist Verifica Post-Migrazione

- [ ] Applicazione si avvia senza errori
- [ ] Login funziona correttamente
- [ ] Lista laboratori mostra dati corretti
- [ ] Lista sezioni mostra dati corretti
- [ ] Inserimento risultato funziona
- [ ] Grafici Levey-Jennings funzionano
- [ ] Export Excel funziona
- [ ] Nessun errore nei log

---

## Appendice A: Comandi Utili

### Backup e Restore

```bash
# Backup
mysqldump -u root -p biovarase > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore
mysql -u root -p biovarase < backup_20251209_120000.sql
```

### Verifica Struttura Tabelle

```bash
# Connetti a MariaDB
mysql -u root -p biovarase

# Mostra struttura
DESCRIBE sites;
DESCRIBE labs;
DESCRIBE sections;
DESCRIBE users;

# Mostra FK
SELECT TABLE_NAME, COLUMN_NAME, CONSTRAINT_NAME, REFERENCED_TABLE_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'biovarase' AND REFERENCED_TABLE_NAME IS NOT NULL;
```

### Test API

```bash
# Health check
curl -k https://localhost/api/health

# Login
curl -k -X POST https://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Get results (con token)
curl -k https://localhost/api/results \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

---

## Appendice B: Domande Frequenti

**D: Posso eseguire la migrazione DB senza fermare l'applicazione?**
R: Si', ma e' consigliato farlo in un momento di basso utilizzo. Le ALTER TABLE
su tabelle piccole sono molto veloci (< 1 secondo).

**D: Gli utenti esistenti perderanno l'accesso?**
R: No. La migrazione imposta `site_id = 1` per tutti gli utenti esistenti,
quindi continueranno a vedere i dati del Sant'Andrea.

**D: Posso tornare indietro dopo la migrazione?**
R: Si', e' disponibile uno script di rollback. Pero' se vengono inseriti
nuovi utenti con user_id > 255, il rollback fallira'.

**D: L'API REST e' obbligatoria?**
R: No, e' opzionale. Il sistema continua a funzionare con connessione DB diretta.
L'API e' necessaria solo per accesso remoto via Internet.

---

**Documento preparato per progetto Biovarase Multi-Site**

*Versione 1.0 - Dicembre 2025*
