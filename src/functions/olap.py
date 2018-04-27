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
            self._update()

            self.log('', self)
            self.log('Selecting top symbols by performance...', self)

            bw = {s: round(i, 3) for s, i in self._cache.items() if i > 0}
            self.log('Financial indexes are: ' + str(bw), self)

            bw = dict(sorted(bw.items(), key=lambda k: k[1])[-5:])
            self.log('Preliminary selection is: ' + str(bw), self)

            bw = {s: i for s, i in bw.items() if i > 7}
            bw = [bw, {}][len(bw) < 3]

            self.log('Final selection is: ' + str(bw), self)
            return bw
        except:
            self.log(traceback.format_exc(), self)

    def _update(self):
        """
        """

        try:
            symbols = self.Wrapper.symbols()
            assert symbols is not None

            ls = len(symbols)
            self._cache.update({s: 0. for s in symbols - set(self._cache)})

            self.log('', self)
            self.log('Updating financial indexes for {} symbols...'.format(ls), self)
            t_delta = time.time()

            for s in symbols:
                if self.Toolkit.halt():
                    break

                t = self._trend(s)
                if t is not None and t < 0:
                    m = self._momentum(s)
                    if m is not None and m > 0:
                        i = self.Toolkit.smooth(-t * m)
                        if i is not None:
                            self._cache[s] = (self._cache[s] + i) / 2

            t_delta = time.time() - t_delta
            av_delta = t_delta / ls
            tt = round(t_delta, 3), round(av_delta, 5)
            self.log('...update done in {0} s, average {1} s/symbol.'.format(*tt), self)
        except:
            self.log(traceback.format_exc(), self)

    def _trend(self, symbol):
        """
        """

        try:
            t24h = self.Wrapper.ticker24h(symbol)
            x, y, z = 0., 0., 0.

            if t24h is not None:
                _open, _high, _low, _close, _volume = t24h
                if _volume > 100 and _close > 1E-5:
                    x = 100 * (_close / _high - 1)  # always <= 0
                    y = 100 * (_close / _low - 1)  # always >= 0
                    z = 100 * (_close / _open - 1)  # any

            return .25 * x + .25 * y + .5 * z
        except:
            self.log(traceback.format_exc(), self)

    def _momentum(self, symbol):
        """
        """

        try:
            book = self.Wrapper.book(symbol, 5)
            asks, bids = 0., 0.

            if book is not None:
                for price, amount in book.items():
                    if amount > 0:
                        asks += price * amount
                    else:
                        bids += price * amount

            if asks > 0:
                return 100 * (abs(bids / asks) - 1)
            return asks
        except:
            self.log(traceback.format_exc(), self)
