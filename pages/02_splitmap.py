import solara
import leafmap.leafmap as leafmap

def create_split_map():
    split_control = leafmap.split_map(
        left_layer="Esri.WorldImagery",  # 左邊：衛星圖
        right_layer="OpenStreetMap",     # 右邊：街道圖
        left_label="衛星影像",
        right_label="街道地圖",
        center=[121.353, 23.646],        # 馬太鞍溪堰塞湖
        zoom=13,                         # 放大一點看細節
    )
    
    split_control.layout.height = "700px"  # 調整高度
    return split_control

@solara.component
def Page():
    solara.Markdown("## 馬太鞍溪 2D 捲簾比對地圖")
    
    split_widget = solara.use_memo(create_split_map, dependencies=[])
    
    with solara.Column(style={"width": "100%", "height": "750px"}):
        solara.display(split_widget)
