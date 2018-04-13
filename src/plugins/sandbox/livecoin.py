# todo

import hashlib
import hmac
import json
import time
import traceback

from calendar import timegm
from socket import gaierror
from urllib import parse, request
from urllib.error import URLError


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

        self.Toolkit = toolkit
        self.Key, self.Secret = self.Toolkit.setup(self.Brand)
        self.log, self.err = self.Toolkit.log, self.Toolkit.err

    def symbols(self):
        """
        """

        try:
            return

        except:
            self.log(traceback.format_exc())

    def book(self, symbol, margin=1):
        """
        """

        try:
            return

        except:
            self.log(traceback.format_exc())

    def history(self, symbol, cutoff):
        """
        """

        try:
            return

        except:
            self.log(traceback.format_exc())

    def balance(self):
        """
        """

        try:
            return

        except:
            self.log(traceback.format_exc())

    def fire(self, amount, price, symbol):
        """
        """

        try:
            return

        except:
            self.log(traceback.format_exc())

    def orders(self, order_id=None):
        """
        """

        try:
            return

        except:
            self.log(traceback.format_exc())

    def _request(self, req_uri, signing=True):
        """
        """

        try:
            return

        except:
            self.log(traceback.format_exc())
