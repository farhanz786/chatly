import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

intents = discord.Intents.default()
intents.members = True
intents.message_content = True


class ChatlyBot(commands.Bot):
    async def setup_hook(self):
        # Load all cogs first
        await self.load_extension("cogs.self_roles")
        await self.load_extension("cogs.member_count")
        await self.load_extension("cogs.data_privacy")
        await self.load_extension("cogs.rules")
        await self.load_extension("cogs.premium")
        await self.load_extension("cogs.ticket")
        await self.load_extension("cogs.staff_stats")
        await self.load_extension("cogs.moderation")
        await self.load_extension("cogs.levelling")
        await self.load_extension("cogs.owner_tools")
        await self.load_extension("cogs.verification")
        await self.load_extension("cogs.staff_applications")

        # Sync commands after all cogs have been loaded
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        synced = await self.tree.sync(guild=guild)

        print(f"Synced {len(synced)} command(s):")
        for command in synced:
            print(f"- /{command.name}")


bot = ChatlyBot(
    command_prefix="!",
    intents=intents
)


@bot.event
async def on_ready():
    print(f"Chatly is online as {bot.user}")
    print(f"Connected to {len(bot.guilds)} server(s)")


@bot.tree.command(
    name="ping",
    description="Check if Chatly is online.",
    guild=discord.Object(id=GUILD_ID)
)
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!")


bot.run(TOKEN)