#  Finds movies and sends them to the website API to process.
#  Uses a socket to establish a connection with the website and load newer progress.
#  !fm <movie_name> -> find movies -> send message -> listen to reacts -> scroll right and left -> on check ->
#  choose quality -> listen to DM from user of pass -> send API request to create the room.
#  TODO Add password creation through DMs.
import asyncio
import os

import aiohttp
import discord
from discord.ext import commands
from app.helpers.movie import MovieList


class Movies(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=['fm', 'findmovie'])
    async def find_movie(self, ctx: discord.ext.commands.Context, *, name):
        movies = await MovieList(name)
        await ctx.send(f"Found {movies.count()} movies")
        if movies.count():
            embed = movies.format_embed()
            message = await ctx.send(embed=embed)
            await message.add_reaction(emojis['LEFT_ARROW'])
            await message.add_reaction(emojis['CHECK'])
            await message.add_reaction(emojis['RIGHT_ARROW'])
            await self.handle_react(ctx, message, movies)

        return

    async def handle_react(self, ctx, message, movies, step=0):
        arrow_pressed = False
        movie_chosen = False
        quality_chosen = False
        done, pending = await asyncio.wait([
            self.bot.wait_for('reaction_add',
                              check=lambda reaction,
                                           user: user.id == ctx.author.id
                              and str(reaction.emoji in emojis)
                              and reaction.message.id == message.id),
            self.bot.wait_for('reaction_remove',
                              check=lambda reaction, user: user.id == ctx.author.id
                              and str(reaction.emoji in emojis)
                              and reaction.message.id == message.id)
        ], return_when=asyncio.FIRST_COMPLETED)
        try:
            result = done.pop().result()
            if str(result[0].emoji) == emojis['RIGHT_ARROW'] and result[1].id == ctx.author.id:
                movies.next()
                arrow_pressed = True
            elif str(result[0].emoji) == emojis['LEFT_ARROW'] and result[1].id == ctx.author.id:
                movies.prev()
                arrow_pressed = True
            if arrow_pressed:
                await message.edit(embed=movies.format_embed())
            elif step == 0 and str(result[0].emoji) == emojis['CHECK'] and result[1].id == ctx.author.id:
                await message.edit(content=f"You have selected {movies.title()}. Please DM me a password, or click"
                                           f"{emojis['CHECK']} if you do not need one.")
                await message.clear_reactions()
                await message.add_reaction(emojis['CHECK'])
                await movies.select()
                quality_chosen = 2
            elif step == 2 and str(result[0].emoji) == emojis['CHECK'] and result[1].id == ctx.author.id:
                await message.edit(content=f"You have skipped setting a password, you can still set one up later.\n"
                                           f"Setting up your room now.")
                imdb = await movies.imdb_title()
                await self.create_movie(movies.get_id(), '', message, result[1].id, imdb)
        except Exception as e:
            print(e)
        for future in done:
            print('oopsie')
            future.exception()
        for future in pending:
            future.cancel()
        if arrow_pressed:
            await self.handle_react(ctx, message, movies)
        elif movie_chosen:
            await self.handle_react(ctx, message, movies, 1)
        elif quality_chosen:
            await self.handle_react(ctx, message, movies, 2)
        return

    async def create_movie(self, _id, password, message, u_id, title):
        async with aiohttp.ClientSession() as session:
            async with session.post(os.getenv("WEBSITE_URL") + os.getenv("WEBSITE_ROOM_ENDPOINT"),
                                   params={'video': _id, 'password': password, 'imdb': title}) as res:
                res = await res.json()
                room_id = res['id']
                url = res['url']
                validation = res['validation']
                url = os.getenv("WEBSITE_URL") + url
                print(f"Room created! Please type in '{validation}' to validate your ownership.\n"
                      f"Room URL: {url}")
                await message.edit(content="Room prepared! Please check your DMs.")
                user = await self.bot.fetch_user(u_id)
                await user.send(f"Room created! Please type in '{validation}'"
                                f" to validate your ownership.\n"
                                f"Room URL: {url}")
        return


emojis = {
    'LEFT_ARROW': '\U00002b05\U0000fe0f',
    'RIGHT_ARROW': '\U000027a1\U0000fe0f',
    'CHECK': '<:check:791611554297937920>',
    '720p': '<:720p:791607639690838026>',
    '1080p': '<:1080p:791607640055742494>'
}


def setup(bot):
    bot.add_cog(Movies(bot))
