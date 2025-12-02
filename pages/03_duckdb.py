import duckdb
import pandas as pd
import leafmap.maplibregl as leafmap
import json

def create_map():

    # DuckDB
    con = duckdb.connect()
    con.install_extension("httpfs")
    con.load_extension("httpfs")

    df = con.sql("""
        SELECT name, country, population, lon, lat
        FROM 'https://data.gishub.org/duckdb/cities.csv'
        LIMIT 200;
    """).df()

    # 轉 GeoJSON
    features = []
    for _, row in df.iterrows():
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [row["lon"], row["lat"]],
            },
            "properties": {
                "name": row["name"],
                "country": row["country"],
                "population": row["population"],
            },
        })

    geojson_data = {
        "type": "FeatureCollection",
        "features": features
    }

    geojson_str = json.dumps(geojson_data)

    # MapLibre 地圖（無 popup）
    m = leafmap.Map(
        center=[20, 0],
        zoom=2,
        height="750px",
        style="https://demotiles.maplibre.org/style.json"
    )

    # 加圖層（不帶 popup）
    m.add_geojson(geojson_str, layer_name="cities")

    return m
