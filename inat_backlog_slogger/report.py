import re
from logging import getLogger
from os import makedirs
from os.path import dirname

import pandas as pd
from jinja2 import Template

from pyinaturalist.converters import try_datetime

from inat_backlog_slogger.constants import (
    JSON_OBSERVATIONS,
    JSON_OBSERVATION_EXPORT,
    RANKING_WEIGHTS,
    REPORT_TEMPLATE,
)
from inat_backlog_slogger.image_downloads import get_image_url
from inat_backlog_slogger.observations import load_observations
from inat_backlog_slogger.ranking import get_ranked_subset

DATETIME_FORMAT = '%Y-%m-%d %H:%M'
EXPORT_COLUMNS = [
    'id',
    'created_at',
    'description',
    'short_description',
    'iconic_taxon',
    'license_code',
    'location',
    'num_identification_agreements',
    'num_identification_disagreements',
    'observed_on',
    'photo.id',
    'photo.iqa_aesthetic',
    'photo.iqa_technical',
    # 'photo.small_url',
    'photo.medium_url',
    'photo.original_url',
    'place_guess',
    'quality_grade',
    'rank',
    'ranking_values',
    'tag_list',
    'taxon.id',
    'taxon.formatted_name',
    'taxon.rank',
    'title',
    'updated_at',
    'user.created_at',
    'user.icon',
    'user.iconic_taxon_identifications_count',
    'user.iconic_taxon_rg_observations_count',
    'user.id',
    'user.identifications_count',
    'user.login',
    'user.observations_count',
    'user.species_count',
]

logger = getLogger(__name__)


def truncate(desc, n_chars=120):
    desc = re.sub(r'\s+', ' ', desc.strip())
    return f'{desc[:n_chars-3]}...' if len(desc) > n_chars else desc


def get_ranking_values(row):
    """Format values used in ranking to be shown on hover"""
    return {col: f'{row[col]:.3f}' for col in ['rank'] + list(RANKING_WEIGHTS)}


def format_datetime(value):
    return try_datetime(value).strftime(DATETIME_FORMAT)


def format_taxon_str(row) -> str:
    """Format a taxon name including common name, if available"""
    common_name = row.get('taxon.preferred_common_name')
    return f"{row['taxon.name']}" + (f' ({common_name})' if common_name else '')


"""
<b>{row['taxon.rank']}:&nbsp;</b>
<a href="https://www.inaturalist.org/taxa/{row['taxon.id']}" title="{taxon}">{taxon}</a>
"""
"""
<b>Observed by:</b>
<a href="https://www.inaturalist.org/people/{row['user.id']}">{row['user_login'] or 'unknown'}</a>
on {{ row['observed_on'] }}
"""


def format_title(row):
    taxon = format_taxon_str(row)
    return f"""
    <b>{row['taxon.rank']}:&nbsp;</b><br />
    <a href="'https://www.inaturalist.org/taxa/{row['taxon.id']}'" title="{taxon}">{taxon}</a>
    """


def format_description(row):
    return f"""
    <b>Observed by:</b>
    <a href="https://www.inaturalist.org/people/{row['user.id']}">{row['user.login'] or 'unknown'}</a>
    on {row['observed_on']}
    """


def generate_report(file_path: str, df, top: int = None, bottom: int = None):
    """Generate an HTML report from the specified observations"""
    df = get_ranked_subset(df, top, bottom)
    df['ranking_values'] = df.apply(get_ranking_values, axis=1)
    df['short_description'] = df['description'].apply(truncate)
    df['taxon.formatted_name'] = df.apply(format_taxon_str, axis=1)
    observations = df.to_dict('records')
    observation_chunks = list(ka_chunk(observations, 4))

    with open(REPORT_TEMPLATE) as f:
        template = Template(f.read())

    report = template.render(observation_chunks=observation_chunks)
    report = report.replace('  ', ' ').replace('\n', '')
    makedirs(dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        f.write(report)

    return df


def ka_chunk(data, chunk_size):
    for i in range(0, len(data), chunk_size):
        yield data[i : i + chunk_size]


def load_json_observations():
    """Load observation data from JSON"""
    return pd.read_json(JSON_OBSERVATIONS)


def save_json_observations(df, path=JSON_OBSERVATIONS, top: int = None, bottom: int = None):
    """Export a subset of columns into JSON from ranked and sorted observations"""
    df = get_ranked_subset(df, top, bottom)
    df['ranking_values'] = df.apply(get_ranking_values, axis=1)
    df['short_description'] = df['description'].apply(truncate)

    def get_default_photo(photos):
        return photos[0]['url'].rsplit('/', 1)[0]

    df['taxon.formatted_name'] = df.apply(format_taxon_str, axis=1)
    df['taxon.rank'] = df['taxon.rank'].apply(lambda x: x.title())
    if 'photos' in df and 'photo.url' not in df:
        df['photo.url'] = df['photos'].apply(get_default_photo)
    df['photo.small_url'] = df['photo.url'].apply(lambda x: get_image_url(x, 'medium'))
    df['photo.medium_url'] = df['photo.url'].apply(lambda x: get_image_url(x, 'medium'))
    df['photo.original_url'] = df['photo.url'].apply(lambda x: get_image_url(x, 'original'))
    df['observed_on'] = df['observed_on'].apply(format_datetime)
    df['created_at'] = df['created_at'].apply(format_datetime)
    df['title'] = df.apply(format_title, axis=1)
    df['description'] = df.apply(format_description, axis=1)

    df = df[EXPORT_COLUMNS]
    df = df.rename(columns={col: col.replace('.', '_') for col in sorted(df.columns)})
    df.to_json(path, orient='records', indent=2)
    logger.info(f'Written to {path}')
    return df


if __name__ == '__main__':
    df = load_observations()
    save_json_observations(df, path=JSON_OBSERVATION_EXPORT, top=20)
    # generate_report('example_reports/top_500.html', df, top=500)
    # generate_report('example_reports/bottom_500.html', df, bottom=500)
