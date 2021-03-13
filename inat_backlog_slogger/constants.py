from os.path import expanduser, join

# TODO: Make this a parameter to all relevant functions instead of a constant
ICONIC_TAXON = 'Arachnida'

# Note: all values are normalized before ranking weights are applied.
# fmt: off
RANKING_WEIGHTS = {
    'iqa_technical':                      2.0,   # Image quality assessment score
    'iqa_aesthetic':                      1.0,   # Secondary image quality assessment score
    'iconic_taxon_rg_observations_count': 1.5,   # Number of research-grade observations for ICONIC_TAXON
    'iconic_taxon_identifications_count': 2.0,   # Number of identifications for ICONIC_TAXON
    'observations_count':                 0.1,   # Total observations (all taxa)
    'identifications_count':              0.1,   # Total identifications (all taxa)
}

# Files & directories
DATA_DIR = join(expanduser('~'), 'Downloads')
CACHE_FILE = join(DATA_DIR, 'inat_requests.db')
CSV_EXPORTS = join(DATA_DIR, 'observations-*.csv')
CSV_COMBINED_EXPORT = join(DATA_DIR, 'combined-observations.csv')
IQA_REPORTS = [join(DATA_DIR, 'iqa_aesthetic.json'), join(DATA_DIR, 'iqa_technical.json')]
IMAGE_DIR = join(DATA_DIR, 'images')
MINIFIED_EXPORT = join(DATA_DIR, 'minified_observations.json')


THROTTLING_DELAY = 2.0
