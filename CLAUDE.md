# Business Capability Model Visualizer

## Project Overview
A Python CLI app that reads a business capability model from an Excel file and renders it as a self-contained interactive HTML file (collapsible tree).

## File Structure
```
/home/zig/vis/
├── visualize.py               # Main app — reads Excel, outputs HTML
├── generate_sample.py         # Generates sample_capabilities.xlsx for testing
├── requirements.txt           # pandas, openpyxl
├── capability headings.xlsx   # Column schema reference (header row only)
├── sample_capabilities.xlsx   # Test data (generated)
└── output.html                # Generated visualization (not checked in)
```

## Excel Input Format
Column names must match exactly (leading/trailing spaces are stripped automatically):

| Column | Purpose |
|---|---|
| `capability ID` | Unique node identifier (primary key) |
| `Capability name` | Display label in the tree |
| `tier` | Top-level grouping — drives left-border color |
| `capability description` | Shown below summary when node is expanded |
| `capability level` | Numeric depth: 1 = root, 2 = child, 3 = leaf |
| `capability parent name` | Human-readable parent label (reference only) |
| `capability parent id` | Parent's ID — used to build the tree |
| `capability type` | Classification — shown as a badge on each node |
| `source` | Metadata — shown in expanded detail |

Tree is built by linking `capability parent id` → `capability ID`. Rows with an empty `capability parent id` are treated as root nodes.

## Usage
```bash
# Install dependencies (first time only)
pip install -r requirements.txt

# Generate sample data
python generate_sample.py

# Run visualizer
python visualize.py sample_capabilities.xlsx
python visualize.py your_file.xlsx --output my_output.html
```

## HTML Output Behaviour
- L1 nodes: expanded by default (`<details open>`)
- L2+ nodes: collapsed by default
- Each node shows: capability name + `capability_type` badge
- Expanded view shows: `capability_description` and `source`
- Left-border color is assigned per unique `tier` value, cycling through a fixed palette
- Fully self-contained — no CDN or external JS dependencies

## Environment Notes
- Python 3.12.3, no system pip by default
- pip was bootstrapped via `get-pip.py --break-system-packages`
- pandas and openpyxl installed with `--break-system-packages`
