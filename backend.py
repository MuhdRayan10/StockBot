from easy_sqlite3 import *
import random


class StockMarket:
    def __init__(self, bot):
        self.bot = bot
        self.increase = {10: [1, 2, 0, 0, -1, -2],
                         50: [1, 2, 3, 0, 0, -1, -2, -3],
                         100: [1, 2, 3, 4, 0, 0, -1, -2, -3, -4],
                         250: [1, 2, 3, 4, 5, 6, 0, 0, -1, -2, -3, -4, -5, -6],
                         500: [1, 2, 3, 4, 5, 6, 7, 8, 0, 0, -1, -2, -3, -4, -5, -6, -7, -8],
                         1000: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 0, 0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10]}

        db = Database("stocks")
        db.create_table("stock_list",
                        {"stock": "TEXT", "price": INT, "holdings": INT, "market_cap": INT, "history": "TEXT"})

        db.close()

    def add_stock(self, stock_name: str, start_price: int):

        db = Database("stocks")

        if db.if_exists("stock_list", where={"stock": stock_name}):
            db.close()
            return

        db.insert("stock_list", {"stock": stock_name, "price": start_price, "holdings": 0, "market_cap": 0,
                                 "history": f"[{start_price}]"})
        db.close()

    def update_stocks(self):
        db = Database("stocks")
        stock_data = db.select("stock_list")

        for data in stock_data:
            self.update_stock_price(data[0])

    def update_stock_price(self, stock):
        db = Database("stocks")
        stock_data = db.select("stock_list", where={"stock": stock}, size=1)

        price = stock_data[1]

        limit = 0
        for lim in self.increase:
            if lim >= price:
                limit += lim
                print(limit)
                break

        limit += 1000 if not limit else 0

        price += random.choice(self.increase[limit])

        print(stock, stock_data[1], price)

        history = eval(stock_data[4])
        history.append(price)

        db.update("stock_list", {"price": price, "market_cap": price * stock_data[2], "history": repr(history)},
                  where={"stock": stock})
        db.close()

        db.close()

    def percentage(self, stock, db):
        prices = db.select("stock_list", where={"stock": stock[0]}, size=1)

        prices = eval(prices[4])

        n = 120

        if len(prices) > n:
            prices = prices[-n:]

        return float(prices[-1] - prices[0]) / prices[0]

    def get_stocks(self):
        db = Database("stocks")

        data = db.select("stock_list")

        stocks, prices, percentages = "", "", ""
        for stock in data:
            increase = round(self.percentage(stock, db), 2)
            symbol = "🟢" if increase >= 0 else "🔴"
            stocks += f"\n{stock[0]}"
            prices += f"\n${stock[1]}"
            percentages += f"\n{round(increase * 100, 2)}% {symbol}"

        return stocks, prices, percentages
