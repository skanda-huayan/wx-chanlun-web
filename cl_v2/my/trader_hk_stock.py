from cl_v2 import exchange_futu
from cl_v2 import fun
from cl_v2 import trader

# 交易所对象放到外面，不然无法进行序列化
futu_ex = exchange_futu.ExchangeFutu()


class HKStockTrader(trader.Trader):
    """
    港股股票交易对象
    """

    def __init__(self, name, is_stock=True, is_futures=False, mmds=None, log=None, is_test=False):
        super().__init__(name, is_stock, is_futures, mmds, log, is_test=is_test)
        self.b_space = 3  # 资金分割数量

    # 做多买入
    def open_buy(self, code, opt):
        positions = futu_ex.positions()
        if len(positions) >= self.b_space:
            return False
        stock_info = futu_ex.stock_info(code)
        if stock_info is None:
            return False
        can_tv = futu_ex.can_trade_val(code)
        if can_tv is None:
            return False
        max_amount = (can_tv['max_margin_buy'] / (self.b_space - len(positions)))
        max_amount = max_amount - (max_amount % stock_info['lot_size'])

        if max_amount == 0:
            return False
        order = futu_ex.order(code, 'buy', max_amount)
        if order is False:
            fun.send_dd_msg('hk', '%s 下单失败 买入数量 %s' % (code, max_amount))
            return False
        msg = '股票买入 %s 价格 %s 数量 %s 原因 %s' % (code, order['dealt_avg_price'], order['dealt_amount'], opt['msg'])
        fun.send_dd_msg('hk', msg)

        return {'price': order['dealt_avg_price'], 'amount': order['dealt_amount']}

    # 做空卖出
    def open_sell(self, code, opt):
        positions = futu_ex.positions()
        if len(positions) >= self.b_space:
            return False
        stock_info = futu_ex.stock_info(code)
        if stock_info is None:
            return False
        can_tv = futu_ex.can_trade_val(code)
        if can_tv is None:
            return False
        max_amount = (can_tv['max_margin_short'] / (self.b_space - len(positions)))
        max_amount = max_amount - (max_amount % stock_info['lot_size'])
        if max_amount == 0:
            return False
        order = futu_ex.order(code, 'sell', max_amount)
        if order is False:
            fun.send_dd_msg('hk', '%s 下单失败 卖出数量 %s' % (code, max_amount))
            return False
        msg = '股票卖空 %s 价格 %s 数量 %s 原因 %s' % (code, order['dealt_avg_price'], order['dealt_amount'], opt['msg'])
        fun.send_dd_msg('hk', msg)

        return {'price': order['dealt_avg_price'], 'amount': order['dealt_amount']}

    # 做多平仓
    def close_buy(self, code, pos: trader.POSITION, opt):
        positions = futu_ex.positions(code)
        if len(positions) == 0:
            return {'price': pos.price, 'amount': pos.amount}

        order = futu_ex.order(code, 'sell', pos.amount)
        if order is False:
            fun.send_dd_msg('hk', '%s 下单失败 平仓卖出 %s' % (code, pos.amount))
            return False
        msg = '股票卖出 %s 价格 %s 数量 %s 盈亏 %s (%.2f%%) 原因 %s' % (
            code, order['dealt_avg_price'], order['dealt_amount'], positions[0]['profit_val'], positions[0]['profit'],
            opt['msg'])
        fun.send_dd_msg('hk', msg)
        return {'price': order['dealt_avg_price'], 'amount': order['dealt_amount']}

    # 做空平仓
    def close_sell(self, code, pos: trader.POSITION, opt):
        positions = futu_ex.positions(code)
        if len(positions) == 0:
            return {'price': pos.price, 'amount': pos.amount}

        order = futu_ex.order(code, 'buy', pos.amount)
        if order is False:
            fun.send_dd_msg('hk', '%s 下单失败 平仓买入 %s' % (code, pos.amount))
            return False
        msg = '股票平空 %s 价格 %s 数量 %s 盈亏 %s (%.2f%%) 原因 %s' % (
            code, order['dealt_avg_price'], order['dealt_amount'], positions[0]['profit_val'], positions[0]['profit'],
            opt['msg'])
        fun.send_dd_msg('hk', msg)
        return {'price': order['dealt_avg_price'], 'amount': order['dealt_amount']}
