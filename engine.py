#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Engine Module - Main Orchestrator for Biovarase.

This module provides the Engine class, which serves as the central orchestrator
combining all system components through multiple inheritance (mixin architecture).

Architecture (Mixin Pattern):
    Engine combines multiple specialized mixins:
    - DBMS: Database connection and query execution
    - Controller: SQL builders and domain logic
    - QC: Quality control statistical calculations
    - Westgards: Westgard multirule QC evaluation
    - Exporter/Importer: Data import/export functionality
    - Tools: Shared utility functions
    - Launcher: External file opening

Key Responsibilities:
    - Global state management (current_ids: site/lab/section selection)
    - Window registry (dict_instances: track open GUI windows)
    - Cross-component communication and coordination
    - Configuration file management (section_id, ddof, zscore, etc.)
    - Error logging (on_log method)
    - User session management (log_user, log_ip)

Observer Pattern:
    Engine provides an event system for decoupled view communication:
    - subscribe(event, callback): Register for an event
    - unsubscribe(event, callback): Unregister from an event
    - notify(event, data): Emit an event to all subscribers

    Events:
    - "batch_changed": Fired when a batch is modified
    - "result_changed": Fired when a QC result is modified
    - "section_changed": Fired when section context changes
    - "supplier_changed": Fired when a supplier is modified
    - "equipment_changed": Fired when equipment is modified
    - "test_method_changed": Fired when a test method is modified

Global Context (current_ids):
    The Engine maintains application-wide context for multi-site operations:
    - site_id: Current laboratory site
    - lab_id: Current laboratory within site
    - section_id: Current section within laboratory

Window Registry (dict_instances):
    Tracks all open GUI windows for:
    - Singleton enforcement (master windows)
    - Cross-window refresh coordination
    - Centralized window lifecycle management

Configuration Management:
    Engine provides helper methods to read config files:
    - get_section_id(), get_ddof(), get_zscore()
    - get_observations(), get_remember_batch()
    - get_file(filename) for path resolution

Classes:
    Engine: Main orchestrator combining all mixins

Author: 1966bc (Giuseppe Costanzi)
Email: giuseppecostanzi@gmail.com
License: GNU GPL v3
Version: 4.2 (Professional Edition - Full Rewrite 2025)
"""
import os
import sys
import inspect
import traceback
import datetime
import socket
from typing import Dict, Any

from tools import Tools
from dbms import DBMS
from controller import Controller
from qc import QC
from westgards import Westgards
from exporter import Exporter
from importer import Importer
from launcher import Launcher

APP_TITLE = "Biovarase"

# User role constants (hierarchy: admin > superuser > technician > autologin)
ROLE_ADMIN = 0       # System administrator - multi-site configuration + full access
ROLE_SUPERUSER = 1   # Lab manager - QC validation + lab-wide data access
ROLE_TECHNICIAN = 2  # Section worker - data entry + section-only access
ROLE_AUTOLOGIN = 3   # Guest user - read-only access


class _EngineMeta(type):
    """
    Metaclass that ensures only one Engine instance exists.

    Implements the Singleton pattern at the metaclass level,
    intercepting instance creation before __new__ and __init__ are called.

    How it works:
        1. First call to Engine(...) creates and stores the instance
        2. Subsequent calls return the stored instance, ignoring new arguments
    """

    _instance = None

    def __call__(cls, *args, **kwargs):
        """
        Intercept instance creation.

        Returns the existing instance if one exists, otherwise creates
        a new one using the normal class instantiation process.
        """
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance


class Engine(DBMS, Controller, QC, Westgards, Exporter, Importer, Launcher, Tools,
             metaclass=_EngineMeta):
    """
    Main orchestrator for Biovarase - combines all system components via mixin inheritance.

    The Engine class is the central hub of Biovarase, combining multiple specialized
    mixins through Python's multiple inheritance to provide a unified interface for
    all application functionality.

    **Singleton Pattern**:
        Engine uses _EngineMeta metaclass to ensure only one instance exists.
        Multiple calls to Engine() return the same instance.

    **Mixin Architecture** (in MRO order):
        1. DBMS: Database connection and query execution
        2. Controller: SQL builders and domain logic
        3. QC: Quality control statistical calculations
        4. Westgards: Westgard multirule QC evaluation
        5. Exporter: Data export to various formats
        6. Importer: Data import from various sources
        7. Launcher: External file/application launching
        8. Tools: Shared utility functions

    **Global State Management**:
        - current_ids (dict): Multi-site context (site_id, lab_id, section_id)
        - dict_instances (dict): Window registry for singleton enforcement
        - log_user (dict): Currently logged-in user information
        - log_ip (str): Client IP address for audit logging

    **Key Responsibilities**:
        - Coordinate all application components
        - Manage GUI window lifecycles (singleton patterns)
        - Provide global application context
        - Configuration file management
        - Error logging and exception handling
        - User session management

    **Window Registry** (dict_instances):
        Tracks open GUI windows by name for:
        - Singleton enforcement (master windows open only once)
        - Cross-window refresh coordination
        - Centralized window management

        Example:
            self.dict_instances["batches"] = BatchesWindow(...)
            self.dict_instances["results"] = ResultsWindow(...)

    **Global Context** (current_ids):
        Maintains application-wide selection state:
        - site_id: Current laboratory site
        - lab_id: Current laboratory
        - section_id: Current section

        Used throughout app for multi-site data filtering.

    **Configuration Management**:
        Provides helper methods to read configuration files:
        - get_section_id() -> int: Current section ID
        - get_ddof() -> int: Degrees of freedom for statistics
        - get_zscore() -> float: Z-score threshold
        - get_observations() -> int: Observation window size
        - get_file(filename) -> str: Resolve config file path

    **Error Handling**:
        - on_log(): Comprehensive error logging to log.txt
        - Captures function, exception type, value, module, caller
        - Full stack trace with formatted output
        - Never raises exceptions from logging itself

    Attributes:
        dict_instances (dict): Registry of open GUI windows
        current_ids (dict): Global context (site/lab/section IDs)
        log_user (dict): Currently logged-in user
        log_ip (str): Client IP address
        _subscribers (dict): Event subscribers registry for Observer pattern

    Example:
        >>> engine = Engine("biovarase", "password", "biovarase")
        >>> engine.set_log_user(user_dict)
        >>> engine.on_open("batches", BatchesWindow, parent=main_window)
    """
    def __init__(self, user, password, database, host='localhost', port=3306, autocommit=True):
        super().__init__(user=user, password=password, database=database, host=host, port=port, autocommit=autocommit)

        # Windows registry: name -> widget
        self.dict_instances = {}

        # Event system: event_name -> [callbacks]
        self._subscribers = {}
        self.log_user = {}
        self.no_selected = "Attention!\nNo record selected!"
        self.mandatory = "Attention!\nField %s is mandatory!"
        self.delete = "Delete data?"
        self.ask_to_delete = "Delete data?"
        self.ask_to_save = "Do you want to save?"
        self.abort = "Operation aborted!"
        self.user_not_enable = "User not enabled for this function."
        self.batch_data = None
        self.title = APP_TITLE
        self.app_title = APP_TITLE
        self.current_ids = {}
        self.load_context_ids()
  
        
    def __str__(self):
        return "class: {0}\nMRO: {1}".format(self.__class__.__name__,
                                                       [x.__name__ for x in Engine.__mro__])

    # -------------------------------------------------------------------------
    # Observer Pattern: Event System
    # -------------------------------------------------------------------------

    def subscribe(self, event: str, callback) -> None:
        """
        Register a callback for an event.

        Views call this to receive notifications when something changes.
        Remember to unsubscribe in on_cancel() to avoid dead references.

        Args:
            event: Event name (e.g., "batch_changed", "result_changed")
            callback: Function to call when event fires

        Example:
            # In batches.__init__:
            self.engine.subscribe("batch_changed", self.on_batch_changed)
        """
        if event not in self._subscribers:
            self._subscribers[event] = []
        if callback not in self._subscribers[event]:
            self._subscribers[event].append(callback)

    def unsubscribe(self, event: str, callback) -> None:
        """
        Remove a callback from an event.

        Call this in on_cancel() before the window closes.

        Args:
            event: Event name
            callback: Function to remove
        """
        if event in self._subscribers:
            try:
                self._subscribers[event].remove(callback)
            except ValueError:
                pass

    def notify(self, event: str, data=None) -> None:
        """
        Notify all subscribers of an event.

        Views call this after making changes that other views might
        need to know about. Subscribers receive the event asynchronously.

        Args:
            event: Event name
            data: Optional data to pass to callbacks

        Example:
            # In batch editor after saving:
            self.engine.notify("batch_changed")
        """
        for callback in self._subscribers.get(event, []):
            try:
                callback(data)
            except Exception:
                # Subscriber might be dead or have errors, ignore
                pass

    # -------------------------------------------------------------------------
    # Permission Helper Methods (Role-Based Access Control)
    # -------------------------------------------------------------------------

    def can_validate_qc(self) -> bool:
        """
        Check if user can validate QC results.

        Only admins (role=0) and superusers (role=1) can validate.
        This is the primary daily QC validation permission check.

        Returns:
            bool: True if user can validate QC results, False otherwise
        """
        role = self.get_user_role()
        return role <= ROLE_SUPERUSER  # Admin (0) or Superuser (1)

    def can_configure_system(self) -> bool:
        """
        Check if user can access system configuration.

        Only admins (role=0) can configure global entities like:
        - Units of measurement
        - Test methods
        - Test names
        - Sites, Labs, Sections
        - Ensures "Glucose is Glucose everywhere"

        Returns:
            bool: True if user can configure system, False otherwise
        """
        role = self.get_user_role()
        return role == ROLE_ADMIN

    def can_modify_data(self) -> bool:
        """
        Check if user can insert/edit data.

        Admins (role=0), superusers (role=1), and technicians (role=2) can modify data.
        Autologin users (role=3) are read-only.

        Returns:
            bool: True if user can modify data, False otherwise
        """
        role = self.get_user_role()
        return role <= ROLE_TECHNICIAN  # Admin (0), Superuser (1), Technician (2)

    def is_read_only(self) -> bool:
        """
        Check if user has read-only access.

        Autologin users (role=3) and any role >= 3 are read-only.
        Used for demo kiosks, monitoring screens, or guest access.

        Returns:
            bool: True if user is read-only, False otherwise
        """
        role = self.get_user_role()
        return role >= ROLE_AUTOLOGIN

    def get_data_scope(self) -> tuple:
        """
        Get appropriate data filtering scope based on user role.

        Returns:
            tuple: (scope_type: str, filter_id: int or None)
                - Admin: ("all_sites", None) - no filtering
                - Superuser: ("lab", lab_id) - filter by lab_id
                - Technician/Autologin: ("section", section_id) - filter by section_id

        Example:
            scope, filter_id = self.get_data_scope()
            if scope == "lab":
                sql += " WHERE lab_id = ?"
                args = (filter_id,)
        """
        role = self.get_user_role()

        if role == ROLE_ADMIN:
            return ("all_sites", None)
        elif role == ROLE_SUPERUSER:
            lab_id = self.current_ids.get("lab_id")
            return ("lab", lab_id)
        else:  # TECHNICIAN or AUTOLOGIN
            section_id = self.get_section_id()
            return ("section", section_id)

    def get_autologin_flag(self) -> bool:
        """
        Return True if 'autologin' file exists and contains '1' (trimmed).
        Return False on missing file, '0', or any error.
        """
        try:
            path = self.get_file("autologin")
            if not os.path.exists(path):
                return False

            with open(path, "r", encoding="utf-8") as f:
                value = f.readline().strip()

            return value == "1"
        except Exception as e:
            self.on_log(
                inspect.stack()[0][3],
                e,
                type(e),
                sys.modules[__name__],
            )
            return False

    def autologin_generic_user(self) -> bool:
        """
        Try to perform autologin as the generic 'viewer' user.

        Returns:
            True  if autologin succeeded and log_user is set.
            False otherwise.
        """
        try:
            row = self.get_autologin_user()
            if not row:
                return False

            # read_dict() returns an ordered dict (columns in declaration order).
            # set_log_user() expects a sequence, not a dict.
            record = tuple(row[col] for col in row.keys())

            self.set_log_user(record)
            return True

        except Exception as e:
            self.on_log(
                inspect.stack()[0][3],
                e,
                type(e),
                sys.modules[__name__],
            )
            return False


    def load_context_ids(self):
        """
        Load and store all hierarchical IDs (site_id, supplier_id, comp_id,
        lab_id, section_id) associated with the current section_id.

        The section_id is read from the 'section_id' file.
        If the section_id is missing or the lookup query returns no data,
        the context is cleared and the application continues safely.

        All retrieved IDs are stored in the dictionary self.current_ids.
        """
        try:
            # Read the current section_id from file
            section_id = self.get_section_id()
            if section_id is None:
                # No section available → clear context
                self.current_ids = {}
                return

            # Query DB for hierarchical IDs related to this section_id
            row = self.get_idd_by_section_id(section_id)
            if not row:
                # No database row found → clear context
                self.current_ids = {}
                return

            # row is a dict from read_dict(False, ...)
            self.current_ids = {
                "site_id":    row["site_id"],
                "supplier_id": row["supplier_id"],
                "comp_id":    row["comp_id"],
                "lab_id":     row["lab_id"],
                "section_id": row["section_id"],
            }

        except Exception as e:
            # Log the error but do not crash the app
            self.on_log("load_context_ids", e, type(e), sys.modules[__name__])
            self.current_ids = {}

    def get_user_role(self) -> int:
        """
        Return numeric role of logged user (0=admin, 1=superuser, 2=user).
        Returns 99 if role is not available.
        """
        try:
            return int(self.log_user["role"])
        except (KeyError, TypeError, ValueError):
            return 99  # invalid / unknown

    def is_admin(self) -> bool:
        """
        Check if user is admin (role=0).

        Admin has full access to system configuration and all operations.

        Returns:
            bool: True if user is admin, False otherwise
        """
        return self.get_user_role() == ROLE_ADMIN

    def is_superuser(self) -> bool:
        """
        Check if user is superuser (role=1).

        Superuser can validate QC for entire laboratory.

        Returns:
            bool: True if user is superuser, False otherwise
        """
        return self.get_user_role() == ROLE_SUPERUSER

    def is_user(self) -> bool:
        """
        Check if user is technician (role=2).

        Technician can enter data in their section.

        Returns:
            bool: True if user is technician, False otherwise
        """
        return self.get_user_role() == ROLE_TECHNICIAN

    def can_delete_results(self) -> bool:
        """
        Check if user can delete QC results.

        Only admins and superusers can delete results.

        Returns:
            bool: True if user can delete results, False otherwise
        """
        return self.get_user_role() <= ROLE_SUPERUSER  # Admin (0) or Superuser (1)

    def get_log_file(self):
        path = self.get_file("log.txt") 
        self.launch(path)

    def on_log(self, function, exc_value, exc_type, module, caller=None):
        """
        Scrive su log.txt:
        - timestamp
        - Classe.metodo (e caller se presente)
        - Tipo: messaggio dell'eccezione
        - nome modulo
        - traceback completo dell'eccezione corrente
        """
        try:
            
            now = datetime.datetime.now().astimezone()
            
            ts = now.isoformat(sep=" ", timespec="seconds")
            
            module_name = getattr(module, "__name__", str(module))
            
            tb_text = traceback.format_exc()

            header = f"{ts}\n{type(self).__name__}.{function}"
            
            if caller:
                header += f"  (caller: {caller})"

            log_text = (
                f"{header}\n"
                f"{exc_type.__name__}: {exc_value}\n"
                f"{module_name}\n"
                f"{tb_text}\n"
            )

            path = self.get_file("log.txt")
            #fh = file handle
            with open(path, "a", encoding="utf-8", errors="backslashreplace") as fh:
                fh.write(log_text)

        except Exception as e:
            # il logging non deve mai generare eccezioni
            pass

    def get_python_version(self,):
        return "Python version: %s" % ".".join(map(str, sys.version_info[:3]))

    def get_file(self, file):
        """# return full path of the directory where program resides."""

        return os.path.join(os.path.dirname(__file__), file)

    def busy(self, caller):
        caller.config(cursor="watch")

    def not_busy(self, caller):
        caller.config(cursor="")

    def set_log_user(self, rs: Dict[str, Any]) -> None:
        """
        Set the logged-in user information.

        Args:
            rs: Dictionary with user fields from the users table

        Creates a dictionary with both numeric keys (backward compatibility)
        and string keys (new code).
        """
        self.log_user.clear()

        # Define field names in declaration order (matching users table schema)
        field_names = [
            "user_id",
            "last_name",
            "first_name",
            "nickname",
            "pswrd",         # Column name in DB is 'pswrd', not 'password'
            "role",
            "elapsing_time",
            "enable_time",
            "status"
        ]

        # Populate with both numeric and string keys for compatibility
        for idx, field_name in enumerate(field_names):
            value = rs[field_name]              # Access dict value by key
            self.log_user[idx] = value          # Backward compatibility
            self.log_user[field_name] = value   # New readable access


    def set_zscore(self, value):
        try:
            path = self.get_file('zscore')
            with open(path, 'w') as f:
                f.write(str(value))
        except (FileNotFoundError, IOError) as e:
            self.on_log(inspect.stack()[0][3],
                        e,
                        type(e),
                        sys.modules[__name__])

    def set_ddof(self, value):
        try:
            path = self.get_file('ddof')
            with open(path, 'w') as f:
                f.write(str(value))
        except (FileNotFoundError, IOError) as e:
            self.on_log(inspect.stack()[0][3],
                        e,
                        type(e),
                        sys.modules[__name__])

    def get_section_id(self):

        try:
            path = self.get_file("section_id")
            with open(path, 'r') as f:
                v = f.readline()
            return int(v)
        except (FileNotFoundError, IOError, ValueError) as e:
            self.on_log(inspect.stack()[0][3],
                        e,
                        type(e),
                        sys.modules[__name__])

    def set_section_id(self, value):

        try:
            path = self.get_file("section_id")
            with open(path, "w") as f:
                f.write(str(value))

        except (FileNotFoundError, IOError) as e:
            self.on_log(inspect.stack()[0][3],
                        e,
                        type(e),
                        sys.modules[__name__])

    def get_language(self):
        """
        Read language preference from configuration file.

        Returns:
            str: Language code ('en' or 'it'). Defaults to 'en'.
        """
        try:
            path = self.get_file("language")
            with open(path, 'r', encoding='utf-8') as f:
                lang = f.readline().strip().lower()
            if lang in ("en", "it"):
                return lang
            return "en"
        except FileNotFoundError:
            return "en"
        except (IOError, ValueError) as e:
            self.on_log(inspect.stack()[0][3], e, type(e), sys.modules[__name__])
            return "en"

    def set_language(self, lang):
        """
        Save language preference to configuration file.

        Args:
            lang: Language code ('en' or 'it')

        Returns:
            bool: True if successful, False on error
        """
        try:
            if lang not in ("en", "it"):
                return False
            path = self.get_file("language")
            with open(path, 'w', encoding='utf-8') as f:
                f.write(lang)
            return True
        except (FileNotFoundError, IOError) as e:
            self.on_log(inspect.stack()[0][3], e, type(e), sys.modules[__name__])
            return False

    def get_remember_batch(self):
        """
        Legge il flag 'remember batch' dal file 'remember_batch' e ritorna un bool.
        Ritorna False in caso di file mancante, vuoto o qualsiasi errore.
        """
        try:
            path = self.get_file("remember_batch")
            with open(path, 'r', encoding='utf-8') as f:
                v = f.readline()
            if not v:
                return False
            v = v.strip().lower()
            return v in ("1", "true", "yes", "on")
        except FileNotFoundError:
            # Se il file non esiste ancora, considera False (default sicuro)
            return False
        except Exception as e:
            self.on_log(inspect.stack()[0][3], e, type(e), sys.modules[__name__])
            return False


    def set_remember_batch(self, flag):
        """
        Salva il flag 'remember batch' nel file 'batch_data' come 1/0.
        Accetta True/False, 1/0 o stringhe equivalenti.
        Ritorna True se scrive con successo, False in caso di errore.
        """
        try:
            path = self.get_file("remember_batch")
            val = 1 if (str(flag).strip().lower() in ("1", "true", "yes", "on")) else 0
            with open(path, 'w', encoding='utf-8') as f:
                f.write(str(val))
            return True
        except Exception as e:
            self.on_log(inspect.stack()[0][3], e, type(e), sys.modules[__name__])
            return False


    def get_log_ip(self):
        try:
            return socket.gethostbyname(socket.getfqdn())
        except OSError:
            return "No IP Get."

    def get_log_time(self):
        return datetime.datetime.now()

    def get_log_id(self):
        return self.log_user["user_id"]

    def get_license(self):
        """get license"""
        try:
            path = self.get_file("LICENSE")
            with open(path, "r") as f:
                v = f.read()
            return v
        except (FileNotFoundError, IOError) as e:
            self.on_log(inspect.stack()[0][3],
                        e,
                        type(e),
                        sys.modules[__name__])

    def get_date(self):
        now = datetime.datetime.now()
        return now.strftime("%Y-%m-%d")

    def get_today(self):
        now = datetime.datetime.now()
        return now.strftime("%d-%m-%Y")

    def get_date_format(self):
        """
        Return the configured date format string.

        Returns:
            str: Either 'dd-mm-yyyy' or 'mm-dd-yyyy'
        """
        try:
            path = self.get_file("date_format")
            with open(path, 'r', encoding='utf-8') as f:
                fmt = f.readline().strip()
            # Validate format
            if fmt in ('dd-mm-yyyy', 'mm-dd-yyyy'):
                return fmt
            else:
                return 'dd-mm-yyyy'  # Default to European
        except (FileNotFoundError, IOError) as e:
            self.on_log(inspect.stack()[0][3],
                        e,
                        type(e),
                        sys.modules[__name__])
            return 'dd-mm-yyyy'  # Default to European on error

    def format_date(self, dt):
        """
        Format a datetime object according to the configured date format.

        Args:
            dt: datetime object to format

        Returns:
            str: Formatted date string (e.g., '29-01-2025' or '01-29-2025')
        """
        if dt is None:
            return ""

        try:
            date_format = self.get_date_format()
            if date_format == 'mm-dd-yyyy':
                return dt.strftime("%m-%d-%Y")
            else:  # dd-mm-yyyy (European default)
                return dt.strftime("%d-%m-%Y")
        except (AttributeError, ValueError) as e:
            self.on_log(inspect.stack()[0][3],
                        e,
                        type(e),
                        sys.modules[__name__])
            return ""

    def format_datetime(self, dt):
        """
        Format a datetime object with both date and time according to the configured date format.

        Args:
            dt: datetime object to format

        Returns:
            str: Formatted datetime string (e.g., '29-01-2025 14:35:22' or '01-29-2025 14:35:22')
        """
        if dt is None:
            return ""

        try:
            date_format = self.get_date_format()
            if date_format == 'mm-dd-yyyy':
                return dt.strftime("%m-%d-%Y %H:%M:%S")
            else:  # dd-mm-yyyy (European default)
                return dt.strftime("%d-%m-%Y %H:%M:%S")
        except (AttributeError, ValueError) as e:
            self.on_log(inspect.stack()[0][3],
                        e,
                        type(e),
                        sys.modules[__name__])
            return ""

    def get_time(self):
        return datetime.datetime.now().time()


    def get_observations(self):
        try:
            path = self.get_file('observations')
            with open(path, 'r') as file:
                observations = file.readline().strip()
            return observations
        except (FileNotFoundError, IOError) as e:
            self.on_log(inspect.stack()[0][3],
                        e,
                        type(e),
                        sys.modules[__name__])
            return None

    def set_observations(self, observations):
        try:
            with open('observations', 'w') as f:
                f.write(str(observations))
        except (FileNotFoundError, IOError) as e:
            self.on_log(inspect.stack()[0][3],
                        e,
                        type(e),
                        sys.modules[__name__])
            return None


    def get_correlation_coefficient(self):
        try:
            path = self.get_file("correlation_coefficient")
            with open(path, "r") as file:
                ret = file.readline().strip()
            return float(ret)
        except (FileNotFoundError, IOError, ValueError) as e:
            self.on_log(inspect.stack()[0][3],
                        e,
                        type(e),
                        sys.modules[__name__])
            return None

    def get_icon(self):
        try:
            path = self.get_file("icon")
            with open(path, "r") as f:
                v = f.readline().strip()
            return v
        except (FileNotFoundError, IOError) as e:
            self.on_log(inspect.stack()[0][3],
                        e,
                        type(e),
                        sys.modules[__name__])
            return None

    def get_expiration_date(self, expiration_date):
        try:
            expiry_date = datetime.datetime.strptime(expiration_date, "%d-%m-%Y").date()
            days_until_expiration = (expiry_date - datetime.date.today()).days
            return days_until_expiration
        except (ValueError, TypeError) as e:
            self.on_log(inspect.stack()[0][3],
                        e,
                        type(e),
                        sys.modules[__name__])
            return None

    def get_dimensions(self):
        try:
            dimensions = {}
            path = self.get_file("dimensions")
            with open(path, "r") as filestream:
                for line in filestream:
                    currentline = line.strip().split(",")
                    if len(currentline) == 2:
                        key = currentline[0].strip()
                        value = currentline[1].strip()
                        dimensions[key] = value
                    else:
                        # Skip invalid lines silently (not an error, just malformed data)
                        pass
            return dimensions
        except (FileNotFoundError, IOError) as e:
            self.on_log(inspect.stack()[0][3],
                        e,
                        type(e),
                        sys.modules[__name__])
            return {}

    def launch_document(self, key):
        """
        Launch a document from the documents folder.

        Args:
            key: Document key from documents.json (e.g., "user_manual", "guidelines")

        Returns:
            True if document was launched successfully, False otherwise
        """
        try:
            import json
            config_path = self.get_file("documents.json")

            with open(config_path, 'r', encoding='utf-8') as f:
                documents = json.load(f)

            if key not in documents:
                return False

            filename = documents[key]["filename"]
            path = self.get_file(os.path.join("documents", filename))

            return self.launch(path)

        except Exception as e:
            self.on_log(inspect.stack()[0][3],
                        sys.exc_info()[1],
                        sys.exc_info()[0],
                        sys.modules[__name__])
            return False


def main():
    """
    Test/debug entry point.

    NOTE: Do not use hardcoded credentials in production code.
    Use encrypted config.enc via security.decrypt_config() instead.
    """
    # SECURITY: Commented out hardcoded credentials
    # foo = Engine("biovarase,", "pS2dY^hX1nB5mL", "biovarase")
    # print(foo)
    # input('end')

    print("engine.py main() - Test code disabled. Run biovarase.py instead.")
    print("For setup with encrypted credentials, see deploy/README.md")


if __name__ == "__main__":
    main()
