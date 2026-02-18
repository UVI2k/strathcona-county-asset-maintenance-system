from pathlib import Path
import geopandas as gpd
import pandas as pd

RAW = Path("data/raw")

STREET_PATH = RAW / "Street_Network.geojson"
ADDRESS_PATH = RAW / "Civic_Address.geojson"

def read_layer(path: Path) -> gpd.GeoDataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}. Put it in data/raw/ with this exact name.")
    try:
        return gpd.read_file(path)
    except Exception as e:
        msg = (
            f"\nFailed to read {path.name} with geopandas.read_file.\n"
            f"Error: {type(e).__name__}: {e}\n\n"
            "Fix (recommended for Codespaces):\n"
            "  pip install -U geopandas shapely pyogrio\n"
            "Then retry.\n"
        )
        raise RuntimeError(msg)

def quick_profile(gdf: gpd.GeoDataFrame, name: str) -> None:
    print(f"\n=== {name} ===")
    print("Rows:", len(gdf))
    print("CRS:", gdf.crs)
    print("Geometry types:", list(pd.Series(gdf.geom_type).value_counts().head(5).index))
    print("Columns (first 30):", list(gdf.columns)[:30])
    # show a few likely useful columns if present
    candidates = [c for c in gdf.columns if any(k in c.lower() for k in ["class", "type", "speed", "surface", "name", "length", "id"])]
    print("Likely useful fields:", candidates[:20])

def main():
    streets = read_layer(STREET_PATH)
    addresses= read_layer(ADDRESS_PATH)

    #Ensuring both layers share a CRS for future joins
    if streets.crs and addresses.crs and streets.crs != addresses.crs:
        addresses = addresses.to_crs(streets.crs)

    quick_profile(streets, "Street Network")
    quick_profile(addresses, "Civic Address")

if __name__ == "__main__":
    main()