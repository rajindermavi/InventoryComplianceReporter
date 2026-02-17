"""Tkinter GUI frontend for Inventory Compliance Reporter."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any, Mapping, Sequence

from icr.frontend import messages
from icr.frontend.flow import AppFlow, FrontendIO


def _vessel_id(vessel: Mapping[str, Any]) -> str:
    return str(vessel.get("ship_id", ""))


def _vessel_label(vessel: Mapping[str, Any]) -> str:
    ship_id = vessel.get("ship_id", "")
    ship_name = vessel.get("ship_name")
    if ship_name:
        return f"{ship_name} ({ship_id})"
    return str(ship_id)


class GuiIO:
    """FrontendIO implementation that writes to a tkinter Text widget."""

    def __init__(self, text_widget: tk.Text) -> None:
        self._text = text_widget

    def display(self, message: str) -> None:
        self._text.configure(state="normal")
        self._text.insert("end", message + "\n")
        self._text.see("end")
        self._text.configure(state="disabled")

    def prompt(self, message: str) -> str:
        return ""

    def confirm(self, message: str) -> bool:
        return messagebox.askyesno("Confirm", message)


class VesselSelectionDialog(tk.Toplevel):
    """Popup dialog for selecting vessels with checkboxes."""

    def __init__(
        self,
        parent: tk.Widget,
        vessels: Sequence[Mapping[str, Any]],
        previously_selected: set[str],
    ) -> None:
        super().__init__(parent)
        self.title("Select Vessels")
        self.transient(parent)
        self.grab_set()
        self.resizable(True, True)
        self.minsize(350, 300)

        self._vessels = vessels
        self._vars: dict[str, tk.BooleanVar] = {}
        self.selected_ids: set[str] = set(previously_selected)
        self._cancelled = False

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _build_ui(self) -> None:
        btn_frame = ttk.Frame(self, padding=5)
        btn_frame.pack(fill="x")
        ttk.Button(btn_frame, text="Select All", command=self._select_all).pack(
            side="left", padx=2
        )
        ttk.Button(btn_frame, text="Clear All", command=self._clear_all).pack(
            side="left", padx=2
        )
        ttk.Button(btn_frame, text="Done", command=self._on_done).pack(
            side="right", padx=2
        )

        canvas_frame = ttk.Frame(self)
        canvas_frame.pack(fill="both", expand=True, padx=5, pady=5)

        canvas = tk.Canvas(canvas_frame)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        self._inner = ttk.Frame(canvas)

        self._inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=self._inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for vessel in self._vessels:
            vid = _vessel_id(vessel)
            label = _vessel_label(vessel)
            var = tk.BooleanVar(value=vid in self.selected_ids)
            self._vars[vid] = var
            ttk.Checkbutton(self._inner, text=label, variable=var).pack(
                anchor="w", padx=5, pady=1
            )

    def _select_all(self) -> None:
        for var in self._vars.values():
            var.set(True)

    def _clear_all(self) -> None:
        for var in self._vars.values():
            var.set(False)

    def _on_done(self) -> None:
        self.selected_ids = {vid for vid, var in self._vars.items() if var.get()}
        self.grab_release()
        self.destroy()

    def _on_cancel(self) -> None:
        self._cancelled = True
        self.grab_release()
        self.destroy()


class ICRApp:
    """Main GUI application with 4 tabs."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(messages.WELCOME["title"])
        self.root.geometry("800x600")
        self.root.minsize(700, 500)

        self._ic_inventory = tk.StringVar()
        self._vessels_index = tk.StringVar()
        self._vessels_inventory = tk.StringVar()

        self._vessels: list[Mapping[str, Any]] = []
        self._selected_ids: set[str] = set()
        self._summary: Mapping[str, Any] | None = None
        self._processing = False

        self._notebook = ttk.Notebook(self.root)
        self._notebook.pack(fill="both", expand=True, padx=5, pady=5)

        self._build_config_tab()
        self._build_generate_tab()
        self._build_review_tab()
        self._build_export_tab()

        self._flow = AppFlow(
            get_vessel_id=_vessel_id,
            get_vessel_label=_vessel_label,
            io=self._io,
        )

        self._update_button_states()

    # ── Tab 1: Config ──────────────────────────────────────────────

    def _build_config_tab(self) -> None:
        tab = ttk.Frame(self._notebook, padding=15)
        self._notebook.add(tab, text="Config")

        ttk.Label(tab, text="Input File Paths", font=("", 12, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 10)
        )

        labels = ["IC Inventory:", "Vessels Index:", "Vessels Inventory:"]
        variables = [self._ic_inventory, self._vessels_index, self._vessels_inventory]

        for i, (label_text, var) in enumerate(zip(labels, variables), start=1):
            ttk.Label(tab, text=label_text).grid(row=i, column=0, sticky="w", pady=4)
            entry = ttk.Entry(tab, textvariable=var, state="readonly", width=60)
            entry.grid(row=i, column=1, sticky="ew", padx=5, pady=4)
            ttk.Button(
                tab,
                text="Browse",
                command=lambda v=var: self._browse_file(v),
            ).grid(row=i, column=2, pady=4)

        tab.columnconfigure(1, weight=1)

    def _browse_file(self, var: tk.StringVar) -> None:
        path = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
        )
        if path:
            var.set(path)
            self._update_button_states()

    # ── Tab 2: Generate Report ─────────────────────────────────────

    def _build_generate_tab(self) -> None:
        tab = ttk.Frame(self._notebook, padding=15)
        self._notebook.add(tab, text="Generate Report")

        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill="x", pady=(0, 10))

        self._fetch_btn = ttk.Button(
            btn_frame, text="Fetch Vessels", command=self._on_fetch_vessels
        )
        self._fetch_btn.pack(side="left", padx=5)

        self._select_btn = ttk.Button(
            btn_frame, text="Select Vessels", command=self._on_select_vessels
        )
        self._select_btn.pack(side="left", padx=5)

        self._process_btn = ttk.Button(
            btn_frame, text="Process", command=self._on_process
        )
        self._process_btn.pack(side="left", padx=5)

        self._progress = ttk.Progressbar(tab, mode="indeterminate")

        log_frame = ttk.LabelFrame(tab, text="Status", padding=5)
        log_frame.pack(fill="both", expand=True)

        self._log_text = tk.Text(log_frame, state="disabled", wrap="word", height=15)
        log_scroll = ttk.Scrollbar(
            log_frame, orient="vertical", command=self._log_text.yview
        )
        self._log_text.configure(yscrollcommand=log_scroll.set)
        self._log_text.pack(side="left", fill="both", expand=True)
        log_scroll.pack(side="right", fill="y")

        self._io = GuiIO(self._log_text)

    # ── Tab 3: Review Report ───────────────────────────────────────

    def _build_review_tab(self) -> None:
        tab = ttk.Frame(self._notebook, padding=15)
        self._notebook.add(tab, text="Review Report")
        self._review_tab = tab

        self._review_placeholder = ttk.Label(
            tab,
            text="No report available yet. Generate a report first.",
            font=("", 11),
        )
        self._review_placeholder.pack(expand=True)

    def _populate_review_tab(self) -> None:
        for widget in self._review_tab.winfo_children():
            widget.destroy()

        if self._summary is None:
            return

        try:
            from tkinterweb import HtmlFrame
        except ImportError:
            ttk.Label(
                self._review_tab,
                text="tkinterweb is required to view reports.\nInstall with: pip install tkinterweb",
            ).pack(expand=True)
            return

        summary_path = self._summary.get("summary_html_path")
        if summary_path:
            ttk.Label(
                self._review_tab, text="Run Summary", font=("", 11, "bold")
            ).pack(anchor="w", pady=(0, 5))

            summary_frame = ttk.Frame(self._review_tab)
            summary_frame.pack(fill="both", expand=True)

            html_frame = HtmlFrame(summary_frame, messages_enabled=False)
            html_frame.pack(fill="both", expand=True)
            html_frame.load_file(str(summary_path))

        vessels = self._summary.get("vessels", [])
        if vessels:
            ttk.Separator(self._review_tab, orient="horizontal").pack(
                fill="x", pady=10
            )
            ttk.Label(
                self._review_tab, text="Vessel Reports", font=("", 11, "bold")
            ).pack(anchor="w", pady=(0, 5))

            list_frame = ttk.Frame(self._review_tab)
            list_frame.pack(fill="x")

            for v in vessels:
                ship_id = v.get("ship_id", "")
                ship_name = v.get("ship_name")
                label = f"{ship_name} ({ship_id})" if ship_name else ship_id
                report_path = v.get("report_path", "")

                btn = ttk.Button(
                    list_frame,
                    text=label,
                    command=lambda p=report_path, lbl=label: self._open_vessel_report(
                        p, lbl
                    ),
                )
                btn.pack(anchor="w", pady=1)

    def _open_vessel_report(self, report_path: str, title: str) -> None:
        try:
            from tkinterweb import HtmlFrame
        except ImportError:
            messagebox.showerror(
                "Missing Dependency",
                "tkinterweb is required to view reports.",
            )
            return

        popup = tk.Toplevel(self.root)
        popup.title(title)
        popup.geometry("750x550")

        html_frame = HtmlFrame(popup, messages_enabled=False)
        html_frame.pack(fill="both", expand=True)
        html_frame.load_file(report_path)

    # ── Tab 4: Export ──────────────────────────────────────────────

    def _build_export_tab(self) -> None:
        tab = ttk.Frame(self._notebook, padding=15)
        self._notebook.add(tab, text="Export")
        ttk.Label(tab, text="Export functionality coming soon.", font=("", 11)).pack(
            expand=True
        )

    # ── Button state management ────────────────────────────────────

    def _update_button_states(self) -> None:
        config_ready = all([
            self._ic_inventory.get(),
            self._vessels_index.get(),
            self._vessels_inventory.get(),
        ])

        has_vessels = len(self._vessels) > 0
        has_selection = len(self._selected_ids) > 0

        fetch_state = "normal" if config_ready and not self._processing else "disabled"
        select_state = "normal" if has_vessels and not self._processing else "disabled"
        process_state = (
            "normal" if has_selection and not self._processing else "disabled"
        )

        self._fetch_btn.configure(state=fetch_state)
        self._select_btn.configure(state=select_state)
        self._process_btn.configure(state=process_state)

    # ── Actions ────────────────────────────────────────────────────

    def _on_fetch_vessels(self) -> None:
        self._processing = True
        self._update_button_states()
        self._show_progress(True)
        self._io.display("Initializing workflow...")

        def work() -> list[Mapping[str, Any]] | None:
            ok = self._flow.initialize(
                ic_inventory=self._ic_inventory.get(),
                vessels_index=self._vessels_index.get(),
                vessels_inventory=self._vessels_inventory.get(),
            )
            if not ok:
                return None
            return self._flow.fetch_vessels()

        def done(result: Any) -> None:
            self._show_progress(False)
            self._processing = False
            if result is not None:
                self._vessels = result
                self._io.display(f"Found {len(result)} AMS vessel(s).")
            else:
                self._io.display("Failed to fetch vessels. Check status above.")
            self._update_button_states()

        self._run_in_thread(work, done)

    def _on_select_vessels(self) -> None:
        dialog = VesselSelectionDialog(
            self.root, self._vessels, self._selected_ids
        )
        self.root.wait_window(dialog)

        if not dialog._cancelled:
            self._selected_ids = dialog.selected_ids
            count = len(self._selected_ids)
            self._io.display(f"{count} vessel(s) selected.")
        self._update_button_states()

    def _on_process(self) -> None:
        if not self._selected_ids:
            return

        self._processing = True
        self._update_button_states()
        self._show_progress(True)

        ids = list(self._selected_ids)

        def work() -> Mapping[str, Any] | None:
            return self._flow.process(ids)

        def done(result: Any) -> None:
            self._show_progress(False)
            self._processing = False
            if result is not None:
                self._summary = result
                self._io.display("Report generation complete.")
                self._populate_review_tab()
            else:
                self._io.display("Processing failed. Check status above.")
            self._update_button_states()

        self._run_in_thread(work, done)

    # ── Helpers ────────────────────────────────────────────────────

    def _run_in_thread(
        self,
        target: Any,
        callback: Any,
    ) -> None:
        def wrapper() -> None:
            try:
                result = target()
            except Exception as exc:
                self.root.after(0, self._io.display, f"Error: {exc}")
                result = None
            self.root.after(0, callback, result)

        threading.Thread(target=wrapper, daemon=True).start()

    def _show_progress(self, show: bool) -> None:
        if show:
            self._progress.pack(fill="x", pady=(0, 5), before=self._log_text.master)
            self._progress.start(15)
        else:
            self._progress.stop()
            self._progress.pack_forget()


def run_gui() -> None:
    """Launch the GUI application."""
    root = tk.Tk()
    ICRApp(root)
    root.mainloop()
