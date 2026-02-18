"""End-to-end workflow orchestration."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from icr.backend import (
    Database,
    RunMetadata,
    compare_inventory,
    draft_emails,
    get_ams_vessels,
    get_onboard_inventory,
    get_reference_inventory,
    ingest_excel_files,
    render_run_summary,
    render_vessel_report,
)
from icr.backend.config import get_config

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WorkflowRuntimePaths:
    """Runtime paths wrapper that includes db_path for Database compatibility."""

    run_id: str
    run_dir: Path
    db_path: Path


@dataclass(frozen=True)
class WorkflowPaths:
    """Input file paths for the workflow."""
    
    ic_inventory: Path
    vessels_index: Path
    vessels_inventory: Path


class WorkflowState:
    """Maintains state for a single workflow execution."""
    
    def __init__(self, run_id: str , db_path: Path, input_paths: WorkflowPaths| None = None):
        self.input_paths = input_paths
        self.config = get_config()

        # Initialize runtime paths
        from icr.backend import get_run_dir
        run_dir = get_run_dir(run_id)
        self.paths = WorkflowRuntimePaths(
            run_id=run_id,
            run_dir=run_dir,
            db_path=db_path
        )

        # Initialize database
        self.db = Database(self.paths)
        
        # State tracking
        self.ingested = False
        self.ams_vessels: list[Mapping[str, Any]] = []
        self.selected_vessel_ids: list[str] = []
        
    def initialize(self) -> None:
        """Initialize database and ingest files."""
        if self.ingested:
            return
            
        # Create database with schema
        metadata = RunMetadata(
            run_id=self.paths.run_id,
            app_version="0.1.0-dev",
            git_commit="HEAD",
            build_date=datetime.now(timezone.utc).isoformat(),
            input_fingerprint=self._compute_fingerprint(),
        )
        self.db.initialize(metadata)
        
        # Ingest Excel files
        logger.info(f"[{self.paths.run_id}] Starting ingestion...")
        summary = ingest_excel_files(
            ic_inventory_path=self.input_paths.ic_inventory,
            vessels_index_path=self.input_paths.vessels_index,
            vessels_inventory_path=self.input_paths.vessels_inventory,
            db=self.db,
            paths=self.paths,
        )
        
        logger.info(
            f"[{self.paths.run_id}] Ingestion complete: "
            f"{sum(r.rows_inserted for r in summary.results)} rows inserted"
        )
        
        if summary.has_warnings:
            logger.warning(
                f"[{self.paths.run_id}] Ingestion warnings: {len(summary.warnings)}"
            )
        
        self.ingested = True
        
    def discover_ams_vessels(self) -> list[Mapping[str, Any]]:
        """Query and return AMS-marked vessels."""
        self.initialize()
        
        with self.db.connect() as conn:
            rows = get_ams_vessels(conn)
            vessels = [dict(row) for row in rows]
            
        # Apply default office email from config
        default_office = self.config.email.default_office_email
        for vessel in vessels:
            if not vessel.get("office_email"):
                vessel["office_email"] = default_office
                
        self.ams_vessels = vessels
        logger.info(f"[{self.paths.run_id}] Found {len(vessels)} AMS vessels")
        return vessels
        
    def process_vessels(self, vessel_ids: Sequence[str]) -> Mapping[str, Any]:
        """Process selected vessels: compare, report, email."""
        if not self.ingested:
            raise RuntimeError("Must call discover_ams_vessels first")
            
        self.selected_vessel_ids = list(vessel_ids)
        
        # Get reference inventory once
        with self.db.connect() as conn:
            reference_items = list(get_reference_inventory(conn))
            
        vessels_processed = []
        total_issues = 0
        for vessel_id in vessel_ids:
            vessel = self._get_vessel_by_id(vessel_id)
            if not vessel:
                logger.warning(f"Vessel {vessel_id} not found, skipping")
                continue
            vessel_name = vessel.get('ship_name')
            # Compare inventory
            with self.db.connect() as conn:
                onboard_items = list(get_onboard_inventory(conn, vessel_id))
                
            issues = compare_inventory(
                ship_id=vessel_id,
                ship_name=vessel_name,
                onboard_items=onboard_items,
                reference_items=reference_items,
                deduplicate=True,
            )
            
            # Filter out OK issues for reporting (only show problems)
            problem_issues = [
                issue for issue in issues 
                if issue.issue_type.value != "OK"
            ]
            ok_issues = [
                issue for issue in issues 
                if issue.issue_type.value == "OK"
            ]
            
            # Generate HTML report
            html_content = render_vessel_report(
                vessel=vessel,
                problem_issues=problem_issues,
                ok_issues = ok_issues,
                run_timestamp=self._get_timestamp(),
            )
            
            # Write report to file
            report_filename = f"{vessel_id}_report.html"
            report_path = self.paths.run_dir / report_filename
            report_path.write_text(html_content, encoding="utf-8")
            
            vessels_processed.append({
                "ship_id": vessel_id,
                "ship_name": vessel.get("ship_name"),
                "issue_count": len(problem_issues),
                "report_filename": report_filename,
                "report_path": str(report_path),
            })
            
            total_issues += len(problem_issues)
            logger.info(
                f"[{self.paths.run_id}] Processed {vessel_id}: "
                f"{len(problem_issues)} issues"
            )
            
        # Generate run summary HTML
        run_summary_html = render_run_summary(
            vessels=vessels_processed,
            run_timestamp=self._get_timestamp(),
            source_files=self._get_source_filenames(),
        )
        summary_html_path = self.paths.run_dir / "run_summary.html"
        summary_html_path.write_text(run_summary_html, encoding="utf-8")
        
        # Create summary JSON
        summary_data = {
            "run_id": self.paths.run_id,
            "timestamp": self._get_timestamp(),
            "ams_vessels_found": len(self.ams_vessels),
            "vessels_selected": len(vessel_ids),
            "vessels_processed": len(vessels_processed),
            "vessels_with_issues": sum(
                1 for v in vessels_processed if v["issue_count"] > 0
            ),
            "total_issue_rows": total_issues,
            "source_files": self._get_source_filenames(),
            "vessels": vessels_processed,
            "errors": [],
            "summary_html_path": str(summary_html_path)
        }
        
        summary_json_path = self.paths.run_dir / "summary.json"
        summary_json_path.write_text(
            json.dumps(summary_data, indent=2), encoding="utf-8"
        )
        
        # Draft emails
        html_reports = {
            v["ship_id"]: self.paths.run_dir / v["report_filename"]
            for v in vessels_processed
        }
        
        vessel_records = [self._get_vessel_by_id(vid) for vid in vessel_ids]
        vessel_records = [v for v in vessel_records if v is not None]
        
        eml_dir = self.paths.run_dir / "emails"
        drafting_result = draft_emails(
            vessels=vessel_records,
            html_reports=html_reports,
            summary_path=summary_json_path,
            subject_template=self.config.email.subject_template,
            default_office_email=self.config.email.default_office_email,
            include_pdf=self.config.email.include_pdf,
            eml_output_dir=eml_dir,
            from_email=self.config.email.from_email,
            run_id=self.paths.run_id,
        )
        
        logger.info(
            f"[{self.paths.run_id}] Drafted {len(drafting_result.drafts)} emails"
        )
        
        if drafting_result.errors:
            logger.error(
                f"[{self.paths.run_id}] Email drafting errors: "
                f"{len(drafting_result.errors)}"
            )
            
        return summary_data
        
    def _get_vessel_by_id(self, vessel_id: str) -> Mapping[str, Any] | None:
        """Find vessel in cached AMS vessels list."""
        for vessel in self.ams_vessels:
            if vessel.get("ship_id") == vessel_id:
                return vessel
        return None
        
    def _compute_fingerprint(self) -> str:
        """Compute fingerprint of input files."""
        names = [
            self.input_paths.ic_inventory.name,
            self.input_paths.vessels_index.name,
            self.input_paths.vessels_inventory.name,
        ]
        return "|".join(sorted(names))
        
    def _get_timestamp(self) -> str:
        """Get ISO timestamp for reports."""
        return datetime.now(timezone.utc).isoformat(timespec="seconds")
        
    def _get_source_filenames(self) -> list[str]:
        """Get list of source filenames."""
        return [
            self.input_paths.ic_inventory.name,
            self.input_paths.vessels_index.name,
            self.input_paths.vessels_inventory.name,
        ]


# Public API for frontend
_current_workflow: WorkflowState | None = None


def initialize_workflow(
    ic_inventory: Path | str,
    vessels_index: Path | str,
    vessels_inventory: Path | str,
    run_id: str | None = None,
    db_path: Path | None = None,
) -> None:
    """Initialize a new workflow with input files."""
    global _current_workflow

    from icr.backend.persistence.paths import _generate_run_id, get_run_dir

    if run_id is None:
        run_id = _generate_run_id()

    if db_path is None:
        run_dir = get_run_dir(run_id)
        data_dir = run_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        db_path = data_dir / "run.db"

    paths = WorkflowPaths(
        ic_inventory=Path(ic_inventory),
        vessels_index=Path(vessels_index),
        vessels_inventory=Path(vessels_inventory),
    )

    _current_workflow = WorkflowState(run_id, db_path, paths)


def discover_ams_vessels() -> list[Mapping[str, Any]]:
    """Public API: discover AMS vessels."""
    if _current_workflow is None:
        raise RuntimeError("Workflow not initialized")
    return _current_workflow.discover_ams_vessels()


def process_vessels(vessel_ids: Sequence[str]) -> Mapping[str, Any]:
    """Public API: process selected vessels."""
    if _current_workflow is None:
        raise RuntimeError("Workflow not initialized")
    return _current_workflow.process_vessels(vessel_ids)