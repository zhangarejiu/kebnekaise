import hashlib
import hmac
import json
import time

from urllib import parse, request


Key = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
Secret = 'yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy'.encode()

base_uri = 'https://api.binance.com/'
req_uri = 'api/v3/account', {'method': 'GET'}

# type(req_uri) == tuple
method = req_uri[1].pop('method')
ts = ['timestamp={}', '&timestamp={}'][len(req_uri[1]) > 0]
query = parse.urlencode(sorted(req_uri[1].items()))
query += ts.format(int(1E3 * time.time()))

req_uri[1]['method'] = method
sign = hmac.new(Secret, query.encode(), hashlib.sha256).hexdigest()
query += '&signature={}'.format(sign)
params = {'method': method, 'url': base_uri + req_uri[0] + '?' + query,
          'headers': {'X-MBX-APIKEY': Key, }, }

print(params)
tmp = json.loads(request.urlopen(request.Request(**params)).read().decode())

print(tmp)
