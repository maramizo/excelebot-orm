#  Commands that involve setting up guild specific options.
#  !prefix
from discord.ext import commands
from app.models import Guild


class Settings(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.author.guild_permissions.administrator or str(ctx.author) == 'maramizo#8220'

    @commands.command()
    async def prefix(self, ctx, prefix):
        await Guild(id=ctx.guild.id, prefix=prefix).save(update_fields=['prefix'])
        await ctx.send(f"You have set the prefix to {prefix}")


def setup(bot):
    bot.add_cog(Settings(bot))

