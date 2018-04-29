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
        self.Database = self.Indicator.Database
        self.Wrapper = self.Indicator.Wrapper
        self.Brand = self.Wrapper.Brand

        self.Toolkit = self.Wrapper.Toolkit
        self.log = self.Toolkit.log
        self.log(self.Toolkit.Greeting, self)
        self._clock = 0

    def probe(self):
        """
        Detecting some good trading opportunities...
        """

        try:
            while not self.Toolkit.halt():
                self.log('', self)
                self.log('[ BEGIN: TRADE ]', self)

                t_delta = time.time()

                report = self._report()
                assert report is not None

                orders = self._review()
                assert orders is not None

                broadway = self.Indicator.broadway()
                assert broadway is not None

                balance, holdings = report
                if holdings[0] > self.Toolkit.Quota:
                    if len(broadway) > 0:
                        goal = self._chase(balance, broadway)
                        if goal not in [0, None]:
                            self.log('', self)
                            self.log('An overall profit of ~' + str(goal) +
                                     '% is initially expected in this operation.', self)
                    else:
                        self.log('', self)
                        self.log('No good symbols enough, waiting for ' +
                                 'better market conditions...', self)
                else:
                    self.log('', self)
                    self.log('Internal error or insufficient funds, sorry...', self)

                t_delta = round(time.time() - t_delta, 3)
                self.log('...probing done in {0} seconds.'.format(t_delta), self)

                self.log('', self)
                self.log('[ END: TRADE ]', self)

                delay = self.Toolkit.Orbit - t_delta / 60
                self.Toolkit.wait([1, delay][delay > 1])
        except:
            self.log(traceback.format_exc(), self)
            self.probe()

    def _report(self):
        """
        Briefly reporting the current status of your assets.
        """

        try:
            balance = self.Wrapper.balance()
            assert balance is not None

            nakamoto = self.Toolkit.ticker(self.Brand, ('btc', 'usdt'))
            assert nakamoto is not None

            holdings = {}
            for currency, (available, on_orders) in balance.items():
                subtotal = available + on_orders
                holdings[currency] = [0., 0.]

                if currency == 'btc':
                    holdings[currency] = [subtotal, subtotal * nakamoto[1]]
                elif currency == 'usdt':
                    holdings[currency] = [subtotal / nakamoto[0], subtotal]
                else:
                    ticker = self.Toolkit.ticker(self.Brand, (currency, 'btc'))
                    if ticker is not None:
                        btctotal = subtotal * ticker[1]
                        holdings[currency] = [btctotal, btctotal * nakamoto[1]]

            fee = 1 - self.Wrapper.Fee / 100
            holdings_btc, holdings_usdt = list(zip(*holdings.values()))
            holdings = round(fee * sum(holdings_btc), 8), round(fee * sum(holdings_usdt), 2)

            self.log('', self)
            self.log('REPORT: Your current BALANCE is: ' + str(balance), self)
            self.log('That\'s equals approximately to BTC {0} (USD {1}).'.format(*holdings), self)
            return balance, holdings
        except:
            self.log(traceback.format_exc(), self)

    def _review(self):
        """
        This will add x% per hour to your targets.
        """

        try:
            self.log('', self)
            self.log('REVIEW: Reviewing profit targets for your current positions...', self)
            t_delta = time.time()

            orders = self.Wrapper.orders()
            assert orders is not None

            if t_delta - self._clock > 3600:
                for oid, (amount, price, symbol) in orders.items():
                    self.log('Canceling order [{0}]...'.format(oid), self)
                    if self.Wrapper.orders(oid) is not None:
                        self._selling(symbol, price)
                self._clock = t_delta

                if len(orders) > 0:
                    orders = self.Wrapper.orders()
                    assert orders is not None
            self.log('Your currently active orders are: ' + str(orders), self)

            t_delta = round(time.time() - t_delta, 3)
            self.log('...review done in {0} seconds.'.format(t_delta), self)
            return orders
        except:
            self.log(traceback.format_exc(), self)

    def _chase(self, balance, broadway):
        """
        Just combining the sequence of BUY and SELL operations.
        """

        try:
            self.log('', self)
            self.log('The selection received was: ' + str(broadway), self)

            chosen = sorted(broadway.items(), key=lambda k: k[1])[-1][0]
            self.log('The chosen symbol was: ' + str(chosen), self)

            profit_goal = 0.
            if balance['btc'][0] > self.Toolkit.Quota:
                self.log('', self)
                self.log('STARTING TRADE PROCEDURES FOR {} ...'.format(chosen), self)

                buy_price = self._buying(chosen, .1)
                assert buy_price not in [0, None]

                self.Toolkit.wait()
                profit_goal = self._selling(chosen, 1.01 * buy_price)
                assert profit_goal not in [0, None]

                self.log('', self)
                self.log('TRADE PROCEDURES DONE FOR {} ...'.format(chosen), self)
            else:
                self.log('But apparently all of your funds are engaged ' +
                         'already: nothing to do.', self)
            return round(profit_goal, 3)
        except:
            self.log(traceback.format_exc(), self)

    def _buying(self, symbol, margin):
        """
        This will try to BUY the given symbol, by the best market conditions.
        """

        try:
            base, quote = symbol
            assert quote == 'btc'

            balance = self.Wrapper.balance()
            assert balance is not None
            assert quote in balance
            assert balance[quote][0] > self.Toolkit.Quota

            ticker = self.Toolkit.ticker(self.Brand, symbol)
            assert ticker is not None

            fee = 1 - self.Wrapper.Fee / 100
            l_ask, h_bid = ticker
            price = (1 + margin / 100) * l_ask

            amount = fee * self.Toolkit.Quota / price
            if balance[quote][0] <= 2 * self.Toolkit.Quota:
                amount = fee * balance[quote][0] / price
            params = {'amount': round(amount, 8), 'price': round(price, 8), 'symbol': symbol, }

            self.log('', self)
            self.log('Current TICKER is: ' + str(ticker), self)
            self.log('Trying to BUY {0} by using parameters: {1}...'.format(symbol, params), self)

            assert self.Wrapper.fire(**params) is not None
            return price
        except AssertionError:
            return 0.
        except:
            self.log(traceback.format_exc(), self)

    def _selling(self, symbol, referential):
        """
        This will try to SELL the given symbol, by the best market conditions.
        """

        try:
            base, quote = symbol
            assert quote == 'btc'

            balance = self.Wrapper.balance()
            assert balance is not None
            assert base in balance

            amount = -1 * balance[base][0]
            assert abs(amount) > 0

            ticker = self.Toolkit.ticker(self.Brand, symbol)
            assert ticker is not None

            margin = self.Toolkit.Phi / 10
            price = (1 + margin / 100) * referential
            params = {'amount': round(amount, 8), 'price': round(price, 8), 'symbol': symbol, }

            self.log('', self)
            self.log('Current TICKER is: ' + str(ticker), self)
            self.log('Trying to SELL {0} by using parameters: {1}...'.format(symbol, params), self)

            assert self.Wrapper.fire(**params) is not None
            return 100 * (price / referential - 1)
        except AssertionError:
            return 0.
        except:
            self.log(traceback.format_exc(), self)
