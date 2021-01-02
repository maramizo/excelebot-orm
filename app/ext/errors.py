# handle all errors
import discord
from discord.ext import commands


class Errors(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: discord.ext.commands.Context, error):
        print(f'{error}')
        if isinstance(error, commands.CheckFailure):
            await ctx.send('You are not authorized to use this command. :(')
        elif isinstance(error, commands.MissingRequiredArgument):
            params = ''
            aliases = ctx.command.aliases
            aliases.append(ctx.command.name)
            for param in ctx.command.clean_params:
                params = f'{params} {param}'
            await ctx.send(
                embed=discord.Embed(
                    title="Command help",
                    description=f"{ctx.prefix}{'/'.join(aliases)}{params}"))
        else:
            await ctx.send(error)


def setup(bot):
    bot.add_cog(Errors(bot))
