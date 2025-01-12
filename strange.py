import discord
import os 
import asyncpg 
import traceback,sys
from discord.ext import commands
import os
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
import datetime
import json
from typing import (TYPE_CHECKING, Any, Callable, Coroutine, Dict, List,Optional, Tuple, Type, Union,cast)


import re


import asyncio


import logging
import jishaku

logging.basicConfig(

    level=logging.INFO,

    format='%(asctime)s [%(levelname)s] %(message)s',

    datefmt='%Y-%m-%d %H:%M:%S')

logger = logging.getLogger()
#async def add_count(ctx, user, guild, cmd_name):
   # user_columns = database.fetchone("*", "count", "xd", 1)
   # if user_columns is None:
     #   c = {}
     #   c[user.id] = 1
     #   cc = {}
     #   cc[guild.id] = 1
    #    ccc = {}
    #    ccc[cmd_name] = 1
    #    database.insert("count", "xd, 'user_count', 'guild_count', 'cmd_count'", (1, f"{c}", f"{cc}", f"{ccc}",))
  #  else:
   #     c = literal_eval(user_columns['user_count'])
   #     if user.id in c:
    #        c[user.id] = c[user.id] + 1
     #   else:
      #      c[user.id] = 1
    #    c = {k: v for k, v in reversed(sorted(c.items(), key=lambda item: item[1]))}
     #   database.update("count", 'user_count', f"{c}", "xd", 1)
     #   cc = literal_eval(user_columns['guild_count'])
    #    if guild.id in cc:
     #       cc[guild.id] = cc[guild.id] + 1
    #    else:
    #        cc[guild.id] = 1
   #     cc = {k: v for k, v in reversed(sorted(cc.items(), key=lambda item: item[1]))}
     #   database.update("count", 'guild_count', f"{cc}", "xd", 1)
    #    ccc = literal_eval(user_columns['cmd_count'])
     #   if cmd_name in ccc:
    #        ccc[cmd_name] = ccc[cmd_name] + 1
    #    else:
    #        ccc[cmd_name] = 1
    #    ccc = {k: v for k, v in reversed(sorted(ccc.items(), key=lambda item: item[1]))}
    #    database.update("count", 'cmd_count', f"{ccc}", "xd", 1)

async def get_pre1(bot, ctx):
    if ctx.guild is None:
        return commands.when_mentioned_or("+")(bot, ctx)  # Return prefix for DMs

    # Get guild-specific prefix from cache
    db = cache.cache.cache.prefixes.get(str(ctx.guild.id), '+')  # Default to '+' if no prefix found
    prefix = db

    try:
        # Check user-specific prefix in cache
        if str(ctx.author.id) in cache.cache.cache.noprefix:
            res1 = cache.cache.cache.noprefix[str(ctx.author.id)]
            if res1 and "main" in res1 and res1["main"] == 1:
                return commands.when_mentioned_or("")(bot, ctx)  # Empty prefix if user has no prefix
    except Exception as e:
        logger.error(f"Error in file {__file__}: {e}, {traceback.format_exc()}")

    # Default to the guild's prefix
    return commands.when_mentioned_or(prefix)(bot, ctx)
  
    
async def get_pre(bot, ctx):
    if ctx.guild is None:
        return commands.when_mentioned_or(f"+")(bot, ctx)
    db = Cache.pref.get(str(ctx.guild.id))    
 
    if db:
        prefix = db
    else:
        prefix = '+'
    try:
        res1 = Cache.noprefix.get(str(ctx.author.id))
        
        if res1 is not None:
           
            if res1["main"] == 1:
                return commands.when_mentioned_or(f"{prefix}", "")(bot, ctx)
    except Exception as e:
        logger.error(f"Error in file {__file__}: {traceback.format_exc()}")
    return commands.when_mentioned_or(prefix)(bot,ctx)

intents = discord.Intents.all()
a = [991889829774241793,1062994575058276373,224611733032009729,724533169964974112]


        
class Bot(commands.AutoShardedBot):
    def __init__(self, get_pre, intents) -> None:
        super().__init__(command_prefix ="!", case_insensitive=True,strip_after_prefix=True,shard_count=2,intents=intents,allowed_mentions=discord.AllowedMentions(
                everyone=False, replied_user=False, roles=False
            ))
    

    async def setup_hook(self):
          
        self.db = await asyncpg.create_pool(
            database="soward",
            user="prince024",
            password="shaizan24",
            host="localhost"
        )
   
        initial_extensions = ['jishaku']

        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                initial_extensions.append("cogs." + filename[:-3])

        for extension in initial_extensions:
            await self.load_extension(extension)
      
        await self.tree.sync()
        


bot = Bot(get_pre, intents)

bot.owner_ids = 1068967045263261746
bot.remove_command("help")


    

@bot.event
async def on_ready():
    i = [1068967045263261746]
    bot.owner_ids = discord.utils.get(bot.users, id=i)
    await bot.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.listening, name=f"!help | Watching {len(bot.guilds)}"))


#@bot.event
async def on_message(message: discord.Message) -> None:
    await bot.wait_until_ready()

    # Handle DM messages
    if isinstance(message.channel, discord.DMChannel):
        if message.author.id != bot.user.id:
            webhook = discord.SyncWebhook.from_url(botinfo.webhook_dm_logs)
            avatar_url = message.author.avatar.url if message.author.avatar else None
            webhook.send(
                content=message.content,
                username=f"{str(message.author)} | DM Logs",
                avatar_url=avatar_url,
            )
        return

    # Check bot permissions
    if not (
        message.guild.me.guild_permissions.read_messages
        and message.guild.me.guild_permissions.read_message_history
        and message.guild.me.guild_permissions.view_channel
        and message.guild.me.guild_permissions.send_messages
    ):
        return

    ctx = await bot.get_context(message)

    # Mention prefix handler
    if re.fullmatch(rf"<@!?{bot.user.id}>", message.content) and not ctx.author.bot:
        prefix = Cache.pref.get(str(message.guild.id), "+")
        emb = discord.Embed(
            description=(f"Hey {message.author.mention}, my prefix is `{prefix}`\n"
                         f"To view all my modules, use `{prefix}help` or </help:1063005466914979900>.\n"
                         f"For module-related help, use `{prefix}help <module name>` "
                         f"or </help:1063005466914979900> `<module name>`."),
            color=botinfo.root_color,
        )
        page = discord.ui.View()
        page.add_item(discord.ui.Button(label="Invite me", url=f"https://discord.com/api/oauth2/authorize?client_id={botinfo.bot_id}&permissions=8&scope=bot"))
        page.add_item(discord.ui.Button(label="Support Server", url=f"{botinfo.support_server}"))
        await ctx.reply(embed=emb, mention_author=False, view=page, delete_after=10)
        return

    # Ignore settings
    ig_db = Cache.ignore.get(str(ctx.guild.id))  # Fetch the ignored settings for the current guild
    if ig_db is None:  # If no data found, initialize default values
        ig_db = {}

    # Safely attempt to load data from ig_db with default fallbacks if data is None
    userss_data_str = ig_db.get("userss", "{}")  # Ensure default to "{}" if None
    if userss_data_str is None:
        userss_data_str = "{}"  # Force default if None
    try:
        userss_data = json.loads(userss_data_str)  # Safely load JSON data
    except json.JSONDecodeError as e:
        logger.error(f"Malformed 'userss' data: {e}")
        userss_data = {}  # Default to empty dictionary if JSON is invalid

    channel_data_str = ig_db.get("channel", "[]")  # Ensure default to "[]" if None
    if channel_data_str is None:
        channel_data_str = "[]"
    try:
        channel_data = json.loads(channel_data_str)  # Safely load JSON data
    except json.JSONDecodeError as e:
        logger.error(f"Malformed 'channel' data: {e}")
        channel_data = []  # Default to empty list if JSON is invalid

    role_data_str = ig_db.get("role", "[]")  # Ensure default to "[]" if None
    if role_data_str is None:
        role_data_str = "[]"
    try:
        role_data = json.loads(role_data_str)  # Safely load JSON data
    except json.JSONDecodeError as e:
        logger.error(f"Malformed 'role' data: {e}")
        role_data = []  # Default to empty list if JSON is invalid

    if message.author.id in userss_data:
        return

    c_channel = await by_channel(ctx, message.author, message.channel)
    if message.channel.id in channel_data and not c_channel:
        return
    member = message.author
    if isinstance(member,discord.Member):
        if any(role.id in role_data for role in member.roles):
            c_role = await by_role(ctx, member, message.channel)
            if not c_role:
                return

    # Ignore bot's own messages
    if message.author.id == bot.user.id:
        return

    # Process commands
    try:
        if bot.mesaagecreate:
            return await bot.process_commands(message)
    except:
        pass
    s_db = Cache.setup.get(str(message.guild.id))
    if s_db is None or message.channel.id != s_db["channel_id"]:
        return await bot.process_commands(message)

    # Prefix handling for music-only channel
    pre = await get_prefix(message)
    check = False
    content = message.content
    prefix = None
    for k in pre:
        if content.startswith(k):
            content = content[len(k):].strip()
            check = True
            prefix = k
            break

    command_name = content.split(" ", 1)[0]
    cmd = bot.get_command(command_name)
    if cmd is None:
        # Default to "play" command
        message.content = f"<@{bot.user.id}> play {message.content}" if not check else f"<@{bot.user.id}> {content}"
    else:
        if cmd.cog_name != "music":
            return await ctx.send(
                f"{message.author.mention} You can only use commands from the music module in this channel.",
                delete_after=15,
            )
        message.content = prefix + content if check else f"<@{bot.user.id}> {message.content}"

    # Process the updated message
    await bot.process_commands(message)

    # Delete processed messages and clean up channel history
    try:
        await message.delete()
    except discord.Forbidden:
        pass

    await asyncio.sleep(60)
    async for msg in message.channel.history(limit=100):
        if msg.id == s_db["msg_id"] or msg.components:
            continue
        try:
            await msg.delete()
        except discord.Forbidden:
            pass


    
    
            

#bot.event
async def process_commands(message: discord.Message) -> None:
    if message.author.bot:
        return

    s_id = message.guild.shard_id
    sh = bot.get_shard(s_id)
    if sh.is_ws_ratelimited():
        webhook = discord.SyncWebhook.from_url(botinfo.webhook_ratelimit_logs)
        webhook.send(
            "The bot is being ratelimited",
            username=f"{str(bot.user)} | Ratelimit Logs",
            avatar_url=bot.user.avatar.url,
        )

    ctx = await bot.get_context(message)

    ig_db = Cache.ignore.get(str(message.guild.id))
    if ig_db is None:
        return await bot.invoke(ctx)
    cmd_restriction = ig_db.get('cmd','[]')
    if cmd_restriction is not None:
        cmd_restrictions = json.loads(cmd_restriction)
    else:
        cmd_restrictions = []
    module_restrictions = ig_db.get('module','[]')
    if module_restrictions is not None:
        module_restrictions = json.loads(module_restrictions)
    else:
        module_restrictions = []
    if ctx.command is None:
       
        return await bot.invoke(ctx)

    # Check bypass permissions
    cmd_qualified_name = ctx.command.qualified_name if ctx.command else None
    cog_name = ctx.command.cog_name.lower() if ctx.command and ctx.command.cog_name else None

    is_bypass_user = await by_cmd(ctx, message.author, cmd_qualified_name)
    is_bypass_module = await by_module(ctx, message.author, cog_name)
    is_bypass_channel = await by_channel(ctx, message.author, ctx.channel)

    if is_bypass_user or is_bypass_module or is_bypass_channel:
        return await bot.invoke(ctx)

    # Music module setup restrictions
    if ctx.command and ctx.command.cog_name and ctx.command.cog_name.lower() == "music":
        music_allowed_commands = ["247", "msetup"]  
        cmd_name = ctx.command.qualified_name

        s_db = Cache.setup.get(str(message.guild.id))
        channel_check = False

        if s_db:
            music_channel = bot.get_channel(s_db['channel_id'])
            if music_channel and ctx.channel.id == s_db['channel_id']:
                channel_check = True

        if cmd_name not in music_allowed_commands:
            if not channel_check:
                if s_db and music_channel:
                    return await ctx.reply(
                        f"You can only use music commands in {music_channel.mention}.", delete_after=5
                    )
          #      else:
         #           return await ctx.reply(
      #                  "Music commands are restricted to the music setup channel.", delete_after=5
       #             )

    # Command restrictions
    if ctx.command and ctx.command.qualified_name in cmd_restrictions:
        is_cmd_allowed = await by_cmd(ctx, message.author, ctx.command.qualified_name)
        if not is_cmd_allowed:
            return await ctx.reply(
                f"The `{ctx.command.qualified_name}` command is disabled for this server.", delete_after=5
            )

    # Module restrictions
    if ctx.command and ctx.command.cog_name and ctx.command.cog_name.lower() in module_restrictions:
        is_module_allowed = await by_module(ctx, message.author, ctx.command.cog_name.lower())
        if not is_module_allowed:
            return await ctx.reply(
                f"The `{ctx.command.cog_name.capitalize()}` module is disabled for this server.", delete_after=5
            )

    

    # Invoke the command if no restrictions apply
    await bot.invoke(ctx)
     
            
   
        
                


async def process_commandssss(message: discord.Message) -> None:
    if message.author.bot:
        return

    
    s_id = message.guild.shard_id
    sh = bot.get_shard(s_id)
    if sh.is_ws_ratelimited():
        webhook = discord.SyncWebhook.from_url(botinfo.webhook_ratelimit_logs)
        webhook.send("The bot is being ratelimited", username=f"{str(bot.user)} | Ratelimit Logs", avatar_url=bot.user.avatar.url)


    ctx = await bot.get_context(message)

  
    ig_db = Cache.ignore.get(str(message.guild.id))

    if ig_db is None: 
        return await bot.invoke(ctx)
    
  
    cmd_restrictions = json.loads(ig_db.get('cmd', '[]'))
    module_restrictions = json.loads(ig_db.get('module', '[]'))
    if ctx.command is None:
        return await bot.invoke(ctx)
    
    is_bypass_user = await by_cmd(ctx, message.author, ctx.command.qualified_name)
    is_bypass_module = await by_module(ctx, message.author, ctx.command.cog_name.lower())
    is_bypass_channel = await by_channel(ctx, message.author, ctx.channel)

   
    if is_bypass_user or is_bypass_module or is_bypass_channel:
        return await bot.invoke(ctx)

    # Music module setup restrictions
    if ctx.command and ctx.command.cog_name.lower() == "music":
        music_allowed_commands = ["247", "msetup"]  
        cmd_name = ctx.command.qualified_name

      
        s_db = Cache.setup.get(str(message.guild.id))
        channel_check = False

        if s_db:
            music_channel = bot.get_channel(s_db['channel_id'])
            if music_channel and ctx.channel.id == s_db['channel_id']:
                channel_check = True

        
        if cmd_name not in music_allowed_commands:
            if not channel_check:
                if s_db and music_channel:
                    return await ctx.reply(f"You can only use music commands in {music_channel.mention}.", delete_after=5)
                else:
                    return await ctx.reply("Music commands are restricted to the music setup channel.", delete_after=5)

    
    if ctx.command and ctx.command.qualified_name in cmd_restrictions:
        is_cmd_allowed = await by_cmd(ctx, message.author, ctx.command.qualified_name)
        if not is_cmd_allowed:
            return await ctx.reply(f"The `{ctx.command.qualified_name}` command is disabled for this server.", delete_after=5)

  
    if ctx.command and ctx.command.cog_name.lower() in module_restrictions:
        is_module_allowed = await by_module(ctx, message.author, ctx.command.cog_name.lower())
        if not is_module_allowed:
            return await ctx.reply(f"The `{ctx.command.cog_name.capitalize()}` module is disabled for this server.", delete_after=5)

   
    logger.info(
        f"Command restrictions (cmd): {cmd_restrictions}, Module restrictions (module): {module_restrictions}"
    )

    # Invoke command if no restrictions apply
    await bot.invoke(ctx)
  

        
    
    
      
                
#@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    await bot.wait_until_ready()
    if after.content == before.content:
        return
    message = after
    ctx = await bot.get_context(message)
    query = "SELECT * FROM ignore WHERE guild_id = %s"
    values = (message.guild.id)
    db = await create_connection()
    
    ig_db= await db.fetchone(query,values)
   
    if ig_db is not None:
        xd = literal_eval(ig_db['userss'])
        if message.author.id in xd:
            return
        xdd = literal_eval(ig_db['channel'])
        c_channel = await by_channel(ctx, message.author, message.channel)
        if message.channel.id in xdd and not c_channel:
            return
        xddd = literal_eval(ig_db['role'])
        oke = discord.utils.get(message.guild.members, id=message.author.id)
        if oke is not None:
          for i in message.author.roles:
            if i.id in xddd:
                c_role = await by_role(ctx, message.author, i)
                if not c_role:
                    return
    await bot.process_commands(after)      





    
                    
                

    
           
    

     
            
       

         
    
       

    
async def main():
    try:
        
        
      

        tasks = []

        async def start_bot():
            try:
                await bot.start("MTI5MTc2NzQ0MDUzNTA2NDY2Ng.GtmEyq.tHJN1urfGFZsfBfocnyb2BTfigAY0lK9uqKHJQ", reconnect=True)
            except KeyboardInterrupt:
                logger.error("Bot has been stopped")
            except discord.RateLimited as e:
                logger.error(f"Bot is rate limited. Retrying in {e.retry_after} seconds")
            except discord.LoginFailure as e:
                logger.error(f"Login failed. {e}")
            except discord.HTTPException as e:
                retry_after = e.response.headers.get('Retry-After', 'N/A')
                logger.error(f"Bot is rate limited. Retrying in {retry_after} seconds")
                if retry_after == 'N/A':
                    return
                # Log detailed information about the request that caused the rate limit
                logger.error(f"Rate limit details: {e.response.status} {e.response.reason}")
                logger.error(f"Response headers: {e.response.headers}")
                logger.error(f"Response text: {e.status} {e.text}")
                await asyncio.sleep(int(retry_after))
     
        try:
            tasks.append(asyncio.create_task(start_bot()))
        except Exception as e:
            logger.error(f"Error in file {__file__}: {traceback.format_exc()}")
        await asyncio.gather(*tasks)
    except Exception as e:
        logger.error(f"Error in file {__file__}: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(main())
             
    
    
        
            
       
           
                



