# TODO
#  Handles giving a role for activity after a specific word count usage, message amount, or both.
#  Commands: !activity role, !activity word_count, !activity messages.
import discord
from discord.ext import commands, tasks
from app.models import Guild, Points
from datetime import datetime, timezone
import math


class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.author.guild_permissions.administrator and ctx.guild.me.guild_permissions.manage_roles

    @commands.Cog.listener()
    async def on_ready(self):
        self.check_roles.start()
        self.remove_roles.start()
        return

    def cog_unload(self):
        self.check_roles.cancel()
        self.remove_roles.cancel()

    @tasks.loop(hours=1)
    async def remove_roles(self):
        for guild in self.bot.guilds:
            db_guild = await Guild.filter(id=guild.id).first()
            if db_guild.points and db_guild.role:
                role = guild.get_role(int(db_guild.role))
                for user in guild.members:
                    if role in user.roles:
                        points = await Points.filter(user_id=user.id, guild_id=guild.id).first()
                        if not points:
                            continue
                        date_diff = datetime.now(timezone.utc) - points.last_updated
                        if date_diff.days > 0:
                            if date_diff.days > 1:
                                new_amount = points.amount-math.trunc((date_diff.seconds/(60*60))-24)
                            else:
                                new_amount = points.amount-1
                                points = await Points(id=points.id, amount=new_amount).save(update_fields=['amount'])
                            if points.amount < db_guild.points:
                                await user.remove_roles(role)
                                print(f"Removed the activity role from {user}. They now have {points.amount} points.")
        return

    @tasks.loop(seconds=5)
    async def check_roles(self):
        for guild in self.bot.guilds:
            db_guild = await Guild.filter(id=guild.id).first()
            if db_guild.points and db_guild.role:
                for user in guild.members:
                    points = await Points.filter(user_id=user.id, guild_id=guild.id).first()
                    role = guild.get_role(int(db_guild.role))
                    if points and points.amount > db_guild.points and role not in user.roles:
                        await user.add_roles(role)
                        print(f'Gave {user} the role')
        return

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
    async def points(self, ctx: discord.ext.commands.Context, points: int = None):
        if points:
            await Guild(id=ctx.guild.id, points=points).save(update_fields=['points'])
            await ctx.send(f"You have set the points amount to {points}")
        else:
            points = await Guild.get(id=ctx.guild.id).values_list('points', flat=True)
            if points[0]:
                await ctx.send(f"The current amount of points is set to {points}")
            else:
                await ctx.send(f"You have not yet set a points amount.")
        return


def setup(bot):
    bot.add_cog(Roles(bot))
