from logging import getLogger

import pandas as pd
from jinja2 import Template

from inat_backlog_slogger.constants import MINIFIED_OBSERVATIONS, RANKING_WEIGHTS, REPORT_TEMPLATE
from inat_backlog_slogger.observations import load_observations

logger = getLogger(__name__)


def get_ranking_values(row):
    """Format values used in ranking to be shown on hover"""
    return {col: f'{row[col]:.3f}' for col in ['rank'] + list(RANKING_WEIGHTS)}


def format_taxon_str(row) -> str:
    """Format a taxon name including common name, if available"""
    common_name = row.get('taxon.preferred_common_name')
    return f"{row['taxon.name']}" + (f' ({common_name})' if common_name else '')


def generate_report(file_path: str, df, top: int = None, bottom: int = None):
    """Generate an HTML report from the specified observations"""
    df = get_observation_subset(df, top, bottom)
    df['ranking_values'] = df.apply(get_ranking_values, axis=1)
    df['taxon.formatted_name'] = df.apply(format_taxon_str, axis=1)
    observations = df.to_dict('records')
    observation_chunks = list(ka_chunk(observations, 4))

    with open(REPORT_TEMPLATE) as f:
        template = Template(f.read())

    report = template.render(observation_chunks=observation_chunks)
    report = report.replace('  ', ' ').replace('\n', '')
    with open(file_path, 'w') as f:
        f.write(report)

    return df


def get_observation_subset(df, top: int = None, bottom: int = None):
    """Get highest or lowest-ranked items, if specified, and omit any that haven't been ranked"""
    df = df[df['photo.iqa_technical'] != 0]
    if top:
        selection = f'top {top}'
        df = df.iloc[:top].copy()
    elif bottom:
        selection = f'bottom {bottom}'
        df = df.iloc[-bottom:].copy()
    else:
        selection = str(len(df))
    logger.info(f'Generating report from {selection} observations')
    return df


def ka_chunk(data, chunk_size):
    for i in range(0, len(data), chunk_size):
        yield data[i : i + chunk_size]


def load_minified_observations():
    """Load minified observation data"""
    return pd.read_json(MINIFIED_OBSERVATIONS)


def save_minified_observations(df):
    """Get minimal info for ranked and sorted observations"""

    def get_default_photo(photos):
        return photos[0]['url'].rsplit('/', 1)[0]

    df['taxon.rank'] = df['taxon.rank'].apply(lambda x: f'{x.title()}: ')
    df['taxon'] = df['taxon.rank'] + df['taxon.name']
    if 'photos' in df:
        df['photo'] = df['photos'].apply(get_default_photo)
    else:
        df['photo'] = df['photo.url']

    df = df[['id', 'taxon', 'photo']]
    df.to_json(MINIFIED_OBSERVATIONS)
    return df


if __name__ == '__main__':
    df = load_observations()
    save_minified_observations(df)
    generate_report('report.html', df)
