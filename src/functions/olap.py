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

            tail = str(round(100 * ratio, 3)) + ' % of the symbols in downtrend.'
            tmp = dict(sorted(self._cache.items(), key=lambda k: k[1])[-5:])
            self.log('Preliminary selection is: ' + str(tmp), self)

            if ratio > 1 - (1 / self.Toolkit.Phi) ** 3:  # ~ 0.76393202
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

    def _update(self, symbols, threshold=5):
        """
        """

        try:
            if self.Toolkit.halt():
                return 0.

            tmp = {}
            cheap, valid = 0, 0
            ls = len(symbols)

            self.log('', self)
            self.log('Updating financial indexes for this {0} symbols: {1}'.format(ls, symbols), self)
            t_delta = time.time()

            for s in symbols:
                t = self._trend(s)
                if t not in [0, None]:
                    valid += 1
                    if t < 0:
                        cheap += 1
                        m = self._momentum(s)
                        if m is not None and m > 0:

                            i = self.Toolkit.smooth(-t * m)
                            if i is not None and i > threshold:
                                tmp[s] = i
                                if s in self._cache:
                                    tmp[s] = (self._cache[s] + tmp[s]) / 2
            self._cache = {s: round(i, 3) for s, i in tmp.items()}

            t_delta = time.time() - t_delta
            av_delta = t_delta / ls
            tt = round(t_delta, 3), round(av_delta, 5)

            self.log('', self)
            self.log('Financial indexes are: ' + str(self._cache), self)
            self.log('...update done in {0} s, average {1} s/symbol.'.format(*tt), self)

            if valid > 0:
                return cheap / valid
            return valid
        except:
            self.log(traceback.format_exc(), self)

    def _targets(self):
        """
        """

        try:
            if self.Toolkit.halt():
                return 0.

            inside = set(self._cache)
            outside = self.Wrapper.symbols() - inside

            if len(inside) > 0:
                k = min(len(outside), 30)
            else:
                k = round(len(outside) / 2)

            return inside | set(random.sample(outside, k))
        except:
            self.log(traceback.format_exc(), self)

    def _momentum(self, symbol):
        """
        """

        try:
            if self.Toolkit.halt():
                return 0.

            asks, bids = 0., 0.
            book = self.Wrapper.book(symbol, 5)

            if book is not None:
                for price, amount in book.items():
                    notional = price * amount
                    if amount > 0:
                        asks += notional
                    else:
                        bids += notional

            if asks > 0:
                return 100 * (abs(bids / asks) - 1)
            return 0.
        except:
            self.log(traceback.format_exc(), self)

    def _trend(self, symbol):
        """
        """

        try:
            if self.Toolkit.halt():
                return 0.

            x, y, z = 0., 0., 0.
            t24h = self.Wrapper.ticker24h(symbol)

            if t24h is not None:
                _open, _high, _low, _close, _volume = t24h
                if _volume > 100 and _close > 1E-5:
                    x = 100 * (_close / _high - 1)  # always <= 0
                    y = 100 * (_close / _low - 1)  # always >= 0
                    z = 100 * (_close / _open - 1)  # any

            return .25 * x + .25 * y + .5 * z
        except:
            self.log(traceback.format_exc(), self)
