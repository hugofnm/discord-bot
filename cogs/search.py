from discord import Embed, Status, Member, Color, Invite
from discord.ext import commands

from datetime import datetime
from os import environ
from sqlite3 import connect
from aiohttp import ClientSession
from github import Github


class Search(commands.Cog, name='Recherche'):
    """
    Module de recherche (animes, wikipedia, github, discord).
    """
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def get_json(link, headers=None):
        async with ClientSession() as s:
            async with s.get(link, headers=headers) as resp:
                return await resp.json()

    @commands.command(brief='!twitch [jeu] [mots]', description='Rechercher des streams sur Twitch')
    async def twitch(self, ctx, game, *keys, streams=[]):
        headers = {
            'Accept': 'application/vnd.twitchtv.v5+json',
            'Client-ID': environ['TWITCH_CLIENT'],
            'Authorization': f"Bearer {environ['TWITCH_TOKEN']}",
        }
        category = dict(await Search.get_json(f'https://api.twitch.tv/kraken/search/games?query={game}', headers))['games'][0]
        embed = (Embed(title=category['name'], color=0x3498db)
                 .set_thumbnail(url=category['box']['small'])
                 .set_author(name='Twitch', icon_url='https://www.pearlinux.fr/wp-content/uploads/2018/10/logo-tv-twitch-android-app.png'))
        response = await Search.get_json(f"https://api.twitch.tv/helix/streams?game_id={category['_id']}", headers)
        for stream in response['data']:
            if keys:
                for key in keys:
                    if key.lower() in stream['title'].lower() and not stream in streams:
                        streams.append(stream)
                        embed.add_field(name=f"{stream['user_name']}", value=f"[{stream['title']}](https://twitch.tv/{stream['user_name']})")
            else:
                embed.add_field(name=f"{stream['user_name']}", value=f"[{stream['title']}](https://twitch.tv/{stream['user_name']})")
        if len(embed.fields)==0:
            embed.add_field(name='\u200b', value='Aucuns streams trouvés')
        await ctx.send(embed=embed)

    @commands.command(brief='!profil [membre]', description="Afficher le profil d'un membre")
    async def profil(self, ctx, member: Member = None):
        member = member if member else ctx.author
        with connect('data.db') as conn:
            c = conn.cursor()
            c.execute(f'SELECT WARNS FROM "{ctx.guild.id}" WHERE User_ID=?', (member.id,))
            entry = c.fetchone()
            warn_nb = len(entry.split('\n')) if entry else 0
        flags = [str(flag)[10:].replace('_', ' ').title() for flag in member.public_flags.all()]
        status = {'online': 'En ligne', 'offline': 'Hors ligne', 'invisible': 'Invisible', 'idle': 'Absent', 'dnd': 'Ne pas déranger'}
        embed = (Embed(color=0x1abc9c)
                 .add_field(name='📥 Membre depuis', value=member.joined_at.strftime("%d/%m/%Y"), inline=True)
                 .add_field(name='⌨️ Pseudo', value=f'{member.name}#{member.discriminator}', inline=True)
                 .add_field(name='💡 Status', value=status[str(member.status)], inline=True)
                 .add_field(name='📝 Création du compte', value=member.created_at.strftime("%d/%m/%Y"), inline=True)
                 .add_field(name='🥇 Role principal', value=member.top_role.mention, inline=True)
                 .add_field(name='⚠️ Warns', value=f"{warn_nb} warns")
                 .add_field(name='🚩 Flags', value=', '.join(flags))
                 .add_field(name='Activité', value=member.activity.name if member.activity else 'Rien')
                 .set_author(name=f"Profil de {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
                 .set_thumbnail(url=member.avatar_url))
        if member.premium_since:
            embed.add_field(name='📈 Booste depuis', value=member.premium_since.strftime("%d/%m/%Y"), inline=True)
        await ctx.send(embed=embed)

    @commands.command(brief='github [nom/lien]', description='Rechercher des informations sur un repo')
    async def github(self, ctx, arg: str):
        if 'github.com' in arg: name = arg[19:]
        else: name = arg.capitalize()
        g = Github(environ['GITHUB_TOKEN'])
        repo, name = g.get_repo(name), name.capitalize()
        embed = (Embed(title=f'A propos de "{name}"', description=f'{repo.description}', url=repo.html_url, color=0x546e7a)
                 .set_footer(text=f"Tags : {' • '.join([topic for topic in repo.get_topics()])}")
                 .set_author(name='Github', icon_url='https://image.flaticon.com/icons/png/512/23/23957.png'))
        desc = {
            '👀 Vues':  f"{repo.get_views_traffic()['count']} vues",
            '⭐ Étoiles': f"[{repo.stargazers_count} étoiles]({repo.stargazers_url})",
            '📥 Forks': f'[{repo.forks_count} branches]({repo.forks_url})',
            '📝 Création': repo.created_at.strftime('%d/%m/%Y'),
            '📝 Auteur': f'[{name.split("/")[0]}]({repo.owner.url})',
            '⏲️ Dernier Commit': repo.updated_at.strftime('%d/%m/%Y à %H:%M'),
        }
        for name, value in desc.items():
            embed.add_field(name=name, value=value)
        embed.set_thumbnail(url=repo.owner.avatar_url)
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.command(brief='!serveur [invitation]', description='Rechercher un serveur discord')
    async def discord(self, ctx, invite: Invite = None):
        guild = invite.guild if invite else ctx.guild
        embed = (Embed(description=guild.description if guild.description else '', color=0x546e7a)
                 .set_author(name=f'Discord', icon_url='https://logo-logos.com/wp-content/uploads/2018/03/Discord_icon.png')
                 .set_thumbnail(url=guild.icon_url))
        fields = {
            '👥 Membres': f'{guild.member_count} membres',
            '🟢 En ligne': f'{len([member for member in guild.members if member.status != Status.offline])} membres',
            '🤖 Bots': f'{len([member for member in guild.members if member.bot])} bots',
            '🌍 Région': str(guild.region).title(),
            '🗝️ Owner': guild.owner,
            '📝 Création': guild.created_at.strftime('%d/%m/%Y'),
            '🏅 Roles': f'{len(guild.roles)} roles',
            '💬 Text Channels': f'{len(guild.text_channels)} channels',
            '🔊 Voice Channels': f'{len(guild.voice_channels)} channels',
            '😀 Emojis': ' '.join(guild.emojis) if guild.emojis else 'Aucuns emojis'
        }
        for name, value in fields.items():
            embed.add_field(name=name, value=value)
        await ctx.send(embed=embed)

    @commands.command(brief='!wikipedia [mots]', description='Rechercher un article wikipedia', aliases=['wiki'])
    async def wikipedia(self, ctx, *, arg):
        resp = list(await Search.get_json(f'https://fr.wikipedia.org/w/api.php?action=opensearch&search={arg}&namespace=0&limit=1'))
        title, url = resp[1][0], resp[3][0]
        resp = dict(await Search.get_json(f'https://fr.wikipedia.org/w/api.php?format=json&action=query&prop=extracts|pageimages&exintro&explaintext&redirects=1&titles={title}'))['query']['pages']
        data = next(iter(resp.values()))
        desc = data['extract'] if len(data['extract'])<2045 else f"{data['extract'][:2045]}..."
        embed = (Embed(title=f'{title} - Wikipedia', description=desc, url=url, color=0x546e7a)
                 .set_author(name='Wikipedia', icon_url='https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/Wikipedia_logo_%28svg%29.svg/1250px-Wikipedia_logo_%28svg%29.svg.png')
                 .set_thumbnail(url=data['thumbnail']['source']))
        await ctx.send(embed=embed)

    @commands.command(brief='!anime [nom]', description='Rechercher un anime')
    async def anime(self, ctx, *, name):
        resp = dict(await Search.get_json(f'https://kitsu.io/api/edge/anime?filter[text]={name}'))['data'][0]
        anime, url = resp['attributes'], resp['links']['self']
        h, m = divmod(int(anime['totalLength']), 60)
        embed = (Embed(title=anime['titles']['en_jp'], description=anime['synopsis'], url=url, color=0x546e7a)
                 .set_author(name='Anime', icon_url='https://lh3.googleusercontent.com/CjzbMcLbmTswzCGauGQExkFsSHvwjKEeWLbVVJx0B-J9G6OQ-UCl2eOuGBfaIozFqow')
                 .set_thumbnail(url=anime['posterImage']['tiny']))
        fields = {
            '🥇 Score': f"{anime['averageRating']}/100",
            '🖥️ Épisodes': f"{anime['episodeCount']} épisodes ({h:d}h{m:02d}min)",
            '📅 Diffusion': f"{datetime.strptime(anime['startDate'], '%Y-%m-%d').strftime('%d/%m/%Y')} → {datetime.strptime(anime['endDate'], '%Y-%m-%d').strftime('%d/%m/%Y')}",
        }
        for name, value in fields.items():
            embed.add_field(name=name, value=value)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Search(bot))