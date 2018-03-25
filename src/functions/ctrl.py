import inspect
import os
import random
import sys
import time
import traceback

from configparser import ConfigParser
from os.path import exists


class Toolkit(object):
    """
    If a feature is needed in more than one class, it's better simply put it here.
    """

    def __init__(self, path):
        """
        Constructor method.
        """

        self.Path = path
        self.CP = ConfigParser(allow_no_value=True)
        self.CP.read(self.Path + '/bin/conf.ini')
        self.Plugins = self._plugins()
        self.Quota = 1E-3

        self.Phi = (1 + 5 ** .5) / 2  # https://en.wikipedia.org/wiki/Golden_ratio
        self.Greeting = 'This component was successfully started.'
        self._halted = False

    def setup(self, plugin_id=None, errors=0):
        """
        Read settings at '/bin/conf.ini' and retrieve it
        from [DEFAULT] or [PLUGIN_NAME] section
        """

        call = locals()

        try:
            if plugin_id is None:
                return dict(self.CP.defaults())
            else:
                plg = plugin_id.upper()
                key = self.CP.get(plg, 'key')
                secret = self.CP.get(plg, 'secret').encode()
                return key, secret
        except:
            self.err(call)

    def ticker(self, brand, symbol, errors=0):
        """
        Just returns the current Lowest Ask / Highest Bid for a given market & symbol.
        """

        call = locals()

        try:
            wrapper = {plg for plg in self.Plugins if plg.Brand == brand}.pop()
            call['self'] = wrapper

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
            self.err(call)

    def wait(self, minutes=1., errors=0):
        """
        A more sophisticated alternative to 'time.sleep()', puts random sized delays.
        """

        call = locals()

        try:
            delay = int(60 * minutes)
            delay = [delay, 10][delay < 10]

            c, r = 0, random.randrange(delay - 10, delay + 10)
            while not (self.halt() or c == r):
                time.sleep(1)
                c += 1
            return r
        except:
            self.err(call)

    def halt(self, send=False, remove=False, errors=0):
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

        call = locals()

        try:
            halt_file = self.Path + '/logs/.halt'
            time.sleep(.1)

            if remove:
                os.remove(halt_file)
            elif send:
                os.mknod(halt_file)
            elif self._halted:
                return self._halted
            else:
                self._halted = exists(halt_file)
                return self._halted

        except (FileExistsError, FileNotFoundError):
            pass
        except:
            self.err(call)

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

    def err(self, calling, max_tries=3, delay=3):
        """
        Tries to get a happy ending for error situations.
        """

        calling['errors'] += 1

        try:
            if self.halt():
                return

            caller_slice = inspect.stack()[1]
            caller_class = calling.pop('self')
            caller_method = dict(inspect.getmembers(caller_class))[caller_slice[3]]
            caller_class = [caller_class, None][caller_class == self]

            self.log('', caller_class)
            self.log('METHOD [{0}] FAILED!'.format(caller_slice[3]), caller_class)

            self.log('', caller_class)
            if calling['errors'] < max_tries and not self.halt():
                self.log('TRYING [{0}] AGAIN IN {1} SECONDS...'.format(
                    caller_slice[3], delay), caller_class)
                time.sleep(delay)
                return caller_method(**calling)
            else:
                exc_text = traceback.format_exc()
                [e_code, e_name, e_file, e_line] = self._brief_errors(exc_text)
                err_list = self._http_errors(e_code)

                if e_name in ['AssertionError', 'URLError']:
                    self.log('(' + e_name + ' | ' + e_file + ' | ' + e_line + ')', caller_class)
                elif e_name == 'HTTPError' and len(err_list) > 0:
                    for s in err_list: self.log(s, caller_class)
                else:
                    self.log(exc_text, caller_class)

                if 500 <= e_code < 600:
                    self.log('', caller_class)
                    self.log('Going to sleep for ~1 hour from now...', caller_class)
                    self.wait(60)
        except:
            self.log(traceback.format_exc())

    def _brief_errors(self, traceback_msg):
        """
        Extracts from:
            Traceback (most recent call last):
              File "/path/to/kebnekaise/directory/file.py", line 117, in <module>
                assert tmp is not None
            AssertionError

        Something like this:
            ('AssertionError', 'file.py', 'line 117')
        """

        try:
            e_code, e_name = 0, traceback_msg.splitlines()[-1].split(':')[0].split('.')[-1]
            if e_name == 'HTTPError':
                e_code = int(traceback_msg.splitlines()[-1].split(':')[1].split(' ')[-1])

            source = [s for s in traceback_msg.splitlines()
                      if 'File "/' in s and 'lib/python3' not in s].pop()

            e_file = source.split('"')[1].split('/')[-1]
            e_line = source.split(',')[1][1:]
            if e_name == 'gaierror':
                e_file, e_line = '', ''

            return e_code, e_name, e_file, e_line
        except:
            self.log(traceback.format_exc())

    def _http_errors(self, err_id):
        """
        Enhanced notification for errors and exceptions in the HTTP protocol.
        """

        try:
            wiki = '\n(https://en.wikipedia.org/wiki/List_of_HTTP_status_codes)'

            codes = {
                422: '''HTTP Error 422: Unprocessable Entity.
                        HINT: check the system clock or API keys.
                        WIKIPEDIA: "The request was well-formed but was unable to '''
                     + '''be followed due to semantic errors."'''
                     + wiki,
                429: '''HTTP Error 429: Too Many Requests.
                        HINT: check \'SECURITY DELAY\' in \'Wrapper._request()\'.
                        WIKIPEDIA: "The user has sent too many requests in a given '''
                     + '''amount of time."''' + wiki,
                503: '''HTTP Error 503: Service Temporarily Unavailable.
                        HINT: just wait. Your favorite website may be undergoing some '''
                     + '''scheduled maintenance.
                        WIKIPEDIA: "The server is currently unavailable (because it is '''
                     + '''overloaded or down for maintenance). Generally, this '''
                     + '''is a temporary state."''' + wiki,
                521: '''HTTP Error 521: Origin Down / Web Server Is Down.
                        HINT: allow some time to your favorite website fix that.
                        WIKIPEDIA: "The origin server has refused the connection '''
                     + '''from Cloudflare."''' + wiki,
                524: '''HTTP Error 524: Origin Time-out / A Timeout Occurred.
                        HINT: wait while I\'m trying again in a few moments.
                        WIKIPEDIA: "Cloudflare was able to complete a TCP '''
                     + '''connection to the origin server, but did not receive '''
                     + '''a timely HTTP response."''' + wiki,
            }

            if err_id in codes:
                return [s.strip() for s in codes[err_id].splitlines()]
            return []
        except:
            self.log(traceback.format_exc())

    def _plugins(self, errors=0):
        """
        Returns a set with all plugins (the object only) enabled
        in 'src/plugins/__init__.py'
        or 'src/plugins/sandbox/__init__.py'.
        """

        call = locals()

        try:
            def test_uri(uri):
                exclude = {'src.plugins', 'src.plugins.sandbox', }
                startsw = {uri.startswith(e) for e in exclude}
                return uri not in exclude and True in startsw

            return {m_obj.Wrapper(self) for m_uri, m_obj in sys.modules.items()
                    if test_uri(m_uri)}
        except:
            self.err(call)


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
        self.log, self.err = self.Toolkit.log, self.Toolkit.err
        self.log(self.Toolkit.Greeting, self)

    def test(self, fire_mode=True, errors=0):
        """
        For each plugin, this will test all the functions on it.
        """

        call = locals()

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
            self.err(call)

    def _symbols(self, errors=0):
        """
        Self explanatory...
        """

        call = locals()

        try:
            self.log('Testing [SYMBOLS] functionality...', self)

            S = self.Wrapper.symbols()
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
            self.err(call)
            self._cache['errors'] += 1

    def _book(self, errors=0):
        """
        Self explanatory...
        """

        call = locals()

        try:
            self.log('Testing [BOOK] functionality...', self)

            params = {'symbol': self._cache['symbols'][0],
                      'margin': round(self.Toolkit.Phi, 8), }
            self.log('Using the following parameters: ' + str(params), self)

            book = self.Wrapper.book(**params)
            self.log('The response was: ' + str(book), self)
        except:
            self.err(call)
            self._cache['errors'] += 1

    def _history(self, errors=0):
        """
        Self explanatory...
        """

        call = locals()

        try:
            self.log('Testing [HISTORY] functionality...', self)

            params = {'symbol': self._cache['symbols'][1]}
            self.log('Using the following parameters: ' + str(params), self)

            history = self.Wrapper.history(**params)
            self.log('The response was: ' + str(history), self)
        except:
            self.err(call)
            self._cache['errors'] += 1

    def _balance(self, errors=0):
        """
        Self explanatory...
        """

        call = locals()

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
            self.err(call)
            self._cache['errors'] += 1

    def _buy(self, errors=0):
        """
        Self explanatory...
        """

        call = locals()

        try:
            self.log('Testing [FIRE] functionality in [BUY] mode...', self)

            params = {'symbol': self._cache['symbols'][2]}
            price = .97 * self.Toolkit.ticker(self.Brand, params['symbol'])[1]  # h_bid
            amount = self.Toolkit.Quota / price
            params.update({'amount': round(amount, 8), 'price': round(price, 8), })

            self.log('Putting a BUY order with parameters: ' + str(params), self)
            oid = self.Wrapper.fire(**params)

            if oid != 0:
                self._cache['orders'].append(oid)
                self.log('The response was: ' + str(oid), self)
            else:
                self.log('Internal error or insufficient funds to make BUY tests...', self)
        except:
            self.err(call)
            self._cache['errors'] += 1

    def _sell(self, errors=0):
        """
        Self explanatory...
        """

        call = locals()

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
            self.err(call)
            self._cache['errors'] += 1

    def _orders(self, errors=0):
        """
        Self explanatory...
        """

        call = locals()

        try:
            self.log('Testing [ORDERS] functionality...', self)

            O = self.Wrapper.orders()
            self.log('The response was: ' + str(O), self)
        except:
            self.err(call)
            self._cache['errors'] += 1

    def _cancel(self, errors=0):
        """
        Self explanatory...
        """

        call = locals()

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
            self.err(call)
            self._cache['errors'] += 1
