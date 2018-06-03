import random
import time
import traceback


class Advisor(object):
    """
    https://en.wikipedia.org/wiki/Online_analytical_processing
    """

    def __init__(self, database):
        """
        Constructor method.
        """

        self.Database = database
        self.Wrapper = self.Database.Wrapper
        self.Brand = self.Wrapper.Brand

        self._cache = {
            'protected': (0, 1, 2),
            'datasets': {}, 'information': {}, 'knowledge': {},
            'profits': {}, 'cycle': 0,
        }
        self._cardinality = 7

        self.Toolkit = self.Wrapper.Toolkit
        self.log = self.Toolkit.log
        self.log(self.Toolkit.Greeting, self)

    def broadway(self):
        """
        https://www.pokernews.com/pokerterms/broadway.htm
        """

        try:
            self.log('Starting analysis of market data...', self)
            t_delta = time.time()

            tmp = self.Database.query(self)
            if len(tmp) > 0:
                self._cache.update(tmp)

            assert self._datasets() is not None
            assert self._information() is not None
            assert self._knowledge() is not None

            alot = 'Tons of data! Omitted here but saved to disk...'
            cache = {
                'datasets': {alot},
                'information': {alot},
                'knowledge': self._cache['knowledge'],
                'protected': self._cache['protected'],
                'cycle': self._cache['cycle'],
            }
            self.log('Current CACHE is: ' + str(cache), self)

            fittest = self._cache['protected'][0]
            strategy = self._cache['knowledge'][fittest]
            bw = self._choose(strategy, 5)
            self.log('Current BROADWAY is: ' + str(bw), self)

            self._cache['cycle'] += 1
            self.Database.query(self, self._cache)

            t_delta = time.time() - t_delta
            self.log('...done in {:.8f} seconds.'.format(t_delta), self)
            return [bw, {}][self._cache['cycle'] < 100]

        except AssertionError:
            return {}
        except:
            self.log(traceback.format_exc(), self)

    def _datasets(self):
        """
        https://en.wikipedia.org/wiki/DIKW_pyramid
        """

        try:
            symbols = self.Wrapper.symbols()
            assert symbols is not None

            ls = len(symbols)
            assert ls > 0

            self.log('DATASETS routine: updating for {} symbols...'.format(ls), self)
            t_delta = time.time()

            self._cache['datasets'] = {}
            for s in symbols:
                if not self.Toolkit.halt():
                    data = [
                        self.Wrapper.ohlcv(s),
                        self.Wrapper.history(s),
                        self.Toolkit.ticker(self.Brand, s, 1)
                    ]
                    if None not in data:
                        self._cache['datasets'][s] = data

            t_delta = time.time() - t_delta
            av_delta = t_delta / ls
            self.log('...done in {:.8f} s, average {:.8f} s/symbol.'
                     .format(t_delta, av_delta), self)
            return 0

        except AssertionError:
            return
        except:
            self.log(traceback.format_exc(), self)

    def _information(self):
        """
        https://en.wikipedia.org/wiki/DIKW_pyramid
        """

        try:
            symbols = set(self._cache['datasets'])
            ls = len(symbols)
            assert ls > 0

            self.log('INFORMATION routine: updating for {} symbols...'.format(ls), self)
            t_delta = time.time()

            self._cache['information'] = {}
            for s in symbols:
                if not self.Toolkit.halt():
                    info = [self._long_i(s), self._short_i(s), self._instant_i(s)]
                    if None not in info:
                        self._cache['information'][s] = sum(info, ())

            t_delta = time.time() - t_delta
            av_delta = t_delta / ls
            self.log('...done in {:.8f} s, average {:.8f} s/symbol.'
                     .format(t_delta, av_delta), self)
            return 0

        except AssertionError:
            return
        except:
            self.log(traceback.format_exc(), self)

    def _knowledge(self):
        """
        https://en.wikipedia.org/wiki/DIKW_pyramid
        """

        try:
            if len(self._cache['knowledge']) == 0:
                self._cache['knowledge'] = {i: self._crossover() for i in range(10)}
            ls = len(self._cache['knowledge'])

            self.log('KNOWLEDGE: updating for {} strategies...'.format(ls), self)
            t_delta = time.time()

            if not self._cache['cycle'] % 5 == 0:  # mutation
                mutables = set(self._cache['knowledge']) - set(self._cache['protected'])
                modified = random.sample(mutables, 1).pop()
                self._cache['knowledge'][modified]['weights'][
                    random.randrange(self._cardinality)] = random.uniform(-1, 1)
            else:
                self._generation()

            t_delta = time.time() - t_delta
            av_delta = t_delta / ls
            self.log('...done in {:.8f} s, average {:.8f} s/symbol.'
                     .format(t_delta, av_delta), self)
            return 0
        except:
            self.log(traceback.format_exc(), self)

    def _long_i(self, symbol):
        """
        Indicators from data, of the last 24 hours.
        """

        try:
            ohlcv = self._cache['datasets'][symbol][0]
            p_open, p_high, p_low, p_close, volume = ohlcv

            amplitude = 100 * (p_high / p_low - 1)
            variation = 100 * (p_close / p_open - 1)
            volatility = amplitude - abs(variation)

            return amplitude, variation, volatility
        except:
            self.log(traceback.format_exc(), self)

    def _short_i(self, symbol):
        """
        Indicators from data, of the last 100 trades.
        """

        try:
            history = self._cache['datasets'][symbol][1]
            tmp = {epoch: amount * price for epoch, amount, price in history}

            hours = (max(tmp) - min(tmp)) / 3600
            trades = len(history)
            trend, frequency = 0., 0.

            if hours > 0:
                trend = sum(tmp.values()) / hours
                frequency = trades / hours

            return trend, frequency
        except:
            self.log(traceback.format_exc(), self)

    def _instant_i(self, symbol):
        """
        Indicators from data, of the current book of orders.
        """

        try:
            ticker = self._cache['datasets'][symbol][2]

            l_ask, h_bid, [l_ask_weight, h_bid_weight, buy_pressure] = ticker
            spread = 100 * (l_ask / h_bid - 1)

            return buy_pressure, spread
        except:
            self.log(traceback.format_exc(), self)

    def _choose(self, strategy, limit=1):
        """
        Uses the given strategy to choose symbols, with the available indicators.
        """

        try:
            weights = strategy['weights']
            rlw = range(len(weights))

            bw = {s: sum(weights[n] * L[n] for n in rlw)
                  for s, L in self._cache['information'].items()}
            bw = {k: int(1E3 * self.Toolkit.smooth(v))
                  for k, v in bw.items()}
            bw = sorted(bw.items(), key=lambda k: k[1])[-limit:]

            return [bw[0][0], dict(bw)][limit > 1]
        except:
            self.log(traceback.format_exc(), self)

    def _exchange(self, strategy):
        """
        Changes the status of the balance associated with a strategy, according
        to current market conditions (kind a trade simulation).
        """

        try:
            balance, currency = strategy['balance']

            if currency == 'btc':  # buying
                balance += [0, .1][balance < .1]
                target = self._choose(strategy)

                ticker = self._cache['datasets'][target][2]
                l_ask, h_bid, _ = ticker
                strategy['balance'] = [balance / l_ask, target[0]]

            else:  # selling
                target = currency, 'btc'
                if target in self._cache['datasets']:
                    ticker = self._cache['datasets'][target][2]
                else:
                    ticker = self.Toolkit.ticker(self.Brand, target, 1)

                l_ask, h_bid, _ = ticker
                strategy['balance'] = [balance * h_bid, target[1]]

            return strategy
        except:
            self.log(traceback.format_exc(), self)

    def _crossover(self, f_strategy=None, m_strategy=None):
        """
        f_strategy = father
        m_strategy = mother
        """

        try:
            weights = [random.uniform(-1, 1) for _ in range(self._cardinality)]

            if None not in [f_strategy, m_strategy]:
                weights = [
                    (f_strategy['weights'][n] + m_strategy['weights'][n]) / 2
                    for n in range(len(weights))
                ]
            return {'weights': weights, 'balance': [1., 'btc']}
        except:
            self.log(traceback.format_exc(), self)

    def _generation(self):
        """
        Starting a new breed of trade agents.
        """

        try:
            # BUYING if self._cache['cycle'] == 0, SELLING otherwise
            self._cache['knowledge'] = {
                k: self._exchange(v) for k, v in self._cache['knowledge'].items()}

            if not self._cache['cycle'] == 0:
                # symbols of the last experiment were 'sold'...
                self._cache['profits'] = {
                    idt: 100 * (strategy['balance'][0] - 1)
                    for idt, strategy in self._cache['knowledge'].items()
                }
                ranking = sorted(self._cache['profits'].items(),
                                  key=lambda k: k[1], reverse=True)

                # calculating parents...
                self._cache['protected'] = list(zip(*ranking[:2] + ranking[-1:]))[0]
                father = self._cache['knowledge'][self._cache['protected'][0]]
                mother = self._cache['knowledge'][self._cache['protected'][1]]
                self._cache['knowledge'][ranking[-1][0]] = self._crossover(father, mother)

                # buying symbols again...
                self._cache['knowledge'] = {
                    k: self._exchange(v) for k, v in self._cache['knowledge'].items()}
            else:
                # symbols of the last experiment were 'bought'...
                # ('else' clause placed here just for clarification)
                pass
        except:
            self.log(traceback.format_exc(), self)
