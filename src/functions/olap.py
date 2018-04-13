import inspect
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
        self.Account = dict(inspect.getmembers(self))['__class__'].__name__.upper()

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

            bw = {}
            for s, (bb, h) in self.Database.load(self.Account).items():

                b = {}
                if len(bb) > 0:
                    b = bb[max(bb)]

                m, t = self._momentum(b), self._trend(h)
                if None not in [m, t]:
                    if m > 100 and t < 0:
                        bw[s] = round(m * abs(t), 5)

            self.log('Trade indexes are: ' + str(bw), self)

            bw = dict(sorted(bw.items(), key=lambda k: k[1])[-5:])
            self.log('Current selection is: ' + str(bw), self)

            return bw
        except:
            self.log(traceback.format_exc(), self)

    def _update(self, hours=8):
        """
        Downloads the book of orders and trades history info.
        """

        try:
            symbols = {s for s in self.Wrapper.symbols() if s[1] == 'btc'}

            self.log('', self)
            self.log('Downloading orders BOOK & trades HISTORY information for {0} symbols...'
                     .format(len(symbols)), self)
            t_delta = time.time()

            tmp = self.Database.load(self.Account)
            if tmp == 0:
                tmp = {s: [{}, []] for s in symbols}

            b, h = {}, []
            for s in symbols:
                if not self.Toolkit.halt():
                    b = self.Wrapper.book(s, 1)

                if not self.Toolkit.halt():
                    h = self.Wrapper.history(s, t_delta)

                if None not in [b, h]:
                    if len(b) * len(h) > 0:
                        tmp[s][0].update({t_delta: b})
                        tmp[s][1] += [t for t in h if t not in tmp[s][1]]
                        tmp[s][1] = [t for t in tmp[s][1] if t_delta - t[0] < hours * 3600]
                    else:
                        tmp[s] = [{}, []]
            self.Database.save(self.Account, tmp)

            t_delta = time.time() - t_delta
            av_delta = t_delta / len(symbols)
            stats = round(t_delta, 3), round(av_delta, 5)

            self.log('', self)
            self.log('...download done in {0} s, average {1} s/symbol.'.format(*stats), self)
            return stats
        except:
            self.log(traceback.format_exc(), self)

    def _momentum(self, book):
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
            for v in book.values():
                if v > 0:
                    asks += v
                else:
                    bids += v

            if abs(asks * bids) > 0:
                return 100 * (abs(bids / asks) - 1)
        except:
            self.log(traceback.format_exc(), self)

    def _trend(self, history):
        """
        https://www.investopedia.com/terms/o/ohlcchart.asp
        """

        try:
            if self.Toolkit.halt():
                return

            h = self._vclock(history)
            if h is not None:
                p_open, p_high, p_low, p_close = h[0], max(h), min(h), h[-1]

                f = 100 * (p_high / p_open - 1)
                g = 100 * (p_close / p_low - 1)
                h = 100 * (p_close / p_open - 1)

                t = (f + g + h) / 3
                if abs(t) > 0:
                    return t
        except:
            self.log(traceback.format_exc(), self)

    def _vclock(self, history, quantile=1.):
        """
        https://www.amazon.com/dp/178272009X

        (Chapter 1) The Volume Clock: Insights into the High-Frequency Paradigm
        """

        try:
            if self.Toolkit.halt():
                return

            tmp1, tmp2, tmp3 = history.copy(), [0, 0], []
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

            cardinality = int(20 * quantile)
            if len(tmp3) > cardinality:
                tmp3.reverse()
                return tmp3[-cardinality:]
        except:
            self.log(traceback.format_exc(), self)
