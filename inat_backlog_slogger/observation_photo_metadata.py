#!/usr/bin/env python3
"""Borrowed from:
https://github.com/niconoe/pyinaturalist/blob/main/examples/observation_photo_metadata.py

TODO: If this were a bit more polished it could maybe be moved to pyinaturalist-convert
"""
from pprint import pprint

import requests
from bs4 import BeautifulSoup
from pyinaturalist.node_api import get_observation
from pyinaturalist.rest_api import get_access_token

IGNORE_ATTRIBUTES = ['Associated observations', 'Sizes']
PHOTO_INFO_BASE_URL = 'https://www.inaturalist.org/photos'


def get_photo_metadata(photo_url, access_token):
    """Scrape content from a photo info URL, and attempt to get its metadata"""
    print(f'Fetching {photo_url}')
    photo_page = requests.get(photo_url, headers={'Authorization': f'Bearer {access_token}'})
    soup = BeautifulSoup(photo_page.content, 'html.parser')
    table = soup.find(id='wrapper').find_all('table')[1]

    metadata = {}
    for row in table.find_all('tr'):
        key = row.find('th').text.strip()
        value = row.find('td').text.strip()
        if value and key not in IGNORE_ATTRIBUTES:
            metadata[key] = value
    return metadata


def get_observation_photo_metadata(observation_id, access_token):
    """Attempt to scrape metadata from a photo info pages associated with an observation
    (first photo only)
    """
    print(f'Fetching observation {observation_id}')
    obs = get_observation(observation_id)
    photo_ids = [photo['id'] for photo in obs.get('photos', [])]
    photo_urls = [f'{PHOTO_INFO_BASE_URL}/{id}' for id in photo_ids]
    print(f'{len(photo_urls)} photo URL(s) found')
    return get_photo_metadata(photo_urls[0], access_token)


if __name__ == '__main__':
    # Get creds from keyring or environment variables
    access_token = get_access_token()
    photo_metadata = {}
    test_observation_ids = [98, 99]

    for id in test_observation_ids:
        photo_metadata[id] = get_observation_photo_metadata(id, access_token)
    pprint(photo_metadata, indent=4)
