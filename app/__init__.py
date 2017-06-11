# -*- coding: utf-8 -*-
"""
    app
    ~~~

    Provides the flask application

    ###########################################################################
    # WARNING: if running on a a staging server, you MUST set the 'STAGE' env
    # heroku config:set STAGE=true --remote staging
    ###########################################################################
"""
from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import config

from os import getenv
from json import dumps
from functools import partial

from flask import Flask, send_from_directory, render_template
from flask_caching import Cache
from flask_compress import Compress
from flask_cors import CORS
from flask_sslify import SSLify

from app.frs import Swaggerify
from app.helper import gen_tables

from builtins import *  # noqa  # pylint: disable=unused-import

__version__ = '1.5.2'

__title__ = 'eBay Search API'
__package_name__ = 'ebay-search-api'
__author__ = 'Reuben Cummings'
__description__ = 'RESTful API for searching eBay sites'
__email__ = 'reubano@gmail.com'
__license__ = 'MIT'
__copyright__ = 'Copyright 2017 Reuben Cummings'

cache = Cache()
compress = Compress()
swag = Swaggerify()

API_RESPONSE = [{'name': 'objects', 'desc': 'message', 'type': 'str'}]
SEARCH_RESULT = [
    {'name': 'buy_now_price', 'desc': 'Buy It Now price', 'type': 'float'},
    {
        'name': 'buy_now_price_and_shipping',
        'desc': 'Buy It Now plus shipping cost', 'type': 'float'},
    {'name': 'condition', 'desc': 'Item condition', 'type': 'str'},
    {'name': 'end_date', 'desc': 'End date', 'type': 'date'},
    {'name': 'end_date_time', 'desc': 'End datetime in seconds', 'type': 'int'},
    {'name': 'end_time', 'desc': 'End time', 'type': 'time'},
    {'name': 'id', 'desc': 'Item ID', 'type': 'int'},
    {'name': 'item_type', 'desc': 'Item type', 'type': 'str'},
    {'name': 'price', 'desc': 'Item price', 'type': 'float'},
    {
        'name': 'price_and_shipping', 'desc': 'Item price plus shipping cost',
        'type': 'float'},
    {'name': 'shipping', 'desc': 'Item shipping cost', 'type': 'float'},
    {'name': 'title', 'desc': 'Item title', 'type': 'str'},
    {'name': 'url', 'desc': 'Item url', 'type': 'str'}]

SHIP_RESULT = [
    {'name': 'actual_shipping', 'desc': 'Shipping cost', 'type': 'float'},
    {
        'name': 'actual_shipping_currency',
        'desc': 'Accepted shipping currency', 'type': 'str'},
    {
        'name': 'actual_shipping_service', 'desc': 'Shipping service',
        'type': 'str'},
    {'name': 'actual_shipping_type', 'desc': 'Shipping type', 'type': 'str'},
    {'name': 'item_id', 'desc': 'Item ID', 'type': 'int'}]

CAT_RESULT = [
    {'name': 'category', 'type': 'str'},
    {'name': 'country', 'type': 'str'},
    {'name': 'id', 'type': 'int'},
    {'name': 'level', 'type': 'int'},
    {'name': 'parent_id', 'type': 'int'}]

ITEM_RESULT = [
    {'name': 'AutoPay', 'type': 'bool'},
    {'name': 'BuyItNowPrice', 'type': 'object'},
    {'name': 'BuyerGuaranteePrice', 'type': 'object'},
    {'name': 'BuyerProtection', 'type': 'str'},
    {'name': 'BuyerResponsibleForShipping', 'type': 'bool'},
    {'name': 'ConditionDisplayName', 'type': 'str'},
    {'name': 'ConditionID', 'type': 'int'},
    {'name': 'Country', 'type': 'str'},
    {'name': 'Currency', 'type': 'str'},
    {'name': 'DispatchTimeMax', 'type': 'int'},
    {'name': 'GetItFast', 'type': 'bool'},
    {'name': 'GiftIcon', 'type': 'int'},
    {'name': 'HideFromSearch', 'type': 'bool'},
    {'name': 'HitCount', 'type': 'int'},
    {'name': 'HitCounter', 'type': 'str'},
    {'name': 'IntangibleItem', 'type': 'bool'},
    {'name': 'ItemID', 'type': 'int'},
    {'name': 'ListingDetails', 'type': 'object'},
    {'name': 'ListingDuration', 'type': 'str'},
    {'name': 'ListingType', 'type': 'str'},
    {'name': 'Location', 'type': 'str'},
    {'name': 'LocationDefaulted', 'type': 'bool'},
    {'name': 'PaymentMethods', 'type': 'str'},
    {'name': 'PictureDetails', 'type': 'object'},
    {'name': 'PostCheckoutExperienceEnabled', 'type': 'bool'},
    {'name': 'PostalCode', 'type': 'str'},
    {'name': 'PrimaryCategory', 'type': 'object'},
    {'name': 'PrivateListing', 'type': 'bool'},
    {'name': 'ProductListingDetails', 'type': 'object'},
    {'name': 'ProxyItem', 'type': 'bool'},
    {'name': 'Quantity', 'type': 'int'},
    {'name': 'RelistParentID', 'type': 'int'},
    {'name': 'ReturnPolicy', 'type': 'object'},
    {'name': 'ReviseStatus', 'type': 'object'},
    {'name': 'Seller', 'type': 'object'},
    {'name': 'SellingStatus', 'type': 'object'},
    {'name': 'ShipToLocations', 'type': 'str'},
    {'name': 'ShippingDetails', 'type': 'object'},
    {'name': 'ShippingPackageDetails', 'type': 'object'},
    {'name': 'Site', 'type': 'str'},
    {'name': 'StartPrice', 'type': 'object'},
    {'name': 'Storefront', 'type': 'object'},
    {'name': 'TimeLeft', 'type': 'str'},
    {'name': 'Title', 'type': 'str'},
    {'name': 'TopRatedListing', 'type': 'bool'},
    {'name': 'eBayPlus', 'type': 'bool'},
    {'name': 'eBayPlusEligible', 'type': 'bool'}]


def create_app(config_mode=None, config_file=None):
    # Create webapp instance
    app = Flask(__name__)
    app.register_blueprint(blueprint)
    CORS(app)
    compress.init_app(app)
    cache_config = {}

    if config_mode:
        app.config.from_object(getattr(config, config_mode))
    elif config_file:
        app.config.from_pyfile(config_file)
    else:
        app.config.from_envvar('APP_SETTINGS', silent=True)

    if app.config.get('SERVER_NAME'):
        SSLify(app)

    if app.config['HEROKU']:
        cache_config['CACHE_TYPE'] = 'saslmemcached'
        cache_config['CACHE_MEMCACHED_SERVERS'] = [getenv('MEMCACHIER_SERVERS')]
        cache_config['CACHE_MEMCACHED_USERNAME'] = getenv('MEMCACHIER_USERNAME')
        cache_config['CACHE_MEMCACHED_PASSWORD'] = getenv('MEMCACHIER_PASSWORD')
    elif app.config['DEBUG_MEMCACHE']:
        cache_config['CACHE_TYPE'] = 'memcached'
        cache_config['CACHE_MEMCACHED_SERVERS'] = [getenv('MEMCACHE_SERVERS')]
    else:
        cache_config['CACHE_TYPE'] = 'simple'

    cache.init_app(app, config=cache_config)

    skwargs = {
        'name': app.config['APP_NAME'], 'version': __version__,
        'description': __description__}

    swag.init_app(app, **skwargs)

    swag_config = {
        'dom_id': '#swagger-ui',
        'url': app.config['SWAGGER_JSON'],
        'layout': 'StandaloneLayout'}

    context = {
        'base_url': app.config['SWAGGER_URL'],
        'app_name': app.config['APP_NAME'],
        'config_json': dumps(swag_config)}

    @app.route('/')
    @app.route('/<path>/')
    @app.route('{API_URL_PREFIX}/'.format(**app.config))
    @app.route('{API_URL_PREFIX}/<path>/'.format(**app.config))
    def home(path=None):
        if not path or path == 'index.html':
            return render_template('index.html', **context)
        else:
            return send_from_directory('static', path)

    exclude = app.config['SWAGGER_EXCLUDE_COLUMNS']
    create_docs = partial(swag.create_docs, exclude_columns=exclude)
    create_defs = partial(create_docs, skip_path=True)

    create_defs({'columns': SEARCH_RESULT, 'name': 'search_result'})
    create_defs({'columns': SHIP_RESULT, 'name': 'ship_result'})
    create_defs({'columns': ITEM_RESULT, 'name': 'item_result'})
    create_defs({'columns': CAT_RESULT, 'name': 'category_result'})
    create_defs({'columns': CAT_RESULT, 'name': 'sub_category_result'})

    with app.app_context():
        rule_map = app.url_map._rules_by_endpoint

        for table in gen_tables(app.view_functions, rule_map, **app.config):
            create_docs(table)

    return app

# put at bottom to avoid circular reference errors
from app.views import blueprint  # noqa
