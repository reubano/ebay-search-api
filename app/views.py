# -*- coding: utf-8 -*-
"""
    app.view
    ~~~~~~~~

    Provides additional api endpoints
"""
from __future__ import (
    absolute_import, division, print_function, unicode_literals)

try:
    from urllib.parse import unquote
except ImportError:
    from urllib import unquote

from random import choice

from ebaysdk.exception import ConnectionError
from flask import Blueprint, request, url_for

from config import Config

from app import cache
from app.api import Trading, Finding, Shopping
from app.utils import make_cache_key, jsonify, BACON_IPSUM, cache_header, parse

from builtins import *  # noqa  # pylint: disable=unused-import

blueprint = Blueprint('blueprint', __name__)

PREFIX = Config.API_URL_PREFIX
CACHE_TIMEOUT = Config.CACHE_TIMEOUT
CAT_CACHE_TIMEOUT = Config.CAT_CACHE_TIMEOUT
SUB_CAT_CACHE_TIMEOUT = Config.SUB_CAT_CACHE_TIMEOUT


# API routes
@blueprint.route('/search/')
@blueprint.route('/api/search/')
@blueprint.route('{}/search/'.format(PREFIX))
@cache_header(CACHE_TIMEOUT, key_prefix=make_cache_key)
def search():
    """Perform an eBay site search

    Kwargs:
        q (str): The search term(s) (either this or the 'cid'
            parameter is required)

        cid (int): ID of the category to display (either this or the 'q'
            parameter is required)

        country (str): eBay country (one of ['US', 'UK'], default: 'US')
        verb (str): The type of search to perform (one of ['findCompletedItems',
            'findItemsAdvanced', 'findItemsByCategory', 'findItemsByKeywords',
            'findItemsByProduct', 'findItemsIneBayStores', 'getHistograms'],
            default: 'findItemsAdvanced')

        sort_order (str): Sort order (one of ['BestMatch',
            'CurrentPriceHighest', 'DistanceNearest', 'EndTimeSoonest',
            'PricePlusShippingHighest', 'PricePlusShippingLowest',
            'StartTimeNewest'], default: 'EndTimeSoonest')

        limit (int): Number of results to return (default: 10)
        page (int): The results page to view (default: 1)
    """
    kwargs = {k: parse(v) for k, v in request.args.to_dict().items()}
    query = kwargs.pop('q', None)
    cid = kwargs.pop('cid', None)

    if query:
        kwargs.setdefault('keywords', query)

    if cid:
        kwargs.setdefault('categoryId', cid)

    kwargs.setdefault('sortOrder', kwargs.pop('sort_order', 'EndTimeSoonest'))
    kwargs.setdefault('verb', 'findItemsAdvanced')
    limit = kwargs.pop('limit', 10)
    page = kwargs.pop('page', 1)
    finding = Finding(**kwargs)

    options = {'paginationInput': {'entriesPerPage': limit, 'pageNumber': page}}
    options.update(kwargs)

    try:
        response = finding.search(options)
    except ConnectionError as err:
        result = str(err)
        status = 500
    else:
        result = finding.parse(response)
        status = 200

    return jsonify(status, objects=result)


@blueprint.route('/ship/<item_id>/')
@blueprint.route('/api/ship/<item_id>/')
@blueprint.route('{}/ship/<item_id>/'.format(PREFIX))
@cache_header(CACHE_TIMEOUT, key_prefix=make_cache_key)
def ship(item_id):
    """Calculate an item's shipping cost

    Args:
        item_id (str): ID of item to ship

    Kwargs:
        country (str): origin country (one of ['US', 'UK'], default: 'US')
        dest (str): destination country (see
            http://www.airlinecodes.co.uk/country.asp for valid codes,
            default: 'US')

        code (str): destination postal code (required if 'dest' is 'US')
        details (bool): include details? (default: False)
        quantity (int): quantity to ship (default: 1)
    """
    kwargs = {k: parse(v) for k, v in request.args.to_dict().items()}
    dest = kwargs.pop('dest', 'US')
    code = kwargs.pop('code', None)
    details = kwargs.pop('details', None)
    quantity = kwargs.pop('quantity', None)
    options = {
        'ItemID': item_id, 'MessageID': item_id, 'DestinationCountryCode': dest}

    if code:
        options['DestinationPostalCode'] = code

    if details:
        options['IncludeDetails'] = details

    if quantity:
        options['QuantitySold'] = quantity

    options.update(kwargs)
    shopping = Shopping(**kwargs)

    try:
        response = shopping.search(options)
    except ConnectionError as err:
        result = str(err)
        status = 500
    else:
        result = shopping.parse(response)
        status = 200

    return jsonify(status, objects=result)


@cache.memoize(CAT_CACHE_TIMEOUT)
def get_categories(**kwargs):
    trading = Trading(**kwargs)
    response = trading.get_categories()
    return trading.parse(response.CategoryArray.Category)


@blueprint.route('/category/')
@blueprint.route('/api/category/')
@blueprint.route('{}/category/'.format(PREFIX))
@cache_header(CAT_CACHE_TIMEOUT, key_prefix=make_cache_key)
def category():
    """Get all eBay categories

    Kwargs:
        country (str): eBay country (one of ['US', 'UK'], default: 'US')
    """
    kwargs = {k: parse(v) for k, v in request.args.to_dict().items()}
    return jsonify(objects=get_categories(**kwargs))


@blueprint.route('/category/<int:cid>/')
@blueprint.route('/category/<name>/')
@blueprint.route('/api/category/<name>/subcategories/')
@blueprint.route('{}/category/<int:cid>/'.format(PREFIX))
@blueprint.route('{}/category/<name>/'.format(PREFIX))
@blueprint.route('{}/category/<name>/subcategories/'.format(PREFIX))
@cache_header(SUB_CAT_CACHE_TIMEOUT, key_prefix=make_cache_key)
def sub_category(name=None, cid=None):
    """Get all subcategories of a given eBay category

    Args:
        cid (int): eBay category ID, e.g., 267
        name (str): eBay category name, e.g., 'Books'

    Kwargs:
        country (str): eBay country (one of ['US', 'UK'], default: 'US')
    """
    if not (name or cid):
        return jsonify(400, objects="Either 'name' or 'id' must be provided")

    kwargs = {k: parse(v) for k, v in request.args.to_dict().items()}
    trading = Trading(**kwargs)
    url = url_for('blueprint.category', _external=True)
    msg = "Category {} doesn't exist. View {} to see valid categories."

    if name and not cid:
        categories = get_categories(**kwargs)
        lookup = trading.make_lookup(categories)

        try:
            cid = lookup[unquote(name.lower())]['id']
        except KeyError:
            pass

    response = trading.get_hierarchy(cid) if cid else None

    try:
        result = trading.parse(response.CategoryArray.Category)
    except AttributeError:
        result = msg.format(name, url)
        status = 404
    except TypeError:
        result = msg.format(cid, url)
        status = 404
    else:
        status = 200

    return jsonify(status, objects=result)


@blueprint.route('/item/<item_id>/')
@blueprint.route('/api/item/<item_id>/')
@blueprint.route('{}/item/<item_id>/'.format(PREFIX))
@cache_header(CACHE_TIMEOUT, key_prefix=make_cache_key)
def item(item_id):
    """Get an item's details

    Args:
        item_id (str): item ID

    Kwargs:
        country (str): eBay country (one of ['US', 'UK'], default: 'US')
    """
    kwargs = {k: parse(v) for k, v in request.args.to_dict().items()}

    try:
        trading = Trading(**kwargs)
    except ConnectionError as err:
        result = str(err)
        status = 500
    else:
        response = trading.get_item(item_id)
        result = response['Item']
        status = 200

    return jsonify(status, objects=result)


@blueprint.route('/lorem/')
@blueprint.route('/api/lorem/')
@blueprint.route('{}/lorem/'.format(PREFIX))
@cache_header(CACHE_TIMEOUT, key_prefix=make_cache_key)
def lorem():
    """Get a random 'bacon ipsum' sentence

    Return:
        str: A bacon ipsum sentence
    """
    return jsonify(objects=choice(BACON_IPSUM))


@blueprint.route('/cache/', methods=['DELETE'])
@blueprint.route('/cache/<base>/', methods=['DELETE'])
@blueprint.route('/api/cache/', methods=['DELETE'])
@blueprint.route('/api/cache/<base>/', methods=['DELETE'])
@blueprint.route('{}/cache/'.format(PREFIX), methods=['DELETE'])
@blueprint.route('{}/cache/<base>/'.format(PREFIX), methods=['DELETE'])
def cached(base=None):
    """Reset all caches or remove a cached url by base

    Args:
        base (str): The base of the cached url to remove, e.g., 'lorem'

    Return:
        str: Response message
    """
    if base:
        url = request.url.replace('delete/', '')
        msg = 'Cached URL "{}" deleted!'.format(url)
        cache.delete(url)
    else:
        msg = 'Caches reset!'
        cache.clear()

    return jsonify(status=204, objects=msg)
