from discord.ext import commands
from discord import app_commands
from discord.ext import tasks
from backend import StockMarket
import discord


class Stock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.owners = [984245773887766551, 734416913437950011, 940215499764146176, 758957941033402388,
                       776029514811441152,
                       837584356988944396]
        self.stockmarket = StockMarket(self.bot)

        self.update_stocks.start()

    @tasks.loop(seconds=15)
    async def update_stocks(self):
        self.stockmarket.update_stocks()

    @app_commands.command(name="add-stock", description="Create stock")
    async def add_stock(self, interaction, name: str, price: int):
        if interaction.user.id not in self.owners:
            await interaction.response.send_message(
                "What colors are your IMO, NSO, IEO, IIO, IoE, IoS and GK medals this year? Thought so.")
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

    # Syncing new commands
    @commands.command()
    async def sync(self, ctx):
        fmt = await ctx.bot.tree.sync()

        await ctx.send(f"Synced {len(fmt)} commands.")


async def setup(bot):
    await bot.add_cog(Stock(bot))
