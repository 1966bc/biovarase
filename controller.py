#!/usr/bin/env python3
"""
Controller layer for Biovarase - SQL builders and domain logic.

This module provides the Controller class, which extends DBMS with SQL query builders,
domain-specific business logic, and application-level database operations.

Architecture:
    - DBMS: Base database layer (connection + basic read/write)
    - Controller: This layer (SQL builders + domain logic)
    - Engine: Main orchestrator (combines Controller + QC + Westgards + other mixins)

Responsibilities:
    - Build SQL queries for INSERT/UPDATE/DELETE operations
    - Implement domain-specific data retrieval methods
    - User authentication and authorization
    - Multi-site/lab/section filtering
    - Window instance management and refresh coordination

Key Methods:
    - get_autologin_user(): Auto-login functionality
    - on_login(): User authentication
    - get_selected(): Generic record retrieval by table/field
    - refresh_windows_for_table(): Coordinate UI updates across windows
    - get_new_password(): Generate secure password hashes

Security:
    - Bcrypt password hashing (cost factor 12)
    - SQL identifier validation to prevent injection
    - Role-based access control (admin/superuser/technician)

Classes:
    Controller: SQL builder and domain logic layer

Author: 1966bc (Giuseppe Costanzi)
License: GNU GPL v3
Version: 4.2 (Professional Edition)
"""
import os
import sys
import inspect
import re
from typing import Optional, List, Dict, Tuple, Any, Union

import bcrypt


class Controller:
    """
    Controller layer - SQL builders and domain logic for Biovarase.

    Extends DBMS with application-specific database operations, SQL query builders,
    user authentication, and cross-window coordination logic.

    This layer sits between DBMS (low-level database operations) and Engine
    (high-level orchestration), providing domain-specific data access methods.

    Key Responsibilities:
        - User authentication and authorization (on_login, get_autologin_user)
        - Generic record retrieval (get_selected)
        - Window instance tracking and refresh coordination
        - Multi-site/lab/section filtering

    Authentication & Authorization:
        - Bcrypt password hashing with cost factor 12
        - Role-based access: 0=Admin, 1=Superuser, 2=Technician, 3=Autologin
        - Automatic 'viewer' account for autologin mode
        - Password verification against encrypted database storage

    Window Management:
        - refresh_windows_for_table(): Coordinate UI updates across windows
        - Uses dict_instances registry (provided by Engine)
        - Table-specific refresh logic (batches, tests, results, etc.)

    Security Features:
        - SQL identifier validation (prevents injection via table/field names)
        - Parameterized queries throughout
        - Secure password generation (get_new_password)

    Multi-Site Architecture:
        - Filters data by current site_id, lab_id, section_id
        - Uses get_section_id() from Engine for context

    Example:
        >>> controller = Controller("user", "pass", "biovarase")
        >>> user = controller.on_login("admin", "password")
        >>> if user:
        ...     print(f"Logged in as: {user['username']}")
    """
    def __str__(self) -> str:
        return "class: %s\nMRO: %s" % (self.__class__.__name__,  [x.__name__ for x in Controller.__mro__])


    def get_autologin_user(self) -> Optional[Dict[str, Any]]:
        """
        Return the generic 'viewer' user for autologin as a dict,
        or None if not found or disabled.
        """
        sql = """
            SELECT *
            FROM users
            WHERE nickname = ?
              AND status = 1
            LIMIT 1;
        """
        # Fixed nickname for the generic viewer user
        args = ("viewer",)
        return self.read(False, sql, args)

    def get_test_method_id_by_analyte_and_workstation(
        self,
        analyte: str,
        workstation_id: int,
    ) -> Optional[int]:
        """
        Return test_method_id for a given analyte (tests.description)
        restricted to the given workstation via workstation_test_methods.

        JOIN structure:

            tests t
            JOIN test_methods tm ON t.test_id = tm.test_id
            JOIN workstation_test_methods wtm
                 ON tm.test_method_id = wtm.test_method_id
                AND wtm.workstation_id = ?

        If multiple rows are found, the first one is returned and a warning
        is logged. All rows MUST be active (status = 1).
        """

        sql = """
            SELECT tm.test_method_id
            FROM tests AS t
            INNER JOIN test_methods AS tm
                    ON t.test_id = tm.test_id
            INNER JOIN workstation_test_methods AS wtm
                    ON tm.test_method_id = wtm.test_method_id
                   AND wtm.workstation_id = ?
            WHERE t.description = ?
              AND t.status = 1
              AND tm.status = 1
            ORDER BY tm.test_method_id ASC
            LIMIT 2;
        """

        rows = self.read(True, sql, (workstation_id, analyte))
        if not rows:
            return None

        if len(rows) > 1:
            self.on_log(
                "get_test_method_id_by_analyte_and_workstation",
                RuntimeError(
                    f"Multiple test_methods for analyte='{analyte}' "
                    f"and workstation_id={workstation_id}"
                ),
                RuntimeError,
                sys.modules[__name__],
            )

        return rows[0]["test_method_id"]


    def get_batch_id_by_lot_and_test_method(
        self,
        lot_number: str,
        test_method_id: int,
        workstation_id: int,
    ) -> Optional[int]:
        """
        Return batch_id for the given lot_number, test_method_id and workstation_id.
        """
        sql = """
            SELECT
                batch_id
            FROM batches
            WHERE lot_number = ?
              AND test_method_id = ?
              AND workstation_id = ?
              AND status = 1
            LIMIT 2;
        """
        rows = self.read(True, sql, (lot_number, test_method_id, workstation_id))
        if not rows:
            return None

        if len(rows) > 1:
            self.on_log(
                "get_batch_id_by_lot_and_test_method",
                RuntimeError(
                    f"Multiple batches for lot_number='{lot_number}', "
                    f"test_method_id={test_method_id}, workstation_id={workstation_id}"
                ),
                RuntimeError,
                sys.modules[__name__],
            )

        return rows[0]["batch_id"]

    def import_qc_file_auto(
        self,
        filepath: str,
        received_ts: Any,
        workstation_id: int,
        reagent_lot: str,
    ) -> Tuple[int, int, int, str]:
        """
        High-level QC import workflow.

        Args:
            filepath: Path to QC file (any filename accepted)
            received_ts: Timestamp when samples were received
            workstation_id: Workstation ID from GUI selection
            reagent_lot: Reagent lot number from GUI (or "NOT ASSIGNED")

        Steps:
          1. Get device_id from workstations table using workstation_id
          2. Use Importer.get_generic_file_auto() to parse the file with device_id
          3. For each normalized row:
               - Extract reagent_lot from file (if available) or use GUI value
               - Resolve test_method_id (analyte + workstation)
               - Resolve batch_id (lot_number + test_method_id + workstation)
               - Insert row into 'results' table with reagent_lot

        Returns:
          imported_rows, matched_batches, not_matched_rows, profile_name
        """
        # 1) Get device_id from workstations table
        try:
            sql = """SELECT device_id
                     FROM workstations
                     WHERE workstation_id = ?"""
            row = self.read(False, sql, (workstation_id,))
            if not row:
                self.on_log(
                    "import_qc_file_auto",
                    f"Workstation not found: workstation_id={workstation_id}",
                    ValueError,
                    sys.modules[__name__],
                )
                return 0, 0, 0, ""
            device_id = row["device_id"]
        except Exception as e:
            self.on_log(
                "import_qc_file_auto",
                e,
                type(e),
                sys.modules[__name__],
            )
            return 0, 0, 0, ""

        # 2) Parse file using device_id from database
        rows, _device_id, profile_name = self.get_generic_file_auto(filepath, device_id)
        if not rows:
            return 0, 0, 0, profile_name or ""

        # 3) Process imported rows

        imported = 0
        matched = 0
        not_matched = 0

        # 3) INSERT SQL
        sql_insert = self.build_sql("results", "insert")

        for item in rows:
            analyte = item["analyte"]
            lot_number = item["lot_number"]
            result_val = float(item["result"])

            # Extract reagent_lot from file if available, otherwise use GUI value
            reagent_lot_value = item.get("reagent_lot") or reagent_lot
            if not reagent_lot_value:
                reagent_lot_value = "NOT ASSIGNED"

            # 3a) test_method_id
            test_method_id = self.get_test_method_id_by_analyte_and_workstation(
                analyte,
                workstation_id,
            )
            if not test_method_id:
                not_matched += 1
                continue

            # 3b) batch_id
            batch_id = self.get_batch_id_by_lot_and_test_method(
                lot_number,
                test_method_id,
                workstation_id,
            )
            if not batch_id:
                not_matched += 1
                continue

            # 3c) INSERT into results
            try:
                args = (
                    batch_id,               # batch_id
                    self.get_lab_id(),      # lab_id (multi-tenant)
                    "0",                    # run_number (MANDATORY, cannot be NULL)
                    workstation_id,         # workstation_id
                    reagent_lot_value,      # reagent_lot
                    result_val,             # result
                    received_ts,            # received (timestamp)
                    1,                      # status
                    0,                      # validated (new results are unvalidated)
                    None,                   # validated_by (NULL until validated)
                    None,                   # validated_at (NULL until validated)
                    0,                      # is_delete
                    self.get_log_time(),    # log_time
                    self.get_log_id(),      # log_id
                    self.get_log_ip(),      # log_ip
                )

                self.write(sql_insert, args)
                imported += 1
                matched += 1

            except Exception as e:
                self.on_log(
                    "import_qc_file_auto",
                    e,
                    type(e),
                    sys.modules[__name__],
                )
                not_matched += 1

        return imported, matched, not_matched, profile_name or ""



    def close_instance(self, name: str) -> None:
        """
        Close a registered window instance by name.

        If the instance exists and is still alive, closes it.
        Use this for ChildView dialogs before creating a new one
        to switch context (e.g., editing a different record).

        Args:
            name: Window name as registered in dict_instances
        """
        registry = getattr(self, "dict_instances", None)
        if not registry:
            return
        instance = registry.get(name)
        if instance is not None:
            try:
                if instance.winfo_exists():
                    instance.on_cancel()
            except Exception:
                pass
            # Ensure cleanup
            registry.pop(name, None)

    def refresh_windows_for_table(self, table_name: str) -> None:
        """
        Central dispatcher for cross-window GUI refreshes after editing lookup tables.
        """
        registry = getattr(self, "dict_instances", None)
        if not registry:
            return

        # ------------------------- MAPPING -------------------------
        mapping = {
            "suppliers": (
                "sites",
                "labs",
                "sections",
                "workstation_test_methods",
                "test_methods",
            ),
            "sites": (
                "labs",
                "sections",
                "workstation_test_methods",
                "test_methods",
            ),
            "labs": (
                "sections",
                "workstation_test_methods",
                "test_methods",
            ),
            "sections": (
                "workstation_test_methods",
                "test_methods",
                "batches",
            ),
            "batches": (
                "main",
            ),
            "tests": (
                "tests",
                "test_methods",
                "workstation_test_methods",
            ),
            "equipments": (
                "workstations",
            ),
            "workstation_test_methods": (
                "workstation_test_methods",
                "main",
            ),

        }

        # ------------------------- DEFAULT METHODS -------------------------
        refresh_methods = {
            "sites": "set_values",
            "labs": "_load_tree",
            "sections": "_load_tree",
            "workstation_test_methods": "_load_tree",
            "main": "set_batches",
            "tests": "set_values",                  # lookup sui tests
            "test_methods": "refresh_context_from_section",
            "batches": "_load_tree",
            "workstations": "refresh_workstations", 
        }

        targets = mapping.get(table_name, ())
        if not targets:
            return

        # ------------------------- MAIN LOOP -------------------------
        for name in targets:
            win = registry.get(name)
            if not win:
                continue

            try:
                if callable(getattr(win, "winfo_exists", None)) and not win.winfo_exists():
                    continue

                # 1) Get default refresh method
                method_name = refresh_methods.get(name)

                # ---------------- SPECIAL CASES ----------------
                if name == "test_methods" and table_name == "tests":
                    # Reload TEST list
                    method_name = "_load_tests"

                if name == "workstation_test_methods" and table_name == "tests":
                    # Update only the test side of the Workstation ↔ Test Methods window
                    method_name = "refresh_from_tests"

                # When workstation_test_methods change, update the workstations list
                # on the main window
                if name == "main" and table_name == "workstation_test_methods":
                    method_name = "set_workstations"
                # ------------------------------------------------

                # 2) Execute refresh method
                if method_name and hasattr(win, method_name):
                    getattr(win, method_name)()

            except Exception as e:
                print(e)


    def get_primary_key(self, table_name: str) -> str:
        # Use cache to avoid re-querying INFORMATION_SCHEMA
        if "_pk_cache" not in self.__dict__:
            self._pk_cache = {}

        if table_name in self._pk_cache:
            return self._pk_cache[table_name]

        sql = """
            SELECT k.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS t
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE k
              ON t.CONSTRAINT_NAME = k.CONSTRAINT_NAME
             AND t.TABLE_SCHEMA = k.TABLE_SCHEMA
             AND t.TABLE_NAME = k.TABLE_NAME
            WHERE t.TABLE_SCHEMA = DATABASE()
              AND t.TABLE_NAME = ?
              AND t.CONSTRAINT_TYPE = 'PRIMARY KEY'
            LIMIT 1;
        """

        rs = self.read(False, sql, (table_name,))

        if not rs:
            raise RuntimeError(f"No primary key found for table '{table_name}'")

        pk = rs["COLUMN_NAME"]
        self._pk_cache[table_name] = pk
        return pk



    def on_login(self, args: Tuple[str, bytes]) -> Optional[Dict[str, Any]]:
        """
        Authenticate user by nickname and password.

        Args:
            args: Tuple of (nickname, password) where password is bytes

        Returns:
            User record as dict if authentication succeeds, None otherwise
        """
        nick, password = args
        password = password.strip()  # Remove whitespace (already byte string)

        # Fetch user record with hashed password
        sql = "SELECT * FROM users WHERE nickname = ?;"
        user = self.read(False, sql, (nick,))

        if not user:
            return None

        # Verify password against stored hash
        hashed_password_from_db = user["pswrd"].encode('utf-8')
        if bcrypt.checkpw(password, hashed_password_from_db):
            return user  # Already a complete dict with all fields

        return None

    def get_new_password(self) -> bytes:
        new_password = b'pass'
        # Generate a salt and hash the password
        hashed_password = bcrypt.hashpw(new_password, bcrypt.gensalt())
        return hashed_password

    def get_company_data(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve hierarchical organization information for the current lab context.

        Returns country, region, lab, section names from organizations table.
        Uses the current lab_id from current_ids.
        """
        lab_id = self.current_ids.get("lab_id")
        if not lab_id:
            return None

        # Get lab and its ancestors using recursive CTE
        sql = """
            WITH RECURSIVE ancestors AS (
                SELECT org_id, parent_id, org_type, description
                FROM organizations WHERE org_id = ?
                UNION ALL
                SELECT o.org_id, o.parent_id, o.org_type, o.description
                FROM organizations o
                JOIN ancestors a ON o.org_id = a.parent_id
            )
            SELECT
                org_type, description
            FROM ancestors
            ORDER BY FIELD(org_type, 'country', 'region', 'site', 'lab', 'section')
        """
        rows = self.read(True, sql, (lab_id,))
        if not rows:
            return None

        # Build result dict mapping org_type to description
        result = {"lab_id": lab_id}
        for row in rows:
            result[row["org_type"]] = row["description"]

        return result

    def get_selected(self, table: str, field: str, pk: Any) -> Optional[Dict[Union[int, str], Any]]:
        """
        Return a single row from the given table.

        Backward compatible behavior:
          - numeric keys:    record[0], record[1], ...  (old style)
          - named keys:      record['column_name']      (new style)

        Args:
            table: table name
            field: column name used in WHERE clause (usually PK)
            pk: value to match in the WHERE clause

        Returns:
            Hybrid dictionary (both int and str keys) or None if no row is found

        Raises:
            ValueError: If table or field name contains invalid characters
        """
        # Validate table and field names to prevent SQL injection
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table):
            raise ValueError(
                f"Invalid SQL table name: '{table}'. "
                f"Must match pattern: ^[a-zA-Z_][a-zA-Z0-9_]*$"
            )
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', field):
            raise ValueError(
                f"Invalid SQL column name: '{field}'. "
                f"Must match pattern: ^[a-zA-Z_][a-zA-Z0-9_]*$"
            )

        sql = f"SELECT * FROM {table} WHERE {field} = ?;"
        row = self.read(False, sql, (pk,))

        if row is None:
            return None

        hybrid = {}

        # Preserve order from read: Python 3.7+ dicts are ordered.
        for idx, (col, value) in enumerate(row.items()):
            # Old style: record[0], record[1], ...
            hybrid[idx] = value
            # New style: record['column_name']
            hybrid[col] = value
        #print(hybrid)
        return hybrid

    def get_series(
        self,
        batch_id: int,
        workstation_id: int,
        limit: Optional[int] = None,
        result_id: Optional[int] = None
    ) -> List[float]:
        """
        Retrieve QC results series for a given batch and workstation.

        Args:
            batch_id: Batch identifier
            workstation_id: Workstation identifier
            limit: Maximum number of results to retrieve
            result_id: Optional upper limit for result_id (inclusive)

        Returns:
            List of results (floats) in chronological order (oldest to newest)
        """
        series = []

        if result_id is not None:
            sql = """
                SELECT ROUND(result, 2) AS result, status
                FROM results
                WHERE batch_id = ?
                  AND result_id <= ?
                  AND workstation_id = ?
                  AND is_delete = 0
                ORDER BY received DESC
                LIMIT ?;
            """
            args = (batch_id, result_id, workstation_id, limit)
        else:
            sql = """
                SELECT ROUND(result, 2) AS result, status
                FROM results
                WHERE batch_id = ?
                  AND workstation_id = ?
                  AND is_delete = 0
                ORDER BY received DESC
                LIMIT ?;
            """
            args = (batch_id, workstation_id, limit)

        rs = self.read(True, sql, args)

        if not rs:
            return series

        # Filter out disabled records (status = 0)
        active_results = [row for row in rs if row["status"] != 0]

        # Reverse to get chronological order (oldest first)
        for row in reversed(active_results):
            series.append(row["result"])

        return series

    def get_lab_id(self) -> Optional[int]:
        """Return the lab_id for the current section loaded in memory."""
        return self.current_ids.get("lab_id")

    def get_idd_by_section_id(self, section_id: int) -> Optional[Dict[str, int]]:
        """
        Return the hierarchical IDs for a given section_id as a dict:

            {
                "site_id": ...,
                "supplier_id": ...,
                "comp_id": ...,
                "lab_id": ...,
                "section_id": ...
            }

        Returns None / {} if no row is found (depending on read implementation).

        Note: Now uses organizations table. Returns dict with org hierarchy.
        For backward compatibility, also includes legacy keys mapped to org_ids.
        """
        # Get the org and its ancestors using recursive CTE
        sql = """
            WITH RECURSIVE ancestors AS (
                SELECT org_id, parent_id, org_type, description
                FROM organizations WHERE org_id = ?
                UNION ALL
                SELECT o.org_id, o.parent_id, o.org_type, o.description
                FROM organizations o
                JOIN ancestors a ON o.org_id = a.parent_id
            )
            SELECT org_id, org_type FROM ancestors
        """
        rows = self.read(True, sql, (section_id,))
        if not rows:
            return None

        # Build result dict with both new and legacy keys
        result = {}
        for row in rows:
            org_type = row["org_type"]
            org_id = row["org_id"]
            result[f"{org_type}_org_id"] = org_id

            # Legacy key mapping for backward compatibility
            if org_type == "section":
                result["section_id"] = org_id
                result[4] = org_id  # Tuple index 4
            elif org_type == "lab":
                result["lab_id"] = org_id
                result[3] = org_id  # Tuple index 3
                result[1] = org_id  # Legacy index for lab_id
            elif org_type == "region":
                result["site_id"] = org_id  # region = site in old model
                result[0] = org_id  # Tuple index 0
            elif org_type == "country":
                result["country_org_id"] = org_id

        return result

    def get_idd_by_lab_id(self, lab_id: int) -> Optional[Dict[str, int]]:
        """
        Return the hierarchical IDs for a given lab_id (org_id) as a dict.

        Now uses organizations table.

        Returns None if no row is found.
        """
        # Get the lab and its ancestors using recursive CTE
        sql = """
            WITH RECURSIVE ancestors AS (
                SELECT org_id, parent_id, org_type, description
                FROM organizations WHERE org_id = ?
                UNION ALL
                SELECT o.org_id, o.parent_id, o.org_type, o.description
                FROM organizations o
                JOIN ancestors a ON o.org_id = a.parent_id
            )
            SELECT org_id, org_type FROM ancestors
        """
        rows = self.read(True, sql, (lab_id,))
        if not rows:
            return None

        # Build result dict
        result = {"lab_id": lab_id}
        for row in rows:
            org_type = row["org_type"]
            org_id = row["org_id"]
            result[f"{org_type}_org_id"] = org_id
            if org_type == "region":
                result["site_id"] = org_id

        return result

    def get_first_section_by_lab(self, lab_id: int) -> Optional[Dict[str, Any]]:
        """
        Return the first active section for a given lab_id (org_id).

        Used to set a default section when initializing context from lab_id.
        Now uses organizations table.

        Args:
            lab_id: The laboratory org_id

        Returns:
            Dict with section_id (org_id), or None if no sections found
        """
        sql = """
            SELECT org_id AS section_id
            FROM organizations
            WHERE parent_id = ?
              AND org_type = 'section'
              AND status = 1
            ORDER BY org_id
            LIMIT 1;
        """
        return self.read(False, sql, (lab_id,))

    def get_lab_id_by_section_id(self, section_id: int) -> Optional[int]:
        """
        Return the lab_id (org_id) associated with the given section_id (org_id).

        Uses organizations table - gets parent of section.

        Args:
            section_id: The section org_id

        Returns:
            The lab org_id if found, otherwise None
        """
        sql = """
            SELECT parent_id AS lab_id
            FROM organizations
            WHERE org_id = ? AND org_type = 'section';
        """

        row = self.read(False, sql, (section_id,))
        if not row:
            return None

        return row["lab_id"]

    def get_test_name(self, test_id: int) -> Optional[str]:
        """
        Return test description for given test_id.

        Args:
            test_id: Test identifier

        Returns:
            Test description (str) or None if not found
        """
        sql = "SELECT description FROM tests WHERE test_id = ?;"
        row = self.read(False, sql, (test_id,))
        return row["description"] if row else None

    def get_control_name(self, control_id: int) -> Optional[str]:
        """
        Return control description for given control_id.

        Args:
            control_id: Control identifier

        Returns:
            Control description (str) or None if not found
        """
        sql = "SELECT description FROM controls WHERE control_id = ?;"
        row = self.read(False, sql, (control_id,))
        return row["description"] if row else None

    def get_um(self, unit_id: int) -> Optional[Dict[str, Any]]:
        """
        Return unit of measurement as a dict like:
            {'description': 'mg/dL'}

        or None if not found or on error.
        """
        sql = """
            SELECT description
            FROM units
            WHERE unit_id = ? AND status = 1;
        """
        return self.read(False, sql, (unit_id,))

    def get_mandatory(self) -> List[str]:
        """
        Return list of mandatory test descriptions for current lab.

        Returns:
            List of test description strings (may be empty)
        """
        mandatory_tests = []

        sql = """
            SELECT tests.description
            FROM tests
            INNER JOIN test_methods ON tests.test_id = test_methods.test_id
            INNER JOIN sections ON test_methods.section_id = sections.section_id
            WHERE sections.lab_id = ?
              AND test_methods.is_mandatory = 1
              AND test_methods.status = 1;
        """

        rows = self.read(True, sql, (self.get_lab_id(),))

        if rows:
            mandatory_tests = [row["description"] for row in rows]

        return mandatory_tests

    def get_test_method_with_goals(self, test_method_id: int) -> Optional[Dict[str, Any]]:
        """
        Return a unified dictionary containing:
          - all fields from test_methods
          - matching goals fields (cvw, cvb, bias, teap005, teap001, to_export)
        
        If no goals exist for this test method, the fields are returned as None.
        """

        sql = """
            SELECT 
                tm.*, 
                g.cvw,
                g.cvb,
                g.imp,
                g.bias,
                g.teap005,
                g.teap001,
                g.to_export
            FROM test_methods AS tm
            LEFT JOIN goals AS g
                   ON g.test_method_id = tm.test_method_id
                  AND g.status = 1
            WHERE tm.test_method_id = ?;
        """

        return self.read(False, sql, (test_method_id,))
