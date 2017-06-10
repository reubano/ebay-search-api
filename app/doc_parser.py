# -*- coding: utf-8 -*-

from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import pygogo as gogo

from docutils.core import publish_doctree
from xml.etree.ElementTree import fromstring
from sphinxcontrib.napoleon.docstring import GoogleDocstring

from builtins import *  # noqa  # pylint: disable=unused-import

logger = gogo.Gogo(__name__, monolog=True).logger


class CustomDocstring(GoogleDocstring):
    def __init__(self, *args, **kwargs):
        self._sections = {
            'args': self._parse_parameters_section,
            'attributes': self._parse_attributes_section,
            'examples': self._parse_examples_section,
            'kwargs': self._parse_keyword_arguments_section,
            'notes': self._parse_notes_section,
            'returns': self._parse_returns_section,
            'raises': self._parse_raises_section,
            'references': self._parse_references_section,
            'see also': self._parse_see_also_section,
            'todo': self._parse_todo_section,
            'warns': self._parse_warns_section,
            'yields': self._parse_yields_section,
        }

        super(CustomDocstring, self).__init__(*args, **kwargs)


def parse_docblock(source, google_style=True):
    '''
    Args:
        source (str): docblock
        google_style (bool): Google style docblocks

    Return:
        class: ElementTree.Element

    Examples:
        >>> source1 = """Some text ...
        ...
        ... :foo: bar
        ...
        ... Some text ...
        ... """
        ...
        >>> source2 = """One line summary.
        ...
        ... Extended description.
        ...
        ... Args:
        ...     arg1 (int): Description of `arg1`
        ...     arg2 (str): Description of `arg2`
        ...
        ... Returns:
        ...     str: Description of return value.
        ... """
        ...
        >>> parse_docblock(source1)  # doctest: +ELLIPSIS
        <Element 'document' at 0x...>
        >>> tree = parse_docblock(source2)
        >>> next(tree.iter(tag='field'))  # doctest: +ELLIPSIS
        <Element 'field' at 0x...>
    '''
    if google_style:
        docstring = CustomDocstring(source)
        doctree = publish_doctree(str(docstring))
    else:
        doctree = publish_doctree(source)

    dom = doctree.asdom()
    xml = dom.toxml()
    # logger.debug(dom.toprettyxml(indent='  '))
    return fromstring(xml)


def gen_fields(tree, arguments=None):  # noqa  # pylint: disable=too-complex
    '''
    Args:
        tree (class): ElementTree.Element

    Kwargs:
        arguments (Seq[str]): Allowed arguments

    Yields:
        dict: item

    Examples:
        >>> source1 = """Some text ...
        ...
        ... :foo: bar
        ...
        ... Some text ...
        ... """
        ...
        >>> source2 = """One line summary.
        ...
        ... Extended description.
        ...
        ... Args:
        ...     arg1 (int): Description of `arg1`
        ...     arg2 (str): Description of `arg2`
        ...
        ... Returns:
        ...     str: Description of return value.
        ... """
        ...
        >>> source3 = """A source that fetches and parses a csv file
        ...
        ... Args:
        ...     item (dict): The entry to process
        ...
        ... Kwargs:
        ...     conf (dict): The pipe configuration.
        ...
        ... Yields:
        ...     dict: item
        ... """
        >>> tree = parse_docblock(source1)
        >>> next(gen_fields(tree)) == {
        ...     'name': 'foo', 'desc': 'bar', 'type': 'n/a', 'kind': 'n/a'}
        True
        >>> tree = parse_docblock(source2)
        >>> fields = gen_fields(tree)
        >>> next(fields) == {
        ...     'name': 'arg1', 'desc': 'Description of arg1',
        ...     'type': 'int', 'kind': 'type'}
        True
        >>> next(fields) == {
        ...     'name': 'arg2', 'desc': 'Description of arg2',
        ...     'type': 'str', 'kind': 'type'}
        True
        >>> next(fields) == {
        ...     'name': 'rvalue', 'desc': 'Description of return value.',
        ...     'type': 'str', 'kind': 'result'}
        True
        >>> tree = parse_docblock(source3)
        >>> fields = gen_fields(tree)
        >>> next(fields) == {
        ...     'name': 'item', 'desc': 'The entry to process',
        ...     'type': 'dict', 'kind': 'type'}
        True
        >>> next(fields) == {
        ...     'name': 'conf', 'desc': 'The pipe configuration.',
        ...     'type': 'dict', 'kind': 'kwtype'}
        True
        >>> next(fields) == {
        ...     'name': 'yvalue', 'desc': 'item', 'type': 'dict',
        ... 'kind': 'result'}
        True
    '''
    prev_arg = None

    if arguments is not None:
        arguments = set(arguments)

    for field in tree.iter(tag='field'):
        name = next(field.iter(tag='field_name')).text
        _body = next(field.iter(tag='field_body'))
        body = ''.join(_body.itertext())

        if ' ' in name:
            kind, arg = name.split(' ')
        else:
            kind, arg = 'n/a', name.lower()

        if arguments is not None and kind == 'type' and arg not in arguments:
            continue

        if (kind in {'param', 'keyword'}) or (arg == 'returns'):
            desc = body
        elif arg == 'yields':
            desc = ' -- '.join(body.split(' -- ')[1:])
        elif (kind in {'type', 'kwtype'}) or (arg == 'rtype'):
            arg_type = body
        else:
            desc, arg_type = body, kind

        if arg in {'returns', 'rtype'}:
            kind, arg = 'result', 'rvalue'

        if arg == 'yields':
            kind, arg = 'result', 'yvalue'
        elif kind != 'n/a' and prev_arg != arg:
            prev_arg = arg
            continue

        yield {'name': arg, 'desc': desc, 'type': arg_type, 'kind': kind}
