import time


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
        self._cache = [{}, {}, {}]

        self.Toolkit = self.Wrapper.Toolkit
        self.log, self.err = self.Toolkit.log, self.Toolkit.err
        self.log(self.Toolkit.Greeting, self)

    def broadway(self, symbols, cached=False, errors=0):
        """
        https://www.pokernews.com/pokerterms/broadway.htm
        """

        call = locals()

        try:
            if not cached:
                self._download(symbols)
            self._update()

            common = set(
                self._cache[2]['L']) & set(
                self._cache[2]['M']) & set(
                self._cache[2]['T'])

            bw = {symbol: self._cache[2]['M'].index(symbol) / (
                    self._cache[2]['T'].index(symbol) + 1) for symbol in common}
            bw = set(dict(sorted(bw.items(), key=lambda k: k[1])[-5:]))
            bw = {s: 1 + self._cache[2]['L'].index(s) for s in bw}

            self.log('Current selection is: ' + str(bw), self)
            return bw
        except:
            self.err(call)

    def _download(self, symbols, errors=0):
        """
        Downloads the book of orders, for every element in the
        given symbol set, storing these data in the memory.
        """

        call = locals()

        try:
            self.log('', self)
            self.log('Downloading orders BOOK & trades HISTORY information for {0} symbols...'
                     .format(len(symbols)), self)
            t_delta = time.time()

            for s in symbols:
                if not self.Toolkit.halt():
                    book = self.Wrapper.book(s, 5)
                    if book is not None:
                        self._cache[0][s] = book

                    history = self.Wrapper.history(s)
                    if history is not None:
                        self._cache[1][s] = history

            t_delta = time.time() - t_delta
            av_delta = t_delta / len(symbols)
            stats = round(t_delta, 3), round(av_delta, 5)

            self.log('', self)
            self.log('...download done in {0} s, average {1} s/symbol.'.format(*stats), self)
            return stats
        except:
            self.err(call)

    def _update(self, errors=0):
        """
        It serves to manage the structure 'self._metrics'.
        """

        call = locals()

        try:
            self.log('', self)
            self.log('Updating financial indexes database...', self)
            t_delta = time.time()

            tmp_liquidity, tmp_momentum, tmp_trend = [], [], []
            for symbol, book in self._cache[0].items():
                if not self.Toolkit.halt():
                    tmp_liquidity += [(self._liquidity(book), symbol)]
                    tmp_momentum += [(self._momentum(book), symbol)]

            for symbol, history in self._cache[1].items():
                if not self.Toolkit.halt():
                    tmp_trend += [(self._trend(history), symbol)]

            self._cache[2] = {
                'L': [s for l, s in sorted(tmp_liquidity)],
                'M': [s for m, s in sorted(tmp_momentum)],
                'T': [s for t, s in sorted(tmp_trend)],
            }
            cardinality = max(len(v) for v in self._cache[2].values())

            t_delta = time.time() - t_delta
            av_delta = t_delta / cardinality
            stats = round(t_delta, 3), round(av_delta, 5)

            self.log('', self)
            self.log('...update done in {0} s, average {1} s/symbol.'.format(*stats), self)
            return stats
        except:
            self.err(call)

    def _liquidity(self, book, errors=0):
        """
        The multiplicative inverse or reciprocal of the SPREAD.
        """

        call = locals()

        try:
            asks, bids = [], []

            for p, a in book.items():
                if a > 0:
                    asks.append(p)
                else:
                    bids.append(p)

            spread = 100 * (min(asks) / max(bids) - 1)
            return 1 / spread
        except:
            self.err(call)

    def _momentum(self, book, errors=0):
        """
        How many % does the volume in BIDS exceed the volume in ASKS?

        From:
            Algorithmic Trading: Winning Strategies and Their Rationale
            Chan, Ernest P., 2013 - page 164 (ISBN-13: 978-1118460146)
        """

        call = locals()

        try:
            asks, bids = 0, 0

            for v in book.values():
                if v > 0:
                    asks += v
                else:
                    bids += v

            return 100 * (abs(bids / asks) - 1)
        except:
            self.err(call)

    def _trend(self, history, errors=0):
        """
        https://www.investopedia.com/terms/o/ohlcchart.asp
        """

        call = locals()

        try:
            p_open, p_high, p_low, p_close = 0, 0, 0, 0
            h = [(a / abs(a)) * p for _, a, p in history]

            fail = -1E3
            if len({p > 0 for p in h}) == 1:
                return fail

            for price in h:
                if p_open == 0:
                    p_open = [p_open, price][price > 0]
                else:
                    if price > 0:
                        p_low = [min(p_low, price), price][p_low == 0]
                    else:
                        p = abs(price)
                        p_high = max(p_high, p)
                        p_close = p

            if p_open * p_high * p_low * p_close > 0:
                f = 100 * (p_high / p_open - 1)
                g = 100 * (p_close / p_low - 1)
                h = 100 * (p_close / p_open - 1)
                return (f + g + h) / 3
            else:
                return fail
        except:
            self.err(call)