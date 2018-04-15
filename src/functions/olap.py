# todo

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
        self._cache = {s: {} for s in self.Wrapper.symbols() if s[1] == 'btc'}

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
            self.log('Calculating financial indexes for {0} symbols...'
                     .format(len(self._cache)), self)
            t_delta = time.time()

            bw = {s: self._index2(s) for s in self._cache if not self.Toolkit.halt()}
            bw = {k: v for k, v in bw.items() if v is not None}

            self.log('', self)
            self.log('Financial indexes are: ' + str(bw), self)

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
            self.log('', self)
            self.log('Downloading orders BOOK & trades HISTORY information for {0} symbols...'
                     .format(len(self._cache)), self)
            t_delta = time.time()

            tmp = self.Database.load(self)
            if tmp == 0:
                for s in self._cache:
                    if not self.Toolkit.halt():
                        self._cache[s]['book'] = self.Wrapper.book(s, 3)

                    if not self.Toolkit.halt():
                        self._cache[s]['history'] = self.Wrapper.history(s, t_delta)

                    if not self.Toolkit.halt():
                        self._cache[s]['ohlc'] = self.Wrapper.history(s)
                self.Database.save(self, self._cache)
            else:
                self._cache = tmp
            self.Database.reset(self)

            t_delta = time.time() - t_delta
            av_delta = t_delta / len(self._cache)
            stats = round(t_delta, 3), round(av_delta, 5)

            self.log('', self)
            self.log('...download done in {0} s, average {1} s/symbol.'.format(*stats), self)
            return stats
        except:
            self.log(traceback.format_exc(), self)

    def _index(self, symbol):
        """
        """

        try:
            if self.Toolkit.halt():
                return

            v = self._vclock(symbol)
            s = self._stillness(symbol)
            m = self._momentum(symbol)

            if None not in [m, s, v]:
                p_open, p_high, p_low, p_close = v[0], max(v), min(v), v[-1]
                x = 100 * (p_close / p_high - 1)  # always <= 0
                y = 100 * (p_close / p_low - 1)  # always >= 0
                z = 100 * (p_close / p_open - 1)  # any

                return self.Toolkit.smooth(s + m * (x + y + z) / 3)
        except:
            self.log(traceback.format_exc(), self)

    def _index2(self, symbol):
        """
        """

        try:
            if self.Toolkit.halt():
                return

            m = self._momentum(symbol)
            s = self._stillness(symbol)

            if None not in [m, s] and m > 0:
                return self.Toolkit.smooth(s)
        except:
            self.log(traceback.format_exc(), self)

    def _momentum(self, symbol):
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
            for p, a in self._cache[symbol]['book'].items():
                if a > 0:
                    asks += p * a
                else:
                    bids += p * a

            if asks > 0:
                return 100 * (abs(bids / asks) - 1)
        except:
            self.log(traceback.format_exc(), self)

    def _stillness(self, symbol):
        """
        Intuitively, symbols with less activity are more likely to
        get abrupt price changes (pumps).
        """

        try:
            if self.Toolkit.halt():
                return

            p_open, p_high, p_low, p_close = self._cache[symbol]['ohlc']
            trend = 100 * (p_close / p_open - 1)
            extent = 100 * (p_high / p_low - 1)

            if trend > 0:
                return 1 / extent
        except:
            self.log(traceback.format_exc(), self)

    def _vclock(self, symbol, quantile=.1, cardinality=10):
        """
        https://www.amazon.com/dp/178272009X

        (Chapter 1) The Volume Clock: Insights into the High-Frequency Paradigm
        """

        try:
            if self.Toolkit.halt():
                return

            tmp1 = self._cache[symbol]['history'].copy()
            tmp2, tmp3 = [0, 0], []

            self.log('', self)
            self.log('symbol, tmp1 = ' + str((symbol, tmp1,)), self)

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
            tmp3.append(round(tmp2[1], 8))

            self.log('', self)
            self.log('symbol, tmp3 = ' + str((symbol, tmp3,)), self)

            if len(tmp3) > cardinality:
                tmp3.reverse()
                return tmp3[-cardinality:]
        except:
            self.log(traceback.format_exc(), self)
