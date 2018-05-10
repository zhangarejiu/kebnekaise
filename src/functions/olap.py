import random
import time
import traceback


class Indicator(object):
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

    def broadway(self, roof=50):
        """
        https://www.pokernews.com/pokerterms/broadway.htm
        """

        try:
            symbols = self.Wrapper.symbols()
            self._cache.update({s: 0. for s in symbols - set(self._cache)})

            ls = len(symbols)
            if ls > roof:
                symbols, ls = random.sample(symbols, roof), roof

            self.log('Selecting top symbols by performance from {} available...'.format(ls), self)
            t_delta = time.time()

            bw = {s: self._1st(s) for s in symbols}
            bw = {s: i for s, i in bw.items() if i > 0}
            self.log('FIRST selection of symbols is: ' + str(bw), self)

            bw = {s: self._2nd(s) for s in bw}
            bw = {s: i for s, i in bw.items() if i > 0}
            self.log('SECOND selection of symbols is: ' + str(bw), self)

            bw = {s: self._3rd(s) for s in bw}
            bw = {s: i for s, i in bw.items() if i > 0}
            self.log('THIRD selection of symbols is: ' + str(bw), self)

            for s, i in self._cache.items():
                if s in bw: i += bw[s]
                self._cache[s] = round(i / 2)
            bw = {s: i for s, i in self._cache.items() if i > 0}

            if len(bw) > 5:
                bw = dict(sorted(bw.items(), key=lambda k: k[1])[-5:])
            else:
                bw = {}
            self.log('FINAL selection of symbols is: ' + str(bw), self)

            t_delta = time.time() - t_delta
            av_delta = t_delta / ls
            self.log('...done in {:.8f} s, average {:.8f} s/symbol.'
                     .format(t_delta, av_delta), self)
            return bw
        except:
            self.log(traceback.format_exc(), self)

    def _1st(self, symbol):
        """
        """

        try:
            assert not self.Toolkit.halt()

            ohlcv = self.Wrapper.ohlcv(symbol)
            assert ohlcv is not None

            p_open, p_high, p_low, p_close, volume = ohlcv
            assert p_low > 1E-5 and volume > 100

            latitude = 100 * (p_high / p_low - 1)  # % points
            variation = 100 * (p_close / p_open - 1)  # % points
            volatility = latitude - abs(variation)

            if variation < 0:
                return int(1E3 * self.Toolkit.smooth(volatility))
            return int(1E3 * self.Toolkit.smooth(1 / volatility))

        except AssertionError:
            return 0
        except:
            self.log(traceback.format_exc(), self)

    def _2nd(self, symbol):
        """
        """

        try:
            assert not self.Toolkit.halt()

            history = self.Wrapper.history(symbol)
            assert history is not None

            lh = len(history)
            assert lh > 0

            notionals = {epoch: amount * price
                         for epoch, amount, price in history}
            assert len(set(notionals)) > 1

            lag = (max(notionals) - min(notionals)) / 3600  # hours
            frequency = lh / lag  # trades per hour
            trend = round(sum(notionals.values()) / lag, 8)  # BTC per hour

            return int(1E3 * self.Toolkit.smooth(trend * frequency))

        except AssertionError:
            return 0
        except:
            self.log(traceback.format_exc(), self)

    def _3rd(self, symbol):
        """
        """

        try:
            assert not self.Toolkit.halt()

            ticker = self.Toolkit.ticker(self.Brand, symbol)
            assert ticker is not None

            l_ask, h_bid, [l_ask_depth, h_bid_depth, buy_pressure] = ticker
            spread = 100 * (l_ask / h_bid - 1)

            assert h_bid_depth > l_ask_depth > 5
            assert buy_pressure > 100
            assert spread < 1

            return int(1E3 * self.Toolkit.smooth(buy_pressure / spread))

        except AssertionError:
            return 0
        except:
            self.log(traceback.format_exc(), self)
