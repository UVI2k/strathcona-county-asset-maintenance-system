from pathlib import Path
import geopandas as gpd
import folium

PROCESSED = Path("data/processed")
OUTPUTS = Path("outputs")
OUTPUTS.mkdir(parents=True, exist_ok=True)

INFILE = PROCESSED / "streets_priority.geojson"
OUTFILE = OUTPUTS / "priority_map.html"

# Styling by priority band 
BAND_STYLE = {
    "Very Low":  {"color": "#2c7bb6", "weight": 2, "opacity": 0.65},
    "Low":       {"color": "#abd9e9", "weight": 2, "opacity": 0.65},
    "Medium":    {"color": "#ffffbf", "weight": 3, "opacity": 0.75},
    "High":      {"color": "#fdae61", "weight": 4, "opacity": 0.85},
    "Very High": {"color": "#d7191c", "weight": 5, "opacity": 0.95},
}

def style_fn(feature):
    band = feature["properties"].get("priority_band", "Medium")
    return BAND_STYLE.get(band, {"color": "#444444", "weight": 3, "opacity": 0.8})

def tooltip_fields():
    return [
        ("label", "Road Label"),
        ("road_class", "Road Class"),
        ("speed", "Speed"),
        ("addr_count", "Nearby Addresses"),
        ("segment_length_m", "Segment Length (m)"),
        ("priority_score", "Priority Score"),
        ("priority_band", "Priority Band"),
    ]

def make_map(gdf: gpd.GeoDataFrame) -> folium.Map:
    # Center map on dataset bounds
    bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles="OpenStreetMap")

    # Tooltip config 
    available = set(gdf.columns)
    fields = [f for f, _ in tooltip_fields() if f in available]
    aliases = [a for f, a in tooltip_fields() if f in available]

        # ---- Layers ----
    base = folium.FeatureGroup(name="All Roads", show=True)
    high = folium.FeatureGroup(name="High Priority (High + Very High)", show=False)
    vhigh = folium.FeatureGroup(name="Very High Priority Only", show=False)

    # All roads
    folium.GeoJson(
        gdf,
        style_function=style_fn,
        tooltip=folium.GeoJsonTooltip(fields=fields, aliases=aliases, sticky=True, localize=True),
        name="All Roads",
    ).add_to(base)

    # High + Very High
    gdf_high = gdf[gdf["priority_band"].isin(["High", "Very High"])].copy()
    folium.GeoJson(
        gdf_high,
        style_function=style_fn,
        tooltip=folium.GeoJsonTooltip(fields=fields, aliases=aliases, sticky=True, localize=True),
        name="High Priority",
    ).add_to(high)

    # Very High only
    gdf_vhigh = gdf[gdf["priority_band"].isin(["Very High"])].copy()
    folium.GeoJson(
        gdf_vhigh,
        style_function=style_fn,
        tooltip=folium.GeoJsonTooltip(fields=fields, aliases=aliases, sticky=True, localize=True),
        name="Very High Priority",
    ).add_to(vhigh)

    base.add_to(m)
    high.add_to(m)
    vhigh.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)


    # Legend (HTML)
    legend_html = """
    <div style="
        position: fixed;
        bottom: 30px; left: 30px;
        z-index: 9999;
        background: white;
        padding: 12px 14px;
        border: 1px solid #ccc;
        border-radius: 8px;
        font-size: 14px;
        ">
        <b>Maintenance Priority</b><br>
        <i style="background:#2c7bb6;width:12px;height:12px;display:inline-block;"></i> Very Low<br>
        <i style="background:#abd9e9;width:12px;height:12px;display:inline-block;"></i> Low<br>
        <i style="background:#ffffbf;width:12px;height:12px;display:inline-block;"></i> Medium<br>
        <i style="background:#fdae61;width:12px;height:12px;display:inline-block;"></i> High<br>
        <i style="background:#d7191c;width:12px;height:12px;display:inline-block;"></i> Very High<br>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    return m

def main():
    if not INFILE.exists():
        raise FileNotFoundError(f"Missing {INFILE}. Run src/02_priority_score.py first.")

    gdf = gpd.read_file(INFILE)

    # Ensure we are in WGS84 for web mapping
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    elif str(gdf.crs).upper() != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")

    m = make_map(gdf)
    m.save(str(OUTFILE))

    print(f"✅ Saved interactive map: {OUTFILE}")

if __name__ == "__main__":
    main()
