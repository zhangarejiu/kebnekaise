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
            self._update()

            self.log('', self)
            self.log('Selecting top symbols by performance...', self)

            bw = {s: round(1E3 * i) for s, i in self._cache.items()}
            bw = {s: i for s, i in bw.items() if i > 0}
            self.log('Financial indexes are: ' + str(bw), self)

            self.Database.query(self, bw)
            common = self.Database.query(self, 0)
            #self.log('Common indexes are: ' + str(common), self)

            if not len(common) < 2:
                tmp = set()
                for bw in common.values():
                    if len(tmp) > 0:
                        tmp &= set(bw)
                    else:
                        tmp = set(bw)

                    if len(tmp) == 0:
                        break

                tmp = {s: [] for s in tmp}
                for bw in common.values():
                    for s in tmp:
                        tmp[s].append(bw[s])
            else:
                tmp = {}

            bw = {s: round(sum(l) / len(l)) for s, l in tmp.items()}
            self.log('Preliminary selection is: ' + str(bw), self)

            bw = dict(sorted(bw.items(), key=lambda k: k[1])[-5:])
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

            if len(self._cache) == 0:
                self.Database.query(self, self._cache)

            ls = len(symbols)
            self._cache.update({s: 0. for s in symbols - set(self._cache)})

            self.log('', self)
            self.log('Updating financial indexes for {} symbols...'.format(ls), self)
            t_delta = time.time()

            for s in symbols:
                I = self._index(s)
                if I is not None:
                    self._cache[s] = (self._cache[s] + I) / 2

            t_delta = time.time() - t_delta
            av_delta = t_delta / ls
            tt = round(t_delta, 3), round(av_delta, 5)
            self.log('...update done in {0} s, average {1} s/symbol.'.format(*tt), self)
        except:
            self.log(traceback.format_exc(), self)

    def _index(self, symbol):
        """
        """

        try:
            if self.Toolkit.halt():
                return

            t24h = self.Wrapper.ticker24h(symbol)
            assert t24h is not None

            book = self.Wrapper.book(symbol, 5)
            assert book is not None

            _open, _high, _low, _close, _volume = t24h
            assert _volume > 100 and _close > 1E-5

            volatility = 100 * (_high / _low - 1)
            assert volatility < 5

            variation = 100 * (_close / _open - 1)
            assert abs(variation) < 3

            asks, bids, l_ask, h_bid = 0., 0., 0., 0.
            for price, amount in book.items():
                if amount > 0:
                    l_ask = [price, min(price, l_ask)][l_ask > 0]
                    asks += price * amount
                else:
                    h_bid = [price, max(price, h_bid)][h_bid > 0]
                    bids += price * amount

            spread = 100 * (l_ask / h_bid - 1)
            assert spread < 1

            trend = 100 * (abs(bids / asks) - 1)
            return self.Toolkit.smooth(trend)
        except AssertionError:
            return 0.
        except:
            self.log(traceback.format_exc(), self)
