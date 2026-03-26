"""Business capability model visualizer.

Usage:
    python visualize.py <input.xlsx> [--output output.html]
"""
import argparse
import html
import json
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


def tree_to_json(roots: list, tier_colors: dict) -> list:
    """Convert Python tree + tier colors into a JSON-serializable structure."""
    counter = [0]

    def convert(node, color=""):
        counter[0] += 1
        return {
            "id": f"node-{counter[0]}",
            "name": node["name"],
            "desc": node["desc"],
            "type": node["type"],
            "source": node["source"],
            "tier": node["tier"],
            "color": color,
            "children": [convert(c) for c in node["children"]],
        }

    result = []
    for root in roots:
        tier = root["tier"] or root["name"]
        color = tier_colors.get(tier, TIER_COLORS[0])
        result.append(convert(root, color))
    return result


def render_html(roots: list, tier_colors: dict, source_file: str) -> str:
    tree_data = tree_to_json(roots, tier_colors)
    json_blob = json.dumps(tree_data, ensure_ascii=False)
    safe_source = html.escape(source_file)

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
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
    }}
    header {{
      background: #002855;
      color: #fff;
      padding: 14px 24px;
      display: flex;
      align-items: center;
      gap: 16px;
      flex-wrap: wrap;
      flex-shrink: 0;
      z-index: 10;
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
    .toolbar {{
      display: flex;
      align-items: center;
      gap: 10px;
      margin-left: auto;
    }}
    #search {{
      width: 280px;
      padding: 7px 12px 7px 34px;
      border: 2px solid rgba(255,255,255,0.2);
      border-radius: 6px;
      font-size: 0.88rem;
      color: #fff;
      background: rgba(255,255,255,0.1) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='none' viewBox='0 0 24 24'%3E%3Ccircle cx='11' cy='11' r='7' stroke='%2390AFCC' stroke-width='2'/%3E%3Cline x1='16.5' y1='16.5' x2='21' y2='21' stroke='%2390AFCC' stroke-width='2' stroke-linecap='round'/%3E%3C/svg%3E") no-repeat 10px center;
      outline: none;
      transition: border-color 0.15s;
    }}
    #search::placeholder {{ color: #90AFCC; }}
    #search:focus {{ border-color: #0079C1; background-color: rgba(255,255,255,0.15); }}
    .toolbar button {{
      padding: 6px 14px;
      border: 1px solid rgba(255,255,255,0.25);
      border-radius: 6px;
      font-size: 0.82rem;
      font-weight: 600;
      cursor: pointer;
      color: #fff;
      background: rgba(255,255,255,0.08);
      transition: background 0.15s;
    }}
    .toolbar button:hover {{ background: rgba(255,255,255,0.18); }}
    #search-clear {{
      display: none;
      background: #ED1C24;
      border-color: #ED1C24;
    }}
    #search-clear:hover {{ background: #c0151b; }}
    #search-count {{
      font-size: 0.8rem;
      color: #90AFCC;
    }}
    #canvas-container {{
      flex: 1;
      overflow: hidden;
      position: relative;
      cursor: grab;
    }}
    #canvas-container.panning {{
      cursor: grabbing;
    }}
    #tree-svg {{
      width: 100%;
      height: 100%;
      display: block;
    }}
    .link-path {{
      fill: none;
      stroke: #B0C4D8;
      stroke-width: 1.5;
      transition: opacity 0.3s ease;
    }}
    .node-group {{
      cursor: pointer;
      transition: transform 0.4s ease, opacity 0.3s ease;
    }}
    .node-rect {{
      stroke-width: 1.5;
      transition: stroke 0.15s, fill 0.15s;
    }}
    .node-group:hover .node-rect {{
      stroke: #0079C1;
    }}
    .node-group.search-match .node-rect {{
      stroke: #F0A500;
      stroke-width: 2.5;
    }}
    .node-group.search-dim {{
      opacity: 0.25;
    }}
    .node-group.search-dim .link-path {{
      opacity: 0.15;
    }}
    .toggle-circle {{
      cursor: pointer;
      fill: #fff;
      stroke: #0079C1;
      stroke-width: 1.5;
    }}
    .toggle-circle:hover {{
      fill: #EEF5FB;
    }}
    .toggle-text {{
      fill: #0079C1;
      font-size: 14px;
      font-weight: 700;
      text-anchor: middle;
      dominant-baseline: central;
      pointer-events: none;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}

    /* Detail popup */
    #detail-popup {{
      position: fixed;
      z-index: 100;
      max-width: 380px;
      min-width: 280px;
      background: #fff;
      border-radius: 10px;
      padding: 20px 24px;
      box-shadow: 0 8px 32px rgba(0,40,85,0.18), 0 2px 8px rgba(0,40,85,0.08);
      display: none;
      max-height: 80vh;
      overflow-y: auto;
    }}
    #detail-popup.visible {{
      display: block;
    }}
    #detail-popup h2 {{
      margin: 0 0 4px;
      font-size: 1.15rem;
      color: #002855;
      padding-right: 28px;
    }}
    .popup-close {{
      position: absolute;
      top: 12px;
      right: 14px;
      width: 24px;
      height: 24px;
      border: none;
      background: #F2F4F7;
      border-radius: 50%;
      font-size: 14px;
      line-height: 24px;
      text-align: center;
      cursor: pointer;
      color: #5E7A96;
      padding: 0;
    }}
    .popup-close:hover {{
      background: #DCE8F2;
    }}
    .detail-badge {{
      display: inline-block;
      font-size: 0.72rem;
      font-weight: 600;
      background: #DDE9F5;
      color: #0079C1;
      padding: 2px 9px;
      border-radius: 10px;
      margin-bottom: 12px;
    }}
    .detail-tier {{
      display: inline-block;
      font-size: 0.72rem;
      font-weight: 600;
      padding: 2px 9px;
      border-radius: 10px;
      margin-left: 5px;
      margin-bottom: 12px;
      color: #fff;
    }}
    .detail-section {{
      margin-top: 12px;
    }}
    .detail-section h3 {{
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #7A96B0;
      margin: 0 0 4px;
    }}
    .detail-section p {{
      margin: 0;
      font-size: 0.88rem;
      color: #3A5570;
      line-height: 1.5;
    }}
    .children-list {{
      list-style: none;
      padding: 0;
      margin: 0;
    }}
    .children-list li {{
      padding: 3px 0;
    }}
    .children-list a {{
      color: #0079C1;
      text-decoration: none;
      font-size: 0.85rem;
      cursor: pointer;
    }}
    .children-list a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <header>
    <h1>Business Capability Model</h1>
    <p class="subtitle">Source: {safe_source}</p>
    <div class="toolbar">
      <input id="search" type="search" placeholder="Search capabilities\u2026" autocomplete="off" />
      <button id="search-clear">Clear</button>
      <span id="search-count"></span>
      <button id="btn-expand-all">Expand All</button>
      <button id="btn-collapse-all">Collapse All</button>
      <button id="btn-reset-view">Reset View</button>
    </div>
  </header>

  <div id="canvas-container">
    <svg id="tree-svg">
      <g id="viewport">
        <g id="links-layer"></g>
        <g id="nodes-layer"></g>
      </g>
    </svg>
  </div>

  <div id="detail-popup">
    <button class="popup-close" id="popup-close">&times;</button>
    <div id="popup-content"></div>
  </div>

  <script>
    var DATA = {json_blob};

    /* ---- Constants ---- */
    var LEVEL_WIDTH = 280;
    var NODE_W = 200;
    var NODE_H = 36;
    var NODE_SPACING = 52;
    var TOGGLE_R = 9;
    var PAD_TOP = 40;
    var PAD_LEFT = 40;

    /* ---- Flat index & parent map ---- */
    var nodeMap = {{}};
    var parentMap = {{}};
    function indexNodes(nodes, pid) {{
      for (var i = 0; i < nodes.length; i++) {{
        var n = nodes[i];
        nodeMap[n.id] = n;
        if (pid) parentMap[n.id] = pid;
        n._collapsed = true;
        n._x = 0;
        n._y = 0;
        n._visible = true;
        indexNodes(n.children, n.id);
      }}
    }}
    indexNodes(DATA, null);

    /* L1 roots expanded by default */
    for (var i = 0; i < DATA.length; i++) {{
      DATA[i]._collapsed = false;
    }}

    /* Tier color lookup */
    function getTierColor(node) {{
      if (node.color) return node.color;
      var id = node.id;
      while (parentMap[id]) {{
        id = parentMap[id];
      }}
      return nodeMap[id] ? nodeMap[id].color : "";
    }}

    /* ---- SVG references ---- */
    var svgEl = document.getElementById("tree-svg");
    var viewport = document.getElementById("viewport");
    var linksLayer = document.getElementById("links-layer");
    var nodesLayer = document.getElementById("nodes-layer");
    var container = document.getElementById("canvas-container");
    var popup = document.getElementById("detail-popup");
    var popupContent = document.getElementById("popup-content");
    var popupClose = document.getElementById("popup-close");
    var searchInput = document.getElementById("search");
    var searchClear = document.getElementById("search-clear");
    var searchCount = document.getElementById("search-count");

    /* ---- Pan / Zoom state ---- */
    var panX = PAD_LEFT;
    var panY = PAD_TOP;
    var zoom = 1;
    var isPanning = false;
    var panStartX = 0;
    var panStartY = 0;
    var panStartPanX = 0;
    var panStartPanY = 0;

    function applyTransform() {{
      viewport.setAttribute("transform",
        "translate(" + panX + "," + panY + ") scale(" + zoom + ")");
    }}
    applyTransform();

    /* ---- Layout algorithm ---- */
    var leafY = 0;

    function layoutNode(node, depth) {{
      node._x = depth * LEVEL_WIDTH;
      node._visible = true;

      if (node.children.length === 0 || node._collapsed) {{
        node._y = leafY;
        leafY += NODE_SPACING;
        /* Hide collapsed children */
        if (node._collapsed) {{
          hideSubtree(node);
        }}
        return;
      }}

      for (var i = 0; i < node.children.length; i++) {{
        layoutNode(node.children[i], depth + 1);
      }}

      /* Parent centers over children */
      var firstY = node.children[0]._y;
      var lastY = node.children[node.children.length - 1]._y;
      node._y = (firstY + lastY) / 2;
    }}

    function hideSubtree(node) {{
      for (var i = 0; i < node.children.length; i++) {{
        node.children[i]._visible = false;
        hideSubtree(node.children[i]);
      }}
    }}

    function doLayout() {{
      leafY = 0;
      for (var i = 0; i < DATA.length; i++) {{
        layoutNode(DATA[i], 0);
      }}
    }}

    /* ---- Rendering ---- */
    var svgNodes = {{}};  /* id -> g element */
    var svgLinks = {{}};  /* childId -> path element */

    function escapeHtml(s) {{
      var div = document.createElement("div");
      div.textContent = s;
      return div.innerHTML;
    }}

    function truncateText(text, maxLen) {{
      if (text.length <= maxLen) return text;
      return text.substring(0, maxLen - 1) + "\u2026";
    }}

    function createNodeEl(node, isRoot) {{
      var ns = "http://www.w3.org/2000/svg";
      var g = document.createElementNS(ns, "g");
      g.setAttribute("class", "node-group");
      g.setAttribute("data-id", node.id);

      var rect = document.createElementNS(ns, "rect");
      rect.setAttribute("class", "node-rect");
      rect.setAttribute("width", NODE_W);
      rect.setAttribute("height", NODE_H);
      rect.setAttribute("rx", 6);
      rect.setAttribute("ry", 6);
      if (isRoot && node.color) {{
        rect.setAttribute("fill", node.color);
        rect.setAttribute("stroke", node.color);
      }} else {{
        rect.setAttribute("fill", "#fff");
        rect.setAttribute("stroke", "#B0C4D8");
      }}
      g.appendChild(rect);

      /* Text via foreignObject for ellipsis */
      var fo = document.createElementNS(ns, "foreignObject");
      fo.setAttribute("x", 10);
      fo.setAttribute("y", 2);
      fo.setAttribute("width", NODE_W - 20 - (node.children.length > 0 ? 20 : 0));
      fo.setAttribute("height", NODE_H - 4);
      var textDiv = document.createElement("div");
      textDiv.style.cssText = "font-size:13px;font-weight:" + (isRoot ? "700" : "500") +
        ";color:" + (isRoot && node.color ? "#fff" : "#002855") +
        ";line-height:" + NODE_H + "px;height:" + NODE_H +
        "px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;";
      textDiv.textContent = node.name;
      fo.appendChild(textDiv);
      g.appendChild(fo);

      /* Toggle indicator */
      if (node.children.length > 0) {{
        var tc = document.createElementNS(ns, "circle");
        tc.setAttribute("class", "toggle-circle");
        tc.setAttribute("cx", NODE_W + TOGGLE_R + 4);
        tc.setAttribute("cy", NODE_H / 2);
        tc.setAttribute("r", TOGGLE_R);
        g.appendChild(tc);

        var tt = document.createElementNS(ns, "text");
        tt.setAttribute("class", "toggle-text");
        tt.setAttribute("x", NODE_W + TOGGLE_R + 4);
        tt.setAttribute("y", NODE_H / 2);
        tt.textContent = node._collapsed ? "+" : "\u2212";
        g.appendChild(tt);

        tc.addEventListener("click", function(e) {{
          e.stopPropagation();
          toggleNode(node.id);
        }});
        tt.addEventListener("click", function(e) {{
          e.stopPropagation();
          toggleNode(node.id);
        }});
      }}

      /* Click body -> detail popup */
      rect.addEventListener("click", function(e) {{
        e.stopPropagation();
        showPopup(node.id);
      }});
      fo.addEventListener("click", function(e) {{
        e.stopPropagation();
        showPopup(node.id);
      }});

      return g;
    }}

    function buildSvgElements(nodes, isRoot) {{
      for (var i = 0; i < nodes.length; i++) {{
        var node = nodes[i];
        var g = createNodeEl(node, isRoot);
        nodesLayer.appendChild(g);
        svgNodes[node.id] = g;

        /* Create link from parent to this node */
        if (parentMap[node.id]) {{
          var ns = "http://www.w3.org/2000/svg";
          var path = document.createElementNS(ns, "path");
          path.setAttribute("class", "link-path");
          linksLayer.appendChild(path);
          svgLinks[node.id] = path;
        }}

        if (node.children.length > 0) {{
          buildSvgElements(node.children, false);
        }}
      }}
    }}

    function updatePositions() {{
      var allIds = Object.keys(svgNodes);
      for (var k = 0; k < allIds.length; k++) {{
        var id = allIds[k];
        var node = nodeMap[id];
        var g = svgNodes[id];

        if (!node._visible) {{
          g.style.opacity = "0";
          g.style.pointerEvents = "none";
          g.setAttribute("transform", "translate(" + node._x + "," + node._y + ")");
        }} else {{
          g.style.opacity = "";
          g.style.pointerEvents = "";
          g.setAttribute("transform", "translate(" + node._x + "," + node._y + ")");
        }}

        /* Update toggle text */
        var tt = g.querySelector(".toggle-text");
        if (tt) {{
          tt.textContent = node._collapsed ? "+" : "\u2212";
        }}
      }}

      /* Update links */
      var linkIds = Object.keys(svgLinks);
      for (var k = 0; k < linkIds.length; k++) {{
        var childId = linkIds[k];
        var child = nodeMap[childId];
        var pid = parentMap[childId];
        var parent = nodeMap[pid];
        var path = svgLinks[childId];

        if (!child._visible) {{
          path.style.opacity = "0";
          continue;
        }}
        path.style.opacity = "";

        var x1 = parent._x + NODE_W + TOGGLE_R * 2 + 8;
        var y1 = parent._y + NODE_H / 2;
        var x2 = child._x;
        var y2 = child._y + NODE_H / 2;
        var cpx = (x1 + x2) / 2;
        path.setAttribute("d",
          "M" + x1 + "," + y1 +
          " C" + cpx + "," + y1 +
          " " + cpx + "," + y2 +
          " " + x2 + "," + y2);
      }}
    }}

    /* ---- Expand / Collapse ---- */
    function toggleNode(id) {{
      var node = nodeMap[id];
      if (!node || node.children.length === 0) return;
      node._collapsed = !node._collapsed;
      hidePopup();
      doLayout();
      updatePositions();
    }}

    function expandAll() {{
      var ids = Object.keys(nodeMap);
      for (var i = 0; i < ids.length; i++) {{
        nodeMap[ids[i]]._collapsed = false;
      }}
      hidePopup();
      doLayout();
      updatePositions();
    }}

    function collapseAll() {{
      var ids = Object.keys(nodeMap);
      for (var i = 0; i < ids.length; i++) {{
        var n = nodeMap[ids[i]];
        /* Roots stay expanded, everything else collapses */
        if (parentMap[ids[i]]) {{
          n._collapsed = true;
        }} else {{
          n._collapsed = false;
        }}
      }}
      hidePopup();
      doLayout();
      updatePositions();
    }}

    /* ---- Detail Popup ---- */
    var activePopupId = null;

    function showPopup(id) {{
      var node = nodeMap[id];
      if (!node) return;
      activePopupId = id;

      var tierColor = getTierColor(node);
      var tierName = node.tier || "";

      var h = "<h2>" + escapeHtml(node.name) + "</h2>";
      if (node.type || tierName) {{
        if (node.type) {{
          h += '<span class="detail-badge">' + escapeHtml(node.type) + "</span>";
        }}
        if (tierName) {{
          h += '<span class="detail-tier" style="background:' + (tierColor || "#5E7A96") + '">' + escapeHtml(tierName) + "</span>";
        }}
      }}
      if (node.desc) {{
        h += '<div class="detail-section"><h3>Description</h3><p>' + escapeHtml(node.desc) + "</p></div>";
      }}
      if (node.source) {{
        h += '<div class="detail-section"><h3>Source</h3><p>' + escapeHtml(node.source) + "</p></div>";
      }}
      if (node.children.length) {{
        h += '<div class="detail-section"><h3>Children (' + node.children.length + ')</h3><ul class="children-list">';
        for (var i = 0; i < node.children.length; i++) {{
          var child = node.children[i];
          h += '<li><a class="child-link" data-id="' + child.id + '">' + escapeHtml(child.name) + "</a></li>";
        }}
        h += "</ul></div>";
      }}

      popupContent.innerHTML = h;

      /* Bind child links */
      var links = popupContent.querySelectorAll(".child-link");
      for (var i = 0; i < links.length; i++) {{
        (function(a) {{
          a.addEventListener("click", function() {{
            var cid = a.getAttribute("data-id");
            /* Expand to show child */
            node._collapsed = false;
            doLayout();
            updatePositions();
            showPopup(cid);
          }});
        }})(links[i]);
      }}

      /* Position popup near node */
      var svgRect = svgEl.getBoundingClientRect();
      var screenX = (node._x + NODE_W + 30) * zoom + panX + svgRect.left;
      var screenY = node._y * zoom + panY + svgRect.top;

      /* Keep within viewport */
      var popW = 380;
      var popH = 300;
      if (screenX + popW > window.innerWidth - 20) {{
        screenX = (node._x - popW - 10) * zoom + panX + svgRect.left;
        if (screenX < 20) screenX = 20;
      }}
      if (screenY + popH > window.innerHeight - 20) {{
        screenY = window.innerHeight - popH - 20;
      }}
      if (screenY < svgRect.top + 10) {{
        screenY = svgRect.top + 10;
      }}

      popup.style.left = screenX + "px";
      popup.style.top = screenY + "px";
      popup.classList.add("visible");
    }}

    function hidePopup() {{
      popup.classList.remove("visible");
      activePopupId = null;
    }}

    popupClose.addEventListener("click", function(e) {{
      e.stopPropagation();
      hidePopup();
    }});

    /* ---- Pan ---- */
    container.addEventListener("mousedown", function(e) {{
      if (e.target.closest(".node-group") || e.target.closest("#detail-popup")) return;
      isPanning = true;
      panStartX = e.clientX;
      panStartY = e.clientY;
      panStartPanX = panX;
      panStartPanY = panY;
      container.classList.add("panning");
      hidePopup();
    }});

    window.addEventListener("mousemove", function(e) {{
      if (!isPanning) return;
      panX = panStartPanX + (e.clientX - panStartX);
      panY = panStartPanY + (e.clientY - panStartY);
      applyTransform();
    }});

    window.addEventListener("mouseup", function() {{
      isPanning = false;
      container.classList.remove("panning");
    }});

    /* ---- Zoom ---- */
    container.addEventListener("wheel", function(e) {{
      e.preventDefault();
      var rect = svgEl.getBoundingClientRect();
      var mx = e.clientX - rect.left;
      var my = e.clientY - rect.top;

      var oldZoom = zoom;
      var delta = e.deltaY > 0 ? 0.9 : 1.1;
      zoom = Math.min(3.0, Math.max(0.1, zoom * delta));

      /* Zoom toward cursor */
      panX = mx - (mx - panX) * (zoom / oldZoom);
      panY = my - (my - panY) * (zoom / oldZoom);

      applyTransform();
      hidePopup();
    }}, {{ passive: false }});

    /* Click SVG background to dismiss popup */
    svgEl.addEventListener("click", function(e) {{
      if (!e.target.closest(".node-group")) {{
        hidePopup();
      }}
    }});

    /* ---- Reset View ---- */
    function resetView() {{
      panX = PAD_LEFT;
      panY = PAD_TOP;
      zoom = 1;
      applyTransform();
      hidePopup();
    }}

    /* ---- Search ---- */
    var searchActive = false;

    function doSearch() {{
      var query = searchInput.value.trim().toLowerCase();
      if (!query) {{
        clearSearch();
        return;
      }}
      searchActive = true;
      searchClear.style.display = "inline-block";

      /* Find matching ids */
      var matchIds = {{}};
      var ancestorIds = {{}};
      var allIds = Object.keys(nodeMap);
      for (var i = 0; i < allIds.length; i++) {{
        var n = nodeMap[allIds[i]];
        if (n.name.toLowerCase().indexOf(query) !== -1) {{
          matchIds[allIds[i]] = true;
          /* Walk ancestors and expand them */
          var pid = parentMap[allIds[i]];
          while (pid) {{
            ancestorIds[pid] = true;
            nodeMap[pid]._collapsed = false;
            pid = parentMap[pid];
          }}
        }}
      }}

      var matchCount = Object.keys(matchIds).length;
      searchCount.textContent = matchCount ? matchCount + " result" + (matchCount !== 1 ? "s" : "") : "No results";

      /* Re-layout with expanded ancestors */
      doLayout();
      updatePositions();

      /* Apply visual styling */
      for (var i = 0; i < allIds.length; i++) {{
        var g = svgNodes[allIds[i]];
        if (!g) continue;
        if (matchIds[allIds[i]]) {{
          g.classList.add("search-match");
          g.classList.remove("search-dim");
        }} else if (ancestorIds[allIds[i]]) {{
          g.classList.remove("search-match");
          g.classList.remove("search-dim");
        }} else {{
          g.classList.remove("search-match");
          g.classList.add("search-dim");
        }}
      }}

      /* Dim non-relevant links */
      var linkChildIds = Object.keys(svgLinks);
      for (var i = 0; i < linkChildIds.length; i++) {{
        var cid = linkChildIds[i];
        var p = svgLinks[cid];
        if (matchIds[cid] || ancestorIds[cid] || matchIds[parentMap[cid]] || ancestorIds[parentMap[cid]]) {{
          p.classList.remove("search-dim");
        }} else {{
          p.classList.add("search-dim");
        }}
      }}

      /* Pan to first match */
      var firstMatchId = Object.keys(matchIds)[0];
      if (firstMatchId) {{
        var n = nodeMap[firstMatchId];
        var svgRect = svgEl.getBoundingClientRect();
        panX = svgRect.width / 2 - n._x * zoom;
        panY = svgRect.height / 2 - n._y * zoom;
        applyTransform();
      }}

      hidePopup();
    }}

    function clearSearch() {{
      searchInput.value = "";
      searchClear.style.display = "none";
      searchCount.textContent = "";
      searchActive = false;

      /* Remove all search classes */
      var allIds = Object.keys(svgNodes);
      for (var i = 0; i < allIds.length; i++) {{
        svgNodes[allIds[i]].classList.remove("search-match", "search-dim");
      }}
      var linkIds = Object.keys(svgLinks);
      for (var i = 0; i < linkIds.length; i++) {{
        svgLinks[linkIds[i]].classList.remove("search-dim");
      }}

      /* Reset collapse state: roots expanded, rest collapsed */
      collapseAll();
    }}

    /* ---- Wire up buttons ---- */
    document.getElementById("btn-expand-all").addEventListener("click", expandAll);
    document.getElementById("btn-collapse-all").addEventListener("click", collapseAll);
    document.getElementById("btn-reset-view").addEventListener("click", resetView);
    searchInput.addEventListener("input", doSearch);
    searchClear.addEventListener("click", clearSearch);

    /* ---- Initial render ---- */
    buildSvgElements(DATA, true);
    doLayout();
    updatePositions();
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
