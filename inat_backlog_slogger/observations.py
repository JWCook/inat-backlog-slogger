"""Utilities for loading, querying, formatting, and saving observation data"""
from datetime import datetime, timedelta
from logging import getLogger

import pandas as pd
from pyinaturalist.v1 import get_observations
from pyinaturalist_convert.csv import format_columns, format_response, load_csv_exports

from inat_backlog_slogger.constants import CSV_EXPORTS, ICONIC_TAXON, PROCESSED_OBSERVATIONS

logger = getLogger(__name__)


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


if __name__ == '__main__':
    df = load_csv_exports(CSV_EXPORTS)
