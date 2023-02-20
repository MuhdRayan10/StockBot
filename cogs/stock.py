import io
import mplcyberpunk
from discord.ext import commands
from discord import app_commands
from discord.ext import tasks
from backend import StockMarket
import discord
from matplotlib import pyplot as plt


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

    @app_commands.command(name="history", description="View the history of any stock market companies")
    async def history(self, interaction, company1, company2=None, company3=None, company4=None, company5=None):
        data = []
        for company in [company1, company2, company3, company4, company5]:
            if company is not None:
                data.append(self.stockmarket.get_history(company))

        fig, axs = plt.subplots(1, 1)

        t = [i for i in range(1, 10)]

        company_names = [company1]
        for company in [company2, company3, company4, company5]:
            if company is not None:
                company_names.append(company)

        # plot the data
        for i, (months, counts) in enumerate(data):
            axs.plot(t, counts, '-o', label=company_names[i])

        ticks = [i for i in range(1, 13)]
        tick_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May',
                       'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        # set the tick locations and labels
        axs.set_xticks(ticks)
        axs.set_xticklabels(tick_labels)

        # add labels and grid
        axs.set_xlabel('Month')
        axs.set_ylabel('Number of Messages')
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

            embed.title = "Monthly Member Activity"
            embed.description = "Shows the activity of user(s) in a guild on a per month basis."

            embed.set_image(url="attachment://image.png")
            await interaction.response.send_message(embed=embed, file=discord.File(fp=image_binary, filename="image.png"))

        # close the figure
        plt.close(fig)

    # Syncing new commands
    @commands.command()
    async def sync(self, ctx):
        fmt = await ctx.bot.tree.sync()

        await ctx.send(f"Synced {len(fmt)} commands.")


async def setup(bot):
    await bot.add_cog(Stock(bot))
