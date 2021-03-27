#!/usr/bin/env python
"""Utilities for ranking observation data"""
from logging import getLogger

import numpy as np

from inat_backlog_slogger.constants import RANK_BY_NATURAL_LOG, RANKING_WEIGHTS
from inat_backlog_slogger.observations import (
    get_observation_subset,
    load_observations,
    save_observations,
)

logger = getLogger(__name__)


def rank_observations(df):
    """Combine normalized and weighted values into a single ranking value, and sort"""

    def normalize(key, series):
        series = series.copy()
        if key in RANK_BY_NATURAL_LOG:
            with np.errstate(divide='ignore'):
                series = np.log(series)
        series[np.isneginf(series)] = 0
        return (series - series.mean()) / series.std()

    df['rank'] = sum([normalize(key, df[key]) * weight for key, weight in RANKING_WEIGHTS.items()])
    df['rank'].fillna(0)
    return df.sort_values('rank', ascending=False)


def get_ranked_subset(df, top: int = None, bottom: int = None):
    """Get highest or lowest-ranked items, if specified, and omit any that haven't been ranked"""
    return get_observation_subset(df[df['photo.iqa_technical'] != 0], top, bottom)


# Apply ranking to processed observations
if __name__ == '__main__':
    df = load_observations()
    df = rank_observations(df)
    save_observations(df)
