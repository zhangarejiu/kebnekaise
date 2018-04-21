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
        self._upd8ed, self._calcul8ed = 0, None

        self.Toolkit = self.Wrapper.Toolkit
        self.log = self.Toolkit.log
        self.log(self.Toolkit.Greeting, self)

    def broadway(self):
        """
        https://www.pokernews.com/pokerterms/broadway.htm
        """

        try:
            self._update()

            if not len(self._cache) > 0:
                self.log('', self)
                self.log('Error while updating DB, trying again now...', self)

                self._upd8ed = 0
                return self.broadway()

            self.log('', self)
            self.log('Calculating financial indexes for {0} symbols...'
                     .format(len(self._cache)), self)
            t_delta = time.time()

            bw = {s: self._index(s) for s in self._cache if not self.Toolkit.halt()}
            bw = {k: v for k, v in bw.items() if v is not None}

            if not self._calcul8ed:
                self._cache = {s: {} for s in bw}
                self._calcul8ed = True

            self.log('', self)
            self.log('Financial indexes are: ' + str(bw), self)

            bw = {k: v for k, v in bw.items() if 5 < v < 10}
            bw = dict(sorted(bw.items(), key=lambda k: k[1])[-5:])
            bw = [bw, {}][len(bw) < 3]

            self.log('', self)
            self.log('Current selection is: ' + str(bw), self)

            t_delta = time.time() - t_delta
            av_delta = t_delta / max(len(self._cache), 1)
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
            t_delta = time.time()
            if (t_delta - self._upd8ed) / 60 > 6 * self.Toolkit.Orbit:
                self._cache = {s: {} for s in self.Wrapper.symbols()}
                self._upd8ed = t_delta
                self._calcul8ed = False

            self.log('', self)
            self.log('Updating BOOK/HISTORY/OHLC info about symbols: ' +
                     str(set(self._cache)), self)

            self.log('', self)
            self.log('({0} total)'.format(len(self._cache)), self)

            for s in self._cache:
                if not self.Toolkit.halt():
                    self._cache[s]['book'] = self.Wrapper.book(s, 1)

                if not self.Toolkit.halt():
                    self._cache[s]['history'] = self.Wrapper.history(s, t_delta)

                if not self.Toolkit.halt():
                    self._cache[s]['ohlc'] = self.Wrapper.history(s)

                if None in self._cache[s].values():
                    self._cache[s] = {}
            self._cache = {k: v for k, v in self._cache.items() if len(v) > 0}

            t_delta = time.time() - t_delta
            av_delta = t_delta / max(len(self._cache), 1)
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

            v = self._volatility(symbol)  # last 24 hours
            t = self._trend(symbol)  # last 20 minutes
            m = self._momentum(symbol)  # right now

            if None not in [m, t, v]:
                return self.Toolkit.smooth(m * -t * v)
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
            for amount in self._cache[symbol]['book'].values():
                if amount > 0:
                    asks += amount
                else:
                    bids += amount

            if asks != 0:
                m = 100 * (abs(bids / asks) - 1)
                return [None, m][m > 0]
        except:
            self.log(traceback.format_exc(), self)

    def _trend(self, symbol, quantile=.1):
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
                p_open, p_high, p_low, p_close = tmp3[0], max(tmp3), min(tmp3), tmp3[-1]
                if p_close < 1E-5:  # getting rid of DOGE etc.
                    return

                x = 100 * (p_close / p_high - 1)  # always <= 0
                y = 100 * (p_close / p_low - 1)  # always >= 0
                z = 100 * (p_close / p_open - 1)  # any
                return (x + y + z) / 3
        except:
            self.log(traceback.format_exc(), self)

    def _volatility(self, symbol):
        """
        https://www.investopedia.com/terms/v/volatility.asp
        """

        try:
            if self.Toolkit.halt():
                return

            p_open, p_high, p_low, p_close = self._cache[symbol]['ohlc']
            tendency = 100 * (p_close / p_open - 1)

            if tendency > 0:
                return 100 * (p_high / p_low - 1)
        except:
            self.log(traceback.format_exc(), self)
