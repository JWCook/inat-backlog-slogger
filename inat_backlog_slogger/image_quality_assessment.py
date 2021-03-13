#!/usr/bin/env python
"""Utilities to process image quality assessment outputs"""
import json
from logging import getLogger
from os.path import basename, splitext

from .constants import CSV_COMBINED_EXPORT, IQA_REPORTS
from .observations import load_observations_from_export

logger = getLogger(__name__)


def append_iqa_scores(df):
    """Load image quality assessment scores and append to a dataframe of observation records"""
    # Sort user IDs by number of observations (in the current dataset) per user
    scores = load_iqa_scores()

    first_result = list(scores.values())[0]
    for key in first_result.keys():
        logger.info(f'Updating observations with {key}')
        df[key] = df['photo.id'].apply(lambda x: scores.get(x, {}).get(key))
    return df


def load_iqa_scores():
    """Load scores from one or more image quality assessment output files"""
    logger.info('Loading image quality assessment data')
    combined_scores = {}
    for file_path in IQA_REPORTS:
        with open(file_path) as f:
            scores = json.load(f)

        key = splitext(basename(file_path))[0]
        scores = {int(i['image_id']): {key: i['mean_score_prediction']} for i in scores}
        combined_scores.update(scores)

    combined_scores = dict(sorted(combined_scores.items(), key=lambda x: x[1][key]))
    return combined_scores


if __name__ == '__main__':
    df = load_observations_from_export()
    df = append_iqa_scores(df)
    df.to_csv(CSV_COMBINED_EXPORT)
