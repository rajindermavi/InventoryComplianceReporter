#!/usr/bin/env python3
"""Demo script to run the workflow with sample data."""

import logging
import shutil
import sys
from pathlib import Path
import time

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from icr.backend import initialize_workflow, discover_ams_vessels, process_vessels, get_run_dir

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

def main():
    """Run the demo workflow for all samples."""
    samples_dir = project_root / "samples"

    if not samples_dir.exists():
        logger.error(f"Samples directory not found: {samples_dir}")
        return 1

    # Find all sample folders
    sample_folders = [d for d in samples_dir.iterdir() if d.is_dir()]

    if not sample_folders:
        logger.warning(f"No sample folders found in {samples_dir}")
        return 0

    logger.info(f"Found {len(sample_folders)} sample(s) to process")

    # Run each sample
    for sample_folder in sorted(sample_folders):
        sample_name = sample_folder.name
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing sample: {sample_name}")
        logger.info(f"{'='*60}")

        try:
            run_sample(sample_name)
        except Exception as e:
            logger.error(f"Failed to process {sample_name}: {e}", exc_info=True)
            continue

    logger.info(f"\n{'='*60}")
    logger.info("All samples processed!")
    logger.info(f"{'='*60}")
    return 0

def run_sample(sample_name):
    """Run the demo workflow."""
    # Find sample files
    samples_dir = project_root / "samples" 
    samples_dir = samples_dir / sample_name
    
    ic_files = list(samples_dir.glob("SAFE_IC_INVENTORY_*.xlsx",case_sensitive=False))
    index_files = list(samples_dir.glob("SAFE_VESSELS_INDEX_*.xlsx",case_sensitive=False))
    inventory_files = list(samples_dir.glob("SAFE_VESSELS_INVENTORY_*.xlsx",case_sensitive=False))
    
    if not ic_files or not index_files or not inventory_files:
        logger.error(f"Sample files not found in {samples_dir}")
        logger.error(f"  IC files: {len(ic_files)}")
        logger.error(f"  Index files: {len(index_files)}")
        logger.error(f"  Inventory files: {len(inventory_files)}")
        return 1
        
    # Use first (or most recent) of each
    ic_path = sorted(ic_files)[-1]
    index_path = sorted(index_files)[-1]
    inventory_path = sorted(inventory_files)[-1]
    
    logger.info("Using sample files:")
    logger.info(f"  IC: {ic_path.name}")
    logger.info(f"  Index: {index_path.name}")
    logger.info(f"  Inventory: {inventory_path.name}")
    
    # Initialize workflow
    output_dir = samples_dir
    timestamp = str(int(time.time()))
    run_id = sample_name + '_' + timestamp
    db_path = output_dir / 'db.db'

    # Delete existing database if it exists
    if db_path.exists():
        db_path.unlink()

    initialize_workflow(
        run_id= run_id,
        db_path=db_path,
        ic_inventory=ic_path,
        vessels_index=index_path,
        vessels_inventory=inventory_path,
    )
    
    # Discover vessels
    logger.info("\n=== Discovering AMS Vessels ===")
    vessels = discover_ams_vessels()
    
    logger.info(f"\nFound {len(vessels)} AMS vessels:")
    for vessel in vessels:
        logger.info(
            f"  - {vessel['ship_id']}: {vessel.get('ship_name', 'N/A')}"
        )
        
    if not vessels:
        logger.warning("No AMS vessels found!")
        return 0
        
    # Process all vessels
    vessel_ids = [v["ship_id"] for v in vessels]
    
    logger.info(f"\n=== Processing {len(vessel_ids)} Vessels ===")
    summary = process_vessels(vessel_ids)
    
    # Display summary
    logger.info("\n=== Run Summary ===")
    logger.info(f"Run ID: {summary['run_id']}")
    logger.info(f"Vessels processed: {summary['vessels_processed']}")
    logger.info(f"Vessels with issues: {summary['vessels_with_issues']}")
    logger.info(f"Total issues: {summary['total_issue_rows']}")
    
    logger.info("\n=== Output Files ===")
    run_dir = get_run_dir(summary['run_id'])
    logger.info(f"Run directory: {run_dir}")
    logger.info(f"  - summary.json")
    logger.info(f"  - run_summary.html")

    for vessel in summary['vessels']:
        logger.info(
            f"  - {vessel['report_filename']} "
            f"({vessel['issue_count']} issues)"
        )

    eml_dir = run_dir / "emails"
    if eml_dir.exists():
        eml_files = list(eml_dir.glob("*.eml"))
        logger.info(f"\nEmail drafts ({len(eml_files)}):")
        for eml_file in eml_files:
            logger.info(f"  - {eml_file.name}")

    # Copy output files to samples directory
    sample_run_dir = samples_dir / "runs" / summary['run_id']
    if sample_run_dir.exists():
        shutil.rmtree(sample_run_dir)
    shutil.copytree(run_dir, sample_run_dir)

    logger.info(f"\n✓ Demo complete!")
    logger.info(f"  System location: {run_dir}")
    logger.info(f"  Sample location: {sample_run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())