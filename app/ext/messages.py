#  For all guilds:
#   Check if the oldest message is X amount of days old (ENV setting)
#   If it isn't, check for older messages and store these if any.
#  On guild join:
#   Store all messages within the guild that until X amount of days is reached.
#  Listen to new messages.
from datetime import datetime, timezone, timedelta
import discord
from discord.ext import commands, tasks
import re
from app.models import Guild, User, Message, Channel, Points


def valid_message(message):
    if message and len(message.content) > 4 and message.content.find(' ') != -1 \
            and not re.search("^[\\\\!@#$%^&*].*", message.content):
        return True
    return False


class Messages(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.loaded = False
        if bot.is_ready():
            self.reset_dailies.start()

    def cog_unload(self):
        self.reset_dailies.cancel()

    @tasks.loop(hours=24)
    async def reset_dailies(self):
        await Points.all().update(daily=0)

    @commands.Cog.listener()
    async def on_ready(self):
        self.reset_dailies.start()
        if self.loaded is False:
            for guild in self.bot.guilds:
                db_guild = await Guild.filter(id=guild.id).first()
                if not db_guild:
                    await Guild.create(id=guild.id, name=guild.name)
                    await self.load_messages_for_guild(guild)
                else:
                    for channel in guild.channels:
                        db_message = await Message.filter(channel_id=channel.id).order_by('created_at').first()
                        if not db_message:
                            await self.load_messages_for_channel(channel)
                        else:
                            date_time_diff = datetime.now(timezone.utc) - db_message.created_at
                            if date_time_diff.days < 7:
                                await self.load_messages_for_channel(channel, older_than=db_message.id)
            self.loaded = True
            print('Loaded all messages.')

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        user = await User.filter(id=message.author.id).first()
        if not user:
            await User.create(id=message.author.id, name=message.author.name)
        channel = await Channel.filter(id=message.channel.id)
        if not channel:
            await Channel.create(id=message.channel.id, name=message.channel.name)
        if valid_message(message):
            await Message.create(id=message.id, content=message.content,
                                 author_id=message.author.id,
                                 channel_id=message.channel.id, created_at=message.created_at)
            points = await Points.filter(user_id=message.author.id, guild_id=message.guild.id).first()
            if not points:
                await Points.create(user_id=message.author.id, guild_id=message.guild.id, amount=1, daily=1)
            else:
                date_diff = datetime.now(timezone.utc) - points.last_updated
                if date_diff.seconds > 120 and points.daily < 60:
                    await Points(id=points.id, amount=(points.amount+1), daily=(points.daily+1))\
                        .save(update_fields=['amount', 'daily', 'last_updated'])
                    print(f'Adding a point to {message.author}, they now have {points.amount + 1} points.')

    async def load_messages_for_channel(self, channel, older_than=None, times_called=1, limit=50):
        if channel.type is not discord.ChannelType.text:
            return
        try:
            if older_than:
                older_than = await channel.fetch_message(older_than)
                messages = await channel.history(limit=limit * times_called, before=older_than).flatten()
            else:
                messages = await channel.history(limit=limit * times_called).flatten()
        except discord.errors.Forbidden:
            print(f"Don't have access to channel {channel}. SKIPPING")
        except discord.errors.HTTPException:
            print('Request to get messages failed')
        else:
            messages_exist = False
            db_messages = []
            for message in messages:
                if valid_message(message):
                    messages_exist = True
                    user = await User.filter(id=message.author.id).first()
                    if not user:
                        await User.create(id=message.author.id, name=message.author.name)
                    _channel = await Channel.filter(id=message.channel.id).first()
                    if not _channel:
                        await Channel.create(id=message.channel.id, name=message.channel.name,
                                             guild_id=message.channel.guild.id)
                    db_messages.append(Message(id=message.id, content=message.content,
                                               author_id=message.author.id, channel_id=message.channel.id,
                                               created_at=message.created_at))
            if messages_exist:
                await Message.bulk_create(db_messages)
                oldest_message = await Message.filter(channel_id=channel.id).all().order_by('created_at').first()
                if oldest_message:
                    date_time_diff = datetime.now(timezone.utc) - oldest_message.created_at
                    if date_time_diff.days < 7:
                        await self.load_messages_for_channel(channel, oldest_message.id, times_called + 1, 50)
        return

    async def load_messages_for_guild(self, guild):
        for channel in guild.channels:
            await self.load_messages_for_channel(channel)
        return

    @commands.group()
    async def my(self, ctx: discord.ext.commands.Context):
        return

    @my.command()
    async def messages(self, ctx: discord.ext.commands.Context):
        count = await Message.filter(author_id=ctx.author.id).count()
        if count < 50:
            reaction = "Bit timid, aren't you?"
        elif count < 150:
            reaction = "You really do get a lot off of your chest here, huh?"
        elif count < 300:
            reaction = "Pass the microphone."
        else:
            reaction = "Feels like you own the place."
        await ctx.send(f"You ({ctx.author.name}) have sent {count} messages "
                       f"over the past week. {reaction}")

    @my.command()
    async def words(self, ctx: discord.ext.commands.Context):
        week_ago = datetime.now() - timedelta(days=7)
        user_messages = await Message.filter(author=ctx.author.id, created_at__gte=week_ago)\
            .all().values_list('content', flat=True)
        words = len(' '.join(user_messages).split())
        await ctx.send(f"You've sent {words} words in the past week.")
        return


def setup(bot):
    bot.add_cog(Messages(bot))
