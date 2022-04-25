# flake8: noqa: E241
from os.path import dirname, expanduser, join

# TODO: Make this a parameter to all relevant functions instead of a constant
ICONIC_TAXON = 'Arachnida'

# Note: all values are normalized before ranking weights are applied.
# fmt: off
RANKING_WEIGHTS = {
    'photo.iqa_technical':                     9.0,   # Image quality assessment score
    'photo.iqa_aesthetic':                     7.0,   # Secondary image quality assessment score
    'user.iconic_taxon_rg_observations_count': 0.3,   # Number of research-grade observations for ICONIC_TAXON
    'user.iconic_taxon_identifications_count': 0.5,   # Number of identifications for ICONIC_TAXON
    'user.observations_count':                 0.1,   # Total observations (all taxa)
    'user.identifications_count':              0.1,   # Total identifications (all taxa)
}
RANK_BY_NATURAL_LOG = [
    'user.iconic_taxon_identifications_count',
    'user.iconic_taxon_rg_observations_count',
    'user.observations_count',
    'user.identifications_count',
]

# Files & directories; different data sources are stored separately to support incremental results
PROJECT_DIR = dirname(dirname(__file__))
DATA_DIR = join(expanduser('~'), 'Downloads')
CSV_EXPORTS = join(DATA_DIR, 'observations-*.csv')
IMAGE_DIR = join(DATA_DIR, 'images')
IQA_REPORTS = [join(DATA_DIR, 'iqa_aesthetic.json'), join(DATA_DIR, 'iqa_technical.json')]
JSON_OBSERVATIONS = join(DATA_DIR, 'observations.json')
JSON_OBSERVATION_EXPORT = join(dirname(PROJECT_DIR), 'inat-backlog-viewer', 'assets', 'observations.json')
PROCESSED_OBSERVATIONS = join(DATA_DIR, 'observations.parquet')
REPORT_TEMPLATE = join(PROJECT_DIR, 'template', 'observation_viewer.html')
USER_STATS = join(DATA_DIR, f'user_stats_{ICONIC_TAXON.lower()}.json')

THROTTLING_DELAY = 3.0
