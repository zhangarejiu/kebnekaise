import os
import time
import traceback


now_str = time.strftime('%Y.%m.%d.%Z.%H.%M.%S', time.gmtime())
now_str = now_str.replace('GMT', 'UTC')
today = now_str[:10].replace('.', '_')
cache = {}


def _print(msg):
    with open(today + '.txt', 'w') as fp:
        fp.write(str(msg))


try:
    path = '../../logs'
    assert os.path.exists(path)

    for logfile in os.listdir(path):
        with open(path + '/' + logfile, 'r') as fp:
            cache[logfile] = []
            for line in fp.readlines():
                if 'profits' in line:
                    d = eval(line[52:])
                    cache[logfile].append((line[:23], {
                        k: v for k, v in d['profits'].items()
                        if k in d['protected'][:2]
                    }))
    _print(cache)

except AssertionError:
    _print(cache)
except:
    _print(traceback.format_exc())
