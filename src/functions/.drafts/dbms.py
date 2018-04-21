import inspect
import os
import pickle
import traceback


class Database(object):
    """
    Another simplified solution for persistence.
    """

    def __init__(self, wrapper):
        """
        Constructor method.
        """

        self.Wrapper = wrapper
        self.Brand = self.Wrapper.Brand
        self.Toolkit = self.Wrapper.Toolkit
        self.Path = self.Toolkit.Path

        self.log = self.Toolkit.log
        self._dbfile = self.Path + '/data/' + self.Brand + '.db'
        self._check()

        self.log(self.Toolkit.Greeting, self)

    def load(self, account):
        """
        """

        try:
            account = dict(inspect.getmembers(account))['__class__'].__name__.upper()

            with open(self._dbfile, 'rb') as fp:
                tmp = pickle.load(fp)

            if account not in tmp:
                tmp[account] = 0
                with open(self._dbfile, 'wb') as fp:
                    pickle.dump(tmp, fp, pickle.HIGHEST_PROTOCOL)

            return tmp[account]
        except:
            self.log(traceback.format_exc(), self)

    def save(self, account, data):
        """
        """

        try:
            account = dict(inspect.getmembers(account))['__class__'].__name__.upper()

            with open(self._dbfile, 'rb') as fp:
                tmp = pickle.load(fp)
            tmp[account] = data

            with open(self._dbfile, 'wb') as fp:
                pickle.dump(tmp, fp, pickle.HIGHEST_PROTOCOL)
        except:
            self.log(traceback.format_exc(), self)

    def reset(self, account):
        """
        """

        try:
            account = dict(inspect.getmembers(account))['__class__'].__name__.upper()
            tmp = {account: 0}

            with open(self._dbfile, 'wb') as fp:
                pickle.dump(tmp, fp, pickle.HIGHEST_PROTOCOL)
        except:
            self.log(traceback.format_exc(), self)

    def _check(self):
        """
        """

        try:
            if not os.path.exists(self._dbfile):
                os.mknod(self._dbfile)

                with open(self._dbfile, 'wb') as fp:
                    pickle.dump({}, fp, pickle.HIGHEST_PROTOCOL)
        except:
            self.log(traceback.format_exc(), self)
