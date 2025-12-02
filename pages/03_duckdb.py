import solara
import duckdb
import pandas as pd
import folium
from folium import CircleMarker
from branca.element import Figure

# -----------------------------
# 1. 資料來源 & 狀態管理
# -----------------------------
CITIES_CSV_URL = 'https://data.gishub.org/duckdb/cities.csv'

all_countries = solara.reactive([])
selected_country = solara.reactive("")
min_population = solara.reactive(0)
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
        if not df_result.empty:
            min_population.set(int(df_result['population'].min()))
        con.close()
    except Exception as e:
        print(f"Error executing query: {e}")
        data_df.set(pd.DataFrame())

# -----------------------------
# 3. Folium 地圖 component
# -----------------------------
@solara.component
def CityMap(df: pd.DataFrame, min_pop: int):
    if df.empty:
        return solara.Info("沒有城市數據可顯示")

    df_filtered = df[df['population'] >= min_pop]
    if df_filtered.empty:
        return solara.Info("沒有符合篩選的人口城市")

    center = [df_filtered['latitude'].iloc[0], df_filtered['longitude'].iloc[0]]
    fig = Figure(width=800, height=500)
    m = folium.Map(location=center, zoom_start=3, tiles="CartoDB positron")
    fig.add_child(m)

    # 國家邊界
    folium.GeoJson(
        "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson",
        name="Countries",
        style_function=lambda x: {"color": "black", "weight": 1, "fillOpacity": 0}
    ).add_to(m)

    # 城市點
    for _, row in df_filtered.iterrows():
        CircleMarker(
            location=[row.latitude, row.longitude],
            radius=5,
            popup=f"{row.name} ({row.population})",
            color="red",
            fill=True,
            fill_opacity=0.7
        ).add_to(m)

    return solara.HTML(fig._repr_html_())

# -----------------------------
# 4. 主頁面 Page
# -----------------------------
@solara.component
def Page():
    solara.Title("城市地圖篩選 (Folium 平面版)")

    solara.use_effect(load_country_list, dependencies=[])
    solara.use_effect(load_filtered_data, dependencies=[selected_country.value])

    with solara.Card(title="城市篩選器"):
        solara.Select(
            label="選擇國家",
            value=selected_country,
            values=all_countries.value
        )
        # 使用 solara.Slider
        solara.Slider(
            label="最低人口",
            value=min_population,
            min=0,
            max=10000000,
            step=10000
        )

    if selected_country.value and not data_df.value.empty:
        CityMap(data_df.value, min_population.value)
    else:
        solara.Info("正在載入資料...")

Page()
