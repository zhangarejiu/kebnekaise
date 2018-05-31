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

        self.Database = database  # maybe useful in the future...
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
            lc = len(self._cache)

            self.log('Selecting top 5 symbols by forecasting (from {} total)...'.format(lc), self)
            t_delta = time.time()

            bw = {s: round((L[0] * (sum(L[1:]) / 3)) ** .5) for s, L in self._cache.items()}
            bw = {s: i for s, i in bw.items() if i > 0}
            self.log('FIRST selection of symbols is: ' + str(bw), self)

            bw = dict(sorted(bw.items(), key=lambda k: k[1])[-5:])
            self.log('SECOND selection of symbols is: ' + str(bw), self)

            bw = [bw, {}][len(bw) < 2]
            self.log('FINAL selection of symbols is: ' + str(bw), self)

            t_delta = time.time() - t_delta
            av_delta = t_delta / lc
            self.log('...done in {:.8f} s, average {:.8f} s/symbol.'
                     .format(t_delta, av_delta), self)
            return bw
        except:
            self.log(traceback.format_exc(), self)

    def _update(self, symbols):
        """
        """

        try:
            assert not self.Toolkit.halt()
            assert symbols is not None

            if len(self._cache) > 0:
                tmp = {s: L[0] for s, L in self._cache.items() if L[0] > 0}
                tmp = set(dict(sorted(tmp.items(), key=lambda k: k[1])[-20:]))
                symbols = tmp | set(random.sample(symbols - tmp, 10))
            else:
                self._cache = {s: [] for s in symbols}
            ls = len(symbols)

            self.log('Updating indexes for this {0} symbols: {1} ...'.format(ls, symbols), self)
            t_delta = time.time()

            for s in symbols:
                tmp = self._cache[s]
                ma = self._major(s)
                if ma is not None:
                    mi = self._minor(s)
                    if mi is not None:
                        self._cache[s] = [ma] + tmp[1:][-2:] + [mi]

            t_delta = time.time() - t_delta
            av_delta = t_delta / ls
            self.log('...done in {:.8f} s, average {:.8f} s/symbol.'
                     .format(t_delta, av_delta), self)
        except:
            self.log(traceback.format_exc(), self)

    def _major(self, symbol):
        """
        """

        try:
            assert not self.Toolkit.halt()

            ohlcv = self.Wrapper.ohlcv(symbol)
            assert ohlcv is not None

            p_open, p_high, p_low, p_close, volume = ohlcv
            assert p_low > 1E-5 and volume > 100

            latitude = 100 * (p_high / p_low - 1)
            variation = 100 * (p_close / p_open - 1)
            volatility = latitude - abs(variation)

            if variation < 0:
                return int(1E3 * self.Toolkit.smooth(volatility))
            return int(1E3 * self.Toolkit.smooth(1 / volatility))

        except AssertionError:
            return 0
        except:
            self.log(traceback.format_exc(), self)

    def _minor(self, symbol):
        """
        """

        try:
            assert not self.Toolkit.halt()

            ticker = self.Toolkit.ticker(self.Brand, symbol)
            assert ticker is not None

            l_ask, h_bid, [l_ask_depth, h_bid_depth, buy_pressure] = ticker
            assert h_bid_depth > l_ask_depth > 3
            assert buy_pressure > 100

            spread = 100 * (l_ask / h_bid - 1)
            assert spread < 1

            return int(1E3 * self.Toolkit.smooth(buy_pressure / spread))

        except AssertionError:
            return 0
        except:
            self.log(traceback.format_exc(), self)
