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
        self._cache = {}

        self.Toolkit = self.Wrapper.Toolkit
        self.log = self.Toolkit.log
        self.log(self.Toolkit.Greeting, self)

    def broadway(self):
        """
        https://www.pokernews.com/pokerterms/broadway.htm
        """

        try:
            self._update(self.Wrapper.symbols())
            data = self._cache['data']

            self.log('Starting analysis of market data...', self)
            t_delta = time.time()

            excl_bases = {b for (b, q), i in data.items() if i < 11 or 'usd' in b}
            bw = {(b, q): i for (b, q), i in data.items() if b not in excl_bases}
            self.log('Primary selection is: ' + str(sorted(bw)), self)

            bw = {s: int(1E3 * i) for s, i in bw.items()}
            bw = dict(sorted(bw.items(), key=lambda k: k[1])[-5:])

            bw = [bw, {}][len(bw) < 3]
            self.log('FINAL selection is: ' + str(bw), self)

            t_delta = time.time() - t_delta
            self.log('...done in {:.8f} seconds.'.format(t_delta), self)
            return bw

        except:
            self.log(traceback.format_exc(), self)

    def _update(self, symbols):
        """
        """

        try:
            assert symbols is not None

            ls = len(symbols)
            assert ls > 0

            rs = max(10, int(ls / 10))
            t_delta = time.time()

            self._cache = self.Database.query(self)
            if 'data' in self._cache and t_delta - self._cache['last'] < 3600:
                self.log('{0} available symbols: randomly testing {1} of them...'.format(ls, rs), self)
                top5 = set(dict(sorted(self._cache['data'].items(), key=lambda k: k[1])[-5:]))
                rsymbols = set(random.sample(symbols - top5, rs - 5))
                target_set = rsymbols | top5
            else:
                self.log('Testing all {0} available symbols...'.format(ls), self)
                self._cache = {'data': {}, 'last': t_delta}
                target_set = symbols

            self._cache['data'].update({s: self._index(s) for s in target_set
                                        if not self.Toolkit.halt()})
            self.Database.query(self, self._cache)

            t_delta = time.time() - t_delta
            av_delta = t_delta / len(target_set)
            self.log('...done in {:.8f} s, average {:.8f} s/symbol.'
                     .format(t_delta, av_delta), self)

        except AssertionError:
            return
        except:
            self.log(traceback.format_exc(), self)

    def _index(self, symbol, market_depth=5):
        """
        """

        try:
            history = self.Wrapper.history(symbol)
            assert history is not None
            assert len(history) > 0

            epochs = set(list(zip(*history))[0])
            hours = [(max(epochs) - min(epochs)) / 3600, 1 / 3600][len(epochs) == 1]
            frequency = len(history) / hours
            assert frequency > 60

            book = self.Wrapper.book(symbol, market_depth)
            assert book is not None
            assert len(book) > 0

            ticker = self.Toolkit.ticker(book, market_depth)
            assert ticker is not None

            l_ask, h_bid, (l_ask_weight, h_bid_weight, buy_pressure) = ticker
            assert buy_pressure > 5

            spread = 100 * (l_ask / h_bid - 1)
            assert spread < 1

            return self.Toolkit.smooth(frequency * buy_pressure / spread)

        except AssertionError:
            return 0.
        except:
            self.log(traceback.format_exc(), self)
