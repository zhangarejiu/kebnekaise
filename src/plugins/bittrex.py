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

    https://bittrex.com/Home/Api
    """

    def __init__(self, toolkit):
        """
        Constructor method.
        """

        self.Brand, self.Fee = 'bittrex', .25
        self.fmt = '%Y-%m-%dT%H:%M:%S'

        self.Toolkit = toolkit
        self.Key, self.Secret = self.Toolkit.setup(self.Brand)
        self.log = self.Toolkit.log

    def symbols(self):
        """
        """

        try:
            req = self._request('public/getmarketsummaries', False)
            assert req['success'] is True

            now = time.time()
            return {d['MarketName'].lower().partition('-')[::-2] for d in req['result']
                    if now - timegm(time.strptime(d['TimeStamp'][:19], self.fmt)) < 3600}
        except:
            self.log(traceback.format_exc(), self)

    def book(self, symbol, margin=1):
        """
        """

        try:
            params = {'market': '-'.join(symbol[::-1]), 'type': 'both', }
            req = self._request('public/getorderbook?' + parse.urlencode(params), False)
            assert req['success'] is True

            if None not in req['result'].values():
                asks = {d['Rate']: d['Quantity'] for d in req['result']['sell']}
                bids = {d['Rate']: -d['Quantity'] for d in req['result']['buy']}

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

    def history(self, symbol, cutoff):
        """
        """

        end = int(cutoff - cutoff % 60)
        start = end - 1200

        try:
            params = {'market': '-'.join(symbol[::-1]), }
            req = self._request('public/getmarkethistory?' + parse.urlencode(params), False)
            assert req['success'] is True

            if req['result'] is not None:
                tmp = [(timegm(time.strptime(d['TimeStamp'][:19], self.fmt)),
                        [-1, 1][d['OrderType'] == 'BUY'] * d['Quantity'],
                        d['Price']) for d in req['result']]
                tmp = [(epoch, amount, price,) for epoch, amount, price in tmp
                       if start < epoch <= end]
                tmp.reverse()
                return tmp

        except KeyError:
            return []
        except:
            self.log(traceback.format_exc(), self)

    def balance(self):
        """
        """

        try:
            req = self._request(('account/getbalances?', {},))
            assert req['success'] is True

            tmp = {'btc': (0., 0.)}
            for d in req['result']:
                available = d['Available']
                on_orders = d['Balance'] - d['Available']
                if available + on_orders > 0:
                    tmp[d['Currency'].lower()] = (available, on_orders)
            return tmp
        except:
            self.log(traceback.format_exc(), self)

    def fire(self, amount, price, symbol):
        """
        """

        try:
            tmp = {'rate': round(price, 8),
                   'market': '-'.join(symbol[::-1]), }

            if amount > 0:
                uri = 'market/buylimit?'
                tmp.update({'quantity': round(amount, 8), })
            else:
                uri = 'market/selllimit?'
                tmp.update({'quantity': -round(amount, 8), })

            req = self._request((uri, tmp,))
            assert req['success'] is True

            return req['result']['uuid']
        except:
            self.log(traceback.format_exc(), self)

    def orders(self, order_id=None):
        """
        """

        try:
            if order_id is None:
                req = self._request(('market/getopenorders?', {},))
                assert req['success'] is True

                tmp = {
                    d['OrderUuid']: (
                        [-1, 1][d['OrderType'] == 'LIMIT_BUY'] * d['Quantity'],
                        d['Limit'],
                        d['Exchange'].lower().partition('-')[::-2]
                    )
                    for d in req['result']
                }
            else:
                req = self._request(('market/cancel?', {'uuid': order_id, },))
                assert req['success'] is True
                tmp = '-' + order_id.upper()

            # Delaying a bit, to allow the site to recognize newly created / canceled orders...
            time.sleep(10)
            return tmp
        except:
            self.log(traceback.format_exc(), self)

    def _request(self, req_uri, signing=True):
        """
        """

        base_uri = 'https://bittrex.com/api/v1.1/'

        try:
            # SECURITY DELAY: in order to NOT get your IP banned!
            time.sleep(1 / 3)

            if signing:
                # type(req_uri) == tuple
                req_uri[1].update({'apikey': self.Key, 'nonce': int(1E3 * time.time()), })
                url = base_uri + req_uri[0] + parse.urlencode(req_uri[1])
                post_data = url.encode()

                sign = hmac.new(self.Secret, post_data, digestmod=hashlib.sha512).hexdigest()
                params = {'url': url, 'data': post_data,
                          'headers': {'apisign': sign, }, }
                return json.loads(request.urlopen(request.Request(**params)).read().decode())
            else:
                # type(req_uri) == str
                return json.loads(request.urlopen(base_uri + req_uri).read().decode())

        except (KeyboardInterrupt, gaierror, URLError):
            return {}
        except:
            self.log(traceback.format_exc(), self)
