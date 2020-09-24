from discord import Member, Embed, Status, Color, Role
from discord.ext import commands
from discord.utils import get

from asyncio import sleep
from sqlite3 import connect
from datetime import datetime


class Moderation(commands.Cog, name='Moderation'):
    """
    Commandes réservées aux admins et aux modos.
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['purge'], brief='!clear [x]', description='Supprimer [x] messages')
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, x: int):
        await ctx.channel.purge(limit=x+1)

    async def mute_handler(self, ctx, duration, target):
        async def wrapper(mute):
            with connect('data.db') as conn:
                c = conn.cursor()
                c.execute('SELECT Mute FROM setup WHERE Guild_ID=?', (ctx.guild.id,))
                id = c.fetchone()[0]
                role = get(ctx.guild.roles, id=id)
                if role is None:
                    for channel in ctx.guild.channels:
                        await channel.set_permissions(target, send_messages=mute)
                else:
                    await target.add_roles(role) if not mute else await target.remove_roles(role)
        await wrapper(False); await sleep(duration)
        embed = Embed(color=0xe74c3c, description=f'{target.mention} a été unmute.')
        await ctx.send(embed=embed); await wrapper(True)

    @commands.command(brief='!mute [membre] [durée] [raison]', description='Muter un membre')
    @commands.has_permissions(manage_messages=True)
    async def mute(self, ctx, member: Member, time: str, *, reason: str = None):
        units = {"s": [1, 'secondes'], "m": [60, 'minutes'], "h": [3600, 'heures']}
        duration = int(time[:-1]) * units[time[-1]][0]
        time = f"{time[:-1]} {units[time[-1]][1]}"
        embed = (Embed(description=f'Par : {ctx.author.mention}\nDurée : {time}.\nRaison : {reason}', color=0xe74c3c)
                 .set_author(name=f'{member} a été mute', icon_url=member.avatar_url))
        await ctx.send(embed=embed)
        await self.mute_handler(ctx, duration, member)

    @commands.command(brief='!kick [membre] [raison]', description='Kicker un membre')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: Member, *, reason: str = None):
        embed = (Embed(description=f'Par : {ctx.author.mention}\nRaison : {reason}', color=0xe74c3c)
                 .set_author(name=f'{member} a été kick', icon_url=member.avatar_url))
        await member.kick(reason=reason)
        await ctx.send(embed=embed)

    @commands.command(brief='!ban [membre] [raison]', description='Ban un membre')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: Member, *, reason: str = None):
        embed = (Embed(description=f'Par : {ctx.author.mention}\nRaison : {reason}', color=0xe74c3c)
                 .set_author(name=f'{member} a été ban', icon_url=member.avatar_url))
        await member.ban(reason=reason)
        await ctx.send(embed=embed)

    @commands.command(brief='!unban [membre] [raison]', description='Unban un membre')
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, member: str, *, reason: str = None):
        ban_list = await ctx.guild.bans()
        if not ban_list:
            embed = Embed(title="Oups ! Quelque chose s'est mal passé :", description="Aucuns membres bannis !", color=0xe74c3c)
            await ctx.send(embed=embed); return
        for entry in ban_list:
            if member.lower() in entry.user.name.lower():
                embed = (Embed(description=f'Par : {ctx.author.avatar_url}\nRaison : {reason}', color=0x2ecc71)
                 .set_author(name=f'{member} a été unban', icon_url=member.avatar_url))
                await ctx.guild.unban(entry.user, reason=reason)
                await ctx.send(embed=embed); return
        embed = Embed(title="Something went wrong:", description="No matching user!", color=0xe74c3c)
        await ctx.send(embed=embed); return

    @commands.command(brief='!warn [membre] [raison]', description='Avertir un membre')
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: Member, *, reason: str):
        now = datetime.now().strftime('%d/%m/%Y@%H:%M')
        with connect('data.db') as conn:
            c = conn.cursor()
            c.execute(f'SELECT WARNS FROM "{ctx.guild.id}" WHERE User_ID=?', (member.id,))
            entry = c.fetchone()
            warns = (''.join(entry) if entry else '') + f'{now} - {reason}\n'
            if entry is None:
                c.execute(f'INSERT INTO "{ctx.guild.id}" (User_ID, Warns) VALUES (?, ?)', (member.id, warns))
            else:
                c.execute(f'UPDATE "{ctx.guild.id}" SET Warns=? WHERE User_ID=?', (warns, member.id))
            conn.commit()
        
        embed = (Embed(description=f'Par : {ctx.author.mention}\nRaison : {reason}', color=0xe74c3c)
                 .set_author(name=f'{member} a été warn', icon_url=member.avatar_url))
        await ctx.send(embed=embed)

    @commands.command(brief='!warns [membre]', description="Regarder les warns d'un membre")
    @commands.has_permissions(manage_messages=True)
    async def warns(self, ctx, member: Member):
        with connect('data.db') as conn:
            c = conn.cursor()
            c.execute(f'SELECT WARNS FROM "{ctx.guild.id}" WHERE User_ID=?', (member.id,))
            warns = ''.join(c.fetchone())
        embed = Embed(color=0xe74c3c)
        for warn in warns.split('\n')[:-1]:
            date, reason = warn.split(' - ')
            embed.add_field(name=f"🚨 {date.replace('@', ' - ')}", value=f'{reason}', inline=False)
        embed.set_author(name=f"Warns de {member.display_name}", icon_url=member.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(brief='!annonce [texte]', description='Faire une annonce')
    @commands.has_permissions(manage_messages=True)
    async def annonce(self, ctx, *, text):
        embed = (Embed(title=text, timestamp=datetime.now(), color=0xf1c40f)
                 .set_author(name=f'Annonce de {ctx.author.display_name}', icon_url=ctx.author.avatar_url))

        await ctx.message.delete()
        await ctx.send('@here', embed=embed)


def setup(bot):
    bot.add_cog(Moderation(bot))