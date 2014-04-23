#!/usr/bin/env python
import os.path as p

from pprint import pprint
from json import dumps
from requests import get, post

from flask import current_app as app, url_for
from flask.ext.script import Manager
from app import create_app

manager = Manager(create_app)
manager.add_option(
	'-m', '--cfgmode', dest='config_mode', default='Development')
manager.add_option('-f', '--cfgfile', dest='config_file', type=p.abspath)


@manager.command
def checkstage():
	"""Checks staged with git pre-commit hook"""

	path = p.join(p.dirname(__file__), 'app', 'tests', 'test.sh')
	cmd = "sh %s" % path
	return call(cmd, shell=True)


@manager.command
def runtests():
	"""Checks staged with git pre-commit hook"""

	cmd = 'nosetests -xv'
	return call(cmd, shell=True)


if __name__ == '__main__':
	manager.run()
