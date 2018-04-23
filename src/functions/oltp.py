import random
import time
import traceback


class Trader(object):
    """
    https://en.wikipedia.org/wiki/Online_transaction_processing
    """

    def __init__(self, indicator):
        """
        Constructor method.
        """

        self.Indicator = indicator
        self.Wrapper = self.Indicator.Wrapper
        self.Brand = self.Wrapper.Brand
        self.Toolkit = self.Wrapper.Toolkit

        self._quantum = .1
        self._first, self._last = 0, 0
        self._symbols = set()

        self.log = self.Toolkit.log
        self.log(self.Toolkit.Greeting, self)

    def probe(self, stop_loss=False):
        """
        Detecting some good trading opportunities...

        Important: If you wanna test some new crazy symbol by risking quantities much
        below 'self.Toolkit.Quota', simply define 'stop_loss=False' here.
        """

        try:
            while not self.Toolkit.halt():
                self.log('', self)
                self.log('[ BEGIN: TRADE ]', self)
                t_delta = time.time()

                self._symbols = self.Wrapper.symbols()
                assert self._symbols is not None

                if not stop_loss:
                    report = self._report(self._review(self._clear()))
                else:
                    report = self._report(self._flush(self._review(self._clear())))
                assert report is not None

                broadway = self.Indicator.broadway()
                assert broadway is not None

                balance, holdings = report
                if holdings[0] > self.Toolkit.Quota:
                    if len(broadway) > 0:
                        self._chase(balance, broadway)
                    else:
                        self.log('', self)
                        self.log('No good symbols enough, waiting for better market '
                                 + 'conditions...', self)
                else:
                    self.log('', self)
                    self.log('Internal error or insufficient funds, sorry...', self)
                    self.Toolkit.wait(3 * self.Toolkit.Orbit)
                t_delta = round(time.time() - t_delta, 3)

                self.log('', self)
                self.log('...probing done in {0} seconds.'.format(t_delta), self)
                self.log('[ END: TRADE ]', self)

                delay = self.Toolkit.Orbit - t_delta / 60
                self.Toolkit.wait([1, delay][delay > 1])
        except:
            self.log(traceback.format_exc(), self)
            self.probe()

    def _clear(self):
        """
        Checking for idle money.
        """

        try:
            self.log('', self)
            self.log('CLEAR: Checking for altcoin balances not involved in alive orders.', self)
            t_delta = time.time()

            balance = self.Wrapper.balance()
            assert balance is not None

            orders = self.Wrapper.orders()
            assert orders is not None

            self.log('', self)
            self.log('Your currently active orders are: ' + str(orders), self)

            engaged = {s[0] for a, p, s in orders.values()}
            for currency, (available, _) in balance.items():
                symbol = currency, 'btc'

                if symbol in self._symbols:
                    eligible = available * self._value(*symbol) > self.Toolkit.Quota / 2

                    if eligible and currency not in engaged:
                        ticker = self.Toolkit.ticker(self.Brand, symbol)
                        assert ticker is not None
                        self._burn(symbol, -50 * self._quantum, ticker[0])

            t_delta = round(time.time() - t_delta, 3)
            self.log('', self)
            self.log('...check done in {0} seconds.'.format(t_delta), self)

            return orders
        except:
            self.log(traceback.format_exc(), self)

    def _review(self, last_orders):
        """
        This will add x% per hour to your targets.
        """

        try:
            self.log('', self)
            self.log('REVIEW: Reviewing profit targets for your current positions...', self)
            t_delta = time.time()

            orders = self.Wrapper.orders()
            assert orders is not None

            if last_orders != orders:
                self.log('', self)
                self.log('Your currently active orders are: ' + str(orders), self)

            if t_delta - self._last > 3600:
                for oid, (amount, price, symbol) in orders.items():
                    self.log('', self)
                    self.log('Canceling order [{0}]...'.format(oid), self)
                    assert self.Wrapper.orders(oid) is not None
                    self._burn(symbol, -2 * self._quantum, price)
                self._last = t_delta

            t_delta = round(time.time() - t_delta, 3)
            self.log('', self)
            self.log('...review done in {0} seconds.'.format(t_delta), self)

            return orders
        except:
            self.log(traceback.format_exc(), self)

    def _flush(self, last_orders, threshold=5):
        """
        This will close positions that are causing losses.
        """

        try:
            self.log('', self)
            self.log('FLUSH: Removing any assets that failed to become profitable...', self)
            t_delta = time.time()

            orders = self.Wrapper.orders()
            assert orders is not None

            if last_orders != orders:
                self.log('', self)
                self.log('Your currently active orders are: ' + str(orders), self)

            for oid, (amount, price, symbol) in orders.items():
                equity = abs(amount) * self._value(symbol[0], 'btc')

                if 0 < equity < (1 - threshold / 100) * self.Toolkit.Quota:
                    self.log('', self)
                    self.log('Canceling order [{0}]...'.format(oid), self)
                    assert self.Wrapper.orders(oid) is not None

                    ticker = self.Toolkit.ticker(self.Brand, symbol)
                    assert ticker is not None
                    self._burn(symbol, -30 * self._quantum, ticker[1], False)

            t_delta = round(time.time() - t_delta, 3)
            self.log('', self)
            self.log('...removal done in {0} seconds.'.format(t_delta), self)
            return orders
        except:
            self.log(traceback.format_exc(), self)

    def _report(self, last_orders):
        """
        Briefly reporting the current status of your funds and assets.
        """

        try:
            orders = self.Wrapper.orders()
            assert orders is not None

            if last_orders != orders:
                self.log('', self)
                self.log('Your currently active orders are: ' + str(orders), self)

            balance = self.Wrapper.balance()
            assert balance is not None

            holdings = self._holdings(balance)
            assert holdings is not None

            self.log('', self)
            self.log('Your current BALANCE is: ' + str(balance), self)
            self.log('That\'s equals approximately to BTC {0} (USD {1}).'.format(*holdings), self)
            return balance, holdings
        except:
            self.log(traceback.format_exc(), self)

    def _holdings(self, balance):
        """
        The estimated value of your balance, expressed in BTC and USD.
        """

        try:
            fee = 1 - self.Wrapper.Fee / 100
            btc_total = sum(
                (a + o) * self._value(c, 'btc')
                for c, (a, o) in balance.items() if not c.startswith('usd')
            )
            usd_total = 0.

            ticker = self.Toolkit.ticker(self.Brand, ('btc', 'usdt',))
            assert ticker is not None

            l_ask, h_bid = ticker
            if 'usdt' in balance:
                usd_total = fee * sum(balance['usdt']) / l_ask

            btc_total += usd_total
            usd_total = btc_total * h_bid
            return round(btc_total, 8), round(usd_total, 2)
        except:
            self.log(traceback.format_exc(), self)

    def _value(self, source, target):
        """
        Tries to return the approximate unit value from one currency to another.
        """

        try:
            fee = 1 - self.Wrapper.Fee / 100
            symbol, lobmys = (source, target), (target, source)

            if source == target:
                return 1.

            elif symbol in self._symbols:
                t_symbol = self.Toolkit.ticker(self.Brand, symbol)
                assert t_symbol is not None
                return round(fee * t_symbol[1], 8)

            elif lobmys in self._symbols:
                t_lobmys = self.Toolkit.ticker(self.Brand, lobmys)
                assert t_lobmys is not None
                return round(fee / t_lobmys[0], 8)

            else:
                return 0.
        except:
            self.log(traceback.format_exc(), self)

    def _chase(self, balance, broadway, rchoice=False):
        """
        Ensures that the given symbol is bought & sold by the best market conditions.
        """

        try:
            self.log('', self)
            self.log('The selection received was: ' + str(broadway), self)

            if not rchoice:
                chosen = sorted(broadway.items(), key=lambda k: k[1])[-1][0]
                self.log('The chosen symbol was: ' + str(chosen), self)
            else:
                chosen = random.choice(list(broadway))
                self.log('The (randomly) chosen symbol was: ' + str(chosen), self)

            if self._first in [0, chosen]:
                self.log('', self)
                self.log('But it\'s the first one of this session: nothing to do.', self)

                if self._first == 0:
                    self._first = chosen
                return
            self._first = None

            self.log('', self)
            if chosen in {s for a, p, s in self.Wrapper.orders().values()}:
                self.log('But it\'s one of your current assets: nothing to do.', self)

            elif balance['btc'][0] < self.Toolkit.Quota:
                self.log('But apparently all of your funds are engaged already: nothing to do.', self)
            else:
                self.log('STARTING TRADE PROCEDURES FOR SYMBOL: ' + str(chosen), self)

                buying = self._burn(chosen, self._quantum, None, False)
                if buying is None:
                    return

                self.Toolkit.wait(self.Toolkit.Orbit)

                if buying[1] in self.Wrapper.orders():
                    self.Wrapper.orders(buying[1])

                selling = self._burn(chosen, -100 * self._quantum, buying[0]['price'])

                self.log('', self)
                if selling is None:
                    self.log('Buying in maker-mode for ' + str(chosen) + ' FAILED: sorry.', self)
                    return
                else:
                    goal = round(100 * (selling[0]['price'] / buying[0]['price'] - 1), 3)
                    self.log('An overall profit of ~' + str(goal) +
                             '% is initially expected in this operation.', self)
                    return goal
        except:
            self.log(traceback.format_exc(), self)

    def _burn(self, symbol, margin, referential=None, maker=True):
        """
        Simply runs the 'fire()' method of the Wrapper class: just set
        margin > 0 for BUY or margin < 0 for SELL.

        Price will be calculated according to the lowest ask for BUY or
        the "referential" attribute for SELL. All of your available
        balance will be used in SELLS, or 'self.Toolkit.Quota' in BUYS.
        """

        try:
            coef = [1 + margin / 100, 1 - margin / 100][maker]
            base, quote = symbol[0], 'btc'

            balance = self.Wrapper.balance()
            assert balance is not None

            ticker = self.Toolkit.ticker(self.Brand, symbol)
            assert ticker is not None

            if margin > 0:
                assert quote in balance
                price = coef * ticker[0]
                assert price > 0
                amount = self.Toolkit.Quota / price
            else:
                if base not in balance: return
                assert referential is not None
                price = coef * referential
                amount = -1 * balance[base][0]

            params = {'amount': round(amount, 8), 'price': round(price, 8), 'symbol': symbol, }
            side = ['SELL', 'BUY'][amount > 0]

            self.log('', self)
            self.log('Trying to ' + side + ': ' + str(symbol) + '...', self)
            self.log('Current TICKER is: ' + str(ticker), self)
            self.log('Sending order with parameters: {0}...'.format(params), self)

            order_id = self.Wrapper.fire(**params)
            assert order_id is not None
            return params, order_id
        except:
            self.log(traceback.format_exc(), self)
