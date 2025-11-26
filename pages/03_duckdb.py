import duckdb
import pandas as pd
import leafmap.maplibregl as leafmap

# 建立一個記憶體內連線 (In-memory connection)
con = duckdb.connect()

# 安裝和載入 httpfs (用於遠端檔案存取，如 S3)
con.install_extension("httpfs")
con.load_extension("httpfs")

# 安裝和載入 spatial (用於空間資料處理)
con.install_extension("spatial")
con.load_extension("spatial")

# 問題一：預覽城市資料表的前 5 筆紀錄，只看城市名稱、國家代碼與人口
con.sql("""
SELECT name, country, population
FROM 'https://data.gishub.org/duckdb/cities.csv'
LIMIT 5;
""").show()

