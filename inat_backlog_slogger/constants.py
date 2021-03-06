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

# Explicit datatypes for columns loaded from CSV
# TODO: support glob patterns (num_*, *_count, *.id, etc.)
DTYPES = {
    'obscured': bool,
    'id': int,
    'latitude': float,
    'longitude': float,
    'num_identification_agreements': int,
    'num_identification_disagreements': int,
    'photo.id': int,
    'photo.iqa_aesthetic': float,
    'photo.iqa_technical': float,
    'positional_accuracy': float,
    'public_positional_accuracy': float,
    'taxon.id': int,
    'user.activity_count': int,
    'user.iconic_taxon_identifications_count': int,
    'user.iconic_taxon_rg_observations_count': int,
    'user.id': int,
    'user.identifications_count': int,
    'user.journal_posts_count': int,
    'user.observations_count': int,
    'user.site_id': int,
    'user.species_count': int,
    'user.suspended': bool,
    # 'observed_on': 'datetime64',
    # 'created_at': 'datetime64',
    # 'updated_at': 'datetime64',
    # 'user.created_at': 'datetime64',
}

# Columns to drop
DROP_COLUMNS = [
    'cached_votes_total',
    'flags',
    'oauth_application_id',
    'observed_on_string',
    'positioning_method',
    'positioning_device',
    'scientific',
    'spam',
    'time_observed_at',
    'time_zone',
    'user.spam',
    'user.suspended',
    'user.universal_search_rank',
    'uuid',
]

# Columns from CSV export rename to match API response
RENAME_COLUMNS = {
    'common_name': 'taxon.preferred_common_name',
    'coordinates_obscured': 'obscured',
    'image_url': 'photo.url',
    'license': 'license_code',
    'taxon_': 'taxon.',
    'url': 'uri',
    'user_': 'user.',
    '_name': '',
}

# Files & directories; different data sources are stored separately to support incremental results
PROJECT_DIR = dirname(dirname(__file__))
DATA_DIR = join(expanduser('~'), 'Downloads')
CACHE_FILE = join(DATA_DIR, 'inat_requests.db')
CSV_EXPORTS = join(DATA_DIR, 'observations-*.csv')
IMAGE_DIR = join(DATA_DIR, 'images')
IQA_REPORTS = [join(DATA_DIR, 'iqa_aesthetic.json'), join(DATA_DIR, 'iqa_technical.json')]
JSON_OBSERVATIONS = join(DATA_DIR, 'observations.json')
JSON_OBSERVATION_EXPORT = join(dirname(PROJECT_DIR), 'inat-backlog-viewer', 'assets', 'observations.json')
PROCESSED_OBSERVATIONS = join(DATA_DIR, 'observations.parquet')
REPORT_TEMPLATE = join(PROJECT_DIR, 'template', 'observation_viewer.html')
USER_STATS = join(DATA_DIR, f'user_stats_{ICONIC_TAXON.lower()}.json')

THROTTLING_DELAY = 3.0
