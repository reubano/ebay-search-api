# -*- coding: utf-8 -*-
"""
    config
    ~~~~~~

    Provides the flask config options
    ###########################################################################
    # WARNING: if running on a a staging server, you MUST set the 'STAGE' env
    # heroku config:set STAGE=true --remote staging
    ###########################################################################
"""
from os import getenv, path as p
from datetime import timedelta
from pkutils import parse_module

PARENT_DIR = p.abspath(p.dirname(__file__))
DAYS_PER_MONTH = 30

app = parse_module(p.join(PARENT_DIR, 'app', '__init__.py'))
user = getenv('USER', 'user')

__APP_NAME__ = app.__package_name__
__EMAIL__ = app.__email__
__DOMAIN__ = 'nerevu.com'
__SUB_DOMAIN__ = __APP_NAME__.split('-')[-1]


def get_seconds(seconds=0, months=0, **kwargs):
    seconds = timedelta(seconds=seconds, **kwargs).total_seconds()

    if months:
        seconds += timedelta(DAYS_PER_MONTH).total_seconds() * months

    return int(seconds)


# configuration
class Config(object):
    HEROKU = getenv('HEROKU', False)
    DEBUG = False
    TESTING = False
    DEBUG_MEMCACHE = True
    ADMINS = frozenset([__EMAIL__])
    HOST = '127.0.0.1'
    CACHE_TIMEOUT = get_seconds(minutes=60)
    CAT_CACHE_TIMEOUT = get_seconds(days=7)
    SUB_CAT_CACHE_TIMEOUT = get_seconds(hours=24)
    APP_NAME = __APP_NAME__

    end = '-stage' if getenv('STAGE', False) else ''

    if HEROKU:
        SERVER_NAME = '{}{}.herokuapp.com'.format(APP_NAME, end)
    elif getenv('DIGITALOCEAN'):
        SERVER_NAME = '{}.{}'.format(__SUB_DOMAIN__, __DOMAIN__)
        SSLIFY_SUBDOMAINS = True

    API_METHODS = ['GET', 'DELETE']
    API_RESULTS_PER_PAGE = 32
    API_MAX_RESULTS_PER_PAGE = 1024
    API_URL_PREFIX = '/api/v1'
    SWAGGER_URL = ''
    SWAGGER_JSON = 'swagger.json'
    SWAGGER_EXCLUDE_COLUMNS = {'utc_created', 'utc_updated'}
    SWAGGER_EXCLUDE_ROUTES = {'static', 'swagger.swagger_json', 'home'}


class Production(Config):
    HOST = '0.0.0.0'


class Development(Config):
    DEBUG = True
    DEBUG_MEMCACHE = False


class Test(Config):
    TESTING = True
    DEBUG_MEMCACHE = False
