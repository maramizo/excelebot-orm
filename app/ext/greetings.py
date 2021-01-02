# TODO
#  Set up greeting channels and whether or not to greet.
#  Commands:
#  !welcome: toggle welcome in channel, !goodbye: toggle goodbye, !greetings: toggles both
from discord.ext import commands


class Greetings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(Greetings(bot))
