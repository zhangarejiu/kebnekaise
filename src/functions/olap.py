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
            self.Database.reset(self)  # disable this in order to just make tests
            self._update()

            self.log('', self)
            self.log('Calculating financial indexes for {0} symbols...'
                     .format(len(self._cache)), self)
            t_delta = time.time()

            bw = {s: self._index(s) for s in self._cache if not self.Toolkit.halt()}
            bw = {k: v for k, v in bw.items() if v is not None}

            #self.log('', self)
            #self.log('Financial indexes are: ' + str(bw), self)
            bw = dict(sorted(bw.items(), key=lambda k: k[1])[-5:])

            self.log('', self)
            self.log('Current selection is: ' + str(bw), self)

            t_delta = time.time() - t_delta
            av_delta = t_delta / len(self._cache)
            stats = round(t_delta, 3), round(av_delta, 5)

            self.log('', self)
            self.log('...calculation done in {0} s, average {1} s/symbol.'.format(*stats), self)
            return bw
        except:
            self.log(traceback.format_exc(), self)

    def _update(self):
        """
        Downloads the book of orders and trades history info.
        """

        try:
            self._cache = {s: {} for s in self.Wrapper.symbols()}

            self.log('', self)
            self.log('Downloading orders BOOK & trades HISTORY information for {0} symbols...'
                     .format(len(self._cache)), self)
            t_delta = time.time()

            tmp = self.Database.load(self)
            if tmp == 0:
                for s in self._cache:
                    if not self.Toolkit.halt():
                        self._cache[s]['book'] = self.Wrapper.book(s, 1)

                    if not self.Toolkit.halt():
                        self._cache[s]['history'] = self.Wrapper.history(s, t_delta)

                    if not self.Toolkit.halt():
                        self._cache[s]['ohlc'] = self.Wrapper.history(s)

                    if None in self._cache[s].values():
                        self._cache.pop(s)

                self.Database.save(self, self._cache)
            else:
                self._cache = tmp

            t_delta = time.time() - t_delta
            av_delta = t_delta / len(self._cache)
            stats = round(t_delta, 3), round(av_delta, 5)

            self.log('', self)
            self.log('...download done in {0} s, average {1} s/symbol.'.format(*stats), self)
        except:
            self.log(traceback.format_exc(), self)

    def _index(self, symbol):
        """
        """

        try:
            if self.Toolkit.halt():
                return

            p = self._potential(symbol)
            v = self._vclock(symbol)
            s = self._stillness(symbol)

            if None not in [p, v, s]:
                p_open, p_high, p_low, p_close = v[0], max(v), min(v), v[-1]

                if p_close < 1E-5:  # getting rid of DOGE...
                    return

                x = 100 * (p_close / p_high - 1)  # always <= 0
                y = 100 * (p_close / p_low - 1)  # always >= 0
                z = 100 * (p_close / p_open - 1)  # any

                if p > 0 < (x + y + z) / 3:
                    return round(s, 8)
        except:
            self.log(traceback.format_exc(), self)

    def _potential(self, symbol):
        """
        How many % does the volume in BIDS exceed the volume in ASKS?

        From:
            Algorithmic Trading: Winning Strategies and Their Rationale
            Chan, Ernest P., 2013 - page 164 (ISBN-13: 978-1118460146)
        """

        try:
            if self.Toolkit.halt():
                return

            asks, bids = 0, 0
            for amount in self._cache[symbol]['book'].values():
                if amount > 0:
                    asks += amount
                else:
                    bids += amount

            if not asks == 0:
                return 100 * (abs(bids / asks) - 1)
        except:
            self.log(traceback.format_exc(), self)

    def _vclock(self, symbol, quantile=.1):
        """
        https://www.amazon.com/dp/178272009X

        (Chapter 1) The Volume Clock: Insights into the High-Frequency Paradigm
        """

        try:
            if self.Toolkit.halt():
                return

            tmp1 = self._cache[symbol]['history'].copy()
            tmp2, tmp3 = [0, 0], []

            tmp1.reverse()
            for _, a, p in tmp1:
                v1, p1 = tmp2
                v2, p2 = abs(a * p), p
                v = v1 + v2
                p = (v1 * p1 + v2 * p2) / v

                if v > quantile:
                    P, q, r = round(p, 8), int(v / quantile), v % quantile
                    tmp3 += [P for _ in range(q)]
                    tmp2 = [r, p]
                else:
                    tmp2 = [v, p]
            tmp3.reverse()

            if len(tmp3) > 20:
                return tmp3
        except:
            self.log(traceback.format_exc(), self)

    def _stillness(self, symbol):
        """
        Empirically, symbols with less volatility are more likely to
        get abrupt price changes (pumps).
        """

        try:
            if self.Toolkit.halt():
                return

            p_open, p_high, p_low, p_close = self._cache[symbol]['ohlc']
            volatility = 100 * (p_high / p_low - 1)

            return 1 / volatility
        except:
            self.log(traceback.format_exc(), self)
