import json
import textwrap
import aiohttp
import discord
from bs4 import BeautifulSoup
from async_class import AsyncClass
import re

MOVIES_BASE = 'https://lookmovie.ag/movies/search/?q='
BASE = 'https://lookmovie.ag'


def find(string, start, end):
    return string.split(start)[1].split(end)[0]


class MovieList(AsyncClass):
    endpoint = "https://yts.mx/api/v2/list_movies.json"

    async def __ainit__(self, name):
        self.name = name
        self.quality = 'All'
        self.movies = []
        self.index = 0
        await self.load_movies()

    async def load_movies(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{MOVIES_BASE}{self.name}') as response:

                print("Status:", response.status)
                print("Content-type:", response.headers['content-type'])

                response = await response.text()
                soup = BeautifulSoup(response, 'html.parser')
                result = dict()
                for element in soup.find_all('div', 'movie-item-style-2 movie-item-style-1'):
                    info = element.find('h6')
                    year = element.find('p', 'year').string
                    img = element.find('img', 'lozad')
                    rate = element.find('p', 'rate').find('span').string
                    if img:
                        img = f"https://lookmovie.ag{img['data-src']}"

                    link = f"{BASE}{info.a.get('href')}"

                    title = info.a.string.strip()
                    title = re.sub(r'[<>:"/|?*\\]', ' ', title)  # Remove invalid characters for Windows
                    title = ' '.join(title.split())  # Remove consecutive spaces

                    movie = {'title': title, 'year': year, 'img': img, 'rate': rate, 'link': link}
                    self.movies.append(movie)
        return

    def get(self):
        return self.movies[self.index]

    def next(self):
        if self.index < len(self.movies) - 1:
            self.index += 1

    def prev(self):
        if self.index > 0:
            self.index -= 1

    async def select(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.movies[self.index]['link']}") as response:
                response = await response.text()
                soup = BeautifulSoup(response, 'html.parser')
                script = soup.find('div', id='app').find('script').string
                i = find(script, 'id_movie: ', ',')
                self.movies[self.index]['id'] = i

    def get_id(self):
        return self.movies[self.index]['id']

    def year(self):
        return self.movies[self.index]['year']

    def get_uri(self):
        for torrent in self.movies[self.index]['torrents']:
            if torrent['quality'] == self.quality or self.quality == 'All':
                return f"magnet:?xt=urn:btih:{torrent['hash']}"

    async def imdb_title(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://sg.media-imdb.com/suggests/{self.title()[0].lower()}/{self.title()}.json")\
                    as res:
                res = await res.text()
                res = res.split("(", 1)[1].split(")")[0]
                res = json.loads(res)
                if 'd' in res:
                    for result in res['d']:
                        year = self.year()
                        if 'y' in result and result['y'] == int(year):
                            return result['id']
                return ''

    def count(self):
        return len(self.movies)

    def title(self):
        return self.movies[self.index]['title']

    def format_embed(self):
        icon = 'https://cdn.discordapp.com/icons/718283348681687082/2c5557b3a168a323771a3798303a3b93.webp?size=128'
        movie = self.movies[self.index]
        embed = discord.Embed(title=f"{movie['title']} ({movie['year']})", color=7950900)
        embed.set_author(name='Excelobot', url='https://github.com/maramizo/excelobot', icon_url=icon)
        embed.set_footer(text="Made with ❤️| STILL IN BETA", icon_url=icon)
        embed.set_image(url=movie['img'])
        embed.add_field(name="IMDb Rating", value=movie['rate'])
        return embed
