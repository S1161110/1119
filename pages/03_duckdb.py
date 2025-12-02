import solara
import duckdb
import pandas as pd
import plotly.express as px
import leafmap.maplibregl as leafmap

# -----------------------------
# 1. 全域狀態管理
# -----------------------------
CITIES_CSV_URL = 'https://data.gishub.org/duckdb/cities.csv'

all_countries = solara.reactive([])
selected_country = solara.reactive("")
population_threshold = solara.reactive(1_000_000)   # 新增：人口門檻

data_df = solara.reactive(pd.DataFrame())

# -----------------------------
# 2. 載入國家清單
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

        # 預設選 USA 或第一個
        if "USA" in country_list:
            selected_country.set("USA")
        elif country_list:
            selected_country.set(country_list[0])

        con.close()
    except Exception as e:
        print("Error loading countries:", e)

# -----------------------------
# 3. 載入該國家 + 人口門檻的城市
# -----------------------------
def load_filtered_data():
    country_name = selected_country.value
    threshold = population_threshold.value

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
              AND population >= {threshold}
            ORDER BY population DESC
        """).df()

        data_df.set(df_result)
        con.close()

    except Exception as e:
        print("Error loading filtered cities:", e)
        data_df.set(pd.DataFrame())

# -----------------------------
# 4. Leafmap 地圖元件
# -----------------------------
@solara.component
def CityMap(df: pd.DataFrame):
    if df.empty:
        return solara.Info("沒有符合人口門檻的城市")

    # 地圖中心點設為人口最大的城市
    center = [df['latitude'].iloc[0], df['longitude'].iloc[0]]

    m = leafmap.Map(
        center=center,
        zoom=4,
        add_sidebar=True,
        height="600px"
    )
    m.add_basemap("Esri.WorldImagery", before_id=m.first_symbol_layer_id)

    # 轉成 GeoJSON
    features = []
    for _, row in df.iterrows():
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [row["longitude"], row["latitude"]]
            },
            "properties": {
                "name": row["name"],
                "population": int(row["population"])
            }
        })

    geojson = {"type": "FeatureCollection", "features": features}
    m.add_geojson(geojson)

    return m.to_solara()

# -----------------------------
# 5. Solara 主頁面
# -----------------------------
@solara.component
def Page():

    solara.Title("🌍 城市人口濃度互動地圖 (DuckDB + Solara + Leafmap)")

    # 初始化：載入國家清單
    solara.use_effect(load_country_list, dependencies=[])

    # 當國家 或 人口門檻 有改變 → 重新查詢 DuckDB
    solara.use_effect(
        load_filtered_data,
        dependencies=[selected_country.value, population_threshold.value]
    )

    with solara.Card(title="城市篩選器"):
        solara.Select(
            label="選擇國家",
            value=selected_country,
            values=all_countries.value
        )

        # --------------------
        # ⭐ 新增：人口門檻 slider
        # --------------------
        solara.SliderInt(
            label="人口下限",
            value=population_threshold,
            min=0,
            max=20_000_000,
            step=100_000
        )
        solara.Markdown(f"目前人口門檻：**{population_threshold.value:,}**")

    df = data_df.value

    if selected_country.value and not df.empty:

        solara.Markdown(f"## {selected_country.value}（人口 ≥ {population_threshold.value:,}）")

        # 地圖元件
        CityMap(df)

        # 表格
        solara.Markdown("### 📋 數據表格")
        solara.DataFrame(df)

        # --------------------
        # Plotly 視覺化
        # --------------------
        solara.Markdown("### 📊 城市人口分布（Bar Chart）")
        fig_hist = px.bar(
            df,
            x="name",
            y="population",
            color="population",
            title=f"{selected_country.value} 城市人口分布",
            labels={"name": "城市名稱", "population": "人口"},
            height=400
        )
        fig_hist.update_layout(xaxis_tickangle=-45)
        solara.FigurePlotly(fig_hist)

        solara.Markdown("### 🥧 城市人口比例（Pie Chart）")
        fig_pie = px.pie(
            df,
            names="name",
            values="population",
            title=f"{selected_country.value} 城市人口比例",
            height=400
        )
        solara.FigurePlotly(fig_pie)

    else:
        solara.Info("沒有符合條件的城市 / 正在載入中...")

# -----------------------------
# 6. 啟動 App
# -----------------------------
Page()
