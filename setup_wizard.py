# -*- coding: utf-8 -*-
"""
Setup Wizard for Biovarase - First-Time Database Configuration.

This module provides a Tkinter GUI wizard for initial database setup.
It collects database credentials, tests the connection and creates an
encrypted, hardware-locked config.enc file via security.encrypt_config().

Features:
- User-friendly GUI (Tkinter)
- Input validation
- Password visibility toggle
- Database connection testing (mariadb)
- Hardware-locked config.enc creation

Typical usage:
    $ python setup_wizard.py

or from the main application entry point, called when config.enc
is missing or invalid.
"""

from typing import Dict, Optional

import tkinter as tk
from tkinter import ttk, messagebox

import mariadb  # same driver used by DBMS
from security import encrypt_config


CONFIG_PATH = "config.enc"


class SetupWizard(tk.Toplevel):
    """
    Tkinter Toplevel window acting as a modal setup wizard.

    It collects database credentials, allows connection testing, and
    on success writes an encrypted, hardware-locked configuration file.
    """

    def __init__(self, parent: tk.Misc):
        """
        Initialize the setup wizard.

        Args:
            parent: Parent Tk widget (usually root).
        """
        super().__init__(parent)

        self.parent = parent
        self.success: bool = False  # set True only when config.enc is created

        # Variables bound to form fields
        self.var_host = tk.StringVar(value="localhost")
        self.var_port = tk.StringVar(value="3306")
        self.var_database = tk.StringVar(value="biovarase")
        self.var_user = tk.StringVar(value="")
        self.var_password = tk.StringVar(value="")
        self.var_show_password = tk.BooleanVar(value=False)

        self._configure_window()
        self._create_widgets()
        self._center_on_screen()

        # Modal behavior
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

    # ------------------------------------------------------------------ #
    # Window configuration
    # ------------------------------------------------------------------ #
    def _configure_window(self) -> None:
        """Basic window configuration (title, size, style)."""
        self.title("Biovarase – Configurazione iniziale")
        self.resizable(False, False)

    def _center_on_screen(self) -> None:
        """Center the window on the screen."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        if width == 1 and height == 1:
            # Fallback initial size before layout
            width, height = 420, 260

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w // 2) - (width // 2)
        y = (screen_h // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    # ------------------------------------------------------------------ #
    # Widgets
    # ------------------------------------------------------------------ #
    def _create_widgets(self) -> None:
        """Create and layout all widgets."""

        main = ttk.Frame(self, padding=12)
        main.grid(row=0, column=0, sticky="nsew")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Title
        lbl_title = ttk.Label(
            main,
            text="Configurazione database Biovarase",
            font=("TkDefaultFont", 11, "bold"),
        )
        lbl_title.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

        # Host
        ttk.Label(main, text="Host:").grid(row=1, column=0, sticky="e", pady=2, padx=(0, 4))
        ent_host = ttk.Entry(main, textvariable=self.var_host, width=28)
        ent_host.grid(row=1, column=1, columnspan=2, sticky="we", pady=2)

        # Port
        ttk.Label(main, text="Porta:").grid(row=2, column=0, sticky="e", pady=2, padx=(0, 4))
        ent_port = ttk.Entry(main, textvariable=self.var_port, width=8)
        ent_port.grid(row=2, column=1, sticky="w", pady=2)

        # Database
        ttk.Label(main, text="Database:").grid(row=3, column=0, sticky="e", pady=2, padx=(0, 4))
        ent_db = ttk.Entry(main, textvariable=self.var_database, width=28)
        ent_db.grid(row=3, column=1, columnspan=2, sticky="we", pady=2)

        # User
        ttk.Label(main, text="Utente:").grid(row=4, column=0, sticky="e", pady=2, padx=(0, 4))
        ent_user = ttk.Entry(main, textvariable=self.var_user, width=28)
        ent_user.grid(row=4, column=1, columnspan=2, sticky="we", pady=2)

        # Password
        ttk.Label(main, text="Password:").grid(row=5, column=0, sticky="e", pady=2, padx=(0, 4))
        self.ent_password = ttk.Entry(main, textvariable=self.var_password, width=28, show="*")
        self.ent_password.grid(row=5, column=1, columnspan=2, sticky="we", pady=2)

        cb_show = ttk.Checkbutton(
            main,
            text="Mostra password",
            variable=self.var_show_password,
            command=self._toggle_password_visibility,
        )
        cb_show.grid(row=6, column=1, columnspan=2, sticky="w", pady=(0, 6))

        # Status label
        self.lbl_status = ttk.Label(
            main,
            text="Inserisci le credenziali del database e testa la connessione.",
            foreground="gray",
            wraplength=360,
            justify="left",
        )
        self.lbl_status.grid(row=7, column=0, columnspan=3, sticky="we", pady=(4, 8))

        # Separator
        sep = ttk.Separator(main, orient="horizontal")
        sep.grid(row=8, column=0, columnspan=3, sticky="we", pady=(2, 8))

        # Buttons
        btn_test = ttk.Button(main, text="Test connessione", command=self.on_test_connection)
        btn_test.grid(row=9, column=0, sticky="w", pady=2)

        btn_save = ttk.Button(main, text="Salva configurazione", command=self.on_save_config)
        btn_save.grid(row=9, column=1, sticky="e", pady=2, padx=(0, 4))

        btn_cancel = ttk.Button(main, text="Annulla", command=self.on_cancel)
        btn_cancel.grid(row=9, column=2, sticky="e", pady=2)

        # Allow horizontal grow
        for col in range(3):
            main.columnconfigure(col, weight=1)

        # Initial focus
        ent_user.focus_set()

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _toggle_password_visibility(self) -> None:
        """Toggle password field visibility."""
        show = "" if self.var_show_password.get() else "*"
        self.ent_password.configure(show=show)

    def _get_credentials(self) -> Dict[str, str]:
        """Return current credentials as a dict."""
        return {
            "host": self.var_host.get().strip(),
            "port": self.var_port.get().strip(),
            "database": self.var_database.get().strip(),
            "user": self.var_user.get().strip(),
            "password": self.var_password.get().strip(),
        }

    def _validate_inputs(self) -> bool:
        """Validate required fields and show messagebox on error."""
        creds = self._get_credentials()

        if not creds["host"]:
            messagebox.showerror("Errore", "L'host del database è obbligatorio.", parent=self)
            return False

        if not creds["database"]:
            messagebox.showerror("Errore", "Il nome del database è obbligatorio.", parent=self)
            return False

        if not creds["user"]:
            messagebox.showerror("Errore", "Il nome utente è obbligatorio.", parent=self)
            return False

        if not creds["password"]:
            messagebox.showerror("Errore", "La password è obbligatoria.", parent=self)
            return False

        port_str = creds["port"]
        if port_str:
            try:
                port = int(port_str)
                if not (1 <= port <= 65535):
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Errore",
                    "La porta deve essere un numero intero compreso tra 1 e 65535.",
                    parent=self,
                )
                return False

        return True

    def _update_status(self, text: str, error: bool = False) -> None:
        """Update status label text and color."""
        self.lbl_status.configure(text=text, foreground="red" if error else "green")

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #
    def on_test_connection(self) -> None:
        """Test database connection with current credentials."""
        if not self._validate_inputs():
            return

        creds = self._get_credentials()

        try:
            port = int(creds["port"]) if creds["port"] else 3306
        except ValueError:
            port = 3306

        try:
            self._update_status("Verifica connessione in corso...", error=False)
            self.update_idletasks()

            con = mariadb.connect(
                user=creds["user"],
                password=creds["password"],
                host=creds["host"],
                port=port,
                database=creds["database"],
                autocommit=True,
            )
            try:
                cur = con.cursor()
                cur.execute("SELECT 1")
                cur.fetchall()
            finally:
                con.close()

        except mariadb.Error as e:
            msg = f"Connessione fallita:\n{e}"
            self._update_status("Connessione fallita.", error=True)
            messagebox.showerror("Errore connessione", msg, parent=self)
            return

        self._update_status("Connessione riuscita.", error=False)
        messagebox.showinfo(
            "Connessione riuscita",
            "Connessione al database riuscita con successo.",
            parent=self,
        )

    def on_save_config(self) -> None:
        """
        Validate, (optionally) test connection again and save encrypted config.

        On success sets self.success = True and closes the wizard.
        """
        if not self._validate_inputs():
            return

        creds = self._get_credentials()

        # Confirm save
        if not messagebox.askyesno(
            "Conferma",
            "Vuoi salvare queste credenziali in config.enc (cifrato e "
            "bloccato a questa macchina)?",
            parent=self,
        ):
            return

        # Optional: quick connection test before saving
        try:
            port = int(creds["port"]) if creds["port"] else 3306
        except ValueError:
            port = 3306

        try:
            self._update_status("Verifica connessione in corso...", error=False)
            self.update_idletasks()

            con = mariadb.connect(
                user=creds["user"],
                password=creds["password"],
                host=creds["host"],
                port=port,
                database=creds["database"],
                autocommit=True,
            )
            con.close()
        except mariadb.Error as e:
            self._update_status("Connessione fallita.", error=True)
            messagebox.showerror(
                "Errore connessione",
                f"Impossibile connettersi al database:\n{e}\n\n"
                "La configurazione non è stata salvata.",
                parent=self,
            )
            return

        # Prepare payload for encrypt_config (without port, DBMS uses default 3306)
        config_creds = {
            "user": creds["user"],
            "password": creds["password"],
            "database": creds["database"],
            "host": creds["host"],
        }

        try:
            ok = encrypt_config(config_creds, CONFIG_PATH)
        except Exception as e:  # safety net, encrypt_config should already handle errors
            ok = False
            messagebox.showerror(
                "Errore cifratura",
                f"Errore durante la creazione del file di configurazione:\n{e}",
                parent=self,
            )

        if not ok:
            self._update_status("Errore durante la creazione di config.enc.", error=True)
            return

        self.success = True
        self._update_status("Configurazione salvata con successo.", error=False)
        messagebox.showinfo(
            "Configurazione salvata",
            "Il file config.enc è stato creato con successo.\n"
            "Biovarase potrà ora utilizzare queste credenziali.",
            parent=self,
        )
        self.destroy()

    def on_cancel(self) -> None:
        """Handle window close / cancel button."""
        if not self.success:
            if not messagebox.askyesno(
                "Conferma",
                "Annullare la configurazione?\n"
                "Il file config.enc non verrà creato.",
                parent=self,
            ):
                return
        self.destroy()


# ---------------------------------------------------------------------- #
# Standalone entry point
# ---------------------------------------------------------------------- #
def main() -> None:
    """Launch the setup wizard as a standalone application."""
    root = tk.Tk()
    root.title("Biovarase")
    root.update_idletasks()      # <<< IMPORTANTE su Windows
    root.withdraw()              # ora puoi nasconderlo senza flash

    wizard = SetupWizard(root)

    # Modalità corretta: il wizard diventa la finestra principale
    wizard.wait_window()

    root.destroy()

    if wizard.success:
        print("✅ Setup completato: config.enc creato con successo.")
    else:
        print("❌ Setup annullato o non completato.")

if __name__ == "__main__":
    main()
