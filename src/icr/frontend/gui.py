"""Tkinter GUI frontend for Inventory Compliance Reporter."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any, Mapping, Sequence

from icr.frontend import messages
from icr.frontend.flow import AppFlow, FrontendIO

from icr.utils.logging import get_logger
logger = get_logger('gui')

def _vessel_id(vessel: Mapping[str, Any]) -> str:
    return str(vessel.get("ship_id", ""))

def _vessel_customer_no(vessel: Mapping[str, Any]) -> str:
    return str(vessel.get("customer_no", ""))

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

        normalized_vessels = {}
        for vessel in self._vessels:
            vid = _vessel_id(vessel)
            label = _vessel_label(vessel)
            customer_no = _vessel_customer_no(vessel)  # Access customer_no to ensure it's loaded
            normalized_vessels[vid] = {
                "id": vid,
                "label": label, 
                "customer_no": customer_no
            }

        normalized_vessels = sorted(
            normalized_vessels.items(), 
            key=lambda item: (item[1]['customer_no'], item[1]['label'])
        )

        for vid, vessel_data in normalized_vessels:
            label = vessel_data['label']
            customer_no = vessel_data['customer_no']

            var = tk.BooleanVar(value=vid in self.selected_ids)
            self._vars[vid] = var
            ttk.Checkbutton(self._inner, text=f"{customer_no} - {label}", variable=var).pack(
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
        logger.debug('Initialize gui')
        self.root = root
        self.root.title(messages.WELCOME["title"])
        self.root.geometry("800x600")
        self.root.minsize(700, 500)

        self._ic_inventory = tk.StringVar()
        self._vessels_index = tk.StringVar()
        self._vessels_inventory = tk.StringVar()
        self._export_folder = tk.StringVar()

        self._vessels: list[Mapping[str, Any]] = []
        self._selected_ids: set[str] = set()
        self._summary: Mapping[str, Any] | None = None
        self._processing = False
        self._runs_cache: list[Mapping[str, Any]] = []

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
            filetypes=[("Excel files", "*.xlsx *.xls *.XLSX *.XLS"), ("All files", "*.*")],
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

        # Button bar at top
        self._review_btn_frame = ttk.Frame(tab)
        self._review_btn_frame.pack(fill="x", pady=(0, 5))

        self._main_report_btn = ttk.Button(
            self._review_btn_frame,
            text="Main Report",
            command=self._show_main_report,
            state="disabled",
        )
        self._main_report_btn.pack(side="left")

        self._review_placeholder = ttk.Label(
            tab,
            text="No report available yet. Generate a report first.",
            font=("", 11),
        )
        self._review_placeholder.pack(expand=True)

        self._review_html = None
        self._summary_html_path = None

    def _populate_review_tab(self) -> None:
        # Destroy content below the button bar
        for widget in self._review_tab.winfo_children():
            if widget is not self._review_btn_frame:
                widget.destroy()

        # Clear old vessel buttons from btn frame (keep Main Report button)
        for widget in self._review_btn_frame.winfo_children():
            if widget is not self._main_report_btn:
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

        # Enable Main Report button
        self._main_report_btn.configure(state="normal")

        # Add vessel buttons to the button bar
        vessels = self._summary.get("vessels", [])
        if vessels:
            ttk.Separator(self._review_btn_frame, orient="vertical").pack(
                side="left", fill="y", padx=5, pady=2
            )
            for v in vessels:
                ship_id = v.get("ship_id", "")
                ship_name = v.get("ship_name")
                label = f"{ship_name} ({ship_id})" if ship_name else ship_id
                report_path = v.get("report_path", "")
                btn = ttk.Button(
                    self._review_btn_frame,
                    text=label,
                    command=lambda p=report_path: self._show_vessel_report(p),
                )
                btn.pack(side="left", padx=2)

        # Main HTML frame for report content
        self._review_html = HtmlFrame(self._review_tab, messages_enabled=False)
        self._review_html.pack(fill="both", expand=True)

        # Show summary by default
        self._summary_html_path = self._summary.get("summary_html_path")
        if self._summary_html_path:
            self._review_html.load_file(str(self._summary_html_path))

    def _show_main_report(self) -> None:
        if self._review_html and self._summary_html_path:
            self._review_html.load_file(str(self._summary_html_path))

    def _show_vessel_report(self, report_path: str) -> None:
        if self._review_html and report_path:
            self._review_html.load_file(report_path)

    # ── Tab 4: Export ──────────────────────────────────────────────

    def _build_export_tab(self) -> None:
        tab = ttk.Frame(self._notebook, padding=15)
        self._notebook.add(tab, text="Export")
        self._export_tab = tab

        # Export folder row
        folder_frame = ttk.Frame(tab)
        folder_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(folder_frame, text="Export Folder:").pack(side="left")
        entry = ttk.Entry(
            folder_frame, textvariable=self._export_folder, state="readonly", width=50
        )
        entry.pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(
            folder_frame, text="Browse", command=self._browse_export_folder
        ).pack(side="left")

        # Action buttons
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill="x", pady=(0, 10))

        self._export_selected_btn = ttk.Button(
            btn_frame, text="Export Selected", command=self._on_export_selected
        )
        self._export_selected_btn.pack(side="left", padx=5)

        self._export_current_btn = ttk.Button(
            btn_frame, text="Export Current", command=self._on_export_current
        )
        self._export_current_btn.pack(side="left", padx=5)

        self._purge_selected_btn = ttk.Button(
            btn_frame, text="Purge Selected", command=self._on_purge_selected
        )
        self._purge_selected_btn.pack(side="left", padx=5)

        self._purge_all_btn = ttk.Button(
            btn_frame, text="Purge All", command=self._on_purge_all
        )
        self._purge_all_btn.pack(side="left", padx=5)

        # Past runs treeview
        runs_frame = ttk.LabelFrame(tab, text="Past Runs", padding=5)
        runs_frame.pack(fill="both", expand=True)

        columns = ("run_id", "timestamp", "vessels", "issues")
        self._runs_tree = ttk.Treeview(
            runs_frame, columns=columns, show="headings", selectmode="browse"
        )
        self._runs_tree.heading("run_id", text="Run ID")
        self._runs_tree.heading("timestamp", text="Timestamp")
        self._runs_tree.heading("vessels", text="AMS Vessels")
        self._runs_tree.heading("issues", text="Issues")

        self._runs_tree.column("run_id", width=220)
        self._runs_tree.column("timestamp", width=180)
        self._runs_tree.column("vessels", width=70, anchor="center")
        self._runs_tree.column("issues", width=70, anchor="center")

        tree_scroll = ttk.Scrollbar(
            runs_frame, orient="vertical", command=self._runs_tree.yview
        )
        self._runs_tree.configure(yscrollcommand=tree_scroll.set)
        self._runs_tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        self._runs_tree.bind("<<TreeviewSelect>>", lambda _: self._update_export_button_states())

        # Auto-refresh when switching to the Export tab
        self._notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    # ── Export helpers ─────────────────────────────────────────────

    def _browse_export_folder(self) -> None:
        path = filedialog.askdirectory(title="Select Export Folder")
        if path:
            self._export_folder.set(path)
            self._update_export_button_states()

    def _on_tab_changed(self, event: Any) -> None:
        selected = self._notebook.index(self._notebook.select())
        if selected == 3:  # Export tab
            self._refresh_runs_list()

    def _refresh_runs_list(self) -> None:
        for item in self._runs_tree.get_children():
            self._runs_tree.delete(item)

        try:
            self._runs_cache = self._flow.list_runs()
        except Exception:
            self._runs_cache = []

        for run in self._runs_cache:
            self._runs_tree.insert("", "end", values=(
                run.get("run_id", ""),
                run.get("timestamp", ""),
                #run.get("vessels_processed", ""),
                run.get("ams_vessels_found", ""),
                run.get("total_issue_rows", ""),
            ))
        self._update_export_button_states()

    def _get_selected_run_id(self) -> str | None:
        selection = self._runs_tree.selection()
        if not selection:
            return None
        values = self._runs_tree.item(selection[0], "values")
        return values[0] if values else None

    def _on_export_selected(self) -> None:
        folder = self._export_folder.get()
        run_id = self._get_selected_run_id()
        if not folder or not run_id:
            return

        def work() -> bool:
            self._flow.export_run(run_id, folder)
            return True

        def done(result: Any) -> None:
            if result:
                self._io.display(messages.EXPORT["export_success"])

        self._run_in_thread(work, done)

    def _on_export_current(self) -> None:
        folder = self._export_folder.get()
        if not folder:
            return

        def work() -> bool:
            self._flow.export_current_run(folder)
            return True

        def done(result: Any) -> None:
            if result:
                self._io.display(messages.EXPORT["export_success"])

        self._run_in_thread(work, done)

    def _on_purge_selected(self) -> None:
        run_id = self._get_selected_run_id()
        if not run_id:
            return
        if not messagebox.askyesno("Confirm", messages.EXPORT["confirm_purge_selected"]):
            return

        def work() -> bool:
            self._flow.purge_run(run_id)
            return True

        def done(result: Any) -> None:
            if result:
                self._io.display(messages.EXPORT["purge_success"])
            self.root.after(0, self._refresh_runs_list)

        self._run_in_thread(work, done)

    def _on_purge_all(self) -> None:
        if not messagebox.askyesno("Confirm", messages.EXPORT["confirm_purge_all"]):
            return

        def work() -> bool:
            self._flow.purge_all_runs()
            return True

        def done(result: Any) -> None:
            if result:
                self._io.display(messages.EXPORT["purge_all_success"])
            self.root.after(0, self._refresh_runs_list)

        self._run_in_thread(work, done)

    def _update_export_button_states(self) -> None:
        has_folder = bool(self._export_folder.get())
        has_selection = self._get_selected_run_id() is not None
        has_current = self._summary is not None
        has_runs = len(self._runs_tree.get_children()) > 0

        self._export_selected_btn.configure(
            state="normal" if has_folder and has_selection else "disabled"
        )
        self._export_current_btn.configure(
            state="normal" if has_folder and has_current else "disabled"
        )
        self._purge_selected_btn.configure(
            state="normal" if has_selection else "disabled"
        )
        self._purge_all_btn.configure(
            state="normal" if has_runs else "disabled"
        )

    # ── Button state management ────────────────────────────────────

    def _update_button_states(self) -> None:
        self.log_state()
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

        main_report_state = "normal" if self._summary is not None else "disabled"

        self._fetch_btn.configure(state=fetch_state)
        self._select_btn.configure(state=select_state)
        self._process_btn.configure(state=process_state)
        self._main_report_btn.configure(state=main_report_state)
        self._update_export_button_states()

    # ── Actions ────────────────────────────────────────────────────

    def _on_fetch_vessels(self) -> None:
        self._processing = True
        self._update_button_states()
        self._show_progress(True)
        self._io.display("Initializing workflow...")

        # Read StringVar values on the main thread (not thread-safe).
        ic_inv = self._ic_inventory.get()
        vi = self._vessels_index.get()
        vinv = self._vessels_inventory.get()

        def work() -> list[Mapping[str, Any]] | None:
            ok = self._flow.initialize(
                ic_inventory=ic_inv,
                vessels_index=vi,
                vessels_inventory=vinv,
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
    
    def log_state(self):
        logger.debug("="*10 + " LOG STATE " + "="*10)
        logger.debug(f"ic_inventory: {self._ic_inventory.get()}")
        logger.debug(f"vessel_index: {self._vessels_index.get()}")
        logger.debug(f"vessels_inventory: {self._vessels_inventory.get()}")



def run_gui() -> None:
    """Launch the GUI application."""
    root = tk.Tk()
    ICRApp(root)
    root.mainloop()
