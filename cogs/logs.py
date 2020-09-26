from discord import Embed, Colour
from discord.ext import commands
from discord import AuditLogAction
from discord.utils import get

from datetime import datetime, timezone
from sqlite3 import connect


class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def get_data(guild_id, channel=False):
        with connect('data.db') as conn:
            c = conn.cursor()
            if not channel:
                c.execute("SELECT State FROM logs WHERE ID=?", (guild_id,))
            else:
                c.execute("SELECT Logs FROM setup WHERE Guild_ID=?", (guild_id,))
            entry = c.fetchone()
            if entry is None and not channel:
                c.execute("INSERT INTO logs (ID, State) VALUES (?, ?)", (guild_id, 0))
                conn.commit()
                return False
            return int(entry[0]) if entry else False

    @staticmethod
    def check_logs(guild, logs=False):
        state = Logs.get_data(guild.id)
        channel = get(guild.text_channels, name='logs')
        return False if ((not state or channel is None) and not logs) else True

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def logs(self, ctx):
        await ctx.message.delete()
        state = Logs.get_data(ctx.guild.id)
        with connect('data.db') as conn:
            c = conn.cursor()
            if state is None:
                c.execute("INSERT INTO logs(ID, State) VALUES(?, ?)", (ctx.guild.id, 1))
            elif state:
                c.execute("UPDATE logs SET State=? WHERE ID=?", (0, ctx.guild.id))
            else:
                c.execute("UPDATE logs SET State=? WHERE ID=?", (1, ctx.guild.id))
            conn.commit()
            state = 'désactivés' if state else 'activés'
            await ctx.send(f"Logs {state}", delete_after=5.0)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        param = error.param.name if isinstance(error, commands.MissingRequiredArgument) else ''
        perms = ', '.join(error.missing_perms) if isinstance(error, commands.BotMissingPermissions) else ''
        invoke_errors = {
            'index': "Nombre invalide !",
            'is_playing': "Je ne suis connecté à aucun channel !",
            'unpack': "L'utilisateur n'a pas de warns !",
            'channel': "Tu n'es connecté à aucun channel !",
            'Missing Permissions': "Je n'ai pas la permission de faire ça !",
            'ValueError': 'Arguments invalides !',
            'KeyError': 'Arguments invalides !'
        }
        errors = {
            "<class 'discord.ext.commands.errors.MissingRequiredArgument'>": f'Tu as oublié un argument : {param}',
            "<class 'discord.ext.commands.errors.CommandNotFound'>": 'Commande inexistante !',
            "<class 'discord.ext.commands.errors.MissingPermissions'>": "Tu n'as pas la permission de faire ça !",
            "<class 'discord.ext.commands.errors.BotMissingPermissions'>": f"J'ai besoin de ces permissions : {perms} !",
            "<class 'discord.ext.commands.errors.BadArgument'>": 'Tu dois entrer un nombre entier!' if 'int' in str(error) else "Membre introuvable !",
            "<class 'discord.ext.commands.errors.CommandInvokeError'>": ''.join([value for key, value in invoke_errors.items() if key in str(error)]),
            "<class 'discord.ext.commands.errors.MemberNotFound'>": 'Membre ou Role inexistant !\nAvez-vous essayé de le mentionner ?',
            "<class 'discord.ext.commands.errors.BadInviteArgument'>": "Lien d'invitation invalide !",
        }
        clean_error = errors[str(type(error))]
        if not clean_error:
            raise error
        embed = Embed(title="❌ Oups ! Il y a une erreur :", description=clean_error, color=0xe74c3c)
        await ctx.message.delete()
        await ctx.send(embed=embed, delete_after=5.0)

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        cmd = ctx.command.name
        state = Logs.get_data(ctx.guild.id)
        if not Logs.check_logs(ctx.guild, True if cmd=='logs' else False):
            return

        if Logs.get_data(ctx.guild.id, True):
            channel = get(ctx.guild.text_channels, id=Logs.get_data(ctx.guild.id, True))
        else:
            channel = get(ctx.guild.text_channels, name='logs')
        state = 'a activé' if state else 'a désactivé'
        
        cmd_args = ctx.message.content[len(cmd)+1:].split()
        if len(cmd_args)<2:
            cmd_args += ['', '']
        cmd_list = {
            'warn': {'title': '⚠️ Membre warn', 'desc':f"{ctx.author.mention} a warn {cmd_args[0]}\n**Raison:** {' '.join(cmd_args[1:])}", 'color': 0xe67e22},
            'mute': {'title': '🔇 Membre muté', 'desc': f"{ctx.author.mention} a mute {cmd_args[0]}\n**Durée**: {cmd_args[1]}\n**Raison:** {' '.join(cmd_args[2:])}", 'color': 0xe74c3c},
            'clear': {'title': '🗑️  Messages effacés', 'desc': f"{ctx.author.mention} a supprimé {cmd_args[0]} messages.", 'color': 0x1f8b4c},
            'poll': {'title': '📋 Sondage créé', 'desc': f"Question: *{cmd_args[0]}*\nChoix: *{' / '.join(cmd_args[1:])}*\nPar {ctx.author.mention}",'color': 0x7289da},
            'logs': {'title': f'🖨️ Logs {state}', 'desc': f'{ctx.author.mention} {state} les logs', 'color': 0x11806a},
            'role': {'title': f'💾 "{cmd_args[0]}" modifié', 'desc': f'{ctx.author.mention} a défini {cmd_args[1]} pour "{cmd_args[0]}"', 'color': 0xa84300}
        }

        if not cmd in cmd_list.keys():
            return

        embed = Embed(title=cmd_list[cmd]['title'], description=cmd_list[cmd]['desc'], color=cmd_list[cmd]['color'], timestamp=datetime.now())
        await channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if not Logs.check_logs(member.guild):
            return

        entry = await member.guild.audit_logs(limit=1).flatten()
        channel = get(member.guild.text_channels, id=Logs.get_data(member.guild.id, True))

        if entry[0].action == AuditLogAction.ban:
            embed = Embed(title=':man_judge: Membre banni', description=f"{entry[0].user.mention} a ban {entry[0].target.mention}\n**Raison:** {entry[0].reason}", color=0xe74c3c, timestamp=datetime.now())
        elif entry[0].action == AuditLogAction.kick:
            embed = Embed(title=':man_judge: Membre kick', description=f"{entry[0].user.mention} a kick {entry[0].target.mention}\n**Raison:** {entry[0].reason}", color=0xe74c3c, timestamp=datetime.now())
        else:
            embed = Embed(description=f'**:outbox_tray: {member.mention} a quitté le serveur**', color=0xe74c3c, timestamp=datetime.now())
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        if not Logs.check_logs(guild):
            return

        entry = await guild.audit_logs(limit=1).flatten()
        channel = get(guild.text_channels, id=Logs.get_data(guild.id, True))
        embed = Embed(title=':man_judge: Membre unban', description=f"{entry[0].user.mention} a unban {entry[0].target}\n**Raison:** {entry[0].reason}", color=0xc27c0e, timestamp=datetime.now())
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if not Logs.check_logs(member.guild):
            return

        channel = get(member.guild.text_channels, id=Logs.get_data(member.guild.id, True))
        embed = Embed(description=f'**:inbox_tray: {member.mention} a rejoint le serveur !**', color=0x2ecc71, timestamp=datetime.now())
        await channel.send(embed=embed)

        embed = Embed(title=":inbox_tray: Nouveau membre !", description=f'{member.mention} a rejoint le serveru', color=0x2ecc71, timestamp=datetime.now())
        embed.set_image(url=member.avatar_url)
        await member.guild.system_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if not Logs.check_logs(before.guild):
            return

        entry = await after.guild.audit_logs(limit=1).flatten()
        channel = get(before.guild.text_channels, id=Logs.get_data(before.guild.id, True))
        embed = Embed(title=":notepad_spiral: Modification de profil", description=f'{entry[0].user.mention} a modifié {before.mention}', color=0x99aab5, timestamp=datetime.now())

        if before.display_name != after.display_name:
            embed.add_field(name="Pseudo:", value=f"{before.display_name} → {after.display_name}")
        elif before.roles != after.roles:
            new_roles = [role.name for role in after.roles if role not in before.roles]
            removed_roles = [role.name for role in before.roles if role not in after.roles]
            new_roles = "Nouveaux roles: "+("".join(new_roles) if new_roles else "None")
            removed_roles = "Roles supprimés: "+("".join(removed_roles) if removed_roles else "None")
            embed.add_field(name="Roles:", value=f"{new_roles}\n{removed_roles}")
        else:
            return
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        with connect('data.db') as conn:
            c = conn.cursor()
            c.execute("DELETE FROM logs WHERE ID=?", (guild.id,))
            c.execute(f'DROP TABLE"{guild.id}"')
            conn.commit()
        channel = await self.bot.fetch_channel(747480897426817095)
        embed = (Embed(color=0xf1c40f, timestamp=datetime.now())
                 .add_field(name='👥 Membres', value=f'{guild.member_count} members')
                 .add_field(name='🌍 Région', value=str(guild.region).capitalize())
                 .add_field(name='🗝️ Owner', value=guild.owner)
                 .set_author(name=f'''J'ai quitté "{guild.name}"''', icon_url=guild.icon_url))
        await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Logs(bot))