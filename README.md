# ArcGIS Tile Downloader
This Python script allows you to download map tiles from an ArcGIS tile server asynchronously. It uses the `aiohttp` library for efficient concurrent downloads and `tqdm` for progress tracking.

## Features
- Asynchronous tile downloading
- Automatic calculation of tile ranges based on server configuration
- Progress bar to track download status
- Configurable number of concurrent workers

## Requirements
- Python 3.7+
- aiohttp
- tqdm

## Installation
1. Clone this repository:
git clone https://github.com/for/arcGIS-Downloader.git
cd arcGIS-Downloader

2. Install the required packages.

## Configuration
Before running the script, you need to configure the following variables in the `tile_downloader.py` file:

- `CONFIG_URL`: The URL of the ArcGIS MapServer configuration JSON.
- `SAVE_DIR`: The directory where downloaded tiles will be saved.
- `MAX_WORKERS`: The maximum number of concurrent download workers.

You also need to replace the placeholder URL in the `download_tile` function with your actual tile server URL.

## Usage
Run the script using Python:
python arcGIS_Downloader.py

The script will create the specified save directory if it doesn't exist, fetch the server configuration, calculate tile ranges, and start downloading tiles. Progress will be displayed in the console.
