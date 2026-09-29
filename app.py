import io
import math
import os
import tempfile
import urllib.request

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# DXF & SVG Geometry Libraries
try:
  import ezdxf
  from ezdxf import path

  EZDXF_AVAILABLE = True
except ImportError:
  EZDXF_AVAILABLE = False

try:
  from svgpathtools import svg2paths

  SVG_AVAILABLE = True
except ImportError:
  SVG_AVAILABLE = False

try:
  from shapely.geometry import MultiPoint

  SHAPELY_AVAILABLE = True
except ImportError:
  SHAPELY_AVAILABLE = False

# ------------------------------------------------------
# PAGE CONFIGURATION & LIGHT CATALOG STYLING
# ------------------------------------------------------
st.set_page_config(
    page_title="Warner Steel Sales, Inc. - Laser Quoting Dashboard",
    page_icon="⚡",
    layout="wide",
)

st.markdown(
    """
    <style>
    /* 1. FORCE LIGHT INDUSTRIAL CATALOG BACKGROUND ON ALL STREAMLIT CONTAINERS */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stMainBlockContainer"], .main {
        background-color: #eaeaea !important;
        color: #1a1a1a !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif !important;
    }

    /* 2. CATALOG HEADER BAR */
    .catalog-header-bar {
        background-color: #1a1a1a !important;
        border-bottom: 4px solid #cc1111 !important;
        border-radius: 12px;
        padding: 20px 28px;
        margin-bottom: 25px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    /* 3. SECTION HEADERS WITH RED STAR ACCENT */
    .catalog-title {
        font-size: 1.25rem !important;
        font-weight: 900 !important;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #1a1a1a !important;
        margin-bottom: 14px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .catalog-star {
        color: #cc1111 !important;
        font-size: 1.3rem;
    }

    /* 4. FORM FIELD LABELS, CHECKBOXES & INFO CONTRAST FIX */
    label, p, span, [data-testid="stWidgetLabel"], [data-testid="stMarkdownContainer"] p {
        color: #1a1a1a !important;
        font-weight: 700 !important;
    }

    /* FIX QUESTION MARK ICON COLOR (DARK & LEGIBLE) */
    [data-testid="stTooltipIcon"] svg, [data-testid="stTooltipHoverTarget"] svg {
        fill: #1a1a1a !important;
        color: #1a1a1a !important;
        opacity: 0.85 !important;
    }

    /* FIX TOOLTIP POPUP TEXT (WHITE TEXT ON DARK BACKGROUND WITH RED ACCENT BORDER) */
    div[data-baseweb="tooltip"] {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border: 1px solid #cc1111 !important;
        border-radius: 6px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
    }
    div[data-baseweb="tooltip"] * {
        color: #ffffff !important;
        font-weight: 600 !important;
    }

    /* High Contrast Alert & Info Boxes */
    .stAlert, [data-testid="stAlert"] {
        background-color: #ffffff !important;
        border: 1.5px solid #cc1111 !important;
        color: #1a1a1a !important;
        border-radius: 8px !important;
    }
    .stAlert p, [data-testid="stAlert"] p {
        color: #1a1a1a !important;
        font-weight: 800 !important;
    }

    /* 5. FORM INPUTS & DROPDOWNS */
    div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border: 1.5px solid #cccccc !important;
        color: #1a1a1a !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    input {
        color: #1a1a1a !important;
    }

    /* 6. LIGHT FILE UPLOADER DROP-ZONE & BROWSE FILES BUTTON */
    [data-testid="stFileUploader"] {
        background-color: #ffffff !important;
        border: 2px dashed #cccccc !important;
        border-radius: 10px !important;
        padding: 12px !important;
    }
    [data-testid="stFileUploader"] section {
        background-color: #ffffff !important;
    }
    [data-testid="stFileUploader"] section button {
        background-color: #f0f0f0 !important;
        color: #1a1a1a !important;
        border: 1.5px solid #cccccc !important;
        font-weight: 800 !important;
        border-radius: 6px !important;
    }
    [data-testid="stFileUploader"] section button:hover {
        background-color: #e0e0e0 !important;
        border-color: #cc1111 !important;
        color: #cc1111 !important;
    }

    /* 7. METRIC CARDS OVERRIDE */
    [data-testid="stMetric"] {
        background-color: #ffffff !important;
        border: 1px solid #dcdcdc !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04) !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 900 !important;
        color: #1a1a1a !important;
    }
    [data-testid="stMetricLabel"] {
        color: #cc1111 !important;
        font-size: 0.85rem !important;
        font-weight: 800 !important;
        text-transform: uppercase;
    }

    /* 8. RED ACCENT HIGHLIGHT BOX FOR COST PRICING */
    .cost-card {
        background-color: #fdf0f0;
        border: 1.5px solid #f5c6c6;
        border-left: 6px solid #cc1111;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 12px;
        box-shadow: 0 2px 6px rgba(204, 17, 17, 0.08);
    }
    .cost-card label {
        color: #cc1111 !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        font-size: 0.8rem;
        display: block;
        margin-bottom: 2px;
        letter-spacing: 0.5px;
    }
    .cost-card span {
        font-weight: 900;
        font-size: 1.7rem;
        color: #1a1a1a;
    }

    /* 9. CATALOG SPECIFICATIONS PANEL */
    .info-card {
        background-color: #ffffff;
        border: 1px solid #dcdcdc;
        border-left: 4px solid #cc1111;
        padding: 10px 14px;
        border-radius: 8px;
        margin-bottom: 8px;
        color: #1a1a1a;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    }
    .info-card label {
        color: #cc1111 !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        font-size: 0.75rem;
        display: block;
        margin-bottom: 1px;
        letter-spacing: 0.5px;
    }
    .info-card span {
        font-weight: 800;
        font-size: 1.1rem;
        color: #1a1a1a;
    }

    /* 10. TOTAL PRICE BANNER STYLING */
    .total-price-banner {
        background-color: #1a1a1a;
        border-left: 8px solid #cc1111;
        padding: 18px 24px;
        border-radius: 10px;
        margin-top: 15px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .total-price-banner h2 {
        color: #ffffff !important;
        margin: 0;
        font-size: 2.3rem !important;
        font-weight: 900 !important;
        letter-spacing: 0.5px;
    }

    /* 11. WARNER STEEL CRIMSON BUTTONS & TABS */
    .stButton > button {
        background-color: #cc1111 !important;
        color: #ffffff !important;
        font-weight: 800 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        box-shadow: 0 3px 8px rgba(204, 17, 17, 0.3) !important;
    }
    .stButton > button:hover {
        background-color: #aa0e0e !important;
    }

    /* Styled Tab Navigation */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff !important;
        border: 1.5px solid #cccccc !important;
        border-radius: 8px 8px 0 0 !important;
        padding: 10px 20px !important;
        font-weight: 800 !important;
        color: #1a1a1a !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #cc1111 !important;
        color: #ffffff !important;
        border-color: #cc1111 !important;
    }

    hr {
        border-top: 2px solid #cc1111 !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# ------------------------------------------------------
# CONTOUR STITCHING HELPER (ACCURATE PIERCE COUNTING)
# ------------------------------------------------------
def stitch_subpaths_into_contours(subpath_list, tolerance=0.005):
  """Stitches individual line/spline segments into continuous contours."""
  if not subpath_list:
    return [], 0

  segments = []
  for item in subpath_list:
    xs, ys = item["xs"], item["ys"]
    if len(xs) >= 2:
      segments.append({
          "xs": list(xs),
          "ys": list(ys),
          "start": (xs[0], ys[0]),
          "end": (xs[-1], ys[-1]),
          "length": item["length"],
      })

  contours = []

  while segments:
    current = segments.pop(0)
    curr_xs = list(current["xs"])
    curr_ys = list(current["ys"])

    changed = True
    while changed and segments:
      changed = False
      head = (curr_xs[0], curr_ys[0])
      tail = (curr_xs[-1], curr_ys[-1])

      for i, seg in enumerate(segments):
        s_head, s_tail = seg["start"], seg["end"]

        if math.hypot(tail[0] - s_head[0], tail[1] - s_head[1]) <= tolerance:
          curr_xs.extend(seg["xs"][1:])
          curr_ys.extend(seg["ys"][1:])
          segments.pop(i)
          changed = True
          break
        elif math.hypot(tail[0] - s_tail[0], tail[1] - s_tail[1]) <= tolerance:
          curr_xs.extend(seg["xs"][::-1][1:])
          curr_ys.extend(seg["ys"][::-1][1:])
          segments.pop(i)
          changed = True
          break
        elif math.hypot(head[0] - s_tail[0], head[1] - s_tail[1]) <= tolerance:
          curr_xs = seg["xs"][:-1] + curr_xs
          curr_ys = seg["ys"][:-1] + curr_ys
          segments.pop(i)
          changed = True
          break
        elif math.hypot(head[0] - s_head[0], head[1] - s_head[1]) <= tolerance:
          curr_xs = seg["xs"][::-1][:-1] + curr_xs
          curr_ys = seg["ys"][::-1][:-1] + curr_ys
          segments.pop(i)
          changed = True
          break

    contour_len = sum(
        math.hypot(curr_xs[j + 1] - curr_xs[j], curr_ys[j + 1] - curr_ys[j])
        for j in range(len(curr_xs) - 1)
    )

    contours.append({
        "xs": curr_xs,
        "ys": curr_ys,
        "length": contour_len,
    })

  return contours, len(contours)


# ------------------------------------------------------
# MATRIX & EXTRUSION ACCURATE DXF PARSER
# ------------------------------------------------------
def parse_dxf_layers(file_bytes, unit_scale=1.0):
  if not EZDXF_AVAILABLE:
    return None, "ezdxf library is not installed."

  try:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
      tmp.write(file_bytes)
      tmp_path = tmp.name

    doc = ezdxf.readfile(tmp_path)
    os.remove(tmp_path)

    msp = doc.modelspace()
    layer_dict = {}

    entities = []
    to_check = list(msp)
    while to_check:
      e = to_check.pop(0)
      if e.dxftype() == "INSERT":
        try:
          to_check.extend(e.virtual_entities())
        except Exception:
          pass
      else:
        entities.append(e)

    for entity in entities:
      layer_name = str(entity.dxf.layer).strip()
      if layer_name not in layer_dict:
        layer_dict[layer_name] = []

      dxftype = entity.dxftype()
      extrusion_z = getattr(entity.dxf, "extrusion", (0, 0, 1))[2]
      flip_x = -1.0 if extrusion_z < 0 else 1.0

      if dxftype in ("LWPOLYLINE", "POLYLINE"):
        try:
          points = (
              list(entity.vertices())
              if dxftype == "POLYLINE"
              else list(entity.get_points(format="xyb"))
          )
          poly_x, poly_y = [], []
          for pt in points:
            poly_x.append(pt[0] * flip_x * unit_scale)
            poly_y.append(pt[1] * unit_scale)

          if entity.closed and len(poly_x) > 0:
            poly_x.append(poly_x[0])
            poly_y.append(poly_y[0])

          if len(poly_x) >= 2:
            p_len = sum(
                math.hypot(
                    poly_x[i + 1] - poly_x[i], poly_y[i + 1] - poly_y[i]
                )
                for i in range(len(poly_x) - 1)
            )
            layer_dict[layer_name].append({
                "xs": poly_x,
                "ys": poly_y,
                "length": p_len,
            })
        except Exception:
          pass

      elif dxftype == "LINE":
        try:
          start, end = entity.dxf.start, entity.dxf.end
          length_val = (
              math.hypot(end.x - start.x, end.y - start.y) * unit_scale
          )
          x1, y1 = start.x * flip_x * unit_scale, start.y * unit_scale
          x2, y2 = end.x * flip_x * unit_scale, end.y * unit_scale
          layer_dict[layer_name].append({
              "xs": [x1, x2],
              "ys": [y1, y2],
              "length": length_val,
          })
        except Exception:
          pass

      elif dxftype == "CIRCLE":
        try:
          r, center = entity.dxf.radius, entity.dxf.center
          cx = center.x * flip_x * unit_scale
          cy = center.y * unit_scale
          length_val = (2 * math.pi * r) * unit_scale
          circle_x, circle_y = [], []
          for a in range(0, 365, 5):
            rad = math.radians(a)
            circle_x.append(cx + (r * math.cos(rad) * unit_scale))
            circle_y.append(cy + (r * math.sin(rad) * unit_scale))
          layer_dict[layer_name].append({
              "xs": circle_x,
              "ys": circle_y,
              "length": length_val,
          })
        except Exception:
          pass

      elif dxftype == "ARC":
        try:
          r = entity.dxf.radius
          start_angle = math.radians(entity.dxf.start_angle)
          end_angle = math.radians(entity.dxf.end_angle)
          angle_diff = (end_angle - start_angle) % (2 * math.pi)
          length_val = (r * angle_diff) * unit_scale
          center = entity.dxf.center
          cx = center.x * flip_x * unit_scale
          cy = center.y * unit_scale

          arc_x, arc_y = [], []
          steps = max(12, int(math.degrees(angle_diff) / 3))
          for step in range(steps + 1):
            a = start_angle + (angle_diff * step / steps)
            arc_x.append(cx + (r * math.cos(a) * unit_scale))
            arc_y.append(cy + (r * math.sin(a) * unit_scale))
          layer_dict[layer_name].append({
              "xs": arc_x,
              "ys": arc_y,
              "length": length_val,
          })
        except Exception:
          pass

      elif dxftype in ("SPLINE", "ELLIPSE"):
        try:
          bspline = entity.construction_tool()
          pts = list(bspline.approximate(segments=32))
          spline_x = [pt.x * flip_x * unit_scale for pt in pts]
          spline_y = [pt.y * unit_scale for pt in pts]

          if len(spline_x) >= 2:
            p_len = sum(
                math.hypot(
                    spline_x[i + 1] - spline_x[i],
                    spline_y[i + 1] - spline_y[i],
                )
                for i in range(len(spline_x) - 1)
            )
            layer_dict[layer_name].append({
                "xs": spline_x,
                "ys": spline_y,
                "length": p_len,
            })
        except Exception:
          pass

    layer_dict = {k: v for k, v in layer_dict.items() if len(v) > 0}

    if not layer_dict:
      return None, "No valid geometric entities found in DXF file."

    non_cut_keywords = ["BEND", "EXTENT", "TEXT", "DIM", "MARK", "REF"]
    default_layers = [
        l
        for l in layer_dict.keys()
        if not any(kw in l.upper() for kw in non_cut_keywords)
    ]
    if not default_layers:
      default_layers = list(layer_dict.keys())

    return {
        "all_layers": list(layer_dict.keys()),
        "default_layers": default_layers,
        "layer_dict": layer_dict,
    }, None

  except Exception as e:
    return None, f"Error parsing DXF file: {str(e)}"


def parse_svg_geometry(file_bytes, unit_scale=1.0):
  if not SVG_AVAILABLE:
    return None, "svgpathtools library is not installed."

  try:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".svg") as tmp:
      tmp.write(file_bytes)
      tmp_path = tmp.name

    paths, _ = svg2paths(tmp_path)
    os.remove(tmp_path)

    if not paths:
      return None, "No valid vector paths found in SVG file."

    total_length = 0.0
    subpaths_to_plot = []
    all_xs, all_ys = [], []
    scale = unit_scale

    for p in paths:
      try:
        total_length += p.length()

        for subpath in p.continuous_subpaths():
          path_pts_x, path_pts_y = [], []
          num_samples = max(16, int(subpath.length() / 1.5))

          for i in range(num_samples + 1):
            point = subpath.point(i / num_samples)
            px = point.real * scale
            py = -point.imag * scale
            path_pts_x.append(px)
            path_pts_y.append(py)
            all_xs.append(px)
            all_ys.append(py)

          subpaths_to_plot.append((path_pts_x, path_pts_y))
      except Exception:
        pass

    if not all_xs:
      return None, "Could not extract bounding box from SVG."

    min_x, max_x = min(all_xs), max(all_xs)
    min_y, max_y = min(all_ys), max(all_ys)

    part_w = max_x - min_x
    part_h = max_y - min_y
    scaled_cut_len = total_length * scale

    if part_w > 120.0 or part_h > 120.0:
      part_w /= 25.4
      part_h /= 25.4
      scaled_cut_len /= 25.4
      scale /= 25.4
      subpaths_to_plot = [
          ([x / 25.4 for x in xs], [y / 25.4 for y in ys])
          for xs, ys in subpaths_to_plot
      ]

    return {
        "all_layers": ["SVG Profile"],
        "default_layers": ["SVG Profile"],
        "layer_dict": {
            "SVG Profile": [{
                "xs": xs,
                "ys": ys,
                "length": scaled_cut_len / len(subpaths_to_plot),
            } for xs, ys in subpaths_to_plot]
        },
    }, None

  except Exception as e:
    return None, f"Error parsing SVG file: {str(e)}"


# ------------------------------------------------------
# DYNAMIC METRIC RECALCULATION WITH STITCHED PIERCES
# ------------------------------------------------------
def recalculate_active_geometry(
    layer_dict, selected_layers, lead_in_per_pierce=0.5
):
  raw_subpaths = []

  for layer_name in selected_layers:
    if layer_name in layer_dict:
      raw_subpaths.extend(layer_dict[layer_name])

  if not raw_subpaths:
    return {
        "cut_length": 0.0,
        "pierces": 0,
        "length": 0.0,
        "width": 0.0,
        "hull_ratio": 1.0,
        "subpaths": [],
        "part_w": 0.0,
        "part_h": 0.0,
        "min_x": 0.0,
        "min_y": 0.0,
    }

  contours, total_pierces = stitch_subpaths_into_contours(
      raw_subpaths, tolerance=0.005
  )

  all_xs, all_ys = [], []
  raw_cut_length = 0.0
  active_subpaths = []

  for c in contours:
    raw_cut_length += c["length"]
    active_subpaths.append((c["xs"], c["ys"]))
    all_xs.extend(c["xs"])
    all_ys.extend(c["ys"])

  min_x, max_x = min(all_xs), max(all_xs)
  min_y, max_y = min(all_ys), max(all_ys)

  part_w = max_x - min_x
  part_h = max_y - min_y

  total_effective_cut_length = raw_cut_length + (
      total_pierces * lead_in_per_pierce
  )

  hull_ratio = 1.0
  if SHAPELY_AVAILABLE and len(all_xs) >= 3 and part_w > 0 and part_h > 0:
    try:
      pts = list(zip(all_xs, all_ys))
      mp = MultiPoint(pts)
      bbox_area = part_w * part_h
      if bbox_area > 0:
        hull_ratio = max(0.2, min(mp.convex_hull.area / bbox_area, 1.0))
    except Exception:
      hull_ratio = 1.0

  return {
      "cut_length": round(max(total_effective_cut_length, 0.0), 2),
      "pierces": max(total_pierces, 1),
      "length": round(max(part_w, part_h), 2),
      "width": round(min(part_w, part_h), 2),
      "hull_ratio": hull_ratio,
      "subpaths": active_subpaths,
      "part_w": part_w,
      "part_h": part_h,
      "min_x": min_x,
      "min_y": min_y,
  }


# ------------------------------------------------------
# LIVE GOOGLE SHEET CONNECTION
# ------------------------------------------------------
PUBLISHED_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSwuOZluQH2b4ODvc7dW3NZPIeYqJf7M7yuNGuKoWeo9L4zuJxLpPTgjFxLvpdrs5_51a80QNP7NZwL/pub?gid=1755421406&single=true&output=csv"


@st.cache_data(ttl=600)
def load_data():
  req = urllib.request.Request(
      PUBLISHED_CSV_URL,
      headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
  )
  with urllib.request.urlopen(req) as response:
    csv_data = response.read()

  df = pd.read_csv(io.BytesIO(csv_data))
  df.columns = df.columns.astype(str).str.strip()
  return df


try:
  vlookup_data = load_data()
except Exception as e:
  st.error(f"Failed to load Google Sheet data: {e}")
  st.stop()

# ------------------------------------------------------
# HEADER & LOGO
# ------------------------------------------------------
header_col1, header_col2 = st.columns([1, 5])

with header_col1:
  if os.path.exists("logo.png"):
    st.image("logo.png", width=140)
  elif os.path.exists("warner_steel_1280x1280.png"):
    st.image("warner_steel_1280x1280.png", width=140)
  else:
    st.image(
        "https://via.placeholder.com/150x80/cc1111/ffffff?text=WARNER+STEEL",
        width=140,
    )

with header_col2:
  st.title("Warner Steel Sales, Inc.")
  st.caption(
      "2623 E. Raymond St · Indianapolis, IN 46203 · (317) 789-1733 ·"
      " sales@warnersteel.com"
  )

st.divider()

# ------------------------------------------------------
# SESSION STATE INITIALIZATION & RESET HANDLER
# ------------------------------------------------------
if "step" not in st.session_state:
  st.session_state.step = 1


def reset_quote_data():
  st.session_state.cut_length = 0.0
  st.session_state.pierces = 0
  st.session_state.length = 0.0
  st.session_state.width = 0.0
  st.session_state.qty = 1
  st.session_state.hull_ratio = 1.0
  st.session_state.subpaths_to_render = None
  st.session_state.part_w = 0.0
  st.session_state.part_h = 0.0
  st.session_state.min_x = 0.0
  st.session_state.min_y = 0.0
  st.session_state.parsed_layer_data = None
  st.session_state.layer_toggles = {}
  st.session_state.input_mode = "manual"
  st.session_state.step = 1


if "cut_length" not in st.session_state:
  reset_quote_data()

# ------------------------------------------------------
# STEP 1: QUOTE INPUTS & LIVE INTERACTIVE CAD VIEWER
# ------------------------------------------------------
if st.session_state.step == 1:
  top_row1, top_row2 = st.columns([4, 1])
  with top_row1:
    st.markdown(
        '<div class="catalog-title"><span class="catalog-star">✦</span>STEP 1:'
        " ENTER QUOTE DETAILS</div>",
        unsafe_allow_html=True,
    )
  with top_row2:
    if st.button("🔄 Reset / Start New Quote"):
      reset_quote_data()
      st.rerun()

  # 1. MATERIAL & THICKNESS INPUTS (FIRST AT THE TOP)
  mat_col1, mat_col2 = st.columns(2, gap="large")

  with mat_col1:
    mats = vlookup_data["Material"].dropna().unique()
    sel_mat_idx = (
        list(mats).index(st.session_state.selected_mat)
        if "selected_mat" in st.session_state
        and st.session_state.selected_mat in mats
        else 0
    )
    selected_mat = st.selectbox("Material Choice", mats, index=sel_mat_idx)

  with mat_col2:
    available_thick = (
        vlookup_data[vlookup_data["Material"] == selected_mat]["Thickness"]
        .dropna()
        .unique()
    )
    sel_thick_idx = (
        list(available_thick).index(st.session_state.selected_thick)
        if "selected_thick" in st.session_state
        and st.session_state.selected_thick in available_thick
        else 0
    )
    selected_thick = st.selectbox(
        "Thickness Choice", available_thick, index=sel_thick_idx
    )

  st.divider()

  # 2. DEFAULT TO MANUAL DATA ENTRY TAB FIRST
  tab_manual, tab_upload = st.tabs(
      ["✏️ Manual Data Entry", "⚡ Upload CAD File (.dxf / .svg)"]
  )

  # --- TAB 1: MANUAL DATA ENTRY (STACKED VERTICALLY) ---
  with tab_manual:
    st.info(
        "💡 **Manual Entry Note:** Enter the **TOTAL Cut Length** and **TOTAL"
        " Pierces** for your full array layout. Quantity is optional and will"
        " divide totals for per-part unit metrics."
    )

    col_m1, col_m2 = st.columns([1.2, 1], gap="large")

    with col_m1:
      total_job_cut_len = st.number_input(
          "TOTAL Job Cut Length (Inches across ALL parts)",
          min_value=0.0,
          value=float(st.session_state.get("cut_length", 0.0))
          * max(1, int(st.session_state.get("qty", 1))),
          help="Enter the total linear cut length for the entire array/nest.",
      )
      total_job_pierces = st.number_input(
          "TOTAL Job Pierces (Across ALL parts)",
          min_value=0,
          value=int(st.session_state.get("pierces", 0))
          * max(1, int(st.session_state.get("qty", 1))),
          help="Enter the total pierces for the entire array/nest.",
      )
      array_len = st.number_input(
          "Array Length (in)",
          min_value=0.0,
          value=float(st.session_state.get("length", 0.0)),
      )
      array_wid = st.number_input(
          "Array Width (in)",
          min_value=0.0,
          value=float(st.session_state.get("width", 0.0)),
      )
      manual_qty = st.number_input(
          "Total Order Quantity (pcs, Optional)",
          min_value=0,
          value=int(st.session_state.get("qty", 1)),
          step=1,
          key="manual_qty_input",
          help=(
              "Optional quantity. Used to compute per-part unit cost"
              " breakouts."
          ),
      )

      effective_qty = manual_qty if manual_qty > 0 else 1
      per_part_cut_len = total_job_cut_len / effective_qty
      per_part_pierces = int(round(total_job_pierces / effective_qty))

    with col_m2:
      st.markdown(
          f"""
          <div class="info-card" style="margin-top: 25px;">
              <label>Calculated Unit Breakout</label>
              <span>Per Part Cut Length: {per_part_cut_len:.2f} in</span><br>
              <span>Per Part Pierces: {per_part_pierces}</span>
          </div>
      """,
          unsafe_allow_html=True,
      )

  # --- TAB 2: CAD FILE UPLOADER ---
  with tab_upload:
    uploaded_file = st.file_uploader(
        "Drop DXF or SVG file here to extract geometry and cut layers",
        type=["dxf", "svg"],
    )

    col_units, col_qty = st.columns(2)
    with col_units:
      cad_units = st.selectbox(
          "File Units", ["Inches", "Millimeters (mm)", "Screen Pixels (96 DPI)"]
      )
    with col_qty:
      part_qty_upload = st.number_input(
          "Part Quantity",
          min_value=1,
          value=int(st.session_state.get("qty", 1)),
          step=1,
          key="upload_qty_input",
      )

    if cad_units == "Inches":
      unit_scale = 1.0
    elif cad_units == "Millimeters (mm)":
      unit_scale = 0.0393701
    else:
      unit_scale = 1.0 / 96.0

    if uploaded_file is not None:
      file_bytes = uploaded_file.read()
      filename = uploaded_file.name.lower()

      if filename.endswith(".dxf"):
        data, error = parse_dxf_layers(file_bytes, unit_scale=unit_scale)
      elif filename.endswith(".svg"):
        data, error = parse_svg_geometry(file_bytes, unit_scale=unit_scale)
      else:
        data, error = None, "Unsupported file format."

      if error:
        st.error(error)
      elif data:
        st.session_state.parsed_layer_data = data
        st.session_state.qty = part_qty_upload
        st.session_state.input_mode = "upload"

        if (
            "layer_toggles" not in st.session_state
            or not st.session_state.layer_toggles
        ):
          st.session_state.layer_toggles = {
              layer_name: (layer_name in data["default_layers"])
              for layer_name in data["all_layers"]
          }

    # Interactive Layer Controls & Live Preview
    if st.session_state.get("parsed_layer_data") is not None:
      layer_info = st.session_state.parsed_layer_data
      all_layers = layer_info["all_layers"]
      layer_dict = layer_info["layer_dict"]

      st.markdown("---")
      st.subheader("Interactive Layer Controls & Live CAD Alignment Viewer")

      viewer_col1, viewer_col2 = st.columns([1, 1.3], gap="large")

      with viewer_col1:
        st.write("Toggle layers **ON** or **OFF** to select cut paths:")

        active_layers = []
        for l_name in all_layers:
          is_active = st.checkbox(
              f"Layer: {l_name}",
              value=st.session_state.layer_toggles.get(l_name, True),
              key=f"toggle_{l_name}",
          )
          st.session_state.layer_toggles[l_name] = is_active
          if is_active:
            active_layers.append(l_name)

        active_geom = recalculate_active_geometry(
            layer_dict, active_layers, lead_in_per_pierce=0.5
        )

        st.session_state.cut_length = active_geom["cut_length"]
        st.session_state.pierces = active_geom["pierces"]
        st.session_state.length = active_geom["length"]
        st.session_state.width = active_geom["width"]
        st.session_state.hull_ratio = active_geom["hull_ratio"]
        st.session_state.subpaths_to_render = active_geom["subpaths"]
        st.session_state.part_w = active_geom["part_w"]
        st.session_state.part_h = active_geom["part_h"]
        st.session_state.min_x = active_geom["min_x"]
        st.session_state.min_y = active_geom["min_y"]

        st.markdown(
            f"""
            <div class="info-card" style="margin-top: 15px;">
                <label>Active Geometry Summary (Incl. 0.5" Lead-In per Pierce)</label>
                <span>Active Cut Length (Per Part): {active_geom['cut_length']} in</span><br>
                <span>Active Pierces (Per Part): {active_geom['pierces']}</span><br>
                <span>Bounding Box: {active_geom['length']}" L × {active_geom['width']}" W</span>
            </div>
        """,
            unsafe_allow_html=True,
        )

      with viewer_col2:
        st.caption("Live Transformed CAD Preview (Active Layers Only)")
        fig_preview, ax_preview = plt.subplots(
            figsize=(6, 4.5), facecolor="#ffffff"
        )
        ax_preview.set_facecolor("#fafafa")

        if active_geom["subpaths"]:
          for xs, ys in active_geom["subpaths"]:
            ax_preview.plot(xs, ys, color="#cc1111", linewidth=1.2)
          ax_preview.set_aspect("equal", adjustable="datalim")
        else:
          ax_preview.text(
              0.5,
              0.5,
              "No active layers selected",
              ha="center",
              va="center",
              color="#cc1111",
              fontsize=12,
              weight="bold",
              transform=ax_preview.transAxes,
          )

        ax_preview.axis("off")
        st.pyplot(fig_preview, clear_figure=True)

  st.divider()

  if st.button("Calculate Quote & View Estimate →", type="primary"):
    if (
        st.session_state.get("input_mode") == "upload"
        and st.session_state.get("parsed_layer_data") is not None
    ):
      qty = part_qty_upload
    else:
      qty = effective_qty
      st.session_state.cut_length = per_part_cut_len
      st.session_state.pierces = per_part_pierces
      st.session_state.length = array_len
      st.session_state.width = array_wid
      st.session_state.subpaths_to_render = None

    if (
        st.session_state.length == 0
        or st.session_state.width == 0
        or st.session_state.cut_length == 0
    ):
      st.warning(
          "Please select active CAD layers or enter valid total dimensions"
          " before continuing."
      )
    else:
      st.session_state.selected_mat = selected_mat
      st.session_state.selected_thick = selected_thick
      st.session_state.qty = qty
      if st.session_state.part_w == 0.0:
        st.session_state.part_w = st.session_state.length
      if st.session_state.part_h == 0.0:
        st.session_state.part_h = st.session_state.width
      st.session_state.step = 2
      st.rerun()

# ------------------------------------------------------
# STEP 2: ESTIMATE SUMMARY & COST PIE CHART
# ------------------------------------------------------
elif st.session_state.step == 2:
  nav_col1, nav_col2 = st.columns([4, 1])
  with nav_col1:
    if st.button("← Revise Quote Inputs"):
      st.session_state.step = 1
      st.rerun()
  with nav_col2:
    if st.button("🔄 Reset / Start New Quote"):
      reset_quote_data()
      st.rerun()

  selected_mat = st.session_state.selected_mat
  selected_thick = st.session_state.selected_thick
  cut_length = st.session_state.cut_length
  pierces = st.session_state.pierces
  length = st.session_state.length
  width = st.session_state.width
  qty = st.session_state.qty
  hull_ratio = st.session_state.hull_ratio
  subpaths_to_render = st.session_state.subpaths_to_render
  part_w = st.session_state.part_w
  part_h = st.session_state.part_h
  min_x = st.session_state.min_x
  min_y = st.session_state.min_y

  matched_rows = vlookup_data[
      (vlookup_data["Material"] == selected_mat)
      & (vlookup_data["Thickness"] == selected_thick)
  ]

  spacing_gap = 0.25

  if qty == 1:
    cols, rows = 1, 1
  else:
    cols = math.ceil(math.sqrt(qty * (part_h / part_w if part_w > 0 else 1.0)))
    cols = max(1, min(qty, cols))
    rows = math.ceil(qty / cols)

  array_width = (cols * part_w) + (max(0, cols - 1) * spacing_gap)
  array_height = (rows * part_h) + (max(0, rows - 1) * spacing_gap)

  out_col1, out_col2 = st.columns([1.1, 0.9], gap="large")

  with out_col1:
    st.markdown(
        '<div class="catalog-title"><span class="catalog-star">✦</span>CALCULATED'
        " QUOTE BREAKDOWN</div>",
        unsafe_allow_html=True,
    )

    if matched_rows.empty:
      st.warning("No pricing data found for this Material and Thickness.")
    else:
      row = matched_rows.iloc[0]

      base_part_area_sq_ft = (
          (length + spacing_gap) * (width + spacing_gap)
      ) / 144.0

      shape_discount_pct = 80.0
      if qty > 1:
        efficiency_multiplier = 1.0 - (
            (1.0 - hull_ratio) * (shape_discount_pct / 100.0)
        )
      else:
        efficiency_multiplier = 1.0

      total_area_sq_ft = base_part_area_sq_ft * qty * efficiency_multiplier

      def clean_num(val):
        if pd.isna(val):
          return 0.0
        s = str(val).replace("$", "").replace(",", "").strip()
        try:
          return float(s)
        except ValueError:
          return 0.0

      cost_per_in = clean_num(row.get("Cost_per_in", 0))
      cost_per_pierce = clean_num(row.get("Pierce_Cost", 0))
      gas_rate = clean_num(row.get("Gas_Cost_per_in", 0))
      setup_sqft_rate = clean_num(row.get("Setup_cost_per_sqft", 0))
      laser_velocity = clean_num(row.get("Laser_Velocity", 0))

      total_cut_length = cut_length * qty
      total_pierces = pierces * qty

      cut_price = total_cut_length * cost_per_in
      pierce_price = total_pierces * cost_per_pierce
      gas_price = gas_rate * total_cut_length
      setup_price = setup_sqft_rate * total_area_sq_ft

      if laser_velocity > 0:
        est_cut_time_sec = (total_cut_length / laser_velocity) * 60.0
      else:
        est_cut_time_sec = 0.0

      total_price = cut_price + pierce_price + gas_price + setup_price

      # --- ROW 1: Cut Length ---
      r1_c1, r1_c2, r1_c3 = st.columns(3)
      r1_c1.metric("Cut Length (Total)", f"{total_cut_length:.1f} in")
      r1_c2.metric("Rate ($/in)", f"${cost_per_in:.3f}")
      with r1_c3:
        st.markdown(
            f"""
            <div class="cost-card">
                <label>Cut Price</label>
                <span>${cut_price:.2f}</span>
            </div>
        """,
            unsafe_allow_html=True,
        )

      # --- ROW 2: Pierces ---
      r2_c1, r2_c2, r2_c3 = st.columns(3)
      r2_c1.metric("Pierces (Total)", f"{total_pierces}")
      r2_c2.metric("Rate ($/pierce)", f"${cost_per_pierce:.3f}")
      with r2_c3:
        st.markdown(
            f"""
            <div class="cost-card">
                <label>Pierce Price</label>
                <span>${pierce_price:.2f}</span>
            </div>
        """,
            unsafe_allow_html=True,
        )

      # --- ROW 3: Gas ---
      r3_c1, r3_c2, r3_c3 = st.columns(3)
      r3_c1.metric("Gas Type", f"{row.get('Gas', 'N/A')}")
      r3_c2.metric("Rate ($/in)", f"${gas_rate:.3f}")
      with r3_c3:
        st.markdown(
            f"""
            <div class="cost-card">
                <label>Gas Price</label>
                <span>${gas_price:.2f}</span>
            </div>
        """,
            unsafe_allow_html=True,
        )

      # --- ROW 4: Material Footprint ---
      r4_c1, r4_c2, r4_c3 = st.columns(3)
      r4_c1.metric("Nestable Area", f"{total_area_sq_ft:.2f} sq ft")
      r4_c2.metric("Setup Rate ($/sq ft)", f"${setup_sqft_rate:.3f}")
      with r4_c3:
        st.markdown(
            f"""
            <div class="cost-card">
                <label>Setup Price</label>
                <span>${setup_price:.2f}</span>
            </div>
        """,
            unsafe_allow_html=True,
        )

      # TOTAL PRICE BANNER
      st.markdown(
          f"""
          <div class="total-price-banner">
              <h2>Total Price ({qty} pc{"s" if qty > 1 else ""}): ${total_price:.2f}</h2>
          </div>
      """,
          unsafe_allow_html=True,
      )

      # --- SIDE-BY-SIDE: COST PIE CHART & JOB DETAILS ---
      info_col1, info_col2 = st.columns([0.45, 0.55], gap="small")

      with info_col1:
        st.caption("Cost Driver Distribution")

        cost_labels = ["Cut", "Pierce", "Gas", "Setup"]
        cost_values = [cut_price, pierce_price, gas_price, setup_price]

        filtered_labels = [
            label for label, val in zip(cost_labels, cost_values) if val > 0
        ]
        filtered_values = [val for val in cost_values if val > 0]

        if sum(filtered_values) > 0:
          fig_pie, ax_pie = plt.subplots(figsize=(3.8, 2.6), facecolor="none")
          ax_pie.set_facecolor("none")

          colors = ["#cc1111", "#e65100", "#1976d2", "#388e3c"]

          wedges, texts, autotexts = ax_pie.pie(
              filtered_values,
              labels=filtered_labels,
              autopct="%1.0f%%",
              startangle=140,
              colors=colors[: len(filtered_values)],
              textprops=dict(color="#1a1a1a", fontsize=8, weight="bold"),
              wedgeprops=dict(
                  width=0.45, edgecolor=(0.0, 0.0, 0.0, 0.15), linewidth=1.2
              ),
          )

          for autotext in autotexts:
            autotext.set_fontsize(7.5)

          ax_pie.axis("equal")
          st.pyplot(fig_pie, clear_figure=True)

      with info_col2:
        st.caption("Job Specifications")
        st.markdown(
            f"""
            <div class="info-card">
                <label>Material & Thickness</label>
                <span>{selected_mat} — {selected_thick}</span>
            </div>
            <div class="info-card">
                <label>Single Part Bounds</label>
                <span>{length:.2f}" L × {width:.2f}" W</span>
            </div>
            <div class="info-card">
                <label>Est. Total Cut Time</label>
                <span>{est_cut_time_sec:.1f} sec ({est_cut_time_sec/60.0:.2f} min)</span>
            </div>
            <div class="info-card">
                <label>Estimated Array Footprint ({cols} × {rows} Grid, 0.25" gap)</label>
                <span>{array_width:.2f}" W × {array_height:.2f}" H</span>
            </div>
        """,
            unsafe_allow_html=True,
        )

  with out_col2:
    st.markdown(
        f'<div class="catalog-title"><span class="catalog-star">✦</span>ARRAY'
        f" VIEW ({cols} × {rows} GRID)</div>",
        unsafe_allow_html=True,
    )

    fig, ax = plt.subplots(figsize=(7, 5), facecolor="#ffffff")
    ax.set_facecolor("#fafafa")

    cell_w = part_w + spacing_gap
    cell_h = part_h + spacing_gap

    for r in range(rows):
      for c in range(cols):
        if (r * cols + c) >= qty:
          break

        grid_x = c * cell_w
        grid_y = r * cell_h

        rect = plt.Rectangle(
            (grid_x, grid_y),
            part_w,
            part_h,
            fill=False,
            edgecolor="#cc1111",
            linestyle="--",
            linewidth=0.8,
        )
        ax.add_patch(rect)

        if subpaths_to_render:
          for xs, ys in subpaths_to_render:
            norm_xs = [x - min_x + grid_x for x in xs]
            norm_ys = [y - min_y + grid_y for y in ys]
            ax.plot(norm_xs, norm_ys, color="#111111", linewidth=1.1)
        else:
          rect_part = plt.Rectangle(
              (grid_x, grid_y),
              part_w,
              part_h,
              fill=True,
              facecolor="#fdf0f0",
              edgecolor="#cc1111",
              linewidth=1.2,
          )
          ax.add_patch(rect_part)

    ax.set_aspect("equal", adjustable="datalim")
    ax.axis("off")
    st.pyplot(fig, clear_figure=True)