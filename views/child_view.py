#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChildView - Base class for editor dialogs in Biovarase.

Provides:
    - Automatic registration in engine.dict_instances
    - Anti-flash: hides window during construction, shows after centering
    - Transient binding to parent window

Usage:
    class UI(ChildView):
        def __init__(self, parent, index=None):
            super().__init__(parent, name="myentity")

            # ... setup and init_ui() ...
            self.show()  # centers and shows the window

    # In the caller (ParentView):
    def on_add(self):
        self.engine.close_instance("myentity")  # close existing if any
        self.obj = myentity.UI(self)
        self.obj.on_open()

Author: 1966bc (Giuseppe Costanzi)
License: GNU GPL v3
Version: 4.2 (Professional Edition)
"""
import tkinter as tk


class ChildView(tk.Toplevel):
    """
    Base class for CRUD dialogs with auto-registration and anti-flash.

    Use this for edit/create dialogs opened from parent views
    (product, supplier, batch, etc.).

    Subclasses should:
        1. Call super().__init__(parent, name="unique_name")
        2. Call self.show() after init_ui() (auto-centers)
        3. Call super().on_cancel() in their on_cancel() method

    The caller should check engine.get_instance(name) before creating
    to avoid duplicate windows.

    Attributes:
        _dialog_name: Name used for dict_instances registration
        parent: Parent widget
        engine: Application engine reference
    """

    def __init__(self, parent, name=None):
        """
        Initialize the child view.

        Window is hidden during construction (anti-flash).
        Automatically registers in engine.dict_instances.

        Args:
            parent: Parent widget
            name: Unique Tk widget name for this dialog
        """
        super().__init__(name=name)

        # Anti-flash: withdraw immediately, then set transparent
        self.withdraw()

        self.parent = parent
        self.engine = self.nametowidget(".").engine
        self._dialog_name = name

        # Bind to parent window
        self.transient(parent)

        # Fixed size by default (subclasses can override with resizable(1,1))
        self.resizable(0, 0)

        # Escape closes the dialog
        self.bind("<Escape>", self.on_cancel)

        # Window close button calls on_cancel
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

        # Register in dict_instances
        if name:
            self.engine.dict_instances[name] = self

    def show(self, on_screen=False):
        """
        Center and show the window after UI construction.

        Call this at the end of subclass __init__ after init_ui().
        Automatically centers the window before showing.

        Args:
            on_screen: If True, center on screen. If False (default), center on parent.
        """
        self.engine.center_window(self, on_screen=on_screen)
        self.deiconify()

    def on_cancel(self, evt=None):
        """
        Close window and unregister from dict_instances.

        Subclasses should call super().on_cancel() at the end
        of their on_cancel() method.

        Args:
            evt: Optional event object
        """
        if self._dialog_name:
            self.engine.dict_instances.pop(self._dialog_name, None)
        self.destroy()
