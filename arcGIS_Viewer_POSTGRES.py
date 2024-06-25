import folium, logging, sys, threading
import psycopg2
import psycopg2.extras
from psycopg2 import pool
from flask import Flask, send_file, request
from io import BytesIO
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtWebEngineWidgets import *
from xyzservices import TileProvider
from functools import lru_cache

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Database connection parameters
DB_PARAMS = {
    "host": "localhost",
    "database": "xxxxxxxxxx",
    "user": "xxxxxxxxxx",
    "password": "xxxxxxxxx"
}

# Initialize connection pool
conn_pool = pool.ThreadedConnectionPool(1, 20, **DB_PARAMS)

class CustomTileProvider(TileProvider):
    def __init__(self, name, attribution, url_template):
        super().__init__({
            "name": name,
            "url": url_template,
            "attribution": attribution
        })

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.browser = QWebEngineView()
        self.setCentralWidget(self.browser)
        self.showMaximized()
        self.load_map()

    def load_map(self):
        m = folium.Map(location=[50.0000, -5.0000], zoom_start=6, tiles=None)

        zoom_levels = self.get_zoom_levels()

        for zoom in zoom_levels:
            tile_provider = CustomTileProvider(
                name=f'xxxxxxxxxxxxx - Zoom {zoom}',
                attribution="xxxxxxxxxxxxxxxxxxxxxxxxx",
                url_template=f"http://localhost:5000/get_tile/{{z}}/{{x}}/{{y}}?zoom={zoom}"
            )
            folium.TileLayer(
                tiles=tile_provider.url,
                attr=tile_provider.attribution,
                name=tile_provider.name,
                overlay=True,
                control=True
            ).add_to(m)

        # Add a LayerControl to toggle between zoom levels
        folium.LayerControl().add_to(m)

        html = m.get_root().render()
        self.browser.setHtml(html)

    @lru_cache(maxsize=1)
    def get_zoom_levels(self):
        zoom_levels = []
        conn = conn_pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("SELECT DISTINCT z FROM images ORDER BY z")
                zoom_levels = [row[0] for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching zoom levels: {e}")
        finally:
            conn_pool.putconn(conn)
        return zoom_levels

@app.route('/get_tile/<int:z>/<int:x>/<int:y>')
def get_tile(z, x, y):
    image_data = get_image_from_db(z, x, y)
    if image_data:
        return send_file(BytesIO(image_data), mimetype='image/png')
    else:
        return '', 404

@lru_cache(maxsize=1000)
def get_image_from_db(z, x, y):
    image_data = None
    conn = conn_pool.getconn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT image FROM images WHERE z = %s AND x = %s AND y = %s", (z, x, y))
            result = cur.fetchone()
            if result:
                image_data = result[0]
    except Exception as e:
        logger.error(f"Error fetching image from database: {e}")
    finally:
        conn_pool.putconn(conn)

    return image_data

def run_flask():
    app.run(port=5000, threaded=True)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    qt_app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(qt_app.exec())
