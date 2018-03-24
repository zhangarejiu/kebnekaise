# todo

import hashlib
import hmac
import json
import time

from calendar import timegm
from urllib import parse, request


class Wrapper(object):
    """
    Reference:

    https://github.com/binance-exchange/binance-official-api-docs
    """

    def __init__(self, toolkit):
        """
        Constructor method.
        """

        self.Brand, self.Fee = 'binance', .1

        self.Toolkit = toolkit
        self.Key, self.Secret = self.Toolkit.setup(self.Brand)
        self.log, self.err = self.Toolkit.log, self.Toolkit.err

    def symbols(self, errors=0):
        """
        """

        call = locals()

        try:
            return

        except:
            self.err(call)

    def book(self, symbol, margin=3, errors=0):
        """
        """

        call = locals()

        try:
            return

        except:
            self.err(call)

    def history(self, symbol, errors=0):
        """
        """

        call = locals()

        try:
            return

        except:
            self.err(call)

    def balance(self, errors=0):
        """
        """

        call = locals()

        try:
            return

        except:
            self.err(call)

    def fire(self, amount, price, symbol, errors=0):
        """
        """

        call = locals()

        try:
            return

        except:
            self.err(call)

    def orders(self, order_id=None, errors=0):
        """
        """

        call = locals()

        try:
            return

        except:
            self.err(call)

    def _payload(self, req_uri, signing=True, errors=0):
        """
        """

        call = locals()

        try:
            return

        except:
            self.err(call)

    def _request(self, command, options=None, errors=0):
        """
        """

        call = locals()

        try:
            return

        except:
            self.err(call)
