"""Business capability model visualizer.

Usage:
    python visualize.py <input.xlsx> [--output output.html]
"""
import argparse
import sys
import pandas as pd

# BMO-aligned tier colors
TIER_COLORS = [
    "#0079C1", "#002855", "#ED1C24", "#007A5E",
    "#6B2D8B", "#F0A500", "#00A3E0", "#5E8AB4",
]


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    required = {"capability_id", "capability_name", "capability_parent_id"}
    missing = required - set(df.columns)
    if missing:
        print(f"ERROR: Missing required columns: {missing}", file=sys.stderr)
        sys.exit(1)
    df["capability_id"] = df["capability_id"].astype(str).str.strip()
    df["capability_parent_id"] = df["capability_parent_id"].fillna("").astype(str).str.strip()
    for col in ("capability_description", "capability_type", "source", "tier"):
        if col not in df.columns:
            df[col] = ""
        else:
            df[col] = df[col].fillna("")
    return df


def build_tree(df: pd.DataFrame) -> tuple[list, dict]:
    nodes = {}
    for _, row in df.iterrows():
        nodes[row["capability_id"]] = {
            "name": row["capability_name"],
            "desc": str(row["capability_description"]).strip(),
            "type": str(row["capability_type"]).strip(),
            "source": str(row["source"]).strip(),
            "tier": str(row["tier"]).strip(),
            "children": [],
        }
    roots = []
    for _, row in df.iterrows():
        pid = row["capability_parent_id"]
        if pid == "" or pid == "nan":
            roots.append(nodes[row["capability_id"]])
        elif pid in nodes:
            nodes[pid]["children"].append(nodes[row["capability_id"]])
        else:
            print(f"WARNING: parent_id '{pid}' not found for '{row['capability_name']}'", file=sys.stderr)
    return roots, nodes


def assign_tier_colors(roots: list) -> dict:
    tier_map = {}
    color_idx = 0
    for root in roots:
        tier = root["tier"] or root["name"]
        if tier not in tier_map:
            tier_map[tier] = TIER_COLORS[color_idx % len(TIER_COLORS)]
            color_idx += 1
    return tier_map


_node_counter = 0


def render_node(node: dict, tier_color: str = "", is_root: bool = False) -> str:
    global _node_counter
    _node_counter += 1
    node_id = f"node-{_node_counter}"
    open_attr = " open" if is_root else ""
    style = f' style="border-left: 4px solid {tier_color};"' if tier_color else ""
    badge = f'<span class="badge">{node["type"]}</span>' if node["type"] else ""
    children_html = "".join(render_node(c) for c in node["children"])
    extras = ""
    if node["desc"]:
        extras += f'<p class="desc">{node["desc"]}</p>'
    if node["source"]:
        extras += f'<p class="source">Source: {node["source"]}</p>'
    safe_name = node["name"].replace('"', "&quot;")
    return f"""
    <details id="{node_id}"{open_attr} class="node"{style} data-name="{safe_name}">
      <summary><span class="node-label">{node['name']}</span> {badge}</summary>
      {extras}
      {children_html}
    </details>"""


def render_html(roots: list, tier_colors: dict, source_file: str) -> str:
    global _node_counter
    _node_counter = 0
    body = ""
    for root in roots:
        tier = root["tier"] or root["name"]
        color = tier_colors.get(tier, TIER_COLORS[0])
        body += render_node(root, tier_color=color, is_root=True)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Business Capability Model</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #F2F4F7;
      color: #002855;
      margin: 0;
      padding: 24px;
    }}
    header {{
      background: #002855;
      color: #fff;
      padding: 16px 24px 12px;
      margin: -24px -24px 24px;
      display: flex;
      align-items: baseline;
      gap: 16px;
      flex-wrap: wrap;
    }}
    header h1 {{
      font-size: 1.3rem;
      font-weight: 700;
      margin: 0;
      color: #fff;
      letter-spacing: 0.01em;
    }}
    header .subtitle {{
      font-size: 0.82rem;
      color: #90AFCC;
      margin: 0;
    }}
    .search-bar {{
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 20px;
    }}
    #search {{
      flex: 1;
      max-width: 480px;
      padding: 9px 14px 9px 38px;
      border: 2px solid #C5D5E8;
      border-radius: 6px;
      font-size: 0.92rem;
      color: #002855;
      background: #fff url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='none' viewBox='0 0 24 24'%3E%3Ccircle cx='11' cy='11' r='7' stroke='%230079C1' stroke-width='2'/%3E%3Cline x1='16.5' y1='16.5' x2='21' y2='21' stroke='%230079C1' stroke-width='2' stroke-linecap='round'/%3E%3C/svg%3E") no-repeat 10px center;
      outline: none;
      transition: border-color 0.15s;
    }}
    #search:focus {{ border-color: #0079C1; box-shadow: 0 0 0 3px rgba(0,121,193,0.15); }}
    #search-clear {{
      display: none;
      padding: 7px 14px;
      background: #ED1C24;
      color: #fff;
      border: none;
      border-radius: 6px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
    }}
    #search-clear:hover {{ background: #c0151b; }}
    #search-count {{
      font-size: 0.82rem;
      color: #5E7A96;
    }}
    .node {{
      background: #fff;
      border-radius: 6px;
      margin: 6px 0;
      padding: 2px 0;
      box-shadow: 0 1px 3px rgba(0,40,85,0.08);
    }}
    .node > summary {{
      cursor: pointer;
      padding: 10px 14px;
      font-weight: 600;
      font-size: 0.95rem;
      list-style: none;
      display: flex;
      align-items: center;
      gap: 8px;
      user-select: none;
      border-radius: 6px;
    }}
    .node > summary:hover {{ background: #EEF5FB; }}
    .node > summary::before {{
      content: "▶";
      font-size: 0.65rem;
      color: #0079C1;
      transition: transform 0.15s;
      flex-shrink: 0;
    }}
    .node[open] > summary::before {{ transform: rotate(90deg); }}
    .node .node {{
      margin: 4px 0 4px 20px;
      box-shadow: none;
      border: 1px solid #DCE8F2;
    }}
    .node .node > summary {{
      font-weight: 500;
      font-size: 0.9rem;
    }}
    .node .node .node > summary {{
      font-weight: 400;
      color: #3A5570;
    }}
    .badge {{
      font-size: 0.7rem;
      font-weight: 600;
      background: #DDE9F5;
      color: #0079C1;
      padding: 2px 7px;
      border-radius: 10px;
      margin-left: auto;
      white-space: nowrap;
    }}
    .desc {{
      margin: 0 14px 8px 34px;
      font-size: 0.85rem;
      color: #3A5570;
    }}
    .source {{
      margin: 0 14px 8px 34px;
      font-size: 0.78rem;
      color: #7A96B0;
      font-style: italic;
    }}
    .node.search-hidden {{ display: none; }}
    .node.search-match > summary .node-label {{ background: #FFF3CD; border-radius: 3px; padding: 0 2px; }}
    .no-results {{
      color: #7A96B0;
      font-size: 0.9rem;
      padding: 12px 4px;
      display: none;
    }}
  </style>
</head>
<body>
  <header>
    <h1>Business Capability Model</h1>
    <p class="subtitle">Source: {source_file}</p>
  </header>

  <div class="search-bar">
    <input id="search" type="search" placeholder="Search capabilities…" autocomplete="off" />
    <button id="search-clear" onclick="clearSearch()">Clear</button>
    <span id="search-count"></span>
  </div>
  <div class="no-results" id="no-results">No capabilities matched your search.</div>

  <div id="tree">
  {body}
  </div>

  <script>
    const searchInput = document.getElementById('search');
    const clearBtn = document.getElementById('search-clear');
    const countEl = document.getElementById('search-count');
    const noResults = document.getElementById('no-results');

    // Store original open state so we can restore it on clear
    const originalOpen = new Map();
    document.querySelectorAll('details.node').forEach(el => {{
      originalOpen.set(el.id, el.open);
    }});

    function stripHighlight(el) {{
      const label = el.querySelector(':scope > summary > .node-label');
      if (label) label.innerHTML = label.textContent;
    }}

    function highlight(el, query) {{
      const label = el.querySelector(':scope > summary > .node-label');
      if (!label) return;
      const text = label.textContent;
      const re = new RegExp('(' + query.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&') + ')', 'gi');
      label.innerHTML = text.replace(re, '<mark>$1</mark>');
    }}

    function nodeMatches(el, query) {{
      const name = (el.dataset.name || '').toLowerCase();
      return name.includes(query);
    }}

    // Returns true if el or any descendant matches
    function applySearch(el, query) {{
      const selfMatch = nodeMatches(el, query);
      const children = Array.from(el.querySelectorAll(':scope > .node, :scope > p ~ .node, :scope > .node'));
      // get direct child details nodes
      const directChildren = Array.from(el.children).filter(c => c.tagName === 'DETAILS');
      let childMatch = false;
      for (const child of directChildren) {{
        if (applySearch(child, query)) childMatch = true;
      }}
      const visible = selfMatch || childMatch;
      el.classList.toggle('search-hidden', !visible);
      el.classList.toggle('search-match', selfMatch);
      stripHighlight(el);
      if (visible) {{
        el.open = selfMatch || childMatch;
        if (selfMatch) highlight(el, query);
      }}
      return visible;
    }}

    function doSearch() {{
      const query = searchInput.value.trim().toLowerCase();
      const allRoots = Array.from(document.querySelectorAll('#tree > details.node'));

      if (!query) {{
        clearSearch();
        return;
      }}

      clearBtn.style.display = 'inline-block';
      let total = 0;

      for (const root of allRoots) {{
        applySearch(root, query);
      }}

      // Count visible matches
      total = document.querySelectorAll('.node.search-match').length;
      countEl.textContent = total ? `${{total}} result${{total !== 1 ? 's' : ''}}` : '';
      noResults.style.display = total === 0 ? 'block' : 'none';
    }}

    function clearSearch() {{
      searchInput.value = '';
      clearBtn.style.display = 'none';
      countEl.textContent = '';
      noResults.style.display = 'none';
      document.querySelectorAll('details.node').forEach(el => {{
        el.classList.remove('search-hidden', 'search-match');
        stripHighlight(el);
        el.open = originalOpen.get(el.id) || false;
      }});
    }}

    searchInput.addEventListener('input', doSearch);
  </script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Visualize a business capability model from Excel.")
    parser.add_argument("input", help="Path to the Excel file")
    parser.add_argument("--output", default="output.html", help="Output HTML file (default: output.html)")
    args = parser.parse_args()

    df = load_data(args.input)
    roots, _ = build_tree(df)
    tier_colors = assign_tier_colors(roots)
    html = render_html(roots, tier_colors, args.input)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Generated {args.output} with {len(roots)} top-level capabilities.")


if __name__ == "__main__":
    main()
