# -*- coding: utf-8 -*-
"""
    app.helper
    ~~~~~~~~~~

    Provides misc helper functions
"""
from __future__ import (
    absolute_import, division, print_function, unicode_literals)

from inspect import getdoc
from app.doc_parser import gen_fields, parse_docblock

from builtins import *  # noqa  # pylint: disable=unused-import


def gen_tables(view_functions, rule_map, SWAGGER_EXCLUDE_ROUTES=None, **kwargs):
    exclude_routes = SWAGGER_EXCLUDE_ROUTES or {}
    exclude_methods = {'OPTIONS', 'HEAD'}
    other = {'cached', 'lorem'}

    ftypes = {
        'search': 'dict', 'ship': 'wrapped', 'item': 'wrapped',
        'category': 'list', 'sub_category': 'list'}

    func_filterer = lambda item: item[0] not in exclude_routes
    rule_filterer = lambda rule: 'api' not in str(rule)

    for func_name, endpoint in filter(func_filterer, view_functions.items()):
        for rule in filter(rule_filterer, rule_map[func_name]):
            methods = set(rule.methods)

            if func_name.startswith('blueprint'):
                func_name = '.'.join(func_name.split('.')[1:])

            for method in methods.difference(exclude_methods):
                if hasattr(endpoint, 'view_class'):
                    func = getattr(endpoint.view_class, method.lower())
                else:
                    func = endpoint

                source = getdoc(func)

                if source:
                    tree = parse_docblock(source)

                    yield {
                        'columns': list(gen_fields(tree, rule.arguments)),
                        'name': func_name,
                        'method': method,
                        'desc': next(tree.iter(tag='paragraph')).text,
                        'tag': 'Other' if func_name in other else 'Amazon',
                        'rtype': '{}_result'.format(func_name),
                        'ftype': ftypes.get(func_name, 'simple')}
