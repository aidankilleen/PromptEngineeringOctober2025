#!/usr/bin/env python3
"""
Choropleth of Republic of Ireland counties coloured by Wikipedia prose word counts.

Inputs:
- CSV: 'irish_county_wikipedia_prose_wordcounts.csv' (from the XTools script)
  Columns expected: County, ProseWords (or Words)

- GeoJSON: GADM v4.1 level 1 for Ireland (Republic only)
  File: gadm41_IRL_1.json
  County name field: NAME_1

Outputs:
- Static PNG: ireland_counties_wordcount.png
- Interactive HTML: ireland_counties_wordcount.html
"""

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# ---------- CONFIG (tailored to your files) ----------
CSV_PATH = "irish_county_wikipedia_prose_wordcounts.csv"
GEO_PATH = "gadm41_IRL_1.json"      # your GADM file
COUNTY_NAME_FIELD = "NAME_1"        # GADM county name field

PNG_OUT = "ireland_counties_wordcount.png"
HTML_OUT = "ireland_counties_wordcount.html"

COLOR_MODE = "quantile"   # 'quantile' or 'linear'
N_QUANTILES = 5
# -----------------------------------------------------

def norm_county_name(s: str) -> str:
    """Normalize county names for joining."""
    if s is None:
        return ""
    s0 = str(s).strip()
    # Drop leading 'County ' in CSV entries
    if s0.lower().startswith("county "):
        s0 = s0[7:]
    # Normalise punctuation/case
    s0 = (
        s0.replace("’", "'")
           .replace("–", "-")
           .strip()
           .lower()
    )
    # Historical/alt names (GADM already uses modern names)
    aliases = {
        "kings county": "offaly",
        "queens county": "laois",
    }
    return aliases.get(s0, s0)

def load_wordcounts(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    # Column normalisation
    cols = {c.lower(): c for c in df.columns}
    county_col = cols.get("county")
    words_col = cols.get("prosewords") or cols.get("words")
    if county_col is None or words_col is None:
        raise ValueError("CSV must have 'County' and 'ProseWords' (or 'Words') columns.")

    out = df[[county_col, words_col]].rename(columns={county_col: "county", words_col: "value"})
    out["key"] = out["county"].apply(norm_county_name)
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    return out

def load_geo(geo_path: str, county_field: str) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(geo_path)
    if county_field not in gdf.columns:
        raise ValueError(f"'{county_field}' not found in geodata columns: {list(gdf.columns)}")
    gdf = gdf[[county_field, "geometry"]].rename(columns={county_field: "geo_name"})
    gdf["key"] = gdf["geo_name"].apply(norm_county_name)
    return gdf

def make_bins(values: pd.Series, mode="quantile", k=5):
    v = values.dropna().values
    if len(v) == 0:
        return None, None
    if mode == "quantile":
        qs = np.linspace(0, 1, k + 1)
        bins = np.unique(np.quantile(v, qs))
        if len(bins) >= 3:
            return bins, "Quantiles"
        # fallback if too few unique values
    vmin, vmax = float(np.min(v)), float(np.max(v))
    if vmin == vmax:
        bins = np.array([vmin - 1, vmin, vmax + 1])
    else:
        bins = np.linspace(vmin, vmax, k + 1)
    return bins, "Linear"

def main():
    wc = load_wordcounts(CSV_PATH)
    gdf = load_geo(GEO_PATH, COUNTY_NAME_FIELD)

    # Merge (left: geometries)
    merged = gdf.merge(wc[["key", "value"]], on="key", how="left")

    # Quick sanity info
    unique_geo = merged["geo_name"].nunique()
    print(f"GADM polygons found: {unique_geo} (expected around 26 for counties)\n")

    # Report any non-matches
    missing_values = merged.loc[merged["value"].isna(), "geo_name"].tolist()
    if missing_values:
        print("Counties with no wordcount (name mismatch or missing in CSV):")
        print(", ".join(sorted(set(missing_values))))
        print()

    # Determine bins/scale
    bins, scale_label = make_bins(merged["value"], mode=COLOR_MODE, k=N_QUANTILES)

    # --- Static PNG (matplotlib) ---
    fig = plt.figure(figsize=(8.5, 10))
    ax = plt.gca()
    ax.set_axis_off()
    title = "Wikipedia Prose Word Count by County (Republic of Ireland)"
    if scale_label:
        title += f" — {scale_label} scale"
    plt.title(title, fontsize=14)

    merged.plot(
        column="value",
        cmap="viridis",      # default Matplotlib colormap
        linewidth=0.6,
        edgecolor="white",
        legend=True,
        ax=ax,
        missing_kwds={
            "color": "#f0f0f0",
            "edgecolor": "white",
            "hatch": "...",
            "label": "No data",
        },
    )

    plt.tight_layout()
    plt.savefig(PNG_OUT, dpi=200, bbox_inches="tight")
    print(f"Saved static map -> {PNG_OUT}")

    # --- Interactive HTML (Folium) ---
    try:
        import folium
        from folium.features import GeoJsonTooltip
        import matplotlib.cm as cm
        import matplotlib.colors as mcolors
    except ImportError:
        print("Folium not installed; skipping interactive map. Install with: pip install folium")
        return

    vals = merged["value"].dropna().values
    vmin, vmax = (0.0, 1.0) if len(vals) == 0 else (float(np.min(vals)), float(np.max(vals)))

    def color_for(v):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return "#f0f0f0"
        t = 0.5 if vmin == vmax else (v - vmin) / (vmax - vmin)
        rgba = cm.get_cmap("viridis")(t)
        return mcolors.to_hex(rgba)

    m = folium.Map(location=[53.4, -7.9], zoom_start=6, tiles="cartodbpositron")
    gj = folium.GeoJson(
        merged.to_json(),
        style_function=lambda feat: {
            "fillColor": color_for(feat["properties"].get("value")),
            "color": "white",
            "weight": 0.7,
            "fillOpacity": 0.9,
        },
        tooltip=GeoJsonTooltip(fields=["geo_name", "value"], aliases=["County", "Prose words"]),
        name="Word count",
    )
    gj.add_to(m)
    folium.LayerControl().add_to(m)
    m.save(HTML_OUT)
    print(f"Saved interactive map -> {HTML_OUT}")

if __name__ == "__main__":
    main()
