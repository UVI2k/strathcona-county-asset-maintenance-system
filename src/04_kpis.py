from pathlib import Path
import geopandas as gpd
import pandas as pd

INFILE = Path("data/processed/streets_priority.geojson")
OUT_MD = Path("outputs/kpi_summary.md")

def main():
    gdf = gpd.read_file(INFILE)

    total = len(gdf)
    high = gdf["priority_band"].isin(["High", "Very High"]).sum()
    vhigh = (gdf["priority_band"] == "Very High").sum()

    by_class = (
        gdf.groupby("road_class", dropna=False)["priority_score"]
        .agg(["count", "mean", "max"])
        .sort_values("mean", ascending=False)
        .head(10)
        .reset_index()
    )

    top5 = (
        gdf.sort_values("priority_score", ascending=False)
        .loc[:, ["label", "road_class", "speed", "addr_count", "segment_length_m", "priority_score", "priority_band"]]
        .head(5)
    )

    md = []
    md.append("# KPI Summary\n")
    md.append(f"- Total road segments analyzed: **{total:,}**\n")
    md.append(f"- High + Very High priority segments: **{high:,}** ({high/total:.1%})\n")
    md.append(f"- Very High priority segments: **{vhigh:,}** ({vhigh/total:.1%})\n")
    md.append(f"- Average priority score: **{gdf['priority_score'].mean():.2f}**\n")
    md.append(f"- Max priority score: **{gdf['priority_score'].max():.2f}**\n\n")

    md.append("## Top 5 Priority Segments\n")
    md.append(top5.to_markdown(index=False))
    md.append("\n\n## Top Road Classes by Average Priority Score (Top 10)\n")
    md.append(by_class.to_markdown(index=False))

    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print(f" Wrote: {OUT_MD}")

if __name__ == "__main__":
    main()
