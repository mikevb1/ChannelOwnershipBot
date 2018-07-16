from discord.ext import commands
import discord

NUM_OF_OWNERS = 2

def in_voice():
    return commands.check(lambda ctx: ctx.author.voice is not None)

class NotChannelOwner(Exception):
    def __init__(self, *args, channel_info, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel_info = channel_info

class ChannelInfo:
    def __init__(self, channel):
        self.channel = channel
        self.initial_limit = channel.user_limit
        self.heirarchy = channel.members.copy()

    async def lock(self, limit):
        await self.channel.edit(user_limit=limit, reason="Locking")

    async def unlock(self):
        await self.channel.edit(user_limit=self.initial_limit, reason="Unlocking")

class ChannelOwnership:
    def __init__(self, bot):
        self.bot = bot
        self.channel_info = {}

    def get_info_and_check_owner(self, ctx):
        channel_info = self.channel_info[ctx.guild][ctx.author.voice.channel]
        if ctx.author not in channel_info.heirarchy[:NUM_OF_OWNERS]:
            raise NotChannelOwner(channel_info)
        return channel_info
    
    @commands.command(usage='[new_limit]')
    @in_voice()
    async def lock(self, ctx, new_limit: int = -1):
        """As a channel "owner," lock the room so no more users may join.
        
        !lock   -> sets user limit to current number of users in the channel
        !lock 5 -> sets user limit to 5
        """
        channel_info = self.get_info_and_check_owner(ctx)
        if new_limit == -1:
            new_limit = len(channel_info.channel.members)
        if new_limit < 2:
            new_limit = 2
        elif new_limit > channel_info.initial_limit:
            new_limit = channel_info.initial_limit
        if new_limit == channel_info.channel.user_limit:
            await ctx.send(f"{channel_info.channel} already has a user limit of {new_limit}.")
            return
        await channel_info.lock(new_limit)
        await ctx.send(f"{channel_info.channel} now has a user limit of {new_limit}.")

    @commands.command()
    @in_voice()
    async def unlock(self, ctx):
        """As a channel "owner," unlock the room to its original user limit."""
        channel_info = self.get_info_and_check_owner(ctx)
        if channel_info.channel.user_limit == channel_info.initial_limit:
            await ctx.send(f"{channel_info.channel} is already unlocked.")
            return
        await channel_info.unlock()
        await ctx.send(f"{channel_info.channel} has been unlocked.")

    @commands.commands()
    @in_voice()
    async def checkowner(self, ctx):
        """Check who the owners of your room are."""
        ci = self.channel_info[ctx.guild][ctx.author.voice.channel]
        if len(ci.heirarchy > 1):
            await ctx.send(f"The owners of {ci.channel} are {ci.heirarchy[0]} and {ci.heirarchy[1]}.")
        else:
            await ctx.send(f"You are the owner of {ci.channel}.")

    @commands.command(aliases=['shutdown', 'kill'])
    @commands.is_owner()
    async def close(self, ctx):
        """As the bot owner, close the bot gracefully so it unlocks all channels."""
        self.bot._process = False
        for guild, channels in self.channel_info.items():
            for channel, info in channels.items():
                if channel.user_limit != info.initial_limit:
                    await info.unlock()
        await ctx.send('Shutting down.')
        raise KeyboardInterrupt

    async def on_command_error(self, ctx, exc):
        if isinstance(exc, commands.CheckFailure):
            await ctx.send("You must be in a voice channel to use this command.")
        elif isinstance(exc, NotChannelOwner):
            ci = exc.channel_info
            await ctx.send(f"You must be an owner of the voice channel. The current owners are {ci.heirarchy[0]} and {ci.heirarchy[1]}.")
        else:
            await ctx.send(exc)

    async def on_voice_state_update(self, member, before, after):
        if before.channel == after.channel:
            return
        if before.channel and before.channel.user_limit > 0:
            self.channel_info[member.guild][before.channel].heirarchy.remove(member)
            if len(before.channel.members) == 0:
                await self.channel_info[member.guild][before.channel].unlock()
        if after.channel and after.channel.user_limit > 0:
            self.channel_info[member.guild][after.channel].heirarchy.append(member)

    async def on_guild_channel_update(self, before, after):
        if not isinstance(before, discord.VoiceChannel):
            return
        if before.user_limit == 0 and after.user_limit > 0:
            self.channel_info[after.guild][after] = ChannelInfo(after)
        elif after.user_limit == 0 and before.user_limit > 0:
            self.channel_info[after.guild].pop(after, None)

    async def on_guild_update(self, before, after):
        if before.afk_channel != after.afk_channel:
            self.channel_info[after].pop(after.afk_channel, None)
            if before.afk_channel is not None and before.afk_channel.user_limit > 0:
                self.channel_info[after][before.afk_channel] = ChannelInfo(before.afk_channel)

    def populate_guild_info(self, guild):
        self.channel_info[guild] = {}
        for vc in guild.voice_channels:
            if vc != guild.afk_channel and vc.user_limit > 0:
                self.channel_info[guild][vc] = ChannelInfo(vc)

    async def on_guild_join(self, guild):
        self.populate_guild_info(guild)

    async def on_guild_remove(self, guild):
        self.channel_info.pop(guild)

    async def on_ready(self):
        for guild in self.bot.guilds:
            self.populate_guild_info(guild)
        self.bot._process = True


def setup(bot):
    bot.add_cog(ChannelOwnership(bot))