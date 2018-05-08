import hashlib
import hmac
import json
import time
import traceback

from calendar import timegm
from urllib import parse, request


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

    def symbols(self, btc_only=True):
        """
        """

        try:
            req = self._request('public/getmarkets', False)
            assert req['success']

            tmp = {d['MarketName'].lower().partition('-')[::-2]
                   for d in req['result'] if d['IsActive']}

            if btc_only:
                return {s for s in tmp if s[1] == 'btc'}
            return tmp
        except:
            self.log(traceback.format_exc(), self)

    def ohlcv(self, symbol):
        """
        """

        try:
            params = {'market': '-'.join(symbol[::-1]), }
            req = self._request('public/getmarketsummary?' + parse.urlencode(params), False)
            assert req['success']

            if req['result'] is not None and len(req['result']) > 0:
                tmp = req['result'].pop()
                return tmp['PrevDay'], tmp['High'], tmp['Low'], tmp['Last'], tmp['BaseVolume']
        except:
            self.log(traceback.format_exc(), self)

    def history(self, symbol):
        """
        """

        try:
            params = {'market': '-'.join(symbol[::-1]), }
            req = self._request('public/getmarkethistory?' + parse.urlencode(params), False)
            assert req['success']

            tmp = [(timegm(time.strptime(d['TimeStamp'][:19], self.fmt)),
                    [-1, 1][d['OrderType'] == 'BUY'] * d['Quantity'],
                    d['Price']) for d in req['result']]
            tmp.reverse()
            return tmp[-99:]

        except KeyError:
            return
        except:
            self.log(traceback.format_exc(), self)

    def book(self, symbol, margin=1):
        """
        """

        try:
            params = {'market': '-'.join(symbol[::-1]), 'type': 'both', }
            req = self._request('public/getorderbook?' + parse.urlencode(params), False)
            assert req['success']

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
            return
        except:
            self.log(traceback.format_exc(), self)

    def balance(self):
        """
        """

        try:
            req = self._request(('account/getbalances?', {},))
            assert req['success']

            tmp = {'btc': (0., 0.)}
            for d in req['result']:
                available = d['Available']
                on_orders = d['Balance'] - d['Available']
                if available + on_orders > 0:
                    tmp[d['Currency'].lower()] = (available, on_orders)
            return tmp
        except:
            self.log(traceback.format_exc(), self)

    def fire(self, amount, price, symbol, simulate=False):
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

            if simulate:
                return tmp['rate'], tmp['quantity']

            req = self._request((uri, tmp,))
            assert req['success']

            return req['result']['uuid'], tmp['rate']
        except:
            self.log(traceback.format_exc(), self)

    def orders(self, delay=5):
        """
        """

        time.sleep(delay)  # to allow the site recognize newly created / canceled orders...

        try:
            req = self._request(('market/getopenorders?', {},))
            assert req['success']

            return {
                d['OrderUuid']: (
                    [-1, 1][d['OrderType'] == 'LIMIT_BUY'] * d['QuantityRemaining'],
                    d['Limit'],
                    d['Exchange'].lower().partition('-')[::-2]
                )
                for d in req['result']
            }
        except:
            self.log(traceback.format_exc(), self)

    def cancel(self, order_id):
        """
        """

        try:
            req = self._request(('market/cancel?', {'uuid': order_id, },))
            assert req['success']

            time.sleep(7)  # to allow the site recognize newly created / canceled orders...
            return '-' + order_id.upper()

        except AssertionError:
            return ''
        except:
            self.log(traceback.format_exc(), self)

    def _request(self, req_uri, signing=True, debug=False, retry=3):
        """
        """

        calling = locals()
        base_uri = 'https://bittrex.com/api/v1.1/'
        tmp = {}

        try:
            if debug:
                self.log('_request(self, req_uri, signing, debug): ' + str(calling), self)

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
                tmp = json.loads(request.urlopen(request.Request(**params)).read().decode())
            else:
                # type(req_uri) == str
                tmp = json.loads(request.urlopen(base_uri + req_uri).read().decode())

            assert tmp['success']
            return tmp
        except:
            del calling['self']
            if retry > 0:
                calling['retry'] -= 1
                self.log('ERROR: retrying {} more time...'.format(retry), self)
                self.log('(RESPONSE: {})'.format(tmp), self, 0)
                time.sleep(5)
                return self._request(**calling)
            else:
                self.log(traceback.format_exc(), self)
