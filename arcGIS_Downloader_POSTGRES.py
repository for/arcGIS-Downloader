import os
import aiohttp
import asyncio
from tqdm import tqdm
from aiohttp import ClientSession
import psycopg2
import psycopg2.extras

CONFIG_URL = "https://tiles-eu1.arcgis.com/xxxxxxxxx/arcgis/rest/services/xxxxxxxxx/MapServer?f=pjson"
MAX_WORKERS = 150  # 150 is a lot, change this if needed.

# Define the region of interest (xmin, ymin, xmax, ymax)
REGION_OF_INTEREST = {
    "xmin": -xxxxxxxxx.xxxxxxxxx,
    "ymin": xxxxxxxxx.xxxxxxxxx,
    "xmax": -xxxxxxxxx.xxxxxxxxx,
    "ymax": xxxxxxxxx.xxxxxxxxx
}

async def fetch_config(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.json()

def get_tile_ranges(tile_info, full_extent, region, min_zoom, max_zoom):
    lods = tile_info['lods']
    origin_x, origin_y = tile_info['origin']['x'], tile_info['origin']['y']
    tile_size = tile_info['cols']
    xmin, ymin, xmax, ymax = region['xmin'], region['ymin'], region['xmax'], region['ymax']
    
    def calc_range(level):
        lod = next(l for l in lods if l['level'] == level)
        res = lod['resolution']
        min_x = int((xmin - origin_x) / (res * tile_size))
        max_x = int((xmax - origin_x) / (res * tile_size))
        min_y = int((origin_y - ymax) / (res * tile_size))
        max_y = int((origin_y - ymin) / (res * tile_size))
        return range(min_x, max_x + 1), range(min_y, max_y + 1)
    
    return [(lod['level'], *calc_range(lod['level'])) for lod in lods if min_zoom <= lod['level'] <= max_zoom]

""" async def download_tile(session, z, x, y, conn, pbar):
    tile_url = f"https://tiles-eu1.arcgis.com/xxxxxxxxx/arcgis/rest/services/xxxxxxxxx/MapServer/tile/{z}/{y}/{x}"
    async with session.get(tile_url) as response:
        if response.status == 200:
            image_data = await response.read()
            cur = conn.cursor()
            cur.execute("INSERT INTO images (z, x, y, image) VALUES (%s, %s, %s, %s) RETURNING id",
                        (z, x, y, psycopg2.Binary(image_data)))
            image_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
    
    pbar.update(1) """

async def download_tile(session, z, x, y, conn, pbar):
    tile_url = f"https://tiles-eu1.arcgis.com/xxxxxxxxx/arcgis/rest/services/xxxxxxxxx/MapServer/tile/{z}/{y}/{x}"
    async with session.get(tile_url) as response:
        if response.status == 200:
            image_data = await response.read()
            if len(image_data) > 190:  # Check if the file size is greater than 190 bytes
                cur = conn.cursor()
                cur.execute("INSERT INTO images (z, x, y, image) VALUES (%s, %s, %s, %s) RETURNING id",
                            (z, x, y, psycopg2.Binary(image_data)))
                image_id = cur.fetchone()[0]
                conn.commit()
                cur.close()
            else:
                print(f"Skipping tile at z={z}, x={x}, y={y} (size: {len(image_data)} bytes)")
    
    pbar.update(1)

async def main():
    conn = psycopg2.connect(
        host="localhost",
        database="xxxxxxxxx",
        user="xxxxxxxxx",
        password="xxxxxxxxx"
    )
    
    config = await fetch_config(CONFIG_URL)
    tile_info, full_extent = config['tileInfo'], config['fullExtent']
    tile_ranges = get_tile_ranges(tile_info, full_extent, REGION_OF_INTEREST, min_zoom=0, max_zoom=20)
    total_tiles = sum(len(x_range) * len(y_range) for _, x_range, y_range in tile_ranges)
    
    pbar = tqdm(total=total_tiles, desc="Downloading tiles")
    async with ClientSession() as session:
        tasks = []
        for z, x_range, y_range in tile_ranges:
            for x in x_range:
                for y in y_range:
                    if len(tasks) >= MAX_WORKERS:
                        await asyncio.gather(*tasks)
                        tasks = []
                    tasks.append(download_tile(session, z, x, y, conn, pbar))
        if tasks:
            await asyncio.gather(*tasks)
    pbar.close()
    conn.close()

if __name__ == "__main__":
    asyncio.run(main())
