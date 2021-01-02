import textwrap
import aiohttp
import discord
from async_class import AsyncClass


class MovieList(AsyncClass):
    endpoint = "https://yts.mx/api/v2/list_movies.json"

    async def __ainit__(self, name):
        self.name = name
        self.quality = 'All'
        self.movies = {}
        self.index = 0
        await self.load_movies()

    async def load_movies(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.endpoint, params={'query_term': self.name, 'quality': self.quality, 'limit': 50,
                                                          'sort_by': 'seeds', 'with_rt_ratings': 'true'}) as res:
                res = await res.json()
                if res['data']['movie_count'] > 0:
                    self.movies = res['data']['movies']
        return

    def get(self):
        return self.movies[self.index]

    def next(self):
        if self.index < len(self.movies) - 1:
            self.index += 1

    def prev(self):
        if self.index > 1:
            self.index -= 1

    def has_quality(self, quality):
        has_flag = False
        for torrent in self.movies[self.index]['torrents']:
            if torrent['quality'] == quality:
                has_flag = True
                break
        return has_flag

    def set_quality(self, quality):
        self.quality = quality

    def get_quality(self):
        return self.quality

    def get_uri(self):
        for torrent in self.movies[self.index]['torrents']:
            if torrent['quality'] == self.quality or self.quality == 'All':
                return f"magnet:?xt=urn:btih:{torrent['hash']}"

    def imdb_title(self):
        return self.movies[self.index]['imdb_code']

    def count(self):
        return len(self.movies)

    def title(self):
        return self.movies[self.index]['title']


    def format_embed(self):
        icon = 'https://cdn.discordapp.com/icons/718283348681687082/2c5557b3a168a323771a3798303a3b93.webp?size=128'
        movie = self.movies[self.index]
        embed = discord.Embed(title=movie['title_long'],
                              description=textwrap.shorten(movie['summary'],
                                                           width=200,
                                                           placeholder=f"... [(read more)](http://www.imdb.com/title"
                                                                       f"/{movie['imdb_code']})"), color=7950900)
        embed.set_author(name='Excelobot', url='https://github.com/maramizo/excelobot', icon_url=icon)
        embed.set_footer(text="Made with ❤️", icon_url=icon)
        embed.set_image(url=movie['medium_cover_image'])
        embed.add_field(name="IMDb Rating", value=movie['rating'])
        embed.add_field(name="YouTube Trailer", value=f"[Watch](https://youtube.com/watch?v={movie['yt_trailer_code']})")
        embed.add_field(name="Duration", value=f"{movie['runtime']} minutes")
        return embed


