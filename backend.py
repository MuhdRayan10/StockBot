import logging
from colorlog import ColoredFormatter
from easy_sqlite3 import *
import random

logger = logging.getLogger('stock-bot')
stream = logging.StreamHandler()

stream.setFormatter(ColoredFormatter("%(reset)s%(log_color)s%(levelname)-8s%(reset)s | %(log_color)s%(message)s"))
logger.addHandler(stream)

logger.setLevel("INFO")


class StockMarket:
    def __init__(self, bot):
        self.bot = bot
        self.increase = {10: [1, 0, 0, -1],
                         50: [1, 2, 0, 0, -1, -2],
                         100: [1, 2, 3,0, 0, -1, -2, -3,],
                         250: [1, 2, 3, 4, 5,0, 0, -1, -2, -3, -4, -5,],
                         500: [1, 2, 3, 4, 5, 6, 0, 0, -1, -2, -3, -4, -5, -6],
                         1000: [1, 2, 3, 4, 5, 6, 7, 0, 0, -1, -2, -3, -4, -5, -6, -7]}

        db = Database("stocks")
        db.create_table("stock_list",
                        {"stock": "TEXT", "price": INT, "holdings": INT, "market_cap": INT, "history": "TEXT"})

        db.create_table("users", {"user":INT, 'money':INT})
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
                break

        limit += 1000 if not limit else 0

        price += random.choice(self.increase[limit])

        if price < 0:
            db.delete("stock_list", where={"stock":stock})
            return

        history = eval(stock_data[4])
        history.append(price)

        db.update("stock_list", {"price": price, "market_cap": price * stock_data[2], "history": repr(history)},
                  where={"stock": stock})
        db.close()

        db.close()

    def percentage(self, stock, db):
        prices = db.select("stock_list", where={"stock": stock[0]}, size=1)

        prices = eval(prices[4])

        n = 240

        if len(prices) > n:
            prices = prices[-n:]

        cp = 1 if not prices[0] else prices[0] 
        return float(prices[-1] - cp) / cp

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

    def get_history(self, company):
        db = Database("stocks")
        history = db.select("stock_list", where={"stock": company}, size=1)
        db.close()
        return eval(history[4])
    
    def create_account(self, user):
        db = Database("stocks")
        db.insert("users", (user, 5000))

        db.create_table(f"_{user}", {"stock":"TEXT", "price":INT, "count":INT})
        db.close()

    def sell(self, user, stock, amount):
        db = Database("stocks")
        data = db.select("stock_list", where={"stock": stock}, size=1)

        if not data:
            return 
        
        total_price = data[1] * amount
        
        user = db.select("users", where={"user":user}, size=1)

        user_table = f"_{user[0]}"
        if db.if_exists(user_table, where={"stock":stock}):
            user_stock = db.select(user_table, where={"stock":stock}, size=1)
        else:
            return -2
        
        if user_stock[2] < amount: return -1
        
        db.update("stock_list", {"holdings":data[2]-amount, "market_cap":data[3]-total_price}, where={"stock":stock})
        db.update("users", {"money":user[1]+total_price}, where={"user":user[0]})

        if (user_stock[2] - amount) == 0:
            avg_price = 0
        else:
            avg_price = (user_stock[1] * user_stock[2]) - total_price / (user_stock[2] - amount)
        
        db.update(user_table, {"price":avg_price, "count":user_stock[2]-amount}, where={"stock":stock})

        return user[1]+total_price
    
    def corresponding_stock(self, stocks, target, db, user):
        for stock in stocks:
            if stock[0] == target:
                return stock
        
        db.delete(f"_{user}", where={"stock":stock[0]})

    def get_balance(self, user):
        db = Database("stocks")
        data = db.select("users", where={"user":user}, size=1)

        u_stocks = db.select(f"_{user}")
        stocks = db.select("stock_list")

    
        val = 0
        trading_val = 0
        for stock in u_stocks:
            val += stock[1] * stock[2] 
            current = self.corresponding_stock(stocks, stock[0], db, user)

            if current:
                trading_val += stock[2] * current[1] 

        db.close()

        if val == 0:
            percentage = 0
        else:
            percentage = round((trading_val - val)/val * 100, 2)
        
        return data[1], trading_val, val, trading_val-val, percentage, "🟢" if percentage >= 0 else "🔴"

    def buy(self, user, stock, amount):
        db = Database("stocks")
        data = db.select("stock_list", where={"stock": stock}, size=1)

        if not data:
            return 
        
        total_price = data[1] * amount
        
        user = db.select("users", where={"user":user}, size=1)
        
        if user[1] < total_price: return -1

        db.update("stock_list", {"holdings":data[2]+amount, "market_cap":data[3]+total_price}, where={"stock":stock})
        db.update("users", {"money":user[1]-total_price}, where={"user":user[0]})

        user_table = f"_{user[0]}"

        if db.if_exists(user_table, where={"stock":stock}):
            stock_data = db.select(user_table, size=1, where={"stock":stock})
            avg_price = round(((stock_data[1]*stock_data[2]) + total_price)/ (stock_data[2] + amount), 2)
            
            db.update(user_table, {"price":avg_price, "count":amount+stock_data[2]}, where={"stock":stock})

        else:
            db.insert(user_table, (stock, total_price/amount, amount))

        return user[1]-total_price

        
            
        


