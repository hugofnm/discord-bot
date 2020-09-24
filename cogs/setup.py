from discord import Role, TextChannel, Permissions, Embed, Color
from discord.ext import commands
from discord.utils import get

from sqlite3 import connect


class Setup(commands.Cog, name='Setup'):
    """
    Module rassemblant les commandes pour configurer le bot.
    """
    def __init__(self, bot):
        self.bot = bot  

    @commands.command(brief='!setup [verif/mute/logs/temp] [@role/#channel]', description='Définir un role pour "verif" ou "mute"')
    @commands.has_permissions(administrator=True)
    async def setup(self, ctx, mtype: str, setup_data):
        if mtype.lower() in ['verif', 'mute']:
            mod = get(ctx.guild.roles, id=int(setup_data.strip('<@&>')))
        elif mtype.lower() in ['temp', 'logs']:
            mod = get(ctx.guild.channels, id=int(setup_data.strip('<#>')))
        else:
            embed = Embed(title='❌ Oups ! Il y a une erreur :', description='Choix invalide ! (verif/mute/logs/temp)', color=0xe74c3c)
            await ctx.send(embed=embed); return
        with connect('data.db') as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM setup WHERE Guild_ID=?', (ctx.guild.id,))
            if c.fetchone() is None:
                c.execute(f'INSERT INTO setup (Guild_ID, {mtype.capitalize()}) VALUES (?, ?)', (ctx.guild.id, mod.id))
            else:
                c.execute(f'UPDATE setup SET {mtype.capitalize()}=? WHERE Guild_ID=?', (mod.id, ctx.guild.id))
            conn.commit()
        embed = (Embed(description=f'{ctx.author.mention} a défini {mod.mention} pour "{mtype}"', color=0xa84300)
                 .set_author(name=f'{ctx.author} a modifié "{mtype}"', icon_url=ctx.author.avatar_url))
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.has_permissions(manage_messages=True)
    async def regles(self, ctx):
        rules = {
            '👍 Règle n°1': "Respect mutuel ! Pour un chat sympa et bienveillant, pas d'insultes ou de méchancetés",
            '🗳️ Règle n°2': "C'est un serveur dédié à @E - Wizard#3217. Pas de sujets politiques, religieux et pas de racisme, de harcèlement ou de contenu offensif.",
            '🔕 Règle n°3': "Pas de spam ou de mentions abusives. Pour éviter d'avoir un chat qui ressemble à rien, évitez les abus.",
            '👦 Règle n°4': "Ayez un avatar et un pseudo approprié (family-friendly)",
            '🔒 Règle n°5': "Ne partagez pas vos informations personnelles ! Protégez votre intimité et celle des autres.",
            '💛 Règle n°6': "Utilisez votre bon sens. Ne faites pas aux autres ce que vous ne voudriez pas qu'on vous fasse.",
            '💬 Règle n°7': "Évitez la pub ! Vous pouvez partager vos projets dans #vos-projects.",
            '🙏 Règle n°8': "Pas de mandiage de role. C'est juste une perte de temps et ça ne marchera jamais.",
            '📑 Règle n°9': "Repectez les [Guidelines de la Communauté Discord](https://discord.com/guidelines) et les [Conditions d'utilisation](https://discord.com/terms).",
        }
        embed = Embed(title="📃 Règles du serveur:", description='Appuie sur ✅ après avoir lu les règles :',color=0xa84300)
        for key, value in rules.items():
            embed.add_field(name=key, value=f"{value}\n", inline=False)
        await ctx.message.delete()
        msg = await ctx.send(embed=embed)
        await msg.add_reaction('✅')

    @commands.command(brief='!roles', description='Setup a role menu')
    @commands.has_permissions(manage_roles=True)
    async def roles(self, ctx):
        def check(role: Role):
            r = role.permissions
            return (r.manage_messages or r.administrator or r.manage_roles or r.ban_members
                    or r.kick_members or r.manage_guild or r.manage_nicknames or r.manage_channels
                    or r.mute_members or r.deafen_members or r.move_members or r.manage_emojis
                    or role.managed or role==role.guild.default_role)
        roles = [role for role in ctx.guild.roles if not check(role)]
        embed = Embed(title='🔧 Menu de setup de roles', description='Réagis au message pour définir un emoji au role sélectionné.\n Tu peux aussi appuyer sur ❌ pour supprimer le role du menu.', color=0x11806a)
        for i, role in enumerate(roles):
            embed.add_field(name=role.name if i else f'>> {role.name} <<' , value="Pas d'émoji défini", inline=False)
        embed.set_footer(text=f"{embed.fields[0].name.strip('>< ')} • Pas d'émoji défini • Appuie sur 🔧 quand tu as fini")
        msg = await ctx.send(embed=embed)
        for reaction in ['⏪', '⏩', '❌', '🔧']:
            await msg.add_reaction(reaction)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member.bot: return
        member = payload.member
        guild = member.guild
        emoji = payload.emoji
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        reaction = get(message.reactions, emoji=emoji.name)
        embed = message.embeds[0]
        
        with connect('data.db') as conn:
            c = conn.cursor()
            c.execute('SELECT Verif FROM setup WHERE Guild_ID=?', (guild.id,))
            role = get(guild.roles, id=c.fetchone()[0])
        if emoji.name == '✅':
            if not role in member.roles:
                await member.add_roles(role)
            return
        if '🗺️ Menu des roles' == embed.title:
            for field in embed.fields:
                if emoji.name in field.value:
                    role = get(guild.roles, name=field.value.split(' : ')[1].strip('`'))
                    await member.add_roles(role)
                    return
        if not payload.member.guild_permissions.administrator: return

        for i, field in enumerate(embed.fields):
            if '>>' not in field.name:
                continue
            if emoji.name in ['⏪', '⏩', '❌']:
                field_nb, name = len(embed.fields)-1, field.name.strip('<> ')
                index = field_nb if (i==0 and emoji.name in ['⏪', '❌']) else (0 if (i==field_nb and emoji.name in ['⏩', '❌']) else (i-1 if emoji.name=='⏪' else i+1))
                switch = embed.fields[index]
                embed.set_field_at(index if emoji!='❌' else i, name=f'>> {switch.name} <<', value=switch.value, inline=False)
                embed.set_footer(text=f"{switch.name} • {switch.value} • Appuie sur 🔧 quand tu as fini")
                if emoji.name == '❌':
                    role = get(guild.roles, name=name)
                    embed.remove_field(i)
                else:
                    embed.set_field_at(i, name=name, value=field.value, inline=False)
            elif emoji.name == '🔧':
                emojis = [field.value.strip("Émoji → Pas d'émoji défini") for field in embed.fields]
                if '' in emojis:
                    await channel.send('Vous devez définir tous les emojis avant de confirmer !', delete_after=5)
                    return
                role_embed = Embed(title='🗺️ Menu des roles', color=0xf1c40f)
                for emoji, field in zip(emojis, embed.fields):
                    name = field.name.strip('<> ')
                    role_embed.add_field(name='\u200b', value=f"{emoji} : `{name}`", inline=False)
                await channel.purge(limit=2)
                msg = await channel.send(embed=role_embed)
                for emoji in emojis:
                    await msg.add_reaction(emoji)
            else:
                embed.set_field_at(i, name=embed.fields[i].name, value=f'Émoji → {emoji}')
            try:
                await message.edit(embed=embed)
                await reaction.remove(member)
            except:
                pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        guild = await self.bot.fetch_guild(payload.guild_id)
        member = await guild.fetch_member(payload.user_id)
        if member.bot: return
        emoji = payload.emoji
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        embed = message.embeds[0]
        if '🗺️ Menu des roles' == embed.title:
            for field in embed.fields:
                if emoji.name in field.value:
                    role = get(guild.roles, name=field.value.split(' : ')[1].strip('`'))
                    await member.remove_roles(role)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        with connect('data.db') as conn:
            c = conn.cursor()
            c.execute("INSERT INTO logs (ID, State) VALUES (?, ?)", (guild.id, 0))
            c.execute(f'CREATE TABLE IF NOT EXISTS "{guild.id}" (User_ID INTEGER, Warns TEXT, Mute INTEGER, Verif INTEGER, Temp INTEGER)')
            conn.commit()
        channel = await self.bot.fetch_channel(747480897426817095)
        embed = (Embed(color=0xf1c40f)
                 .add_field(name='👥 Membres', value=f'{guild.member_count} members')
                 .add_field(name='🌍 Région', value=str(guild.region).capitalize())
                 .add_field(name='🗝️ Owner', value=guild.owner)
                 .set_author(name=f'''J'ai rejoint "{guild.name}"''', icon_url=guild.icon_url))
        await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Setup(bot))