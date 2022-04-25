#!/usr/bin/env python
"""Utilities to download observation images for image quality assessment"""
# TODO: Persist list of downloaded images, and don't re-download invalid/0KB images
import asyncio
import re
from datetime import datetime
from logging import getLogger
from os import listdir, makedirs
from os.path import basename, join

import aiofiles
import aiohttp
from rich.progress import Console, Progress, track

from inat_backlog_slogger.constants import IMAGE_DIR, THROTTLING_DELAY
from inat_backlog_slogger.observations import load_observations

PHOTO_ID_PATTERN = re.compile(r'.*photos/(.*)/.*\.(\w+)')
logger = getLogger(__name__)


async def download_images(urls, throttle=True):
    download_info = check_downloaded_images(urls)

    with Progress() as progress:
        # Set up progress bar
        task = progress.add_task("[cyan]Downloading...", total=len(urls))
        progress.update(task, advance=len(urls) - len(download_info))

        start_time = datetime.now()
        async with aiohttp.ClientSession() as session:
            download_tasks = [
                download_image(session, url, file_path, progress, task)
                for url, file_path in download_info.items()
            ]
            if throttle:
                for download_task in download_tasks:
                    await download_task
                    await asyncio.sleep(THROTTLING_DELAY)
            else:
                await asyncio.gather(*download_tasks)

    logger.info(f'Downloaded {len(urls)} images in {datetime.now() - start_time}s')


def check_downloaded_images(urls):
    """Get local file paths for URLs, and skip images that we've already downloaded"""
    makedirs(IMAGE_DIR, exist_ok=True)
    console = Console()
    console.print('Checking for completed downloads')
    to_download = {url: get_image_path(url) for url in urls}
    downloaded_images = listdir(IMAGE_DIR)

    to_download = {
        url: path
        for url, path in track(list(to_download.items()))
        if basename(path) not in downloaded_images
    }
    console.print(
        f'{len(urls) - len(to_download)} images already downloaded, ',
        f'{len(to_download)} remaining',
    )
    return to_download


async def download_image(
    session: aiohttp.ClientSession, url: str, file_path: str, progress: Progress, task
):
    try:
        async with session.get(url) as response:
            assert response.status == 200
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(await response.read())
        progress.console.print(f'Downloaded {url} to {file_path}')
    except Exception as e:
        progress.console.print(f'Download for {url} failed: {str(e)}')

    progress.update(task, advance=1)


def get_original_image_urls(df):
    logger.info('Getting image URLs')
    urls = [get_image_url(url, 'original') for url in df['photo.url'].unique()]
    return sorted(filter(None, urls))


def get_image_url(image_url, target_size='original'):
    """Given an image URL (of any size), return the URL for the specified size"""
    if not str(image_url).startswith('http'):
        return None
    for size in ('square', 'small', 'medium', 'large', 'original'):
        image_url = image_url.replace(size, target_size)
    return image_url


def get_image_path(image_url):
    """Determine the local image filename based on its URL"""
    match = re.match(PHOTO_ID_PATTERN, image_url)
    # If for some reason the URL is in an unexpected format, just use the URL resource path
    if match:
        filename = f'{match.group(1)}.{match.group(2)}'
    else:
        filename = image_url.rsplit('/', 1)[1]
    return join(IMAGE_DIR, filename)


def get_photo_id(image_url):
    """Get a photo ID from its URL (for CSV exports, which only include a URL)"""
    match = re.match(PHOTO_ID_PATTERN, str(image_url))
    return match.group(1) if match else ''


# Download images for an existing observation export
if __name__ == '__main__':
    df = load_observations()
    image_urls = get_original_image_urls(df)
    asyncio.run(download_images(image_urls))
