# -*- coding: utf-8 -*-
"""
Internationalization Module for Biovarase.

Provides translation support for English and Italian.

Author: 1966bc (Giuseppe Costanzi)
License: GNU GPL v3
"""

# Available languages
LANGUAGES = {
    "en": "English",
    "it": "Italiano",
}

# Default language
DEFAULT_LANGUAGE = "en"

# Translation dictionary
# Key = English (default), Value = dict with translations
TRANSLATIONS = {
    # ==========================================================================
    # Common Buttons
    # ==========================================================================
    "Save": {"it": "Salva", "en": "Save"},
    "Cancel": {"it": "Annulla", "en": "Cancel"},
    "Close": {"it": "Chiudi", "en": "Close"},
    "New": {"it": "Nuovo", "en": "New"},
    "Edit": {"it": "Modifica", "en": "Edit"},
    "Delete": {"it": "Elimina", "en": "Delete"},
    "Add": {"it": "Aggiungi", "en": "Add"},
    "Remove": {"it": "Rimuovi", "en": "Remove"},
    "Load": {"it": "Carica", "en": "Load"},
    "Loading...": {"it": "Caricamento...", "en": "Loading..."},
    "Validating...": {"it": "Validazione...", "en": "Validating..."},
    "Next update": {"it": "Prossimo aggiornamento", "en": "Next update"},
    "Reset": {"it": "Reimposta", "en": "Reset"},
    "Apply": {"it": "Applica", "en": "Apply"},
    "OK": {"it": "OK", "en": "OK"},
    "Yes": {"it": "Sì", "en": "Yes"},
    "No": {"it": "No", "en": "No"},
    "Login": {"it": "Accedi", "en": "Login"},
    "Logout": {"it": "Esci", "en": "Logout"},
    "Unassigned": {"it": "Non assegnato", "en": "Unassigned"},

    # ==========================================================================
    # Common Labels
    # ==========================================================================
    "Description:": {"it": "Descrizione:", "en": "Description:"},
    "Code:": {"it": "Codice:", "en": "Code:"},
    "Name:": {"it": "Nome:", "en": "Name:"},
    "Status:": {"it": "Stato:", "en": "Status:"},
    "Date:": {"it": "Data:", "en": "Date:"},
    "Note:": {"it": "Nota:", "en": "Note:"},
    "Notes:": {"it": "Note:", "en": "Notes:"},
    "Result:": {"it": "Risultato:", "en": "Result:"},
    "Target:": {"it": "Target:", "en": "Target:"},
    "SD:": {"it": "DS:", "en": "SD:"},
    "CV%:": {"it": "CV%:", "en": "CV%:"},
    "Expiration:": {"it": "Scadenza:", "en": "Expiration:"},
    "Level:": {"it": "Livello:", "en": "Level:"},
    "Unit:": {"it": "Unità:", "en": "Unit:"},
    "Enable": {"it": "Attivo", "en": "Enable"},
    "Enabled": {"it": "Attivo", "en": "Enabled"},
    "Disabled": {"it": "Disattivo", "en": "Disabled"},

    # ==========================================================================
    # Login Window
    # ==========================================================================
    "Username:": {"it": "Utente:", "en": "Username:"},
    "Password:": {"it": "Password:", "en": "Password:"},
    "Remember me": {"it": "Ricordami", "en": "Remember me"},
    "Auto login": {"it": "Accesso automatico", "en": "Auto login"},
    "Invalid credentials.": {"it": "Credenziali non valide.", "en": "Invalid credentials."},
    "Login failed.": {"it": "Accesso fallito.", "en": "Login failed."},
    "User not found.": {"it": "Utente non trovato.", "en": "User not found."},
    "Account disabled.": {"it": "Account disabilitato.", "en": "Account disabled."},
    "Maximum login attempts exceeded.": {
        "it": "Numero massimo di tentativi di accesso superato.",
        "en": "Maximum login attempts exceeded."
    },

    # ==========================================================================
    # Menu - File
    # ==========================================================================
    "File": {"it": "File", "en": "File"},
    "Exit": {"it": "Esci", "en": "Exit"},
    "Do you want to quit": {"it": "Vuoi uscire da", "en": "Do you want to quit"},
    "Do you want to quit {app_name}?": {"it": "Vuoi uscire da {app_name}?", "en": "Do you want to quit {app_name}?"},
    "Change User": {"it": "Cambia Utente", "en": "Change User"},
    "Change Section": {"it": "Cambia Sezione", "en": "Change Section"},
    "Change Laboratory": {"it": "Cambia Laboratorio", "en": "Change Laboratory"},
    "Same Laboratory": {"it": "Stesso Laboratorio", "en": "Same Laboratory"},
    "Already in this laboratory.": {"it": "Sei già in questo laboratorio.", "en": "Already in this laboratory."},
    "Laboratory Changed": {"it": "Laboratorio Cambiato", "en": "Laboratory Changed"},
    "Only administrators can change laboratory.": {"it": "Solo gli amministratori possono cambiare laboratorio.", "en": "Only administrators can change laboratory."},
    "Failed to change laboratory:": {"it": "Impossibile cambiare laboratorio:", "en": "Failed to change laboratory:"},
    "Log": {"it": "Log", "en": "Log"},
    "Analytica": {"it": "Analitici", "en": "Analytica"},
    "Insert random results": {"it": "Inserisci risultati casuali", "en": "Insert random results"},

    # ==========================================================================
    # Menu - Edit
    # ==========================================================================
    "Settings": {"it": "Impostazioni", "en": "Settings"},
    "Preferences": {"it": "Preferenze", "en": "Preferences"},
    "Daily Validation": {"it": "Validazione Giornaliera", "en": "Daily Validation"},
    "Batches": {"it": "Lotti", "en": "Batches"},
    "Test Methods": {"it": "Test Laboratorio", "en": "Laboratory Tests"},
    "Tests Methods Workstations": {"it": "Test Postazioni", "en": "Workstation Tests"},
    "Set Observations": {"it": "Imposta Osservazioni", "en": "Set Observations"},
    "Set Z Score": {"it": "Imposta Z Score", "en": "Set Z Score"},

    # ==========================================================================
    # Menu - Admin
    # ==========================================================================
    "Admin": {"it": "Admin", "en": "Admin"},
    "Users": {"it": "Utenti", "en": "Users"},
    "Organizations": {"it": "Organizzazioni", "en": "Organizations"},
    "Organizations Management": {"it": "Gestione Organizzazioni", "en": "Organizations Management"},
    "Organization": {"it": "Organizzazione", "en": "Organization"},
    "Add Organization": {"it": "Aggiungi Organizzazione", "en": "Add Organization"},
    "Update Organization": {"it": "Modifica Organizzazione", "en": "Update Organization"},
    "Add Child": {"it": "Aggiungi Figlio", "en": "Add Child"},
    "Expand All": {"it": "Espandi Tutto", "en": "Expand All"},
    "Collapse All": {"it": "Comprimi Tutto", "en": "Collapse All"},
    "Parent:": {"it": "Padre:", "en": "Parent:"},
    "Type:": {"it": "Tipo:", "en": "Type:"},
    "(Root)": {"it": "(Radice)", "en": "(Root)"},
    "(Global - App Admin)": {"it": "(Globale - App Admin)", "en": "(Global - App Admin)"},
    "Country": {"it": "Paese", "en": "Country"},
    "Region": {"it": "Regione", "en": "Region"},
    "Site": {"it": "Ospedale", "en": "Site"},
    "Lab": {"it": "Laboratorio", "en": "Lab"},
    "Section": {"it": "Sezione", "en": "Section"},
    "Select a parent organization first.": {
        "it": "Seleziona prima un'organizzazione padre.",
        "en": "Select a parent organization first."
    },
    "This organization type cannot have children.": {
        "it": "Questo tipo di organizzazione non può avere figli.",
        "en": "This organization type cannot have children."
    },
    "Cannot delete: organization has children. Delete children first.": {
        "it": "Impossibile eliminare: l'organizzazione ha figli. Elimina prima i figli.",
        "en": "Cannot delete: organization has children. Delete children first."
    },
    "Select a type.": {"it": "Seleziona un tipo.", "en": "Select a type."},
    "Description is mandatory.": {"it": "La descrizione è obbligatoria.", "en": "Description is mandatory."},
    "Sites": {"it": "Siti", "en": "Sites"},
    "Sites Management": {"it": "Gestione Siti", "en": "Sites Management"},
    "Labs": {"it": "Laboratori", "en": "Labs"},
    "Sections": {"it": "Sezioni", "en": "Sections"},
    "Equipments": {"it": "Strumenti", "en": "Equipments"},
    "Workstations": {"it": "Postazioni", "en": "Workstations"},
    "Controls": {"it": "Controlli", "en": "Controls"},
    "Suppliers": {"it": "Fornitori", "en": "Suppliers"},
    "Methods": {"it": "Metodi", "en": "Methods"},
    "Units": {"it": "Unità", "en": "Units"},
    "Samples": {"it": "Campioni", "en": "Samples"},
    "Actions": {"it": "Azioni", "en": "Actions"},
    "Categories": {"it": "Categorie", "en": "Categories"},
    "Tests": {"it": "Test", "en": "Tests"},

    # ==========================================================================
    # Menu - QC (Quality Control)
    # ==========================================================================
    "QC": {"it": "QC", "en": "QC"},
    "Plots": {"it": "Grafici", "en": "Plots"},
    "Levey-Jennings": {"it": "Levey-Jennings", "en": "Levey-Jennings"},
    "Total Error": {"it": "Errore Totale", "en": "Total Error"},
    "Youden Plot": {"it": "Grafico Youden", "en": "Youden Plot"},
    "Youden": {"it": "Youden", "en": "Youden"},
    "Tea": {"it": "TEa", "en": "Tea"},

    # Youden Selector Dialog
    "Select Batches for Youden Plot": {"it": "Seleziona Lotti per Grafico Youden", "en": "Select Batches for Youden Plot"},
    "Level 1:": {"it": "Livello 1:", "en": "Level 1:"},
    "Level 2:": {"it": "Livello 2:", "en": "Level 2:"},
    "Plot": {"it": "Grafico", "en": "Plot"},
    "Please select a workstation.": {"it": "Selezionare una postazione.", "en": "Please select a workstation."},
    "Please select a test.": {"it": "Selezionare un test.", "en": "Please select a test."},
    "Please select both Level 1 and Level 2 batches.": {"it": "Selezionare entrambi i lotti Livello 1 e Livello 2.", "en": "Please select both Level 1 and Level 2 batches."},

    # ==========================================================================
    # Menu - Documents
    # ==========================================================================
    "Documents": {"it": "Documenti", "en": "Documents"},
    "Reports": {"it": "Report", "en": "Reports"},
    "Export": {"it": "Esporta", "en": "Export"},
    "Import": {"it": "Importa", "en": "Import"},
    "User Manual": {"it": "Manuale Utente", "en": "User Manual"},
    "QC Technical Manual": {"it": "Manuale Tecnico QC", "en": "QC Technical Manual"},
    "Guidelines": {"it": "Linee Guida", "en": "Guidelines"},
    "Biological Values": {"it": "Valori Biologici", "en": "Biological Values"},

    # ==========================================================================
    # Menu - Imports/Exports
    # ==========================================================================
    "Imports": {"it": "Importazioni", "en": "Imports"},
    "Exports": {"it": "Esportazioni", "en": "Exports"},
    "Notes": {"it": "Note", "en": "Notes"},
    "Analytical Goals": {"it": "Obiettivi Analitici", "en": "Analytical Goals"},
    "Counts": {"it": "Conteggi", "en": "Counts"},

    # ==========================================================================
    # Menu - Help
    # ==========================================================================
    "Help": {"it": "Aiuto", "en": "Help"},
    "About": {"it": "Informazioni", "en": "About"},
    "License": {"it": "Licenza", "en": "License"},
    "Language": {"it": "Lingua", "en": "Language"},
    "Python": {"it": "Python", "en": "Python"},
    "Tkinter": {"it": "Tkinter", "en": "Tkinter"},

    # ==========================================================================
    # Status Bar
    # ==========================================================================
    "Site:": {"it": "Sito:", "en": "Site:"},
    "Lab:": {"it": "Lab:", "en": "Lab:"},
    "Observations:": {"it": "Osservazioni:", "en": "Observations:"},
    "Z Score:": {"it": "Z Score:", "en": "Z Score:"},
    "Delta Degree of Freedom": {"it": "Delta Gradi di Libertà", "en": "Delta Degree of Freedom"},
    "Show Expired": {"it": "Mostra Scaduti", "en": "Show Expired"},
    "Recent Only": {"it": "Solo Recenti", "en": "Recent Only"},

    # ==========================================================================
    # Main Window
    # ==========================================================================
    "Tests": {"it": "Test", "en": "Tests"},
    "Results": {"it": "Risultati", "en": "Results"},
    "Workstation Data Source": {"it": "Sorgente Dati Postazione", "en": "Workstation Data Source"},
    "Liv": {"it": "Liv", "en": "Lv"},
    "SD": {"it": "DS", "en": "SD"},
    "TE%": {"it": "TE%", "en": "TE%"},
    "sd": {"it": "ds", "en": "sd"},
    "CV%": {"it": "CV%", "en": "CV%"},
    "QC": {"it": "QC", "en": "QC"},
    "Bias%": {"it": "Bias%", "en": "Bias%"},
    "U": {"it": "U", "en": "U"},
    "Westgard": {"it": "Westgard", "en": "Westgard"},
    "Control": {"it": "Controllo", "en": "Control"},
    "Control:": {"it": "Controllo:", "en": "Control:"},
    "Lot": {"it": "Lotto", "en": "Lot"},
    "Lot:": {"it": "Lotto:", "en": "Lot:"},
    "Workstation": {"it": "Postazione", "en": "Workstation"},
    "Workstation:": {"it": "Postazione:", "en": "Workstation:"},
    "Equipment": {"it": "Strumento", "en": "Equipment"},
    "Equipment:": {"it": "Strumento:", "en": "Equipment:"},
    "Section": {"it": "Sezione", "en": "Section"},
    "Section:": {"it": "Sezione:", "en": "Section:"},
    "Site": {"it": "Sito", "en": "Site"},
    "Site:": {"it": "Sito:", "en": "Site:"},
    "Company:": {"it": "Azienda:", "en": "Company:"},
    "Update Site": {"it": "Modifica Sito", "en": "Update Site"},
    "Add Site": {"it": "Aggiungi Sito", "en": "Add Site"},
    "Select a Company.": {"it": "Selezionare un'Azienda.", "en": "Select a Company."},
    "Select a Site.": {"it": "Selezionare un Sito.", "en": "Select a Site."},
    "Save error:": {"it": "Errore salvataggio:", "en": "Save error:"},
    "Lab": {"it": "Laboratorio", "en": "Lab"},
    "Lab:": {"it": "Laboratorio:", "en": "Lab:"},
    "Labs:": {"it": "Laboratori:", "en": "Labs:"},
    "Laboratories": {"it": "Laboratori", "en": "Laboratories"},
    "Labs Management": {"it": "Gestione Laboratori", "en": "Labs Management"},
    "Hospital:": {"it": "Ospedale:", "en": "Hospital:"},
    "Manager:": {"it": "Responsabile:", "en": "Manager:"},
    "Laboratory:": {"it": "Laboratorio:", "en": "Laboratory:"},
    "Laboratory": {"it": "Laboratorio", "en": "Laboratory"},
    "(Admin)": {"it": "(Admin)", "en": "(Admin)"},
    "(No laboratory - Admin)": {"it": "(Nessun laboratorio - Admin)", "en": "(No laboratory - Admin)"},
    "Update Lab": {"it": "Modifica Laboratorio", "en": "Update Lab"},
    "Add Lab": {"it": "Aggiungi Laboratorio", "en": "Add Lab"},
    "Select a Hospital.": {"it": "Selezionare un Ospedale.", "en": "Select a Hospital."},
    "Select a Manager.": {"it": "Selezionare un Responsabile.", "en": "Select a Manager."},
    "Select a Lab.": {"it": "Selezionare un Laboratorio.", "en": "Select a Lab."},
    "Sections Management": {"it": "Gestione Sezioni", "en": "Sections Management"},
    "Update Section": {"it": "Modifica Sezione", "en": "Update Section"},
    "Add Section": {"it": "Aggiungi Sezione", "en": "Add Section"},
    "Set It": {"it": "Imposta", "en": "Set It"},
    "Suppliers:": {"it": "Fornitori:", "en": "Suppliers:"},
    "Update Equipment": {"it": "Modifica Strumento", "en": "Update Equipment"},
    "Add Equipment": {"it": "Aggiungi Strumento", "en": "Add Equipment"},
    "Not Assigned": {"it": "Non assegnato", "en": "Not Assigned"},
    "Database error:": {"it": "Errore database:", "en": "Database error:"},
    "already exists!": {"it": "già esiste!", "en": "already exists!"},

    # ==========================================================================
    # Samples Management
    # ==========================================================================
    "Samples Management": {"it": "Gestione Campioni", "en": "Samples Management"},
    "Symbol:": {"it": "Simbolo:", "en": "Symbol:"},
    "Symbol": {"it": "Simbolo", "en": "Symbol"},
    "Update Sample": {"it": "Modifica Campione", "en": "Update Sample"},
    "Add Sample": {"it": "Aggiungi Campione", "en": "Add Sample"},
    "has already been assigned!": {"it": "è già stato assegnato!", "en": "has already been assigned!"},
    "Description is required.": {"it": "Descrizione obbligatoria.", "en": "Description is required."},

    # ==========================================================================
    # Analytical Goals
    # ==========================================================================
    "To export:": {"it": "Da esportare:", "en": "To export:"},
    "Cannot load Test Method:": {"it": "Impossibile caricare Metodo Test:", "en": "Cannot load Test Method:"},
    "Update Analytical Goal for": {"it": "Modifica Obiettivo Analitico per", "en": "Update Analytical Goal for"},
    "Add Analytical Goal for": {"it": "Aggiungi Obiettivo Analitico per", "en": "Add Analytical Goal for"},
    "Analytical Goals Explained": {"it": "Obiettivi Analitici Spiegati", "en": "Analytical Goals Explained"},
    "Total Error (TEa):": {"it": "Errore Totale (TEa):", "en": "Total Error (TEa):"},

    # ==========================================================================
    # Observations
    # ==========================================================================
    "Observations": {"it": "Osservazioni", "en": "Observations"},
    "Set observations": {"it": "Imposta osservazioni", "en": "Set observations"},
    "Please enter a valid integer.": {"it": "Inserire un numero intero valido.", "en": "Please enter a valid integer."},

    # ==========================================================================
    # Z-score Settings
    # ==========================================================================
    "Set z-score": {"it": "Imposta z-score", "en": "Set z-score"},
    "Set Z-score": {"it": "Imposta Z-score", "en": "Set Z-score"},
    "Please enter a valid number.": {"it": "Inserire un numero valido.", "en": "Please enter a valid number."},

    # ==========================================================================
    # Export Counts
    # ==========================================================================
    "Export from:": {"it": "Esporta dal:", "en": "Export from:"},
    "Export Counts": {"it": "Esporta Conteggi", "en": "Export Counts"},
    "Export data?": {"it": "Esportare i dati?", "en": "Export data?"},

    # ==========================================================================
    # License
    # ==========================================================================
    "License - GNU GPL v3": {"it": "Licenza - GNU GPL v3", "en": "License - GNU GPL v3"},

    # ==========================================================================
    # Analytical Goals Export
    # ==========================================================================
    "Analytical Goals": {"it": "Obiettivi Analitici", "en": "Analytical Goals"},
    "Set elements to export:": {"it": "Imposta elementi da esportare:", "en": "Set elements to export:"},
    "No record data to compute.": {"it": "Nessun dato da elaborare.", "en": "No record data to compute."},

    # ==========================================================================
    # Export Notes
    # ==========================================================================
    "Export Notes Data": {"it": "Esporta Dati Note", "en": "Export Notes Data"},
    "Export error:": {"it": "Errore esportazione:", "en": "Export error:"},

    # ==========================================================================
    # Quality Control Plots
    # ==========================================================================
    "Quality Control Plots": {"it": "Grafici Controllo Qualità", "en": "Quality Control Plots"},
    "Serial": {"it": "Seriale", "en": "Serial"},
    "No batches available for this test.": {"it": "Nessun lotto disponibile per questo test.", "en": "No batches available for this test."},
    "No data available": {"it": "Nessun dato disponibile", "en": "No data available"},
    "No series available": {"it": "Nessuna serie disponibile", "en": "No series available"},
    "Computed": {"it": "Calcolato", "en": "Computed"},
    "on": {"it": "su", "en": "on"},
    "results": {"it": "risultati", "en": "results"},
    "paired results": {"it": "risultati accoppiati", "en": "paired results"},

    # ==========================================================================
    # Z-Score, Youden, TEA Windows
    # ==========================================================================
    "Z-Score, P-Value, Probability": {"it": "Z-Score, P-Value, Probabilità", "en": "Z-Score, P-Value, Probability"},
    "Youden Plot": {"it": "Grafico Youden", "en": "Youden Plot"},
    "Total Error": {"it": "Errore Totale", "en": "Total Error"},
    "Test:": {"it": "Test:", "en": "Test:"},
    "Workstation:": {"it": "Postazione:", "en": "Workstation:"},
    "Serial:": {"it": "Seriale:", "en": "Serial:"},

    # ==========================================================================
    # Assign Test Methods
    # ==========================================================================
    "Assign test methods": {"it": "Assegna metodi test", "en": "Assign test methods"},
    "Assign test methods to": {"it": "Assegna metodi test a", "en": "Assign test methods to"},
    "Assign test method:": {"it": "Assegnare metodo test:", "en": "Assign test method:"},
    "to workstation:": {"it": "alla postazione:", "en": "to workstation:"},
    "Assign error:": {"it": "Errore assegnazione:", "en": "Assign error:"},

    # ==========================================================================
    # QC Import
    # ==========================================================================
    "Import QC": {"it": "Importa QC", "en": "Import QC"},
    "Received:": {"it": "Ricevuto:", "en": "Received:"},
    "Date": {"it": "Data", "en": "Date"},
    "Reagent Lot:": {"it": "Lotto Reagente:", "en": "Reagent Lot:"},
    "Select workstation and optionally enter reagent lot.": {"it": "Seleziona postazione e opzionalmente inserisci lotto reagente.", "en": "Select workstation and optionally enter reagent lot."},
    "File can have any name (no renaming required).": {"it": "Il file può avere qualsiasi nome (nessuna rinomina richiesta).", "en": "File can have any name (no renaming required)."},
    "Import file…": {"it": "Importa file…", "en": "Import file…"},
    "Select QC file": {"it": "Seleziona file QC", "en": "Select QC file"},
    "QC files": {"it": "File QC", "en": "QC files"},
    "All files": {"it": "Tutti i file", "en": "All files"},
    "Houston we have a problem here.": {"it": "Houston abbiamo un problema.", "en": "Houston we have a problem here."},
    "Something went wrong or you did not select a valid file.": {"it": "Qualcosa è andato storto o non hai selezionato un file valido.", "en": "Something went wrong or you did not select a valid file."},
    "Invalid 'Received' date.": {"it": "Data 'Ricevuto' non valida.", "en": "Invalid 'Received' date."},
    "Please select a workstation.": {"it": "Selezionare una postazione.", "en": "Please select a workstation."},
    "Profile": {"it": "Profilo", "en": "Profile"},
    "Imported rows": {"it": "Righe importate", "en": "Imported rows"},
    "Matched batches": {"it": "Lotti abbinati", "en": "Matched batches"},
    "Unmatched rows": {"it": "Righe non abbinate", "en": "Unmatched rows"},
    "Unexpected error while importing QC file.": {"it": "Errore imprevisto durante importazione file QC.", "en": "Unexpected error while importing QC file."},

    # ==========================================================================
    # Workstation Test Methods Mapping
    # ==========================================================================
    "Workstations — Test Methods Mapping": {"it": "Postazioni — Mappatura Test Laboratorio", "en": "Workstations — Laboratory Tests Mapping"},
    "Edit External Code": {"it": "Modifica Codice Esterno", "en": "Edit External Code"},
    "Remove Mapping": {"it": "Rimuovi Mappatura", "en": "Remove Mapping"},
    "External Code": {"it": "Codice Esterno", "en": "External Code"},
    "from workstation": {"it": "dalla postazione", "en": "from workstation"},
    "External code for": {"it": "Codice esterno per", "en": "External code for"},

    # ==========================================================================
    # Equipments / Test Methods
    # ==========================================================================
    "Equipments": {"it": "Strumenti", "en": "Equipments"},
    "Equipments Management": {"it": "Gestione Strumenti", "en": "Equipments Management"},
    "Items": {"it": "Elementi", "en": "Items"},
    "is required.": {"it": "è richiesto.", "en": "is required."},
    "Category:": {"it": "Categoria:", "en": "Category:"},
    "Sample:": {"it": "Campione:", "en": "Sample:"},
    "Method:": {"it": "Metodo:", "en": "Method:"},
    "Mandatory:": {"it": "Obbligatorio:", "en": "Mandatory:"},
    "Methods": {"it": "Metodi", "en": "Methods"},
    "Tests": {"it": "Test", "en": "Tests"},
    "Goals": {"it": "Obiettivi", "en": "Goals"},
    "Update method for": {"it": "Modifica metodo per", "en": "Update method for"},
    "Add method for": {"it": "Aggiungi metodo per", "en": "Add method for"},
    "Select a": {"it": "Selezionare", "en": "Select a"},
    "Code is required.": {"it": "Codice richiesto.", "en": "Code is required."},
    "Select a Test Method.": {"it": "Selezionare un Metodo Test.", "en": "Select a Test Method."},
    "Category": {"it": "Categoria", "en": "Category"},
    "Sample": {"it": "Campione", "en": "Sample"},
    "Method": {"it": "Metodo", "en": "Method"},
    "Unit": {"it": "Unità", "en": "Unit"},

    # ==========================================================================
    # Batch Window
    # ==========================================================================
    "Batch": {"it": "Lotto", "en": "Batch"},
    "Lot Number": {"it": "Numero Lotto", "en": "Lot Number"},
    "Lot Number:": {"it": "Numero Lotto:", "en": "Lot Number:"},
    "Expiration Date": {"it": "Data Scadenza", "en": "Expiration Date"},
    "Expiration Date:": {"it": "Data Scadenza:", "en": "Expiration Date:"},
    "Remember data": {"it": "Ricorda dati", "en": "Remember data"},
    "Lower:": {"it": "Inferiore:", "en": "Lower:"},
    "Upper:": {"it": "Superiore:", "en": "Upper:"},
    "Rank:": {"it": "Ordine:", "en": "Rank:"},
    "SD mode": {"it": "Modalità DS", "en": "SD mode"},
    "Manual": {"it": "Manuale", "en": "Manual"},
    "Computed": {"it": "Calcolato", "en": "Computed"},
    "Missing context: test method or workstation.": {
        "it": "Contesto mancante: metodo test o postazione.",
        "en": "Missing context: test method or workstation."
    },
    "Test not found.": {"it": "Test non trovato.", "en": "Test not found."},
    "Batch not found.": {"it": "Lotto non trovato.", "en": "Batch not found."},
    "Date format error.": {"it": "Errore formato data.", "en": "Date format error."},
    "Please check the expiration date.": {
        "it": "Verificare la data di scadenza.",
        "en": "Please check the expiration date."
    },
    "Save failed.": {"it": "Salvataggio fallito.", "en": "Save failed."},
    "Delete failed.": {"it": "Eliminazione fallita.", "en": "Delete failed."},
    "The entered value is too long.": {
        "it": "Il valore inserito è troppo lungo.",
        "en": "The entered value is too long."
    },
    "A required field is empty.": {
        "it": "Un campo obbligatorio è vuoto.",
        "en": "A required field is empty."
    },
    "A record with this value already exists.": {
        "it": "Esiste già un record con questo valore.",
        "en": "A record with this value already exists."
    },
    "Cannot delete: this record is referenced by other data.": {
        "it": "Impossibile eliminare: questo record è referenziato da altri dati.",
        "en": "Cannot delete: this record is referenced by other data."
    },
    "Lower value exceeds upper value.": {
        "it": "Il valore inferiore supera il valore superiore.",
        "en": "Lower value exceeds upper value."
    },
    "Cannot compute SD.": {"it": "Impossibile calcolare DS.", "en": "Cannot compute SD."},

    # ==========================================================================
    # Result Window
    # ==========================================================================
    "Received:": {"it": "Ricevuto:", "en": "Received:"},
    "Test:": {"it": "Test:", "en": "Test:"},
    "Batch:": {"it": "Lotto:", "en": "Batch:"},
    "Reagent Lot:": {"it": "Lotto Reagente:", "en": "Reagent Lot:"},
    "Please enter a valid received date.": {
        "it": "Inserire una data di ricezione valida.",
        "en": "Please enter a valid received date."
    },
    "Validated": {"it": "Validato", "en": "Validated"},
    "Not validated": {"it": "Non validato", "en": "Not validated"},

    # ==========================================================================
    # Daily Validation
    # ==========================================================================
    "Daily QC Validation": {"it": "Validazione QC Giornaliera", "en": "Daily QC Validation"},
    "Validation": {"it": "Validazione", "en": "Validation"},
    "Validate": {"it": "Valida", "en": "Validate"},
    "Invalidate": {"it": "Invalida", "en": "Invalidate"},
    "Approve": {"it": "Approva", "en": "Approve"},
    "Approved": {"it": "Approvato", "en": "Approved"},
    "Pending": {"it": "In attesa", "en": "Pending"},
    "History": {"it": "Storico", "en": "History"},

    # ==========================================================================
    # User Management
    # ==========================================================================
    "User": {"it": "Utente", "en": "User"},
    "Role": {"it": "Ruolo", "en": "Role"},
    "Role:": {"it": "Ruolo:", "en": "Role:"},
    "Administrator": {"it": "Amministratore", "en": "Administrator"},
    "Superuser": {"it": "Supervisore", "en": "Superuser"},
    "Technician": {"it": "Tecnico", "en": "Technician"},
    "Guest": {"it": "Ospite", "en": "Guest"},
    "Change Password": {"it": "Cambia Password", "en": "Change Password"},
    "Old Password:": {"it": "Vecchia Password:", "en": "Old Password:"},
    "New Password:": {"it": "Nuova Password:", "en": "New Password:"},
    "Confirm Password:": {"it": "Conferma Password:", "en": "Confirm Password:"},
    "Passwords do not match.": {"it": "Le password non coincidono.", "en": "Passwords do not match."},
    "Password changed successfully.": {"it": "Password cambiata con successo.", "en": "Password changed successfully."},
    "Current password is incorrect.": {"it": "La password attuale non è corretta.", "en": "Current password is incorrect."},
    "Password must be at least 8 characters.": {
        "it": "La password deve essere di almeno 8 caratteri.",
        "en": "Password must be at least 8 characters."
    },
    "Surname:": {"it": "Cognome:", "en": "Surname:"},
    "First Name:": {"it": "Nome:", "en": "First Name:"},
    "Nick:": {"it": "Nick:", "en": "Nick:"},
    "Logout time (min):": {"it": "Tempo logout (min):", "en": "Logout time (min):"},
    "Enable logout:": {"it": "Abilita logout:", "en": "Enable logout:"},
    "Update User": {"it": "Modifica Utente", "en": "Update User"},
    "Add User": {"it": "Aggiungi Utente", "en": "Add User"},
    "Password reset.": {"it": "Password reimpostata.", "en": "Password reset."},
    "No user selected.": {"it": "Nessun utente selezionato.", "en": "No user selected."},
    "This nickname is already in use.": {"it": "Questo nickname è già in uso.", "en": "This nickname is already in use."},
    "Modified": {"it": "Modificato", "en": "Modified"},

    # ==========================================================================
    # Westgard Rules
    # ==========================================================================
    "Westgard Rules": {"it": "Regole di Westgard", "en": "Westgard Rules"},
    "Rule Violation": {"it": "Violazione Regola", "en": "Rule Violation"},
    "Warning": {"it": "Attenzione", "en": "Warning"},
    "Out of control": {"it": "Fuori controllo", "en": "Out of control"},

    # ==========================================================================
    # Common Messages
    # ==========================================================================
    "Error": {"it": "Errore", "en": "Error"},
    "Warning": {"it": "Attenzione", "en": "Warning"},
    "Information": {"it": "Informazione", "en": "Information"},
    "Confirm": {"it": "Conferma", "en": "Confirm"},
    "Success": {"it": "Operazione completata", "en": "Success"},
    "Failed": {"it": "Operazione fallita", "en": "Failed"},
    "No data": {"it": "Nessun dato", "en": "No data"},
    "No selection": {"it": "Nessuna selezione", "en": "No selection"},
    "Please select an item.": {"it": "Selezionare un elemento.", "en": "Please select an item."},
    "Please select a batch.": {"it": "Selezionare un lotto.", "en": "Please select a batch."},
    "Please select a result.": {"it": "Selezionare un risultato.", "en": "Please select a result."},
    "Please select a test.": {"it": "Selezionare un test.", "en": "Please select a test."},
    "Please select a workstation.": {"it": "Selezionare una postazione.", "en": "Please select a workstation."},
    "Please select a section.": {"it": "Selezionare una sezione.", "en": "Please select a section."},
    "Are you sure?": {"it": "Sei sicuro?", "en": "Are you sure?"},
    "Do you want to save changes?": {"it": "Vuoi salvare le modifiche?", "en": "Do you want to save changes?"},
    "Do you want to delete this record?": {"it": "Vuoi eliminare questo record?", "en": "Do you want to delete this record?"},
    "Record saved successfully.": {"it": "Record salvato con successo.", "en": "Record saved successfully."},
    "Record deleted successfully.": {"it": "Record eliminato con successo.", "en": "Record deleted successfully."},
    "Operation completed.": {"it": "Operazione completata.", "en": "Operation completed."},
    "Operation failed.": {"it": "Operazione fallita.", "en": "Operation failed."},
    "Invalid data.": {"it": "Dati non validi.", "en": "Invalid data."},
    "Required field.": {"it": "Campo obbligatorio.", "en": "Required field."},
    "Invalid date.": {"it": "Data non valida.", "en": "Invalid date."},
    "Invalid number.": {"it": "Numero non valido.", "en": "Invalid number."},
    "Validation error:": {"it": "Errore di validazione:", "en": "Validation error:"},

    # ==========================================================================
    # Language
    # ==========================================================================
    "Restart to apply language change.": {
        "it": "Riavviare l'applicazione per applicare il cambio lingua.",
        "en": "Restart to apply language change."
    },
    "Language changed.": {"it": "Lingua cambiata.", "en": "Language changed."},

    # ==========================================================================
    # Change User / Change Section Dialogs
    # ==========================================================================
    "Welcome": {"it": "Benvenuto", "en": "Welcome"},
    "Logged in as:": {"it": "Connesso come:", "en": "Logged in as:"},
    "Failed to change user:": {"it": "Cambio utente fallito:", "en": "Failed to change user:"},
    "Failed to change section:": {"it": "Cambio sezione fallito:", "en": "Failed to change section:"},
    "Logout and switch to different user?\n\nAll open windows will be closed.": {
        "it": "Disconnettersi e passare a un altro utente?\n\nTutte le finestre aperte verranno chiuse.",
        "en": "Logout and switch to different user?\n\nAll open windows will be closed."
    },
    "Select new section:": {"it": "Seleziona nuova sezione:", "en": "Select new section:"},
    "No Selection": {"it": "Nessuna Selezione", "en": "No Selection"},
    "Section Changed": {"it": "Sezione Cambiata", "en": "Section Changed"},
    "Now working in:": {"it": "Ora stai lavorando in:", "en": "Now working in:"},
    "Permission Denied": {"it": "Permesso Negato", "en": "Permission Denied"},
    "Read-only users cannot change section.": {
        "it": "Gli utenti in sola lettura non possono cambiare sezione.",
        "en": "Read-only users cannot change section."
    },
    "No Sections": {"it": "Nessuna Sezione", "en": "No Sections"},
    "No sections available for selection.": {
        "it": "Nessuna sezione disponibile per la selezione.",
        "en": "No sections available for selection."
    },
    "Same Section": {"it": "Stessa Sezione", "en": "Same Section"},
    "Already in this section.": {"it": "Già in questa sezione.", "en": "Already in this section."},

    # ==========================================================================
    # Status Bar and User Messages
    # ==========================================================================
    "Access Denied": {"it": "Accesso Negato", "en": "Access Denied"},

    # ==========================================================================
    # Result/Batch Error Messages
    # ==========================================================================
    "Result not found. Cannot edit.": {
        "it": "Risultato non trovato. Impossibile modificare.",
        "en": "Result not found. Cannot edit."
    },
    "Batch not found. Cannot edit result.": {
        "it": "Lotto non trovato. Impossibile modificare il risultato.",
        "en": "Batch not found. Cannot edit result."
    },
    "Test method not found. Cannot edit result.": {
        "it": "Metodo test non trovato. Impossibile modificare il risultato.",
        "en": "Test method not found. Cannot edit result."
    },
    "Result not found in list. Cannot edit.": {
        "it": "Risultato non trovato nella lista. Impossibile modificare.",
        "en": "Result not found in list. Cannot edit."
    },
    "Batch not found. Cannot add result.": {
        "it": "Lotto non trovato. Impossibile aggiungere il risultato.",
        "en": "Batch not found. Cannot add result."
    },
    "Test method not found.": {
        "it": "Metodo test non trovato.",
        "en": "Test method not found."
    },

    # ==========================================================================
    # Plot Error Messages
    # ==========================================================================
    "Not enough data to plot.\nSelect an instrument and a batch.": {
        "it": "Dati insufficienti per il grafico.\nSeleziona uno strumento e un lotto.",
        "en": "Not enough data to plot.\nSelect an instrument and a batch."
    },
    "Not enough data to plot.\nSelect a test.": {
        "it": "Dati insufficienti per il grafico.\nSeleziona un test.",
        "en": "Not enough data to plot.\nSelect a test."
    },
    "Not enough data to plot.\nSelect a batch.": {
        "it": "Dati insufficienti per il grafico.\nSeleziona un lotto.",
        "en": "Not enough data to plot.\nSelect a batch."
    },
    "Selected test is not enabled for this plot type.": {
        "it": "Il test selezionato non è abilitato per questo tipo di grafico.",
        "en": "Selected test is not enabled for this plot type."
    },
    "Not enough data to plot a Youden chart.\nYou need to select two batches.": {
        "it": "Dati insufficienti per il grafico Youden.\nDevi selezionare due lotti.",
        "en": "Not enough data to plot a Youden chart.\nYou need to select two batches."
    },
    "Youden plot requires exactly two batches.\nPlease select only two batches.": {
        "it": "Il grafico Youden richiede esattamente due lotti.\nSeleziona solo due lotti.",
        "en": "Youden plot requires exactly two batches.\nPlease select only two batches."
    },
    "Not enough data to plot a Youden chart.\nBoth selected batches must have at least one result.": {
        "it": "Dati insufficienti per il grafico Youden.\nEntrambi i lotti selezionati devono avere almeno un risultato.",
        "en": "Not enough data to plot a Youden chart.\nBoth selected batches must have at least one result."
    },

    # ==========================================================================
    # Attention Messages
    # ==========================================================================
    "Attention please.\nNo batch selected.": {
        "it": "Attenzione.\nNessun lotto selezionato.",
        "en": "Attention please.\nNo batch selected."
    },
    "Attention please.\nSelect a batch.": {
        "it": "Attenzione.\nSeleziona un lotto.",
        "en": "Attention please.\nSelect a batch."
    },
    "Attention please.\nBefore adding a result you must select a batch.": {
        "it": "Attenzione.\nPrima di aggiungere un risultato devi selezionare un lotto.",
        "en": "Attention please.\nBefore adding a result you must select a batch."
    },
    "Attention please.\nSelect a result.": {
        "it": "Attenzione.\nSeleziona un risultato.",
        "en": "Attention please.\nSelect a result."
    },
    "Insert 30 random results for:\n{0}\nbatch {1} {2}?": {
        "it": "Inserire 30 risultati casuali per:\n{0}\nlotto {1} {2}?",
        "en": "Insert 30 random results for:\n{0}\nbatch {1} {2}?"
    },

    # ==========================================================================
    # Read-only Mode Messages
    # ==========================================================================
    "Read-only mode.\nCannot add results.": {
        "it": "Modalità sola lettura.\nImpossibile aggiungere risultati.",
        "en": "Read-only mode.\nCannot add results."
    },
    "Read-only mode.\nCannot edit notes.": {
        "it": "Modalità sola lettura.\nImpossibile modificare le note.",
        "en": "Read-only mode.\nCannot edit notes."
    },

    # ==========================================================================
    # Document Error Messages
    # ==========================================================================
    "The file Biological Variation Values does not exist or cannot be opened.": {
        "it": "Il file Valori di Variazione Biologica non esiste o non può essere aperto.",
        "en": "The file Biological Variation Values does not exist or cannot be opened."
    },
    "The Biovarase User Manual does not exist or cannot be opened.": {
        "it": "Il Manuale Utente Biovarase non esiste o non può essere aperto.",
        "en": "The Biovarase User Manual does not exist or cannot be opened."
    },
    "The QC Technical Manual does not exist or cannot be opened.": {
        "it": "Il Manuale Tecnico QC non esiste o non può essere aperto.",
        "en": "The QC Technical Manual does not exist or cannot be opened."
    },
    "The Biovarase Guidelines file does not exist or cannot be opened.": {
        "it": "Il file Linee Guida Biovarase non esiste o non può essere aperto.",
        "en": "The Biovarase Guidelines file does not exist or cannot be opened."
    },

    # ==========================================================================
    # Daily Validation
    # ==========================================================================
    "Workstation / Test": {"it": "Postazione / Test", "en": "Workstation / Test"},
    "Equipment / Batch": {"it": "Strumento / Lotto", "en": "Equipment / Batch"},
    "Counts / Result": {"it": "Conteggi / Risultato", "en": "Counts / Result"},
    "Problems / Z-Score": {"it": "Problemi / Z-Score", "en": "Problems / Z-Score"},
    "Validation enabled": {"it": "Validazione abilitata", "en": "Validation enabled"},
    "View-only mode": {"it": "Modalità sola lettura", "en": "View-only mode"},
    "Please select a valid date.": {"it": "Seleziona una data valida.", "en": "Please select a valid date."},
    "Failed to load data:": {"it": "Caricamento dati fallito:", "en": "Failed to load data:"},
    "Problems": {"it": "Problemi", "en": "Problems"},
    "All validated": {"it": "Tutto validato", "en": "All validated"},
    "This result is already validated.": {
        "it": "Questo risultato è già validato.",
        "en": "This result is already validated."
    },
    "You don't have permission to approve.": {
        "it": "Non hai i permessi per approvare.",
        "en": "You don't have permission to approve."
    },
    "Please select a workstation.": {
        "it": "Seleziona una postazione.",
        "en": "Please select a workstation."
    },
    "This workstation is already approved for today.": {
        "it": "Questa postazione è già approvata per oggi.",
        "en": "This workstation is already approved for today."
    },
    "This workstation has {0} result(s) beyond ±3SD.\n\nAre you sure you want to approve it anyway?": {
        "it": "Questa postazione ha {0} risultato/i oltre ±3DS.\n\nSei sicuro di voler approvare comunque?",
        "en": "This workstation has {0} result(s) beyond ±3SD.\n\nAre you sure you want to approve it anyway?"
    },
    "Approve workstation '{0}'?": {"it": "Approvare la postazione '{0}'?", "en": "Approve workstation '{0}'?"},
    "\n\nThis will also validate {0} pending result(s).": {
        "it": "\n\nQuesto validerà anche {0} risultato/i in sospeso.",
        "en": "\n\nThis will also validate {0} pending result(s)."
    },
    "Confirm Approval": {"it": "Conferma Approvazione", "en": "Confirm Approval"},
    "Workstation '{0}' approved.": {"it": "Postazione '{0}' approvata.", "en": "Workstation '{0}' approved."},
    "Failed to approve:": {"it": "Approvazione fallita:", "en": "Failed to approve:"},
    "You don't have permission to validate.": {
        "it": "Non hai i permessi per validare.",
        "en": "You don't have permission to validate."
    },
    "Please select a result.": {"it": "Seleziona un risultato.", "en": "Please select a result."},
    "Failed to validate:": {"it": "Validazione fallita:", "en": "Failed to validate:"},
    "All Validated": {"it": "Tutto Validato", "en": "All Validated"},
    "All results for this workstation are now validated.\n\nApprove the workstation?": {
        "it": "Tutti i risultati per questa postazione sono ora validati.\n\nApprovare la postazione?",
        "en": "All results for this workstation are now validated.\n\nApprove the workstation?"
    },
    "You don't have permission to invalidate.": {
        "it": "Non hai i permessi per invalidare.",
        "en": "You don't have permission to invalidate."
    },
    "This result is not validated.": {
        "it": "Questo risultato non è validato.",
        "en": "This result is not validated."
    },
    "Invalidate result {0}?\n\nThis workstation is approved.\nThe approval will be revoked.": {
        "it": "Invalidare il risultato {0}?\n\nQuesta postazione è approvata.\nL'approvazione sarà revocata.",
        "en": "Invalidate result {0}?\n\nThis workstation is approved.\nThe approval will be revoked."
    },
    "Invalidate result {0}?": {"it": "Invalidare il risultato {0}?", "en": "Invalidate result {0}?"},
    "Result invalidated. Workstation approval revoked.": {
        "it": "Risultato invalidato. Approvazione postazione revocata.",
        "en": "Result invalidated. Workstation approval revoked."
    },
    "Result invalidated.": {"it": "Risultato invalidato.", "en": "Result invalidated."},
    "Failed to invalidate:": {"it": "Invalidazione fallita:", "en": "Failed to invalidate:"},
    "Please load data first.": {"it": "Carica prima i dati.", "en": "Please load data first."},
    "No data to export.": {"it": "Nessun dato da esportare.", "en": "No data to export."},
    "History exported to:\n{0}": {"it": "Storico esportato in:\n{0}", "en": "History exported to:\n{0}"},
    "Mandatory Tests": {"it": "Test Obbligatori", "en": "Mandatory Tests"},
    "All mandatory tests have been executed.": {
        "it": "Tutti i test obbligatori sono stati eseguiti.",
        "en": "All mandatory tests have been executed."
    },
    "Missing Mandatory Tests": {"it": "Test Obbligatori Mancanti", "en": "Missing Mandatory Tests"},
    "The following mandatory tests have not been executed:\n\n{0}": {
        "it": "I seguenti test obbligatori non sono stati eseguiti:\n\n{0}",
        "en": "The following mandatory tests have not been executed:\n\n{0}"
    },

    # ==========================================================================
    # Notes
    # ==========================================================================
    "Notes": {"it": "Note", "en": "Notes"},
    "Add Note": {"it": "Aggiungi Nota", "en": "Add Note"},
    "Edit Note": {"it": "Modifica Nota", "en": "Edit Note"},
    "Action:": {"it": "Azione:", "en": "Action:"},
    "Modified:": {"it": "Modificato:", "en": "Modified:"},

    # ==========================================================================
    # Export/Import
    # ==========================================================================
    "Export Data": {"it": "Esporta Dati", "en": "Export Data"},
    "Import Data": {"it": "Importa Dati", "en": "Import Data"},
    "Export completed.": {"it": "Esportazione completata.", "en": "Export completed."},
    "Import completed.": {"it": "Importazione completata.", "en": "Import completed."},
    "Export failed.": {"it": "Esportazione fallita.", "en": "Export failed."},
    "Import failed.": {"it": "Importazione fallita.", "en": "Import failed."},

    # ==========================================================================
    # Treeview Headers
    # ==========================================================================
    "Date": {"it": "Data", "en": "Date"},
    "Value": {"it": "Valore", "en": "Value"},
    "Mean": {"it": "Media", "en": "Mean"},
    "Bias": {"it": "Bias", "en": "Bias"},
    "CV": {"it": "CV", "en": "CV"},
    "Range": {"it": "Range", "en": "Range"},
    "Status": {"it": "Stato", "en": "Status"},
    "Operator": {"it": "Operatore", "en": "Operator"},
    "Type": {"it": "Tipo", "en": "Type"},
    "Test": {"it": "Test", "en": "Test"},
    "Code": {"it": "Codice", "en": "Code"},
    "Sample": {"it": "Campione", "en": "Sample"},
    "Method": {"it": "Metodo", "en": "Method"},
    "Lot": {"it": "Lotto", "en": "Lot"},
    "Description": {"it": "Descrizione", "en": "Description"},
    "Expiration": {"it": "Scadenza", "en": "Expiration"},
    "Target": {"it": "Target", "en": "Target"},

    # ==========================================================================
    # Workstation
    # ==========================================================================
    "Equipment:": {"it": "Apparecchiatura:", "en": "Equipment:"},
    "Device ID:": {"it": "ID Dispositivo:", "en": "Device ID:"},
    "Serial:": {"it": "Seriale:", "en": "Serial:"},
    "Section:": {"it": "Sezione:", "en": "Section:"},
    "Rank:": {"it": "Priorità:", "en": "Rank:"},
    "UUID": {"it": "UUID", "en": "UUID"},
    "Update Workstation": {"it": "Modifica Postazione", "en": "Update Workstation"},
    "Add Workstation": {"it": "Aggiungi Postazione", "en": "Add Workstation"},
    "This Device ID is already in use.": {
        "it": "Questo ID Dispositivo è già in uso.",
        "en": "This Device ID is already in use."
    },
    "Users": {"it": "Utenti", "en": "Users"},

    # ==========================================================================
    # Bland-Altman
    # ==========================================================================
    "Bland-Altman": {"it": "Bland-Altman", "en": "Bland-Altman"},
    "Bland-Altman Comparison": {"it": "Confronto Bland-Altman", "en": "Bland-Altman Comparison"},
    "Bland-Altman Plot": {"it": "Grafico Bland-Altman", "en": "Bland-Altman Plot"},
    "Workstation 1:": {"it": "Postazione 1:", "en": "Workstation 1:"},
    "Workstation 2:": {"it": "Postazione 2:", "en": "Workstation 2:"},
    "Calculate": {"it": "Calcola", "en": "Calculate"},
    "Clear": {"it": "Pulisci", "en": "Clear"},
    "Statistics": {"it": "Statistiche", "en": "Statistics"},
    "Pairs:": {"it": "Coppie:", "en": "Pairs:"},
    "Bias:": {"it": "Bias:", "en": "Bias:"},
    "+1.96 SD:": {"it": "+1.96 DS:", "en": "+1.96 SD:"},
    "-1.96 SD:": {"it": "-1.96 DS:", "en": "-1.96 SD:"},
    "Please select two workstations.": {
        "it": "Seleziona due postazioni.",
        "en": "Please select two workstations."
    },
    "Please select two different workstations.": {
        "it": "Seleziona due postazioni diverse.",
        "en": "Please select two different workstations."
    },
    "Please select test and level.": {
        "it": "Seleziona test e livello.",
        "en": "Please select test and level."
    },
    "Not enough paired data. Minimum 10 pairs required.": {
        "it": "Dati accoppiati insufficienti. Minimo 10 coppie richieste.",
        "en": "Not enough paired data. Minimum 10 pairs required."
    },
    "Found": {"it": "Trovate", "en": "Found"},
    "Mean of measurements": {"it": "Media delle misure", "en": "Mean of measurements"},
    "Difference": {"it": "Differenza", "en": "Difference"},

    # Bland-Altman Scanner
    "Bland-Altman Scanner": {"it": "Scanner Bland-Altman", "en": "Bland-Altman Scanner"},
    "Bland-Altman Alert Scanner": {"it": "Scanner Alert Bland-Altman", "en": "Bland-Altman Alert Scanner"},
    "Scan": {"it": "Scansiona", "en": "Scan"},
    "View Plot": {"it": "Visualizza Grafico", "en": "View Plot"},
    "Bias threshold:": {"it": "Soglia Bias:", "en": "Bias threshold:"},
    "% out threshold:": {"it": "Soglia % fuori:", "en": "% out threshold:"},
    "Workstation 1": {"it": "Postazione 1", "en": "Workstation 1"},
    "Workstation 2": {"it": "Postazione 2", "en": "Workstation 2"},
    "Pairs": {"it": "Coppie", "en": "Pairs"},
    "Bias": {"it": "Bias", "en": "Bias"},
    "% Out": {"it": "% Fuori", "en": "% Out"},
    "Alert": {"it": "Allerta", "en": "Alert"},
    "Comparisons": {"it": "Confronti", "en": "Comparisons"},
    "Alerts": {"it": "Allerte", "en": "Alerts"},
    "Scanning...": {"it": "Scansione...", "en": "Scanning..."},
    "Insufficient": {"it": "Insufficiente", "en": "Insufficient"},
    "Please select a comparison.": {
        "it": "Seleziona un confronto.",
        "en": "Please select a comparison."
    },
    "Cannot scan while Abbott import is running.\nPlease wait for the import to complete.": {
        "it": "Impossibile scansionare durante l'import Abbott.\nAttendi il completamento dell'import.",
        "en": "Cannot scan while Abbott import is running.\nPlease wait for the import to complete."
    },
    "Please wait for the scan to complete.": {
        "it": "Attendi il completamento della scansione.",
        "en": "Please wait for the scan to complete."
    },
    "Selected comparison": {"it": "Confronto selezionato", "en": "Selected comparison"},
    "Please select these values in the Bland-Altman view.": {
        "it": "Seleziona questi valori nella vista Bland-Altman.",
        "en": "Please select these values in the Bland-Altman view."
    },

    # ==========================================================================
    # Daily Validation Statistics
    # ==========================================================================
    "Validated:": {"it": "Validati:", "en": "Validated:"},
    "Pending:": {"it": "Pendenti:", "en": "Pending:"},
    "All mandatory OK": {"it": "Test obbligatori OK", "en": "All mandatory OK"},
    "Missing mandatory:": {"it": "Obbligatori mancanti:", "en": "Missing mandatory:"},
    "Auto-refresh paused": {"it": "Aggiornamento sospeso", "en": "Auto-refresh paused"},
    "Auto-refresh stopped": {"it": "Aggiornamento fermato", "en": "Auto-refresh stopped"},
    "Press Load to start": {"it": "Premi Carica per iniziare", "en": "Press Load to start"},
    "Stop": {"it": "Stop", "en": "Stop"},

    # ==========================================================================
    # QC Report
    # ==========================================================================
    "QC Report": {"it": "Report QC", "en": "QC Report"},
    "Select All": {"it": "Seleziona tutti", "en": "Select All"},
    "Deselect All": {"it": "Deseleziona tutti", "en": "Deselect All"},
    "Generate Report": {"it": "Genera Report", "en": "Generate Report"},
    "Please select a valid date.": {
        "it": "Seleziona una data valida.",
        "en": "Please select a valid date."
    },
    "No laboratory selected.": {
        "it": "Nessun laboratorio selezionato.",
        "en": "No laboratory selected."
    },
    "Please select at least one test.": {
        "it": "Seleziona almeno un test.",
        "en": "Please select at least one test."
    },
    "Save Report": {"it": "Salva Report", "en": "Save Report"},
    "Report saved successfully.": {
        "it": "Report salvato correttamente.",
        "en": "Report saved successfully."
    },
    "Error saving file:": {
        "it": "Errore nel salvataggio del file:",
        "en": "Error saving file:"
    },
    "No validated results found for this date.": {
        "it": "Nessun risultato validato trovato per questa data.",
        "en": "No validated results found for this date."
    },
    "Preview": {"it": "Anteprima", "en": "Preview"},
    "Report Preview": {"it": "Anteprima Report", "en": "Report Preview"},
    "Print": {"it": "Stampa", "en": "Print"},
    "Report sent to printer.": {
        "it": "Report inviato alla stampante.",
        "en": "Report sent to printer."
    },
    "Printer not available. Use Save to export the file.": {
        "it": "Stampante non disponibile. Usa Salva per esportare il file.",
        "en": "Printer not available. Use Save to export the file."
    },
    "Print error:": {"it": "Errore di stampa:", "en": "Print error:"},
    "You can only invalidate results you validated yourself.": {
        "it": "Puoi invalidare solo i risultati che hai validato tu.",
        "en": "You can only invalidate results you validated yourself."
    },
    "No pending results selected.": {
        "it": "Nessun risultato in attesa selezionato.",
        "en": "No pending results selected."
    },
    "Validate {0} selected results?": {
        "it": "Validare {0} risultati selezionati?",
        "en": "Validate {0} selected results?"
    },
    "{0} results validated.": {
        "it": "{0} risultati validati.",
        "en": "{0} results validated."
    },
    "Validated: {0}\nFailed: {1}": {
        "it": "Validati: {0}\nFalliti: {1}",
        "en": "Validated: {0}\nFailed: {1}"
    },
    "Select a workstation and click Load": {
        "it": "Seleziona una workstation e premi Carica",
        "en": "Select a workstation and click Load"
    },
    "No results for this date": {
        "it": "Nessun risultato per questa data",
        "en": "No results for this date"
    },
    "Failed to load workstations:": {
        "it": "Impossibile caricare le workstation:",
        "en": "Failed to load workstations:"
    },
    "Failed to load results:": {
        "it": "Impossibile caricare i risultati:",
        "en": "Failed to load results:"
    },
    "Please load a workstation first.": {
        "it": "Prima carica una workstation.",
        "en": "Please load a workstation first."
    },
    "Please select one or more results.": {
        "it": "Seleziona uno o più risultati.",
        "en": "Please select one or more results."
    },
    "Please select a single result.": {
        "it": "Seleziona un singolo risultato.",
        "en": "Please select a single result."
    },
    "Invalidate this result?": {
        "it": "Invalidare questo risultato?",
        "en": "Invalidate this result?"
    },
    "Result invalidated.": {
        "it": "Risultato invalidato.",
        "en": "Result invalidated."
    },
    "Approve WS": {"it": "Approva WS", "en": "Approve WS"},
    "Results:": {"it": "Risultati:", "en": "Results:"},
    "all validated": {"it": "tutti validati", "en": "all validated"},
    "Only problems": {"it": "Solo problemi", "en": "Only problems"},
    "problems only": {"it": "solo problemi", "en": "problems only"},
    "Quick:": {"it": "Rapido:", "en": "Quick:"},
    "Add note '{0}' to selected result?": {
        "it": "Aggiungere nota '{0}' al risultato selezionato?",
        "en": "Add note '{0}' to selected result?"
    },
    "Add note '{0}' to {1} selected results?": {
        "it": "Aggiungere nota '{0}' a {1} risultati selezionati?",
        "en": "Add note '{0}' to {1} selected results?"
    },
    "Note added to {0} result(s).": {
        "it": "Nota aggiunta a {0} risultato/i.",
        "en": "Note added to {0} result(s)."
    },
    "Failed to add note:": {"it": "Impossibile aggiungere nota:", "en": "Failed to add note:"},
    "Please select a single result.": {
        "it": "Selezionare un singolo risultato.",
        "en": "Please select a single result."
    },
    "Please select an action.": {"it": "Selezionare un'azione.", "en": "Please select an action."},
    "+ Note": {"it": "+ Nota", "en": "+ Note"},
    "Add Note": {"it": "Aggiungi Nota", "en": "Add Note"},
    "Update Note": {"it": "Modifica Nota", "en": "Update Note"},
    "Created by: {0}": {"it": "Creata da: {0}", "en": "Created by: {0}"},
    "Created by: {0} (read-only)": {"it": "Creata da: {0} (sola lettura)", "en": "Created by: {0} (read-only)"},
    "Created by: Unknown": {"it": "Creata da: Sconosciuto", "en": "Created by: Unknown"},
    "You don't have permission to edit this note.": {
        "it": "Non hai i permessi per modificare questa nota.",
        "en": "You don't have permission to edit this note."
    },
    "Copy": {"it": "Copia", "en": "Copy"},
    "Report copied to clipboard.": {
        "it": "Report copiato negli appunti.",
        "en": "Report copied to clipboard."
    },
    "Filter:": {"it": "Filtro:", "en": "Filter:"},
    "Search:": {"it": "Cerca:", "en": "Search:"},
    "All": {"it": "Tutti", "en": "All"},
    "OK": {"it": "OK", "en": "OK"},
    "Warning": {"it": "Warning", "en": "Warning"},
    "Violation": {"it": "Violazione", "en": "Violation"},

    # ==========================================================================
    # Performance Dashboard
    # ==========================================================================
    "Performance Dashboard": {"it": "Performance", "en": "Performance Dashboard"},
    "From:": {"it": "Da:", "en": "From:"},
    "To:": {"it": "A:", "en": "To:"},
    "Viol%": {"it": "Viol%", "en": "Viol%"},
    "Warn%": {"it": "Warn%", "en": "Warn%"},
    "Note%": {"it": "Note%", "en": "Note%"},
    "CV%": {"it": "CV%", "en": "CV%"},
    "Bias%": {"it": "Bias%", "en": "Bias%"},
    "Actions Breakdown": {"it": "Dettaglio Azioni", "en": "Actions Breakdown"},
    "No data for selected date range": {
        "it": "Nessun dato per il periodo selezionato",
        "en": "No data for selected date range"
    },
    "From date must be before To date.": {
        "it": "La data iniziale deve precedere quella finale.",
        "en": "From date must be before To date."
    },
    "No actions recorded": {"it": "Nessuna azione registrata", "en": "No actions recorded"},
    "No data to export.": {"it": "Nessun dato da esportare.", "en": "No data to export."},
    "File saved": {"it": "File salvato", "en": "File saved"},
    "Export failed": {"it": "Esportazione fallita", "en": "Export failed"},
    "Test Methods": {"it": "Test Laboratorio", "en": "Test Methods"},

    # ==========================================================================
    # QC Actions (Global Master Data)
    # ==========================================================================
    "Calibration": {"it": "Calibrazione", "en": "Calibration"},
    "Replacement": {"it": "Sostituzione", "en": "Replacement"},
    "Reagent blank performed": {"it": "Eseguito bianco reattivi", "en": "Reagent blank performed"},
    "New calibration performed": {"it": "Eseguita nuova calibrazione", "en": "New calibration performed"},
    "Reagents replaced": {"it": "Sostituiti i reagenti", "en": "Reagents replaced"},
    "Controls reconstituted and repeated": {
        "it": "Ricostituiti e ripetuti i controlli",
        "en": "Controls reconstituted and repeated"
    },
    "Operating conditions check": {"it": "Verifica condizioni operative", "en": "Operating conditions check"},
    "Detection system maintenance": {"it": "Manutenzione sistema rilevazione", "en": "Detection system maintenance"},
    "Target modified": {"it": "Modificato target", "en": "Target modified"},
    "SD modified": {"it": "Modificata DS", "en": "SD modified"},
    "Target and SD modified": {"it": "Modifica target e DS", "en": "Target and SD modified"},
    "Comment": {"it": "Commento", "en": "Comment"},
    "Controls replaced": {"it": "Sostituzione controlli", "en": "Controls replaced"},
    "Electrode replaced": {"it": "Sostituzione elettrodo", "en": "Electrode replaced"},
    "Repeat analysis": {"it": "Ripetere analisi", "en": "Repeat analysis"},
    "Contact service": {"it": "Contattare assistenza", "en": "Contact service"},
    "New lot number": {"it": "Nuovo lotto", "en": "New lot number"},
    "Preventive maintenance": {"it": "Manutenzione preventiva", "en": "Preventive maintenance"},
    "Result excluded": {"it": "Risultato escluso", "en": "Result excluded"},
    "Instrument restart": {"it": "Riavvio strumento", "en": "Instrument restart"},

    # Action editor help
    "Code: English uppercase (e.g., CALIBRATION)": {
        "it": "Codice: inglese maiuscolo (es. CALIBRATION)",
        "en": "Code: English uppercase (e.g., CALIBRATION)"
    },
    "Description: English text (translated via i18n)": {
        "it": "Descrizione: testo inglese (tradotto via i18n)",
        "en": "Description: English text (translated via i18n)"
    },
    "Global Master Data": {"it": "Dati Master Globali", "en": "Global Master Data"},
    "Action": {"it": "Azione", "en": "Action"},

    # Role hints for user editor
    "App Admin - Global access": {"it": "App Admin - Accesso globale", "en": "App Admin - Global access"},
    "Country Admin - Assign to country": {"it": "Country Admin - Assegna a paese", "en": "Country Admin - Assign to country"},
    "Regional Admin - Assign to region/site": {"it": "Regional Admin - Assegna a regione/sito", "en": "Regional Admin - Assign to region/site"},
    "Lab Admin - Assign to lab": {"it": "Lab Admin - Assegna a laboratorio", "en": "Lab Admin - Assign to lab"},
    "Superuser - Assign to lab": {"it": "Superuser - Assegna a laboratorio", "en": "Superuser - Assign to lab"},
    "Technician - Assign to lab": {"it": "Tecnico - Assegna a laboratorio", "en": "Technician - Assign to lab"},
    "Viewer - Assign to lab": {"it": "Viewer - Assegna a laboratorio", "en": "Viewer - Assign to lab"},

    # ==========================================================================
    # Lab Selector
    # ==========================================================================
    "Select Laboratory": {"it": "Seleziona Laboratorio", "en": "Select Laboratory"},
    "Select the laboratory to work with:": {
        "it": "Seleziona il laboratorio con cui lavorare:",
        "en": "Select the laboratory to work with:"
    },
    "Please select a laboratory.": {
        "it": "Seleziona un laboratorio.",
        "en": "Please select a laboratory."
    },
    "Login cancelled.": {"it": "Login annullato.", "en": "Login cancelled."},
    "No laboratory assigned to this user.": {
        "it": "Nessun laboratorio assegnato a questo utente.",
        "en": "No laboratory assigned to this user."
    },
    "Select": {"it": "Seleziona", "en": "Select"},
}


class I18N:
    """Internationalization helper class."""

    def __init__(self, language=None):
        """
        Initialize with specified language.

        Args:
            language: Language code ('en' or 'it'). Defaults to DEFAULT_LANGUAGE.
        """
        self.language = language if language in LANGUAGES else DEFAULT_LANGUAGE

    def get(self, key):
        """
        Get translated string for key.

        Args:
            key: The string to translate (English version)

        Returns:
            Translated string, or key itself if not found
        """
        if key in TRANSLATIONS:
            return TRANSLATIONS[key].get(self.language, key)
        return key

    def __call__(self, key):
        """Shorthand for get()."""
        return self.get(key)

    def set_language(self, language):
        """
        Set current language.

        Args:
            language: Language code ('en' or 'it')
        """
        if language in LANGUAGES:
            self.language = language

    @staticmethod
    def get_languages():
        """Return available languages."""
        return LANGUAGES.copy()


# Global instance - will be initialized by engine
_i18n = None


def get_translator():
    """Get global translator instance."""
    global _i18n
    if _i18n is None:
        _i18n = I18N()
    return _i18n


def set_language(language):
    """Set global language."""
    get_translator().set_language(language)


def _(key):
    """
    Translate a string using the global translator.

    This is the main function to use throughout the application.

    Args:
        key: String to translate (English version)

    Returns:
        Translated string
    """
    return get_translator().get(key)
