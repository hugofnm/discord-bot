from discord import Embed, Member, Color
from discord.ext import commands

from requests import get
from datetime import datetime
from sqlite3 import connect
from os import environ


class Chat(commands.Cog, name='Chat'):
    """
    Utilisable par tout le monde et rassemble toutes les commandes un peu random.
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief='!help [categorie]', description='Afficher ce message')
    async def help(self, ctx, category: str = None):
        embed = Embed(color=0x3498db)
        embed.title = '📋 Liste des catégories :' if not category else f'ℹ️ A propos de {category} :'
        await ctx.message.delete()
        if not category:
            for cat in self.bot.cogs:
                if cat in ['Test', 'Logs']:
                    pass
                else:
                    cog = self.bot.get_cog(cat)
                    embed.add_field(name=cat, value=f"{cog.description}\nÉcris `!help {cat}` pour plus d'infos.", inline=False)
        else:
            for cmd in self.bot.get_cog(category.capitalize()).get_commands():
                if cmd.hidden:
                    pass
                else:
                    embed.add_field(name=f"!{cmd.name}", value=f"{cmd.description} (`{cmd.brief}`)", inline=False)
        await ctx.send(embed=embed)

    @commands.command(brief='!poll "[question]" [choix]', description='Créer un sondage (9 choix max)')
    async def poll(self, ctx, *items):
        question = items[0]
        answers = '\n'.join(items[1:])
        reactions = ['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣']
        embed = (Embed(title=':clipboard: Nouveau sondage', description=f"\> __{question}__", color=0x3498db)
                 .set_author(name=f'Par {ctx.author.display_name}', icon_url=ctx.author.avatar_url))

        await ctx.message.delete()
        for i in range(1, len(items)):
            embed.add_field(name=f"{reactions[i-1]} Option n°{i}", value=items[i], inline=False)
        message = await ctx.channel.send(embed=embed)

        for i in range(len(items[1:])):
            await message.add_reaction(reactions[i])


def setup(bot):
    bot.add_cog(Chat(bot))