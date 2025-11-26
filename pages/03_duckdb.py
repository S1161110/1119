#1125改到UI，只要剩下篩選下拉框就好，其他可以刪掉（還沒改完
import json
import duckdb
import solara
import ipywidgets as widgets
import leafmap.maplibregl as leafmap
import matplotlib.pyplot as plt

def create_map():

    m = leafmap.Map(
        add_sidebar=True,
        add_floating_sidebar=False,
        sidebar_visible=True,
        layer_manager_expanded=False,
        height="800px",
    )
    m.add_basemap("Esri.WorldImagery", before_id=m.first_symbol_layer_id, visible=False)
    m.add_draw_control(controls=["polygon", "trash"])

    con = duckdb.connect()
    con.install_extension("httpfs")
    con.install_extension("spatial")
    con.install_extension("h3", repository="community")
    con.load_extension("httpfs")
    con.load_extension("spatial")
    con.load_extension("h3")

    url = "https://data.gishub.org/duckdb/cities.csv"

    con.sql(
        f"CREATE TABLE IF NOT EXISTS Cities AS SELECT * FROM read_parquet('{url}');"
    )

    colormaps = sorted(plt.colormaps())

    colormap_dropdown = widgets.Dropdown(
        options=colormaps,
        description="Colormap:",
        value="inferno",
        style={"description_width": "initial"},
    )
    class_slider = widgets.IntSlider(
        description="Class:",
        min=1,
        max=10,
        step=1,
        value=5,
        style={"description_width": "initial"},
    )
    apply_btn = widgets.Button(description="Apply")
    close_btn = widgets.Button(description="Close")
    output_widget = widgets.Output()
    output_widget.append_stdout(
        "Draw a polygon on the map. Then, \nclick on the 'Apply' button"
    )

    def on_apply_btn_click(change):
        with output_widget:
            try:
                output_widget.outputs = ()
                if len(m.draw_features_selected) > 0:
                    geojson = m.draw_features_selected[0]["geometry"]
                df = con.sql(
                    f"""
                SELECT * EXCLUDE (geometry), ST_AsText(geometry) AS geometry FROM h3_res4_geo
                WHERE ST_Intersects(geometry, ST_GeomFromGeoJSON('{json.dumps(geojson)}'));
                """
                ).df()
                gdf = leafmap.df_to_gdf(df)
                if "H3 Hexagon" in m.layer_dict:
                    m.remove_layer("H3 Hexagon")

                if outline_chk.value:
                    outline_color = "rgba(255, 255, 255, 255)"
                else:
                    outline_color = "rgba(255, 255, 255, 0)"

                if checkbox.value:
                    m.add_data(
                        gdf,
                        column="building_count",
                        scheme="JenksCaspall",
                        cmap=colormap_dropdown.value,
                        k=class_slider.value,
                        outline_color=outline_color,
                        name="H3 Hexagon",
                        before_id=m.first_symbol_layer_id,
                        extrude=True,
                        fit_bounds=False,
                        add_legend=False,
                    )
                else:
                    m.add_data(
                        gdf,
                        column="building_count",
                        scheme="JenksCaspall",
                        cmap=colormap_dropdown.value,
                        k=class_slider.value,
                        outline_color=outline_color,
                        name="H3 Hexagon",
                        before_id=m.first_symbol_layer_id,
                        fit_bounds=False,
                        add_legend=False,
                    )

                m.remove_from_sidebar(name="Legend")
                m.add_legend_to_sidebar(
                    title="Building Count",
                    legend_dict=m.legend_dict,
                )
            except Exception as e:
                with output_widget:
                    output_widget.outputs = ()
                    output_widget.append_stderr(str(e))

    def on_close_btn_click(change):
        m.remove_from_sidebar(name="H3 Hexagonal Grid")

    apply_btn.on_click(on_apply_btn_click)
    close_btn.on_click(on_close_btn_click)

    widget = widgets.VBox(
        [
            widgets.HBox([checkbox, outline_chk]),
            colormap_dropdown,
            class_slider,
            widgets.HBox([apply_btn, close_btn]),
            output_widget,
        ]
    )
    m.create_container()
    m.add_to_sidebar(
        widget, label="H3 Hexagonal Grid", widget_icon="mdi-hexagon-multiple"
    )

    return m


@solara.component
def Page():
    m = create_map()
    return m.to_solara()