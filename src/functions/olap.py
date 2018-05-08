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

            ls = len(symbols)
            if ls > roof:
                symbols, ls = random.sample(symbols, roof), roof

            self.log('Selecting top symbols by performance from {} available...'.format(ls), self)
            t_delta = time.time()

            bw = {s: int(1E3 * self._major(s)) for s in symbols}
            bw = {s: i for s, i in bw.items() if i > 0}
            self.log('MAJOR: 1st selection is: ' + str(bw), self)

            bw = {s: int(1E3 * self._minor(s)) for s in bw}
            bw = {s: i for s, i in bw.items() if i > 0}
            self.log('MINOR: 2nd selection is: ' + str(bw), self)

            bw = dict(sorted(bw.items(), key=lambda k: k[1])[-5:])
            bw = [bw, {}][len(bw) < 5]
            self.log('FINAL: 3rd selection is: ' + str(bw), self)

            t_delta = time.time() - t_delta
            av_delta = t_delta / ls
            tt = round(t_delta, 3), round(av_delta, 5)
            self.log('...done in {0} s, average {1} s/symbol.'.format(*tt), self)

            return set(bw)
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
            volatility = 1 + latitude - variation

            if variation < 0:
                return self.Toolkit.smooth(volatility)
            return self.Toolkit.smooth(1 / volatility)

        except AssertionError:
            return 0.
        except:
            self.log(traceback.format_exc(), self)

    def _minor(self, symbol):
        """
        """

        try:
            assert not self.Toolkit.halt()

            history = self.Wrapper.history(symbol)
            assert history is not None

            lh = len(history)
            assert lh > 0

            tmp = {epoch: amount * price
                   for epoch, amount, price in history}
            lag = (max(tmp) - min(tmp)) / 3600

            frequency = lh / lag
            trend = round(sum(tmp.values()) / lag, 8)
            return self.Toolkit.smooth(trend / frequency)

        except AssertionError:
            return 0.
        except:
            self.log(traceback.format_exc(), self)
