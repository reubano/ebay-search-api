# -*- coding: utf-8 -*-

""" Interface to Amazon API """


import yaml

from urllib2 import HTTPError
from os import getenv
from amazon.api import AmazonAPI


class Amazon(AmazonAPI):
	"""An Amazon search"""

	def __init__(self, key=None, secret=None, tag=None, **kwargs):
		"""
		Initialization method.

		Parameters
		----------
		key : AWS_ACCESS_KEY_ID
		secret : AWS_SECRET_ACCESS_KEY
		tag : AWS_ASSOCIATE_TAG
		region : string
			one of  ['US', 'FR', 'UK', 'CA', 'DE', 'JP', 'IT', 'ES']

		Keyword Arguments
		-----------------
		see bottlenose docs

		Returns
		-------
		New instance of :class:`Amazon` : Amazon

		Examples
		--------
		>>> Amazon()  #doctest: +ELLIPSIS
		Amazon country is None
		<Lego.api.Amazon object at 0x...>
		"""
		try:
			amazon = yaml.safe_load(file('amazon.yml', 'r'))
		except IOError:
			amazon = {}

		key = (
			key
			or getenv('AWS_ACCESS_KEY_ID')
			or amazon.get('AWS_ACCESS_KEY_ID', None))

		secret = (
			secret
			or getenv('AWS_SECRET_ACCESS_KEY')
			or amazon.get('AWS_SECRET_ACCESS_KEY', None))

		tag = (
			tag
			or getenv('AWS_ASSOCIATE_TAG')
			or amazon.get('AWS_ASSOCIATE_TAG', None))

		if not (key and secret and tag):
			raise SystemExit('Error getting Amazon credentials.')

		super(Amazon, self).__init__(key, secret, tag, **kwargs)

	def parse(self, response):
		"""
		Convert Amazon API search response into a more readable format.

		Parameters
		----------
		response : AmazonSearch object

		Returns
		-------
		Cleaned up search results : dict

		Examples
		--------
		>>> request = Request()
		>>> amazon = Amazon()
		Amazon country is None
		>>> search_kwargs = request.get_amzn_search_kwargs('lego')
		>>> amzn_response = amazon.search(**search_kwargs)
		>>> amazon.parse(amzn_response)[0].keys()
		['amzn_sales_rank', 'amzn_asin', 'amzn_price', 'amzn_title', \
'ebay_model', 'amzn_model', 'amzn_url']
		"""
		items = []

		try:
			for r in response:
				item = {
					'asin': r.asin,
					'model': r.model,
					'url': r.offer_url,
					'title': r.title,
					'price': (r.price_and_currency[0] or 0),
					'currency': r.price_and_currency[1],
					'sales_rank': r._safe_get_element_text('SalesRank'),
				}

				items.append(item)
		except HTTPError:
			pass

		return items
