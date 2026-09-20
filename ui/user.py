# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from ui.child_view import ChildView

# Role constants
ROLE_APP_ADMIN = 0
ROLE_COUNTRY_ADMIN = 1
ROLE_REGIONAL_ADMIN = 2
ROLE_LAB_ADMIN = 3


class UI(ChildView):
    def __init__(self, parent, index=None):
        super().__init__(parent, name="user")

        self.index = index   # None → INSERT, pk → UPDATE

        # Selected record (hybrid dict) in UPDATE mode
        self.selected_item = None

        # Hotkeys
        self.bind("<Alt-s>", self._on_save)
        self.bind("<Return>", self._on_save)
        self.bind("<Alt-r>", self._on_reset)

        # Variables
        self.last_name = tk.StringVar()
        self.first_name = tk.StringVar()
        self.nickname = tk.StringVar()
        self.role = tk.IntVar(value=0)
        self.org_id = tk.IntVar(value=0)  # 0 = no org (app admin)
        self.dict_orgs = {}  # index -> org_id
        self.elapsing_time = tk.IntVar(value=0)
        self.enable_time = tk.BooleanVar(value=False)
        self.status = tk.IntVar(value=1)  # 1 = enabled

        # Layout: two columns (form + buttons)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)

        # --- Build interface ------------------------------------------------
        self._build_ui()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())
        self.show()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        paddings = {"padx": 8, "pady": 8}

        self.frm_main = ttk.Frame(self, style="App.TFrame")
        self.frm_main.grid(row=0, column=0, sticky="nsew")

        frm_left = ttk.Frame(self.frm_main, style="App.TFrame", padding=4)
        frm_left.grid(row=0, column=0, sticky="ns", **paddings)

        r, c = 0, 1
        ttk.Label(frm_left, text="Surname:").grid(row=r, column=0, sticky=tk.W)
        self.txLastName = ttk.Entry(frm_left, textvariable=self.last_name)
        self.txLastName.grid(row=r, column=c, sticky=tk.EW, **paddings)

        r += 1
        ttk.Label(frm_left, text="First Name:").grid(row=r, column=0, sticky=tk.W)
        ttk.Entry(frm_left, textvariable=self.first_name).grid(
            row=r, column=c, sticky=tk.EW, **paddings
        )

        r += 1
        ttk.Label(frm_left, text="Nick:").grid(row=r, column=0, sticky=tk.W)
        ttk.Entry(frm_left, textvariable=self.nickname).grid(
            row=r, column=c, sticky=tk.EW, **paddings
        )

        r += 1
        ttk.Label(frm_left, text="Level:").grid(row=r, column=0, sticky=tk.W)
        self.spnRole = tk.Spinbox(
            frm_left,
            from_=0,
            to=6,
            width=5,
            justify=tk.CENTER,
            wrap=True,
            textvariable=self.role,
            command=self._on_role_changed,
        )
        self.spnRole.grid(row=r, column=c, sticky=tk.W, **paddings)

        r += 1
        # Role hint label
        self.role_hint = tk.StringVar(value="")
        ttk.Label(frm_left, textvariable=self.role_hint, foreground="gray").grid(
            row=r, column=c, sticky=tk.W, padx=8
        )

        r += 1
        ttk.Label(frm_left, text="Organization:").grid(row=r, column=0, sticky=tk.W)
        self.cbOrg = ttk.Combobox(frm_left, state="readonly", width=50)
        self.cbOrg.grid(row=r, column=c, sticky=tk.W, **paddings)

        r += 1
        ttk.Label(frm_left, text="Logout time (min):").grid(
            row=r, column=0, sticky=tk.W
        )
        tk.Spinbox(
            frm_left,
            from_=0,
            to=120,
            width=5,
            justify=tk.CENTER,
            wrap=True,
            textvariable=self.elapsing_time,
        ).grid(row=r, column=c, sticky=tk.W, **paddings)

        r += 1
        ttk.Label(frm_left, text="Enable logout:").grid(
            row=r, column=0, sticky=tk.W
        )
        ttk.Checkbutton(
            frm_left,
            onvalue=1,
            offvalue=0,
            variable=self.enable_time,
        ).grid(row=r, column=c, sticky=tk.W, **paddings)

        r += 1
        ttk.Label(frm_left, text="Status:").grid(row=r, column=0, sticky=tk.W)
        ttk.Checkbutton(
            frm_left,
            onvalue=1,
            offvalue=0,
            variable=self.status,
        ).grid(row=r, column=c, sticky=tk.W, **paddings)

        # Make entry column expand inside frm_left
        frm_left.columnconfigure(0, weight=0)
        frm_left.columnconfigure(1, weight=1)

        # Right: buttons
        frm_buttons = ttk.Frame(self.frm_main, style="App.TFrame")
        frm_buttons.grid(row=0, column=1, sticky="ns", **paddings)

        ttk.Button(
            frm_buttons,
            style="App.TButton",
            text="Save",
            underline=0,
            command=self._on_save,
        ).grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        if self.index is not None:
            ttk.Button(
                frm_buttons,
                style="App.TButton",
                text="Reset",
                underline=0,
                command=self._on_reset,
            ).grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        ttk.Button(
            frm_buttons,
            style="App.TButton",
            text="Cancel",
            underline=0,
            command=self.on_cancel,
        ).grid(row=2, column=0, sticky="ew", padx=5, pady=5)

        # Keep buttons the same width
        frm_buttons.columnconfigure(0, weight=1)

    # ------------------------------------------------------------------ OPEN
    def on_open(self):
        """
        Initialize the form in INSERT or UPDATE mode.

        In UPDATE mode:
            - self.parent.selected_item is expected to be a hybrid dict
              (index + column names) returned by engine.get_selected.
        """
        # Get logged-in user's role to enforce restrictions
        self.logged_user_role = self.engine.log_user.get("role", 5)
        self.logged_user_org_id = self.engine.log_user.get("org_id")

        # Restrict role spinbox: user can only create roles >= their own role
        min_role = max(self.logged_user_role, ROLE_APP_ADMIN)
        self.spnRole.config(from_=min_role)

        if self.index is not None:
            # UPDATE mode - load data first, then orgs based on role
            self.title("Update User")
            self.selected_item = self.parent.selected_item
            self._set_values()
        else:
            # INSERT mode - default to appropriate role based on logged user
            self.title("Add User")
            # Lab Admin creates Superusers by default
            default_role = max(4, min_role)  # Superuser or higher
            self.role.set(default_role)
            self.status.set(1)
            self._load_orgs()
            self._update_role_hint()

        self._focus_entry()

    def _on_role_changed(self):
        """Called when role spinbox changes - update org dropdown and hint."""
        self._load_orgs()
        self._update_role_hint()

    def _update_role_hint(self):
        """Update the role hint label based on current role."""
        role = self.role.get()
        hints = {
            0: "App Admin - Global access",
            1: "Country Admin - Assign to country",
            2: "Regional Admin - Assign to region/site",
            3: "Lab Admin - Assign to lab",
            4: "Superuser - Assign to lab",
            5: "Technician - Assign to lab",
            6: "Viewer - Assign to lab",
        }
        self.role_hint.set(hints.get(role, ""))

    def _get_allowed_org_types(self, role):
        """Return list of allowed org_types for a given role."""
        if role == 0:
            return []  # App Admin: only Global (NULL)
        elif role == 1:
            return ["country"]
        elif role == 2:
            return ["region", "site"]
        else:  # roles 3-6
            return ["lab"]

    def _load_orgs(self):
        """
        Load organizations hierarchy into the combobox, filtered by:
        1. The role being assigned (determines allowed org_types)
        2. The logged-in user's role and scope (restricts visible orgs)
        """
        role = self.role.get()
        allowed_types = self._get_allowed_org_types(role)

        # Build display names with hierarchy path
        self.dict_orgs = {}
        values = []

        # For App Admin (role 0), only show Global option
        if role == 0:
            values.append("(Global - App Admin)")
            self.dict_orgs[0] = None
            self.cbOrg["values"] = values
            self.cbOrg.current(0)
            return

        # Fetch organizations based on logged-in user's scope
        logged_role = getattr(self, "logged_user_role", 0)
        logged_org_id = getattr(self, "logged_user_org_id", None)

        if logged_role == ROLE_APP_ADMIN:
            # App Admin: all organizations
            sql = """
                SELECT org_id, parent_id, org_type, description
                FROM organizations
                WHERE status = 1
                ORDER BY org_type, description
            """
            args = ()
        elif logged_role >= ROLE_LAB_ADMIN:
            # Lab Admin and below: only their own lab
            sql = """
                SELECT org_id, parent_id, org_type, description
                FROM organizations
                WHERE status = 1 AND org_id = ?
                ORDER BY org_type, description
            """
            args = (logged_org_id,)
        else:
            # Country/Regional Admin: organizations in their scope
            sql = """
                WITH RECURSIVE org_tree AS (
                    SELECT org_id, parent_id, org_type, description
                    FROM organizations WHERE org_id = ?
                    UNION ALL
                    SELECT o.org_id, o.parent_id, o.org_type, o.description
                    FROM organizations o
                    JOIN org_tree t ON o.parent_id = t.org_id
                    WHERE o.status = 1
                )
                SELECT * FROM org_tree
                ORDER BY org_type, description
            """
            args = (logged_org_id,)

        rows = self.engine.db.read(True, sql, args) or []

        # Build parent lookup for path generation (need all orgs for path)
        all_orgs_sql = """
            SELECT org_id, parent_id, org_type, description
            FROM organizations WHERE status = 1
        """
        all_rows = self.engine.db.read(True, all_orgs_sql, ()) or []
        org_dict = {row["org_id"]: row for row in all_rows}

        def get_path(org_id):
            """Build full path for an organization."""
            path = []
            current = org_dict.get(org_id)
            while current:
                path.insert(0, current["description"])
                current = org_dict.get(current["parent_id"])
            return " > ".join(path)

        # Filter and sort rows by allowed types
        type_order = {"country": 0, "region": 1, "site": 2, "lab": 3, "section": 4}
        filtered_rows = [r for r in rows if r["org_type"] in allowed_types]
        sorted_rows = sorted(filtered_rows, key=lambda r: (type_order.get(r["org_type"], 99), r["description"]))

        idx = 0
        for row in sorted_rows:
            org_id = row["org_id"]
            path = get_path(org_id)
            values.append(path)
            self.dict_orgs[idx] = org_id
            idx += 1

        self.cbOrg["values"] = values
        if values:
            self.cbOrg.current(0)

    def _focus_entry(self):
        """Focus the surname entry and select its content."""
        try:
            self.txLastName.focus_set()
            self.txLastName.selection_range(0, "end")
        except Exception as e:
            pass

    # ------------------------------------------------------------------ VALUES
    def _set_values(self):
        """
        Populate fields from the selected record (UPDATE mode).

        expected keys in self.selected_item:
            user_id, last_name, first_name, nickname, pswrd,
            role, org_id, lab_id (legacy), elapsing_time, enable_time, status
        """
        s = self.selected_item
        if not s:
            return

        try:
            self.last_name.set(s.get("last_name", ""))
            self.first_name.set(s.get("first_name", ""))
            self.nickname.set(s.get("nickname", ""))
            self.elapsing_time.set(int(s.get("elapsing_time", 0)))
            self.enable_time.set(bool(s.get("enable_time", 0)))
            self.status.set(int(s.get("status", 1)))

            # Set role first, then load orgs filtered by role
            self.role.set(int(s.get("role", 0)))
            self._load_orgs()
            self._update_role_hint()

            # Set organization selection in filtered list
            user_org_id = s.get("org_id")
            org_index = 0  # default: first item
            for idx, oid in self.dict_orgs.items():
                if oid == user_org_id:
                    org_index = idx
                    break
            if self.dict_orgs:
                self.cbOrg.current(org_index)

        except Exception as e:
            self.engine.log.exception("{0} failed".format(inspect.stack()[0][3]))

    def _get_values(self):
        """
        Return current form values as list suitable for SQL arguments.

        Order must match the table definition after the primary key:
            last_name, first_name, nickname, pswrd,
            role, org_id, lab_id, elapsing_time, enable_time, status
        """
        if self.index is not None and self.selected_item:
            # Keep existing password on UPDATE
            pswrd = self.selected_item.get("pswrd")
        else:
            # Generate a new password on INSERT
            pswrd = self.engine.get_new_password()

        # Get selected org_id (NULL for App Admin)
        org_index = self.cbOrg.current()
        org_id = self.dict_orgs.get(org_index)  # Can be None for Global

        # Derive lab_id from org_id for backward compatibility
        # If org is a lab or section, find the lab_id
        lab_id = self._derive_lab_id(org_id)

        return [
            self.last_name.get().strip(),
            self.first_name.get().strip(),
            self.nickname.get().strip(),
            pswrd,
            int(self.role.get()),
            org_id,   # New: organization scope
            lab_id,   # Legacy: for backward compatibility
            int(self.elapsing_time.get()),
            int(bool(self.enable_time.get())),
            int(self.status.get()),
        ]

    def _derive_lab_id(self, org_id):
        """
        Derive lab_id from org_id for backward compatibility.

        - If org is a lab, return its org_id mapped to old lab_id
        - If org is a section, return parent lab's org_id mapped
        - Otherwise return None
        """
        if org_id is None:
            return None

        sql = """
            SELECT org_id, parent_id, org_type
            FROM organizations
            WHERE org_id = ?
        """
        row = self.engine.db.read(False, sql, (org_id,))
        if not row:
            return None

        org_type = row.get("org_type")

        if org_type == "lab":
            # For labs, look up in migration map or use legacy mapping
            # The org_id for labs is old_lab_id + 2000
            # So lab_id = org_id - 2000
            return org_id - 2000 if org_id > 2000 else None

        elif org_type == "section":
            # For sections, get parent (which should be a lab)
            parent_id = row.get("parent_id")
            if parent_id:
                return parent_id - 2000 if parent_id > 2000 else None

        return None

    # ------------------------------------------------------------------ SAVE
    def _on_save(self, evt=None):
        """
        Save handler (INSERT or UPDATE):

            1. Validate fields.
            2. Check nickname uniqueness.
            3. Confirm with user.
            4. Build SQL.
            5. Execute.
            6. Reload parent list and reselect item.
        """
        title = self.engine.app_title

        # 1) Generic field validation
        if self.engine.tools.on_fields_control(self.frm_main, title) is False:
            return

        # 2) Nickname uniqueness check
        if self._check_nicknam() == 0:
            return

        # 3) Confirmation dialog
        if not messagebox.askyesno(
            title,
            self.engine.ask_to_save,
            parent=self,
        ):
            messagebox.showinfo(
                title,
                self.engine.abort,
                parent=self,
            )
            return

        # 4) Build SQL and arguments
        args = self._get_values()

        if self.index is not None:
            # UPDATE path → append primary key at the end
            sql = self.engine.build_sql(self.parent.table, op="update")
            pk = int(self.selected_item.get("user_id"))
            args.append(pk)
            target_id = pk
        else:
            # INSERT path
            sql = self.engine.build_sql(self.parent.table, op="insert")
            target_id = None  # will be resolved from last_id

        last_id = self.engine.db.write(sql, tuple(args))
        if last_id is None:
            err = self.engine.last_write_error
            if err:
                msg = self.engine.tools.get_database_error(err)
            else:
                msg = "Save failed."
            messagebox.showerror(title, msg, parent=self)
            return

        # 5) Refresh parent list
        self.parent._load_items()

        # Determine which PK should be reselected
        if self.index is None and last_id is not None:
            target_id = int(last_id)

        # 6) Reselect row in parent (if possible)
        self._reselect_in_parent(target_id)

        # Close editor
        self.on_cancel()

    def _reselect_in_parent(self, target_pk=None):
        """
        Reselect item in parent Treeview (lstItems):

            - UPDATE: uses PK of selected_item.
            - INSERT: uses target_pk (last inserted id).
        """
        if target_pk is None:
            # For UPDATE, recompute from selected_item
            if self.index is not None and self.selected_item:
                target_pk = int(self.selected_item.get("user_id"))
            else:
                return

        # Treeview iid is str(user_id)
        iid = str(target_pk)
        try:
            self.parent.lstItems.selection_set(iid)
            self.parent.lstItems.see(iid)
            self.parent.lstItems.focus(iid)
            self.parent.on_item_selected()
        except Exception:
            pass

    
    def _on_reset(self, _evt=None):
        """Reset password for the current user (UPDATE mode only)."""
        if self.index is None or not self.selected_item:
            messagebox.showwarning(
                self.engine.app_title,
                "No user selected.",
                parent=self,
            )
            return

        try:
            pswrd = self.engine.get_new_password()
            sql = "UPDATE users SET pswrd = ? WHERE user_id = ?;"
            args = (
                pswrd,
                int(self.selected_item.get("user_id")),   # <-- FIX: use child copy
            )
            self.engine.db.write(sql, args)
            messagebox.showinfo(self.engine.app_title, "Password reset.", parent=self)
        except Exception as e:
            self.engine.log.exception("{0} failed".format(inspect.stack()[0][3]))

    def _check_nicknam(self):
        """
        Check if nickname is already used by another user.

        Returns:
            1  → nickname is valid (unique or same as current user in UPDATE)
            0  → nickname is already taken by another user
        """
        nickname = self.nickname.get().strip()
        if not nickname:
            # Let on_fields_control catch empty fields
            return 1

        sql = "SELECT user_id, nickname FROM users WHERE nickname = ?;"
        try:
            row = self.engine.db.read(False, sql, (nickname,))
        except Exception as e:
            self.engine.log.exception("{0} failed".format(inspect.stack()[0][3]))
            return 1

        if not row:
            # No user with this nickname → OK
            return 1

        existing_id = int(row.get("user_id"))

        # If UPDATE and same user, it's fine
        if self.index is not None and self.selected_item:
            current_id = int(self.selected_item.get("user_id"))
            if existing_id == current_id:
                return 1

        # Otherwise nickname is taken
        msg = "This nickname is already in use."
        messagebox.showwarning(self.engine.app_title, msg, parent=self)
        return 0

    def on_cancel(self, evt=None):
        """Close dialog."""
        super().on_cancel(evt)
