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
    - Exporter: Data export functionality
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
from launcher import Launcher

APP_TITLE = "Biovarase"

# User role constants (international hierarchy)
ROLE_APP_ADMIN = 0       # Global admin - all orgs, master data, system config
ROLE_COUNTRY_ADMIN = 1   # Country admin - all descendants of country org
ROLE_REGIONAL_ADMIN = 2  # Regional admin - all descendants of region org
ROLE_LAB_ADMIN = 3       # Lab admin - lab config, users, workstations
ROLE_SUPERUSER = 4       # QC supervisor - validation, batch management
ROLE_TECHNICIAN = 5      # Technician - data entry only
ROLE_VIEWER = 6          # Viewer - read-only access

# Legacy aliases for backward compatibility during migration
ROLE_ADMIN = ROLE_APP_ADMIN
ROLE_AUTOLOGIN = ROLE_VIEWER


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


class Engine(DBMS, Controller, QC, Westgards, Exporter, Launcher, Tools,
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
        # Context is initialized at login via init_current_ids_from_user()
  
        
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

        Roles that can validate: App Admin (0), Country Admin (1), Regional Admin (2),
        Lab Admin (3), and Superuser (4). Technicians (5) and Viewers (6) cannot.

        Returns:
            bool: True if user can validate QC results, False otherwise
        """
        role = self.get_user_role()
        return role <= ROLE_SUPERUSER  # Roles 0-4 can validate

    def can_configure_system(self) -> bool:
        """
        Check if user can access global system configuration (master data).

        Only App Admin (role=0) can configure global entities like:
        - Tests, Units, Methods, Samples (global master data)
        - Equipments, Controls (shared across all organizations)
        - Ensures "Glucose is Glucose everywhere"

        Returns:
            bool: True if user can configure system, False otherwise
        """
        role = self.get_user_role()
        return role == ROLE_APP_ADMIN

    def can_modify_data(self) -> bool:
        """
        Check if user can insert/edit data.

        All roles except Viewer (role=6) can modify data:
        - App/Country/Regional/Lab Admin (0-3): Full control within scope
        - Superuser (4): QC management
        - Technician (5): Data entry

        Returns:
            bool: True if user can modify data, False otherwise
        """
        role = self.get_user_role()
        return role <= ROLE_TECHNICIAN  # Roles 0-5 can modify

    def is_read_only(self) -> bool:
        """
        Check if user has read-only access.

        Only Viewer (role=6) is read-only.
        Used for demo kiosks, monitoring screens, or guest access.

        Returns:
            bool: True if user is read-only, False otherwise
        """
        role = self.get_user_role()
        return role >= ROLE_VIEWER  # Only role 6 is read-only

    def get_data_scope(self) -> tuple:
        """
        Get appropriate data filtering scope based on user role and org_id.

        Returns:
            tuple: (scope_type: str, filter_id: int or None)
                - App Admin: ("global", None) - no filtering
                - Country/Regional/Lab Admin: ("org", org_id) - filter by org hierarchy
                - Superuser/Technician/Viewer: ("lab", lab_id) - filter by lab_id

        Example:
            scope, filter_id = self.get_data_scope()
            if scope == "lab":
                sql += " WHERE lab_id = ?"
                args = (filter_id,)
        """
        role = self.get_user_role()

        if role == ROLE_APP_ADMIN:
            return ("global", None)
        else:
            # All non-admin users filter by lab_id (for now)
            # TODO: Implement org hierarchy filtering for Country/Regional admins
            lab_id = self.current_ids.get("lab_id")
            return ("lab", lab_id)

    def can_manage_local_config(self) -> bool:
        """
        Check if user can manage local configuration (workstations, test_methods, batches).

        Lab Admin (3) and above can configure local entities within their scope.

        Returns:
            bool: True if user can manage local config, False otherwise
        """
        role = self.get_user_role()
        return role <= ROLE_LAB_ADMIN  # Roles 0-3 can manage local config

    def is_lab_admin(self) -> bool:
        """
        Check if user is Lab Admin (role=3).

        Lab Admin can configure their lab: workstations, test_methods, users, batches.

        Returns:
            bool: True if user is Lab Admin, False otherwise
        """
        return self.get_user_role() == ROLE_LAB_ADMIN

    def get_user_org_id(self) -> int:
        """
        Return the org_id of the logged user.

        Returns:
            int or None: User's org_id (None for App Admin = global scope)
        """
        return self.log_user.get("org_id")

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

    def init_current_ids_from_user(self, lab_id: int = None) -> bool:
        """
        Initialize current_ids from user's org_id or provided lab org_id.

        Uses organizations table. The lab_id stored in current_ids is actually
        the org_id of the lab-level organization.

        For users assigned to non-lab orgs (country, region, site), finds the
        first lab under their org to use as default.

        Args:
            lab_id: Optional lab org_id override (used by admin lab selector)
                    If None, uses log_user["org_id"]

        Returns:
            True if context was successfully initialized, False otherwise
        """
        try:
            # Use provided lab_id or get from logged user's org_id
            if lab_id is None:
                # IMPORTANT: Use org_id (new field) not lab_id (legacy field)
                lab_id = self.log_user.get("org_id")

            if lab_id is None:
                # No org assigned (admin without selection)
                self.current_ids = {}
                return False

            # Check if this org_id is a lab or something higher in hierarchy
            org_type = self._get_org_type(lab_id)

            if org_type and org_type != "lab":
                # User is assigned to country/region/site - find first lab under it
                first_lab = self._get_first_lab_under_org(lab_id)
                if first_lab:
                    lab_id = first_lab
                else:
                    # No lab found under this org
                    self.current_ids = {}
                    return False

            # Query DB for hierarchical org IDs related to this lab org_id
            row = self.get_idd_by_lab_id(lab_id)
            if not row:
                self.current_ids = {}
                return False

            # current_ids uses lab_id to store the lab's org_id for backward compatibility
            self.current_ids = {
                "site_id": row.get("site_id"),      # region org_id (was site)
                "lab_id": row.get("lab_id", lab_id), # lab org_id
            }

            # Get default section_id (first active section in this lab)
            section_row = self.get_first_section_by_lab(lab_id)
            if section_row:
                self.current_ids["section_id"] = section_row["section_id"]

            return True

        except Exception as e:
            self.on_log("init_current_ids_from_user", e, type(e), sys.modules[__name__])
            self.current_ids = {}
            return False

    def _get_org_type(self, org_id: int) -> str:
        """Get the org_type for a given org_id."""
        sql = "SELECT org_type FROM organizations WHERE org_id = ?"
        row = self.read(False, sql, (org_id,))
        return row["org_type"] if row else None

    def _get_first_lab_under_org(self, org_id: int) -> int:
        """
        Find the first active lab under the given organization (recursive).

        Used for Regional/Country admins who need a default lab context.
        """
        sql = """
            WITH RECURSIVE descendants AS (
                SELECT org_id, org_type, status
                FROM organizations WHERE org_id = ?
                UNION ALL
                SELECT o.org_id, o.org_type, o.status
                FROM organizations o
                JOIN descendants d ON o.parent_id = d.org_id
            )
            SELECT org_id FROM descendants
            WHERE org_type = 'lab' AND status = 1
            ORDER BY org_id
            LIMIT 1
        """
        row = self.read(False, sql, (org_id,))
        return row["org_id"] if row else None

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
        Check if user is App Admin (role=0).

        App Admin has full global access to system configuration and all organizations.

        Returns:
            bool: True if user is App Admin, False otherwise
        """
        return self.get_user_role() == ROLE_APP_ADMIN

    def is_superuser(self) -> bool:
        """
        Check if user is Superuser (role=4).

        Superuser can validate QC and manage batches within their lab.

        Returns:
            bool: True if user is Superuser, False otherwise
        """
        return self.get_user_role() == ROLE_SUPERUSER

    def is_user(self) -> bool:
        """
        Check if user is Technician (role=5).

        Technician can enter QC data in their assigned scope.

        Returns:
            bool: True if user is Technician, False otherwise
        """
        return self.get_user_role() == ROLE_TECHNICIAN

    def can_delete_results(self) -> bool:
        """
        Check if user can delete QC results.

        Roles that can delete: App Admin (0), Country Admin (1), Regional Admin (2),
        Lab Admin (3), and Superuser (4). Technicians and Viewers cannot.

        Returns:
            bool: True if user can delete results, False otherwise
        """
        return self.get_user_role() <= ROLE_SUPERUSER  # Roles 0-4 can delete

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
        """Set busy cursor and force GUI update."""
        caller.config(cursor="wait")
        caller.update()

    def not_busy(self, caller):
        """Restore default cursor and force GUI update."""
        caller.config(cursor="")
        caller.update()

    def start_progress(self, progress_widget, caller):
        """Show and start a progress bar animation.

        Args:
            progress_widget: ttk.Progressbar widget to animate
            caller: Window to update
        """
        progress_widget.pack(side="right", padx=(10, 0))
        progress_widget.start(10)
        caller.update()

    def stop_progress(self, progress_widget, caller):
        """Stop and hide a progress bar.

        Args:
            progress_widget: ttk.Progressbar widget to stop
            caller: Window to update
        """
        progress_widget.stop()
        progress_widget.pack_forget()
        caller.update()

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
        # Note: org_id added after role in migration 013
        field_names = [
            "user_id",
            "last_name",
            "first_name",
            "nickname",
            "pswrd",         # Column name in DB is 'pswrd', not 'password'
            "role",
            "org_id",        # Organization scope (NULL = App Admin, else org hierarchy)
            "lab_id",        # Legacy: Default laboratory (kept for backward compatibility)
            "elapsing_time",
            "enable_time",
            "status"
        ]

        # Populate with both numeric and string keys for compatibility
        for idx, field_name in enumerate(field_names):
            value = rs.get(field_name)          # Use .get() for optional fields
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

    def get_show_expired_batches(self) -> int:
        """
        Read show_expired_batches preference from configuration.

        Returns:
            int: 1 to show expired batches, 0 to hide them.
                 Defaults to 0 (hide expired).
        """
        try:
            with open(self.get_file("show_expired_batches"), "r") as f:
                v = f.readline().strip()
                return int(v)
        except (FileNotFoundError, IOError, ValueError):
            return 0  # default: hide expired batches

    def set_show_expired_batches(self, value: int) -> None:
        """
        Save show_expired_batches preference to configuration file.

        Args:
            value: 1 to show expired, 0 to hide
        """
        try:
            path = self.get_file('show_expired_batches')
            with open(path, 'w') as f:
                f.write(str(value))
        except (FileNotFoundError, IOError) as e:
            self.on_log(inspect.stack()[0][3],
                        e,
                        type(e),
                        sys.modules[__name__])

    def get_show_recent_only(self) -> int:
        """
        Read show_recent_only preference from configuration.

        Returns:
            int: 1 to show only recent batches, 0 to show all.
                 Defaults to 1 (show recent only).
        """
        try:
            with open(self.get_file("show_recent_only"), "r") as f:
                v = f.readline().strip()
                return int(v)
        except (FileNotFoundError, IOError, ValueError):
            return 1  # default: show recent batches only

    def set_show_recent_only(self, value: int) -> None:
        """
        Save show_recent_only preference to configuration file.

        Args:
            value: 1 to show recent only, 0 to show all
        """
        try:
            path = self.get_file('show_recent_only')
            with open(path, 'w') as f:
                f.write(str(value))
        except (FileNotFoundError, IOError) as e:
            self.on_log(inspect.stack()[0][3],
                        e,
                        type(e),
                        sys.modules[__name__])

    def get_section_id(self):
        """
        Return current section_id from context.

        Returns:
            int or None: Current section_id from current_ids
        """
        return self.current_ids.get("section_id")

    def get_lab_id(self):
        """
        Return current lab_id from context.

        Returns:
            int or None: Current lab_id from current_ids
        """
        return self.current_ids.get("lab_id")

    def set_section_id(self, value):
        """
        Update section_id in current_ids.

        Args:
            value: New section_id value
        """
        if value is not None:
            self.current_ids["section_id"] = int(value)

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
        """Return embedded application icon as base64 PNG data."""
        return (
            "iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAYAAADDPmHLAAADvklEQVR4nO2d4XHcIBBGpUw6STl2"
            "G9dDSkgP14ZdTmrBv3RzcSQBgoXd+96b8Q/7NBLDPhbYk+Q1pbSALj9mNwDmggDiIIA4CCAOAoiD"
            "AOIggDg/rS+w3lYKDY2ke1qtzr1aFIIIuh29ZegqAIEfRy8RughA4OfRKkLzIpDgz6W1/5sEIPg+"
            "aInDZQEIvi+uxuOSAATfJ1fiUi0AwfdNbXyqBCD4MaiJE6VgcYoFYPTHojReZABxigRg9MekJG5k"
            "AHEQQJysAKT/2OTiRwYQBwHEQQBxEEAcBBAHAcRBAHEQQBwEEAcBxEEAcRBAHAQQBwHEMX88XJ10"
            "///b2PVm9rR3NWQAQ/aCf/b3GSCAEbkge5HAfAr4+P1hfQl3vP16Kzou3dPy+fcze9z7n/fWJh2S"
            "fT8At4TVUzO6R6wHzt4hEGoR6H1BFZEwa4AIC6qIhBAgyoIqIu4FKA2uJwlKpyUP05d7AaLiIbgl"
            "IIA4oXYBkdimpL1MsH2W7ml6ppARwNMWcr2tbiRwPwXUdE7tVtFq4Xg2+jdmj/wN9wKUsN7WR4em"
            "e3r8bL+f4WH3MLMN7kvBuc45Gkm1ndprRJaM/r3je7Zh5xrxS8G1nfM8z3pmdjtdTwG1o2k2re2d"
            "IYJbASKM3l6wC/jGiHmxN72y1WjxXQqw0dqZkWryz20YKYE7AXrP+yODO0rYnrgSwMr8XMe2Xtei"
            "3aOygJttoPW836teYM33MvHe5z1xlQGWZXwafK4gXsFiq3p2rt7CmlcCvY2wV6HyO5LDg91lACij"
            "18Aa8Z9Dl2Upa/Ds7djVOn7Pdr9kHSDKfX01skYrUx/BFHDAbBlHgQDfKKnIvcroXxYE2GVmYEeX"
            "r90UgryxFWSOsoClJLl7BHpee0gGiPSlTCnWa4SjvujdR8MywEirR2F9R++IPhm6BhhldQ+ibF1b"
            "Gb4G8BhsZdgFiIMA4iCAOAhwwCtuXfdAgBNywY0e/GVBgCyRtq5XoBRcwKsEew8ygDgIIA4CiMO7"
            "ggPAu4KhCW4Lh0MQQBwEEAcBxEEAcRBAHAQQBwHEQQBxEEAcBBAHAcRBAHEQQBwEEAcBxEEAcbIC"
            "nN1NAv7JxY8MIA4CiFMkANNATEriRgYQp1gAskAsSuNFBhCnSgCyQAxq4lSdAZDAN7XxuTQFIIFP"
            "rsTl8hoACXxxNR5Ni0Ak8EFLHJp3AUgwl9b+zz4eXnUyHiUfRq+B11WAx0kRwYzeGddEgH8ugAzN"
            "WE6z5gKAbygFi4MA4iCAOAggDgKIgwDifAEIyYnKq3JXZAAAAABJRU5ErkJggg=="
        )

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
