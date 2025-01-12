import asyncpg


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

        # Invite stats table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS  
                invite_stats (
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
                await conn.execute("""
                    UPDATE invite_stats
                    SET fake_invites = fake_invites + 1
                    WHERE guild_id = $1 AND inviter_id = $2
                """, guild_id, inviter_id)
            if rejoin:
                await conn.execute("""
                    UPDATE invite_stats
                    SET rejoin_count = rejoin_count + 1
                    WHERE guild_id = $1 AND inviter_id = $2
                """, guild_id, inviter_id)
            if left:
                await conn.execute("""
                    UPDATE invite_stats
                    SET left_count = left_count + 1
                    WHERE guild_id = $1 AND inviter_id = $2
                """, guild_id, inviter_id)

    async def get_invite_stats(self, guild_id, inviter_id):
        """Get invite stats for a user."""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("""
                SELECT total_invites, fake_invites, rejoin_count
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



