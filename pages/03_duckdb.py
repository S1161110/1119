import duckdb
import pandas as pd
import leafmap.maplibregl as leafmap
import json

def create_map():

    # DuckDB 讀取遠端資料
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

    # 建地圖
    m = leafmap.Map(
        center=[25.03, 121.56],  # 台北
        zoom=2,
        height="750px",
        style="https://demotiles.maplibre.org/style.json"
    )

    # 加 GeoJSON 到 MapLibre
    geojson_str = json.dumps(geojson_data)
    m.add_geojson(geojson_str, layer_name="cities")

    return m
