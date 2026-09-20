#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""
ParentView - Base class for master views in Biovarase.

Provides:
    - Singleton pattern: reuses existing window instead of creating duplicates
    - Anti-flash: hides window during construction, shows after centering

Usage:
    class UI(ParentView):
        def __init__(self, parent):
            super().__init__(parent, name="myview")
            if self._reusing:
                return  # reusing existing window

            # ... setup and _build_ui() ...
            self.show()  # centers and shows the window

Author: 1966bc (Giuseppe Costanzi)
License: GNU GPL v3
Version: 4.2 (Professional Edition)
"""
import tkinter as tk


class ParentView(tk.Toplevel):
    """
    Base class for main views with singleton and anti-flash behavior.

    Use this for list/management windows opened from the main menu
    (products, suppliers, warehouse, etc.).

    Subclasses should:
        1. Call super().__init__(parent, name="unique_name")
        2. Check `if self._reusing: return` to handle reuse
        3. Call self.show() after _build_ui() (auto-centers)
        4. Call super().on_cancel() in their on_cancel() method

    Attributes:
        _instance: Class-level singleton cache
        _is_init: Instance flag to prevent re-initialization
        _reusing: True if this call is reusing an existing window
        parent: Parent widget
        engine: Application engine reference
    """

    _instance = None

    def __new__(cls, parent, *args, **kwargs):
        """
        Singleton allocation.

        If an instance already exists and is still alive,
        brings it to front and returns it instead of creating a new one.

        Args:
            parent: Parent widget
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Existing instance or new instance
        """
        if cls._instance is not None:
            try:
                if cls._instance.winfo_exists():
                    cls._instance.lift()
                    cls._instance.focus_set()
                    return cls._instance
            except Exception:
                pass
        obj = super().__new__(cls)
        cls._instance = obj
        return obj

    def __init__(self, parent, name=None):
        """
        Initialize the parent view.

        Guarded to prevent re-initialization when reusing singleton.
        Window is hidden during construction (anti-flash).

        Args:
            parent: Parent widget
            name: Unique Tk widget name for this view
        """
        # Flag for subclasses: True if reusing existing window
        self._reusing = getattr(self, "_is_init", False)

        if self._reusing:
            self.parent = parent
            return

        super().__init__(name=name)
        self._is_init = True

        # Anti-flash: hide completely during construction
        self.withdraw()

        self.parent = parent
        self.engine = self.nametowidget(".").engine

        # Escape closes the window
        self.bind("<Escape>", self.on_cancel)

        # Window close button calls on_cancel
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

    def show(self, on_screen=False):
        """
        Center and show the window after UI construction.

        Call this at the end of subclass __init__ after _build_ui().
        Automatically centers the window before showing.

        Args:
            on_screen: If True, center on screen. If False (default), center on parent.
        """
        self.engine.tools.center_me(self, on_screen=on_screen)
        self.deiconify()
        self.lift()
        self.focus_set()

    def on_cancel(self, evt=None):
        """
        Close window and clean up singleton reference.

        Subclasses should call super().on_cancel() at the end
        of their on_cancel() method.

        Args:
            evt: Optional event object
        """
        type(self)._instance = None
        self._is_init = False
        self.destroy()
