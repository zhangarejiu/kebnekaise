DATA = {
    'ARKBTC': [(0.00037800, 4.12000000), (0.00037920, -4.11000000)],
    'TNTBTC': [(0.00001406, 111.00000000), (0.00001411, -110.00000000)],
    'MCOBTC': [(0.00119900, 1.29000000), (0.00120300, 1.28000000)]
}


def real_margin(margin, buy_price, buy_amount, sell_amount):
    """
    """

    notional1 = abs(buy_price * buy_amount)
    sell_price = (1 + margin / 100) * notional1 / abs(sell_amount)
    return 100 * (sell_price / buy_price - 1)


for symbol, ((buy_price, buy_amount), (sell_price, sell_amount)) in DATA.items():
    print()
    print(symbol)
    print(real_margin(.1, buy_price, buy_amount, sell_amount))
