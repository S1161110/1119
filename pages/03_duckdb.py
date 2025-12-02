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
    """初始化：載入國家清單"""
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
    """根據選中國家載入城市資料"""
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
    """顯示簡單城市地圖 (不同人口區間顯示不同顏色)"""
    if df.empty:
        return solara.Info("沒有城市數據可顯示")
    
    # 以第一個城市中心作為地圖中心
    center = [df['latitude'].iloc[0], df['longitude'].iloc[0]]
    m = leafmap.Map(
        center=center,
        zoom=3,
        add_sidebar=True,
        height="600px"
    )
    
    # 簡單平面底圖
    m.add_basemap("Carto Light", before_id=m.first_symbol_layer_id)
    
    # 加國家邊界
    m.add_geojson(
        "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson",
        name="Countries",
        layer_type="line",
        paint={"line-color": "#000000", "line-width": 1},
    )
    
    # 城市點按人口分段顏色
    def get_color(pop):
        if pop < 100_000:
            return "#1f77b4"  # 藍
        elif pop < 500_000:
            return "#ff7f0e"  # 橘
        elif pop < 1_000_000:
            return "#2ca02c"  # 綠
        else:
            return "#d62728"  # 紅

    features = []
    for _, row in df.iterrows():
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [row["longitude"], row["latitude"]]},
            "properties": {
                "name": row["name"],
                "population": int(row["population"]) if row["population"] else None,
                "color": get_color(row["population"])
            }
        })
    geojson = {"type": "FeatureCollection", "features": features}
    
    # 使用 circle-color 屬性顯示顏色
    m.add_geojson(geojson, name="Cities", layer_type="circle", circle_color="color", circle_radius=5)
    
    return m.to_solara()

# -----------------------------
# 4. 主頁面 Page
# -----------------------------
@solara.component
def Page():
    solara.Title("城市地圖 (簡單平面 + 人口顏色區分)")

    solara.use_effect(load_country_list, dependencies=[])
    solara.use_effect(load_filtered_data, dependencies=[selected_country.value])

    with solara.Card(title="城市選擇"):
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
