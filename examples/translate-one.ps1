# Run from the project root after installation.
$ErrorActionPreference = "Stop"
uv run cbpdf --config config/config.yaml one cache/incoming/example.pdf
