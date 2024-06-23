import os
import aiohttp
import asyncio
from tqdm import tqdm
from aiohttp import ClientSession

CONFIG_URL = "https://tiles-xxx.arcgis.com/xxxxxxxxxxxxxx/arcgis/rest/services/xxxxxxxxxxxxxx/MapServer?f=pjson" # Replace with your URL
SAVE_DIR = "tiles"
MAX_WORKERS = 20  # Number of concurrent workers

async def fetch_config(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.json()

def get_tile_ranges(tile_info, full_extent):
    lods = tile_info['lods']
    origin_x, origin_y = tile_info['origin']['x'], tile_info['origin']['y']
    tile_size = tile_info['cols']
    xmin, ymin, xmax, ymax = full_extent['xmin'], full_extent['ymin'], full_extent['xmax'], full_extent['ymax']
    
    def calc_range(level):
        lod = next(l for l in lods if l['level'] == level)
        res = lod['resolution']
        min_x = int((xmin - origin_x) / (res * tile_size))
        max_x = int((xmax - origin_x) / (res * tile_size))
        min_y = int((origin_y - ymax) / (res * tile_size))
        max_y = int((origin_y - ymin) / (res * tile_size))
        return range(min_x, max_x + 1), range(min_y, max_y + 1)
    
    return [(lod['level'], *calc_range(lod['level'])) for lod in lods]

async def download_tile(session, z, x, y, save_dir, pbar):
    tile_url = f"https://tiles-xxx.arcgis.com/xxxxxxxxxxxxxx/arcgis/rest/services/xxxxxxxxxxxxxx/MapServer/tile/{z}/{y}/{x}" # Replace with your URL
    async with session.get(tile_url) as response:
        if response.status == 200:
            zoom_dir = os.path.join(save_dir, str(z))
            os.makedirs(zoom_dir, exist_ok=True)
            tile_path = os.path.join(zoom_dir, f"{x}_{y}.png")
            with open(tile_path, 'wb') as tile_file:
                tile_file.write(await response.read())
    
    pbar.update(1)

async def main():
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)
    
    config = await fetch_config(CONFIG_URL)
    tile_info, full_extent = config['tileInfo'], config['fullExtent']
    tile_ranges = get_tile_ranges(tile_info, full_extent)
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
                    tasks.append(download_tile(session, z, x, y, SAVE_DIR, pbar))
        if tasks:
            await asyncio.gather(*tasks)
    pbar.close()

if __name__ == "__main__":
    asyncio.run(main())