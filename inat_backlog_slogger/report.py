from os.path import dirname, join

import pandas as pd
from jinja2 import Template

from inat_backlog_slogger.constants import MINIFIED_EXPORT
from inat_backlog_slogger.observations import load_observations_from_export

REPORT_TEMPLATE = join(dirname(__file__), 'observation_template.html')


def generate_report(file_path, df=None):
    observations = load_observations(df)
    observation_chunks = list(ka_chunk(observations, 4))
    with open(REPORT_TEMPLATE) as f:
        template = Template(f.read())

    report = template.render(observation_chunks=observation_chunks)
    with open(file_path, 'w') as f:
        f.write(report)


def ka_chunk(data, chunk_size):
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]


def load_observations(df=None):
    """Load minified observation data"""
    df = df if df is not None else pd.read_json(MINIFIED_EXPORT)
    return df.to_dict('records')


def minify_observations(df):
    """Get minimal info for ranked and sorted observations"""

    def get_default_photo(photos):
        return photos[0]['url'].rsplit('/', 1)[0]

    df['taxon.rank'] = df['taxon.rank'].apply(lambda x: f'{x.title()}: ')
    df['taxon'] = df['taxon.rank'] + df['taxon.name']
    if 'photos' in df:
        df['photo'] = df['photos'].apply(get_default_photo)
    else:
        df['photo'] = df['photo.url']
    return df[['id', 'taxon', 'photo']]


if __name__ == '__main__':
    df = load_observations_from_export()
    minify_observations(df).to_json(MINIFIED_EXPORT)
    generate_report('report.html', df)
