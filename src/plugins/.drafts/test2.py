ark = {
    'symbol': 'ARKBTC', 'status': 'TRADING', 'baseAsset': 'ARK', 'baseAssetPrecision': 8, 'quoteAsset': 'BTC',
    'quotePrecision': 8, 'orderTypes': ['LIMIT', 'LIMIT_MAKER', 'MARKET', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT_LIMIT'],
    'icebergAllowed': False, 'filters': [
        {'filterType': 'PRICE_FILTER', 'minPrice': '0.00000010', 'maxPrice': '100000.00000000',
         'tickSize': '0.00000010'},
        {'filterType': 'LOT_SIZE', 'minQty': '0.01000000', 'maxQty': '90000000.00000000', 'stepSize': '0.01000000'},
        {'filterType': 'MIN_NOTIONAL', 'minNotional': '0.00100000'}]
}

# P = 0.0003792
# am = q/P = 2.6371308016877637
# am * m / ss = 2.6371308016877637 * (.1 / 100) / 0.01 = 0.26371308016877637

mco = {
    'symbol': 'MCOBTC', 'status': 'TRADING', 'baseAsset': 'MCO', 'baseAssetPrecision': 8, 'quoteAsset': 'BTC',
    'quotePrecision': 8, 'orderTypes': ['LIMIT', 'LIMIT_MAKER', 'MARKET', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT_LIMIT'],
    'icebergAllowed': False, 'filters': [
        {'filterType': 'PRICE_FILTER', 'minPrice': '0.00000100', 'maxPrice': '100000.00000000',
         'tickSize': '0.00000100'},
        {'filterType': 'LOT_SIZE', 'minQty': '0.01000000', 'maxQty': '10000000.00000000', 'stepSize': '0.01000000'},
        {'filterType': 'MIN_NOTIONAL', 'minNotional': '0.00100000'}]
}

# P = 0.001203
# am = q/P = 0.8312551953449708
# am * m / ss = 0.8312551953449708 * (.1 / 100) / 0.01 = 0.08312551953449708

tnt = {
    'symbol': 'TNTBTC', 'status': 'TRADING', 'baseAsset': 'TNT', 'baseAssetPrecision': 8, 'quoteAsset': 'BTC',
    'quotePrecision': 8, 'orderTypes': ['LIMIT', 'LIMIT_MAKER', 'MARKET', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT_LIMIT'],
    'icebergAllowed': False, 'filters': [
        {'filterType': 'PRICE_FILTER', 'minPrice': '0.00000001', 'maxPrice': '100000.00000000',
         'tickSize': '0.00000001'},
        {'filterType': 'LOT_SIZE', 'minQty': '1.00000000', 'maxQty': '90000000.00000000', 'stepSize': '1.00000000'},
        {'filterType': 'MIN_NOTIONAL', 'minNotional': '0.00100000'}]
}

# P = 0.00001411
# am = q/P = 70.87172218284904
# am * m / ss = 70.87172218284904 * (.1 / 100) / 1.0 = 0.07087172218284904
