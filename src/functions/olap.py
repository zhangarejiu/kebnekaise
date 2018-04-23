import random
import time
import traceback


class Indicator(object):
    """
    https://en.wikipedia.org/wiki/Online_analytical_processing
    """

    def __init__(self, wrapper):
        """
        Constructor method.
        """

        self.Wrapper = wrapper
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
            ratio = self._update(self._targets())
            if ratio is None:
                return {}

            self.log('', self)
            self.log('Selecting top symbols by performance...', self)
            t_delta = time.time()

            tmp = {s: i for s, i in self._cache.items() if i > 0}
            self.log('Financial indexes are: ' + str(tmp), self)

            tmp = dict(sorted(tmp.items(), key=lambda k: k[1])[-5:])
            self.log('Preliminary selection is: ' + str(tmp), self)

            tail = str(round(100 * ratio, 2)) + ' % of the symbols in downtrend.'
            if ratio > 1 / self.Toolkit.Phi:
                self.log('ENTERING the market: ' + tail, self)
            else:
                self.log('LEAVING the market: ' + tail, self)
                tmp = {}

            self.log('', self)
            self.log('Final selection is: ' + str(tmp), self)
            t_delta = round(time.time() - t_delta, 5)

            self.log('...selection done in {0} seconds.'.format(t_delta), self)
            return tmp
        except:
            self.log(traceback.format_exc(), self)

    def _update(self, symbols):
        """
        """

        try:
            if self.Toolkit.halt():
                return

            self._cache = {s: 0. for s in symbols}
            lc = len(self._cache)

            self.log('', self)
            self.log('Updating financial indexes for this {0} symbols: {1}'.format(lc, symbols), self)
            t_delta = time.time()

            c = 0
            for s in self._cache:
                lt = self.Toolkit.smooth(self._long_trend(s))
                if lt < 0:
                    c += 1
                    st = self.Toolkit.smooth(self._short_trend(s, t_delta))
                    if st > 0:
                        vt = self.Toolkit.smooth(self._volume_trend(s))
                        if vt > 0:
                            self._cache[s] = round(vt + st - lt, 3)

            t_delta = time.time() - t_delta
            av_delta = t_delta / lc
            tt = round(t_delta, 3), round(av_delta, 5)

            self.log('...update done in {0} s, average {1} s/symbol.'.format(*tt), self)
            return c / lc
        except:
            self.log(traceback.format_exc(), self)

    def _targets(self):
        """
        """

        try:
            if self.Toolkit.halt():
                return

            self.log('', self)
            t_delta = time.time()

            if len(self._cache) == 0:
                self.log('Defining the initial set of target symbols...', self)
                symbols = self.Wrapper.symbols()
            else:
                self.log('Updating the current set of target symbols...', self)
                c = set(self._cache)
                symbols = c | set(random.sample(self.Wrapper.symbols() - c, 10))

            tmp = []
            for s in symbols:
                ohlcv = self.Wrapper.history(s)
                if ohlcv is not None and ohlcv[4] > 100:
                    tmp.append((ohlcv[4], s,))
            tmp = set(list(zip(*sorted(tmp)[-30:]))[1])

            t_delta = time.time() - t_delta
            av_delta = t_delta / len(symbols)
            tt = round(t_delta, 3), round(av_delta, 5)

            self.log('...targeting done in {0} s, average {1} s/symbol.'.format(*tt), self)
            return tmp
        except:
            self.log(traceback.format_exc(), self)

    def _long_trend(self, symbol):
        """
        """

        try:
            if self.Toolkit.halt():
                return

            ohlcv = self.Wrapper.history(symbol)

            if ohlcv is not None:
                p_open, p_high, p_low, p_close = ohlcv[:4]
                if p_close > 1E-5:  # only symbols w/ price above 1000 sat

                    x = 100 * (p_close / p_high - 1)  # always <= 0
                    y = 100 * (p_close / p_low - 1)  # always >= 0
                    z = 100 * (p_close / p_open - 1)  # any
                    return (x + y + z) / 3
            return 0.
        except:
            self.log(traceback.format_exc(), self)

    def _short_trend(self, symbol, cutoff):
        """
        """

        try:
            if self.Toolkit.halt():
                return

            history = self.Wrapper.history(symbol, cutoff)

            if history is not None:
                tmp = [0, 0]

                for epoch1, amount1, price1 in history:
                    for epoch2, amount2, price2 in history:
                        if epoch2 > epoch1 and -amount2 >= amount1 > 0:
                            tmp[0] += 100 * (price2 / price1 - 1)
                            tmp[1] += 1

                return tmp[0] / max(tmp[1], 1)
            return 0.
        except:
            self.log(traceback.format_exc(), self)

    def _volume_trend(self, symbol, tests=3):
        """
        """

        try:
            if self.Toolkit.halt():
                return

            c, tmp = 0, []
            while len(tmp) < tests or c < 3 * tests:
                book = self.Wrapper.book(symbol, 5)
                if book is not None:
                    asks, bids = 0, 0

                    for price, amount in book.items():
                        v = price * amount
                        if amount > 0:
                            asks += v
                        else:
                            bids += v
                    if asks > 0:
                        tmp.append(100 * (abs(bids / asks) - 1))
                c += 1
            return sum(tmp) / tests
        except:
            self.log(traceback.format_exc(), self)
