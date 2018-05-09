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
        self._tracked, self._depth_threshold = {}, 3

        self.Toolkit = self.Wrapper.Toolkit
        self.log = self.Toolkit.log
        self.log(self.Toolkit.Greeting, self)

    def probe(self):
        """
        Detecting some good trading opportunities...
        """

        try:
            while not self.Toolkit.halt():
                self.log('[ BEGIN: TRADE ]', self, 1)
                t_delta = time.time()

                report = self._report()
                assert report is not None

                broadway = self.Indicator.broadway()
                assert broadway is not None

                balance, holdings, _ = report
                if holdings[0] > self.Toolkit.Quota:
                    if len(broadway) > 0:
                        goal = self._chase(balance, self._forecast(broadway))
                        if goal not in [0, None]:
                            self.log('An overall profit of ~' + str(goal) +
                                     '% is initially expected in this operation.', self)
                    else:
                        self.log('No good symbols enough, waiting for ' +
                                 'better market conditions...', self)
                else:
                    self.log('Apparently your funds are insufficient to trade: make a ' +
                             'deposit/transfer to your account and try again. Thanks.', self)
                self.log('(Selection {} checked.)'.format(list(broadway)), self)

                t_delta = round(time.time() - t_delta, 3)
                self.log('...probing done in {} seconds.'.format(t_delta), self)
                self.log('[ END: TRADE ]', self)

                delay = self.Toolkit.Orbit - t_delta / 60
                self.Toolkit.wait([1, delay][delay > 1])

        except AssertionError:
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
            clear = self._clear()
            assert clear is not None
            balance, orders = clear

            orders = self._flush(orders)
            assert orders is not None

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

            self.log('REPORT: Your current BALANCE is: ' + str(balance), self)
            self.log('That\'s equals approximately to BTC {0} (USD {1}).'.format(*holdings), self, 0)
            self.log('Your currently open orders are: ' + str(orders), self, 0)
            return balance, holdings, orders

        except AssertionError:
            self.log('Unexpected error in "_report()" function: moving forward...', self)
            return
        except:
            self.log(traceback.format_exc(), self)

    def _clear(self):
        """
        Checking for idle money.
        """

        try:
            self.log('Checking for altcoin balances not involved in ALIVE orders.', self)
            t_delta = time.time()

            symbols = self.Wrapper.symbols()
            assert symbols is not None

            balance = self.Wrapper.balance()
            assert balance is not None

            orders = self.Wrapper.orders()
            assert orders is not None

            c, engaged = 0, {s[0] for a, p, s in orders.values()}
            for currency, (available, _) in balance.items():
                if currency not in engaged:
                    symbol = currency, 'btc'

                    if symbol in symbols:
                        ticker = self.Toolkit.ticker(self.Brand, symbol)
                        assert ticker is not None

                        l_ask, h_bid, _ = ticker
                        if available * h_bid > 1E-3:
                            self.log('Idle money found for: ' + str(symbol), self)

                            selling = self._selling(symbol, l_ask, 0)
                            assert selling is not None
                            sell_price, oid = selling

                            self.log('The effective SELL price was: {:.8f}'.format(sell_price), self)
                            self.log('(Order # {} created).'.format(oid), self)
                            c += 1
            if c > 0:
                orders = self.Wrapper.orders()
                assert orders is not None

            t_delta = round(time.time() - t_delta, 5)
            self.log('...check done in {} seconds.'.format(t_delta), self)
            return balance, orders

        except AssertionError:
            self.log('Unexpected error in "_clear()" function: moving forward...', self)
            return
        except:
            self.log(traceback.format_exc(), self)

    def _flush(self, orders, stop_loss=60):
        """
        Checking for rotten (unprofitable) orders.
        """

        try:
            self.log('Checking for OUTDATED ({}+ minutes old) orders...'.format(stop_loss), self)
            t_delta = time.time()

            c = 0
            for oid, (amount, price, symbol) in orders.items():
                if oid in self._tracked:
                    if t_delta - self._tracked[oid] > 60 * stop_loss:
                        self.log('Outdated order # {} found, cancelling now...'.format(oid), self)
                        self.Wrapper.cancel(oid)
                        del self._tracked[oid]

                        selling = self._selling(symbol, price, -1)
                        assert selling is not None
                        sell_price, oid = selling

                        self.log('The effective SELL price was: {:.8f}'.format(sell_price), self)
                        self.log('(Order # {} created).'.format(oid), self)
                        c += 1
                else:
                    self._tracked[oid] = t_delta

            if c > 0:
                orders = self.Wrapper.orders()
                assert orders is not None

            t_delta = round(time.time() - t_delta, 5)
            self.log('...check done in {} seconds.'.format(t_delta), self)
            return orders

        except AssertionError:
            self.log('Unexpected error in "_flush()" function: moving forward...', self)
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
                self.log('STARTING TRADE PROCEDURES FOR {} ...'.format(chosen), self)

                buying = self._buying(chosen, balance)
                assert buying is not None
                buy_price, oid = buying

                self.log('The effective BUY price was: {:.8f}'.format(buy_price), self)
                time.sleep(1)

                if oid not in self.Wrapper.orders():
                    fix = 1 + 2 * self.Wrapper.Fee / 100
                    selling = self._selling(chosen, fix * buy_price)
                    assert selling is not None

                    sell_price, oid = selling
                    self.log('The effective SELL price was: {:.8f}'.format(sell_price), self)
                    self.log('(Order # {} created).'.format(oid), self)

                    profit_goal = round(100 * (sell_price / buy_price - fix), 8)
                else:
                    self.log('BUY routine FAILED, sorry...', self)
                    self.Wrapper.cancel(oid)
                self.log('TRADE PROCEDURES DONE FOR {} ...'.format(chosen), self)
            else:
                self.log('Apparently all of your funds are engaged ' +
                         'already: nothing to do.', self)
            return profit_goal

        except AssertionError:
            self.log('Unexpected error while trading {}, sorry...'.format(chosen), self)

            orders = list(self.Wrapper.orders().items())
            self.log('(Current open orders are: {})'.format(orders), self, 0)
            return
        except:
            self.log(traceback.format_exc(), self)

    def _forecast(self, broadway):
        """
        Tries to figure which symbol is most suitable for trade right now.
        """

        try:
            self.log('The selection received was: ' + str(broadway), self)
            forecast = {}

            for symbol in broadway:
                ticker = self.Toolkit.ticker(self.Brand, symbol)
                if ticker is not None:
                    l_ask, h_bid, [l_ask_depth, h_bid_depth, buy_pressure] = ticker
                    spread = 100 * (l_ask / h_bid - 1)

                    requirements = [
                        h_bid_depth > l_ask_depth > self._depth_threshold,
                        buy_pressure > 100,
                        spread < 1
                    ]
                    if False not in requirements:
                        forecast[symbol] = int(buy_pressure / spread)
            self.log('Current forecast is: ' + str(forecast), self)

            if len(forecast) > 0:
                chosen = sorted(forecast.items(), key=lambda k: k[1])[-1][0]
                self.log('The chosen symbol was: ' + str(chosen), self, 0)
            else:
                self.log('As there\'s no symbol to choose, I\'m doing nothing.', self, 0)
                return
            return chosen
        except:
            self.log(traceback.format_exc(), self)

    def _buying(self, symbol, balance, margin=0):
        """
        This will try to BUY the given symbol, by the best market conditions.
        """

        try:
            base, quote = symbol
            assert quote == 'btc'

            assert balance is not None
            assert quote in balance
            assert balance[quote][0] > self.Toolkit.Quota

            ticker = self.Toolkit.ticker(self.Brand, symbol)
            assert ticker is not None

            l_ask, h_bid, stats = ticker
            assert stats[0] > self._depth_threshold

            price = (1 - margin / 100) * l_ask
            amount = self.Toolkit.Quota / price
            if balance[quote][0] <= 2 * self.Toolkit.Quota:
                amount = (balance[quote][0] - self.Toolkit.Quota / 10) / price
            params = {'amount': round(amount, 8), 'price': round(price, 8), 'symbol': symbol, }

            self.log('Current TICKER is: ' + str(ticker), self)
            self.log('Trying to BUY {0} by using parameters: {1} ...'.format(symbol, params), self, 0)

            buying = self.Wrapper.fire(**params)
            assert buying is not None

            order_id, price = buying
            return price, order_id

        except AssertionError:
            return
        except:
            self.log(traceback.format_exc(), self)

    def _selling(self, symbol, referential, margin=.1):
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

            price = (1 + margin / 100) * referential
            params = {'amount': round(amount, 8), 'price': round(price, 8), 'symbol': symbol, }

            self.log('REFERENCE price was: ' + str(referential), self)
            self.log('Trying to SELL {0} by using parameters: {1} ...'.format(symbol, params), self, 0)

            selling = self.Wrapper.fire(**params)
            assert selling is not None

            order_id, price = selling
            return price, order_id

        except AssertionError:
            return
        except:
            self.log(traceback.format_exc(), self)
