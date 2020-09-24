from discord import Embed, Member
from discord.ext import commands
from discord.utils import get

from random import choice, randint
from requests import get as rget


class Fun(commands.Cog, name='Fun'):
    """
    Module qui contient des commandes pour s'amuser.
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief='!pof [pile/face]', description='Faire un pile ou face contre le bot')
    async def pof(self, ctx, arg):
        if arg.lower() == 'pile' or arg.upper() == 'face':
            piece = choice(['pile', 'face'])
            if arg.lower() in piece:
                await ctx.send(f':white_check_mark: {piece}! GG, tu as gagné.')
            else:
                await ctx.send(f':negative_squared_cross_mark: {piece}! Tu as perdu.')
        else:
            await ctx.send('❌ Tu dois entrer "pile" ou "face"!')         

    @commands.command(brief='!ping [random/pseudo]', description="Mentionner quelqu'un")
    async def ping(self, ctx, arg: Member):
        members = [x for x in ctx.guild.members if not x.bot]
        if arg.lower() == 'random':
            await ctx.send(f'Hey {choice(members).mention} !')
        else:
            await ctx.send(f'Hey {arg.mention} !')

    @commands.command(aliases=['r'], brief='!roll [x]', description="Lancer un dé de [x] faces")
    async def roll(self, ctx, faces: int):
        number = randint(1, faces)
        await ctx.send(f'🎲 Tu as obtenu un {number} !')


def setup(bot):
    bot.add_cog(Fun(bot))