# -*- coding: utf-8 -*-

""" Interface to Amazon API """
from __future__ import (
    absolute_import, division, print_function, unicode_literals)

from os import getenv, path as p

import yaml
import pygogo as gogo

from dateutil.parser import parse as du_parse
from ebaysdk.finding import Connection as finding
from ebaysdk.trading import Connection as trading
from ebaysdk.shopping import Connection as shopping

try:
    ConnectionError
except NameError:
    from ebaysdk.exception import ConnectionError
    eBayConnectionError = ConnectionError
else:
    from ebaysdk.exception import ConnectionError as eBayConnectionError

from builtins import *  # noqa  # pylint: disable=unused-import

logger = gogo.Gogo(__name__, monolog=True).logger


def getenv_from_file(env, yml_file):
    parent = p.dirname(p.dirname(__file__))
    yml_file = p.join(parent, yml_file)
    result = yaml.load(open(yml_file, 'r'))
    return result[env]


class Andand(object):
    """A Ruby inspired null soaking object"""

    def __init__(self, item=None):
        self._item_ = item

    def __len__(self):
        return len(self._item_)

    def __iter__(self):
        return iter(self._item_)

    def __getitem__(self, key):
        try:
            return self._item_[key]
        except (KeyError, IndexError):
            return None

    def __getattr__(self, name):
        try:
            return Andand(getattr(self._item_, name))
            # return item if name is 'item' else Andand(item)
        except AttributeError:
            return Andand(self._item_.get(name)) if self._item_ else Andand()

    def __call__(self, default=None):
        return self._item_ or default


class Ebay(object):
    """A general Ebay API config object"""

    def __init__(self, sandbox=False, config_file=None, **kwargs):
        """Initialization method.

        Parameters
        ----------
        argument : string
        appid : eBay application id
        verbose : show debug and warning messages (default: False)
        errors : warnings enabled (default: True)
        country : eBay country (default: US)
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
            'US': {
                'countryabbr': 'EBAY-US', 'countryid': '0', 'currency': 'USD'},
            'UK': {
                'countryabbr': 'EBAY-GB', 'countryid': '3', 'currency': 'GBP'},
            'FR': {
                'countryabbr': 'EBAY-FR', 'countryid': '71', 'currency': 'EUR'},
            'DE': {
                'countryabbr': 'EBAY-DE', 'countryid': '77', 'currency': 'EUR'},
            'IT': {
                'countryabbr': 'EBAY-IT', 'countryid': '101',
                'currency': 'EUR'},
            'ES': {
                'countryabbr': 'EBAY-ES', 'countryid': '186',
                'currency': 'EUR'},
            'CA': {
                'countryabbr': 'EBAY-ENCA', 'countryid': '2',
                'currency': 'CAD'},
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
            'config_file': config_file,
            'debug': kwargs.get('verbose', False),
            'warnings': kwargs.get('verbose', False),
            'errors': kwargs.get('errors', True),
            'country': kwargs.get('country', 'US'),
            'timeout': kwargs.get('timeout', 20),
        }

    def execute(self, verb, data=None):
        """Execute the eBay API request.

        Parameters
        ----------
        verb : string
        data : dict

        Returns
        -------
        eBay API response. : dict

        Examples
        --------
        >>> finding = Finding(sandbox=True)
        >>> data = {'keywords': 'sushi'}
        >>> response = finding.execute('findItemsAdvanced', data)
        >>> set(response) == {
        ...     'itemSearchURL', 'paginationOutput', 'ack', 'timestamp',
        ...     'searchResult', 'version'}
        True
        """
        data = data or {}

        try:
            response = self.api.execute(verb, data)
        except (ConnectionError, eBayConnectionError) as e:
            response = e.response

        try:
            success = response.reply.ack == 'Success'
        except AttributeError:
            try:
                success = response.reply.Ack == 'Success'
            except AttributeError:
                success = False

        result = response.dict()

        if not success:
            try:
                msg = response.reply.Errors.ShortMessage
            except AttributeError:
                msg = response.reply.errorMessage.error.message

            logger.error(msg)
            result['message'] = msg

        return result


class Trading(Ebay):
    """An Ebay Trading API object"""

    def __init__(self, **kwargs):
        """Initialization method.

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
        >>> trading.api.config.values['siteid'] == '0'
        True
        >>> trading = Trading(sandbox=True, country='UK')
        >>> trading.api.config.values['siteid'] == '3'
        True
        """
        super(Trading, self).__init__(**kwargs)

        # for travis.ci since the token is too large for travis encrypt
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
            token = (token or getenv_from_file('EBAY_LIVE_TOKEN', env_file))

        # TODO: add KeyError exception handling
        new = {
            'siteid': self.global_ids[self.kwargs['country']]['countryid'],
            'domain': domain,
            'certid': certid,
            'token': token,
            'version': '861',
            'compatibility': '861',
        }

        self.kwargs.update(new)
        self.api = trading(**self.kwargs)

    # def get_usage(self):
    #     """Get eBay API usage details

    #     Returns
    #     -------
    #     eBay api usage details : dict

    #     Examples
    #     --------
    #     >>> trading = Trading()
    #     >>> response = trading.get_usage()
    #     >>> response
    #     """
    #     return self.execute('GetAPIAccessRules', {})

    def get_item(self, item_id):
        """Get eBay item details

        Parameters
        ----------
        item_id : ebay item id

        Returns
        -------
        eBay item details : dict

        Examples
        --------
        >>> finding = Finding()
        >>> response = finding.search({'keywords': 'lego'})
        >>> parsed = finding.parse(response)
        >>> item = list(parsed['results'].values())[0]
        >>> trading = Trading()
        >>> response = trading.get_item(item['id'])
        >>> fields = {
        ...     'ProxyItem', 'PostCheckoutExperienceEnabled', 'ListingDetails',
        ...     'DispatchTimeMax', 'Site', 'PrimaryCategory', 'HitCounter',
        ...     'GetItFast', 'Quantity', 'IntangibleItem', 'ReturnPolicy',
        ...     'HideFromSearch', 'BuyerProtection', 'ItemID', 'Seller',
        ...     'ConditionID', 'BuyerResponsibleForShipping', 'AutoPay',
        ...     'Title', 'SellingStatus', 'eBayPlusEligible', 'StartPrice',
        ...     'PostalCode', 'Location', 'BuyItNowPrice', 'Country',
        ...     'ShippingDetails', 'LocationDefaulted', 'GiftIcon',
        ...     'PictureDetails', 'eBayPlus', 'Currency', 'ShipToLocations',
        ...     'RelistParentID', 'ListingDuration', 'ProductListingDetails',
        ...     'HitCount', 'BuyerGuaranteePrice', 'TimeLeft', 'Storefront',
        ...     'PrivateListing', 'ConditionDisplayName', 'ReviseStatus',
        ...     'ShippingPackageDetails', 'ListingType', 'PaymentMethods',
        ...     'BuyerRequirementDetails', 'BestOfferDetails',
        ...     'OutOfStockControl', 'TopRatedListing'}
        >>> len(set(response['Item']).intersection(fields)) > 40
        True
        """
        data = {'DetailLevel': 'ItemReturnAttributes', 'ItemID': item_id}
        return self.execute('GetItem', data)

    def get_categories(self):
        """Get eBay top level categories.

        Returns
        -------
        eBay top level categories. : dict

        Examples
        --------
        >>> trading = Trading(sandbox=True)
        >>> response = trading.get_categories()
        >>> response.CategoryArray.Category[3]['CategoryName']
        'Books'
        >>> trading = Trading(sandbox=True, country='UK')
        >>> response = trading.get_categories()
        >>> response.CategoryArray.Category[3]['CategoryName']
        'Books, Comics & Magazines'
        """
        data = {'DetailLevel': 'ReturnAll', 'LevelLimit': 1}
        response = self.execute('GetCategories', data)
        return Andand(response)

    def get_hierarchy(self, category_id, **kwargs):
        """Get the hierarchy for a top level category.

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
        >>> response = trading.get_categories()
        >>> cid = response.CategoryArray.Category[0]['CategoryID']
        >>> response = trading.get_hierarchy(cid, level_limit=2)
        >>> response.CategoryArray.Category[1]['CategoryName']
        'Antiquities'
        """
        data = {
            'CategoryParent': category_id,
            'DetailLevel': kwargs.get('detail_level', 'ReturnAll'),
            # 'LevelLimit': kwargs.get('level_limit', 0),
        }

        response = self.execute('GetCategories', data)
        return Andand(response)

    def parse(self, response):
        """Convert Trading API search response into a more readable format.

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
        >>> trading.parse(response.CategoryArray.Category)[0] == {
        ...     'category': 'Antiques', 'parent_id': '20081', 'country': 'US',
        ...     'id': '20081', 'level': '1'}
        True
        """
        if response and hasattr(response, 'update'):  # one result
            response = [response]

        return [
            {
                'id': r['CategoryID'],
                'category': r['CategoryName'],
                'level': r['CategoryLevel'],
                'parent_id': r['CategoryParentID'],
                'country': self.kwargs['country'],
            } for r in response]

    def make_lookup(self, results):
        """Convert Trading API category list into a lookup table.

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
        >>> set(trading.make_lookup(results)) == {
        ...     'toys & hobbies', 'health & beauty', 'music',
        ...     'musical instruments & gear', 'clothing, shoes & accessories',
        ...     'real estate', 'art', 'antiques', 'home & garden',
        ...     'dolls & bears', 'computers/tablets & networking',
        ...     'business & industrial', 'video games & consoles',
        ...     'consumer electronics', 'tickets & experiences',
        ...     'sports mem, cards & fan shop', 'jewelry & watches',
        ...     'gift cards & coupons', 'entertainment memorabilia',
        ...     'specialty services', 'stamps', 'cameras & photo',
        ...     'pottery & glass', 'coins & paper money', 'everything else',
        ...     'dvds & movies', 'crafts', 'travel', 'pet supplies', 'baby',
        ...     'collectibles', 'books', 'sporting goods',
        ...     'cell phones & accessories'}
        True
        """
        return {r['category'].lower(): r for r in results}


class Finding(Ebay):
    """An eBay Finding API object"""

    def __init__(self, **kwargs):
        """Initialization method.

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
        >>> finding.kwargs['domain'] == 'svcs.sandbox.ebay.com'
        True
        >>> finding = Finding(sandbox=False)
        >>> finding.kwargs['domain'] == 'svcs.ebay.com'
        True
        """
        super(Finding, self).__init__(**kwargs)
        domain = 'svcs.sandbox.ebay.com' if self.sandbox else 'svcs.ebay.com'

        new = {
            'siteid': self.global_ids[self.kwargs['country']]['countryabbr'],
            'domain': domain,
            'version': '1.0.0',
            'compatibility': '1.0.0',
        }

        self.kwargs.update(new)
        self.api = finding(**self.kwargs)

    def search(self, options):
        """Search eBay using the Finding API.

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
        >>> set(response) == {
        ...     'itemSearchURL', 'paginationOutput', 'ack', 'timestamp',
        ...     'searchResult', 'version'}
        True
        >>> finding = Finding(country='UK')
        >>> response = finding.search(opts)
        >>> set(response) == {
        ...     'itemSearchURL', 'paginationOutput', 'ack', 'timestamp',
        ...     'searchResult', 'version'}
        True
        """
        verb = options.pop('verb', 'findItemsAdvanced')
        return self.execute(verb, options)

    def parse(self, response):
        """Convert Finding search response into a more readable format.

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
        >>> set(parsed) == {'message', 'results', 'pages'}
        True
        >>> item = list(parsed['results'].values())[0]
        >>> set(item) == {
        ...     'end_time', 'buy_now_price', 'url', 'currency', 'end_date',
        ...     'shipping', 'buy_now_price_and_shipping', 'title', 'id',
        ...     'condition', 'price_and_shipping', 'item_type', 'price',
        ...     'end_date_time', 'country'}
        True
        >>> 'www.ebay.co.uk' in item['url']
        True
        """
        items = []
        currency = self.global_ids[self.kwargs['country']]['currency']
        result = Andand(response).searchResult.item([])
        pages = Andand(response).paginationOutput.totalPages(0)

        if result and hasattr(result, 'update'):  # one result
            result = [result]

        for r in result:
            date_time = du_parse(r['listingInfo']['endTime'])
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

            price = float(Andand(r).sellingStatus.currentPrice.value(0))
            buy_now_price = float(Andand(r).listingInfo.buyItNowPrice.value(0))

            shipping = float(
                Andand(r).shippingInfo.shippingServiceCost.value(0))

            condition = Andand(r).condition.conditionDisplayName()
            price_and_shipping = price + shipping
            buy_now_price_and_shipping = buy_now_price + shipping

            item = {
                'id': str(r['itemId']),
                'url': r['viewItemURL'],
                'title': r['title'],
                'condition': condition,
                'item_type': r['listingInfo']['listingType'],
                'price': price,
                'buy_now_price': buy_now_price,
                'shipping': shipping,
                'price_and_shipping': price_and_shipping,
                'buy_now_price_and_shipping': buy_now_price_and_shipping,
                'end_date_time': end_date_time,
                'end_date': end_date,
                'end_time': end_time,
                'country': self.kwargs['country'],
                'currency': currency,
            }

            items.append(item)

        results = {r['id']: r for r in items}
        message = response.get('message')
        return {'results': results, 'pages': pages, 'message': message}


class Shopping(Ebay):
    """An eBay Shopping API object"""

    def __init__(self, **kwargs):
        """Initialization method.

        Parameters
        ----------
        sandbox : boolean
        see Ebay class

        Returns
        -------
        New instance of :class:`Shopping` : Shopping

        Examples
        --------
        >>> shopping = Shopping(sandbox=True)
        >>> shopping  #doctest: +ELLIPSIS
        <app.api.Shopping object at 0x...>
        >>> shopping.kwargs['domain'] == 'open.api.sandbox.ebay.com'
        True
        >>> shopping = Shopping(sandbox=False)
        >>> shopping.kwargs['domain'] == 'open.api.ebay.com'
        True
        """

        super(Shopping, self).__init__(**kwargs)

        if self.sandbox:
            domain = 'open.api.sandbox.ebay.com'
        else:
            domain = 'open.api.ebay.com'

        new = {
            'siteid': self.global_ids[self.kwargs['country']]['countryid'],
            'domain': domain,
            'uri': '/shopping',
            'version': '873',
            'compatibility': '873',
        }

        self.kwargs.update(new)
        self.api = shopping(**self.kwargs)

    def search(self, options):
        """Search eBay using the Shopping API.

        see http://developer.ebay.com/DevZone/shopping/docs/CallRef/index.html
        for additional options required for the specific verb.

        Parameters
        ----------
        options : dict containing the following
            verb : string
                one of
                    FindHalfProducts
                    FindPopularItems
                    FindPopularSearches
                    FindProducts
                    FindReviewsAndGuides
                    GetCategoryInfo
                    GeteBayTime
                    GetItemStatus
                    GetMultipleItems
                    GetShippingCosts
                    GetSingleItem
                    GetUserProfile
            ItemID : string
            * : *

        Returns
        -------
        eBay Shopping API search results : dict

        Examples
        --------
        >>> finding = Finding(sandbox=True)
        >>> response = finding.search({'keywords': 'lego'})
        >>> parsed = finding.parse(response)
        >>> item = list(parsed['results'].values())[0]
        >>> shopping = Shopping(sandbox=True)
        >>> opts = {
        ...     'DestinationCountryCode': 'US', 'ItemID': item['id'],
        ...     'DestinationPostalCode': '61605', 'IncludeDetails': False,
        ...     'QuantitySold': 1, 'MessageID': item['id']}
        >>> response = shopping.search(opts)
        >>> set(response) == {
        ...     'Version', 'Build', 'CorrelationID', 'Timestamp',
        ...     'ShippingCostSummary', 'Ack'}
        True
        """
        verb = options.pop('verb', 'GetShippingCosts')
        is_US = options['DestinationCountryCode'] == 'US'

        if is_US and 'DestinationPostalCode' not in options:
            message = 'Missing DestinationPostalCode'
            return {'message': message, 'CorrelationID': options.get('ItemID')}
        else:
            return self.execute(verb, options)

    def parse(self, response):
        """Convert Shopping search response into a more readable format.

        Parameters
        ----------
        response : list
            a search response

        Returns
        -------
        Cleaned up search results : list

        Examples
        --------
        >>> finding = Finding()
        >>> response = finding.search({'keywords': 'lego'})
        >>> parsed = finding.parse(response)
        >>> item = list(parsed['results'].values())[0]
        >>> shopping = Shopping(country='US')
        >>> opts = {
        ...     'DestinationCountryCode': 'US', 'ItemID': item['id'],
        ...     'DestinationPostalCode': '61605', 'IncludeDetails': False,
        ...     'QuantitySold': 1, 'MessageID': item['id']}
        >>> response = shopping.search(opts)
        >>> parsed = shopping.parse(response)
        >>> set(parsed) == {'results'}
        True
        >>> fields = {
        ...     'item_id', 'actual_shipping', 'actual_shipping_service',
        ...     'actual_shipping_currency', 'actual_shipping_type', 'message'}
        >>> set(parsed['results']).difference(fields) == set()
        True
        """
        item_id = response.get('CorrelationID')
        deets = response.get('ShippingCostSummary')

        if deets:
            cost = deets['ShippingServiceCost']

            results = {
                'item_id': item_id,
                'actual_shipping': float(cost['value'] or 0),
                'actual_shipping_currency': cost['_currencyID'],
                'actual_shipping_service': deets['ShippingServiceName'],
                'actual_shipping_type': deets['ShippingType'],
            }
        else:
            results = {'message': response.get('message'), 'item_id': item_id}

        return {'results': results}
