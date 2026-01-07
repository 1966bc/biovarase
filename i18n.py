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
    "Reset": {"it": "Reimposta", "en": "Reset"},
    "Apply": {"it": "Applica", "en": "Apply"},
    "OK": {"it": "OK", "en": "OK"},
    "Yes": {"it": "Sì", "en": "Yes"},
    "No": {"it": "No", "en": "No"},
    "Login": {"it": "Accedi", "en": "Login"},
    "Logout": {"it": "Esci", "en": "Logout"},

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
    "Username:": {"it": "Nome utente:", "en": "Username:"},
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

    # ==========================================================================
    # Menu - Edit
    # ==========================================================================
    "Edit": {"it": "Modifica", "en": "Edit"},
    "Settings": {"it": "Impostazioni", "en": "Settings"},
    "Preferences": {"it": "Preferenze", "en": "Preferences"},

    # ==========================================================================
    # Menu - Admin
    # ==========================================================================
    "Admin": {"it": "Admin", "en": "Admin"},
    "Users": {"it": "Utenti", "en": "Users"},
    "Sites": {"it": "Siti", "en": "Sites"},
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

    # ==========================================================================
    # Menu - Plots
    # ==========================================================================
    "Plots": {"it": "Grafici", "en": "Plots"},
    "Levey-Jennings": {"it": "Levey-Jennings", "en": "Levey-Jennings"},
    "Total Error": {"it": "Errore Totale", "en": "Total Error"},
    "Youden Plot": {"it": "Grafico Youden", "en": "Youden Plot"},

    # ==========================================================================
    # Menu - Documents
    # ==========================================================================
    "Documents": {"it": "Documenti", "en": "Documents"},
    "Reports": {"it": "Report", "en": "Reports"},
    "Export": {"it": "Esporta", "en": "Export"},
    "Import": {"it": "Importa", "en": "Import"},

    # ==========================================================================
    # Menu - Help
    # ==========================================================================
    "Help": {"it": "Aiuto", "en": "Help"},
    "About": {"it": "Informazioni", "en": "About"},
    "License": {"it": "Licenza", "en": "License"},
    "Language": {"it": "Lingua", "en": "Language"},

    # ==========================================================================
    # Main Window
    # ==========================================================================
    "Tests": {"it": "Test", "en": "Tests"},
    "Batches": {"it": "Lotti", "en": "Batches"},
    "Results": {"it": "Risultati", "en": "Results"},
    "Control": {"it": "Controllo", "en": "Control"},
    "Control:": {"it": "Controllo:", "en": "Control:"},
    "Lot": {"it": "Lotto", "en": "Lot"},
    "Lot:": {"it": "Lotto:", "en": "Lot:"},
    "Test Methods": {"it": "Metodi Test", "en": "Test Methods"},
    "Workstation": {"it": "Postazione", "en": "Workstation"},
    "Workstation:": {"it": "Postazione:", "en": "Workstation:"},
    "Equipment": {"it": "Strumento", "en": "Equipment"},
    "Equipment:": {"it": "Strumento:", "en": "Equipment:"},
    "Section": {"it": "Sezione", "en": "Section"},
    "Section:": {"it": "Sezione:", "en": "Section:"},
    "Site": {"it": "Sito", "en": "Site"},
    "Site:": {"it": "Sito:", "en": "Site:"},
    "Lab": {"it": "Laboratorio", "en": "Lab"},
    "Lab:": {"it": "Laboratorio:", "en": "Lab:"},

    # ==========================================================================
    # Batch Window
    # ==========================================================================
    "Batch": {"it": "Lotto", "en": "Batch"},
    "Lot Number": {"it": "Numero Lotto", "en": "Lot Number"},
    "Lot Number:": {"it": "Numero Lotto:", "en": "Lot Number:"},
    "Expiration Date": {"it": "Data Scadenza", "en": "Expiration Date"},
    "Expiration Date:": {"it": "Data Scadenza:", "en": "Expiration Date:"},
    "Remember data": {"it": "Ricorda dati", "en": "Remember data"},

    # ==========================================================================
    # Result Window
    # ==========================================================================
    "Received:": {"it": "Ricevuto:", "en": "Received:"},
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

    # ==========================================================================
    # Language
    # ==========================================================================
    "Restart to apply language change.": {
        "it": "Riavviare l'applicazione per applicare il cambio lingua.",
        "en": "Restart to apply language change."
    },
    "Language changed.": {"it": "Lingua cambiata.", "en": "Language changed."},

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
    "Type": {"it": "Tipo", "en": "Type"},
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
