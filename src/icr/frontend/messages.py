"""User-facing message catalog for the frontend."""

WELCOME = {
    "title": "Inventory Compliance Reporter",
    "body": "Welcome to the Inventory Compliance Reporter.",
}

PROMPTS = {
    "input_ready": "Confirm that the required input files are ready.",
    "confirm_selection": "Proceed with {count} selected vessels? (y/n)",
    "confirm_retry": "Please enter y or n.",
}

SELECTION = {
    "title": "Vessel Selection",
    "instructions": "Select vessels to include in this run.",
    "list_header": "Available vessels:",
    "list_item": "{identifier}: {label}",
    "selected_count": "Selected {selected_count} of {total_count} vessels.",
    "options_header": "Options:",
    "option_all": "A - Select all vessels",
    "option_none": "N - Select no vessels",
    "option_toggle": "T - Toggle a vessel by identifier",
    "option_done": "D - Finish selection",
    "prompt_action": "Choose an option (A/N/T/D): ",
    "prompt_toggle": "Enter a vessel identifier to toggle: ",
    "invalid_action": "Please choose A, N, T, or D.",
    "invalid_toggle": "No vessel matches identifier: {vessel_id}",
    "no_vessels": "No AMS vessels were found.",
}

PROGRESS = {
    "validating_inputs": "Checking input files...",
    "discovering_vessels": "Discovering AMS vessels...",
    "processing": "Processing selected vessels...",
}

STATUS = {
    "selection_cancelled": "Selection cancelled. No processing was started.",
    "selection_empty": "No vessels selected. Run cancelled.",
}

COMPLETION = {
    "success": "Processing complete.",
    "run_id": "Run ID: {run_id}",
    "vessels_processed": "Vessels processed: {vessels_processed}",
    "vessels_with_issues": "Vessels with issues: {vessels_with_issues}",
    "total_issue_rows": "Total issue rows: {total_issue_rows}",
}

ERRORS = {
    "backend_unavailable": {
        "title": "Backend is unavailable.",
        "body": "The application cannot start because backend services are not available.",
        "next_step": "Please ensure the backend is installed and try again.",
    },
    "input_validation": {
        "title": "Inputs are not ready.",
        "body": "The application could not validate the input files.",
        "next_step": "Please confirm the files are present and try again.",
    },
    "discover_vessels": {
        "title": "Unable to discover vessels.",
        "body": "The application could not identify AMS vessels for this run.",
        "next_step": "Please check the input files and try again.",
    },
    "processing": {
        "title": "Processing failed.",
        "body": "The application could not complete processing for the selected vessels.",
        "next_step": "Please review your inputs and try again.",
    },
    "unexpected": {
        "title": "Unexpected error.",
        "body": "Something went wrong while running the application.",
        "next_step": "Please try again or contact support.",
    },
}
