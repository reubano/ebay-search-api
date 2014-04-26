# -*- coding: utf-8 -*-

""" Interface to Amazon API """


import dateutil.parser as du

from os import getenv
from ebaysdk import finding, trading


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
			appid = 'ReubenCu-a3a3-4b38-a01a-b787f6f7bb0a'
		else:
			appid = 'ReubenCu-dd45-46a1-b9fe-56f855e9ae71'

		self.kwargs = {
			'appid': appid,
			'devid': 'fdabe1b2-8cd0-46e4-bf04-1667ec962969',
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
		>>> Trading(sandbox=True)  #doctest: +ELLIPSIS
		<app.api.Trading object at 0x...>
		"""
		super(Trading, self).__init__(**kwargs)
		site_id = self.global_ids[self.kwargs['country']]['trading']

		if self.sandbox:
			domain = 'api.sandbox.ebay.com'
			certid = '84a062e6-505d-42e7-a862-3440624c4a61'
			token = 'AgAAAA**AQAAAA**aAAAAA**YdAQUw**nY+sHZ2PrBmdj6wVnY+sEZ2PrA2dj6wFk4GhC5mFoA6dj6x9nY+seQ**ZY0CAA**AAMAAA**vzX+oYzGaSZ1IOCxVZl0OGvru9RZRXxaPZDTtWaGQZSa8yWCaonskEFxxmyQOBclApnjwyiR8as6Ndm3ytrCPNMqJy76gNwlL030LaBNpAof7jDI42Mw1Nn36Akh9cCnSVmyzm0fyGEdyPO4qme1pEmyPwz6QDP2mTemqUUn6l4mNUhl02rOlCeiEUi8qvl0nU53bsK7PHP+xVsj4zi0Z0lL4+Qh6NGsBfd9/ZB1aNQhJVRHjPot7KlEkdFqmLjHVFjZ+a3jnfa4ni3TbfXAKFzB7HsRBumxujn70qStKzxB3jsQuM3b7qx/2J/5ydCsonDNokCn5tx47or6MDqjRYECJnE0c+92rtC4s8dT1feN4LvY9L2AoEpFeGFT8pFyk699E+ZJHJP6Af3rwgGNKmR3CSbYc70fSmChE7qKO1gASSqhCB4dRFSpckqaSVIYSbj01PidPWFKghvoAuJNp8A/fLBFypAuXJlqlJee1oY4x4fqgB/hhI0pzixg1PkuP9qTHsJTKaAuU+DsBol6j3++72yBN0FmHFGnrHHu8pqzscZc0Ebhc3Len5BzMSic+9Ypm5SiVuh+viAZbYJnEyqX3tjr2KEsbQwif9u5XoT0aMIsRQhaoGIehXNvl9hkS7/ebYgK+BVZJQmmzQp577gNwerAo93J5WAO7e9zxow//jzKaobFLBLm9YtgOv4/PIZsXccPDTlkHw3wpHtSbIfe5AdJLuef6ZTaorQks1sh5eGakk6tl+04FjQwVuL4'
		else:
			domain = 'api.ebay.com'
			certid = '7c187051-74a6-4566-9e87-482200e05005'
			token = 'AgAAAA**AQAAAA**aAAAAA**yOwQUw**nY+sHZ2PrBmdj6wVnY+sEZ2PrA2dj6wJkoWpCJaKpg+dj6x9nY+seQ**/iMCAA**AAMAAA**e33vxWHuVgf9AVDih4FqUJg/iihYvl8tvksaAVGo4XMgqewCP7ysfcui9cblPLrNgTiyJRgrk+WxG+hvTjxCVEHR0bQF36TUkHMyAv5vVzVQpeZDHV5GMo0vxsYOr5euTze1+E1V/8+JsXTYgqXl8qWrDoEqLuwi/GI2g2svvY08xL5ZmOHwNshkzUag4ctXXy27Wt0RkRbHqcl2KmdELNftz9rhowFEEaqgLG+8xrkthHrMAmp4BiQx9kaKrn5PVdL9NN1i/yXjeiEwSyrNurHirtZm4FKlxt++Vw446mEjwNj92I3x22lIIi3k9d9n7VMQ7UFFmZpz0LjV1tvfIuAXpbYUNbx2luRI4Z9ibmQv/V6IoJ4/0YEEqh8UePT2mWQSuJeyFRwfa2pgHsjkPZCjbjDAyWKYRfeHsIw0M3AOQbnsF/URM90qG5EBgBHwnDQmFSekeSt+xhAk+ANfdJ2udCiHRefO8QQKqNaKHw48S2SnX1QEmLkajEVr2gsX/lyyVp777s4UrDu8n5BGcQdb6idipSmPV5HFz/Vd1RaHzO3fcbKDmuZugbrQfKWyyQIkavZWRm1bllfVWeE6daKHL2ZmpKx7A7kCh+Di+YeyLdBK2Fa47lFjGMG7y436LVS7kuV4A1+tvzMqh32FiTviKYetRpY3MXhtXrv6GYlL35ew+lVxUDOVpgV/CFwoo0aS/w1oSZ7KnuT/j/HAAIEZilbkuRmNNqmA97nh0EowGqbcNeSIU//jIMWPlOB7'

		self.kwargs.update({'site_id': site_id, 'domain': domain})
		self.kwargs.update({'certid': certid, 'token': token})
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
		>>> categories[0]['CategoryName']['value']
		'Antiques'
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
		>>> Finding(sandbox=True)  #doctest: +ELLIPSIS
		<app.api.Finding object at 0x...>
		"""
		super(Finding, self).__init__(**kwargs)
		domain = 'svcs.sandbox.ebay.com' if self.sandbox else 'svcs.ebay.com'
		site_id = self.global_ids[self.kwargs['country']]['finding']
		self.kwargs.update({'domain': domain, 'siteid': site_id})
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
		>>> Finding(sandbox=True).search({'keywords': 'Harry Potter'}).keys()
		['itemSearchURL', 'paginationOutput', 'ack', 'timestamp', \
'searchResult', 'version']
		"""
		verb = options.get('verb', 'findItemsAdvanced')
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
		>>> finding = Finding(sandbox=True)
		>>> response = finding.search({'keywords': 'Harry Potter'})
		>>> finding.parse(response).items()[0][1].keys()[:5]
		['price_and_shipping', 'end_date', 'price', 'currency', 'end_date_time']
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
