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
        self.Database = self.Indicator.Database  # maybe useful in the future...
        self.Wrapper = self.Indicator.Wrapper
        self.Brand = self.Wrapper.Brand

        self.Toolkit = self.Wrapper.Toolkit
        self.log = self.Toolkit.log
        self.log(self.Toolkit.Greeting, self)

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

                broadway = self.Indicator.broadway()
                assert broadway is not None

                balance, holdings = report
                if holdings[0] > self.Toolkit.Quota:
                    if len(broadway) > 0:
                        goal = self._chase(balance, self._forecast(broadway))
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
                    self.log('Apparently your funds are insufficient to trade: make a ' +
                             'deposit/transfer to your account and try again. Thanks.', self)

                t_delta = round(time.time() - t_delta, 3)
                self.log('', self)
                self.log('...probing done in {0} seconds.'.format(t_delta), self)

                self.log('', self)
                self.log('[ END: TRADE ]', self)

                delay = self.Toolkit.Orbit - t_delta / 60
                self.Toolkit.wait([1, delay][delay > 1])

        except AssertionError:
            self.log('', self)
            self.log('Unexpected error in "probe()" function: trying again...', self)
            self.probe()
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
                    assert ticker is not None

                    btctotal = subtotal * ticker[1]
                    holdings[currency] = [btctotal, btctotal * nakamoto[1]]

            fee = 1 - self.Wrapper.Fee / 100
            holdings_btc, holdings_usdt = list(zip(*holdings.values()))
            holdings = round(fee * sum(holdings_btc), 8), round(fee * sum(holdings_usdt), 2)

            self.log('', self)
            self.log('REPORT: Your current BALANCE is: ' + str(balance), self)
            self.log('That\'s equals approximately to BTC {0} (USD {1}).'.format(*holdings), self)
            return balance, holdings

        except AssertionError:
            self.log('', self)
            self.log('Unexpected error in "_report()" function: moving forward...', self)
            return
        except:
            self.log(traceback.format_exc(), self)

    def _chase(self, balance, chosen):
        """
        Just combining the sequence of BUY and SELL operations.
        """

        try:
            if chosen is None:
                return

            profit_goal = 0
            if balance['btc'][0] > self.Toolkit.Quota:
                self.log('', self)
                self.log('STARTING TRADE PROCEDURES FOR {} ...'.format(chosen), self)

                buying = self._buying(chosen, balance)
                assert buying is not None
                buy_price, oid = buying
                time.sleep(1)

                if oid not in self.Wrapper.orders():
                    selling = self._selling(chosen, buy_price)
                    assert selling is not None
                    sell_price, oid = selling

                    profit_goal = round(100 * (sell_price / buy_price - 1), 8)
                else:
                    self.log('', self)
                    self.log('BUY routine FAILED, sorry...', self)
                    self.Wrapper.cancel(oid)

                self.log('', self)
                self.log('TRADE PROCEDURES DONE FOR {} ...'.format(chosen), self)
            else:
                self.log('Apparently all of your funds are engaged ' +
                         'already: nothing to do.', self)
            return profit_goal

        except AssertionError:
            self.log('', self)
            self.log('Unexpected error while trading {}, sorry...', self)

            orders = list(self.Wrapper.orders().items())
            self.log('(Current open orders are: {})'.format(orders), self)
            return
        except:
            self.log(traceback.format_exc(), self)

    def _forecast(self, broadway):
        """
        Tries to figure which symbol is most suitable for trade right now.
        """

        try:
            self.log('', self)
            self.log('The selection received was: ' + str(broadway), self)
            forecast = {}

            for symbol in broadway:
                ticker = self.Toolkit.ticker(self.Brand, symbol)
                if ticker is not None:
                    l_ask, h_bid, [l_ask_depth, h_bid_depth, buy_pressure] = ticker
                    spread = 100 * (l_ask / h_bid - 1)

                    requirements = [
                        h_bid_depth > l_ask_depth > 10,
                        spread < 1 - self.Wrapper.Fee,
                        buy_pressure > 100,
                        ]
                    if False not in requirements:
                        forecast[symbol] = int(buy_pressure / spread)

            self.log('', self)
            self.log('Current forecast is: ' + str(forecast), self)

            if len(forecast) > 0:
                chosen = sorted(forecast.items(), key=lambda k: k[1])[-1][0]
                self.log('The chosen symbol was: ' + str(chosen), self)
            else:
                self.log('As there\'s no symbol to choose, I\'m doing nothing.', self)
                return
            return chosen
        except:
            self.log(traceback.format_exc(), self)

    def _buying(self, symbol, balance):
        """
        This will try to BUY the given symbol, by the best market conditions.
        """

        fee = 1 - self.Wrapper.Fee / 100

        try:
            base, quote = symbol
            assert quote == 'btc'

            assert balance is not None
            assert quote in balance
            assert balance[quote][0] > self.Toolkit.Quota

            ticker = self.Toolkit.ticker(self.Brand, symbol)
            assert ticker is not None

            l_ask, h_bid, stats = ticker
            assert stats[0] > 10

            price = l_ask
            amount = self.Toolkit.Quota / price
            if balance[quote][0] <= 2 * self.Toolkit.Quota:
                c = self.Toolkit.Quota / 10
                amount = (balance[quote][0] - c) / price
            params = {'amount': round(amount, 8), 'price': round(price, 8), 'symbol': symbol, }

            self.log('', self)
            self.log('Current TICKER is: ' + str(ticker), self)
            self.log('Trying to BUY {0} by using parameters: {1}...'.format(symbol, params), self)

            buying = self.Wrapper.fire(**params)
            assert buying is not None

            order_id, price = buying
            return price, order_id

        except AssertionError:
            return
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

            margin = 2 * self.Wrapper.Fee + .1
            price = (1 + margin / 100) * referential
            params = {'amount': round(amount, 8), 'price': round(price, 8), 'symbol': symbol, }

            self.log('', self)
            self.log('REFERENCE price was: ' + str(referential), self)
            self.log('Trying to SELL {0} by using parameters: {1}...'.format(symbol, params), self)

            selling = self.Wrapper.fire(**params)
            assert selling is not None

            order_id, price = selling
            return price, order_id

        except AssertionError:
            return
        except:
            self.log(traceback.format_exc(), self)
