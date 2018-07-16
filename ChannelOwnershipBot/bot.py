from discord.ext import commands

import config

class Bot(commands.AutoShardedBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._process = False

    async def on_message(self, message):
        if self._process:
            await self.process_commands(message)

bot = Bot(command_prefix=config.prefix, case_insensitive=True)
bot.load_extension('channelownership')

if __name__ == '__main__':
    bot.run(config.token)