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
        self._cache, self._updated = {}, 0.

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
            self.log('Updating dataset of top symbols...', self)

            t_delta = time.time()
            ratio = len(self._cache) / len(self.Wrapper.symbols())
            tail = str(round(100 * ratio, 3)) + ' % of the symbols in uptrend.'

            tmp = {s: i for s, i in self._cache.items() if i > 0}
            tmp = {k: round(v, 3) for k, v in tmp.items()}

            self.log('', self)
            self.log('Financial indexes are: ' + str(tmp), self)

            self.log('', self)
            if ratio > 2 / 3:
                self.log('Altcoins UP: ' + tail, self)
                tmp = dict(sorted(tmp.items(), key=lambda k: k[1])[-5:])
            else:
                self.log('Altcoins DOWN: ' + tail, self)
                tmp = {}
            tmp = [tmp, {}][len(tmp) < 3]

            self.log('', self)
            self.log('Current selection is: ' + str(tmp), self)
            t_delta = time.time() - t_delta

            self.log('', self)
            self.log('...calculation done in {0} s.'.format(round(t_delta, 3)), self)
            return tmp
        except:
            self.log(traceback.format_exc(), self)

    def _update(self):
        """
        """

        try:
            if self.Toolkit.halt():
                return

            self.log('', self)
            self.log('Updating financial indexes DB...', self)
            t_delta = time.time()

            ls = len(self._cache)
            if (t_delta - self._updated) / 60 > 5 * self.Toolkit.Orbit:
                ls = 0
                for s in self.Wrapper.symbols():
                    t = self._long_trend(s)
                    if t is not None and t > 0:
                        self._cache[s] = 0.
                    ls += 1
                self._updated = t_delta

            self.log('', self)
            self.log('Target symbols: ' + str(set(self._cache)), self)

            now = time.time()
            for s in self._cache:
                self._cache[s] = 0.
                st = self._short_trend(s, now)
                if st is not None and st < 0:
                    self._cache[s] = -st

            for s in self._cache:
                if self._cache[s] > 0:
                    st = self._cache[s]
                    vt = self._volume_trend(s)

                    if vt is not None and vt > 0:
                        self._cache[s] = self.Toolkit.smooth(vt / st)
                    else:
                        self._cache[s] = 0.

            t_delta = time.time() - t_delta
            av_delta = t_delta / max(ls, 1)
            stats = round(t_delta, 3), round(av_delta, 5)

            self.log('', self)
            self.log('...update done in {0} s, average {1} s/symbol.'.format(*stats), self)
        except:
            self.log(traceback.format_exc(), self)

    def _long_trend(self, symbol):
        """
        """

        try:
            if self.Toolkit.halt():
                return

            ohlc = self.Wrapper.history(symbol)
            if ohlc is not None:
                p_open, p_high, p_low, p_close = ohlc
                if p_open > 0:
                    return 100 * (p_close / p_open - 1)
            return 0.
        except:
            self.log(traceback.format_exc(), self)

    def _short_trend(self, symbol, cutoff):
        """
        """

        try:
            if self.Toolkit.halt():
                return

            tmp, V = [0, 0], []
            history = self.Wrapper.history(symbol, cutoff)

            for epoch1, amount1, price1 in history:
                for epoch2, amount2, price2 in history:
                    if epoch2 > epoch1 and -amount2 >= amount1 > 0:
                        V.append(amount1 - amount2)
                        tmp[0] += 100 * (price2 / price1 - 1)
                        tmp[1] += 1
            V = sum(V) / max(len(V), 1)

            if tmp[1] > 0:
                return V * tmp[0] / tmp[1]
            return 0.
        except:
            self.log(traceback.format_exc(), self)

    def _volume_trend(self, symbol, population=3):
        """
        """

        try:
            if self.Toolkit.halt():
                return

            def _trend(book):
                asks, bids = 0, 0
                for amount in book.values():
                    if amount > 0:
                        asks += amount
                    else:
                        bids += amount

                V.append(asks - bids)
                if asks > 0:
                    return 100 * (abs(bids / asks) - 1)

            tmp, V = [], []
            while len(tmp) < population:
                t = _trend(self.Wrapper.book(symbol))
                if t is not None:
                    tmp.append(t)

            V = sum(V) / max(len(V), 1)
            return V * sum(tmp) / population
        except:
            self.log(traceback.format_exc(), self)
