from discord import Embed, Member, Color
from discord.ext import commands

from requests import get
from datetime import datetime
from sqlite3 import connect
from os import environ


class Utility(commands.Cog, name='Utilitaire'):
    """
    Module rassemblant toutes les commandes utilitaires.
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief='!help [categorie]', description='Afficher ce message', aliases=['ahelp'])
    async def help(self, ctx, category: str = None):
        is_admin = ctx.author.guild_permissions.manage_messages
        if (category if category else False) in ['Moderation', 'Setup'] or ('a' in ctx.invoked_with and not is_admin):
            raise commands.errors.MissingPermissions
        member_cogs = [self.bot.get_cog(cog) for cog in self.bot.cogs if cog not in ['Moderation', 'Setup', 'Logs']]
        admin_cogs = [self.bot.get_cog(cog) for cog in ['Moderation', 'Setup']]
        title = "📋 Menu d'aide" if not category else f'ℹ️ A propos de {category} :'
        embed = Embed(title=title, description="Écris `!help [catégorie]` pour plus d'infos.", color=0x3498db)
        await ctx.message.delete()
        if not category:
            for cog in (admin_cogs if is_admin and 'a' in ctx.invoked_with else member_cogs):
                embed.add_field(name=cog.qualified_name, value=cog.description)
        else:
            for cmd in self.bot.get_cog(category.capitalize()).get_commands():
                if not cmd.hidden:
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

    @commands.command()
    async def calcul(self, ctx, string):
        string = string.replace('x', '*')
        string = string.replace('^', '**')
        result = eval(string, {'__builtins__': None})
        embed = Embed(description=f'📟 **Calcul :** {string} = {result}', color=0x206694)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Utility(bot))