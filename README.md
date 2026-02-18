# Strathcona County Asset Maintenance System (GIS)

Enterprise-style GIS decision-support project that prioritizes road maintenance using spatial analytics and automated workflows.

## Business Problem
Municipal teams must prioritize road maintenance under limited budgets. This project demonstrates a repeatable GIS workflow to rank road segments by a **Maintenance Priority Score** using spatial proxies for usage and operational importance.

## Data Sources
- Strathcona County Open Data:
  - Street Network (road centerlines)
  - Civic Address points  
*(Downloaded as GeoJSON from the Strathcona County Open Data Hub.)*

## What This Delivers
- Processed GIS dataset with priority scoring: `data/processed/streets_priority.geojson`
- Ranked export (top 50 segments): `outputs/top_50_priority_segments.csv`
- Interactive web map with layer toggles: `outputs/priority_map.html`

## Methodology
### 1) Spatial ETL + Data Modeling
- Loaded and profiled GIS layers (CRS, geometry types, key attributes)
- Reprojected from **EPSG:4326 → EPSG:3400** for accurate buffering and distance/length calculations (meters)

### 2) Usage Proxy via Address Density
When direct traffic counts are unavailable, we approximate usage/exposure by counting nearby civic addresses:
- Created a buffer around each road segment (meters)
- Spatially joined address points to buffered road segments
- `addr_count` = number of address points near each road segment

### 3) Maintenance Priority Score (0–100)
Features are normalized (min-max) then combined with weights:

- **Traffic Proxy** = 0.7 × Address Density + 0.3 × Speed
- **Priority Score** =  
  `0.50 × Traffic Proxy + 0.30 × Road Class Weight + 0.20 × Segment Length`

Outputs include both continuous `priority_score` and categorical `priority_band` (Very Low → Very High).

## Results
- See: `outputs/top_50_priority_segments.csv`
- See interactive map: https://<UVI2K>.github.io/<strathcona-county-asset-maintenance-system>/  
  Layers:
  - All Roads
  - High Priority (High + Very High)
  - Very High Priority Only


- Total road segments analyzed: **7,608**

- High + Very High priority segments: **3,043** (40.0%)

- Very High priority segments: **1,517** (19.9%)

- Average priority score: **18.70**

- Max priority score: **65.00**


## Top 5 Priority Segments

| label         | road_class   |   speed |   addr_count |   segment_length_m |   priority_score | priority_band   |
|:--------------|:-------------|--------:|-------------:|-------------------:|-----------------:|:----------------|
| HWY 16 (EAST) | Hwy-Primary  |     110 |            0 |           7412.74  |            65    | Very High       |
| HWY 16 (WEST) | Hwy-Primary  |     110 |            0 |           7406.54  |            64.98 | Very High       |
| HWY 16 (WEST) | Hwy-Primary  |     110 |            0 |           5800.38  |            60.65 | Very High       |
| HWY 16 (EAST) | Hwy-Primary  |     110 |            0 |           5794.68  |            60.63 | Very High       |
| LANE          | Lane         |      30 |           92 |            306.196 |            58.42 | Very High       |


## Top Road Classes by Average Priority Score (Top 10)

| road_class    |   count |     mean |   max |
|:--------------|--------:|---------:|------:|
| Hwy-Primary   |     382 | 45.3768  | 65    |
| Hwy-Secondary |     188 | 42.9987  | 48.96 |
| Lane          |     133 | 38.3795  | 58.42 |
| Service Road  |     184 | 38.3371  | 46.51 |
| Arterial      |     739 | 32.1743  | 37.77 |
| Collector     |    1624 | 23.7321  | 52.64 |
| Ramp          |     221 | 18.3653  | 24.59 |
| Local         |    4137 |  9.26548 | 42.43 |
## Project Structure
```text
strathcona-county-asset-maintenance-system/
├── data/
│   ├── raw/                # input GeoJSON files
│   └── processed/          # scored output GeoJSON
├── src/
│   ├── 01_load_and_profile.py
│   ├── 02_priority_score.py
│   ├── 03_generate_map.py
│   └── 04_kpis.py
├── outputs/
│   ├── top_50_priority_segments.csv
│   ├── priority_map.html
│   └── kpi_summary.md
├── requirements.txt
└── README.md
'''

# 1) Create venv + install deps
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2) Generate scored dataset + exports
python src/02_priority_score.py

# 3) Generate interactive map
python src/03_generate_map.py

# 4) Generate KPI summary for README
python src/04_kpis.py
