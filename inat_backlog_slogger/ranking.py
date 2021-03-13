#!/usr/bin/env python
"""Utilities for ranking observation data"""
import numpy as np

from inat_backlog_slogger.constants import RANK_BY_NATURAL_LOG, RANKING_WEIGHTS
from inat_backlog_slogger.observations import load_observations, save_observations


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


# Apply ranking to processed observations
if __name__ == '__main__':
    df = load_observations()
    df = rank_observations(df)
    save_observations(df)
