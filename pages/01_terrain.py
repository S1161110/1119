import solara
import leafmap.maplibregl as leafmap
import os

MAPTILER_KEY = os.environ.get("MAPTILER_API_KEY", "") 

def create_3d_map():
    # 如果沒有 Key，用簡單 2D 地圖
    if not MAPTILER_KEY:
        m = leafmap.Map(
            center=[121.353, 23.646],  # 馬太鞍溪堰塞湖
            zoom=14,
            style="OpenStreetMap",
        )
        m.layout.height = "800px"
        return m
    
    # MapTiler Outdoor-v2 Style 內建支援地形資料
    style_url = f"https://api.maptiler.com/maps/outdoor-v2/style.json?key={MAPTILER_KEY}"
    
    m = leafmap.Map(
        style=style_url,
        center=[121.353, 23.646],  # 馬太鞍溪堰塞湖
        zoom=14,
        pitch=70,   # 傾斜角度
        bearing=0,  # 視角旋轉角度
    )
    m.layout.height = "800px"
    return m

@solara.component
def Page():
    if not MAPTILER_KEY:
        solara.Warning(
            "MapTiler API Key 未設定。請在 Hugging Face Space Settings 中加入 'MAPTILER_API_KEY' Secret，否則 3D 地形無法載入。"
        )
    
    solara.Markdown("## 馬太鞍溪堰塞湖 3D 地形展示")
    
    map_object = solara.use_memo(create_3d_map, dependencies=[MAPTILER_KEY])
    return map_object.to_solara()
