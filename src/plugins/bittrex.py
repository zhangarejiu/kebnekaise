import hashlib
import hmac
import json
import time

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

        self.Toolkit = toolkit
        self.Key, self.Secret = self.Toolkit.setup(self.Brand)
        self.log, self.err = self.Toolkit.log, self.Toolkit.err

    def symbols(self, errors=0):
        """
        """

        call = locals()

        try:
            req = self._request(0)
            assert req is not None
            assert req['result'] is not None

            fmt, now = '%Y-%m-%dT%H:%M:%S', time.time()
            tmp = {d['MarketName'].lower().partition('-')[::-2] for d in req['result']
                   if now - timegm(time.strptime(d['TimeStamp'][:19], fmt)) < 3600}
            tmp = {s for s in tmp if s[1] == 'btc'}

            if len(tmp) > 0:
                return tmp
        except:
            self.err(call)

    def book(self, symbol, margin=3, errors=0):
        """
        """

        call = locals()

        try:
            req = self._request(1, symbol)
            assert req is not None
            assert req['result'] is not None
            assert req['result']['sell'] is not None
            assert req['result']['buy'] is not None

            asks = {d['Rate']: d['Quantity'] for d in req['result']['sell']}
            bids = {d['Rate']: -d['Quantity'] for d in req['result']['buy']}

            if len(asks) * len(bids) > 0:
                h_ask = (1 + margin / 100) * min(asks)
                l_bid = (1 - margin / 100) * max(bids)
                tmp = {k: v for k, v in asks.items() if k <= h_ask}
                tmp.update({k: v for k, v in bids.items() if k >= l_bid})
                return tmp
        except:
            self.err(call)

    def history(self, symbol, errors=0):
        """
        """

        call = locals()

        try:
            cutoff = int(time.time())
            req = self._request(2, (symbol, cutoff,))
            assert req is not None
            assert req['result'] is not None

            cutoff -= cutoff % 180
            tmp = [(timegm(time.strptime(d['TimeStamp'][:19], '%Y-%m-%dT%H:%M:%S')),
                    [-1, 1][d['OrderType'] == 'BUY'] * d['Quantity'],
                    d['Price']) for d in req['result']]
            tmp = [(epoch, amount, price,) for epoch, amount, price in tmp
                   if cutoff - 1200 < epoch <= cutoff]
            tmp.reverse()
            return tmp
        except:
            self.err(call)

    def balance(self, errors=0):
        """
        """

        call = locals()

        try:
            req = self._request(3)
            assert req is not None
            assert req['result'] is not None

            tmp = {'btc': (0., 0.)}
            for d in req['result']:
                available = d['Available']
                on_orders = d['Balance'] - d['Available']
                if available + on_orders > 0:
                    tmp[d['Currency'].lower()] = (available, on_orders)
            return tmp
        except:
            self.err(call)

    def fire(self, amount, price, symbol, errors=0):
        """
        """

        call = locals()

        try:
            opt = round(amount, 8), round(price, 8), symbol
            req = self._request(4, opt)
            assert req is not None
            assert req['result'] is not None
            assert 'uuid' in req['result']

            return req['result']['uuid']
        except:
            self.err(call)

    def orders(self, order_id=None, errors=0):
        """
        """

        call = locals()

        try:
            if order_id is None:
                req = self._request(5)
                assert req is not None
                assert req['result'] is not None

                tmp = {d['OrderUuid']: (
                    [-1, 1][d['OrderType'] == 'LIMIT_BUY'] * d['Quantity'],
                    d['Limit'],
                    d['Exchange'].lower().partition('-')[::-2]
                ) for d in req['result']}
            else:
                req = self._request(5, order_id)
                assert req is not None
                assert req['result'] is not None
                assert 'success' in req and req['success'] is True
                tmp = '-' + order_id.upper()

            # Delaying a bit, to allow the site to recognize newly created / canceled orders...
            time.sleep(9)
            return tmp
        except:
            self.err(call)

    def _payload(self, req_uri, signing=True, errors=0):
        """
        """

        call = locals()

        try:
            if signing:
                req_data = req_uri.encode()
                sign = hmac.new(self.Secret, req_data, digestmod=hashlib.sha512).hexdigest()

                params = {'url': req_uri, 'data': req_data, 'headers': {'apisign': sign, }, }
                return json.loads(request.urlopen(request.Request(**params)).read().decode())
            else:
                return json.loads(request.urlopen(req_uri).read().decode())
        except:
            self.err(call)

    def _request(self, command, options=None, errors=0):
        """
        """

        call = locals()

        try:
            req_address = 'https://bittrex.com/api/v1.1/'

            # SECURITY DELAY: in order to NOT get your IP banned!
            time.sleep(1 / 3)
            konce = {'apikey': self.Key, 'nonce': int(1E3 * time.time()), }

            if command == 0:
                req_address += 'public/getmarketsummaries'
            elif command == 1:
                params = {'market': '-'.join(options[::-1]), 'type': 'both', }
                req_address += 'public/getorderbook?' + parse.urlencode(params)
            elif command == 2:
                params = {'market': '-'.join(options[0][::-1]), }
                req_address += 'public/getmarkethistory?' + parse.urlencode(params)
            elif command == 3:
                req_address += 'account/getbalances?' + parse.urlencode(konce)
            elif command == 4:
                side = ['buylimit', 'selllimit'][options[0] < 0]
                konce.update({'quantity': abs(options[0]), 'rate': options[1],
                              'market': '-'.join(options[2][::-1]), })
                req_address += 'market/{0}?'.format(side) + parse.urlencode(konce)
            else:
                upd8 = [('cancel', {'uuid': options, }), ('getopenorders', {})][options is None]
                konce.update(upd8[1])
                req_address += 'market/{0}?'.format(upd8[0]) + parse.urlencode(konce)

            return self._payload(*[(req_address,), (req_address, False)][command in range(6)[:3]])
        except:
            self.err(call)
