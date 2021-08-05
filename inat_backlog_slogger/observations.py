"""Utilities for loading, querying, formatting, and saving observation data"""
from datetime import datetime, timedelta
from logging import getLogger
from os import makedirs

import pandas as pd
import requests_cache
from pyinaturalist.constants import RANKS
from pyinaturalist.converters import try_datetime
from pyinaturalist.v1 import get_observations
from pyinaturalist_convert import load_exports, to_dataframe

from inat_backlog_slogger.constants import (
    CACHE_FILE,
    CSV_EXPORTS,
    DATA_DIR,
    DROP_COLUMNS,
    DTYPES,
    ICONIC_TAXON,
    PROCESSED_OBSERVATIONS,
    RENAME_COLUMNS,
)

logger = getLogger(__name__)
requests_cache.install_cache(backend='sqlite', cache_name=CACHE_FILE)


def load_observations():
    """Load previously processed observations"""
    logger.info(f'Loading {PROCESSED_OBSERVATIONS}')
    return pd.read_parquet(PROCESSED_OBSERVATIONS)


def save_observations(df):
    """Save processed observations to parquet format"""
    logger.info(f'Saving observations to {PROCESSED_OBSERVATIONS}')
    df = format_columns(df)
    df.to_parquet(PROCESSED_OBSERVATIONS)


def load_observations_from_query(iconic_taxon=ICONIC_TAXON, days=60, **request_params):
    """Query all recent unidentified observations for the given iconic taxon"""
    response = get_observations(
        iconic_taxa=iconic_taxon,
        quality_grade='needs_id',
        d1=datetime.now() - timedelta(days=days),
        page='all',
        **request_params,
    )
    df = format_response(response)
    save_observations(df)
    return df


def load_observations_from_export():
    """Load and format CSV export files"""
    logger.info(f'Loading {CSV_EXPORTS}')
    makedirs(DATA_DIR, exist_ok=True)

    df = load_exports(CSV_EXPORTS)
    df = format_export(df)
    save_observations(df)
    return df


def format_columns(df):
    """Some datatype conversions that apply to both CSV exports and API response data"""
    # Convert to expected datatypes
    for col, dtype in DTYPES.items():
        if col in df:
            df[col] = df[col].fillna(dtype()).astype(dtype)

    # Drop selected columns plus any empty columns
    df = df.drop(columns=[k for k in DROP_COLUMNS if k in df])
    df = df.dropna(axis=1, how='all')
    return df.fillna('')


def format_response(response):
    """Convert and format API response data into a dataframe"""
    df = to_dataframe(response['results'])
    df['photo.url'] = df['photos'].apply(lambda x: x[0]['url'])
    df['photo.id'] = df['photos'].apply(lambda x: x[0]['id'])
    df = format_columns(df)
    return df


# TODO: Normalize datetimes to UTC, convert to datetime64
def format_export(df):
    """Format an exported CSV file to be similar to API response format"""
    from inat_backlog_slogger.image_downloads import get_photo_id

    logger.info(f'Formatting {len(df)} observation records')

    # Rename, convert, and drop selected columns
    df = df.rename(columns={col: _rename_column(col) for col in sorted(df.columns)})
    df = format_columns(df)

    # Convert datetimes
    df['observed_on'] = df['observed_on_string'].apply(lambda x: try_datetime(x) or x)
    df['created_at'] = df['created_at'].apply(lambda x: try_datetime(x) or x)
    df['updated_at'] = df['updated_at'].apply(lambda x: try_datetime(x) or x)

    # Fill out taxon name and rank
    df['taxon.rank'] = df.apply(_get_min_rank, axis=1)
    df['taxon.name'] = df.apply(lambda x: x.get(f"taxon.{x['taxon.rank']}"), axis=1)

    # Format coordinates
    # TODO: Convert API results to latitude, longitude instead
    df['location'] = df.apply(lambda x: [x['latitude'], x['longitude']], axis=1)
    df = df.drop(columns=['latitude', 'longitude'])

    # Add some other missing columns
    df['photo.id'] = df['photo.url'].apply(get_photo_id)
    return df


def get_observation_subset(df, top: int = None, bottom: int = None):
    """Get highest or lowest-ranked items, if specified"""
    if top:
        selection = f'top {top}'
        df = df.iloc[:top].copy()
    elif bottom:
        selection = f'bottom {bottom}'
        df = df.iloc[-bottom:].copy()
    else:
        selection = str(len(df))
    logger.info(f'Selecting {selection} observations')
    return df


def get_updated_observations(df, top: int = None, bottom: int = None):
    """Get updated info for recently updated observations"""
    last_updated = df['updated_at'].max()
    df = get_observation_subset(df, top, bottom)
    response = get_observations(id=list(df['id']), updated_since=last_updated)
    return format_response(response)


def update_observations(df, top: int = None, bottom: int = None):
    """Update local observation data with any remote changes since last update"""
    updated = get_updated_observations(df, top, bottom)
    return df.merge(updated, on='id', how='left')


def iloc(df, loc):
    """Get the specified dataframe row as a dict"""
    return dict(sorted(df.iloc[loc].items()))


def _fixna(df):
    """Fix null values of the wrong type"""
    for col, dtype in DTYPES.items():
        if col in df:
            df[col] = df[col].apply(lambda x: x or dtype())
    return df


def _get_min_rank(series):
    for rank in RANKS:
        if series.get(f'taxon.{rank}'):
            return rank
    return ''


def _rename_column(col):
    for str_1, str_2 in RENAME_COLUMNS.items():
        col = col.replace(str_1, str_2)
    return col
