import os
from os import path as p

_basedir = p.dirname(__file__)
_user = os.environ.get('USER', os.environ.get('USERNAME', 'default'))
__YOUR_EMAIL__ = '%s@gmail.com' % _user


# configuration
class Config(object):
	app = 'ebay-search-api'
	HEROKU = os.environ.get('DATABASE_URL', False)

	DEBUG = False
	DEBUG_MEMCACHE = True
	ADMINS = frozenset([__YOUR_EMAIL__])
	TESTING = False
	HOST = '127.0.0.1'

	if HEROKU:
		SERVER_NAME = '%s.herokuapp.com' % app

	SECRET_KEY = os.environ.get('SECRET_KEY', 'key')
	API_METHODS = ['GET']
	API_MAX_RESULTS_PER_PAGE = 1000
	API_URL_PREFIX = '/api/v1'


class Production(Config):
	HOST = '0.0.0.0'


class Development(Config):
	DEBUG = True
	DEBUG_MEMCACHE = False


class Test(Config):
	TESTING = True
	DEBUG_MEMCACHE = False
