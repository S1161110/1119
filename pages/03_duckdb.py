import duckdb
import solara
import ipywidgets as widgets
import leafmap.maplibregl as leafmap


def create_map():

    # --- 建立世界地圖 ---
    m = leafmap.Map(
        add_sidebar=True,
        sidebar_visible=True,
        height="800px",
        zoom=2,
        center=[20, 0],
    )

    # 世界國界
    m.add_geojson(
        data="https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson",
        name="World Countries",
        layer_type="line",
        paint={
            "line-color": "rgba(0,0,0,0.5)",
            "line-width": 1,
        },
    )

    # --- DuckDB 載入城市資料 ---
    con = duckdb.connect()
    con.install_extension("httpfs")
    con.load_extension("httpfs")

    url = "https://data.gishub.org/duckdb/cities.csv"

    con.sql(f"""
        CREATE TABLE IF NOT EXISTS Cities AS 
        SELECT * FROM read_csv('{url}');
    """)

    minpop, maxpop = con.sql(
        "SELECT MIN(population), MAX(population) FROM Cities"
    ).fetchone()

    # --- UI ---
    pop_slider = widgets.IntSlider(
        description="人口大於：",
        min=int(minpop),
        max=int(maxpop),
        step=10000,
        value=500000,
        continuous_update=False,
        style={"description_width": "initial"},
    )

    # --- DataFrame -> GeoJSON ---
    def df_to_geojson(df):
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [row["longitude"], row["latitude"]],
                    },
                    "properties": {
                        "name": row["name"],
                        "country": row["country"],
                        "population": row["population"],
                    },
                }
                for _, row in df.iterrows()
            ],
        }

    # --- 更新城市點 layer ---
    def update_city_layer(change=None):
        if "Cities Layer" in m.layer_dict:
            m.remove_layer("Cities Layer")

        df = con.sql(f"""
            SELECT name, country, population, latitude, longitude
            FROM Cities
            WHERE population >= {pop_slider.value};
        """).df()

        geojson_data = df_to_geojson(df)

        m.add_geojson(
            data=geojson_data,
            name="Cities Layer",
            layer_type="circle",
            paint={
                "circle-radius": 4,
                "circle-color": "#ff0000",
            },
            popup=["name", "country", "population"],
        )

    update_city_layer()
    pop_slider.observe(update_city_layer, names="value")

    m.add_to_sidebar(pop_slider, label="人口篩選")

    return m


@solara.component
def Page():
    m = create_map()
    return m.to_solara()
