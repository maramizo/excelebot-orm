from discord.ext import commands


class CogLoader(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.last_loaded = 'cogloader'

    async def cog_check(self, ctx):
        return ctx.author.guild_permissions.administrator

    @commands.command()
    async def cload(self, ctx, extname=None):
        if extname is None:
            extname = self.last_loaded
        else:
            self.last_loaded = extname
        extname = f'app.ext.{extname}'
        if extname in self.bot.extensions:
            self.bot.reload_extension(extname)
            await ctx.send(f"{extname} reloaded.")
        else:
            self.bot.load_extension(extname)
            await ctx.send(f"{extname} loaded.")
        return


def setup(bot):
    bot.add_cog(CogLoader(bot))