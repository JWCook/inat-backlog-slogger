from logging import basicConfig, getLogger

basicConfig(
    level='INFO',
    format='[%(asctime)s] %(levelname)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
getLogger('pyrate_limiter').setLevel('WARNING')
