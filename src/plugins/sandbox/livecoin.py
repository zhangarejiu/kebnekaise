# todo

import hashlib
import hmac
import json
import time
import traceback

from urllib import parse, request


class Wrapper(object):
    """
    Reference:

    https://www.livecoin.net/api
    """

    def __init__(self, toolkit):
        """
        Constructor method.
        """

        self.Brand, self.Fee = 'livecoin', .18
        self._fails = 0

        self.Toolkit = toolkit
        self.Key, self.Secret = self.Toolkit.setup(self.Brand)
        self.log = self.Toolkit.log

    def symbols(self, btc_only=True):
        """
        """

        try:
            return

        except:
            self.log(traceback.format_exc(), self)

    def balance(self):
        """
        """

        try:
            return

        except:
            self.log(traceback.format_exc(), self)

    def ticker24h(self, symbol):
        """
        """

        try:
            return

        except:
            self.log(traceback.format_exc(), self)

    def book(self, symbol, margin=1):
        """
        """

        try:
            return

        except:
            self.log(traceback.format_exc(), self)

    def fire(self, amount, price, symbol):
        """
        """

        try:
            return

        except:
            self.log(traceback.format_exc(), self)

    def orders(self, order_id=None, recheck=3):
        """
        """

        try:
            return

        except:
            self.log(traceback.format_exc(), self)

    def _request(self, req_uri, signing=True):
        """
        """

        try:
            return

        except:
            self.log(traceback.format_exc(), self)
