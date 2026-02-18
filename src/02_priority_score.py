from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd

RAW = Path("data/raw")
PROCESSED = Path("data/processed")
OUTPUTS = Path("outputs")
PROCESSED.mkdir(parents = True, exist_ok=True)
OUTPUTS.mkdir(parents = True, exist_ok=True)

STREET_PATH = RAW / "Street_Network.geojson"
ADDRESS_PATH = RAW / "Civic_Address.geojson"

# Good Projected CRS for Edmonton/ Strathcona (mts)
PROJECTED_CRS = "EPSG:3400" #NAD83 / Alberta 10-TM

def minmax(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    s = s.astype("float64")
    lo = s.min(skipna=True)
    hi = s.max(skipna=True)
    if pd.isna(lo) or pd.isna(hi) or hi == lo:
        return pd.Series(0.0, index=s.index, dtype="float64")
    return ((s - lo) / (hi - lo)).astype("float64")


def road_class_weight(series: pd.Series) -> pd.Series:
    """
    Map road_class to a maintenance importance weight.
    If values are unfamiliar, default to 1.0.
    """

    s = series.astype(str).str.upper().fillna("UNKNOWN")

    weights = pd.Series(1.0, index=s.index)

    #Commons Patterns
    weights[s.str.contains("HIGHWAY|FREEWAY")] = 1.00
    weights[s.str.contains("ARTERIAL")] = 0.85
    weights[s.str.contains("COLLECTOR")] = 0.70
    weights[s.str.contains("LOCAL|RESIDENT")] = 0.45
    weights[s.str.contains("RAMP")] = 0.60

    return weights

def main():
    streets = gpd.read_file(STREET_PATH)
    addresses = gpd.read_file(ADDRESS_PATH)

    # Project to meters for buffering + lengths
    streets_m = streets.to_crs(PROJECTED_CRS)
    addresses_m = addresses.to_crs(PROJECTED_CRS)

    # 1) Segment length in meters
    streets_m["segment_length_m"] = streets_m.geometry.length

    # 2) Address density proxy: count addresses within 30m of each road segment
    buffer_m = 30
    streets_buf = streets_m[["objectid", "geometry"]].copy()
    streets_buf["geometry"] = streets_buf.geometry.buffer(buffer_m)

    # Spatial join: points within buffered road polygons
    joined = gpd.sjoin(
        addresses_m[["objectid", "geometry"]],
        streets_buf[["objectid", "geometry"]],
        predicate="within",
        how="inner",
    )

    addr_counts = joined.groupby("objectid_right").size().rename("addr_count")
    streets_m = streets_m.merge(
        addr_counts,
        left_on="objectid",
        right_index=True,
        how="left"
    )
    streets_m["addr_count"] = streets_m["addr_count"].fillna(0).astype(int)

    # 3) Create feature proxies
    streets_m["speed_num"] = pd.to_numeric(streets_m["speed"], errors="coerce").fillna(0)
    streets_m["road_class_w"] = road_class_weight(streets_m["road_class"])

    # Normalize
    streets_m["addr_norm"] = minmax(streets_m["addr_count"])
    streets_m["speed_norm"] = minmax(streets_m["speed_num"])
    streets_m["len_norm"] = minmax(streets_m["segment_length_m"])
    streets_m["class_norm"] = minmax(streets_m["road_class_w"])

    for c in ["addr_norm","speed_norm","len_norm","class_norm"]:
        streets_m[c] = pd.to_numeric(streets_m[c], errors="coerce").fillna(0.0)

    # print("CRS streets:", streets_m.crs, "CRS addresses:", addresses_m.crs)
    # print("addr_count describe:\n", streets_m["addr_count"].describe())
    # print("speed_num describe:\n", streets_m["speed_num"].describe())
    # print("segment_length_m describe:\n", streets_m["segment_length_m"].describe())

    # print("roads with addr_count>0:", (streets_m["addr_count"] > 0).sum(), "of", len(streets_m))

    # Traffic proxy = blend of address density + speed
    streets_m["traffic_proxy"] = 0.7 * streets_m["addr_norm"] + 0.3 * streets_m["speed_norm"]

    # 4) Priority score (0-100)
    # Tuned for "maintenance priority": usage + importance + length
    streets_m["priority_score"] = (
    0.50 * streets_m["traffic_proxy"] +
    0.30 * streets_m["class_norm"] +
    0.20 * streets_m["len_norm"]
    )

    streets_m["priority_score"] = pd.to_numeric(streets_m["priority_score"], errors="coerce").fillna(0.0)
    streets_m["priority_score"] = (100 * streets_m["priority_score"]).round(2)

    print("addr_norm:", streets_m["addr_norm"].describe())
    print("speed_norm:", streets_m["speed_norm"].describe())
    print("len_norm:", streets_m["len_norm"].describe())
    print("class_norm:", streets_m["class_norm"].describe())
    print("traffic_proxy:", streets_m["traffic_proxy"].describe())
    print("priority_score:", streets_m["priority_score"].describe())

    print(streets_m[["addr_norm","speed_norm","len_norm","class_norm","traffic_proxy","priority_score"]].dtypes)


    # 5) Risk bands
    streets_m["priority_band"] = pd.qcut(
        streets_m["priority_score"],
        q=5,
        labels=["Very Low", "Low", "Medium", "High", "Very High"]
    )

    # Save processed GeoJSON (back to EPSG:4326 for web maps)
    streets_out = streets_m.to_crs("EPSG:4326")
    streets_out.to_file(PROCESSED / "streets_priority.geojson", driver="GeoJSON")

    # Save top list
    top = streets_out.sort_values("priority_score", ascending=False).head(50)
    cols = [
        "objectid", "streets_id", "label", "road_class", "speed",
        "segment_length_m", "addr_count", "priority_score", "priority_band"
    ]
    top[cols].to_csv(OUTPUTS / "top_50_priority_segments.csv", index=False)

    print("Saved:")
    print(" - data/processed/streets_priority.geojson")
    print(" - outputs/top_50_priority_segments.csv")

if __name__ == "__main__":
    main()