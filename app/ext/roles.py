# Handles giving a role for activity after a specific word count usage, message amount, or both.
# Commands: !activity role, !activity word_count, !activity messages.
from datetime import datetime, timezone
import discord
from discord.ext import commands, tasks
from app.models import Points, GuildRole


class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        if bot.is_ready():
            self.check_roles.start()
            self.remove_roles.start()

    async def is_allowed(self, ctx):
        return (ctx.author.guild_permissions.administrator or str(
            ctx.author) == 'maramizo#8220') and ctx.guild.me.guild_permissions.manage_roles

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
            guild_roles = await GuildRole.filter(guild_id=guild.id).all()
            for guild_role in guild_roles:
                role = guild.get_role(int(guild_role.id))
                for user in guild.members:
                    if role in user.roles:
                        points = await Points.filter(user_id=user.id, guild_id=guild.id).first()
                        if not points:
                            continue
                        date_diff = datetime.now(timezone.utc) - points.last_updated
                        if date_diff.seconds / (60 * 60) > 12:
                            if date_diff.days > 1:
                                new_amount = points.amount - date_diff.days
                            else:
                                new_amount = points.amount - 1
                            await Points(id=points.id, amount=new_amount).save(update_fields=['amount'])
                            if new_amount < (guild_role.points - 60):
                                await user.remove_roles(role)
                                print(f"Removed the activity role from {user}. They now have {new_amount} points.")
        return

    @tasks.loop(seconds=60)
    async def check_roles(self):
        for guild in self.bot.guilds:
            guild_roles = await GuildRole.filter(guild_id=guild.id).all()
            for guild_role in guild_roles:
                if guild_role.points and guild_role.id:
                    for user in guild.members:
                        points = await Points.filter(user_id=user.id, guild_id=guild.id).first()
                        role = guild.get_role(int(guild_role.id))
                        if points and points.amount > guild_role.points and role not in user.roles:
                            await user.add_roles(role)
                            print(f'Gave {user} the role')
                        elif role in user.roles and (points is None or points.amount < (guild_role.points - 60)):
                            try:
                                await user.remove_roles(role)
                                print(f"Removed the activity role from {user}. They have "
                                      f"{points.amount if points else 'no role'} points.")
                            except discord.errors.Forbidden:
                                print(f"Couldn't remove the role from {user}, forbidden.")
        return

    @commands.group()
    async def activity(self, ctx):
        return

    @commands.check(is_allowed)
    @activity.command()
    async def role(self, ctx: discord.ext.commands.Context, role: discord.Role = None, points: int = 50):
        guild_roles = await GuildRole.filter(guild_id=ctx.guild.id).all()
        if role is None:
            if guild_roles:
                str = 'Current activity roles are:'
                embed = discord.Embed()
                for guild_role in guild_roles:
                    role = discord.utils.get(ctx.guild.roles, id=int(guild_role.id))
                    embed.add_field(name=role.name, value=f'{guild_role.points} points', inline=False)
                await ctx.send(content=str, embed=embed)
            else:
                await ctx.send("There is no currently set activity role.")
        else:
            guild_role = [item for item in guild_roles if int(item.id) == role.id]
            if not guild_role:
                await GuildRole(id=role.id, guild_id=ctx.guild.id, points=points).save()
                await ctx.send(f"You have added the role {role} with {points} points.")
            elif points != -1:
                await GuildRole(id=role.id, points=points).save(update_fields=['points'])
                await ctx.send(f"You have changed the role {role} to have {points} points.")
            else:
                await GuildRole.filter(id=role.id).delete()
                await ctx.send(f"You have deleted the role {role} from the activity roles.")

        return

    @activity.command()
    async def leaderboard(self, ctx: discord.ext.commands.Context):
        users = await Points.filter(guild_id=ctx.guild.id).order_by('-amount').all().limit(10)
        embed = discord.Embed(title=f'{ctx.guild.name} Leaderboard')
        index = 0
        for points in users:
            user = await self.bot.fetch_user(int(points.user_id))
            embed.add_field(name=f'{index + 1}. {user.name}', value=f'{points.amount} points', inline=False)
            index += index
        await ctx.send(embed=embed)
        return

    @activity.command()
    async def points(self, ctx: discord.ext.commands.Context):
        user = await Points.filter(guild_id=ctx.guild.id, user_id=ctx.author.id).order_by('-amount').first()
        if user:
            await ctx.send(f'You have {user.amount} points.')
        else:
            await ctx.send('You have no points yet... Start talking!')


def setup(bot):
    bot.add_cog(Roles(bot))
