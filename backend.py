import logging
from colorlog import ColoredFormatter
from gbm import new_prices
from easy_sqlite3 import *
import random
import json

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

        self.extra_stocks = ["Microsoft", "Google", "Amazon.com", "Tesla", "NVIDIA", "Walmart", 
                             "Mastercard Inc", "Home Depot", "CocaCola", "Alibaba", "PepsiCo", 
                             "Pfizer", "Oracle", "McDonalds", "Nike", "Adidas", "Toyota"]


        self.db = Database("stocks")
        self.db.create_table("stock_list",
                        {"stock": "TEXT", "price": INT, "holdings": INT, "market_cap": INT, "history": "TEXT"})

        self.db.create_table("users", {"user":INT, 'money':INT})
        
        self.db.create_table("limits", {"user":INT, 'stock':"TEXT", 'amount':INT, 'price':INT})
        self.db.create_table("stop_loss", {"user":INT, 'stock':"TEXT", 'amount':INT, 'price':INT})
        

    def add_stock(self, stock_name: str, start_price: int):


        if self.db.if_exists("stock_list", where={"stock": stock_name}):
            
            return -1

        self.db.insert("stock_list", {"stock": stock_name, "price": start_price, "holdings": 0, "market_cap": 0,
                                 "history": f"[{start_price}]"})
        

    def update_stocks(self):
        stock_data = self.db.select("stock_list")

        for data in stock_data:
            self.update_stock_price(data[0])

    def get_stock_price(self, stock, price):
        
        with open("stock_prices.json", "r") as f:
            data = json.load(f)

        new_price = 0

        if data.get(stock, None) is None:
            data[stock] = new_prices(price)

        new_price = data[stock].pop(0)

        if len(data[stock]) == 0:
            data[stock] = new_prices(new_price)

        with open("stock_list.json", "w") as f:
            json.dump(data, f)

        return new_price


    def update_stock_price(self, stock):
        stock_data = self.db.select("stock_list", where={"stock": stock}, size=1)

        limits = self.db.select("limits", where={"stock": stock})
        stop_loss = self.db.select("stop_loss", where={"stock": stock})
        
        price = stock_data[1]

        limit = 0
        for lim in self.increase:
            if lim >= price:
                limit += lim
                break

        limit += 1000 if not limit else 0

        price = self.get_stock_price(stock, price)

        if price <= 0:
            try:
                
                self.db.execute(f'DELETE FROM stock_list WHERE stock="{stock}"')
                self.erase_stock(stock)
                result, tries = -1, 0
                while result == -1 and tries <= 20:
                    result = self.add_stock(random.choice(self.extra_stocks), 50)
                return
            except: 
                print(stock)
        for lim in limits:
            if lim[3] <= price:
                self.sell(lim[0], lim[1], lim[2])

                self.db.delete("limits", where={"user":lim[0], "stock":lim[1], "amount":lim[2], "price":lim[3]})

        for lo in stop_loss:
            print(lo)
            if lo[3] >= price:
                self.sell(lo[0], lo[1], lo[2])

                self.db.delete("stop_loss", where={"user":lo[0], "stock":lo[1], "amount":lo[2], "price":lo[3]})
            
        history = eval(stock_data[4])
        history.append(price)

        self.db.update("stock_list", {"price": price, "market_cap": price * stock_data[2], "history": repr(history)},
                  where={"stock": stock})
          

    def percentage(self, stock):
        prices = self.db.select("stock_list", where={"stock": stock[0]}, size=1)

        prices = eval(prices[4])

        n = 240

        if len(prices) > n:
            prices = prices[-n:]

        cp = 1 if not prices[0] else prices[0] 
        return float(prices[-1] - cp) / cp

    def get_stocks(self):

        data = self.db.select("stock_list")

        stocks, prices, percentages = "", "", ""
        for stock in data:
            increase = round(self.percentage(stock), 2)
            symbol = "🟢" if increase >= 0 else "🔴"
            stocks += f"\n{stock[0]}"
            prices += f"\n${stock[1]}"
            percentages += f"\n{round(increase * 100, 2)}% {symbol}"

        return stocks, prices, percentages

    def get_history(self, company):
        history = self.db.select("stock_list", where={"stock": company}, size=1)
        
        return eval(history[4])

    def create_account(self, user):

        if self.db.if_exists("users", where={"user":user}):
            return -1
        
        self.db.insert("users", (user, 5000))

        self.db.create_table(f"_{user}", {"stock":"TEXT", "price":INT, "count":INT})
        

    def sell(self, user, stock, amount):
        data = self.db.select("stock_list", where={"stock": stock}, size=1)

        if amount <= 0:
            return -3

        if not data:
            return 
        
        total_price = data[1] * amount
        
        user = self.db.select("users", where={"user":user}, size=1)

        user_table = f"_{user[0]}"
        user_stock = self.db.select(user_table, where={"stock":stock}, size=1)

        if not user_stock:
            return -2
        
        if user_stock[2] < amount: return -1
        
        self.db.update("stock_list", {"holdings":data[2]-amount, "market_cap":data[3]-total_price}, where={"stock":stock})
        self.db.update("users", {"money":user[1]+total_price}, where={"user":user[0]})

        if (user_stock[2] - amount) == 0:  
            self.db.execute(f'DELETE FROM {user_table} WHERE stock="{stock}"', )
            self.db.commit()
        else:
            avg_price = (user_stock[1] * user_stock[2]) - total_price / (user_stock[2] - amount)
            self.db.update(user_table, {"price":round(avg_price, 2), "count":user_stock[2]-amount}, where={"stock":stock})

            
        return user[1]+total_price, data[1]
    
    def corresponding_stock(self, stocks, target, user, delete=True):
        for stock in stocks:
            if stock[0] == target:
                return stock
        
        if delete:
            try:
                self.db.execute(f'DELETE FROM _{user} WHERE stock="{target}"')
                self.erase_stock(target)
                
            except:
                pass

    def get_balance(self, user):
        data = self.db.select("users", where={"user":user}, size=1)

        u_stocks = self.db.select(f"_{user}")
        stocks = self.db.select("stock_list")

        if not data:
            
            return

        val = 0
        trading_val = 0
        for stock in u_stocks:
            val += stock[1] * stock[2] 
            current = self.corresponding_stock(stocks, stock[0], user)

            if current:
                trading_val += stock[2] * current[1] 

        

        if val == 0:
            percentage = 0
        else:
            percentage = round((trading_val - val)/val * 100, 2)
        
        return data[1], trading_val, val, trading_val-val, percentage, "🟢" if percentage >= 0 else "🔴"

    def buy(self, user, stock, amount, limit):
        data = self.db.select("stock_list", where={"stock": stock}, size=1)

        if amount <= 0:
            return -3

        if not data:
            return 
        
        total_price = data[1] * amount
        
        user = self.db.select("users", where={"user":user}, size=1)
        
        if user[1] < total_price: return -1

        self.db.update("stock_list", {"holdings":data[2]+amount, "market_cap":data[3]+total_price}, where={"stock":stock})
        self.db.update("users", {"money":user[1]-total_price}, where={"user":user[0]})

        user_table = f"_{user[0]}"

        if self.db.if_exists(user_table, where={"stock":stock}):
            stock_data = self.db.select(user_table, size=1, where={"stock":stock})
            avg_price = round(((stock_data[1]*stock_data[2]) + total_price)/ (stock_data[2] + amount), 2)
            
            self.db.update(user_table, {"price":avg_price, "count":amount+stock_data[2]}, where={"stock":stock})

        else:
            self.db.insert(user_table, (stock, total_price/amount, amount))

        # Adding the limit thingy 
        if limit:
            self.db.insert("limits" if data[1] <= limit else "stop_loss", (user[0], stock, amount, limit))

        

        return user[1]-total_price, data[1]
    
    def see_portfolio(self, user):
        
        current = self.db.select("stock_list")
        user_stocks = self.db.select(f"_{user}")

        
        stock_names = [u[0] for u in user_stocks]
        current = [c for c in current if c[0] in stock_names]

        if not user_stocks:
            return -1
        
        data = []
        for stock in user_stocks:
            
            if not stock[1]: continue

            market = self.corresponding_stock(current, stock[0], user)

            if stock[1] == 0: percentage = 0
            else: percentage = ((market[1] - stock[1]) / stock[1]) * 100

            percentage = f'`${round((market[1]-round(stock[1], 2))*stock[2], 2)}` {round(percentage,2)}% {"🟢" if percentage >= 0 else "🔴"}'

            data.append([f"`[{stock[2]}]` {stock[0]} ", f"`${stock[1]}`", f"`${market[1]}` ({percentage})"])

        

        return '\n'.join([d[0] for d in data]), '\n'.join([d[1] for d in data]), '\n'.join([d[2] for d in data])

    def erase_stock(self, stock):
        tables = self.db.get_tables()

        for table in tables:
            if table.startswith("_"):
                try:
                    self.db.delete(table, where={"stock":stock})
                except:
                    pass
    def leaderboard(self):
        users = self.db.select("users")
        stock_list = self.db.select("stock_list")

        riches = []

        for user in users:
            balance = user[1]

            u_list = self.db.select(f"_{user[0]}")
            for stock in u_list:
                current = self.corresponding_stock(stock_list, stock, user, delete=False)
                if current:
                    balance += current[1] * stock[2]
    
            riches.append([user[0], round(balance, 2)])

        
        riches.sort(key=lambda x: x[1], reverse=True)

        return riches


