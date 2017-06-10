# -*- coding: utf-8 -*-
"""
    app.tests.test_site
    ~~~~~~~~~~~~~~

    Provides unit tests for the website.
"""

from json import loads

import pytest

from app import create_app

JSON = 'application/json'


def get_json(resp):
    return loads(resp.get_data(as_text=True))


@pytest.fixture
def client(request):
    app = create_app(config_mode='Test')
    client = app.test_client()
    client.prefix = app.config['API_URL_PREFIX']
    return client


def test_home(client):
    r = client.get('{}/'.format(client.prefix))
    assert r.status_code == 200


def test_search(client):
    r = client.get('{}/search/?q=lego'.format(client.prefix))
    assert r.status_code == 200
    results = get_json(r)['objects']['results']
    assert len(results) == 10
