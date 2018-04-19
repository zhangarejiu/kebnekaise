import hashlib
import hmac
import json
import time
import traceback

from calendar import timegm
from socket import gaierror
from urllib import parse, request
from urllib.error import URLError


class Wrapper(object):
    """
    Reference:

    https://poloniex.com/support/api/
    """

    def __init__(self, toolkit):
        """
        Constructor method.
        """

        self.Brand, self.Fee = 'poloniex', .25

        self.Toolkit = toolkit
        self.Key, self.Secret = self.Toolkit.setup(self.Brand)
        self.log = self.Toolkit.log

    def symbols(self, btc_only=True):
        """
        """

        try:
            req = self._request('public?command=returnTicker', False)
            assert req is not None

            tmp = {key.lower().partition('_')[::-2]
                   for key in req if int(req[key]['isFrozen']) == 0}

            if btc_only:
                return {s for s in tmp if s[1] == 'btc'}
            return tmp
        except:
            self.log(traceback.format_exc(), self)

    def book(self, symbol, margin=1):
        """
        """

        try:
            req = self._request('public?command=returnOrderBook&currencyPair=' +
                                '_'.join(symbol[::-1]).upper() + '&depth=99', False)
            assert req is not None

            asks = {float(p): a for p, a in req['asks']}
            bids = {float(p): -a for p, a in req['bids']}

            if len(asks) * len(bids) > 0:
                h_ask = (1 + margin / 100) * min(asks)
                l_bid = (1 - margin / 100) * max(bids)
                tmp = {k: v for k, v in asks.items() if k <= h_ask}
                tmp.update({k: v for k, v in bids.items() if k >= l_bid})
                return tmp

        except KeyError:
            return {}
        except:
            self.log(traceback.format_exc(), self)

    def history(self, symbol, cutoff=None):
        """
        """

        try:
            if cutoff is not None:
                # last 20 minutes trades history

                end = int(cutoff - cutoff % 60)
                start = end - 1200
                params = '_'.join(symbol[::-1]).upper(), start, end

                req = self._request('public?command=returnTradeHistory&currencyPair='
                                    + '{0}&start={1}&end={2}'.format(*params), False)
                assert req is not None

                tmp = [(timegm(time.strptime(d['date'], '%Y-%m-%d %H:%M:%S')),
                        [-1, 1][d['type'] == 'buy'] * float(d['amount']),
                        float(d['rate'])) for d in req]
                tmp = [(epoch, amount, price,) for epoch, amount, price in tmp
                       if start < epoch <= end]
                tmp.reverse()
                return tmp
            else:
                # last 24 hours "OPEN|HIGH|LOW|CLOSE" prices

                now = int(time.time())
                end = now - now % 60
                start = end - 86400
                params = '_'.join(symbol[::-1]).upper(), start, end

                req = self._request('public?command=returnChartData&currencyPair='
                                    + '{0}&start={1}&end={2}&period=7200'.format(*params), False)
                assert req is not None

                tmp = list(zip(*[(d['open'], d['high'], d['low'], d['close'],) for d in req]))
                return tmp[0][0], max(tmp[1]), min(tmp[2]), tmp[3][-1]

        except KeyError:
            return []
        except:
            self.log(traceback.format_exc(), self)

    def balance(self):
        """
        """

        try:
            req = self._request(('tradingApi', {'command': 'returnCompleteBalances'},))
            assert req is not None

            tmp = {'btc': (0., 0.)}
            for key in req:
                available = float(req[key]['available'])
                on_orders = float(req[key]['onOrders'])
                if available + on_orders > 0:
                    tmp[key.lower()] = (available, on_orders)
            return tmp
        except:
            self.log(traceback.format_exc(), self)

    def fire(self, amount, price, symbol):
        """
        """

        req = {}

        try:
            tmp = {'rate': round(price, 8),
                   'currencyPair': '_'.join(symbol[::-1]).upper(), }

            if amount > 0:
                tmp.update({'amount': round(amount, 8), 'command': 'buy', })
            else:
                tmp.update({'amount': -round(amount, 8), 'command': 'sell', })

            req = self._request(('tradingApi', tmp,))
            assert req is not None

            return int(req['orderNumber'])
        except:
            self.log(traceback.format_exc(), self)

            self.log('', self)
            self.log('Response: ' + str(req), self)

    def orders(self, order_id=None):
        """
        """

        try:
            if order_id is None:
                req = self._request(('tradingApi', {
                    'command': 'returnOpenOrders', 'currencyPair': 'all'},))
                assert req is not None

                tmp = {
                    int(d['orderNumber']): (
                        [-1, 1][d['type'] == 'buy'] * float(d['amount']),
                        float(d['rate']),
                        pair_str.lower().partition('_')[::-2]
                    )
                    for pair_str, orders_list in req.items()
                    for d in orders_list if len(orders_list) > 0
                }
            else:
                req = self._request(('tradingApi', {'command': 'cancelOrder',
                                                    'orderNumber': order_id, },))
                assert req is not None
                tmp = -order_id

            # Delaying a bit, to allow the site to recognize newly created / canceled orders...
            time.sleep(10)
            return tmp
        except:
            self.log(traceback.format_exc(), self)

    def _request(self, req_uri, signing=True):
        """
        """

        base_uri = 'https://poloniex.com/'

        try:
            if self.Toolkit.halt():
                return

            # SECURITY DELAY: in order to NOT get your IP banned!
            time.sleep(1 / 3)

            if signing:
                # type(req_uri) == tuple
                req_uri[1].update({'nonce': int(1E3 * time.time()), })
                post_data = parse.urlencode(req_uri[1]).encode()

                sign = hmac.new(self.Secret, post_data, digestmod=hashlib.sha512).hexdigest()
                params = {'url': base_uri + req_uri[0], 'data': post_data,
                          'headers': {'Key': self.Key, 'Sign': sign, }, }
                return json.loads(request.urlopen(request.Request(**params)).read().decode())
            else:
                # type(req_uri) == str
                return json.loads(request.urlopen(base_uri + req_uri).read().decode())

        except (ConnectionResetError, KeyboardInterrupt, gaierror, URLError):
            return
        except:
            self.log(traceback.format_exc(), self)
            return
