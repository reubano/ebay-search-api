# -*- coding: utf-8 -*-

""" Interface to Amazon API """


import dateutil.parser as du
import yaml

from os import getenv, path as p
from ebaysdk import finding, trading


def getenv_from_file(env, yml_file):
	parent = p.dirname(p.dirname(__file__))
	yml_file = p.join(parent, yml_file)
	result = yaml.load(file(yml_file, 'r'))
	return result[env]


class Andand(object):
	"""A Ruby inspired null soaking object"""

	def __init__(self, item=None):
		self.item = item

	def __getattr__(self, name):
		try:
			item = getattr(self.item, name)
			return item if name is 'item' else Andand(item)
		except AttributeError:
			return Andand()

	def __call__(self):
		return self.item


class Ebay(object):
	"""A general Ebay API config object"""

	def __init__(self, sandbox=False, **kwargs):
		"""
		Initialization method.

		Parameters
		----------
		argument : string
		app_id : eBay application id
		verbose : show debug and warning messages (default: False)
		errors : warnings enabled (default: True)
		country : eBay country (default: UK)
		timeout : HTTP request timeout (default: 20)
		parallel : ebaysdk parallel object

		Returns
		-------
		New instance of :class:`Ebay` : Ebay

		Examples
		--------
		>>> Ebay()  #doctest: +ELLIPSIS
		<app.api.Ebay object at 0x...>
		"""
		self.global_ids = {
			'US': {'finding': 'EBAY-US', 'trading': 0, 'currency': 'USD'},
			'UK': {'finding': 'EBAY-GB', 'trading': 3, 'currency': 'GBP'},
		}

		self.sandbox = sandbox

		if self.sandbox:
			appid = kwargs.get('appid', getenv('EBAY_SB_APP_ID'))
		else:
			appid = kwargs.get('appid', getenv('EBAY_LIVE_APP_ID'))

		# TODO: look into defaultdict
		self.kwargs = {
			'appid': appid,
			'devid': kwargs.get('devid', getenv('EBAY_DEV_ID')),
			'debug': kwargs.get('verbose', False),
			'warnings': kwargs.get('verbose', False),
			'errors': kwargs.get('errors', True),
			'country': kwargs.get('country', 'US'),
			'timeout': kwargs.get('timeout', 20),
		}

	def execute(self, verb, data):
		"""
		Execute the eBay API request.

		Parameters
		----------
		verb : string
		data : dict

		Returns
		-------
		eBay API response. : dict

		Examples
		--------
		>>> Finding(sandbox=True).execute('findItemsAdvanced', \
{'keywords': 'sushi'}).keys()
		['itemSearchURL', 'paginationOutput', 'ack', 'timestamp', \
'searchResult', 'version']
		"""
		self.api.execute(verb, data)

		if self.api.error():
			raise self.api.error()
		else:
			return self.api.response_dict()


class Trading(Ebay):
	"""An Ebay Trading API object"""

	def __init__(self, **kwargs):
		"""
		Initialization method.

		Parameters
		----------
		sandbox : boolean
		see Ebay class

		Returns
		-------
		New instance of :class:`Trading` : Trading

		Examples
		--------
		>>> trading = Trading(sandbox=True)
		>>> trading  #doctest: +ELLIPSIS
		<app.api.Trading object at 0x...>
		>>> trading.api.config.values['siteid']
		0
		>>> trading = Trading(sandbox=True, country='UK')
		>>> trading.api.config.values['siteid']
		3
		"""
		super(Trading, self).__init__(**kwargs)

		# for travis.ci since the value is too large for travis encrypt
		env_file = 'envs.yml'

		if self.sandbox:
			domain = 'api.sandbox.ebay.com'
			certid = kwargs.get('certid', getenv('EBAY_SB_CERT_ID'))
			token = kwargs.get('token', getenv('EBAY_SB_TOKEN'))
			token = (token or getenv_from_file('EBAY_SB_TOKEN', env_file))
		else:
			domain = 'api.ebay.com'
			certid = kwargs.get('certid', getenv('EBAY_LIVE_CERT_ID'))
			token = kwargs.get('token', getenv('EBAY_LIVE_TOKEN'))

		new = {
			'siteid': self.global_ids[self.kwargs['country']]['trading'],
			'domain': domain,
			'certid': certid,
			'token': token,
			'version': 861,
			'compatibility': 861,
		}

		self.kwargs.update(new)
		self.api = trading(**self.kwargs)

	def get_item(self, id):
		"""
		Get eBay item details

		Parameters
		----------
		id : ebay id

		Returns
		-------
		eBay item details : dict
		"""
		data = {'DetailLevel': 'ItemReturnAttributes', 'ItemID': id}
		return self.execute('GetItem', data)

	def get_categories(self):
		"""
		Get eBay top level categories.

		Returns
		-------
		eBay top level categories. : dict

		Examples
		--------
		>>> trading = Trading(sandbox=True)
		>>> categories = trading.get_categories().CategoryArray.Category
		>>> categories[3]['CategoryName']['value']
		'Books'
		>>> trading = Trading(sandbox=True, country='UK')
		>>> categories = trading.get_categories().CategoryArray.Category
		>>> categories[3]['CategoryName']['value']
		'Books, Comics & Magazines'
		"""
		data = {'DetailLevel': 'ReturnAll', 'LevelLimit': 1}
		return self.execute('GetCategories', data)

	def get_hierarchy(self, category_id, **kwargs):
		"""
		Get the hierarchy for a top level category.

		Parameters
		----------
		category_id : int
			use get_categories to find a top level category

		level_limit : int
			deepest level to retrieve

		detail_level : string
			one of ['ReturnAll']

		Returns
		-------
		Hierarchy for a top level category : dict

		Examples
		--------
		>>> trading = Trading(sandbox=True)
		>>> categories = trading.get_categories().CategoryArray.Category
		>>> id = categories[0]['CategoryID']['value']
		>>> response = trading.get_hierarchy(id, level_limit=2)
		>>> response.CategoryArray.Category[1]['CategoryName']['value']
		'Antiquities'
		"""
		data = {
			'CategoryParent': category_id,
			'DetailLevel': kwargs.get('detail_level', 'ReturnAll'),
			# 'LevelLimit': kwargs.get('level_limit', 0),
		}
		return self.execute('GetCategories', data)

	def parse(self, response):
		"""
		Convert Trading API search response into a more readable format.

		Parameters
		----------
		response : list
			a search response

		Returns
		-------
		Cleaned up search results : list

		Examples
		--------
		>>> trading = Trading(sandbox=True)
		>>> response = trading.get_categories()
		>>> trading.parse(response.CategoryArray.Category)[0]
		{'category': 'Antiques', 'parent_id': '20081', 'id': '20081', 'level': '1'}
		"""
		items = []

		if response and hasattr(response, 'update'):  # one result
			response = [response]

		for r in response:
			item = {
				'id': r.CategoryID,
				'category': r.CategoryName,
				'level': r.CategoryLevel,
				'parent_id': r.CategoryParentID,
			}

			items.append(item)

		return items

	def make_lookup(self, results):
		"""
		Convert Trading API category list into a lookup table.

		Parameters
		----------
		results : list of dicts
			a `parse` result

		Returns
		-------
		Category lookup table : dict

		Examples
		--------
		>>> trading = Trading(sandbox=True)
		>>> response = trading.get_categories()
		>>> results = trading.parse(response.CategoryArray.Category)
		>>> trading.make_lookup(results).keys()[:3]
		['everything else', 'business & industrial', 'pet supplies']
		"""
		return {r['category'].lower(): r for r in results}


class Finding(Ebay):
	"""An eBay Finding API object"""

	def __init__(self, **kwargs):
		"""
		Initialization method.

		Parameters
		----------
		sandbox : boolean
		see Ebay class

		Returns
		-------
		New instance of :class:`Finding` : Finding

		Examples
		--------
		>>> finding = Finding(sandbox=True)
		>>> finding  #doctest: +ELLIPSIS
		<app.api.Finding object at 0x...>
		>>> finding.kwargs['domain']
		'svcs.sandbox.ebay.com'
		>>> finding = Finding(sandbox=False)
		>>> finding.kwargs['domain']
		'svcs.ebay.com'
		"""
		super(Finding, self).__init__(**kwargs)
		domain = 'svcs.sandbox.ebay.com' if self.sandbox else 'svcs.ebay.com'

		new = {
			'siteid': self.global_ids[self.kwargs['country']]['finding'],
			'domain': domain,
			'version': '1.0.0',
			'compatibility': '1.0.0',
		}

		self.kwargs.update(new)
		self.api = finding(**self.kwargs)

	def search(self, options):
		"""
		Search eBay using the Finding API.

		You must specify keywords and/or a category_id. The exception to this
		rule is when the Seller item filter is used. The Seller item filter can
		be used without specifying either keywords or categoryId to retrieve
		all active items for the specified seller.

		Parameters
		----------
		options : dict containing the following
			verb : string
				one of
					findCompletedItems
					findItemsAdvanced
					findItemsByCategory
					findItemsByImage
					findItemsByKeywords
					findItemsByProduct
					findItemsIneBayStores
					getHistograms

			categoryId : integer
			descriptionSearch : boolean
			outputSelector : string
				one of
					SellerInfo
					StoreInfo
					AspectHistogram
					CategoryHistogram

			itemFilter : dict or list of dicts
				{
					'name': ItemFilterType,
					'value': string,
					'paramName': token (optional),
					'paramValue': string (optional),
				}

			aspectFilter : dict
				{'aspectName': AspectFilterType, 'aspectValueName': string}

			domainFilter : dict
				{'domainName': DomainFilterType}

			keywords : string
			paginationInput : dict
				{'entriesPerPage': int, 'pageNumber': int}

			sortOrder : string
				one of
					BestMatch
					BidCountFewest
					BidCountMost
					CountryAscending
					CountryDescending
					CurrentPriceHighest
					DistanceNearest
					EndTimeSoonest
					PricePlusShippingHighest
					PricePlusShippingLowest
					StartTimeNewest

		Returns
		-------
		eBay Finding API search results : dict

		Examples
		--------
		>>> finding = Finding(sandbox=True)
		>>> opts = {'keywords': 'Harry Potter'}
		>>> response = finding.search(opts)
		>>> response.keys()
		['itemSearchURL', 'paginationOutput', 'ack', 'timestamp', \
'searchResult', 'version']
		>>> finding = Finding(country='UK')
		>>> response = finding.search(opts)
		>>> response.keys()
		['itemSearchURL', 'paginationOutput', 'ack', 'timestamp', \
'searchResult', 'version']
		"""
		verb = options.pop('verb', 'findItemsAdvanced')
		return self.execute(verb, options)

	def parse(self, response):
		"""
		Convert Finding search response into a more readable format.

		Parameters
		----------
		response : list
			a search response

		Returns
		-------
		Cleaned up search results : list

		Examples
		--------
		>>> finding = Finding(country='UK')
		>>> opts = {'keywords': 'Harry Potter'}
		>>> response = finding.search(opts)
		>>> parsed = finding.parse(response)
		>>> parsed.keys()
		['results', 'pages']
		>>> type(parsed['pages'])
		<type 'str'>
		>>> items = parsed['results'].items()
		>>> item = items[0][1]
		>>> item.keys()[:5]
		['price_and_shipping', 'end_date', 'price', 'currency', 'end_date_time']
		>>> url = item['url']
		>>> split = url.split('/')[2].split('.')
		>>> '.'.join(split[-2:])
		'co.uk'
		>>> split[0]
		'www'
		"""
		items = []
		currency = self.global_ids[self.kwargs['country']]['currency']
		result = response.searchResult.item
		pages = response.paginationOutput.totalPages

		if result and hasattr(result, 'update'):  # one result
			result = [result]

		for r in result:
			date_time = du.parse(r.listingInfo.endTime)
			end_date = date_time.strftime("%Y-%m-%d")
			end_time = date_time.strftime("%H:%M")
			offset_years = int(date_time.strftime("%Y")) - 2010
			year_in_sec = offset_years * 365 * 24 * 60 * 60
			days_in_sec = int(date_time.strftime("%j")) * 24 * 60 * 60
			hours_in_sec = int(date_time.strftime("%H")) * 60 * 60
			minutes_in_sec = int(date_time.strftime("%M")) * 60
			secs_in_sec = int(date_time.strftime("%S"))

			args = [year_in_sec, days_in_sec, hours_in_sec, minutes_in_sec]
			args.append(secs_in_sec)
			end_date_time = sum(args)
			price = float(Andand(r).sellingStatus.currentPrice.value() or 0)
			buy_now_price = float(Andand(r).listingInfo.buyItNowPrice.value() or 0)
			shipping = float(Andand(r).shippingInfo.shippingServiceCost.value() or 0)
			condition = Andand(r).condition.conditionDisplayName()
			price_and_shipping = price + shipping
			buy_now_price_and_shipping = buy_now_price + shipping

			item = {
				'id': str(r.itemId),
				'url': r.viewItemURL,
				'title': r.title,
				'condition': condition,
				'item_type': r.listingInfo.listingType,
				'price': price,
				'buy_now_price': buy_now_price,
				'shipping': shipping,
				'price_and_shipping': price_and_shipping,
				'buy_now_price_and_shipping': buy_now_price_and_shipping,
				'end_date_time': end_date_time,
				'end_date': end_date,
				'end_time': end_time,
				'currency': currency,
			}

			items.append(item)

		return {'results': {r['id']: r for r in items}, 'pages': pages}
