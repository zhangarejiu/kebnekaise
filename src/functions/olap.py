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
            if ratio is None: return {}

            self.log('', self)
            self.log('Selecting top symbols by performance...', self)

            t_delta = time.time()
            tmp = {s: i for s, i in self._cache.items() if i > 0}

            self.log('', self)
            self.log('Financial indexes are: ' + str(tmp), self)

            tmp = dict(sorted(tmp.items(), key=lambda k: k[1])[-5:])

            self.log('', self)
            self.log('Preliminary selection is: ' + str(tmp), self)

            tail = str(round(100 * ratio, 3)) + ' % of the symbols in uptrend.'

            self.log('', self)
            if ratio > 1 / self.Toolkit.Phi:
                self.log('Altcoins UP: ' + tail, self)
            else:
                self.log('Altcoins DOWN: ' + tail, self)
                tmp = {}

            self.log('', self)
            self.log('Final selection is: ' + str(tmp), self)

            t_delta = time.time() - t_delta

            self.log('', self)
            self.log('...selection done in {0} s.'.format(round(t_delta, 3)), self)
            return tmp
        except:
            self.log(traceback.format_exc(), self)

    def _update(self, symbols):
        """
        """

        try:
            if self.Toolkit.halt():
                return

            self.log('', self)
            self.log('Updating financial indexes for symbols: ' + str(symbols), self)
            ls = len(symbols)

            self.log('', self)
            self.log('({0} total)'.format(ls), self)

            t_delta = time.time()
            self._cache = {s: 0. for s in symbols}

            c = 0
            for s in self._cache:
                lt = self.Toolkit.smooth(self._long_trend(s))
                if lt > 0:
                    c += 1
                    st = self.Toolkit.smooth(self._short_trend(s))

                    if st < 0:
                        vt = {self._volume_trend(s) for _ in range(5)}
                        vt.discard(None)
                        vt.discard(0)

                        vt = self.Toolkit.smooth(sum(vt) / len(vt))
                        if vt > 0:
                            self._cache[s] = round(lt - st + vt, 3)

            t_delta = time.time() - t_delta
            av_delta = t_delta / ls
            stats = round(t_delta, 3), round(av_delta, 5)

            self.log('', self)
            self.log('...update done in {0} s, average {1} s/symbol.'.format(*stats), self)
            return c / ls
        except:
            self.log(traceback.format_exc(), self)

    def _targets(self):
        """
        """

        try:
            if self.Toolkit.halt():
                return

            if len(self._cache) > 0:
                c = set(self._cache)
                outsiders = set(random.sample(self.Wrapper.symbols() - c, 5))
                symbols = c | outsiders
            else:
                symbols = self.Wrapper.symbols()

            tmp = set()
            for s in symbols:
                ohlcv = self.Wrapper.history(s)
                if ohlcv is not None and ohlcv[4] > 100:
                    tmp.add(s)
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

                x = 100 * (p_close / p_high - 1)  # always <= 0
                y = 100 * (p_close / p_low - 1)  # always >= 0
                z = 100 * (p_close / p_open - 1)  # any

                return (x + y + z) / 3
            return 0.
        except:
            self.log(traceback.format_exc(), self)

    def _short_trend(self, symbol):
        """
        """

        try:
            if self.Toolkit.halt():
                return

            history = self.Wrapper.history(symbol, time.time())

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

    def _volume_trend(self, symbol):
        """
        """

        try:
            if self.Toolkit.halt():
                return

            book = self.Wrapper.book(symbol)

            if book is not None:
                asks, bids = 0, 0

                for price, amount in book.items():
                    v = price * amount
                    if amount > 0:
                        asks += v
                    else:
                        bids += v

                if asks > 0:
                    return 100 * (abs(bids / asks) - 1)
            return 0.
        except:
            self.log(traceback.format_exc(), self)
