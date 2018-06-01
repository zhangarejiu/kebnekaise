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
        self.log(self.Toolkit.Greeting, self)

    def query(self, account, data=None):
        """
        """

        try:
            account = dict(inspect.getmembers(account))['__class__'].__name__.upper()
            path = self.Path + '/data/'
            fqfn = path + self.Brand + '.db'

            if data is None:  # reads only you
                tmp = self._load(fqfn)
                if account in tmp:
                    return tmp[account]
                return {}

            elif type(data) in [int, float]:  # reads everyone
                tmp = {}
                for dbfile in os.listdir(path):
                    brand = dbfile.split('.')[0].upper()
                    data = self._load(path + dbfile)
                    if account in data:
                        tmp[brand] = data[account]
                    else:
                        tmp[brand] = {}
                return tmp

            else:  # write (only you)
                assert type(data) == dict
                self._dump(fqfn, {account: data})

        except AssertionError:
            return
        except:
            self.log(traceback.format_exc(), self)

    def _load(self, archive, data=None):
        """
        """

        try:
            self.Toolkit.check(archive)
            if os.stat(archive).st_size == 0:
                with open(archive, 'wb') as fp:
                    pickle.dump({}, fp, pickle.HIGHEST_PROTOCOL)

            with open(archive, 'rb') as fp:
                tmp = pickle.load(fp)

            if data is not None:
                tmp.update(data)
            return tmp
        except:
            self.log(traceback.format_exc(), self)

    def _dump(self, archive, data=None):
        """
        """

        try:
            if data is None:
                data = {}

            data = self._load(archive, data)
            with open(archive, 'wb') as fp:
                pickle.dump(data, fp, pickle.HIGHEST_PROTOCOL)
        except:
            self.log(traceback.format_exc(), self)