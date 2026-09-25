
import json
import os
import time
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands


DATA_FILE = "staff_stats.json"

POINT_VALUES = {
    "claim_ticket": 2,
    "add_member": 2,
    "evidence_ping": 1,
    "staff_note": 1,
    "lock_ticket": 3,
    "unlock_ticket": 3,
    "rename_ticket": 2,
    "transfer_ticket": 3,
    "mark_solved": 5,
    "mark_fixed": 5,
    "close_ticket": 5,

    # Moderation weights:
    "warn": 10,
    "timeout": 8,
    "jail": 6,
    "sus": 4,
    "ban": 2,
}

ACTION_COOLDOWN = 30


class StaffStats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data = self.load_data()

    def load_data(self):
        if not os.path.exists(DATA_FILE):
            return {
                "staff": {},
                "action_history": []
            }

        try:
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, OSError):
            return {
                "staff": {},
                "action_history": []
            }

    def save_data(self):
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(self.data, file, indent=4)

    def record_action(
        self,
        staff_id: int,
        action: str,
        reference: str | None = None,
        points: int | None = None,
    ) -> bool:
        staff_id = str(staff_id)

        if action not in POINT_VALUES and points is None:
            return False

        now = time.time()

        if reference:
            for entry in reversed(self.data["action_history"]):
                if (
                    entry["staff_id"] == staff_id
                    and entry["action"] == action
                    and entry.get("reference") == reference
                    and now - entry["timestamp"] < ACTION_COOLDOWN
                ):
                    return False

        awarded_points = points if points is not None else POINT_VALUES[action]

        if staff_id not in self.data["staff"]:
            self.data["staff"][staff_id] = {
                "points": 0,
                "actions": 0,
                "action_counts": {}
            }

        staff = self.data["staff"][staff_id]

        staff["points"] += awarded_points
        staff["actions"] += 1

        if action not in staff["action_counts"]:
            staff["action_counts"][action] = 0

        staff["action_counts"][action] += 1

        self.data["action_history"].append({
            "staff_id": staff_id,
            "action": action,
            "points": awarded_points,
            "reference": reference,
            "timestamp": now,
            "datetime": datetime.now(timezone.utc).isoformat()
        })

        if len(self.data["action_history"]) > 5000:
            self.data["action_history"] = self.data["action_history"][-5000:]

        self.save_data()
        return True

    def get_stats(self, staff_id: int):
        staff_id = str(staff_id)

        return self.data["staff"].get(
            staff_id,
            {
                "points": 0,
                "actions": 0,
                "action_counts": {}
            }
        )

    @app_commands.command(
        name="staffstats",
        description="View staff statistics and Mod Points."
    )
    async def staffstats(
        self,
        interaction: discord.Interaction,
        member: discord.Member | None = None
    ):
        target = member or interaction.user
        stats = self.get_stats(target.id)

        embed = discord.Embed(
            title="📈 Staff Statistics",
            description=f"Statistics for **{target.display_name}**",
            color=discord.Color.green()
        )

        embed.add_field(
            name="Mod Points",
            value=f"**{stats['points']}**",
            inline=True
        )

        embed.add_field(
            name="Actions",
            value=f"**{stats['actions']}**",
            inline=True
        )

        if stats["action_counts"]:
            actions = sorted(
                stats["action_counts"].items(),
                key=lambda item: item[1],
                reverse=True
            )

            action_text = "\n".join(
                f"`{action}` — {count}"
                for action, count in actions[:10]
            )
        else:
            action_text = "No recorded actions yet."

        embed.add_field(
            name="Action Breakdown",
            value=action_text,
            inline=False
        )

        embed.set_thumbnail(url=target.display_avatar.url)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="staffleaderboard",
        description="View the Staff Mod Points leaderboard."
    )
    async def staffleaderboard(
        self,
        interaction: discord.Interaction
    ):
        if not self.data["staff"]:
            await interaction.response.send_message(
                "📈 No staff statistics have been recorded yet.",
                ephemeral=True
            )
            return

        leaderboard = sorted(
            self.data["staff"].items(),
            key=lambda item: item[1]["points"],
            reverse=True
        )

        lines = []

        for position, (staff_id, stats) in enumerate(
            leaderboard[:10],
            start=1
        ):
            member = interaction.guild.get_member(int(staff_id))

            if member:
                name = member.display_name
            else:
                name = f"User {staff_id}"

            lines.append(
                f"**{position}.** {name} — "
                f"**{stats['points']}** points"
            )

        embed = discord.Embed(
            title="🏆 Staff Stats Leaderboard",
            description="\n".join(lines),
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(StaffStats(bot))
