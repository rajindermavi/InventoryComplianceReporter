# Configuration Specification

## Config File (YAML)

ams_rule:
  source_column: NOTE2
  match_type: contains
  match_value: AMS

email:
  default_office_email: ops@example.com
  subject_template: "Inventory Compliance – {SHIPNAME}"
  include_pdf: false

comparison:
  case_insensitive_item: true
  include_missing_onboard: true

output:
  runs_dir: runs
  write_html: true
  write_pdf: false
