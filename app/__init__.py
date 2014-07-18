# -*- coding: utf-8 -*-
"""
	app
	~~~~~~~~~~~~~~

	Provides the flask application
"""
from __future__ import absolute_import
from future.builtins import str

try:
	from urllib.parse import unquote
except ImportError:
	from urllib import unquote

import config

from ast import literal_eval
from os import getenv
from json import JSONEncoder, dumps, loads
from .api import Trading, Finding, Shopping
from ebaysdk.exception import ConnectionError
from flask import Flask, redirect, url_for, request, make_response
from flask.ext.cache import Cache

cache = Cache()
search_cache_timeout = 60 * 60 * 1  # hours (in seconds)
ship_cache_timeout = 60 * 60 * 1  # hours (in seconds)
usage_cache_timeout = 60 * 60 * 1  # hours (in seconds)
category_cache_timeout = 60 * 60 * 24 * 7  # days (in seconds)
sub_category_cache_timeout = 60 * 60 * 24 * 1  # days (in seconds)
encoding = 'utf8'


def jsonify(status=200, indent=2, sort_keys=True, **kwargs):
	options = {'indent': indent, 'sort_keys': sort_keys, 'ensure_ascii': False}
	response = make_response(dumps(kwargs, cls=CustomEncoder, **options))
	response.headers['Content-Type'] = 'application/json; charset=utf-8'
	response.headers['mimetype'] = 'application/json'
	response.status_code = status
	return response


def corsify(response, methods):
	base = 'HEAD, OPTIONS'
	headers = 'Origin, X-Requested-With, Content-Type, Accept'

	for m in methods:
		base += ', %s' % m

	response.headers['Access-Control-Allow-Origin'] = '*'
	response.headers['Access-Control-Allow-Methods'] = base
	response.headers['Access-Control-Allow-Headers'] = headers
	response.headers['Access-Control-Allow-Credentials'] = 'true'
	return response


def make_cache_key(*args, **kwargs):
	return request.url


def parse(string):
	string = string.encode(encoding)

	if string.lower() in ('true', 'false'):
		return loads(string.lower())
	else:
		try:
			return literal_eval(string)
		except (ValueError, SyntaxError):
			return string


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
		cache_config['CACHE_MEMCACHED_SERVERS'] = [getenv('MEMCACHIER_SERVERS')]
		cache_config['CACHE_MEMCACHED_USERNAME'] = getenv('MEMCACHIER_USERNAME')
		cache_config['CACHE_MEMCACHED_PASSWORD'] = getenv('MEMCACHIER_PASSWORD')
	elif app.config['DEBUG_MEMCACHE']:
		cache_config['CACHE_TYPE'] = 'memcached'
		cache_config['CACHE_MEMCACHED_SERVERS'] = [getenv('MEMCACHE_SERVERS')]
	else:
		cache_config['CACHE_TYPE'] = 'simple'

	cache.init_app(app, config=cache_config)

	@app.route('/')
	def home():
		return redirect(url_for('api'))

	@app.route('/api/')
	@app.route('%s/' % app.config['API_URL_PREFIX'])
	def api():
		return 'Welcome to the %s!' % app.config['APP_NAME']

	@app.route('/api/usage/')
	@app.route('%s/usage/' % app.config['API_URL_PREFIX'])
	@cache.cached(timeout=usage_cache_timeout, key_prefix=make_cache_key)
	def usage():
		kwargs = {k: parse(v) for k, v in request.args.to_dict().items()}
		finding = Finding(**kwargs)
		options = {}
		options.update(kwargs)

		try:
			response = finding.search(options)
			result = finding.parse(response)
			status = 200
		except ConnectionError as err:
			result = err.message
			status = 500

		return jsonify(status, objects=result)

	@app.route('/api/search/')
	@app.route('%s/search/' % app.config['API_URL_PREFIX'])
	@cache.cached(timeout=search_cache_timeout, key_prefix=make_cache_key)
	def search():
		kwargs = {k: parse(v) for k, v in request.args.to_dict().items()}
		finding = Finding(**kwargs)

		options = {
			'paginationInput': {'entriesPerPage': 100, 'pageNumber': 1},
			'sortOrder': 'EndTimeSoonest',
		}

		options.update(kwargs)

		try:
			response = finding.search(options)
			result = finding.parse(response)
			status = 200
		except ConnectionError as err:
			result = err.message
			status = 500

		return jsonify(status, objects=result)

	@app.route('/api/ship/<id>/')
	@app.route('%s/ship/<id>/' % app.config['API_URL_PREFIX'])
	@cache.cached(timeout=ship_cache_timeout, key_prefix=make_cache_key)
	def ship(id):
		kwargs = {k: parse(v) for k, v in request.args.to_dict().items()}
		shopping = Shopping(**kwargs)
		options = {'ItemID': id, 'MessageID': id, 'DestinationCountryCode': 'US'}
		# see http://www.airlinecodes.co.uk/country.asp for valid codes
		options.update(kwargs)

		try:
			response = shopping.search(options)
			result = shopping.parse(response)
			status = 200
		except ConnectionError as err:
			result = err.message
			status = 500

		return jsonify(status, objects=result)

	@app.route('/api/category/')
	@app.route('%s/category/' % app.config['API_URL_PREFIX'])
	@cache.cached(timeout=category_cache_timeout, key_prefix=make_cache_key)
	def category():
		kwargs = {k: parse(v) for k, v in request.args.to_dict().items()}
		trading = Trading(**kwargs)
		cat_array = trading.get_categories().CategoryArray
		response = cat_array.Category
		return jsonify(objects=trading.parse(response))

	@app.route('/api/category/<name>/subcategories/')
	@app.route('%s/category/<name>/subcategories/' % app.config['API_URL_PREFIX'])
	@cache.cached(timeout=sub_category_cache_timeout, key_prefix=make_cache_key)
	def sub_category(name):
		kwargs = {k: parse(v) for k, v in request.args.to_dict().items()}
		trading = Trading(**kwargs)
		cat_array = trading.get_categories().CategoryArray
		response = cat_array.Category
		categories = trading.parse(response)
		lookup = trading.make_lookup(categories)

		try:
			cat_id = lookup[unquote(name.lower())]['id']
			hier_array = trading.get_hierarchy(cat_id).CategoryArray
			response = hier_array.Category
			result = trading.parse(response)
			status = 200
		except KeyError:
			url = request.url.replace('%s/subcategories/' % name, '')
			msg = "Category %s doesn't exist. View %s to see valid categories."
			result = msg % (name, url)
			status = 500

		return jsonify(status, objects=result)

	@app.route('/api/item/<id>/')
	@app.route('%s/item/<id>/' % app.config['API_URL_PREFIX'])
	@cache.cached(timeout=search_cache_timeout, key_prefix=make_cache_key)
	def item(id):
		kwargs = {k: parse(v) for k, v in request.args.to_dict().items()}

		try:
			trading = Trading(**kwargs)
			response = trading.get_item(id)
			result = response.Item
			status = 200
		except ConnectionError as err:
			result = err.message
			status = 500

		return jsonify(status, objects=result)

	@app.route('/api/reset/')
	@app.route('%s/reset/' % app.config['API_URL_PREFIX'])
	def reset():
		cache.clear()
		return jsonify(objects="Caches reset")

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
