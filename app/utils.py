# -*- coding: utf-8 -*-
"""
    app.utils
    ~~~~~~~~~

    Provides misc utility functions
"""
from __future__ import (
    absolute_import, division, print_function, unicode_literals)

from json import loads, dumps

try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

try:
    from time import monotonic
except ImportError:
    from time import time as monotonic

from ast import literal_eval
from datetime import datetime as dt, timedelta

from functools import wraps

import requests
import pygogo as gogo

from flask import make_response, request
from dateutil.relativedelta import relativedelta
from http.client import responses
from meza import fntools as ft

from app import cache

from builtins import *  # noqa  # pylint: disable=unused-import

logger = gogo.Gogo(__name__, monolog=True).logger

# https://baconipsum.com/?paras=5&type=meat-and-filler&make-it-spicy=1
BACON_IPSUM = [
    'Spicy jalapeno bacon ipsum dolor amet prosciutto bresaola ball chicken.',
    'Alcatra officia enim, labore eiusmod kielbasa pancetta turducken.',
    'Aliqua pork loin picanha turducken proident.',
    'Qui meatloaf fatback cillum meatball tail duis short ribs commodo.',
    'Ball tip non salami meatloaf in, tri-tip dolor filet mignon.',
    'Leberkas tenderloin ball tip sirloin, ad culpa drumstick laborum.',
    'Porchetta eiusmod pastrami voluptate pig kielbasa jowl occaecat.',
    'Shank landjaeger andouille ea, in drumstick prosciutto bacon excepteur.',
    'Prosciutto alcatra minim elit, fugiat ut sausage beef tri-tip.',
    'Non culpa irure magna turkey short loin filet mignon.',
    'Chuck prosciutto laborum cupidatat shank pariatur ribeye in elit tempor.',
    'Dolor pig ham hock officia picanha chuck sed shankle dolore.',
    'Short ribs non ea beef ball tip, shoulder dolore.',
    'Tri-tip leberkas excepteur nisi sunt turducken deserunt.',
    'Turducken picanha doner, eiusmod short loin et fatback short ribs bacon.',
    'Tongue magna esse brisket cupim fugiat adipisicing aute veniam picanha.',
    'Pastrami hamburger prosciutto labore veniam pork loin voluptate.',
    'Venison excepteur pork ground round sausage est mollit.',
    'Biltong sunt bresaola porchetta excepteur porchetta.',
    'Consequat alcatra jowl commodo, anim incididunt officia beef tail.',
    'Ground round deserunt in, tri-tip kielbasa ball tip ex.',
    'Labore est cow nulla kielbasa, turducken ham adipisicing mollit kevin.',
    'Cillum in shank leberkas occaecat ea andouille.'
]


def jsonify(status=200, indent=2, sort_keys=True, **kwargs):
    """ Creates a jsonified response. Necessary because the default
    flask.jsonify doesn't correctly handle sets, dates, or iterators

    Args:
        status (int): The status code (default: 200).
        indent (int): Number of spaces to indent (default: 2).
        sort_keys (bool): Sort response dict by keys (default: True).
        kwargs (dict): The response to jsonify.

    Returns:
        (obj): Flask response
    """
    options = {'indent': indent, 'sort_keys': sort_keys, 'ensure_ascii': False}
    kwargs['status'] = responses[status]
    json_str = dumps(kwargs, cls=ft.CustomEncoder, **options)
    response = make_response((json_str, status))
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    response.headers['mimetype'] = 'application/json'
    response.last_modified = dt.utcnow()
    response.add_etag()
    return response


def parse(string):
    """ Parses a string into an equivalent Python object

    Args:
        string (str): The string to parse

    Returns:
        (obj): equivalent Python object

    Examples:
        >>> parse('True')
        True
        >>> parse('{"key": "value"}')
        {'key': 'value'}
    """
    if string.lower() in {'true', 'false'}:
        return loads(string.lower())
    else:
        try:
            return literal_eval(string)
        except (ValueError, SyntaxError):
            return string


def make_cache_key(*args, **kwargs):
    """ Creates a memcache key for a url and its query parameters

    Returns:
        (obj): Flask request url
    """
    return request.url


def fmt_elapsed(elapsed):
    """ Generates a human readable representation of elapsed time.

    Args:
        elapsed (float): Number of elapsed seconds.

    Yields:
        (str): Elapsed time value and unit

    Examples:
        >>> formatted = fmt_elapsed(1000)
        >>> next(formatted) == '16 minutes'
        True
        >>> next(formatted) == '40 seconds'
        True
    """
    # http://stackoverflow.com/a/11157649/408556
    # http://stackoverflow.com/a/25823885/408556
    attrs = ['years', 'months', 'days', 'hours', 'minutes', 'seconds']
    delta = relativedelta(seconds=elapsed)

    for attr in attrs:
        value = getattr(delta, attr)

        if value:
            yield '%d %s' % (value, attr[:-1] if value == 1 else attr)


def get(url):
    start = monotonic()
    r = requests.get(url)

    try:
        resp = r.json()
    except JSONDecodeError as err:
        resp = {'status': 500, 'message': err}
    else:
        resp['status'] = r.status_code

    elapsed_time = ', '.join(fmt_elapsed(monotonic() - start))
    resp['objects'] = {}
    resp['objects']['elapsed_time'] = elapsed_time
    return resp


# https://gist.github.com/glenrobertson/954da3acec84606885f5
# http://stackoverflow.com/a/23115561/408556
# https://github.com/pallets/flask/issues/637
def cache_header(max_age, **ckwargs):
    """
    Add Flask cache response headers based on max_age in seconds.

    If max_age is 0, caching will be disabled.
    Otherwise, caching headers are set to expire in now + max_age seconds
    If round_to_minute is True, then it will always expire at the start of a
    minute (seconds = 0)

    Example usage:

    @app.route('/map')
    @cache_header(60)
    def index():
        return render_template('index.html')

    """
    def decorator(view):
        f = cache.cached(max_age, **ckwargs)(view)

        @wraps(f)
        def wrapper(*args, **wkwargs):
            response = f(*args, **wkwargs)
            response.cache_control.max_age = max_age

            if max_age:
                response.cache_control.public = True
                extra = timedelta(seconds=max_age)
                response.expires = response.last_modified + extra
            else:
                response.headers['Pragma'] = 'no-cache'
                response.cache_control.must_revalidate = True
                response.cache_control.no_cache = True
                response.cache_control.no_store = True
                response.expires = '-1'

            return response.make_conditional(request)
        return wrapper

    return decorator
