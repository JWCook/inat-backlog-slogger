#!/usr/bin/env python
"""Utilities for downloading observer information"""
import json
from logging import getLogger
from os.path import isfile, join
from time import sleep

from pyinaturalist.node_api import get_identifications, get_observations, get_user_by_id
from pyinaturalist.request_params import ICONIC_TAXA
from rich.progress import track

from .constants import CSV_COMBINED_EXPORT, DATA_DIR, ICONIC_TAXON, THROTTLING_DELAY
from .observations import load_observations_from_export

USER_STATS_FILE = join(DATA_DIR, f'user_stats_{ICONIC_TAXON.lower()}.json')
logger = getLogger(__name__)


def append_user_stats(df):
    """Fetch user stats and append to a dataframe of observation records"""
    # Sort user IDs by number of observations (in the current dataset) per user
    sorted_user_ids = dict(df['user.id'].value_counts()).keys()
    user_info = get_all_user_stats(sorted_user_ids)

    first_result = list(user_info.values())[0]
    for key in first_result.keys():
        logger.info(f'Updating observations with user.{key}')
        df[f'user.{key}'] = df['user.id'].apply(lambda x: user_info.get(x, {}).get(key))
    return df


def get_all_user_stats(user_ids, user_records=None):
    """Get some additional information about observers"""
    iconic_taxa_lookup = {v.lower(): k for k, v in ICONIC_TAXA.items()}
    iconic_taxon_id = iconic_taxa_lookup[ICONIC_TAXON.lower()]
    user_ids = set(user_ids)
    user_info = {}
    user_records = user_records or {}

    # Load previously saved stats, if any
    if isfile(USER_STATS_FILE):
        with open(USER_STATS_FILE) as f:
            user_info = {int(k): v for k, v in json.load(f).items()}
        logger.info(f'{len(user_info)} partial results loaded')

    # Estimate how long this thing is gonna take
    n_users_remaining = len(user_ids) - len(user_info)
    secs_per_user = (2 if user_records else 3) * THROTTLING_DELAY
    est_time = n_users_remaining / (60 / secs_per_user) / 60
    logger.info(f'Getting stats for {n_users_remaining} unique users')
    logger.warning(f'Estimated time, with default API request throttling: {est_time:.2f} hours')

    # Fetch results, and save partial results if interrupted
    for user_id in track(user_ids):
        if user_id in user_info:
            continue

        try:
            user_info[user_id] = get_user_stats(user_id, iconic_taxon_id, user_records.get(user_id))
        except (Exception, KeyboardInterrupt) as e:
            logger.exception(e)
            logger.error(f'Aborting and saving partial results to {USER_STATS_FILE}')
            break

    with open(USER_STATS_FILE, 'w') as f:
        json.dump(user_info, f)

    return user_info


def get_user_stats(user_id, iconic_taxon_id, user=None):
    """Get info for an individual user"""
    logger.debug(f'Getting stats for user {user_id}')
    # Full user info will already be available if fetched from API, but not for CSV exports
    if not user:
        user = get_user_by_id(user_id)
        sleep(THROTTLING_DELAY)
    user.pop('id', None)

    user_observations = get_observations(
        user_id=user_id,
        iconic_taxa=ICONIC_TAXON,
        quality_grade='research',
        count_only=True,
    )
    sleep(THROTTLING_DELAY)
    user_identifications = get_identifications(
        user_id=user_id,
        iconic_taxon_id=iconic_taxon_id,
        count_only=True,
    )
    sleep(THROTTLING_DELAY)

    user['iconic_taxon_rg_observations_count'] = user_observations['total_results']
    user['iconic_taxon_identifications_count'] = user_identifications['total_results']
    return user


if __name__ == '__main__':
    df = load_observations_from_export()
    df = append_user_stats(df)
    df.to_csv(CSV_COMBINED_EXPORT)
