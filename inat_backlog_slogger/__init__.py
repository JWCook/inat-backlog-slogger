from logging import basicConfig, getLogger

basicConfig(level='INFO')
getLogger('pyrate_limiter').setLevel('WARNING')
