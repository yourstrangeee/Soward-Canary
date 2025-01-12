import discord
from discord.ext import commands
import datetime
import asyncpg
from discord.ui import View, Button
import discord
from discord.ext import commands
from discord.ui import View

class InviteLeaderboardView(View):
    def __init__(self, leaderboard_data, per_page=10):
        super().__init__(timeout=120)  # 2-minute timeout for interaction
        self.leaderboard_data = leaderboard_data
        self.per_page = per_page
        self.current_page = 0

        self.max_pages = (len(leaderboard_data) - 1) // per_page + 1
        self.embed_message = None

        self.update_buttons()

    def update_buttons(self):
        # Enable/disable navigation buttons based on the current page
        self.first_page.disabled = self.current_page == 0
        self.previous_page.disabled = self.current_page == 0
        self.next_page.disabled = self.current_page >= self.max_pages - 1
        self.last_page.disabled = self.current_page >= self.max_pages - 1

    async def update_embed(self, interaction=None):
        """Updates the embed with the current page's data."""
        start = self.current_page * self.per_page
        end = start + self.per_page
        page_data = self.leaderboard_data[start:end]

        embed = discord.Embed(title="🏆 Invite Leaderboard", color=0x2f3136)

        if page_data:
            description = ""
            for idx, entry in enumerate(page_data, start=start + 1):
                member_name, total_invites, joins, leaves, fakes, rejoins = entry
                description += (
                    f"**#{idx} {member_name}** - {total_invites} Invites "
                    f"({joins} Joins, {leaves} Leaves, {fakes} Fakes, {rejoins} Rejoins)\n"
                )
            embed.description = description
        else:
            embed.description = "No data available."

        # Add the guild icon and page information to the footer
        guild_icon_url = self.embed_message.guild.icon.url if self.embed_message.guild.icon else None
        embed.set_footer(
            text=f"Page {self.current_page + 1}/{self.max_pages}",
            icon_url=guild_icon_url
        )

        if interaction:
            await interaction.response.edit_message(embed=embed, view=self)
        elif self.embed_message:
            await self.embed_message.edit(embed=embed, view=self)

    async def start(self, ctx):
        """Start the paginator."""
         # Set initial embed content
        embed = discord.Embed(title="🏆 Invite Leaderboard", description="Loading...", color=0x2f3136)

        self.embed_message = await ctx.send(embed=embed, view=self)
        await self.update_embed()

    @discord.ui.button(label="⏮", style=discord.ButtonStyle.secondary)
    async def first_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = 0
        self.update_buttons()
        await self.update_embed(interaction)

    @discord.ui.button(label="⏪", style=discord.ButtonStyle.primary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = max(0, self.current_page - 1)
        self.update_buttons()
        await self.update_embed(interaction)

    @discord.ui.button(emoji="⏹", style=discord.ButtonStyle.danger)
    async def stop_pagination(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Stops the pagination and disables all buttons."""
        for child in self.children:
            child.disabled = True  # Disable all buttons
        await interaction.response.edit_message(view=self)  # Update the message to disable buttons
        self.stop()  # Stop the view's event loop

    @discord.ui.button(label="⏩", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = min(self.max_pages - 1, self.current_page + 1)
        self.update_buttons()
        await self.update_embed(interaction)

    @discord.ui.button(label="⏭", style=discord.ButtonStyle.secondary)
    async def last_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = self.max_pages - 1
        self.update_buttons()
        await self.update_embed(interaction)

    

    

class InviteResetView(View):
    def __init__(self, ctx, member=None):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.member = member
        self.response = None

    async def interaction_check(self, interaction):
        return interaction.user == self.ctx.author

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction, button):
        self.response = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction, button):
        self.response = False
        self.stop()
        await interaction.response.defer()

class Database:
    def __init__(self, dsn):
        self.dsn = dsn
        self.pool = None

    async def connect(self):
        """Create a connection pool."""
        self.pool = await asyncpg.create_pool(dsn=self.dsn)

    async def disconnect(self):
        """Close the connection pool."""
        if self.pool:
            await self.pool.close()

    async def create_tables(self):
        """Creates the necessary tables."""
        async with self.pool.acquire() as conn:
            # Invites table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS invites (
                    guild_id BIGINT NOT NULL,
                    invite_code TEXT NOT NULL,
                    inviter_id BIGINT NOT NULL,
                    uses INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (guild_id, invite_code)
                );
            """)

            await conn.execute("""CREATE TABLE IF NOT EXISTS invited (
                guild_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL,
                invite_code TEXT,
                inviter_id BIGINT,
                joined_at TIMESTAMP DEFAULT NOW(),
                PRIMARY KEY (guild_id, user_id));""")

            # Invite stats table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS invite_stats (
                    guild_id BIGINT NOT NULL,
                    inviter_id BIGINT NOT NULL,
                    total_invites INTEGER NOT NULL DEFAULT 0,
                    fake_invites INTEGER NOT NULL DEFAULT 0,
                    rejoin_count INTEGER NOT NULL DEFAULT 0,
                    left_count INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (guild_id, inviter_id)
                );
            """)

            # Member history table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS member_history (
                    guild_id BIGINT NOT NULL,
                    user_id BIGINT NOT NULL,
                    first_joined TIMESTAMP WITH TIME ZONE NOT NULL,
                    PRIMARY KEY (guild_id, user_id)
                );
            """)
            await conn.execute("""CREATE TABLE IF NOT EXISTS log_channels (
                guild_id BIGINT PRIMARY KEY,
                leave_channel_id BIGINT,
                join_channel_id BIGINT
                );
            """)
            await conn.execute("""CREATE TABLE IF NOT EXISTS vanity_uses (guild_id BIGINT PRIMARY KEY, uses INT DEFAULT 0);""")
    async def get_vanity_uses(self, guild_id):
        async with self.db.pool.acquire() as conn:
            result = await conn.fetchrow("SELECT uses FROM vanity_uses WHERE guild_id = $1", guild_id)
            return result['uses'] if result else 0

    async def update_vanity_uses(self, guild_id, uses):
        async with self.db.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO vanity_uses (guild_id, uses)
                VALUES ($1, $2)
                ON CONFLICT (guild_id) DO UPDATE
                SET uses = $2
            """, guild_id, uses)
    async def insert_or_update_join(self, guild_id,  channel_id):
        """Insert or update kooin channel."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO log_channels (guild_id, join_channel_id)
                VALUES ($1, $2)
                ON CONFLICT (guild_id)
                DO UPDATE SET join_channel_id = $2
            """, guild_id, channel_id)

    async def insert_or_update_invite(self, guild_id, invite_code, inviter_id, uses):
        """Insert or update an invite."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO invites (guild_id, invite_code, inviter_id, uses)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (guild_id, invite_code)
                DO UPDATE SET uses = $4
            """, guild_id, invite_code, inviter_id, uses)

    async def get_invites(self, guild_id):
        """Retrieve all invites for a guild."""
        async with self.pool.acquire() as conn:
            return await conn.fetch("""
                SELECT invite_code, inviter_id, uses FROM invites WHERE guild_id = $1
            """, guild_id)

    async def delete_invite(self, guild_id, invite_code):
        """Delete an invite."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                DELETE FROM invites WHERE guild_id = $1 AND invite_code = $2
            """, guild_id, invite_code)

    async def update_invite_stats(self, guild_id, inviter_id, fake=False, rejoin=False, left=False):
        """Update invite stats for an inviter."""
        async with self.pool.acquire() as conn:
            if fake:
                print(f"[DEBUG] Incrementing fake_invites for inviter ID: {inviter_id} in guild ID: {guild_id}.")
                await conn.execute("""
                    INSERT INTO invite_stats (guild_id, inviter_id, fake_invites)
                    VALUES ($1, $2, 1)
                    ON CONFLICT (guild_id, inviter_id)
                    DO UPDATE SET fake_invites = invite_stats.fake_invites + 1
                """, guild_id, inviter_id)
            elif rejoin:
                print(f"[DEBUG] Incrementing rejoin_count for inviter ID: {inviter_id} in guild ID: {guild_id}.")
                await conn.execute("""
                                   INSERT INTO invite_stats (guild_id, inviter_id, rejoin_count)
                                   VALUES ($1, $2, 1)
                                   ON CONFLICT (guild_id, inviter_id)
                                   DO UPDATE SET rejoin_count = invite_stats.rejoin_count + 1
                                   """, guild_id, inviter_id)
            elif left:
                print(f"[DEBUG] Incrementing left_count for inviter ID: {inviter_id} in guild ID: {guild_id}.")
                await conn.execute("""
                    UPDATE invite_stats
                    SET left_count = left_count + 1
                    WHERE guild_id = $1 AND inviter_id = $2
                """, guild_id, inviter_id)
            else:
                print(f"[DEBUG] Incrementing total_invites for inviter ID: {inviter_id} in guild ID: {guild_id}.")
                await conn.execute("""
                    INSERT INTO invite_stats (guild_id, inviter_id, total_invites)
                    VALUES ($1, $2, 1)
                    ON CONFLICT (guild_id, inviter_id)
                    DO UPDATE SET total_invites = invite_stats.total_invites + 1
                """, guild_id, inviter_id)

    async def get_join_channel(self, guild_id):
        """Get invite stats for a user."""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("""
                SELECT channel_id
                FROM join_channels
                WHERE guild_id = $1
            """, guild_id)

    async def get_invite_stats(self, guild_id, inviter_id):
        """Get invite stats for a user."""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("""
                SELECT total_invites, fake_invites, rejoin_count, left_count
                FROM invite_stats
                WHERE guild_id = $1 AND inviter_id = $2
            """, guild_id, inviter_id)

    async def insert_or_update_member_history(self, guild_id, user_id):
        """Insert or update member join history."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO member_history (guild_id, user_id, first_joined)
                VALUES ($1, $2, NOW())
                ON CONFLICT (guild_id, user_id)
                DO NOTHING
            """, guild_id, user_id)

class InviteTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database(dsn="postgresql://prince024:shaizan24@localhost:5432/soward")
        self.invite_cache = {}

    async def cog_load(self):
        """Called when the cog is loaded."""
        await self.db.connect()
        await self.db.create_tables()

        # Cache invites for all guilds the bot is in
        for guild in self.bot.guilds:
            await self.cache_invites(guild)

    async def cache_invites(self, guild):
        """Cache all invites for the given guild."""
        invites = await guild.invites()
        for invite in invites:
            self.invite_cache[invite.code] = {
                'inviter_id': invite.inviter.id,
                'uses': invite.uses
            }

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        """Handles when a new invite is created."""
        try:
            self.invite_cache[invite.code] = {
                'inviter_id': invite.inviter.id,
                'uses': invite.uses
            }
        except Exception as e:
            print(f"Error updating invite cache: {e}")
        await self.db.insert_or_update_invite(
            guild_id=invite.guild.id,
            invite_code=invite.code,
            inviter_id=invite.inviter.id,
            uses=invite.uses
        )

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        """Handles when an invite is deleted."""
        if invite.code in self.invite_cache:
            del self.invite_cache[invite.code]
        await self.db.delete_invite(guild_id=invite.guild.id, invite_code=invite.code)

   # @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        current_invites = await guild.invites()
        inviter = "vanity"  # Default to vanity if no inviter is found
        uses = None
        inviter_id = None
        try:
            vanity_invite = await member.guild.vanity_invite()
            vanity_uses = vanity_invite.uses if vanity_invite else None
        except Exception as e:
            vanity_uses = None 
        db_invites = await self.db.get_invites(guild.id)
        db_invites_dict = {invite['invite_code']: invite['uses'] for invite in db_invites}

        # Compare invites to determine the inviter
        for invite in current_invites:
            if invite.uses > db_invites_dict.get(invite.code, 0):
                inviter = invite.inviter
                inviter_id = invite.inviter.id
                uses = invite.uses
                # Update the invite in the database
                await self.db.insert_or_update_invite(
                    guild_id=guild.id,
                    invite_code=invite.code,
                    inviter_id=invite.inviter.id,
                    uses=invite.uses
                )
                break

        # Calculate account age
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        account_age_days = (now - member.created_at).days
        account_age_months = account_age_days // 30

        
        async with self.db.pool.acquire() as conn:
            channel_record = await conn.fetchrow("""
            SELECT join_channel_id FROM log_channels WHERE guild_id = $1
            """, guild.id)

        
        if channel_record:
            channel_id = channel_record['join_channel_id']
            join_channel = guild.get_channel(channel_id)

            if join_channel:
                if inviter == "vanity":
                    message = (
                        f"✛ Welcome `{str(member)}`!\n"
                        f"✛ Created `{account_age_months} months ago`\n"
                        f"✛ They joined using the vanity URL (uses: `{vanity_uses}`)\n"
                        f"✛ `{guild.name}` now has `{guild.member_count}` members"
                    )
                else:
                    stats = await self.db.get_invite_stats(member.guild.id, invite.inviter.id)

     
                    
                    total_invites = stats.get('total_invites', 0)
                    fake_invites = stats.get('fake_invites', 0)
                    rejoin_count = stats.get('rejoin_count', 0)
                    left_count = stats.get('left_count', 0)
                    invalid_invites = fake_invites + rejoin_count + left_count
                    current = max(0, total_invites - invalid_invites)

                    message = (
                        f"✛ Welcome `{str(member)}` `({member.name}#{member.discriminator})!`\n"
                        f"✛ Created `{account_age_months}` months ago\n"
                        f"✛ They were invited by `{inviter.name}#{inviter.discriminator} `"
                        f"(total invites: `{current}`)\n"
                        f"✛ `{guild.name}` now has `{guild.member_count}` members"
                    )
                await join_channel.send(message)
            else:
                print(f"[DEBUG] Join channel with ID {channel_id} not found in guild {guild.name}.")
        else:
            print(f"[DEBUG] No join channel set for guild {guild.name}.")

        # Additional logic for handling fake invites and rejoin tracking
        if account_age_days < 30:  # Less than 30 days old
            print(f"[DEBUG] Marking {member.name}#{member.discriminator}'s inviter (ID: {inviter_id}) with a fake invite.")
            await self.db.update_invite_stats(guild.id, inviter_id, fake=True)

        async with self.db.pool.acquire() as conn:
            record = await conn.fetchrow("""
                SELECT first_joined FROM member_history
                WHERE guild_id = $1 AND user_id = $2
            """, guild.id, member.id)
            if not record:
                print(f"[DEBUG] Member {member.id} ({member.name}) not found in member_history. Inserting new record.")
                await self.db.insert_or_update_member_history(guild.id, member.id)
            else:
                print(f"[DEBUG] Member {member.id} ({member.name}) found in member_history. Updating rejoin count.")
                await self.db.update_invite_stats(guild.id, inviter_id, rejoin=True)

        await self.db.update_invite_stats(guild.id, inviter_id)

    #@commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        current_invites = await guild.invites()
        inviter = "vanity"  # Default to vanity if no inviter is found
        uses = None
        inviter_id = None

        try:
            vanity_invite = await guild.vanity_invite()
            vanity_uses = vanity_invite.uses if vanity_invite else None
        except Exception as e:
            print(f"[DEBUG] Error fetching vanity invite: {e}")
            vanity_uses = None 

        db_invites = await self.db.get_invites(guild.id)
        db_invites_dict = {invite['invite_code']: invite['uses'] for invite in db_invites or []}

        # Compare invites to determine the inviter
        for invite in current_invites:
            if invite.uses > db_invites_dict.get(invite.code, 0):
                inviter = invite.inviter
                inviter_id = invite.inviter.id
                uses = invite.uses

                # Update the invite in the database
                await self.db.insert_or_update_invite(
                    guild_id=guild.id,
                    invite_code=invite.code,
                    inviter_id=invite.inviter.id,
                    uses=invite.uses
                )
                break

        # Calculate account age
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        account_age_days = (now - member.created_at).days
        account_age_months = account_age_days // 30

        async with self.db.pool.acquire() as conn:
            channel_record = await conn.fetchrow("""
                SELECT join_channel_id FROM log_channels WHERE guild_id = $1
            """, guild.id)

        if channel_record:
            channel_id = channel_record['join_channel_id']
            join_channel = guild.get_channel(channel_id)

            if join_channel:
                if inviter == "vanity":
                    message = (
                        f"✛ Welcome `{str(member)}`!\n"
                        f"✛ Created `{account_age_months} months ago`\n"
                        f"✛ They joined using the vanity URL (uses: `{vanity_uses}`)\n"
                        f"✛ `{guild.name}` now has `{guild.member_count}` members"
                    )
                else:
                    stats = await self.db.get_invite_stats(member.guild.id, inviter_id)
                    stats = stats or {}
                    total_invites = stats.get('total_invites', 0)
                    fake_invites = stats.get('fake_invites', 0)
                    rejoin_count = stats.get('rejoin_count', 0)
                    left_count = stats.get('left_count', 0)
                    invalid_invites = fake_invites + rejoin_count + left_count
                    current = max(0, total_invites - invalid_invites)

                    message = (
                        f"✛ Welcome `{str(member)}` `({member.name}#{member.discriminator})!`\n"
                        f"✛ Created `{account_age_months}` months ago\n"
                        f"✛ They were invited by `{inviter.name}#{inviter.discriminator}` "
                        f"(total invites: `{current}`)\n"
                        f"✛ `{guild.name}` now has `{guild.member_count}` members"
                    )
                await join_channel.send(message)
            else:
                print(f"[DEBUG] Join channel with ID {channel_id} not found in guild {guild.name}.")
        else:
            print(f"[DEBUG] No join channel set for guild {guild.name}.")

        # Additional logic for handling fake invites and rejoin tracking
        if account_age_days < 30:  # Less than 30 days old
            print(f"[DEBUG] Marking {member.name}#{member.discriminator}'s inviter (ID: {inviter_id}) with a fake invite.")
            if inviter_id:
                await self.db.update_invite_stats(guild.id, inviter_id, fake=True)

        async with self.db.pool.acquire() as conn:
            record = await conn.fetchrow("""
                SELECT first_joined FROM member_history
                WHERE guild_id = $1 AND user_id = $2
            """, guild.id, member.id)
            if not record:
                print(f"[DEBUG] Member {member.id} ({member.name}) not found in member_history. Inserting new record.")
                await self.db.insert_or_update_member_history(guild.id, member.id)
            else:
                print(f"[DEBUG] Member {member.id} ({member.name}) found in member_history. Updating rejoin count.")
                if inviter_id:
                    await self.db.update_invite_stats(guild.id, inviter_id, rejoin=True)

        if inviter_id:
            await self.db.update_invite_stats(guild.id, inviter_id)
            
    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        inviter = "unknown"
        inviter_id = None
        vanity_uses = None
        current_invites = await guild.invites()

        try:
            # Fetch the vanity invite
            vanity_invite = await guild.vanity_invite()
            current_vanity_uses = vanity_invite.uses if vanity_invite else 0

            # Fetch previous vanity uses from the database
            async with self.db.pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT uses FROM vanity_uses WHERE guild_id = $1
                """, guild.id)
                previous_vanity_uses = result['uses'] if result else 0

            # Check if vanity uses increased
            if current_vanity_uses > previous_vanity_uses:
                inviter = "vanity"
                vanity_uses = current_vanity_uses

                # Update the vanity uses in the database
                async with self.db.pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO vanity_uses (guild_id, uses)
                        VALUES ($1, $2)
                        ON CONFLICT (guild_id) DO UPDATE
                       SET uses = $2
                    """, guild.id, current_vanity_uses)

        except Exception as e:
            print(f"[DEBUG] Error fetching or updating vanity invite: {e}")
            vanity_uses = None

        # Handle normal invites
        if inviter != "vanity":
            db_invites = await self.db.get_invites(guild.id)
            db_invites_dict = {invite['invite_code']: invite['uses'] for invite in db_invites or []}

            for invite in current_invites:
                if invite.uses > db_invites_dict.get(invite.code, 0):
                    inviter = invite.inviter
                    inviter_id = invite.inviter.id

                    # Update the invite in the database
                    await self.db.insert_or_update_invite(
                        guild_id=guild.id,
                        invite_code=invite.code,
                        inviter_id=invite.inviter.id,
                        uses=invite.uses
                    )
                    break
        
        # Save inviter and member info to the invited table
        async with self.db.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO invited (guild_id, invite_code, inviter_id, user_id, joined_at)
                VALUES ($1, $2, $3, $4, NOW())
                ON CONFLICT (guild_id, user_id) DO UPDATE 
                SET invite_code = $2, 
                    inviter_id = $3, 
                    joined_at = NOW()
            """, guild.id, invite.code, inviter_id, member.id)
        # Log the join event
        async with self.db.pool.acquire() as conn:
            channel_record = await conn.fetchrow("""
                SELECT join_channel_id FROM log_channels WHERE guild_id = $1
            """, guild.id)

            if channel_record:
                join_channel_id = channel_record['join_channel_id']
                join_channel = guild.get_channel(join_channel_id)

                if join_channel:
                    # Create message
                    if inviter == "vanity":
                        message = (
                            f"✛ Welcome `{member}`!\n"
                            f"✛ They joined using the vanity URL (uses: `{vanity_uses}`)\n"
                            f"✛ `{guild.name}` now has `{guild.member_count}` members"
                        )
                    else:
                        # Fetch inviter stats
                        stats = await self.db.get_invite_stats(member.guild.id, inviter_id)
                        stats = stats or {}
                        total_invites = stats.get('total_invites', 0)
                        fake_invites = stats.get('fake_invites', 0)
                        rejoin_count = stats.get('rejoin_count', 0)
                        left_count = stats.get('left_count', 0)
                        invalid_invites = fake_invites + rejoin_count + left_count
                        current = max(0, total_invites - invalid_invites)

                        message = (
                            f"✛ Welcome `{str(member)}` `({member.name}#{member.discriminator})!`\n"
                            f"✛ They were invited by `{inviter.name}#{inviter.discriminator}` "
                            f"(total invites: `{current}`)\n"
                            f"✛ `{guild.name}` now has `{guild.member_count}` members"
                        )

                    await join_channel.send(message)
                else:
                    print(f"[DEBUG] Join channel not found in guild {guild.name}.")
            else:
                print(f"[DEBUG] No join channel set for guild {guild.name}.")

        # Update inviter's fake invites if member's account is too new
        account_age_days = (datetime.datetime.now(tz=datetime.timezone.utc) - member.created_at).days
        if account_age_days < 30 and inviter_id:  # Less than 30 days old
            await self.db.update_invite_stats(guild.id, inviter_id, fake=True)

        # Handle rejoin logic
        async with self.db.pool.acquire() as conn:
            record = await conn.fetchrow("""
                SELECT first_joined FROM member_history
                WHERE guild_id = $1 AND user_id = $2
            """, guild.id, member.id)
            if not record:
                await self.db.insert_or_update_member_history(guild.id, member.id)
            else:
                if inviter_id:
                    await self.db.update_invite_stats(guild.id, inviter_id, rejoin=True)

        # Update inviter stats
        if inviter_id:
            await self.db.update_invite_stats(guild.id, inviter_id)
        

#    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Handles logging when a member leaves the server."""
        guild = member.guild
        try:
            vanity_invite = await ctx.guild.vanity_invite()
            vanity_uses = vanity_invite.uses if vanity_invite else None
        except Exception as e:
            vanity_uses = None 
        async with self.db.pool.acquire() as conn:
            # Fetch the inviter ID from the database
            inviter_record = await conn.fetchrow("""
                SELECT inviter_id, invite_code FROM invites
                WHERE guild_id = $1 AND invite_code IN (
                SELECT invite_code FROM invites WHERE guild_id = $1
                )
            """, guild.id)

            inviter_id = inviter_record['inviter_id'] if inviter_record else None
            invite_code = inviter_record['invite_code'] if inviter_record else None

            # Update stats if inviter is found
            if inviter_id:
                await self.db.update_invite_stats(guild.id, inviter_id, left=True)

            # Fetch leave log channel
            channel_record = await conn.fetchrow("""
                SELECT leave_channel_id FROM log_channels WHERE guild_id = $1
            """, guild.id)

            if channel_record and channel_record['leave_channel_id']:
                leave_channel = guild.get_channel(channel_record['leave_channel_id'])
                if leave_channel:
                    inv = self.bot.get_user(inviter_id)
                    inviter_mention = "vanity" if not inviter_id else f"{str(inv)}"
                    inviter_uses = 0

                # Fetch inviter uses if inviter exists
                    if inviter_id:
                        stats = await self.db.get_invite_stats(member.guild.id, inviter_id)
                        total_invites = stats.get('total_invites', 0)
                        fake_invites = stats.get('fake_invites', 0)
                        rejoin_count = stats.get('rejoin_count', 0)
                        left_count = stats.get('left_count', 0)

                          # Calculate current valid invites
                        invalid_invites = fake_invites + rejoin_count + left_count
                        current = max(0, total_invites - invalid_invites)
                    # Construct and send the leave message
                    leave_message = (
                        f"✛ `{str(member)}` just left the server :(\n"
                        f"✛ They were invited by `{inviter_mention}` `({current if inviter_id else vanity_uses})`\n"
                        f"✛` {guild.name}` now has `{guild.member_count}` members"
                    )
                    await leave_channel.send(leave_message)
                else:
                    print(f"[DEBUG] Leave log channel with ID {channel_record['leave_channel_id']} not found.")
            else:
                print(f"[DEBUG] No leave log channel set for guild {guild.name}.")


 #   @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Handles logging when a member leaves the server."""
        guild = member.guild
        inviter_mention = "unknown"
        vanity_uses = None
        inviter_id = None

        try:
            # Fetch the current vanity invite uses
            vanity_invite = await guild.vanity_invite()
            vanity_uses = vanity_invite.uses if vanity_invite else None
        except Exception as e:
            print(f"[DEBUG] Error fetching vanity invite: {e}")
            vanity_uses = None

        async with self.db.pool.acquire() as conn:
            # Fetch inviter details from the database
            inviter_record = await conn.fetchrow("""
                SELECT inviter_id, invite_code FROM invites
                WHERE guild_id = $1 AND invite_code IN (
                    SELECT invite_code FROM invites WHERE guild_id = $1
                )
            """, guild.id)

            if inviter_record:
                inviter_id = inviter_record['inviter_id']
                invite_code = inviter_record['invite_code']

                # Update stats for the inviter if found
                if inviter_id:
                    await self.db.update_invite_stats(guild.id, inviter_id, left=True)

            # Fetch the leave log channel
            channel_record = await conn.fetchrow("""
                SELECT leave_channel_id FROM log_channels WHERE guild_id = $1
            """, guild.id)

            if channel_record and channel_record['leave_channel_id']:
                leave_channel = guild.get_channel(channel_record['leave_channel_id'])

                if leave_channel:
                    # Fetch inviter details for logs
                    if inviter_id:
                        inviter_user = self.bot.get_user(inviter_id)
                        inviter_mention = (
                            f"{inviter_user.name}#{inviter_user.discriminator}"
                            if inviter_user else f"User ID: {inviter_id}"
                        )

                        # Fetch inviter stats
                        stats = await self.db.get_invite_stats(guild.id, inviter_id)
                        total_invites = stats.get('total_invites', 0)
                        fake_invites = stats.get('fake_invites', 0)
                        rejoin_count = stats.get('rejoin_count', 0)
                        left_count = stats.get('left_count', 0)

                        # Calculate current valid invites
                        invalid_invites = fake_invites + rejoin_count + left_count
                        current_valid_invites = max(0, total_invites - invalid_invites)

                        # Construct the leave message for normal inviter
                        leave_message = (
                            f"✛ `{str(member)}` just left the server :(\n"
                            f"✛ They were invited by `{inviter_mention}` "
                            f"(`{current_valid_invites}` invites)\n"
                            f"✛ `{guild.name}` now has `{guild.member_count}` members"
                        )
                    else:
                        # Construct the leave message for vanity invite
                        leave_message = (
                            f"✛ `{str(member)}` just left the server :(\n"
                            f"✛ They were invited by `vanity` (`{vanity_uses}` uses)\n"
                            f"✛ `{guild.name}` now has `{guild.member_count}` members"
                        )

                    # Send the leave log
                    await leave_channel.send(leave_message)
                else:
                    print(f"[DEBUG] Leave log channel with ID {channel_record['leave_channel_id']} not found.")
            else:
                print(f"[DEBUG] No leave log channel set for guild {guild.name}.")
            
  #  @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Handles logging when a member leaves the server."""
        guild = member.guild
        inviter_mention = "unknown"
        vanity_uses = None
        inviter_id = None

        try:
            # Fetch the current vanity invite uses
            vanity_invite = await guild.vanity_invite()
            vanity_uses = vanity_invite.uses if vanity_invite else None
        except Exception as e:
            print(f"[DEBUG] Error fetching vanity invite: {e}")
            vanity_uses = None

        async with self.db.pool.acquire() as conn:
            # Fetch inviter details from the database
            inviter_record = await conn.fetchrow("""
                SELECT inviter_id, invite_code FROM invites
                WHERE guild_id = $1 AND invite_code IN (
                    SELECT invite_code FROM invites WHERE guild_id = $1
                )
            """, guild.id)
  
            if inviter_record:
                inviter_id = inviter_record['inviter_id']
                invite_code = inviter_record['invite_code']

                # Update stats for the inviter if found
                if inviter_id:
                    await self.db.update_invite_stats(guild.id, inviter_id, left=True)

            # Fetch the leave log channel
            channel_record = await conn.fetchrow("""
                SELECT leave_channel_id FROM log_channels WHERE guild_id = $1
            """, guild.id)

            if channel_record and channel_record['leave_channel_id']:
                leave_channel = guild.get_channel(channel_record['leave_channel_id'])

                if leave_channel:
                    # Fetch inviter details for logs
                    if inviter_id:
                        inviter_user = self.bot.get_user(inviter_id)
                        inviter_mention = (
                            f"{inviter_user.name}#{inviter_user.discriminator}"
                            if inviter_user else f"User ID: {inviter_id}"
                        )

                        # Fetch inviter stats
                        stats = await self.db.get_invite_stats(guild.id, inviter_id)

                        if stats:
                            total_invites = stats.get('total_invites', 0)
                            fake_invites = stats.get('fake_invites', 0)
                            rejoin_count = stats.get('rejoin_count', 0)
                            left_count = stats.get('left_count', 0)

                            # Calculate current valid invites
                            invalid_invites = fake_invites + rejoin_count + left_count
                            current_valid_invites = max(0, total_invites - invalid_invites)
                        else:
                            # If stats are None, set default values
                            total_invites = 0
                            current_valid_invites = 0

                        # Construct the leave message for normal inviter
                        leave_message = (
                            f"✛ `{str(member)}` just left the server :(\n"
                            f"✛ They were invited by `{inviter_mention}` "
                            f"(`{current_valid_invites}` invites)\n"
                            f"✛ `{guild.name}` now has `{guild.member_count}` members"
                        )
                    else:
                        # Construct the leave message for vanity invite
                        leave_message = (
                            f"✛ `{str(member)}` just left the server :(\n"
                            f"✛ They were invited by `vanity` (`{vanity_uses}` uses)\n"
                            f"✛ `{guild.name}` now has `{guild.member_count}` members"
                        )

                    # Send the leave log
                    await leave_channel.send(leave_message)
                else:
                    print(f"[DEBUG] Leave log channel with ID {channel_record['leave_channel_id']} not found.")
            else:
                print(f"[DEBUG] No leave log channel set for guild {guild.name}.")
            
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Handles logging when a member leaves the server."""
        guild = member.guild
        inviter_mention = "unknown"
        vanity_uses = None
        inviter_id = None
        is_vanity = False

        try:
            # Fetch the current vanity invite uses
            vanity_invite = await guild.vanity_invite()
            vanity_uses = vanity_invite.uses if vanity_invite else None
        except Exception as e:
            print(f"[DEBUG] Error fetching vanity invite: {e}")
            vanity_uses = None

        async with self.db.pool.acquire() as conn:
            inviter_record = await conn.fetchrow("""
                SELECT invite_code, inviter_id 
                FROM invited 
                WHERE guild_id = $1 AND user_id = $2
            """, guild.id, member.id)

            if inviter_record:
                inviter_id = inviter_record['inviter_id']
                invite_code = inviter_record['invite_code']
            else:
                is_vanity = True

            # Update stats only if it's not a vanity invite
            if inviter_id and not is_vanity:
                await self.db.update_invite_stats(guild.id, inviter_id, left=True)

            # Fetch the leave log channel
            channel_record = await conn.fetchrow("""
                SELECT leave_channel_id FROM log_channels WHERE guild_id = $1
            """, guild.id)

            if channel_record and channel_record['leave_channel_id']:
                leave_channel = guild.get_channel(channel_record['leave_channel_id'])

                if leave_channel:
                    if is_vanity:
                        # Construct the leave message for vanity invite
                        leave_message = (
                            f"✛ `{str(member)}` just left the server :(\n"
                            f"✛ They were invited by `vanity` (`{vanity_uses}` uses)\n"
                            f"✛ `{guild.name}` now has `{guild.member_count}` members"
                        )
                    else:
                        # Fetch inviter details for logs
                        inviter_user = self.bot.get_user(inviter_id)
                        inviter_mention = (
                            f"{inviter_user.name}#{inviter_user.discriminator}"
                            if inviter_user else f"User ID: {inviter_id}"
                        )

                        # Fetch inviter stats
                        stats = await self.db.get_invite_stats(guild.id, inviter_id)

                        if stats:
                            total_invites = stats.get('total_invites', 0)
                            fake_invites = stats.get('fake_invites', 0)
                            rejoin_count = stats.get('rejoin_count', 0)
                            left_count = stats.get('left_count', 0)

                            # Calculate current valid invites
                            invalid_invites = fake_invites + rejoin_count + left_count
                            current_valid_invites = max(0, total_invites - invalid_invites)
                        else:
                            # If stats are None, set default values
                            total_invites = 0
                            current_valid_invites = 0

                        # Construct the leave message for normal inviter
                        leave_message = (
                            f"✛ `{str(member)}` just left the server :(\n"
                            f"✛ They were invited by `{inviter_mention}` "
                            f"(`{current_valid_invites}` invites)\n"
                            f"✛ `{guild.name}` now has `{guild.member_count}` members"
                        )

                    # Send the leave log
                    await leave_channel.send(leave_message)
                else:
                    print(f"[DEBUG] Leave log channel with ID {channel_record['leave_channel_id']} not found.")
            else:
                print(f"[DEBUG] No leave log channel set for guild {guild.name}.")
            
    
    @commands.command(name="addinvites")
    @commands.has_permissions(manage_guild=True)
    async def add_invites(self, ctx, member: discord.Member, invites: int):
        """
        Adds a specific number of invites to a member's invite stats.
        """
        if invites < 0:
            await ctx.reply("You cannot add a negative number of invites.")
            return

        async with self.db.pool.acquire() as conn:
        # Update or insert invite stats
            await conn.execute("""
                INSERT INTO invite_stats (guild_id, inviter_id, total_invites)
                VALUES ($1, $2, $3)
                ON CONFLICT (guild_id, inviter_id)
                DO UPDATE SET total_invites = invite_stats.total_invites + $3""", ctx.guild.id, member.id, invites)

        await ctx.reply(
            f"Successfully added **{invites} invites** to {member.mention}."
        )

    @commands.command(name="removeinvites")
    @commands.has_permissions(manage_guild=True)
    async def remove_invites(self, ctx, member: discord.Member, invites: int):
        """
        Removes a specific number of invites from a member's invite stats.
        """
        if invites < 0:
            await ctx.reply("You cannot remove a negative number of invites.")
            return
        stats = await self.db.get_invite_stats(ctx.guild.id, member.id)
        total = stats.get('total_invites',0)
        if total < 1:
            return await ctx.reply(f"{member.mention} **Does Not Have Any Invites")
        
        to_remove = total - invites
        async with self.db.pool.acquire() as conn:
            await conn.execute(f"""
                    INSERT INTO invite_stats (guild_id, inviter_id, total_invites)
                    VALUES ($1, $2, 1)
                    ON CONFLICT (guild_id, inviter_id)
                    DO UPDATE SET total_invites = {to_remove}
                """, ctx.guild.id, member.id)
            

        await ctx.reply(
            f"Successfully removed **{invites} invites** from {member.mention}."
        )
   

    @commands.command(aliases=['setjoin'])
    @commands.has_permissions(administrator=True)
    async def setjoinchannel(self, ctx, channel: discord.TextChannel = None):
        # Check if the command author is the server owner
        if ctx.guild.owner.id == ctx.author.id:
            pass
        else:
            # Ensure the author has a higher role than the bot
            if ctx.author.top_role.position <= ctx.guild.me.top_role.position and ctx.author.id not in self.bot.owner_ids:
                em = discord.Embed(
                    description="You must have a higher role than the bot to run this command.",
                    color=0x2f3136
                )
                return await ctx.send(embed=em)

        if channel is None:
            # Fetch the current join channel from the database
            async with self.db.pool.acquire() as conn:
                ab = "SELECT join_channel_id FROM log_channels WHERE guild_id = $1"
                a = await conn.fetchrow(ab,ctx.guild.id)
            if a:
                chnl = a['join_channel_id']
                c = ctx.guild.get_channel(chnl)
                if c:
                    await ctx.reply(f"**Current Join Channel is {c.mention}**")
                else:
                    await ctx.reply("Join Channel is set in the database but the channel no longer exists.")
            else:
                await ctx.reply("Join Channel is not set up.")
        else:
            # Insert or update the join channel in the database
            await self.db.insert_or_update_join(ctx.guild.id, channel.id)
            em = discord.Embed(
                title="**Join Channel Setup**",
                description=f"**Successfully set {channel.mention} as the Join Channel.**",
                color=0x2f3136
            )
            await ctx.reply(embed=em)

    @commands.command(aliases=['setleave'])
    @commands.has_permissions(administrator=True)
    async def setleavelog(self, ctx, channel: discord.TextChannel = None):
        """Command to set the leave log channel."""
        if channel is None:
            async with self.db.pool.acquire() as conn:
                record = await conn.fetchrow("""
                    SELECT leave_channel_id FROM log_channels WHERE guild_id = $1
                """, ctx.guild.id)
            if record:
                chnl = ctx.guild.get_channel(record['leave_channel_id'])
                if chnl:
                    await ctx.reply(f"**Current Leave Log Channel is {chnl.mention}**")
                else:
                    await ctx.reply("Leave Log Channel is set in the database but no longer exists.")
            else:
                await ctx.reply("Leave Log Channel is not set up.")
        else:
            async with self.db.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO log_channels (guild_id, leave_channel_id)
                    VALUES ($1, $2)
                    ON CONFLICT (guild_id) DO UPDATE
                    SET leave_channel_id = $2
                """, ctx.guild.id, channel.id)
            await ctx.reply(f"**Successfully set {channel.mention} as the Leave Log Channel.**")

    @commands.command(aliases=['unsetjoin'])
    @commands.has_permissions(administrator=True)
    async def unsetjoinchannel(self, ctx):
        """Command to unset the join log channel."""
        async with self.db.pool.acquire() as conn:
            record = await conn.fetchrow("""
                  SELECT join_channel_id FROM log_channels WHERE guild_id = $1
            """, ctx.guild.id)

            if record and record['join_channel_id']:
                await conn.execute("""
                    UPDATE log_channels
                    SET join_channel_id = NULL
                    WHERE guild_id = $1
                """, ctx.guild.id)
                await ctx.reply("**Join log channel has been successfully unset.**")
            else:
                await ctx.reply("**No join log channel is currently set.**")

    @commands.command(aliases=['unsetleave'])
    @commands.has_permissions(administrator=True)
    async def unsetleavelog(self, ctx):
        """Command to unset the leave log channel."""
        async with self.db.pool.acquire() as conn:
            record = await conn.fetchrow("""
                SELECT leave_channel_id FROM log_channels WHERE guild_id = $1
            """, ctx.guild.id)

            if record and record['leave_channel_id']:
                await conn.execute("""
                    UPDATE log_channels
                    SET leave_channel_id = NULL
                    WHERE guild_id = $1
                """, ctx.guild.id)
                await ctx.reply("**Leave log channel has been successfully unset.**")
            else:
                await ctx.reply("**No leave log channel is currently set.**")


    @commands.command(aliases=["lb", "inviteslb"])
    async def leaderboard(self, ctx):
        """Display the invite leaderboard with button pagination."""
        async with self.db.pool.acquire() as conn:
            query = """
                SELECT inviter_id, total_invites, left_count, fake_invites, rejoin_count
                FROM invite_stats
                WHERE guild_id = $1
                ORDER BY total_invites DESC
            """
            records = await conn.fetch(query, ctx.guild.id)

        if not records:
            return await ctx.send("No invite data available for this server.")

        leaderboard_data = []
        for record in records:
            member = ctx.guild.get_member(record['inviter_id']) or "Unknown Member"
            member_name = member.mention if isinstance(member, discord.Member) else member
            total_invites = record.get('total_invites', 0)
            fake_invites = record.get('fake_invites', 0)
            rejoin_count = record.get('rejoin_count', 0)
            left_count = record.get('left_count', 0)

            # Calculate current valid invites
            invalid_invites = fake_invites + rejoin_count + left_count
            current = max(0, total_invites - invalid_invites)
            leaderboard_data.append((
                member_name,
                current,
                record['total_invites'],
                record['left_count'],
                record['fake_invites'],
                record['rejoin_count']
            ))

        view = InviteLeaderboardView(leaderboard_data)
        await view.start(ctx)

    @commands.command(aliases=['reset'])
    @commands.has_permissions(administrator=True)
    async def reset_invites(self, ctx, member: discord.Member = None):
        """Reset invites for a specific member or all members."""
        if member:
            message = f"Are you sure you want to reset invites for {member.display_name}?"
        else:
            message = "Are you sure you want to reset invites for all server members?"

        # Send the confirmation prompt with buttons
        view = InviteResetView(ctx, member=member)
        msg = await ctx.send(message, view=view)
        await view.wait()

        if view.response is None:
            await ctx.send("No response received. Reset canceled.")
            return

        if view.response:
            if member:
                # Reset invites for the specific member
                async with self.db.pool.acquire() as conn:
                    await conn.execute("""
                        DELETE FROM invite_stats
                        WHERE guild_id = $1 AND inviter_id = $2
                    """, ctx.guild.id, member.id)
                await msg.edit(content=f"Successfully reset invites for {member.display_name}.",view=None)
            else:
                # Reset invites for all members in the guild
                async with self.db.pool.acquire() as conn:
                    await conn.execute("""
                        DELETE FROM invite_stats
                        WHERE guild_id = $1
                    """, ctx.guild.id)
                await msg.edit(content="Successfully reset invites for all members in the server.",view=None)
        else:
            await ctx.send("Reset canceled.")


    @commands.command(aliases=["i"])
    async def invites(self, ctx, member: discord.Member = None):
        """Check invite stats for a user."""
        member = member or ctx.author
        stats = await self.db.get_invite_stats(ctx.guild.id, member.id)

        # Check if stats are None
        if stats is None:
            embed = discord.Embed(
                title="**Invite Log**",
                description=f"No invite data found for {member.display_name}.",
                color=0x2f3136
            )
            embed.add_field(name="**Joins**", value=0, inline=True)
            embed.add_field(name="**Fake**", value=0, inline=True)
            embed.add_field(name="**Rejoins**", value=0, inline=True)
            embed.add_field(name="**Left**", value=0, inline=True)
            await ctx.reply(embed=embed)
            return

        # Default values for missing stats
        total_invites = stats.get('total_invites', 0)
        fake_invites = stats.get('fake_invites', 0)
        rejoin_count = stats.get('rejoin_count', 0)
        left_count = stats.get('left_count', 0)

        # Calculate current valid invites
        invalid_invites = fake_invites + rejoin_count + left_count
        current = max(0, total_invites - invalid_invites)

        # Create and send the embed
        embed = discord.Embed(
            title="**Invite Log**",
            description=f"**{member.display_name} has {current} valid invites**",
            color=0x2f3136
        )
        embed.add_field(name="**Joins**", value=total_invites if total_invites > 0 else 0, inline=True)
        embed.add_field(name="**Fake**", value=fake_invites if fake_invites > 0 else 0, inline=True)
        embed.add_field(name="**Rejoins**", value=rejoin_count if rejoin_count > 0 else 0, inline=True)
        embed.add_field(name="**Left**", value=left_count if left_count > 0 else 0, inline=True)
    
        await ctx.reply(embed=embed)



    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Handles the bot being added to a new guild."""
        await self.cache_invites(guild)

async def setup(bot):
    await bot.add_cog(InviteTracker(bot))
