from discord import Embed, Color
from discord.ext import commands
from discord.utils import get

from tools.tools import get_json
from os import environ
from datetime import datetime, timedelta


class Weather(commands.Cog, name='Météo'):
    """
    Module de prévision météo (instantanée et sur 5 jours).
    """
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def get_cast(city, forecast=False):
        if forecast:
            return await get_json(f"http://api.openweathermap.org/data/2.5/forecast?q={city}&units=metric&APPID={environ['WEATHER_TOKEN']}")
        data = await get_json(f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&APPID={environ['WEATHER_TOKEN']}")
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
        data = await Weather.get_cast(city)
        embed = Embed(title=f":white_sun_small_cloud: Météo à {data['Ville']} :", color=0x3498db)
        for key, value in data.items():
            embed.add_field(name=key, value=value)
        embed.set_footer(text=f"Page 1/6 • {city} • {datetime.now().strftime('%d/%m/%Y')}")

        data = await Weather.get_cast(city, True)
        days = {entry['dt_txt'][:10]: [] for entry in data['list']}
        for index, entry in enumerate(data['list']):
            days[entry['dt_txt'][:10]].append(f"{entry['dt_txt'][11:-3]} → {entry['weather'][0]['main']} - {entry['main']['temp']}°C\n")

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
        emoji = payload.emoji.name
        reaction = get(message.reactions, emoji=emoji)
        embed = message.embeds[0]

        page, city, day = embed.footer.text.split(' • ')
        data = (await Weather.get_cast(city, True))
        forecast = {entry['dt_txt'][:10]: [] for entry in data['list']}
        for entry in data['list']:
            forecast[entry['dt_txt'][:10]].append(f"{entry['dt_txt'][11:]} → {entry['weather'][0]['main']} - {entry['main']['temp']}°C")
 
        if emoji == "▶️":
            next_page = (int(page[5])+1)%6 if (int(page[5])+1)%6 != 0 else 1
            next_day = [(datetime.strptime(day, '%d/%m/%Y') + timedelta(days=1))]*2
        elif emoji == "◀️":
            next_page = (int(page[5])-1)%6 if (int(page[5])-1)%6 != 0 else 6
            next_day = [(datetime.strptime(day, '%d/%m/%Y') - timedelta(days=1))]*2 if next_page != 6 else [datetime.strptime(list(forecast.keys())[-1], '%Y-%m-%d')]*2
        next_day[0], next_day[1] = next_day[0].strftime('%d/%m/%Y'), next_day[1].strftime('%Y-%m-%d')

        day_data = forecast if next_page != 1 else (await Weather.get_cast(city))
        if next_page == 1:
            embed = (Embed(title=f":white_sun_small_cloud: Météo à {day_data['Ville']} :", color=0x3498db)
                     .set_footer(text=f"Page 1/6 • {city} • {datetime.now().strftime('%d/%m/%Y')}"))
            for key, value in day_data.items():
                embed.add_field(name=key, value=value)
        else:
            embed = (Embed(title=f":white_sun_small_cloud: {next_day[0]} - Météo à {city}:", 
                           description='\n'.join(forecast[next_day[1]]), 
                           color=0x3498db)
                     .set_footer(text=f"Page {next_page}/6 • {city} • {next_day[0]}"))

        await reaction.remove(user)
        await message.edit(embed=embed)


def setup(bot):
    bot.add_cog(Weather(bot))