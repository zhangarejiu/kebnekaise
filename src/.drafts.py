import random


blue_chips = {
    ('amp', 'btc'), ('blk', 'btc'), ('clam', 'btc'), ('dash', 'btc'), ('dcr', 'btc'),
    ('dgb', 'btc'), ('doge', 'btc'), ('emc2', 'btc'), ('etc', 'btc'), ('eth', 'btc'),
    ('exp', 'btc'), ('fct', 'btc'), ('game', 'btc'), ('gno', 'btc'), ('gnt', 'btc'),
    ('lbc', 'btc'), ('ltc', 'btc'), ('maid', 'btc'), ('nav', 'btc'), ('omg', 'btc'),
    ('pink', 'btc'), ('pot', 'btc'), ('ppc', 'btc'), ('rep', 'btc'), ('strat', 'btc'),
    ('vrc', 'btc'), ('xem', 'btc'), ('xmr', 'btc'), ('zec', 'btc')
}

_cache = [{}, {}, {'L': list(blue_chips), 'M': list(blue_chips), 'T': list(blue_chips), }]

db = 'L'
random.shuffle(_cache[2][db])
print()
print(db + ' = ' + str(_cache[2][db]))

db = 'M'
random.shuffle(_cache[2][db])
print()
print(db + ' = ' + str(_cache[2][db]))

db = 'T'
random.shuffle(_cache[2][db])
print()
print(db + ' = ' + str(_cache[2][db]))


def _index(data_id, symbol):
    return 1 + _cache[2][data_id].index(symbol)


common = set(_cache[2]['L']) & set(_cache[2]['M']) & set(_cache[2]['T'])

bw = {s: (_index('L', s) + _index('M', s)) / _index('T', s) for s in common}
print()
print(len(bw))

bw = {k: round(v, 3) for k, v in bw.items() if v > 2 * len(bw) / 3}
bw = dict(sorted(bw.items(), key=lambda k: k[1])[-5:])
print()
print(bw)
