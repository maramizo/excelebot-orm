# TODO
#  Handles giving a role for activity after a specific word count usage, message amount, or both.
#  Commands: !activity role, !activity word_count, !activity messages.
import discord
from discord.ext import commands
from app.models import Guild


class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.author.guild_permissions.administrator and ctx.guild.me.guild_permissions.manage_roles

    @commands.group()
    async def activity(self, ctx):
        return

    @activity.command()
    async def role(self, ctx: discord.ext.commands.Context, role: discord.Role = None):
        if role is None:
            guild_setting = await Guild.filter(id=ctx.guild.id).get()
            if guild_setting and guild_setting.role:
                role = discord.utils.get(ctx.guild.roles, id=int(guild_setting.role))
                await ctx.send(f"Current activity role is {role}.")
            else:
                await ctx.send("There is no currently set activity role.")
        else:
            await Guild(id=ctx.guild.id, role=role.id).save(update_fields=['role'])
            await ctx.send(f"You have set the activity role to {role}.")
        return

    @activity.command()
    async def words(self, ctx: discord.ext.commands.Context, words: int = None):
        if words:
            await Guild(id=ctx.guild.id, word_count=words).save(update_fields=['word_count'])
            await ctx.send(f"You have set the words amount to {words}")
        else:
            words = await Guild.get(id=ctx.guild.id).values_list('word_count', flat=True)
            if words[0]:
                await ctx.send(f"The current amount of words is set to {words}")
            else:
                await ctx.send(f"You have not yet set a words amount.")
        return


def setup(bot):
    bot.add_cog(Roles(bot))

