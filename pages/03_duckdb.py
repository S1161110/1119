import duckdb
import solara
import ipywidgets as widgets
import leafmap.maplibregl as leafmap


def create_map():

    # --- 建立地圖 ---
    m = leafmap.Map(
        add_sidebar=True,
        sidebar_visible=True,
        height="800px",
        zoom=2,
        center=[20, 0],
    )

    # 加上世界國界線（leafmap 內建）
    m.add_geojson(
        data="https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson",
        name="World Countries",
        layer_type="fill",
        paint={
            "fill-color": "rgba(0,0,0,0)",
            "fill-outline-color": "rgba(0,0,0,0.6)",
        },
    )

    # --- DuckDB: 載入資料集 ---
    con = duckdb.connect()
    con.install_extension("httpfs")
    con.load_extension("httpfs")

    url = "https://data.gishub.org/duckdb/cities.csv"

    con.sql(f"""
        CREATE TABLE IF NOT EXISTS Cities AS 
        SELECT *, 
        ST_Point(longitude, latitude) AS geometry
        FROM read_csv('{url}');
    """)

    # 取得最小、最大人口（用於 Slider 範圍）
    minpop, maxpop = con.sql("SELECT MIN(population), MAX(population) FROM Cities").fetchone()

    # --- UI: 人口篩選 Slider ---
    pop_slider = widgets.IntSlider(
        description="人口大於：",
        min=int(minpop),
        max=int(maxpop),
        step=10000,
        value=500000,
        continuous_update=False,
        style={"description_width": "initial"},
    )

    # --- 城市圖層更新 ---
    def update_city_layer(change=None):
        # 移除舊圖層
        if "Cities Layer" in m.layer_dict:
            m.remove_layer("Cities Layer")

        # 查詢人口 > slider.value 的城市
        df = con.sql(f"""
            SELECT name, country, population, latitude, longitude
            FROM Cities
            WHERE population >= {pop_slider.value};
        """).df()

        # 加到地圖上（點圖層 + popup）
        m.add_points_from_xy(
            df,
            x="longitude",
            y="latitude",
            popup=["name", "country", "population"],
            name="Cities Layer",
            radius=5,
            color="#ff0000",
        )

    # 初始化一次
    update_city_layer()

    # slider 動作觸發更新
    pop_slider.observe(update_city_layer, names="value")

    # 加入側邊欄
    m.add_to_sidebar(pop_slider, label="人口篩選")

    return m



@solara.component
def Page():
    m = create_map()
    return m.to_solara()
