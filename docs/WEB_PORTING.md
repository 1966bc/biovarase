# Biovarase Web Porting

Documentazione del porting di Biovarase da applicazione desktop (Python/Tkinter) a web (PHP/JavaScript).

## Filosofia

**Non tradurre, ripensare.** Non replichiamo Tkinter in PHP/JS, ma ricostruiamo l'applicazione assecondando i paradigmi web.

## Stack Tecnologico

| Componente | Scelta | Motivazione |
|------------|--------|-------------|
| Backend | PHP 7+ puro | Nessun framework, controllo totale |
| Frontend | JavaScript vanilla | Nessuna dipendenza, codice nostro |
| Database | MariaDB | Stesso di Biovarase desktop |
| Charts | Chart.js | Levey-Jennings con annotazioni |
| Dipendenze | Zero | Tutto codice nostro |

## Architettura

```
web/
├── index.php              # Entry point + router
├── .htaccess              # URL rewriting per Apache
├── favicon.ico            # Icona Biovarase
├── engine/
│   ├── router.php         # Router custom PHP 7
│   └── auth.php           # Sessioni, login, ruoli, permessi
├── api/
│   ├── config.php         # DB connection + helpers
│   ├── workstations.php   # Lista workstation
│   ├── workstation_tests.php # Test per workstation
│   ├── test_controls.php  # Dati grafici + drift
│   ├── result.php         # GET/PUT/POST(void) risultato
│   ├── notes.php          # GET/POST note
│   └── actions.php        # Lista azioni correttive
├── pages/
│   ├── dashboard.php      # Dashboard QC
│   ├── charts.php         # Grafici Levey-Jennings
│   ├── login.php          # Form login
│   ├── login_action.php   # Gestione login POST
│   ├── logout.php         # Logout
│   ├── profile.php        # Profilo utente
│   └── change_password.php # Cambio password
├── includes/
│   ├── header.php         # Header + navigazione dinamica
│   └── footer.php         # Footer + JS includes
├── js/
│   ├── dashboard.js       # Logica dashboard
│   ├── charts.js          # Grafici + modal note/edit
│   ├── chart.min.js       # Chart.js library
│   └── chartjs-plugin-annotation.min.js
├── css/
│   ├── dashboard.css
│   └── charts.css
└── migrations/            # Migrazioni SQL
```

## Autenticazione

Implementata in `auth.php`:
- Sessioni PHP con httpOnly, sameSite
- Timeout configurabile per utente (elapsing_time, enable_time)
- Password bcrypt (compatibile con Python)
- Ruoli 0-6 (stesso schema desktop)

### Funzioni Permessi

```php
isLoggedIn()           // Utente loggato?
getCurrentUser()       // Dati utente corrente
getCurrentRole()       // Ruolo numerico
hasRole($maxRole)      // Ha almeno questo ruolo?
isAdmin()              // Role 0-3
canValidateQC()        // Role 0-4
canModifyData()        // Role 0-5
canModifyResult($r)    // Può modificare questo risultato?
canVoidResult($r)      // Può annullare questo risultato?
```

### Permessi Granulari (created_by)

Logica permessi per modifica/annullamento risultati:
- **Role 0-3** (Admin): può modificare qualsiasi risultato del proprio org
- **Role 4-5** (Superuser/Tecnico): può modificare se:
  - `created_by = user_id` (l'ha creato lui)
  - `created_by IS NULL` (dato strumentale, team può modificare)
- **Role 6** (Viewer): sola lettura

## Funzionalità Grafici

### Click su punto
Utenti loggati possono cliccare sui punti del grafico per:
1. **Visualizzare dettagli** - Data, valore, z-score, chi ha inserito
2. **Modificare valore** - Se hanno permessi (sezione blu)
3. **Annullare risultato** - Status=0, resta visibile in grigio (sezione rossa)
4. **Aggiungere note** - Con azione correttiva (sezione arancione)

### Indicatori Visivi
- **Punti con note**: raggio maggiore (8px), bordo nero
- **Punti annullati**: colore grigio, tooltip "Annullato da: Nome"
- **Tooltip**: `[N]` per note, `[ANNULLATO]` per annullati

### Statistiche
Le statistiche (media, DS, CV, bias) escludono i risultati annullati.

## Migrazioni Web

Eseguire dopo le migrazioni desktop:

```bash
# Permessi granulari
mysql -u root -p biovarase < migrations/026_add_created_by_to_results.sql

# Operazione VOID nell'audit
mysql -u root -p biovarase < migrations/027_add_void_to_audit_operation.sql

# Nuova tabella assays (sostituisce test_methods + goals per web)
mysql -u root -p biovarase < migrations/028_create_assays_table.sql
```

## Schema Database Web vs Desktop

| Web (nuovo) | Desktop (legacy) | Note |
|-------------|------------------|------|
| `assays` | `test_methods` + `goals` | Tabella unificata |
| `batches.assay_id` | `batches.test_method_id` | Entrambi presenti |
| `audit_assays` | - | Nuovo audit trail |

La tabella `assays` include:
- Tutti i campi di `test_methods`
- Tutti i campi di `goals` (cvw, cvb, imp, bias, teap005, teap001)
- Campo `description` per nome locale del lab
- Trigger automatici per audit

## Configurazione Apache

1. Abilitare mod_rewrite:
```bash
sudo a2enmod rewrite
```

2. Modificare `/etc/apache2/apache2.conf`:
```apache
<Directory /var/www/>
    Options Indexes FollowSymLinks
    AllowOverride All
    Require all granted
</Directory>
```

3. Riavviare:
```bash
sudo systemctl restart apache2
```

## URL API

| URL | Metodo | Descrizione | Auth |
|-----|--------|-------------|------|
| `/api/workstations.php` | GET | Lista workstation | No |
| `/api/workstation_tests.php` | GET | Test per workstation | No |
| `/api/test_controls.php` | GET | Dati grafici + serie | No |
| `/api/result.php` | GET | Dettaglio risultato | No |
| `/api/result.php` | PUT | Modifica valore | Si |
| `/api/result.php` | POST | Annulla (action=void) | Si |
| `/api/notes.php` | GET | Note per risultato | No |
| `/api/notes.php` | POST | Aggiungi nota | Si |
| `/api/actions.php` | GET | Lista azioni | No |

## Deployment

### Copia file su server
```bash
cp -r web/* /var/www/html/biovarase/
chown -R www-data:www-data /var/www/html/biovarase/
chmod -R 755 /var/www/html/biovarase/
```

### Configurazione DB
Modificare `api/config.php` con credenziali corrette.

## Progressi

### Completato
- [x] Dashboard read-only
- [x] Grafici Levey-Jennings multipli
- [x] API REST per dati QC
- [x] Router PHP custom (PHP 7 compatibile)
- [x] Autenticazione con sessioni
- [x] Menu dinamico per ruolo
- [x] Login/logout
- [x] Cambio password
- [x] Click su punti per note/modifica
- [x] Annullamento risultati (grigio)
- [x] Permessi granulari (created_by)
- [x] Audit trail completo
- [x] Auto-selezione primo test

### Prossimi passi
- [ ] Validazione giornaliera
- [ ] Inserimento risultati manuali
- [ ] Gestione batch
- [ ] Report/export
