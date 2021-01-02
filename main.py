from tortoise import Tortoise
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from app.models import Guild
import glob
load_dotenv()

intents = discord.Intents.default()
intents.members = True


async def init():
    await Tortoise.init(
        db_url=os.getenv("DB_URL"),
        modules={'models': ['app.models']}
    )
    await Tortoise.generate_schemas()
    print('Database loaded')


async def determine_prefix(_bot, message: discord.message):
    guild = await Guild.filter(id=message.guild.id).first()
    if not guild:
        return '.'
    return guild.prefix


extensions = []
for ext in glob.glob('.\\app\\ext\\*.py'):
    extensions.append(ext[2:].replace('\\', '.').replace('.py', ''))


def load_extensions():
    for extension in extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Failed to load extension {}\n{}'.format(extension, exc))


bot = commands.Bot(command_prefix=determine_prefix, description="", intents=intents)


@bot.event
async def on_ready():
    print(f"Connected! \nName: {bot.user.name}\tID: {bot.user.id}\n")


print('Version: ' + discord.__version__)
print(f'Version info: {discord.version_info}')


def main():
    load_extensions()
    bot.loop.create_task(init())
    bot.run(os.getenv("TOKEN"))


main()
