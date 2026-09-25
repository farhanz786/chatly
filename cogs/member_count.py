import discord
from discord.ext import commands


GUILD_ID = 1467231978813128834
CHANNEL_ID = 1503429466674827407


class MemberCount(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def update_member_count(self, guild: discord.Guild):
        channel = guild.get_channel(CHANNEL_ID)

        if channel is None:
            print(f"Member count channel not found: {CHANNEL_ID}")
            return

        new_name = f"🧩︰{guild.member_count}"

        if channel.name != new_name:
            await channel.edit(
                name=new_name,
                reason="Update Chatly member count"
            )

            print(f"Member count updated: {guild.member_count}")

    @commands.Cog.listener()
    async def on_ready(self):
        guild = self.bot.get_guild(GUILD_ID)

        if guild:
            await self.update_member_count(guild)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id == GUILD_ID:
            await self.update_member_count(member.guild)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if member.guild.id == GUILD_ID:
            await self.update_member_count(member.guild)


async def setup(bot):
    await bot.add_cog(MemberCount(bot))