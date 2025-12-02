import solara
import duckdb
import pandas as pd
import leafmap.maplibregl as leafmap

# -----------------------------
# 1. 資料來源 & 狀態管理
# -----------------------------
CITIES_CSV_URL = 'https://data.gishub.org/duckdb/cities.csv'

all_countries = solara.reactive([])
selected_country = solara.reactive("")
data_df = solara.reactive(pd.DataFrame())

# -----------------------------
# 2. 資料載入函數
# -----------------------------
def load_country_list():
    try:
        con = duckdb.connect()
        con.install_extension("httpfs")
        con.load_extension("httpfs")
        result = con.sql(f"""
            SELECT DISTINCT country
            FROM '{CITIES_CSV_URL}'
            ORDER BY country
        """).fetchall()
        country_list = [row[0] for row in result]
        all_countries.set(country_list)
        if "USA" in country_list:
            selected_country.set("USA")
        elif country_list:
            selected_country.set(country_list[0])
        con.close()
    except Exception as e:
        print(f"Error loading countries: {e}")

def load_filtered_data():
    country_name = selected_country.value
    if not country_name:
        return
    try:
        con = duckdb.connect()
        con.install_extension("httpfs")
        con.load_extension("httpfs")
        df_result = con.sql(f"""
            SELECT name, country, population, latitude, longitude
            FROM '{CITIES_CSV_URL}'
            WHERE country = '{country_name}'
            ORDER BY population DESC
            LIMIT 100
        """).df()
        data_df.set(df_result)
        con.close()
    except Exception as e:
        print(f"Error executing query: {e}")
        data_df.set(pd.DataFrame())

# -----------------------------
# 3. Leafmap 地圖 component
# -----------------------------
@solara.component
def CityMap(df: pd.DataFrame):
    if df.empty:
        return solara.Info("沒有城市數據可顯示")
    
    # 地圖中心設為世界中心，zoom 調整讓整個世界一次顯示
    m = leafmap.Map(
        center=[0, 0],
        zoom=1.5,
        add_sidebar=True,
        height="600px"
    )
    
    # 簡單平面底圖
    m.add_basemap("Carto Light", before_id=m.first_symbol_layer_id)
    
    # 加國家邊界（全世界一次）
    m.add_geojson(
        "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson",
        name="Countries",
        layer_type="line",
        paint={"line-color": "#000000", "line-width": 1},
    )
    
    # 加城市點
    features = []
    for _, row in df.iterrows():
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [row["longitude"], row["latitude"]]},
            "properties": {"name": row["name"], "population": int(row["population"]) if row["population"] else None}
        })
    geojson = {"type": "FeatureCollection", "features": features}
    m.add_geojson(geojson, name="Cities")
    
    return m.to_solara()

# -----------------------------
# 4. 主頁面 Page
# -----------------------------
@solara.component
def Page():
    solara.Title("城市地圖篩選 (全世界平面一次顯示)")

    solara.use_effect(load_country_list, dependencies=[])
    solara.use_effect(load_filtered_data, dependencies=[selected_country.value])

    with solara.Card(title="城市篩選器"):
        solara.Select(
            label="選擇國家",
            value=selected_country,
            values=all_countries.value
        )

    if selected_country.value and not data_df.value.empty:
        CityMap(data_df.value)
    else:
        solara.Info("正在載入資料...")

# -----------------------------
# 5. 啟動 Page
# -----------------------------
Page()
