from discord import Game, Intents, __version__
from discord.ext import commands
from os import environ, listdir

intents = Intents.all()
bot = commands.Bot(command_prefix=['!', '$'], intents=intents)
bot.remove_command('help')

if __name__ == '__main__':
    for extension in listdir('cogs/'):
        bot.load_extension(f'cogs.{extension}')

@bot.event
async def on_ready():
    print(f'\nLogged as: {bot.user.name} - {bot.user.id}\nVersion: {__version__}\n')
    await bot.change_presence(activity=Game(name='!help'))
    print(f'Bot is ready to go!')

bot.run(environ['BOT_TOKEN'], bot=True, reconnect = True)