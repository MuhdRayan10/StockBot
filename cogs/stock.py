import asyncio
import io
import json

from discord.ext import commands
from discord import app_commands
from discord.ext import tasks
from backend import StockMarket
import discord
from matplotlib import pyplot as plt
import mplcyberpunk
#from mpl_finance import candlestick_ohlc


class Stock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.owners = [984245773887766551, 964523363559170088, 734416913437950011, 758957941033402388,
                       656409780918812683, 775260152831279106, 625265223250608138, 1043772011182301225,
                       761116517307252746]
        self.stockmarket = StockMarket(self.bot)
        plt.style.use("ggplot")

        self.update_stocks.start()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Cog: Stock.py Loaded")

        # get the message ids from temp.json

        while True:
            data = self.stockmarket.get_stocks()
            embed = discord.Embed(title="Stock Market", description="The SRG Stock Market")
            embed.add_field(name="Stocks", value=data[0])
            embed.add_field(name="Prices", value=data[1])
            embed.add_field(name="Change", value=data[2])

            # get the channel
            guild = self.bot.get_guild(880368659858616321)
            channel = guild.get_channel(734416913437950012)

            # get the last posted message in channel
            try:
                last_message = (await channel.history(limit=1).flatten())[0]
                await last_message.edit(embed=embed)
            except:
                continue
            # edit the message
            
            await asyncio.sleep(15)


    @tasks.loop(seconds=15)
    async def update_stocks(self):
        self.stockmarket.update_stocks()

    @app_commands.command(name="add-stock", description="Create stock")
    async def add_stock(self, interaction, name: str, price: int):
        if interaction.user.id not in self.owners:
            await interaction.response.send_message(
                "What colors are your- No, I won't say it anymore :)")
            return

        if price <= 0:
            await interaction.response.send_message("Bruh no u")
            return

        self.stockmarket.add_stock(name, price)
        await interaction.response.send_message(
            f"`{name}` was added to the stock market successfully at the price `${price}` per stock")

    @app_commands.command(name="stockmarket", description="View the stock market")
    async def stockmarket_view(self, interaction):
        embed = discord.Embed(title="Stock Market", description="The SRG Stock Market")
        data = self.stockmarket.get_stocks()
        embed.add_field(name="Stocks", value=data[0])
        embed.add_field(name="Prices", value=data[1])
        embed.add_field(name="Change", value=data[2])

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="sendembed", description="Send a embed which auto-updates every 15s")
    async def sendembed(self, interaction):
        embed = discord.Embed(title="Stock Market", description="The SRG Stock Market")
        data = self.stockmarket.get_stocks()
        embed.add_field(name="Stocks", value=data[0])
        embed.add_field(name="Prices", value=data[1])
        embed.add_field(name="Change", value=data[2])

        await interaction.response.send_message("Sent the embed", ephemeral=True)
        await interaction.channel.send(embed=embed)


    @app_commands.command(name="graph", description="View the history of any stock market companies")
    async def graph(self, interaction, company1: str, company2: str = None, company3: str = None, company4: str = None,
                    company5: str = None):
        n = 1000

        def refactor(his):
            return his if len(his) < n else his[-n:]  # refactor can also have other stuff to be added like skip count

        data = []

        for company in [company1, company2, company3, company4, company5]:
            if company is not None:
                history = self.stockmarket.get_history(company)
                data.append(refactor(history))

        fig, axs = plt.subplots(1, 1)
        #candlestick_ohlc(axs, quotes, width=0.6, colorup='green', colordown='red', alpha=0.8)

        company_names = [company1]
        for company in [company2, company3, company4, company5]:
            if company is not None:
                company_names.append(company)

        # plot the data
        for i, counts in enumerate(data):
            axs.plot([i for i in range(1, len(counts) + 1)], counts, '-o', label=company_names[i], markersize=1)

        # add labels and grid
        axs.set_ylabel('Price')
        axs.grid(True)

        # add a title
        axs.set_title('Stock Market History')
        axs.legend()
        fig.tight_layout()

        mplcyberpunk.add_glow_effects()

        # save the graph as a virtual file and send it
        with io.BytesIO() as image_binary:
            fig.savefig(image_binary, format='png')
            image_binary.seek(0)

            embed = discord.Embed()

            embed.title = "Stock Graph"
            embed.description = "Shows the graph of the particular stock."

            embed.set_image(url="attachment://image.png")
            await interaction.response.send_message(embed=embed,
                                                    file=discord.File(fp=image_binary, filename="image.png"))

        # close the figure
        plt.close(fig)

    @app_commands.command(name="create-account", description="Create a stock market holding account.")
    async def create_account(self, interaction):
        if interaction.user.id not in self.owners:
            await interaction.response.send_message(
                "What colors are your- No, I won't say it anymore :)")
            return

        self.stockmarket.create_account(interaction.user.id)
        await interaction.response.send_message("Done", ephemeral=True)

    @app_commands.command(name="buy", description="Buy a stock from the stock market.")
    @app_commands.describe(stock="The stock you want to buy from the stock market.")
    @app_commands.describe(amount="How many of the stock you want to buy.")
    async def buy(self, interaction, stock: str, amount: int):

        if interaction.user.id not in self.owners:
            await interaction.response.send_message(
                "What colors are your- No, I won't say it anymore :)")
            return

        result = self.stockmarket.buy(interaction.user.id, stock, amount)
        if not result:
            await interaction.response.send_message(f"No stock named `{stock}`...")
        elif result == -1:
            await interaction.response.send_message(f"You do not have enough money to buy `x{amount}` of `{stock}`...")
        elif result == -3:
            await interaction.response.send_message(f"You think you're smart, don't you?")
        else:
            await interaction.response.send_message(f"Bought `{amount}` of the `{stock}` stock at the rate `{result[1]}`! Your balance is `{result[0]}`")

    @app_commands.command(name="balance", description="See your balance and trading account details.")
    async def balance(self, interaction, user:discord.Member=None):
        
        user = user or interaction.user
        data = self.stockmarket.get_balance(user.id)
        embed = discord.Embed(title=f"{user.name} Balance")
        embed.add_field(name="Balance", value=f"`${data[0]}`")
        embed.add_field(name="Trading", value=f"`${data[1]}`")
        embed.add_field(name="Invested", value=f"`${data[2]}`")
        embed.add_field(name="Change", value=f"`{data[3]}`    {data[4]}% {data[5]}", inline=True)
        embed.add_field(name="Net Worth", value=f"`${data[0]+data[1]}`")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="sell", description="Sell a stock from the stock market.")
    @app_commands.describe(stock="The stock you want to sell to the stock market.")
    @app_commands.describe(amount="How many of the stock you want to sell.")
    async def sell(self, interaction, stock:str, amount:int):

        if interaction.user.id not in self.owners:
            await interaction.response.send_message(
                "What colors are your- No, I won't say it anymore :)")
            return
        
        result = self.stockmarket.sell(interaction.user.id, stock, amount)
        if not result:
            await interaction.response.send_message(f"No stock named `{stock}`...")
        elif result == -1:
            await interaction.response.send_message(f"You do not have enough stocks to sell `x{amount}` of `{stock}`...")
        elif result == -2:
            await interaction.response.send_message(f"Create account first bro")
        elif result == -3:
            await interaction.response.send_message(f"You think you're smart, don't you?")
        else:
            await interaction.response.send_message(f"Sold `{amount}` of the `{stock}` stock at the rate `{result[1]}`! Your balance is `{result[0]}`")
    
    @app_commands.command(name="stocks", description="View the portfolio of the person.")
    async def stocks(self, interaction, user:discord.Member=None):
        user = user or interaction.user

        result = self.stockmarket.see_portfolio(user.id)

        if result == -1:
            await interaction.response.send_message(f"No stocks :(")
            return

        embed = discord.Embed(title=f"{user.name} Stocks")

        fields = ["Stocks", "Buy Price", "Market Price"]
        for i, field in enumerate(fields):
            embed.add_field(name=field, value=result[i], inline=True)

        await interaction.response.send_message(embed=embed)

    # Syncing new commands
    @commands.command()
    async def sync(self, ctx):
        fmt = await ctx.bot.tree.sync()

        await ctx.send(f"Synced {len(fmt)} commands.")


async def setup(bot):
    await bot.add_cog(Stock(bot))
