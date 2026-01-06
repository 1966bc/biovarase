# -*- coding: utf-8 -*-
"""
Tools Module - Style and utilities for Biovarase.

This module provides style configuration and helper methods.
Used as a mixin class inherited by Engine.

Author: 1966bc (Giuseppe Costanzi)
License: GNU GPL v3
Version: 4.2 (Professional Edition)
"""
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional, Any, List


class Tools:
    """Style configuration and utilities."""

    BASE_BG_RGB = (240, 240, 237)

    def __init__(self) -> None:
        """Initialize shared style instance."""
        self._style = ttk.Style()

    def __str__(self) -> str:
        return f"class: {self.__class__.__name__}"

    # -------------------------------------------------------------------------
    # Style Configuration
    # -------------------------------------------------------------------------
    def set_style(self, style: ttk.Style) -> None:
        """Set a unified theme and styles for the application widgets."""
        style.theme_use("clam")

        bg_color = self.get_rgb(*self.BASE_BG_RGB)
        style.configure(".", background=bg_color, font=('TkFixedFont'))

        # Treeview styling
        style.map('Treeview',
                  foreground=self.fixed_map('foreground'),
                  background=self.fixed_map('background'))

        style.configure("Treeview.Heading",
                        background=bg_color,
                        font=("TkFixedFont", 10, "italic"))

        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

        # StatusBar styling
        style.configure("StatusBar.TFrame",
                        relief=tk.FLAT,
                        padding=4,
                        background=bg_color)

        style.configure("LoggedUser.TLabel",
                        font=("TkDefaultFont", 10, 'bold'),
                        relief=tk.FLAT,
                        foreground='blue')

        # Application widget styles
        style.configure("App.TLabel",
                        background=bg_color,
                        padding=2,
                        anchor=tk.W,
                        font="TkFixedFont")

        style.configure("App.TLabelframe",
                        background=bg_color,
                        relief=tk.GROOVE,
                        padding=2,
                        font="TkFixedFont")

        style.configure("App.TFrame",
                        background=bg_color)

        style.configure("Panel.TFrame",
                        background=bg_color,
                        relief=tk.GROOVE,
                        padding=8)

        style.configure("App.TButton",
                        background=bg_color,
                        padding=5,
                        border=1,
                        relief=tk.RAISED,
                        font="TkFixedFont")

        style.configure("App.TRadiobutton",
                        background=bg_color,
                        padding=4,
                        font="TkFixedFont")

        style.configure("App.TCombobox",
                        background=bg_color,
                        font="TkFixedFont")

        style.configure("Data.TLabel",
                        font=('Helvetica', 12, 'bold'))

        # QC-specific styles
        style.configure("Target.TLabel",
                        foreground=self.get_rgb(255, 69, 0),
                        background=self.get_rgb(255, 255, 255))

        style.configure("Average.TLabel",
                        foreground=self.get_rgb(25, 102, 188),
                        background=self.get_rgb(255, 255, 255))

        style.configure("westgard_violation.TLabel",
                        background=self.get_rgb(255, 106, 106))

        style.configure("westgard_ok.TLabel",
                        background=self.get_rgb(152, 251, 152))

        style.configure("black_and_white.TLabel",
                        background=self.get_rgb(255, 255, 255),
                        foreground=self.get_rgb(77, 77, 77))

    # -------------------------------------------------------------------------
    # Color Utilities
    # -------------------------------------------------------------------------
    def get_rgb(self, r: int, g: int, b: int) -> str:
        """Convert RGB integers to a Tkinter-friendly hex color."""
        return "#%02x%02x%02x" % (r, g, b)

    def get_base_bg_color_hex(self) -> str:
        """Returns the application's base background color in Tkinter hex format."""
        return self.get_rgb(*self.BASE_BG_RGB)

    def fixed_map(self, option: str) -> List[tuple]:
        """Fix style map for Treeview to support themed widgets in Tk 8.6.9."""
        style = ttk.Style()
        return [elm for elm in style.map('Treeview', query_opt=option)]

    # -------------------------------------------------------------------------
    # Window Utilities
    # -------------------------------------------------------------------------
    def center_window(self, window: Any, on_screen: bool = False) -> None:
        """
        Center a window on its parent or on screen.

        Args:
            window: The Toplevel window to center
            on_screen: If True, center on screen. If False (default), center on parent.
        """
        window.update_idletasks()

        if on_screen:
            ref_x = 0
            ref_y = 0
            ref_width = window.winfo_screenwidth()
            ref_height = window.winfo_screenheight()
        else:
            parent = window.parent
            ref_x = parent.winfo_rootx()
            ref_y = parent.winfo_rooty()
            ref_width = parent.winfo_width()
            ref_height = parent.winfo_height()

        min_w, min_h = window.wm_minsize()
        width = max(window.winfo_reqwidth(), min_w)
        height = max(window.winfo_reqheight(), min_h)
        x = ref_x + (ref_width - width) // 2
        y = ref_y + (ref_height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")

    def safe_close(self, win: Any) -> None:
        """
        Safely close a Toplevel window.

        - Destroy child window (if any and still alive).
        - Reset class-level _instance (if present).
        - Destroy the window itself.
        """
        try:
            child = getattr(win, "child", None)
            if child and child.winfo_exists():
                child.destroy()
        except Exception:
            pass

        cls = type(win)
        if hasattr(cls, "_instance"):
            cls._instance = None

        try:
            win.destroy()
        except Exception:
            pass

    def close_unregistered_toplevels(self, root: tk.Misc) -> None:
        """
        Close all Toplevel windows that are NOT registered in self.dict_instances.

        Args:
            root: Typically self.nametowidget(".") when called from a widget
        """
        registry = getattr(self, "dict_instances", {})
        registered = set(registry.values())

        try:
            for widget in root.winfo_children():
                if isinstance(widget, tk.Toplevel):
                    if widget not in registered:
                        self.safe_close(widget)
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # Widget Factories (minimal set)
    # -------------------------------------------------------------------------
    def create_button(self, parent: Any, text: str, command: Callable,
                      width: int = 10, underline: int = 0, **kwargs) -> ttk.Button:
        """
        Create a standard application button.

        Args:
            parent: Parent widget
            text: Button text
            command: Callback function
            width: Button width (default 10)
            underline: Index of character to underline for Alt+key (default 0)

        Returns:
            ttk.Button with standard application style
        """
        return ttk.Button(
            parent,
            text=text,
            command=command,
            width=width,
            underline=underline,
            style="App.TButton",
            **kwargs
        )

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------
    def get_validate_integer(self, caller: Any) -> tuple:
        """Return validation tuple for integer fields."""
        return (caller.register(self.validate_integer), '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')

    def validate_integer(self, action: str, index: str, value_if_allowed: str,
                         prior_value: str, text: str, validation_type: str,
                         trigger_type: str, widget_name: str) -> bool:
        """Validate integer input in real time."""
        if action == '1':
            if text in '0123456789':
                try:
                    int(value_if_allowed)
                    return True
                except ValueError:
                    return False
            return False
        return True

    def get_float_vcmd(self, caller: Any) -> tuple:
        """Return validation tuple for float fields."""
        return (caller.register(self.validate_float), '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')

    def validate_float(self, action: str, index: str, value_if_allowed: str,
                       prior_value: str, text: str, validation_type: str,
                       trigger_type: str, widget_name: str) -> bool:
        """Validate float input in real time."""
        if action == "1":
            if text in '0123456789.-+':
                try:
                    float(value_if_allowed)
                    return True
                except ValueError:
                    return False
            return False
        return True

    def limit_chars(self, c: int, v: tk.StringVar, *args: Any) -> None:
        """Limit characters in a StringVar to a given length."""
        if len(v.get()) > c:
            v.set(v.get()[:-1])

    def _iter_widgets(self, container: Any):
        """Recursively iterate over all descendant widgets."""
        stack = [container]
        while stack:
            w = stack.pop()
            yield w
            if hasattr(w, "winfo_children"):
                stack.extend(w.winfo_children())

    def on_fields_control(self, container: Any, title: Optional[str] = None) -> bool:
        """
        Validate that all required fields are properly filled.

        Args:
            container: Widget container to validate
            title: Dialog title for warning messages

        Returns:
            True if all fields valid, False otherwise
        """
        title = title or "Biovarase"

        for field in self._iter_widgets(container):
            try:
                state = str(field.cget("state")) if hasattr(field, "cget") else ""
            except Exception:
                state = ""

            if state in ("disabled", "readonly"):
                continue
            if hasattr(field, "winfo_viewable") and not field.winfo_viewable():
                continue

            # Entry validation
            if isinstance(field, (ttk.Entry, tk.Entry)):
                if not field.get().strip():
                    messagebox.showwarning(title, "Please fill all fields.", parent=container)
                    field.focus_set()
                    return False

            # Combobox validation
            elif isinstance(field, ttk.Combobox):
                text = field.get().strip()
                if not text:
                    messagebox.showwarning(title, "Please fill all fields.", parent=container)
                    field.focus_set()
                    return False
                try:
                    values = tuple(field.cget("values") or ())
                except Exception:
                    values = ()
                if text not in [str(v) for v in values]:
                    messagebox.showwarning(title, "You can choose only a value from the list.", parent=container)
                    field.focus_set()
                    return False

        return True

    # -------------------------------------------------------------------------
    # Text Utilities
    # -------------------------------------------------------------------------
    @staticmethod
    def normalize_desc(value: str, compress: bool = True) -> str:
        """
        Normalize a textual description.

        Args:
            value: Raw string value.
            compress: If True, collapse multiple spaces into a single one.

        Returns:
            Normalized string (empty string if input is falsy).
        """
        if not value:
            return ""
        s = value.strip()
        if compress:
            s = " ".join(s.split())
        return s

    # -------------------------------------------------------------------------
    # Treeview Utilities
    # -------------------------------------------------------------------------
    def parse_iid(self, iid: str) -> dict:
        """
        Parse a Treeview item identifier like 'lab_7' or 'section_12'.

        Returns:
            dict: {'type': 'lab', 'id': 7} or {} if invalid.
        """
        try:
            if not iid or "_" not in iid:
                return {}
            kind, id_str = iid.split("_", 1)
            return {"type": kind, "id": int(id_str)}
        except Exception:
            return {}

    def clear_treeview(self, tree: ttk.Treeview) -> None:
        """Clear all items from a Treeview widget."""
        for iid in tree.get_children():
            tree.delete(iid)

    def clear_listbox(self, listbox: tk.Listbox) -> None:
        """Clear all items from a Listbox widget."""
        listbox.delete(0, tk.END)

    # -------------------------------------------------------------------------
    # Button Factory with Hotkey
    # -------------------------------------------------------------------------
    def add_button(self, parent: Any, text: str, command: Callable,
                   hotkey: Optional[str] = None, window: Any = None) -> ttk.Button:
        """
        Create a button and optionally bind a hotkey.

        Args:
            parent: Parent widget for the button
            text: Button text
            command: Callback function
            hotkey: Optional hotkey like "<Alt-a>"
            window: Window to bind hotkey to (defaults to parent's toplevel)

        Returns:
            ttk.Button instance
        """
        btn = ttk.Button(
            parent,
            style="App.TButton",
            text=text,
            command=command,
        )
        btn.pack(fill=tk.X, pady=4)

        if hotkey:
            target = window or parent.winfo_toplevel()
            target.bind(hotkey, lambda e: command())

        return btn

    # -------------------------------------------------------------------------
    # Child Window Management
    # -------------------------------------------------------------------------
    def open_child(self, parent: Any, child_class: type,
                   index: Any = None, **kwargs) -> Any:
        """
        Safely open a child editor window, destroying any previous instance.

        Args:
            parent: Parent window (must have 'child' attribute)
            child_class: The UI class to instantiate
            index: Primary key for UPDATE mode, None for INSERT mode
            **kwargs: Additional arguments passed to child_class

        Returns:
            The new child window instance
        """
        # Destroy existing child if open
        try:
            child = getattr(parent, "child", None)
            if child is not None and child.winfo_exists():
                child.destroy()
        except Exception:
            pass

        # Create new child
        parent.child = child_class(parent, index=index, **kwargs)
        if hasattr(parent.child, "on_open"):
            parent.child.on_open()

        return parent.child
