"""Backend package.

Exports the public backend interfaces across ingest, domain, reporting,
emailer, persistence, and delivery subsystems so callers can import from
`icr.backend`.
"""

from __future__ import annotations

from .delivery import (
    EmailDeliveryPlan,
    EmailDeliveryResult,
    PdfResult,
    deliver_emails,
    generate_pdfs,
)
from .domain import (
    IssueRow,
    IssueType,
    compare_inventory,
    get_ams_vessels,
    get_onboard_inventory,
    get_reference_inventory,
)
from .emailer import (
    DEFAULT_SUBJECT_TEMPLATE,
    EMAIL_PHASE,
    DraftAttachment,
    DraftEmail,
    DraftIssue,
    DraftingResult,
    draft_emails,
)
from .ingest import (
    DatabaseLike,
    IngestionFatalError,
    IngestionStats,
    IngestionSummary,
    RuntimePathsLike,
    SheetSpec,
    ValidationIssue,
    ingest_excel_files,
)
from .persistence import (
    Database,
    RunMetadata,
    RuntimePaths,
    get_app_data_dir,
    get_run_dir,
    get_runs_base_dir,
)
from .reporting import (
    render_run_summary, 
    render_vessel_report,
)
from .orchestrator import (
    discover_ams_vessels,
    export_current_run,
    export_run,
    initialize_workflow,
    list_runs,
    process_vessels,
    purge_all_runs,
    purge_run,
)

__all__ = [
    "DEFAULT_SUBJECT_TEMPLATE",
    "Database",
    "DatabaseLike",
    "DraftAttachment",
    "DraftEmail",
    "DraftIssue",
    "DraftingResult",
    "EMAIL_PHASE",
    "EmailDeliveryPlan",
    "EmailDeliveryResult",
    "IngestionFatalError",
    "IngestionStats",
    "IngestionSummary",
    "IssueRow",
    "IssueType",
    "PdfResult",
    "RunMetadata",
    "RuntimePaths",
    "RuntimePathsLike",
    "SheetSpec",
    "ValidationIssue",
    "compare_inventory",
    "deliver_emails",
    "discover_ams_vessels",
    "draft_emails",
    "export_current_run",
    "export_run",
    "generate_pdfs",
    "get_ams_vessels",
    "get_app_data_dir",
    "get_onboard_inventory",
    "get_reference_inventory",
    "get_run_dir",
    "get_runs_base_dir",
    "ingest_excel_files",
    "initialize_workflow",
    "list_runs",
    "process_vessels",
    "purge_all_runs",
    "purge_run",
    "render_run_summary",
    "render_vessel_report",
]
