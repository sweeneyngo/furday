import time
import discord
import os
import timeago as timesince
import json
import random

from datetime import datetime
from discord.ext import commands, tasks
from utils import default


class Daily(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = default.config()
        self.tdaily = self.tdaily.start()
        self.activated = False
        self.channel = -1

    def cog_unload(self):
        self.tdaily.cancel()

    @tasks.loop(minutes=30)
    async def tdaily(self):

        if not self.activated or self.channel < 0:
            return

        channel = self.bot.get_channel(self.channel)
        
        res = default.search()
        if res != None:
            res, img, profile, time = res
        

        user = self.bot.get_user(self.config['id'])
        embedColour = random.randint(0, self.config['white'])
        # if hasattr(ctx, "guild") and ctx.guild is not None:
        #     embedColour = ctx.me.top_role.colour

        embed = default.send_embed(embedColour, user, res, img, profile, time)
        await channel.send(embed=embed)

    # @tdaily.before_loop
    # async def before_tdaily():
    #     await self.bot.wait_until_ready()

    @commands.command(alias=["on"])
    async def activate(self, ctx):

        """ Activate the background retrieval. """
        await ctx.message.delete()
        self.activated = True
        self.channel = ctx.channel.id
        await ctx.send(f'Activated in {ctx.channel}!')

    @commands.command(alias=["off"])
    async def deactivate(self, ctx):

        """ Deactivate the background retrieval. """
        self.activated = False

    @commands.command(alias=["day"])
    async def daily(self, ctx):

        """ Retrieve a daily furry. """
        await ctx.message.delete()

        res = default.search()
        if res != None:
            res, img, profile, time = res
        
        embedColour = random.randint(0, self.config['white'])

        embed = default.send_embed(embedColour, ctx.bot.user, res, img, profile, time)
        await ctx.send(embed=embed)



def setup(bot):
    bot.add_cog(Daily(bot))
