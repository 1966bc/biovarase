<?php
/**
 * Internationalization Module for Biovarase Web
 *
 * Provides translation support for English and Italian.
 * Same pattern as Python desktop app.
 *
 * Usage:
 *   require_once 'engine/i18n.php';
 *   echo _('Save');  // Output: "Salva" (if language is 'it')
 *
 * Author: 1966bc (Giuseppe Costanzi)
 * License: GNU GPL v3
 */

// Available languages
define('LANGUAGES', [
    'en' => 'English',
    'it' => 'Italiano',
]);

// Default language
define('DEFAULT_LANGUAGE', 'it');

// Translation dictionary
// Key = English (default), Value = array with translations
$TRANSLATIONS = [
    // ==========================================================================
    // Common Buttons
    // ==========================================================================
    'Save' => ['it' => 'Salva', 'en' => 'Save'],
    'Cancel' => ['it' => 'Annulla', 'en' => 'Cancel'],
    'Close' => ['it' => 'Chiudi', 'en' => 'Close'],
    'New' => ['it' => 'Nuovo', 'en' => 'New'],
    'Edit' => ['it' => 'Modifica', 'en' => 'Edit'],
    'Delete' => ['it' => 'Elimina', 'en' => 'Delete'],
    'Add' => ['it' => 'Aggiungi', 'en' => 'Add'],
    'Remove' => ['it' => 'Rimuovi', 'en' => 'Remove'],
    'Load' => ['it' => 'Carica', 'en' => 'Load'],
    'Search' => ['it' => 'Cerca', 'en' => 'Search'],
    'Reset' => ['it' => 'Reimposta', 'en' => 'Reset'],
    'Apply' => ['it' => 'Applica', 'en' => 'Apply'],
    'OK' => ['it' => 'OK', 'en' => 'OK'],
    'Yes' => ['it' => 'Sì', 'en' => 'Yes'],
    'No' => ['it' => 'No', 'en' => 'No'],
    'Back' => ['it' => 'Indietro', 'en' => 'Back'],
    'Next' => ['it' => 'Avanti', 'en' => 'Next'],
    'Create' => ['it' => 'Crea', 'en' => 'Create'],
    'Update' => ['it' => 'Aggiorna', 'en' => 'Update'],

    // ==========================================================================
    // Common Labels
    // ==========================================================================
    'Description' => ['it' => 'Descrizione', 'en' => 'Description'],
    'Code' => ['it' => 'Codice', 'en' => 'Code'],
    'Name' => ['it' => 'Nome', 'en' => 'Name'],
    'Status' => ['it' => 'Stato', 'en' => 'Status'],
    'Date' => ['it' => 'Data', 'en' => 'Date'],
    'Active' => ['it' => 'Attivo', 'en' => 'Active'],
    'Inactive' => ['it' => 'Disattivo', 'en' => 'Inactive'],
    'Enabled' => ['it' => 'Attivo', 'en' => 'Enabled'],
    'Disabled' => ['it' => 'Disabilitato', 'en' => 'Disabled'],
    'Actions' => ['it' => 'Azioni', 'en' => 'Actions'],
    'ID' => ['it' => 'ID', 'en' => 'ID'],
    'Total' => ['it' => 'Totale', 'en' => 'Total'],

    // ==========================================================================
    // Authentication
    // ==========================================================================
    'Login' => ['it' => 'Accedi', 'en' => 'Login'],
    'Logout' => ['it' => 'Esci', 'en' => 'Logout'],
    'Username' => ['it' => 'Utente', 'en' => 'Username'],
    'Password' => ['it' => 'Password', 'en' => 'Password'],
    'Remember me' => ['it' => 'Ricordami', 'en' => 'Remember me'],
    'Invalid credentials.' => ['it' => 'Credenziali non valide.', 'en' => 'Invalid credentials.'],
    'Profile' => ['it' => 'Profilo', 'en' => 'Profile'],
    'Change Password' => ['it' => 'Cambia Password', 'en' => 'Change Password'],

    // ==========================================================================
    // Navigation
    // ==========================================================================
    'Dashboard' => ['it' => 'Dashboard', 'en' => 'Dashboard'],
    'Charts' => ['it' => 'Grafici', 'en' => 'Charts'],
    'Validation' => ['it' => 'Validazione', 'en' => 'Validation'],
    'Batches' => ['it' => 'Lotti', 'en' => 'Batches'],
    'Results' => ['it' => 'Risultati', 'en' => 'Results'],
    'Admin' => ['it' => 'Admin', 'en' => 'Admin'],
    'Administration' => ['it' => 'Amministrazione', 'en' => 'Administration'],

    // ==========================================================================
    // Admin Menu
    // ==========================================================================
    'Tests' => ['it' => 'Test', 'en' => 'Tests'],
    'Methods' => ['it' => 'Metodi', 'en' => 'Methods'],
    'Units' => ['it' => 'Unità', 'en' => 'Units'],
    'Samples' => ['it' => 'Campioni', 'en' => 'Samples'],
    'Categories' => ['it' => 'Categorie', 'en' => 'Categories'],
    'Controls' => ['it' => 'Controlli', 'en' => 'Controls'],
    'Equipments' => ['it' => 'Strumenti', 'en' => 'Equipments'],
    'Suppliers' => ['it' => 'Fornitori', 'en' => 'Suppliers'],
    'Corrective Actions' => ['it' => 'Azioni Correttive', 'en' => 'Corrective Actions'],
    'Organizations' => ['it' => 'Organizzazioni', 'en' => 'Organizations'],
    'Assays' => ['it' => 'Assays', 'en' => 'Assays'],
    'Users' => ['it' => 'Utenti', 'en' => 'Users'],

    // Admin descriptions
    'Analytes and laboratory tests' => ['it' => 'Analiti e test di laboratorio', 'en' => 'Analytes and laboratory tests'],
    'Analytical methods' => ['it' => 'Metodi analitici', 'en' => 'Analytical methods'],
    'Units of measurement' => ['it' => 'Unità di misura', 'en' => 'Units of measurement'],
    'Sample types' => ['it' => 'Tipi di campione', 'en' => 'Sample types'],
    'Test categories' => ['it' => 'Categorie test', 'en' => 'Test categories'],
    'QC control materials' => ['it' => 'Materiali di controllo QC', 'en' => 'QC control materials'],
    'Instrumentation' => ['it' => 'Strumentazione', 'en' => 'Instrumentation'],
    'Suppliers and manufacturers' => ['it' => 'Fornitori', 'en' => 'Suppliers and manufacturers'],
    'QC corrective actions' => ['it' => 'Azioni correttive QC', 'en' => 'QC corrective actions'],
    'Organizational structure' => ['it' => 'Struttura organizzativa', 'en' => 'Organizational structure'],
    'QC test configuration' => ['it' => 'Configurazione test QC', 'en' => 'QC test configuration'],
    'User management' => ['it' => 'Gestione utenti', 'en' => 'User management'],

    // Admin sections
    'Master Data (Global Data)' => ['it' => 'Master Data (Dati Globali)', 'en' => 'Master Data (Global Data)'],
    'Laboratory Management' => ['it' => 'Gestione Laboratorio', 'en' => 'Laboratory Management'],
    'System tables and configuration management' => ['it' => 'Gestione tabelle di sistema e configurazione', 'en' => 'System tables and configuration management'],

    // ==========================================================================
    // CRUD Operations
    // ==========================================================================
    'New Test' => ['it' => 'Nuovo Test', 'en' => 'New Test'],
    'Edit Test' => ['it' => 'Modifica Test', 'en' => 'Edit Test'],
    'Delete Test' => ['it' => 'Elimina Test', 'en' => 'Delete Test'],
    'Test Management' => ['it' => 'Gestione Tests', 'en' => 'Test Management'],
    'Tests (Analytes)' => ['it' => 'Tests (Analiti)', 'en' => 'Tests (Analytes)'],

    'New Method' => ['it' => 'Nuovo Metodo', 'en' => 'New Method'],
    'Edit Method' => ['it' => 'Modifica Metodo', 'en' => 'Edit Method'],
    'Method Management' => ['it' => 'Gestione Metodi', 'en' => 'Method Management'],

    'New Unit' => ['it' => 'Nuova Unità', 'en' => 'New Unit'],
    'Edit Unit' => ['it' => 'Modifica Unità', 'en' => 'Edit Unit'],
    'Unit Management' => ['it' => 'Gestione Unità', 'en' => 'Unit Management'],

    'New Sample' => ['it' => 'Nuovo Campione', 'en' => 'New Sample'],
    'Edit Sample' => ['it' => 'Modifica Campione', 'en' => 'Edit Sample'],
    'Sample Management' => ['it' => 'Gestione Campioni', 'en' => 'Sample Management'],

    'New Category' => ['it' => 'Nuova Categoria', 'en' => 'New Category'],
    'Edit Category' => ['it' => 'Modifica Categoria', 'en' => 'Edit Category'],
    'Category Management' => ['it' => 'Gestione Categorie', 'en' => 'Category Management'],

    // ==========================================================================
    // Messages
    // ==========================================================================
    'Description is required' => ['it' => 'La descrizione è obbligatoria', 'en' => 'Description is required'],
    'created successfully' => ['it' => 'creato con successo', 'en' => 'created successfully'],
    'updated successfully' => ['it' => 'aggiornato con successo', 'en' => 'updated successfully'],
    'deleted successfully' => ['it' => 'eliminato con successo', 'en' => 'deleted successfully'],
    'Error' => ['it' => 'Errore', 'en' => 'Error'],
    'Database error' => ['it' => 'Errore database', 'en' => 'Database error'],
    'A record with this description already exists' => ['it' => 'Esiste già un record con questa descrizione', 'en' => 'A record with this description already exists'],
    'Cannot delete: record is in use' => ['it' => 'Impossibile eliminare: record in uso', 'en' => 'Cannot delete: record is in use'],
    'Cannot delete: used in assays' => ['it' => 'Impossibile eliminare: utilizzato in assays', 'en' => 'Cannot delete: used in assays'],
    'Cannot delete: used in test_methods' => ['it' => 'Impossibile eliminare: utilizzato in test_methods', 'en' => 'Cannot delete: used in test_methods'],
    'Data loading error' => ['it' => 'Errore caricamento dati', 'en' => 'Data loading error'],
    'No records found' => ['it' => 'Nessun record trovato', 'en' => 'No records found'],

    // ==========================================================================
    // Filters
    // ==========================================================================
    'Search...' => ['it' => 'Cerca...', 'en' => 'Search...'],
    'Show disabled' => ['it' => 'Mostra disabilitati', 'en' => 'Show disabled'],
    'All' => ['it' => 'Tutti', 'en' => 'All'],

    // ==========================================================================
    // Confirmation
    // ==========================================================================
    'Confirm Deletion' => ['it' => 'Conferma Eliminazione', 'en' => 'Confirm Deletion'],
    'Are you sure you want to delete' => ['it' => 'Sei sicuro di voler eliminare', 'en' => 'Are you sure you want to delete'],
    'This action cannot be undone.' => ['it' => 'Questa azione non può essere annullata.', 'en' => 'This action cannot be undone.'],

    // ==========================================================================
    // Charts
    // ==========================================================================
    'Workstation' => ['it' => 'Postazione', 'en' => 'Workstation'],
    'Test' => ['it' => 'Test', 'en' => 'Test'],
    'Batch' => ['it' => 'Lotto', 'en' => 'Batch'],
    'Level' => ['it' => 'Livello', 'en' => 'Level'],
    'Target' => ['it' => 'Target', 'en' => 'Target'],
    'SD' => ['it' => 'DS', 'en' => 'SD'],
    'CV%' => ['it' => 'CV%', 'en' => 'CV%'],
    'Bias%' => ['it' => 'Bias%', 'en' => 'Bias%'],
    'Mean' => ['it' => 'Media', 'en' => 'Mean'],
    'Value' => ['it' => 'Valore', 'en' => 'Value'],
    'Z-Score' => ['it' => 'Z-Score', 'en' => 'Z-Score'],

    // ==========================================================================
    // Notes
    // ==========================================================================
    'Notes' => ['it' => 'Note', 'en' => 'Notes'],
    'Add Note' => ['it' => 'Aggiungi Nota', 'en' => 'Add Note'],
    'Edit Note' => ['it' => 'Modifica Nota', 'en' => 'Edit Note'],
    'Action' => ['it' => 'Azione', 'en' => 'Action'],
    'Select an action' => ['it' => 'Seleziona un\'azione', 'en' => 'Select an action'],

    // ==========================================================================
    // Result Operations
    // ==========================================================================
    'Edit Result' => ['it' => 'Modifica Risultato', 'en' => 'Edit Result'],
    'Void Result' => ['it' => 'Annulla Risultato', 'en' => 'Void Result'],
    'Voided' => ['it' => 'Annullato', 'en' => 'Voided'],
    'Voided by' => ['it' => 'Annullato da', 'en' => 'Voided by'],
    'Created by' => ['it' => 'Creato da', 'en' => 'Created by'],

    // ==========================================================================
    // Roles
    // ==========================================================================
    'App Admin' => ['it' => 'App Admin', 'en' => 'App Admin'],
    'Country Admin' => ['it' => 'Country Admin', 'en' => 'Country Admin'],
    'Regional Admin' => ['it' => 'Regional Admin', 'en' => 'Regional Admin'],
    'Lab Admin' => ['it' => 'Lab Admin', 'en' => 'Lab Admin'],
    'Superuser' => ['it' => 'Supervisore', 'en' => 'Superuser'],
    'Technician' => ['it' => 'Tecnico', 'en' => 'Technician'],
    'Viewer' => ['it' => 'Viewer', 'en' => 'Viewer'],

    // ==========================================================================
    // QC Specific
    // ==========================================================================
    'Levey-Jennings' => ['it' => 'Levey-Jennings', 'en' => 'Levey-Jennings'],
    'Westgard Rules' => ['it' => 'Regole di Westgard', 'en' => 'Westgard Rules'],
    'Out of control' => ['it' => 'Fuori controllo', 'en' => 'Out of control'],
    'Warning' => ['it' => 'Attenzione', 'en' => 'Warning'],
    'In control' => ['it' => 'In controllo', 'en' => 'In control'],

    // ==========================================================================
    // Units table specific
    // ==========================================================================
    'Symbol' => ['it' => 'Simbolo', 'en' => 'Symbol'],

    // ==========================================================================
    // Samples table specific
    // ==========================================================================
    'Sample Type' => ['it' => 'Tipo Campione', 'en' => 'Sample Type'],

    // ==========================================================================
    // LOINC
    // ==========================================================================
    'LOINC Code' => ['it' => 'Codice LOINC', 'en' => 'LOINC Code'],

    // ==========================================================================
    // Settings / Preferences
    // ==========================================================================
    'Settings' => ['it' => 'Impostazioni', 'en' => 'Settings'],
    'Language' => ['it' => 'Lingua', 'en' => 'Language'],
    'Theme' => ['it' => 'Tema', 'en' => 'Theme'],
    'Light' => ['it' => 'Chiaro', 'en' => 'Light'],
    'Dark' => ['it' => 'Scuro', 'en' => 'Dark'],
    'Change' => ['it' => 'Cambia', 'en' => 'Change'],

    // ==========================================================================
    // Users
    // ==========================================================================
    'User' => ['it' => 'Utente', 'en' => 'User'],
    'Last Name' => ['it' => 'Cognome', 'en' => 'Last Name'],
    'First Name' => ['it' => 'Nome', 'en' => 'First Name'],
    'Email' => ['it' => 'Email', 'en' => 'Email'],
    'Role' => ['it' => 'Ruolo', 'en' => 'Role'],
    'Organization' => ['it' => 'Organizzazione', 'en' => 'Organization'],
    'Reset Password' => ['it' => 'Reimposta Password', 'en' => 'Reset Password'],
    'New Password' => ['it' => 'Nuova Password', 'en' => 'New Password'],
    'Minimum 6 characters' => ['it' => 'Minimo 6 caratteri', 'en' => 'Minimum 6 characters'],
    'Password must be at least 6 characters' => ['it' => 'La password deve essere di almeno 6 caratteri', 'en' => 'Password must be at least 6 characters'],
    'Valid email is required' => ['it' => 'Email valida richiesta', 'en' => 'Valid email is required'],
    'Username already exists' => ['it' => 'Username già esistente', 'en' => 'Username already exists'],
    'Password reset successfully' => ['it' => 'Password reimpostata con successo', 'en' => 'Password reset successfully'],
    'Cannot create user with higher privileges' => ['it' => 'Impossibile creare utente con privilegi superiori', 'en' => 'Cannot create user with higher privileges'],
    'Cannot edit user with higher privileges' => ['it' => 'Impossibile modificare utente con privilegi superiori', 'en' => 'Cannot edit user with higher privileges'],
    'All roles' => ['it' => 'Tutti i ruoli', 'en' => 'All roles'],
    'No organization (global)' => ['it' => 'Nessuna organizzazione (globale)', 'en' => 'No organization (global)'],

    // ==========================================================================
    // Assays
    // ==========================================================================
    'Assay' => ['it' => 'Assay', 'en' => 'Assay'],
    'Method' => ['it' => 'Metodo', 'en' => 'Method'],
    'Unit' => ['it' => 'Unità', 'en' => 'Unit'],
    'Sample' => ['it' => 'Campione', 'en' => 'Sample'],
    'Category' => ['it' => 'Categoria', 'en' => 'Category'],
    'Section' => ['it' => 'Sezione', 'en' => 'Section'],
    'All sections' => ['it' => 'Tutte le sezioni', 'en' => 'All sections'],
    'Test is required' => ['it' => 'Test obbligatorio', 'en' => 'Test is required'],
    'Method is required' => ['it' => 'Metodo obbligatorio', 'en' => 'Method is required'],
    'Unit is required' => ['it' => 'Unità obbligatoria', 'en' => 'Unit is required'],
    'Sample is required' => ['it' => 'Campione obbligatorio', 'en' => 'Sample is required'],
    'Code is required' => ['it' => 'Codice obbligatorio', 'en' => 'Code is required'],
    'Select test...' => ['it' => 'Seleziona test...', 'en' => 'Select test...'],
    'Select method...' => ['it' => 'Seleziona metodo...', 'en' => 'Select method...'],
    'Select unit...' => ['it' => 'Seleziona unità...', 'en' => 'Select unit...'],
    'Select sample...' => ['it' => 'Seleziona campione...', 'en' => 'Select sample...'],
    'No category' => ['it' => 'Nessuna categoria', 'en' => 'No category'],
    'No section (global)' => ['it' => 'Nessuna sezione (globale)', 'en' => 'No section (global)'],
    'Local Name' => ['it' => 'Nome Locale', 'en' => 'Local Name'],
    'Optional local lab name' => ['it' => 'Nome locale opzionale', 'en' => 'Optional local lab name'],
    'Analytical Goals' => ['it' => 'Obiettivi Analitici', 'en' => 'Analytical Goals'],
    'Imprecision' => ['it' => 'Imprecisione', 'en' => 'Imprecision'],
    'Bias' => ['it' => 'Bias', 'en' => 'Bias'],
    'Mandatory' => ['it' => 'Obbligatorio', 'en' => 'Mandatory'],
    'Export to reports' => ['it' => 'Esporta nei report', 'en' => 'Export to reports'],
    'Search code or test...' => ['it' => 'Cerca codice o test...', 'en' => 'Search code or test...'],
    'Permission denied' => ['it' => 'Permesso negato', 'en' => 'Permission denied'],

    // ==========================================================================
    // Dashboard
    // ==========================================================================
    'Workstations' => ['it' => 'Linee Analitiche', 'en' => 'Workstations'],
    'Select a workstation' => ['it' => 'Seleziona una linea analitica', 'en' => 'Select a workstation'],
    'Select a test' => ['it' => 'Seleziona un test', 'en' => 'Select a test'],
    'Period' => ['it' => 'Periodo', 'en' => 'Period'],
    'Today' => ['it' => 'Oggi', 'en' => 'Today'],
    '7 days' => ['it' => '7 giorni', 'en' => '7 days'],
    '30 days' => ['it' => '30 giorni', 'en' => '30 days'],
    '60 days' => ['it' => '60 giorni', 'en' => '60 days'],
    'or' => ['it' => 'oppure', 'en' => 'or'],
    'Start date' => ['it' => 'Data inizio', 'en' => 'Start date'],
    'End date' => ['it' => 'Data fine', 'en' => 'End date'],
    'Clear dates' => ['it' => 'Cancella date', 'en' => 'Clear dates'],
    'Auto-refresh' => ['it' => 'Auto-refresh', 'en' => 'Auto-refresh'],
    '30 seconds' => ['it' => '30 secondi', 'en' => '30 seconds'],
    '1 minute' => ['it' => '1 minuto', 'en' => '1 minute'],
    '2 minutes' => ['it' => '2 minuti', 'en' => '2 minutes'],
    '5 minutes' => ['it' => '5 minuti', 'en' => '5 minutes'],
    'Refresh' => ['it' => 'Aggiorna', 'en' => 'Refresh'],

    // ==========================================================================
    // Workstations
    // ==========================================================================
    'New Workstation' => ['it' => 'Nuova Workstation', 'en' => 'New Workstation'],
    'Edit Workstation' => ['it' => 'Modifica Workstation', 'en' => 'Edit Workstation'],
    'Workstation created successfully' => ['it' => 'Workstation creata con successo', 'en' => 'Workstation created successfully'],
    'Workstation updated successfully' => ['it' => 'Workstation aggiornata con successo', 'en' => 'Workstation updated successfully'],
    'No sections found for this lab. Create sections first.' => ['it' => 'Nessuna sezione trovata per questo laboratorio. Crea prima le sezioni.', 'en' => 'No sections found for this lab. Create sections first.'],
    'No workstations found.' => ['it' => 'Nessuna workstation trovata.', 'en' => 'No workstations found.'],
    'Show assigned assays' => ['it' => 'Mostra assay assegnati', 'en' => 'Show assigned assays'],
    'Assigned Assays' => ['it' => 'Assay Assegnati', 'en' => 'Assigned Assays'],
    'Assign Assay' => ['it' => 'Assegna Assay', 'en' => 'Assign Assay'],
    'Assign Assay to' => ['it' => 'Assegna Assay a', 'en' => 'Assign Assay to'],
    'No assays assigned' => ['it' => 'Nessun assay assegnato', 'en' => 'No assays assigned'],
    'External Code' => ['it' => 'Codice Esterno', 'en' => 'External Code'],
    'External code' => ['it' => 'Codice esterno', 'en' => 'External code'],
    'Assay assigned successfully' => ['it' => 'Assay assegnato con successo', 'en' => 'Assay assigned successfully'],
    'Assay already assigned to this workstation' => ['it' => 'Assay già assegnato a questa workstation', 'en' => 'Assay already assigned to this workstation'],
    'Assay removed successfully' => ['it' => 'Assay rimosso con successo', 'en' => 'Assay removed successfully'],
    'External code updated' => ['it' => 'Codice esterno aggiornato', 'en' => 'External code updated'],
    'Invalid selection' => ['it' => 'Selezione non valida', 'en' => 'Invalid selection'],
    'from this workstation?' => ['it' => 'da questa workstation?', 'en' => 'from this workstation?'],
    'Serial Number' => ['it' => 'Numero Seriale', 'en' => 'Serial Number'],
    'Assays' => ['it' => 'Assay', 'en' => 'Assays'],
    'Assign' => ['it' => 'Assegna', 'en' => 'Assign'],
    'Optional' => ['it' => 'Opzionale', 'en' => 'Optional'],
    'Analytical workstations' => ['it' => 'Linee analitiche', 'en' => 'Analytical workstations'],
    'assay' => ['it' => 'assay', 'en' => 'assay'],
    'assays' => ['it' => 'assay', 'en' => 'assays'],
    'Edit External Code' => ['it' => 'Modifica Codice Esterno', 'en' => 'Edit External Code'],
    'Edit external code' => ['it' => 'Modifica codice esterno', 'en' => 'Edit external code'],
    'Enter external code' => ['it' => 'Inserisci codice esterno', 'en' => 'Enter external code'],
    'Code used by external systems (e.g., Abbott)' => ['it' => 'Codice usato da sistemi esterni (es. Abbott)', 'en' => 'Code used by external systems (e.g., Abbott)'],
    'Remove assignment' => ['it' => 'Rimuovi assegnazione', 'en' => 'Remove assignment'],

    // ==========================================================================
    // Batches
    // ==========================================================================
    'Batches' => ['it' => 'Lotti QC', 'en' => 'Batches'],
    'batches' => ['it' => 'lotti', 'en' => 'batches'],
    'New Batch' => ['it' => 'Nuovo Lotto', 'en' => 'New Batch'],
    'Edit Batch' => ['it' => 'Modifica Lotto', 'en' => 'Edit Batch'],
    'Batch created successfully' => ['it' => 'Lotto creato con successo', 'en' => 'Batch created successfully'],
    'Batch updated successfully' => ['it' => 'Lotto aggiornato con successo', 'en' => 'Batch updated successfully'],
    'No batches found.' => ['it' => 'Nessun lotto trovato.', 'en' => 'No batches found.'],
    'Workstation, Assay and Control are required' => ['it' => 'Workstation, Assay e Controllo sono obbligatori', 'en' => 'Workstation, Assay and Control are required'],
    'Lot number is required' => ['it' => 'Il numero lotto è obbligatorio', 'en' => 'Lot number is required'],
    'Target and SD must be greater than zero' => ['it' => 'Target e SD devono essere maggiori di zero', 'en' => 'Target and SD must be greater than zero'],
    'Search lot, test...' => ['it' => 'Cerca lotto, test...', 'en' => 'Search lot, test...'],
    'All Workstations' => ['it' => 'Tutte le Workstations', 'en' => 'All Workstations'],
    'All Status' => ['it' => 'Tutti gli stati', 'en' => 'All Status'],
    'Lot' => ['it' => 'Lotto', 'en' => 'Lot'],
    'Lot Number' => ['it' => 'Numero Lotto', 'en' => 'Lot Number'],
    'Target' => ['it' => 'Target', 'en' => 'Target'],
    'SD' => ['it' => 'DS', 'en' => 'SD'],
    'Expiration' => ['it' => 'Scadenza', 'en' => 'Expiration'],
    'Expiration Date' => ['it' => 'Data Scadenza', 'en' => 'Expiration Date'],
    'Expired' => ['it' => 'Scaduto', 'en' => 'Expired'],
    'Results' => ['it' => 'Risultati', 'en' => 'Results'],
    'Control' => ['it' => 'Controllo', 'en' => 'Control'],
    'Select workstation first...' => ['it' => 'Seleziona prima la workstation...', 'en' => 'Select workstation first...'],
    'No assays assigned to this workstation' => ['it' => 'Nessun assay assegnato a questa workstation', 'en' => 'No assays assigned to this workstation'],
    'Error loading assays' => ['it' => 'Errore caricamento assay', 'en' => 'Error loading assays'],
    'Loading...' => ['it' => 'Caricamento...', 'en' => 'Loading...'],
    'SD Mode' => ['it' => 'Modalità DS', 'en' => 'SD Mode'],
    'Manual' => ['it' => 'Manuale', 'en' => 'Manual'],
    'Computed' => ['it' => 'Calcolato', 'en' => 'Computed'],
    'Lower Limit' => ['it' => 'Limite Inferiore', 'en' => 'Lower Limit'],
    'Upper Limit' => ['it' => 'Limite Superiore', 'en' => 'Upper Limit'],
    'Rank' => ['it' => 'Priorità', 'en' => 'Rank'],
    'Clear' => ['it' => 'Pulisci', 'en' => 'Clear'],
    'Select...' => ['it' => 'Seleziona...', 'en' => 'Select...'],
    'All required fields must be filled' => ['it' => 'Tutti i campi obbligatori devono essere compilati', 'en' => 'All required fields must be filled'],
    'Error loading data' => ['it' => 'Errore caricamento dati', 'en' => 'Error loading data'],
];

/**
 * Get current language from session or default
 */
function getCurrentLanguage() {
    // First check cookie (persistent preference)
    if (isset($_COOKIE['biovarase_lang']) && isset(LANGUAGES[$_COOKIE['biovarase_lang']])) {
        return $_COOKIE['biovarase_lang'];
    }
    // Fallback to session if exists
    if (session_status() !== PHP_SESSION_NONE && isset($_SESSION['language'])) {
        return $_SESSION['language'];
    }
    return DEFAULT_LANGUAGE;
}

/**
 * Set current language in session
 */
function setLanguage($lang) {
    if (isset(LANGUAGES[$lang])) {
        // Set cookie for 1 year
        setcookie('biovarase_lang', $lang, [
            'expires' => time() + (365 * 24 * 60 * 60),
            'path' => '/biovarase',
            'httponly' => true,
            'samesite' => 'Strict'
        ]);
        // Also set in session if active
        if (session_status() !== PHP_SESSION_NONE) {
            $_SESSION['language'] = $lang;
        }
        return true;
    }
    return false;
}

/**
 * Translate a string
 *
 * Note: We use t() instead of _() to avoid conflict with PHP gettext extension
 *
 * @param string $key The string to translate (English version)
 * @return string Translated string, or key itself if not found
 */
function t($key) {
    global $TRANSLATIONS;
    $lang = getCurrentLanguage();

    if (isset($TRANSLATIONS[$key])) {
        return isset($TRANSLATIONS[$key][$lang]) ? $TRANSLATIONS[$key][$lang] : $key;
    }
    return $key;
}

/**
 * Translate with parameters (printf style)
 *
 * @param string $key The string to translate
 * @param mixed ...$args Arguments for sprintf
 * @return string Translated and formatted string
 */
function tf($key, ...$args) {
    $translated = t($key);
    if (!empty($args)) {
        return sprintf($translated, ...$args);
    }
    return $translated;
}

/**
 * Get available languages
 */
function getAvailableLanguages() {
    return LANGUAGES;
}
