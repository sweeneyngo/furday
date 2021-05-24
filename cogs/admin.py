import time
import discord
import os
import sys

from discord.ext import commands
from utils import permissions, default


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = default.config()

    @commands.command()
    async def amiadmin(self, ctx):
        if ctx.author.id in self.config["owners"]:
            return await ctx.send(f"Yes, you are an admin! ✅")

        await ctx.send(f"No, fuck off {ctx.author.name}!")

    @commands.command()
    @commands.check(permissions.is_owner)
    async def reload(self, ctx, name: str):
        """ Reloads an extension. """
        try:
            self.bot.reload_extension(f"cogs.{name}")
        except Exception as e:
            return await ctx.send(default.traceback_maker(e))
        await ctx.send(f"Reloaded extension **{name}.py**")

    @commands.command()
    @commands.check(permissions.is_owner)
    async def reloadall(self, ctx):
        """ Reloads all extensions. """
        error_collection = []
        for file in os.listdir("cogs"):
            if file.endswith(".py"):
                name = file[:-3]
                try:
                    self.bot.reload_extension(f"cogs.{name}")
                except Exception as e:
                    error_collection.append(
                        [file, default.traceback_maker(e, advance=False)]
                    )

        if error_collection:
            output = "\n".join([f"**{g[0]}** ```diff\n- {g[1]}```" for g in error_collection])
            return await ctx.send(
                f"Attempted to reload all extensions, was able to reload, "
                f"however the following failed...\n\n{output}"
            )

        await ctx.send("Successfully reloaded all extensions")
        
def setup(bot):
    bot.add_cog(Admin(bot))
