import hashlib
import hmac
import json
import time

from calendar import timegm
from urllib import parse, request


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
        self.log, self.err = self.Toolkit.log, self.Toolkit.err

    def symbols(self, errors=0):
        """
        """

        call = locals()

        try:
            req = self._request(0)
            assert req is not None

            tmp = {key.lower().partition('_')[::-2] for key in req
                   if int(req[key]['isFrozen']) == 0}
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
            assert req['asks'] is not None
            assert req['bids'] is not None

            asks = {float(p): a for p, a in req['asks']}
            bids = {float(p): -a for p, a in req['bids']}

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

            cutoff -= cutoff % 180
            tmp = [(timegm(time.strptime(d['date'], '%Y-%m-%d %H:%M:%S')),
                    [-1, 1][d['type'] == 'buy'] * float(d['amount']),
                    float(d['rate'])) for d in req]
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

            tmp = {'btc': (0., 0.)}
            for key in req:
                available = float(req[key]['available'])
                on_orders = float(req[key]['onOrders'])
                if available + on_orders > 0:
                    tmp[key.lower()] = (available, on_orders)
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
            assert 'orderNumber' in req

            return int(req['orderNumber'])
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

                tmp = {int(d['orderNumber']): (
                    [-1, 1][d['type'] == 'buy'] * float(d['amount']),
                    float(d['rate']),
                    pair_str.lower().partition('_')[::-2]
                ) for pair_str, orders_list in req.items()
                    for d in orders_list if len(orders_list) > 0}
            else:
                req = self._request(5, order_id)
                assert req is not None
                assert 'success' in req and req['success'] == 1
                tmp = -order_id

            # Delaying a bit, to allow the site to recognize newly created / canceled orders...
            time.sleep(7)
            return tmp
        except:
            self.err(call)

    def _payload(self, req_uri, signing=True, errors=0):
        """
        """

        call = locals()

        try:
            if signing:
                # type(req_uri) == tuple
                post_data = parse.urlencode(req_uri[1]).encode()
                sign = hmac.new(self.Secret, post_data, digestmod=hashlib.sha512).hexdigest()

                params = {'url': req_uri[0], 'data': post_data,
                          'headers': {'Key': self.Key, 'Sign': sign, }, }
                return json.loads(request.urlopen(request.Request(**params)).read().decode())
            else:
                # type(req_uri) == str
                return json.loads(request.urlopen(req_uri).read().decode())
        except:
            self.err(call)

    def _request(self, command, options=None, errors=0):
        """
        """

        call = locals()

        try:
            req_address = 'https://poloniex.com/'

            # SECURITY DELAY: in order to NOT get your IP banned!
            time.sleep(1 / 3)
            conce = {'command': str(), 'nonce': int(1E3 * time.time())}

            if command == 0:
                req_address += 'public?command=returnTicker'
            elif command == 1:
                req_address += 'public?command=returnOrderBook&currencyPair=' \
                               + '_'.join(options[::-1]).upper() + '&depth=99'
            elif command == 2:
                s, e = options[1] - 1400, options[1]
                req_address += 'public?command=returnTradeHistory&currencyPair=' \
                               + '_'.join(options[0][::-1]).upper() + '&start=' \
                               + str(s) + '&end=' + str(e)
            elif command == 3:
                conce.update({'command': 'returnCompleteBalances'})
                req_address = req_address + 'tradingApi', conce
            elif command == 4:
                upd8 = [(1, 'buy'), (-1, 'sell')][options[0] < 0]
                conce.update({'amount': upd8[0] * options[0], 'rate': options[1],
                              'currencyPair': '_'.join(options[2][::-1]).upper(),
                              'command': upd8[1], })
                req_address = req_address + 'tradingApi', conce
            else:
                upd8 = [{'command': 'cancelOrder', 'orderNumber': options, },
                        {'command': 'returnOpenOrders', 'currencyPair': 'all'}][options is None]
                conce.update(upd8)
                req_address = req_address + 'tradingApi', conce

            return self._payload(*[(req_address,), (req_address, False)][command in range(6)[:3]])
        except:
            self.err(call)
