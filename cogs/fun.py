from discord import Embed, Member, Color
from discord.ext import commands
from discord.utils import get

from random import choice
from requests import get as rget


class Fun(commands.Cog, name='Fun'):
    """
    Module qui contient des commandes pour s'amuser.
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief='!pof [pile/face]', description='Faire un pile ou face contre le bot')
    async def pof(self, ctx, arg):
        if arg.title() in ['Pile', 'Face']:
            result = choice(['Pile', 'Face'])
            if arg.title() in result: desc = f'🪙 {result} ! Tu as gagné.'
            else: desc = f'🪙 {result} ! Tu as perdu.'
        else:
            desc = '❌ Tu dois entrer "pile" ou "face"!'
        embed = Embed(description=desc, color=0xf1c40f)
        await ctx.send(embed=embed)

    @commands.command(brief='!ping [random/pseudo]', description="Mentionner quelqu'un")
    async def ping(self, ctx, arg: Member):
        members = [x for x in ctx.guild.members if not x.bot]
        if arg.lower() == 'random':
            await ctx.send(f'Hey {choice(members).mention} !')
        else:
            await ctx.send(f'Hey {arg.mention} !')

    @commands.command(aliases=['r'], brief='!roll [x]', description="Lancer un dé de [x] faces")
    async def roll(self, ctx, dices: str):
        content = dices.split('+')
        rolls, bonus = [], []
        for elem in content:
            if elem.isdigit():
                bonus.append(int(elem))
            else:
                n, faces = elem.split('d') if elem.split('d')[0] != '' else (1, elem[1:])
                rolls.append([choice(range(1, int(faces)+1)) for _ in range(int(n))])
        if len(rolls)>1:
            total = sum(sum(l) for l in rolls) + sum(bonus)
            rolls, bonus = [[str(n) for n in roll] for roll in rolls], f" + {' + '.join([str(n) for n in bonus])}"
            rolls = " + ".join([' + '.join(roll) for roll in rolls])
        else:
            total = sum(rolls[0]) + sum(bonus)
            rolls, bonus = ' + '.join([str(n) for n in rolls[0]]), f" + {' + '.join([str(n) for n in bonus])}"
        embed = Embed(description=f"**🎲 Résultat du lancé :** {rolls}{bonus if bonus!=' + ' else ''} = {total}", color=0xf1c40f)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Fun(bot))