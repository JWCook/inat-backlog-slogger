#!/usr/bin/env python
# flake8: noqa: E241
"""Utilities for loading and querying observation data"""
from datetime import datetime, timedelta
from logging import getLogger
from os import makedirs
from os.path import isfile

import pandas as pd
import requests_cache
from pyinaturalist.node_api import get_observations
from pyinaturalist.request_params import RANKS
from pyinaturalist.response_format import try_datetime
from pyinaturalist.response_utils import load_exports, to_dataframe

from inat_backlog_slogger.constants import (
    CACHE_FILE,
    CSV_COMBINED_EXPORT,
    CSV_EXPORTS,
    DATA_DIR,
    ICONIC_TAXON,
    RANKING_WEIGHTS,
)

logger = getLogger(__name__)
requests_cache.install_cache(backend='sqlite', cache_name=CACHE_FILE)


def rank_observations(df):
    """Combine normalized and weighted values into a single ranking value, and sort"""

    def normalize(series):
        return (series - series.mean()) / series.std()

    df['rank'] = sum([normalize(df[key]) * weight for key, weight in RANKING_WEIGHTS.items()])
    df['rank'].fillna(0)
    return df.sort_values('rank', ascending=False)


def load_observations_from_query(iconic_taxon=ICONIC_TAXON, days=60, **request_params):
    """Query all recent unidentified observations for the given iconic taxon"""
    response = get_observations(
        iconic_taxa=iconic_taxon,
        quality_grade='needs_id',
        d1=datetime.now() - timedelta(days=days),
        page='all',
        **request_params,
    )
    df = to_dataframe(response['results'])
    df['photo.url'] = df['photos'].apply(lambda x: x[0]['url'])
    df['photo.id'] = df['photos'].apply(lambda x: x[0]['id'])
    return df


def load_observations_from_export():
    """Either load and format raw export files, or load previously processed export file, if it
    exists
    """
    makedirs(DATA_DIR, exist_ok=True)
    if isfile(CSV_COMBINED_EXPORT):
        logger.info(f'Loading {CSV_COMBINED_EXPORT}')
        return pd.read_csv(CSV_COMBINED_EXPORT)

    logger.info(f'Loading {CSV_EXPORTS}')
    df = load_exports(CSV_EXPORTS)
    df = format_export(df)
    df.to_csv(CSV_COMBINED_EXPORT)
    return df


def save_observations(df):
    for k in RANKING_WEIGHTS:
        if k in df:
            df[k] = df[k].apply(lambda x: x or 0.0).astype(float)
    logger.info(f'Saving observations to {CSV_COMBINED_EXPORT}')
    df.to_csv(CSV_COMBINED_EXPORT)


def format_export(df):
    """Format an exported CSV file to be similar to API response format"""
    from inat_backlog_slogger.image_downloads import get_photo_id

    logger.info(f'Formatting {len(df)} observation records')
    replace_strs = {
        'common_name': 'taxon.preferred_common_name',
        'image_url': 'photo.url',
        'taxon_': 'taxon.',
        'user_': 'user.',
        '_name': '',
    }
    drop_cols = [
        'observed_on_string',
        'positioning_method',
        'positioning_device',
        'scientific',
        'time_observed_at',
        'time_zone',
    ]

    # Convert datetimes
    df['observed_on'] = df['observed_on_string'].apply(lambda x: try_datetime(x) or x)
    df['created_at'] = df['created_at'].apply(lambda x: try_datetime(x) or x)
    df['updated_at'] = df['updated_at'].apply(lambda x: try_datetime(x) or x)

    # Rename and drop selected columns
    def rename_column(col):
        for str_1, str_2 in replace_strs.items():
            col = col.replace(str_1, str_2)
        return col

    df = df.rename(columns={col: rename_column(col) for col in sorted(df.columns)})
    df = df.drop(columns=drop_cols)

    def get_min_rank(series):
        for rank in RANKS:
            if series.get(f'taxon.{rank}'):
                return rank
        return ''

    # Fill out taxon name and rank
    df = df.fillna('')
    df['taxon.rank'] = df.apply(get_min_rank, axis=1)
    df['taxon.name'] = df.apply(lambda x: x.get(f"taxon.{x['taxon.rank']}"), axis=1)

    # Add some other missing columns
    df['photo.id'] = df['photo.url'].apply(get_photo_id)
    return df


def main(source='export'):
    if source == 'api':
        df = load_observations_from_query(ICONIC_TAXON)
    else:
        df = load_observations_from_export()
    df = rank_observations(df)
    save_observations(df)


if __name__ == '__main__':
    main()
