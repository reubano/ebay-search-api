# -*- coding: utf-8 -*-
"""
	app
	~~~~~~~~~~~~~~

	Provides the flask application
"""

from __future__ import print_function

import config

from json import JSONEncoder, dumps
from api import Amazon
from pprint import pprint
from flask import Flask, redirect, url_for, request, make_response


def jsonify(result):
	response = make_response(dumps(result, cls=CustomEncoder))
	response.headers['Content-Type'] = 'application/json; charset=utf-8'
	response.headers['mimetype'] = 'application/json'
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
	amazon_us = Amazon(region='US')
	amazon_uk = Amazon(region='UK')

	def get_amazon(region):
		switch = {'US': amazon_us, 'UK': amazon_uk,}
		return switch.get(region)

	if config_mode:
		app.config.from_object(getattr(config, config_mode))
	elif config_file:
		app.config.from_pyfile(config_file)
	else:
		app.config.from_envvar('APP_SETTINGS', silent=True)

	@app.route('/')
	def home():
		return redirect(url_for('api'))

	@app.route('/api/')
	@app.route('%s/' % app.config['API_URL_PREFIX'])
	def api():
		return 'Welcome to the Amazon Search API!'

	@app.route('/api/search/')
	@app.route('/api/search/<limit>/')
	@app.route('/api/search/<limit>/<region>/')
	@app.route('%s/search/' % app.config['API_URL_PREFIX'])
	@app.route('%s/search/<limit>/' % app.config['API_URL_PREFIX'])
	@app.route('%s/search/<limit>/<region>/' % app.config['API_URL_PREFIX'])
	def search(limit=1, region='US'):
		print(request.args)
		amazon = get_amazon(region)
		keywords = request.args.get('keywords')

		if not keywords:
			items = "Please enter a 'keywords' parameter"
		else:
			kwargs = {
				'Keywords': keywords,
				'Condition': request.args.get('condition', 'New'),
				'SearchIndex': request.args.get('search_index', 'All'),
				'ResponseGroup': request.args.get('response_group', 'Medium'),
			}

			response = amazon.search_n(limit, **kwargs)
			items = amazon.parse(response)

		return jsonify({'objects': items})

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
