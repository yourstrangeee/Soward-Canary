import discord
from discord.ext import commands

class VCRoleManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        # Ensure the database table exists
        async with self.bot.db.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS vc_roles (
                    guild_id BIGINT NOT NULL,
                    vc_id BIGINT NOT NULL,
                    role_id BIGINT NOT NULL,
                    PRIMARY KEY (guild_id, vc_id, role_id)
                )
            """)

    @commands.group(name="invc", invoke_without_command=True)
    @commands.has_permissions(manage_channels=True)
    async def invc(self, ctx):
        """Voice Channel Role System Commands."""
        await ctx.send("Use `invc add`, `invc remove`, or `invc config` for more options.")

    @invc.command(name="add")
    @commands.has_permissions(manage_channels=True)
    async def invc_add(self, ctx, channel: discord.VoiceChannel, role: discord.Role):
        """Add a role to be assigned when a member joins a specific VC."""
        # Dangerous permissions to check for
        dangerous_permissions = [
            "administrator",
            "manage_guild",
            "manage_roles",
            "ban_members",
            "kick_members",
            "manage_channels",
        ]

        # Check if the role has any dangerous permissions
        if any(getattr(role.permissions, perm) for perm in dangerous_permissions):
            await ctx.send(
                f"The role `{role.name}` cannot be added because it has dangerous permissions (e.g., `ADMINISTRATOR`, `MANAGE_GUILD`)."
            )
            return

        async with self.bot.db.acquire() as conn:
            # Check if the voice channel already has a role assigned
            existing_role = await conn.fetchrow(
                "SELECT role_id FROM vc_roles WHERE guild_id = $1 AND vc_id = $2",
                ctx.guild.id,
                channel.id,
            )
            
            if existing_role:
                existing_role_name = ctx.guild.get_role(existing_role["role_id"]).name
                await ctx.send(
                    f"The voice channel `{channel.name}` already has the role `{existing_role_name}` assigned. "
                    f"Use `invc remove` to remove it before adding a new role."
                )
                return
            
            # Add the role to the database
            await conn.execute(
                """
                INSERT INTO vc_roles (guild_id, vc_id, role_id)
                VALUES ($1, $2, $3)
                """,
                ctx.guild.id,
                channel.id,
                role.id,
            )
        
        await ctx.send(
            f"The role `{role.name}` has been successfully assigned to the voice channel `{channel.name}`."
        )
    
    @invc.command(name="remove")
    @commands.has_permissions(manage_channels=True)
    async def invc_remove(self, ctx, channel_id: int):
        """Remove the role assigned to a specific VC by channel ID."""
        channel = self.bot.get_channel(channel_id)
        if not channel or not isinstance(channel, discord.VoiceChannel):
            await ctx.send(f"No valid voice channel found with ID `{channel_id}`.")
            return

        async with self.bot.db.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM vc_roles WHERE guild_id = $1 AND vc_id = $2",
                ctx.guild.id,
                channel.id,
            )
        
        if result == "DELETE 0":
            await ctx.send(f"No role is currently assigned to the voice channel with ID `{channel_id}`.")
        else:
            await ctx.send(f"Role assignment for the voice channel `{channel.name}` has been removed.")

    @invc.command(name="reset")
    @commands.has_permissions(manage_channels=True)
    async def invc_reset(self, ctx):
        """Remove all VC-role assignments for the server."""
        async with self.bot.db.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM vc_roles WHERE guild_id = $1", ctx.guild.id
            )
        
        if result == "DELETE 0":
            await ctx.send("No roles are currently assigned to any voice channels in this server.")
        else:
            await ctx.send("All VC-role assignments have been successfully reset.")
    @invc.command(name="config")
    @commands.has_permissions(manage_channels=True)
    async def invc_config(self, ctx):
        """Show the current VC role configurations."""
        async with self.bot.db.acquire() as conn:
            records = await conn.fetch("""
                SELECT vc_id, role_id FROM vc_roles
                WHERE guild_id = $1
            """, ctx.guild.id)
        if not records:
            await ctx.send("No voice channel role configurations found.")
            return

        description = "\n".join(
            f"<#{record['vc_id']}> ➜ <@&{record['role_id']}>"
            for record in records
        )
        embed = discord.Embed(
            title="Voice Channel Role Configurations",
            description=description,
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Assign or remove roles when members join/leave voice channels."""
        if before.channel == after.channel:
            return  # No change in voice state

        async with self.bot.db.acquire() as conn:
            # Remove roles when leaving a VC
            if before.channel:
                records = await conn.fetch("""
                    SELECT role_id FROM vc_roles
                    WHERE guild_id = $1 AND vc_id = $2
                """, member.guild.id, before.channel.id)
                for record in records:
                    role = member.guild.get_role(record["role_id"])
                    if role:
                        await member.remove_roles(role, reason="Left voice channel")

            # Add roles when joining a VC
            if after.channel:
                records = await conn.fetch("""
                    SELECT role_id FROM vc_roles
                    WHERE guild_id = $1 AND vc_id = $2
                """, member.guild.id, after.channel.id)
                for record in records:
                    role = member.guild.get_role(record["role_id"])
                    if role:
                        await member.add_roles(role, reason="Joined voice channel")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.bot.wait_until_ready()
        bot = self.bot
        em = discord.Embed(title="Guild Joined")
        em.add_field(name="Guild Information:", value=f"Server Name: {guild.name}\nServer Id: {guild.id}\nServer Owner: {guild.owner.name} [{guild.owner.id}]\nCreated At: <t:{round(guild.created_at.timestamp())}:R>\nMember Count: {len(guild.members)} Members\nRoles: {len(guild.roles)} Roles\nText Channels: {len(guild.text_channels)} Channels\nVoice Channels: {len(guild.voice_channels)} Channels")
        em.add_field(name="Bot Info:", value=f"Servers: {len(bot.guilds)} Servers\nUsers: {len(bot.users)} Users\nChannels: {str(len(set(bot.get_all_channels())))} Channels")
        try:
            em.set_thumbnail(url=guild.icon.url)
        except:
            pass
        em.set_footer(text=f"{str(bot.user)}", icon_url=bot.user.avatar.url)
        webhook = bot.get_channel(1320704092225667105)
        await webhook.send(embed=em)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await self.bot.wait_until_ready()
        bot = self.bot
        if guild is None:
          return
        em = discord.Embed(title="Guild Leave", color=botinfo.root_color)
        em.add_field(name="Guild Information:", value=f"Server Name: {guild.name}\nServer Id: {guild.id}\nCreated At: <t:{round(guild.created_at.timestamp())}:R>\nMember Count: {len(guild.members)} Members\nRoles: {len(guild.roles)} Roles\nText Channels: {len(guild.text_channels)} Channels\nVoice Channels: {len(guild.voice_channels)} Channels")
        em.add_field(name="Bot Info:", value=f"Servers: {len(bot.guilds)} Servers\nUsers: {len(bot.users)} Users\nChannels: {str(len(set(bot.get_all_channels())))} Channels")
        try:
            em.set_thumbnail(url=guild.icon.url)
        except:
            pass
        em.set_footer(text=f"{str(bot.user)}", icon_url=bot.user.avatar.url)
        webhook = bot.get_channel(1320452887125561504)
        await webhook.send(embed=em)

async def setup(bot):
    await bot.add_cog(VCRoleManager(bot))
