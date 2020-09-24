from discord import Embed, Color
from discord.ext import commands
from discord.utils import get

from requests import get as rget
from os import environ
from datetime import datetime, timedelta
from sqlite3 import connect


class Weather(commands.Cog, name='Météo'):
    """
    Utilisable par tout le monde et permet d'avoir des prévisions météo.
    """
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def get_cast(city, forecast=False):
        if forecast:
            return rget(f"http://api.openweathermap.org/data/2.5/forecast?q={city}&units=metric&APPID={environ['WEATHER_TOKEN']}").json()
        data  = rget(f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&APPID={environ['WEATHER_TOKEN']}").json()
        cleared_data = {
            'Ville': data['name'],
            'Heure': (datetime.utcfromtimestamp(data['dt']) + timedelta(hours=2)).strftime('%H:%M:%S'),
            'Météo': f"{data['weather'][0]['main']} - {data['weather'][0]['description']}",
            'Temperature': f"{data['main']['temp']}°C",
            'Ressenti': f"{data['main']['feels_like']}°C",
            'Temperature min': f"{data['main']['temp_min']}°C",
            'Temperature max': f"{data['main']['temp_max']}°C",
            'Humidité': f"{data['main']['humidity']}%",
            'Pression': f"{data['main']['pressure']} Pa",
            'Nuages': f"{data['clouds']['all']}%",
            'Vent': f"{data['wind']['speed']} km/h",
            'Coucher du soleil': (datetime.utcfromtimestamp(data['sys']['sunset']) + timedelta(hours=2)).strftime('%H:%M:%S'),
            'Lever du soleil': (datetime.utcfromtimestamp(data['sys']['sunrise']) + timedelta(hours=2)).strftime('%H:%M:%S'),
        }
        return cleared_data

    @commands.command(brief='!meteo [ville]', description="Météo et prévisons sur 5 jours d'une ville")
    async def meteo(self, ctx,  *, city):
        data = Weather.get_cast(city)
        embed = Embed(title=f":white_sun_small_cloud: Météo à {data['Ville']} :", color=0x3498db)
        for key, value in data.items():
            embed.add_field(name=key, value=value)
        embed.set_footer(text="Page 1/6")

        data = Weather.get_cast(city, True)
        days = {entry['dt_txt'][:10]: [] for entry in data['list']}
        for index, entry in enumerate(data['list']):
            days[entry['dt_txt'][:10]].append(f"{entry['dt_txt'][11:-3]} → {entry['weather'][0]['main']} - {entry['main']['temp']}°C\n")

        with connect('data.db') as conn:
            c = conn.cursor()
            for key in days.keys():
                days[key] = ''.join(days[key])
                c.execute('SELECT * FROM weather WHERE (Day=? AND City=?)', (key, data['city']['name']))
                if c.fetchone() is None:
                    c.execute("INSERT INTO weather(Day, City, Data) VALUES (?, ?, ?)", (key, data['city']['name'], days[key]))
            conn.commit()

        msg = await ctx.send(embed=embed)
        for emoji in ["◀️", "▶️"]:
            await msg.add_reaction(emoji)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        user = self.bot.get_user(payload.user_id)
        if not payload.emoji.name in ["◀️", "▶️"] or user.bot:
            return

        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        reaction = get(message.reactions, emoji=payload.emoji.name)
        page = int(message.embeds[0].footer.text[5])
        days = tuple((message.created_at+timedelta(days=i)).strftime("%Y-%m-%d") for i in range(0,6))

        with connect('data.db') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM weather WHERE Day=? OR Day=? OR Day=? OR Day=? OR Day=? or Day=?", days)
            data = [list(day) for day in c.fetchall()]

        await reaction.remove(user)
        if (page==1 and payload.emoji.name =="◀️") or (page==6 and payload.emoji.name =="▶️"):
            return
        data = data[page-2] if payload.emoji.name == "◀️" else data[page]
        if page == 2 and datetime.now().strftime("%Y-%m-%d") == data[0]:
            data = Weather.get_cast(data[1])
            embed = (Embed(title=f":white_sun_small_cloud: Météo à {data['City']} :", color=0x3498db)
                     .set_footer(text="Page 1/6"))
            for key, value in data.items():
                embed.add_field(name=key, value=value)
        else:
            embed = (Embed(title=f':white_sun_small_cloud: {data[0]} - Météo à {data[1]}:', color=0x3498db)
                     .add_field(name=data[2], value='\u200b')
                     .set_footer(text=f"Page {page-1}/6" if payload.emoji.name == "◀️" else f"Page {page+1}/6"))
        await message.edit(embed=embed)


def setup(bot):
    bot.add_cog(Weather(bot))