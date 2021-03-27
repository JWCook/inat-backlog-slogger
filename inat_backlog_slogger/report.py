from logging import getLogger
from os import makedirs
from os.path import dirname

import pandas as pd
from jinja2 import Template

from inat_backlog_slogger.constants import JSON_OBSERVATIONS, RANKING_WEIGHTS, REPORT_TEMPLATE
from inat_backlog_slogger.image_downloads import get_image_url
from inat_backlog_slogger.observations import load_observations
from inat_backlog_slogger.ranking import get_ranked_subset

EXPORT_COLUMNS = [
    'id',
    'created_at',
    'description',
    'iconic_taxon',
    'latitude',
    'license',
    'longitude',
    'num_identification_agreements',
    'num_identification_disagreements',
    'observed_on',
    'photo.id',
    'photo.iqa_aesthetic',
    'photo.iqa_technical',
    'photo.medium_url',
    'photo.original_url',
    'place_guess',
    'quality_grade',
    'rank',
    'tag_list',
    'taxon.formatted_name',
    'taxon.rank',
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


def get_ranking_values(row):
    """Format values used in ranking to be shown on hover"""
    return {col: f'{row[col]:.3f}' for col in ['rank'] + list(RANKING_WEIGHTS)}


def format_taxon_str(row) -> str:
    """Format a taxon name including common name, if available"""
    common_name = row.get('taxon.preferred_common_name')
    return f"{row['taxon.name']}" + (f' ({common_name})' if common_name else '')


def generate_report(file_path: str, df, top: int = None, bottom: int = None):
    """Generate an HTML report from the specified observations"""
    df = get_ranked_subset(df, top, bottom)
    df['ranking_values'] = df.apply(get_ranking_values, axis=1)
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


def save_json_observations(df, top: int = None, bottom: int = None):
    """Export a subset of columns into JSON from ranked and sorted observations"""
    df = get_ranked_subset(df, top, bottom)

    def get_default_photo(photos):
        return photos[0]['url'].rsplit('/', 1)[0]

    # df['taxon.rank'] = df['taxon.rank'].apply(lambda x: f'{x.title()}: ')
    # df['taxon.formatted_name'] = df['taxon.rank'] + df['taxon.name']
    df['taxon.formatted_name'] = df.apply(format_taxon_str, axis=1)
    df['taxon.rank'] = df['taxon.rank'].apply(lambda x: x.title())
    if 'photos' in df and 'photo.url' not in df:
        df['photo.url'] = df['photos'].apply(get_default_photo)
    df['photo.medium_url'] = df['photo.url'].apply(lambda x: get_image_url(x, 'medium'))
    df['photo.original_url'] = df['photo.url'].apply(lambda x: get_image_url(x, 'original'))

    df = df[EXPORT_COLUMNS]
    df = df.rename(columns={col: col.replace('.', '_') for col in sorted(df.columns)})
    df.to_json(JSON_OBSERVATIONS, orient='records')
    logger.info(f'Written to {JSON_OBSERVATIONS}')
    return df


if __name__ == '__main__':
    df = load_observations()
    save_json_observations(df)
    generate_report('example_reports/top_500.html', df, top=500)
    generate_report('example_reports/bottom_500.html', df, bottom=500)
