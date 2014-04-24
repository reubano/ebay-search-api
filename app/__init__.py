# -*- coding: utf-8 -*-
"""
	app
	~~~~~~~~~~~~~~

	Provides the flask application
"""
import config

from os import environ
from json import JSONEncoder, dumps
from urllib import unquote
from api import Trading, Finding
from ebaysdk.exception import ConnectionError
from flask import Flask, redirect, url_for, request, make_response
from flask.ext.cache import Cache

cache = Cache()
search_cache_timeout = 1 * 60 * 60  # hours (in seconds)


def jsonify(result, status=200):
	response = make_response(dumps(result, cls=CustomEncoder))
	response.headers['Content-Type'] = 'application/json; charset=utf-8'
	response.headers['mimetype'] = 'application/json'
	response.status_code = status
	return response


def corsify(response, methods):
	allow = 'HEAD, OPTIONS'

	for m in methods:
		allow += ', %s' % m

	response.headers['Access-Control-Allow-Origin'] = '*'
	response.headers['Access-Control-Allow-Methods'] = allow
	response.headers['Access-Control-Allow-Headers'] = (
		'Origin, X-Requested-With, Content-Type, Accept')

	response.headers['Access-Control-Allow-Credentials'] = 'true'
	return response


def create_app(config_mode=None, config_file=None):
	# Create webapp instance
	app = Flask(__name__)
	cache_config = {}

	if config_mode:
		app.config.from_object(getattr(config, config_mode))
	elif config_file:
		app.config.from_pyfile(config_file)
	else:
		app.config.from_envvar('APP_SETTINGS', silent=True)

	if app.config['HEROKU']:
		cache_config['CACHE_TYPE'] = 'spreadsaslmemcachedcache'
		cache_config.setdefault('CACHE_MEMCACHED_SERVERS',
			[environ.get('MEMCACHIER_SERVERS')])
		cache_config.setdefault('CACHE_MEMCACHED_USERNAME',
			environ.get('MEMCACHIER_USERNAME'))
		cache_config.setdefault('CACHE_MEMCACHED_PASSWORD',
			environ.get('MEMCACHIER_PASSWORD'))
	elif app.config['DEBUG_MEMCACHE']:
		cache_config = {
			'CACHE_TYPE': 'memcached',
			'CACHE_MEMCACHED_SERVERS': [environ.get('MEMCACHE_SERVERS')]}
	else:
		cache_config['CACHE_TYPE'] = 'simple'

	cache.init_app(app, config=cache_config)

	@app.route('/')
	def home():
		return redirect(url_for('api'))

	@app.route('/api/')
	@app.route('%s/' % app.config['API_URL_PREFIX'])
	def api():
		return 'Welcome to the Ebay Search API!'

	@app.route('/api/search/')
	@app.route('%s/search/' % app.config['API_URL_PREFIX'])
	@cache.cached(timeout=search_cache_timeout)
	def search():
		args = request.args.to_dict()
		region = args.get('region', 'US')
		finding = Finding(region=region)

		kwargs = {
			'paginationInput': {'entriesPerPage': 100, 'pageNumber': 1},
			'sortOrder': 'EndTimeSoonest',
		}

		kwargs.update(args)

		try:
			response = finding.search(**kwargs)
			result = finding.parse(response)
			status = 200
		except ConnectionError as err:
			result = err.message
			status = 500

		return jsonify({'objects': result}, status)

	@app.route('/api/category/<name>/subcategories/')
	@app.route('%s/category/<name>/subcategories/' % app.config['API_URL_PREFIX'])
	def sub_category(name):
		name = name.lower()
		args = request.args.to_dict()
		region = args.get('region', 'US')
		trading = Trading(region=region)
		cat_array = trading.get_categories().CategoryArray
		response = cat_array.Category
		categories = trading.parse(response)
		lookup = trading.make_lookup(categories)

		try:
			cat_id = lookup[unquote(name)]['id']
			hier_array = trading.get_hierarchy(cat_id).CategoryArray
			response = hier_array.Category
			result = trading.parse(response)
			status = 200
		except KeyError:
			result = "Category %s doesn't exist" % name
			status = 500

		return jsonify({'objects': result}, status)

	@app.route('/api/item/<id>/')
	@app.route('%s/item/<id>/' % app.config['API_URL_PREFIX'])
	def item(id):
		args = request.args.to_dict()
		region = args.get('region', 'US')

		try:
			trading = Trading(region=region)
			response = trading.get_item(id)
			result = response.Item
			status = 200
		except ConnectionError as err:
			result = err.message
			status = 500

		return jsonify({'objects': result}, status)

	@app.route('/api/reset/')
	@app.route('%s/reset/' % app.config['API_URL_PREFIX'])
	def reset():
		cache.clear()
		return jsonify({'objects': "Caches reset"})

	@app.after_request
	def add_cors_header(response):
		return corsify(response, app.config['API_METHODS'])

	return app


class CustomEncoder(JSONEncoder):
	def default(self, obj):
		if set(['quantize', 'year']).intersection(dir(obj)):
			return str(obj)
		elif set(['next', 'union']).intersection(dir(obj)):
			return list(obj)
		return JSONEncoder.default(self, obj)
