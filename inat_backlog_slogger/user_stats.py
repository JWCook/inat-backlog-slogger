#!/usr/bin/env python
"""Utilities for downloading observer user information"""
import json
from logging import getLogger
from os.path import isfile
from time import sleep

from pyinaturalist.node_api import get_identifications, get_observations, get_user_by_id
from pyinaturalist.request_params import ICONIC_TAXA
from rich.progress import Progress

from inat_backlog_slogger.constants import ICONIC_TAXON, THROTTLING_DELAY, USER_STATS
from inat_backlog_slogger.observations import load_observations, save_observations

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


# TODO: Process as a dataframe instead of a dict, save/load as parquet files instead of JSON
def get_all_user_stats(user_ids, user_records=None):
    """Get some additional information about observers"""
    iconic_taxa_lookup = {v.lower(): k for k, v in ICONIC_TAXA.items()}
    iconic_taxon_id = iconic_taxa_lookup[ICONIC_TAXON.lower()]
    user_ids = set(user_ids)
    user_info = {}
    user_records = user_records or {}

    # Load previously saved stats, if any
    if isfile(USER_STATS):
        with open(USER_STATS) as f:
            user_info = {int(k): v for k, v in json.load(f).items()}
        logger.info(f'{len(user_info)} results loaded')
    user_ids = [u for u in user_ids if u not in user_info]

    # Estimate how long this thing is gonna take
    secs_per_user = (2 if user_records else 3) * THROTTLING_DELAY
    est_time = len(user_ids) / (60 / secs_per_user) / 60
    logger.info(f'Getting stats for {len(user_ids)} unique users')
    logger.warning(f'Estimated time, with default API request throttling: {est_time:.2f} hours')

    # Fetch results, and save partial results if interrupted
    with Progress() as progress:
        task = progress.add_task("[cyan]Downloading...", total=len(user_ids) + len(user_info))
        progress.update(task, advance=len(user_info))

        for user_id in user_ids:
            try:
                user_info[user_id] = get_user_stats(
                    user_id, iconic_taxon_id, progress.console, user_records.get(user_id)
                )
            except (Exception, KeyboardInterrupt) as e:
                logger.exception(e)
                logger.error(f'Aborting and saving {len(user_info)} results to {USER_STATS}')
                break
            progress.update(task, advance=1)

    with open(USER_STATS, 'w') as f:
        json.dump(user_info, f, default=str)

    return user_info


# TODO: Store stats for multiple taxa in same file; will need additional checks & handling
def get_user_stats(user_id, iconic_taxon_id, console, user=None):
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
    console.print(f'Downloaded stats for user {user["login"]} ({user_id})')
    return user


# Add user info to an existing observation export
if __name__ == '__main__':
    df = load_observations()
    df = append_user_stats(df)
    df['user.created_at'] = df['user.created_at'].astype(str)
    df['user.roles'] = df['user.roles'].astype(str)
    save_observations(df)
