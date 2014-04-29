#!/usr/bin/env python
import os.path as p

from subprocess import call, check_call
from flask.ext.script import Manager
from app import create_app

manager = Manager(create_app)
manager.add_option('-m', '--cfgmode', dest='config_mode', default='Development')
manager.add_option('-f', '--cfgfile', dest='config_file', type=p.abspath)


@manager.command
def checkstage():
	"""Checks staged with git pre-commit hook"""
	path = p.join(p.dirname(__file__), 'app', 'tests', 'test.sh')
	cmd = "sh %s" % path
	return call(cmd, shell=True)


@manager.command
def lint():
	"""Check style with flake8"""
	call('flake8', shell=True)


@manager.command
def test():
	"""Run nosetests"""
	check_call('nosetests -xv', shell=True)


@manager.command
def require():
	"""Create requirements.txt"""
	cmd = 'pip freeze -l | grep -vxFf requirements/dev.txt '
	cmd += '| grep -vxFf requirements/prod.txt '
	cmd += '| grep -vxFf requirements/test.txt '
	cmd += '> requirements/common.txt'
	call(cmd, shell=True)


if __name__ == '__main__':
	manager.run()
