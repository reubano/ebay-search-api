try:
	from setuptools import setup, find_packages
except ImportError:
	from distutils.core import setup, find_packages


with open('../requirements.txt') as file:
	requirements = file.read()


config = {
	'name': 'ebay-search-api',
	'description': 'RESTful API for searching eBay sites',
	'long_description': open('README.rst', 'rt').read(),
	'author': 'Reuben Cummings',
	'author_email': 'reubano@gmail.com',
	'version': '1.1.0',
	'install_requires': requirements.split('\n'),
	'classifiers': [
		'Development Status :: 4 - Beta',
		'License :: OSI Approved :: The MIT License (MIT)',
		'Environment :: Web Environment',
		'Intended Audience :: Developers',
		'Operating System :: MacOS :: MacOS X',
		'Operating System :: Microsoft :: Windows',
		'Operating System :: Microsoft :: POSIX',
		'Framework :: Flask',
		'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
		'Topic :: Internet :: WWW/HTTP :: WSGI :: Server',
	],
	'keywords': 'ebay-api, web-service',
	'packages': find_packages(),
	'zip_safe': False,
	'license': 'MIT',
	'platforms': ['MacOS X', 'Windows', 'Linux'],
	'include_package_data': True,
}

setup(**config)
