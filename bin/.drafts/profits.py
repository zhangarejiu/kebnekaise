import os
import traceback


separator = '$$$$$ $$$$$ $$$$$ $$$$$ $$$$$ $$$$$ $$$$$'
path = '../../logs'

try:
    cache = {}
    for logfile in os.listdir(path):
        with open(path + '/' + logfile, 'r') as fp:
            cache[logfile] = []
            for line in fp.readlines():
                if 'profits' in line:
                    d = eval(line[52:])
                    cache[logfile].append(
                        (line[:23], {k: v for k, v in d['profits'].items() if k in d['protected'][:2]})
                    )
    print(cache)
except:
    print(traceback.format_exc())
