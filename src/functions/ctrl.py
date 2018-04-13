import inspect
import os
import random
import sys
import time
import traceback

from configparser import ConfigParser


class Toolkit(object):
    """
    If a feature is needed in more than one class, it's better simply put it here.
    """

    def __init__(self, path):
        """
        Constructor method.
        """

        self.Path = path
        self.CParser = ConfigParser(allow_no_value=True)
        self.CParser.read(self.Path + '/bin/conf.ini')
        self.Plugins = self._plugins()
        self.Quota = 1E-3

        self.Phi = (1 + 5 ** .5) / 2  # https://en.wikipedia.org/wiki/Golden_ratio
        self.Greeting = 'This component was successfully started.'
        self._halted = False

    def setup(self, brand=None):
        """
        Read settings at '/bin/conf.ini' and retrieve it
        from [DEFAULT] or [PLUGIN_NAME] section
        """

        try:
            if brand is None:
                return dict(self.CParser.defaults())
            else:
                plg = brand.upper()
                key = self.CParser.get(plg, 'key')
                secret = self.CParser.get(plg, 'secret').encode()
                return key, secret
        except:
            self.log(traceback.format_exc(), self)

    def ticker(self, brand, symbol):
        """
        Just returns the current Lowest Ask / Highest Bid for a given market & symbol.
        """

        try:
            wrapper = {plg for plg in self.Plugins if plg.Brand == brand}.pop()

            book = wrapper.book(symbol, 1)
            if book is None:
                return 0., 0.

            asks, bids = [], []
            for price, amount in book.items():
                if amount > 0:
                    asks.append(price)
                else:
                    bids.append(price)
            return min(asks), max(bids)
        except:
            self.log(traceback.format_exc(), self)

    def log(self, message, caller=None):
        """
        Better starve to death before use this:

        https://docs.python.org/release/3.4.3/library/logging.html
        """

        now_str = time.strftime('%Y.%m.%d.%Z.%H.%M.%S', time.gmtime())
        today = now_str[:10].replace('.', '_')
        logfile = self.Path + '/logs/' + today + '.'

        try:
            if caller is not None:
                operation = caller.Brand.upper()
                component = dict(inspect.getmembers(caller))['__class__'].__name__.upper()
            else:
                operation, component = 'Kebnekaise', 'TOOLKIT'

            message = '{0} |{1}| {2}\n'.format(now_str, component, message)
            with open(logfile + operation + '.log', 'a') as fp:
                fp.writelines([message])
        except:
            with open(logfile + 'err', 'a') as fp:
                fp.writelines([traceback.format_exc() + '\n'])

    def wait(self, minutes=1.):
        """
        A more sophisticated alternative to 'time.sleep()', puts random sized delays.
        """

        try:
            delay = int(60 * minutes)
            delay = [delay, 10][delay < 10]

            c, r = 0, random.randrange(delay - 10, delay + 10)

            while not (self.halt() or c == r):
                time.sleep(1)
                c += 1

            return r
        except:
            self.log(traceback.format_exc(), self)

    def halt(self, send=False, remove=False):
        """
        READ for the HALT command, SEND it, or CLEAN the HALT file.

        IMPORTANT:
            In order to prevents the system from ignoring your halt commands, please
            don't forget to include this test in your (heavy) loops!

        Examples:
            while not self.Toolkit.halt():
                (some complex or slow code here, like
                downloads or some kind of fancy calculations...)

            for element in data:
                if not self.Toolkit.halt():
                    (some complex or slow code here, like
                    downloads or some kind of fancy calculations...)
        """

        try:
            halt_file = self.Path + '/logs/.halt'
            # time.sleep(1 / 9)

            if remove:
                os.remove(halt_file)
            elif send:
                os.mknod(halt_file)
            elif self._halted:
                return self._halted
            else:
                self._halted = os.path.exists(halt_file)
                return self._halted

        except (FileExistsError, FileNotFoundError):
            pass
        except:
            self.log(traceback.format_exc(), self)

    def _plugins(self):
        """
        Returns a set with all plugins (the object only) enabled
        in 'src/plugins/__init__.py'
        or 'src/plugins/sandbox/__init__.py'.
        """

        try:
            def test_uri(uri):
                exclude = {'src.plugins', 'src.plugins.sandbox', }
                startsw = {uri.startswith(e) for e in exclude}
                return uri not in exclude and True in startsw

            return {m_obj.Wrapper(self) for m_uri, m_obj in sys.modules.items()
                    if test_uri(m_uri)}
        except:
            self.log(traceback.format_exc(), self)


class Auditor(object):
    """
    Health test for enabled plugins.
    """

    def __init__(self, wrapper):
        """
        Constructor method.
        """

        self.Wrapper = wrapper
        self.Brand = self.Wrapper.Brand
        self._cache = {'errors': 0, 'symbols': [], 'balance': {}, 'orders': [], }

        self.Toolkit = self.Wrapper.Toolkit
        self.log = self.Toolkit.log
        self.log(self.Toolkit.Greeting, self)

    def test(self, fire_mode=True):
        """
        For each plugin, this will test all the functions on it.
        """

        try:
            self.log('', self)
            self.log('Starting test of the \'{0}\' API wrapper...'.format(
                self.Brand.upper()), self)

            quiz = [self._symbols, self._book, self._history, self._balance, self._buy,
                    self._sell, self._orders, self._cancel]

            for func in quiz[:[4, None][fire_mode]]:
                if self._cache['errors'] == 0 and not self.Toolkit.halt():
                    self.log('', self)
                    func()

            self.log('', self)
            self.log('All tests DONE with {0} error(s). Exiting...'.format(
                self._cache['errors']), self)
            return self._cache['errors'] == 0
        except:
            self.log(traceback.format_exc(), self)

    def _symbols(self):
        """
        Self explanatory...
        """

        try:
            self.log('Testing [SYMBOLS] functionality...', self)

            S = {s for s in self.Wrapper.symbols() if s[1] == 'btc'}
            ls = len(S)

            if ls > 0:
                engaged = {s for a, p, s in self.Wrapper.orders().values()}
                self._cache['symbols'] = list(S - engaged)
                random.shuffle(self._cache['symbols'])
            else:
                self._cache['errors'] += 1
            self.log('The response was: ' + str(S), self)

            self.log('', self)
            self.log('(Were found {0} symbols total)'.format(ls), self)
        except:
            self.log(traceback.format_exc(), self)
            self._cache['errors'] += 1

    def _book(self):
        """
        Self explanatory...
        """

        try:
            self.log('Testing [BOOK] functionality...', self)

            params = {'symbol': self._cache['symbols'][0],
                      'margin': round(self.Toolkit.Phi, 8), }
            self.log('Using the following parameters: ' + str(params), self)

            book = self.Wrapper.book(**params)
            self.log('The response was: ' + str(book), self)
        except:
            self.log(traceback.format_exc(), self)
            self._cache['errors'] += 1

    def _history(self):
        """
        Self explanatory...
        """

        try:
            self.log('Testing [HISTORY] functionality...', self)

            #params = {'symbol': self._cache['symbols'][1], 'cutoff': int(time.time())}
            params = {'symbol': ('eth', 'btc'), 'cutoff': int(time.time())}
            self.log('Using the following parameters: ' + str(params), self)

            history = self.Wrapper.history(**params)
            self.log('The response was: ' + str(history), self)
        except:
            self.log(traceback.format_exc(), self)
            self._cache['errors'] += 1

    def _balance(self):
        """
        Self explanatory...
        """

        try:
            self.log('Testing [BALANCE] functionality...', self)

            self._cache['balance'] = self.Wrapper.balance()
            self.log('The response was: ' + str(self._cache['balance']), self)

            if self._cache['balance']['btc'][0] < self.Toolkit.Quota:
                self.log('', self)
                self.log('BALANCE ERROR: please make sure you have at least BTC ' +
                         str(self.Toolkit.Quota) + ' available in your account, in ' +
                         'order to proceed with other tests.', self)
                self._cache['errors'] += 1
        except:
            self.log(traceback.format_exc(), self)
            self._cache['errors'] += 1

    def _buy(self):
        """
        Self explanatory...
        """

        try:
            self.log('Testing [FIRE] functionality in [BUY] mode...', self)

            params = {'symbol': self._cache['symbols'][2]}
            price = .97 * self.Toolkit.ticker(self.Brand, params['symbol'])[1]  # h_bid
            amount = (1 - self.Wrapper.Fee / 100) * self.Toolkit.Quota / price
            params.update({'amount': round(amount, 8), 'price': round(price, 8), })

            self.log('Putting a BUY order with parameters: ' + str(params), self)
            oid = self.Wrapper.fire(**params)

            if oid != 0:
                self._cache['orders'].append(oid)
                self.log('The response was: ' + str(oid), self)
            else:
                self.log('Internal error or insufficient funds to make BUY tests...', self)
        except:
            self.log(traceback.format_exc(), self)
            self._cache['errors'] += 1

    def _sell(self):
        """
        Self explanatory...
        """

        try:
            self.log('Testing [FIRE] functionality in [SELL] mode...', self)

            params = {'symbol': ('btc', 'usdt')}
            price = 1.03 * self.Toolkit.ticker(self.Brand, params['symbol'])[0]  # l_ask
            amount = -1 * self.Toolkit.Quota
            params.update({'amount': round(amount, 8), 'price': round(price, 8), })

            self.log('Putting a SELL order with parameters: ' + str(params), self)
            oid = self.Wrapper.fire(**params)

            if oid != 0:
                self._cache['orders'].append(oid)
                self.log('The response was: ' + str(oid), self)
            else:
                self.log('Internal error or insufficient funds to make SELL tests...', self)
        except:
            self.log(traceback.format_exc(), self)
            self._cache['errors'] += 1

    def _orders(self):
        """
        Self explanatory...
        """

        try:
            self.log('Testing [ORDERS] functionality...', self)

            O = self.Wrapper.orders()
            self.log('The response was: ' + str(O), self)
        except:
            self.log(traceback.format_exc(), self)
            self._cache['errors'] += 1

    def _cancel(self):
        """
        Self explanatory...
        """

        try:
            self.log('Testing [CANCEL] functionality...', self)

            for oid in self._cache['orders']:
                params = {'order_id': oid}

                self.log('', self)
                self.log('Using the following parameters: ' + str(params), self)
                self.log('The response was: ' + str(self.Wrapper.orders(**params)), self)

            orders = list(self.Wrapper.orders())
            self.log('(Current open orders are: {0})'.format(orders), self)
        except:
            self.log(traceback.format_exc(), self)
            self._cache['errors'] += 1
