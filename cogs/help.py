import discord
from discord import app_commands
from discord.ext import commands
import datetime
import discord
from discord import app_commands
from discord.ext import commands

import random
from typing import Optional, List
from discord.ui import *

class BasicView(discord.ui.View):
    def __init__(self, ctx: commands.Context,bot):
        super().__init__()
        self.ctx = ctx
        self.bot = bot
    async def interaction_check(self, interaction: discord.Interaction):

        if interaction.user.id != self.ctx.author.id and interaction.user.id not in  [991889829774241793]:

            await interaction.response.send_message(f"Um, Looks like you are not the author of the command...", ephemeral=True)

            return False

        return True

class HelpDropdown(discord.ui.Select):
    def __init__(self,bot):
        self.bot = bot
        options = [
            discord.SelectOption(label="Invite Tracker", description="Show You Invite Tracker Commands"),
            discord.SelectOption(label="VcRole", description="Show You VcRole Commands")
            
                                 
        ]
        super().__init__(placeholder="Choose a category...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "Invite Tracker":
            a = self.bot.get_cog("InviteTracker")
            c = [c.name for c in a.walk_commands()]
            prince = self.bot.get_user(991889829774241793)
            embed = discord.Embed(title=f" Invite Tracker Commands..", description=",".join(c),color=0x2f3136)
            embed.set_footer(text="Made By Prince?",icon_url=prince.display_avatar)

            await interaction.response.edit_message(embed=embed)
        elif self.values[0] == "VcRole":
            a = self.bot.get_cog("VCRoleManager")
            c = [c.name for c in a.walk_commands()]
            prince = self.bot.get_user(991889829774241793)
            embed = discord.Embed(title=f"VcRole Commands..", description=",".join(c),color=0x2f3136)
            embed.set_footer(text="Made By Prince?",icon_url=prince.display_avatar)
            await interaction.response.edit_message(embed=embed)
        
class HelpView(BasicView):
    def __init__(self,ctx,bot):
        super().__init__(ctx,bot)
        self.bot = bot 
        self.ctx = ctx
        self.add_item(HelpDropdown(bot))
        self.add_item(discord.ui.Button(label="Invite me", url=f"https://discord.com/api/oauth2/authorize?client_id=1291767440535064666&&permissions=8&scope=bot"))
        self.add_item(discord.ui.Button(label="Support Server", url=f"https://discord.gg/soward"))

    
    
    

class help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(description="Get Help with the bot's commands or modules")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def help(self, ctx: commands.Context, command: Optional[str]):
        
            xd = self.bot.get_user(991889829774241793)
            anay = str(xd)
            pfp = xd.display_avatar.url
            em = discord.Embed(title="Soward Beta Version",description="**Welcome to Soward's beta version! This version is designed to help us identify and fix bugs.\n\nModules\nhelp\ninvite tracker\ninvc\n\n\nBug Report\nIf you encounter any bugs, please join our support server to report them. We'll be happy to assist you!\n\n\nNote\nThis is a beta version, so some commands or features may not work as expected. Your feedback will help us improve Soward.**")
            em.set_footer(text="Made By Prince?")
            em.set_thumbnail(url=self.bot.user.avatar)
            page = HelpView(ctx,self.bot)
            await ctx.send(embed=em,view=page)

    
    @commands.command(aliases=['inv'])
    async def invite(self, ctx):
        view = discord.ui.View()
        a = Button(label="invite",style=discord.ButtonStyle.link,url=f"https://discord.com/api/oauth2/authorize?client_id={self.bot.user.id}&&permissions=8&scope=bot")
        view.add_item(a)
        em = discord.Embed(description=f"> Click Below Button To Invite Me In Your Server", color=0x2f3136)
        await ctx.reply(embed=em,view=view)

    @commands.command()
    async def support(self, ctx):
        em = discord.Embed(description=f"> [Click To Invite {self.bot.user.name} in Your Server](https://discord.com/api/oauth2/authorize?client_id={self.bot.user.id}&&permissions=8&scope=bot)\n> [Click To Join Support Server]({botinfo.support_server})", color=0x2f3136)
        await ctx.reply(embed=em, mention_author=False)
        
   
        
async def setup(bot):
    await bot.add_cog(help(bot))
