from discord import Embed, Member
from discord.ext import commands
from discord.utils import get


class Interaction(commands.Cog, name='Interaction'):
    """
    Module d'intéraction entre les membres du serveur.
    """
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(Interaction(bot))