import hashlib
import hmac
import json
import time
import traceback

from decimal import Decimal
from urllib import parse, request


class Wrapper(object):
    """
    IMPORTANT: in order to get nice profits from this website, just do this FIRST:
        1. GO to [https://www.binance.com/userCenter/myAccount.html] and get the option "Using BNB to
            pay for fees" checked ON;
        2. BUY enough of the BNB_BTC symbol (to "pay for fees", obviously);
        3. NEVER trade the symbol BNB_BTC (this option is disabled in the "symbols ()" method already) or
            you'll lose that "fees payer" balance!

    Reference:
    https://github.com/binance-exchange/binance-official-api-docs
    """

    def __init__(self, toolkit):
        """
        Constructor method.
        """

        self.Brand, self.Fee = 'binance', .1

        self.Toolkit = toolkit
        self.Key, self.Secret = self.Toolkit.setup(self.Brand)
        self.log = self.Toolkit.log
        self._filters, self._orders = {}, {}

    def symbols(self, btc_only=True):
        """
        """

        try:
            req = self._request('api/v1/exchangeInfo', False)
            assert req is not None

            for s_dict in req['symbols']:
                s = s_dict['baseAsset'].lower(), s_dict['quoteAsset'].lower()
                self._filters[s] = s_dict['filters'][0]
                self._filters[s].update(s_dict['filters'][1])
                self._filters[s].update(s_dict['filters'][2])
                del self._filters[s]['filterType']
            tmp = set(self._filters) - {('bnb', 'btc')}

            if btc_only:
                return {s for s in tmp if s[1] == 'btc'}
            return tmp
        except:
            self.log(traceback.format_exc(), self)

    def ohlcv(self, symbol):
        """
        """

        try:
            req = self._request('api/v1/ticker/24hr?symbol=' + ''.join(symbol).upper(), False)
            assert req is not None

            return float(
                req['openPrice']), float(
                req['highPrice']), float(
                req['lowPrice']), float(
                req['lastPrice']), float(
                req['quoteVolume'])
        except:
            self.log(traceback.format_exc(), self)

    def history(self, symbol, limit=100):
        """
        """

        try:
            req = self._request('api/v1/trades?symbol=' + ''.join(symbol).upper()
                                + '&limit=100', False)
            assert req is not None

            tmp = [(int(d['time'] / 1E3),
                    [1, -1][d['isBuyerMaker']] * float(d['qty']),
                    float(d['price'])) for d in req]
            return tmp[-limit:]

        except KeyError:
            return
        except:
            self.log(traceback.format_exc(), self)

    def book(self, symbol, margin=1):
        """
        """

        try:
            req = self._request('api/v1/depth?symbol=' + ''.join(symbol).upper()
                                + '&limit=100', False)
            assert req is not None

            asks = {float(p): float(a) for p, a, _ in req['asks']}
            bids = {float(p): -float(a) for p, a, _ in req['bids']}

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
            req = self._request(('api/v3/account', {'method': 'GET'},))
            assert req is not None

            tmp = {'btc': (0., 0.)}
            for d in req['balances']:
                available = float(d['free'])
                on_orders = float(d['locked'])
                if available + on_orders > 0:
                    tmp[d['asset'].lower()] = (available, on_orders)
            return tmp
        except:
            self.log(traceback.format_exc(), self)

    def fire(self, amount, price, symbol, simulate=False):
        """
        """

        try:
            if len(self._filters) == 0:
                self.symbols()

            price, amount = Decimal(str(price)), Decimal(str(amount))
            min_price = Decimal(self._filters[symbol]['minPrice'])
            min_amount = Decimal(self._filters[symbol]['minQty'])
            min_notional = Decimal(self._filters[symbol]['minNotional'])

            r_price, r_amount = price % min_price, amount % min_amount
            if amount > 0:
                price -= r_price
                amount += min_amount - r_amount
            else:
                price += min_price - r_price
                amount -= r_amount
            assert abs(price * amount) > min_notional

            price, amount = float(price), float(amount)
            tmp = {
                'price': '{:.8f}'.format(price),
                'symbol': ''.join(symbol).upper(),
                'type': 'LIMIT',
                'timeInForce': 'GTC',
                'method': 'POST',
            }
            if amount > 0:
                tmp.update({'quantity': '{:.8f}'.format(amount), 'side': 'BUY', })
            else:
                tmp.update({'quantity': '{:.8f}'.format(-amount), 'side': 'SELL', })

            if simulate:
                return price, amount

            req = self._request(('api/v3/order', tmp,))
            assert req is not None

            oid = req['orderId']
            self._orders[oid] = symbol
            return oid, price
        except:
            self.log(traceback.format_exc(), self)

    def orders(self, delay=5):
        """
        """

        time.sleep(delay)  # to allow the site recognize newly created / canceled orders...

        try:
            if len(self._filters) == 0:
                self.symbols()

            translate = {''.join(s).upper(): s for s in self._filters}
            req = self._request(('api/v3/openOrders', {'method': 'GET'},))
            assert req is not None

            tmp = {
                d['orderId']: (
                    [-1, 1][d['side'] == 'BUY'] * (float(d['origQty']) - float(d['executedQty'])),
                    float(d['price']),
                    translate[d['symbol']]
                )
                for d in req
            }

            self._orders.update({oid: s for oid, (a, p, s) in tmp.items()})
            return tmp
        except:
            self.log(traceback.format_exc(), self)

    def cancel(self, order_id):
        """
        """

        try:
            params = {
                'symbol': ''.join(self._orders[order_id]).upper(),
                'orderId': order_id,
                'method': 'DELETE',
            }
            req = self._request(('api/v3/order', params,))
            assert req is not None

            time.sleep(5)  # to allow the site recognize newly created / canceled orders...
            return '-' + str(order_id).upper()

        except AssertionError:
            return 0
        except:
            self.log(traceback.format_exc(), self)

    def _request(self, req_uri, signing=True, debug=False, retry=3):
        """
        """

        calling = locals()
        base_uri = 'https://api.binance.com/'
        tmp = {}

        try:
            if debug:
                self.log('_request(self, req_uri, signing, debug): ' + str(calling), self)

            # SECURITY DELAY: in order to NOT get your IP banned!
            time.sleep(1 / 3)

            if signing:
                # type(req_uri) == tuple
                method = req_uri[1].pop('method')
                ts = ['timestamp={}', '&timestamp={}'][len(req_uri[1]) > 0]
                query = parse.urlencode(sorted(req_uri[1].items()))
                query += ts.format(int(1E3 * time.time()))

                req_uri[1]['method'] = method
                sign = hmac.new(self.Secret, query.encode(), hashlib.sha256).hexdigest()
                query += '&signature={}'.format(sign)
                params = {'method': method, 'url': base_uri + req_uri[0] + '?' + query,
                          'headers': {'X-MBX-APIKEY': self.Key, }, }
                tmp = json.loads(request.urlopen(request.Request(**params)).read().decode())
            else:
                # type(req_uri) == str
                tmp = json.loads(request.urlopen(base_uri + req_uri).read().decode())

            assert tmp is not None
            return tmp
        except:
            del calling['self']
            if retry > 0:
                calling['retry'] -= 1
                self.log('ERROR: retrying {} more time...'.format(retry), self)
                self.log('(RESPONSE: {})'.format(tmp), self, 0)
                self.Toolkit.wait()
                return self._request(**calling)
            else:
                self.log(traceback.format_exc(), self)
