from discord import Game, Intents, __version__
from discord.ext import commands
from os import environ

intents = Intents.default()
intents.members = True
intents.presences = True
bot = commands.Bot(command_prefix=['!', '$'], intents=intents)
bot.remove_command('help')

initial_extensions = [
    'cogs.admin',
    'cogs.setup',
    'cogs.logs',
    'cogs.utility',
    'cogs.music',
    'cogs.fun',
    'cogs.weather',
    'cogs.search',
    'cogs.interaction',
]

if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)

@bot.event
async def on_ready():
    print(f'\nLogged as: {bot.user.name} - {bot.user.id}\nVersion: {__version__}\n')
    await bot.change_presence(activity=Game(name='!help'))
    print(f'Bot is ready to go!')

bot.run(environ['BOT_TOKEN'], bot=True, reconnect = True)