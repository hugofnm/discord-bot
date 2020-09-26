from discord import Embed, Member, Color
from discord.ext import commands
from discord.utils import get

from aiohttp import ClientSession
from random import choice


class Interaction(commands.Cog, name='Interaction'):
    """
    Module d'intéraction entre les membres du serveur.
    """
    def __init__(self, bot):
        self.bot = bot

    async def search(self, tag: str, filter: str = 'low'):
        async with ClientSession() as session:
            async with session.get(f'https://api.tenor.com/v1/search?&key=GRIIGKINBO7N&contentfilter={filter}&tag={tag}') as resp:
                results = await resp.json()
                return choice(results['results'])

    @commands.command(brief='!pat !kiss !hug !handshake !gift !slap', description='Intéragir avec un membre', aliases=['pat', 'hug', 'kiss', 'slap', 'gift', 'handshake'])
    async def interact(self, ctx, member: Member = None):
        url = (await self.search(ctx.invoked_with, 'high'))['media'][0]['tinygif']['url']
        interacts = {
            'interact': '**{}** intéragie avec **{}**',
            'pat': '❤️ **{}** pat **{}**',
            'kiss': '💋 **{}** embrasse **{}**',
            'hug': '🤗 **{}** fait un calin à **{}**',
            'slap': '👊 **{}** giffle **{}**',
            'handshake': '✋ **{}** check **{}**',
            'gift': '🎁 **{}** donne un cadeau à **{}**'
        }
        embed = Embed(description=interacts[ctx.invoked_with].format(ctx.author.display_name, member.display_name), color=0xFFB6C1)
        if ctx.invoked_with!='interact': embed.set_image(url=url)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Interaction(bot))