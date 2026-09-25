import asyncio
import json
import os
import random
import re
import time
from pathlib import Path
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands


# ============================================================
# CHATLY VERIFICATION
# ============================================================

DATA_FILE = "levelling_data.json"

OWNER_ID = 937242913535033404

VERIFIED_ROLE_ID = 1503429447322435725
SUS_ROLE_ID = 1503429236239634656

DEFAULT_VERIFICATION_CHANNEL_ID = 1503429521087398019
SUS_VERIFICATION_CHANNEL_ID = 1503429624200429678
VERIFICATION_LOG_CHANNEL_ID = 1552331237257904289

PROFILE_CHANNEL_ID = 1503429516943425607
MODERATOR_APPLICATION_CHANNEL_ID = 1503429512078164142

CAPTCHA_COOLDOWN = 5 * 60
MAX_CONSECUTIVE_FAILURES = 3
MAX_AUTO_REJOINS = 3
CHALLENGE_COUNT = 2
CHALLENGE_DIFFICULTY = "Medium"

CHATLY_GREEN = 0x52FB18

# Verification emojis from Chatly's emoji source of truth.
TICK = "<:tick:1550538067570335764>"
LOCK = "<:lock:1551275905253511238>"
INFO = "<:info:1550551426269319168>"
LINK = "<:link:1550536411189616670>"
EXCLAMATION = "<:exclaimation:1550544117249998878>"
SKULL = "<:skull:1550551579751485642>"
USER = "<:user:1550286898126262312>"
MOD = "<:mod:1550551457109901435>"
CAMERA = "<:camera:1550917998024458352>"
APPS = "<:apps:1550920307596853340>"

VERIFIED_FEATURES = {
    "Profiles": {
        "emoji": USER,
        "description": "Unlock the ability to create and customize your Chatly profile.",
        "channel_id": PROFILE_CHANNEL_ID,
    },
    "Moderator Applications": {
        "emoji": MOD,
        "description": "Unlock access to Chatly's moderator application system.",
        "channel_id": MODERATOR_APPLICATION_CHANNEL_ID,
    },
    "Media Access": {
        "emoji": CAMERA,
        "description": "Unlock the ability to post in designated media channels.",
        "channel_id": None,
    },
    "More Features": {
        "emoji": APPS,
        "description": "Unlock additional verified-only features as they become available.",
        "channel_id": None,
    },
}

# Only these three challenge families exist.
CHALLENGE_TYPES = (
    "visual",
    "interaction",
    "pattern",
)

SYMBOLS = [
    "◆", "●", "▲", "■", "★", "⬟", "⬢", "✦", "✚", "✿", "☀", "☾"
]

BUTTON_EMOJIS = [
    "🔹", "🔸", "🔺", "🔻", "⭐", "🌙", "☀️", "🍀", "🟣", "🟠", "🔵", "🟢"
]


def load_data() -> dict:
    if not os.path.exists(DATA_FILE):
        return {}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_data(data: dict) -> None:
    temp_file = DATA_FILE + ".tmp"
    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
    os.replace(temp_file, DATA_FILE)


def verification_store(data: dict) -> dict:
    store = data.setdefault("__verification__", {})
    if not isinstance(store, dict):
        data["__verification__"] = {}
        store = data["__verification__"]
    return store


def get_member_record(data: dict, guild_id: int, user_id: int) -> dict:
    store = verification_store(data)
    guild_data = store.setdefault(str(guild_id), {})
    record = guild_data.setdefault(
        str(user_id),
        {
            "verified": False,
            "verified_at": None,
            "verification_attempts": 0,
            "last_attempt": 0,
            "sus_triggered": False,
            "rejoin_count": 0,
        },
    )

    # Backward-compatible defaults.
    record.setdefault("verified", False)
    record.setdefault("verified_at", None)
    record.setdefault("verification_attempts", 0)
    record.setdefault("last_attempt", 0)
    record.setdefault("sus_triggered", False)
    record.setdefault("rejoin_count", 0)
    record.setdefault("pre_sus_roles", [])
    return record


def format_remaining(seconds: float) -> str:
    seconds = max(0, int(seconds))
    minutes, seconds = divmod(seconds, 60)
    if minutes:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


def clean_text(value: str, limit: int = 500) -> str:
    value = str(value).strip()
    value = re.sub(r"@everyone|@here", "@\u200beveryone", value, flags=re.IGNORECASE)
    return value[:limit]


def role_is_staff(role: discord.Role) -> bool:
    return role.name.lower() in {
        "sr mod",
        "admin",
        "manager",
        "executive",
        "co owner",
        "owner",
    }


def is_sr_mod_or_higher(member: discord.Member) -> bool:
    if member.id == OWNER_ID:
        return True
    return any(role_is_staff(role) for role in member.roles)


class VerificationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data = load_data()
        self.data_lock = asyncio.Lock()
        self.active_attempts: dict[tuple[int, int], "VerificationAttempt"] = {}
        self.restored_rejoin_users: set[tuple[int, int]] = set()
        self.persistent_views_registered = False

    # ========================================================
    # STORAGE
    # ========================================================

    async def save(self) -> None:
        async with self.data_lock:
            save_data(self.data)

    def record(self, guild_id: int, user_id: int) -> dict:
        return get_member_record(self.data, guild_id, user_id)

    # ========================================================
    # EVENTS / STARTUP
    # ========================================================

    async def cog_load(self):
        self.bot.loop.create_task(self._register_persistent_views())

    async def _register_persistent_views(self):
        await self.bot.wait_until_ready()
        if self.persistent_views_registered:
            return

        self.bot.add_view(VerificationPanelView(self))
        self.bot.add_view(SUSRecoveryPanelView(self))
        self.persistent_views_registered = True

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return

        async with self.data_lock:
            record = self.record(member.guild.id, member.id)
            verified = bool(record.get("verified", False))
            rejoin_count = int(record.get("rejoin_count", 0))

            if not verified or rejoin_count >= MAX_AUTO_REJOINS:
                save_data(self.data)
                return

            record["rejoin_count"] = rejoin_count + 1
            save_data(self.data)

        role = member.guild.get_role(VERIFIED_ROLE_ID)
        if role and role not in member.roles:
            try:
                await member.add_roles(role, reason="Chatly verification: automatic verified-status restoration")
            except discord.HTTPException:
                pass

        await self.log_event(
            member.guild,
            "Rejoin restoration",
            member=member,
            status=f"Restored verified status ({rejoin_count + 1}/{MAX_AUTO_REJOINS})",
        )

    # ========================================================
    # SETUP PANEL
    # ========================================================

    @app_commands.command(
        name="setup-verification",
        description="Post or replace the Chatly verification panel.",
    )
    async def setup_verification(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return

        if not is_sr_mod_or_higher(interaction.user):
            await interaction.response.send_message(
                f"{LOCK} You need **Sr Mod or higher** to use this command.",
                ephemeral=True,
            )
            return

        channel = interaction.channel
        if channel is None or not hasattr(channel, "history"):
            await interaction.response.send_message(
                "This command must be used in a text channel.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        # Remove previous verification panels in this channel.
        try:
            async for message in channel.history(limit=100):
                if message.author.id != self.bot.user.id:
                    continue
                if not message.embeds:
                    continue
                if message.embeds[0].title in {"Chatly Verification", "Chatly Verification Recovery"}:
                    try:
                        await message.delete()
                    except discord.HTTPException:
                        pass
        except discord.HTTPException:
            pass

        thumbnail_path = Path(__file__).resolve().parent.parent / "assets" / "verification_thumbnail.png"
        thumbnail_file = discord.File(thumbnail_path, filename="verification_thumbnail.png")
        embed = self.create_verification_embed()
        embed.set_thumbnail(url="attachment://verification_thumbnail.png")

        message = await channel.send(
            embed=embed,
            file=thumbnail_file,
            view=VerificationPanelView(self),
        )

        await interaction.followup.send(
            f"{TICK} Verification panel posted: {message.jump_url}",
            ephemeral=True,
        )

    def create_verification_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"{TICK} Chatly Verification",
            description="Verify to unlock Chatly's verified-only features.",
            color=CHATLY_GREEN,
        )

        feature_lines = []
        for name, feature in VERIFIED_FEATURES.items():
            feature_lines.append(
                f"{feature['emoji']} **{name}** — {feature['description']}"
            )

        embed.add_field(
            name="Verified Features",
            value="\n".join(feature_lines),
            inline=False,
        )

        embed.add_field(
            name="Fast & Simple",
            value=(
                "Complete a quick two-step verification to confirm you're a genuine "
                "member and help keep Chatly safe from automated and abusive activity."
            ),
            inline=False,
        )

        return embed

    # ========================================================
    # VERIFICATION ACCESS
    # ========================================================

    def has_verified_access(self, member: discord.Member) -> bool:
        return any(role.id == VERIFIED_ROLE_ID for role in member.roles)

    async def ensure_verified_role(self, member: discord.Member) -> bool:
        role = member.guild.get_role(VERIFIED_ROLE_ID)
        if role is None:
            return False

        if role not in member.roles:
            try:
                await member.add_roles(role, reason="Chatly verification successful")
            except discord.HTTPException:
                return False
        return True

    async def remove_verified_role(self, member: discord.Member) -> None:
        role = member.guild.get_role(VERIFIED_ROLE_ID)
        if role and role in member.roles:
            try:
                await member.remove_roles(role, reason="Chatly verification state removed")
            except discord.HTTPException:
                pass

    async def make_verified_role_mentionable(self, guild: discord.Guild) -> None:
        role = guild.get_role(VERIFIED_ROLE_ID)
        if role is None or not guild.me:
            return
        if role.mentionable:
            return
        try:
            await role.edit(mentionable=True, reason="Chatly verification setup")
        except discord.HTTPException:
            pass

    # ========================================================
    # ATTEMPTS
    # ========================================================

    async def begin_attempt(self, interaction: discord.Interaction) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                "Verification can only be used inside Chatly.", ephemeral=True
            )
            return

        member = interaction.user
        guild = interaction.guild
        record = self.record(guild.id, member.id)

        if self.has_verified_access(member) or record.get("verified"):
            await interaction.response.send_message(
                "You're already verified.", ephemeral=True
            )
            return

        now = time.time()
        last_attempt = float(record.get("last_attempt", 0))
        remaining = CAPTCHA_COOLDOWN - (now - last_attempt)
        if remaining > 0:
            await interaction.response.send_message(
                f"{EXCLAMATION} Please wait **{format_remaining(remaining)}** before trying again.",
                ephemeral=True,
            )
            return

        key = (guild.id, member.id)
        if key in self.active_attempts:
            await interaction.response.send_message(
                f"{EXCLAMATION} You already have an active verification attempt.",
                ephemeral=True,
            )
            return

        challenge_types = random.sample(list(CHALLENGE_TYPES), CHALLENGE_COUNT)
        challenges = [self.build_challenge(kind) for kind in challenge_types]

        attempt = VerificationAttempt(
            cog=self,
            guild_id=guild.id,
            user_id=member.id,
            challenges=challenges,
        )
        self.active_attempts[key] = attempt

        record["verification_attempts"] = int(record.get("verification_attempts", 0)) + 1
        record["last_attempt"] = now
        await self.save()

        await self.log_event(
            guild,
            "Verification attempt",
            member=member,
            status=f"Started; challenge 1/{CHALLENGE_COUNT}",
            challenge_types=challenge_types,
            attempt_number=record["verification_attempts"],
            sus=bool(record.get("sus_triggered")),
        )

        await interaction.response.send_message(
            embed=attempt.current_embed(),
            view=attempt.current_view(),
            ephemeral=True,
        )

    def build_challenge(self, kind: str) -> dict:
        if kind == "visual":
            target = random.choice(SYMBOLS)
            options = random.sample([s for s in SYMBOLS if s != target], 5)
            options.append(target)
            random.shuffle(options)
            return {
                "type": kind,
                "target": target,
                "options": options,
            }

        if kind == "interaction":
            target = random.choice(BUTTON_EMOJIS)
            options = random.sample([x for x in BUTTON_EMOJIS if x != target], 5)
            options.append(target)
            random.shuffle(options)
            return {
                "type": kind,
                "target": target,
                "options": options,
            }

        # Pattern / Logic: choose a sequence with a single missing value.
        pattern_family = random.choice(("increment", "alternate", "step"))
        if pattern_family == "increment":
            start = random.randint(1, 8)
            step = random.randint(2, 5)
            sequence = [start + i * step for i in range(4)]
        elif pattern_family == "alternate":
            a = random.randint(1, 8)
            b = random.randint(10, 18)
            sequence = [a, b, a + 2, b + 2]
        else:
            start = random.randint(2, 7)
            sequence = [start, start + 1, start + 3, start + 6]

        missing_index = random.choice((1, 2))
        answer = sequence[missing_index]
        shown = [str(value) if i != missing_index else "?" for i, value in enumerate(sequence)]

        choices = {answer}
        while len(choices) < 6:
            candidate = answer + random.choice((-5, -3, -2, -1, 1, 2, 3, 4, 5))
            if candidate > 0:
                choices.add(candidate)

        options = list(choices)
        random.shuffle(options)
        return {
            "type": kind,
            "sequence": shown,
            "answer": answer,
            "options": options,
        }

    async def handle_challenge_answer(
        self,
        interaction: discord.Interaction,
        attempt: "VerificationAttempt",
        answer: str,
    ) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return

        key = (interaction.guild.id, interaction.user.id)
        if self.active_attempts.get(key) is not attempt:
            await interaction.response.send_message(
                "This verification attempt is no longer active.", ephemeral=True
            )
            return

        challenge = attempt.current_challenge
        correct = str(challenge.get("answer", challenge.get("target"))) == str(answer)

        if not correct:
            await self.fail_attempt(interaction, attempt)
            return

        attempt.index += 1

        if attempt.index >= CHALLENGE_COUNT:
            await self.complete_verification(interaction, attempt)
            return

        await interaction.response.edit_message(
            embed=attempt.current_embed(),
            view=attempt.current_view(),
        )

        await self.log_event(
            interaction.guild,
            "Challenge passed",
            member=interaction.user,
            status=f"Challenge {attempt.index}/{CHALLENGE_COUNT} completed",
            challenge_types=[c["type"] for c in attempt.challenges],
        )

    async def fail_attempt(
        self,
        interaction: discord.Interaction,
        attempt: "VerificationAttempt",
    ) -> None:
        guild = interaction.guild
        member = interaction.user
        if not guild or not isinstance(member, discord.Member):
            return

        key = (guild.id, member.id)
        self.active_attempts.pop(key, None)

        record = self.record(guild.id, member.id)
        failures = int(record.get("verification_attempts", 0))

        # verification_attempts is total attempts, so keep consecutive failures separately
        record["consecutive_failures"] = int(record.get("consecutive_failures", 0)) + 1
        record["last_attempt"] = time.time()
        consecutive = record["consecutive_failures"]

        sus_triggered = False
        if consecutive >= MAX_CONSECUTIVE_FAILURES:
            sus_triggered = True
            await self.trigger_sus(member, record)

        await self.save()

        await self.log_event(
            guild,
            "Verification failed",
            member=member,
            status=(
                "SUS triggered after 3 consecutive failures"
                if sus_triggered
                else f"Failed; cooldown {format_remaining(CAPTCHA_COOLDOWN)}"
            ),
            challenge_types=[c["type"] for c in attempt.challenges],
            attempt_number=failures,
            sus=sus_triggered,
        )

        if sus_triggered:
            message = (
                f"{SKULL} Verification failed **3 times consecutively**.\n\n"
                "Your account has been placed in restricted SUS status. "
                "You can retry verification in the locked recovery channel after the cooldown."
            )
        else:
            message = (
                f"{EXCLAMATION} Verification failed.\n\n"
                f"One incorrect challenge fails the entire attempt. Please wait **{format_remaining(CAPTCHA_COOLDOWN)}** before trying again."
            )

        await interaction.response.edit_message(
            content=message,
            embed=None,
            view=None,
        )

    async def complete_verification(
        self,
        interaction: discord.Interaction,
        attempt: "VerificationAttempt",
    ) -> None:
        guild = interaction.guild
        member = interaction.user
        if not guild or not isinstance(member, discord.Member):
            return

        key = (guild.id, member.id)
        self.active_attempts.pop(key, None)

        record = self.record(guild.id, member.id)
        record["verified"] = True
        record["verified_at"] = time.time()
        record["consecutive_failures"] = 0
        record["last_attempt"] = 0
        record["sus_triggered"] = False
        record["rejoin_count"] = 0
        record["pre_sus_roles"] = []

        await self.ensure_verified_role(member)
        await self.remove_sus_and_restore_roles(member, record)
        await self.save()

        await self.log_event(
            guild,
            "Verification success",
            member=member,
            status="Verified; verified-only features unlocked",
            challenge_types=[c["type"] for c in attempt.challenges],
            sus=False,
        )

        await interaction.response.edit_message(
            content=f"{TICK} **Verification successful!** Your verified-only features are now unlocked.",
            embed=None,
            view=None,
        )

    # ========================================================
    # SUS
    # ========================================================

    async def trigger_sus(self, member: discord.Member, record: dict) -> None:
        sus_role = member.guild.get_role(SUS_ROLE_ID)
        if sus_role is None:
            return

        # Preserve manageable non-default roles so recovery can restore normal access.
        saved_roles = []
        for role in member.roles:
            if role.is_default() or role.id == SUS_ROLE_ID:
                continue
            if member.guild.me and role >= member.guild.me.top_role:
                continue
            saved_roles.append(role.id)

        record["pre_sus_roles"] = saved_roles
        record["sus_triggered"] = True
        record["verified"] = False

        await self.remove_verified_role(member)
        try:
            await member.add_roles(sus_role, reason="Chatly verification: 3 consecutive failures")
        except discord.HTTPException:
            pass

    async def remove_sus_and_restore_roles(self, member: discord.Member, record: dict) -> None:
        sus_role = member.guild.get_role(SUS_ROLE_ID)
        if sus_role and sus_role in member.roles:
            try:
                await member.remove_roles(sus_role, reason="Chatly verification recovery successful")
            except discord.HTTPException:
                pass

        for role_id in record.get("pre_sus_roles", []):
            role = member.guild.get_role(int(role_id))
            if role is None or role.is_default():
                continue
            if member.guild.me and role >= member.guild.me.top_role:
                continue
            if role not in member.roles:
                try:
                    await member.add_roles(role, reason="Chatly verification recovery: restore previous role")
                except discord.HTTPException:
                    pass

    def create_sus_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"{SKULL} Verification Recovery",
            description=(
                "Your account is currently restricted because verification failed "
                "three consecutive times."
            ),
            color=CHATLY_GREEN,
        )
        embed.add_field(
            name="What happens now?",
            value=(
                "After the cooldown expires, use **Verify Me** below to complete "
                "the same two-step randomized verification."
            ),
            inline=False,
        )
        embed.add_field(
            name="Need help?",
            value="Use **View Case** or **View Evidence** for the member-facing information available to you.",
            inline=False,
        )
        return embed

    @app_commands.command(
        name="setup-sus-verification",
        description="Post or replace the SUS verification recovery panel.",
    )
    async def setup_sus_verification(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("Server only.", ephemeral=True)
            return
        if not is_sr_mod_or_higher(interaction.user):
            await interaction.response.send_message(
                f"{LOCK} You need **Sr Mod or higher** to use this command.",
                ephemeral=True,
            )
            return

        channel = interaction.guild.get_channel(SUS_VERIFICATION_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "The configured SUS CAPTCHA channel could not be found.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        try:
            async for message in channel.history(limit=100):
                if message.author.id != self.bot.user.id or not message.embeds:
                    continue
                if message.embeds[0].title == "Chatly Verification Recovery":
                    try:
                        await message.delete()
                    except discord.HTTPException:
                        pass
        except discord.HTTPException:
            pass

        message = await channel.send(
            embed=self.create_sus_embed(),
            view=SUSRecoveryPanelView(self),
        )
        await interaction.followup.send(
            f"{TICK} SUS recovery panel posted: {message.jump_url}", ephemeral=True
        )

    async def begin_sus_recovery(self, interaction: discord.Interaction) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return

        member = interaction.user
        record = self.record(interaction.guild.id, member.id)

        sus_role = interaction.guild.get_role(SUS_ROLE_ID)
        is_sus = sus_role in member.roles if sus_role else bool(record.get("sus_triggered"))

        if not is_sus:
            if self.has_verified_access(member) or record.get("verified"):
                await interaction.response.send_message("You're already verified.", ephemeral=True)
            else:
                await interaction.response.send_message(
                    "You are not currently in SUS recovery status. Use the main verification panel.",
                    ephemeral=True,
                )
            return

        now = time.time()
        remaining = CAPTCHA_COOLDOWN - (now - float(record.get("last_attempt", 0)))
        if remaining > 0:
            await interaction.response.send_message(
                f"{EXCLAMATION} Please wait **{format_remaining(remaining)}** before retrying.",
                ephemeral=True,
            )
            return

        key = (interaction.guild.id, member.id)
        if key in self.active_attempts:
            await interaction.response.send_message(
                f"{EXCLAMATION} You already have an active verification attempt.", ephemeral=True
            )
            return

        challenge_types = random.sample(list(CHALLENGE_TYPES), CHALLENGE_COUNT)
        challenges = [self.build_challenge(kind) for kind in challenge_types]
        attempt = VerificationAttempt(
            cog=self,
            guild_id=interaction.guild.id,
            user_id=member.id,
            challenges=challenges,
            sus_recovery=True,
        )
        self.active_attempts[key] = attempt

        record["verification_attempts"] = int(record.get("verification_attempts", 0)) + 1
        record["last_attempt"] = now
        await self.save()

        await self.log_event(
            interaction.guild,
            "SUS recovery attempt",
            member=member,
            status="Started; challenge 1/2",
            challenge_types=challenge_types,
            attempt_number=record["verification_attempts"],
            sus=True,
        )

        await interaction.response.send_message(
            embed=attempt.current_embed(),
            view=attempt.current_view(),
            ephemeral=True,
        )

    # ========================================================
    # MANUAL STAFF CONTROLS
    # ========================================================

    @app_commands.command(
        name="verify",
        description="Manually verify a member for recovery or exceptional cases.",
    )
    @app_commands.describe(
        member="Member to verify.",
        reason="Required reason for manual verification.",
        evidence="Optional Discord attachment supporting the action.",
        evidence_link="Optional Discord message or evidence link.",
    )
    async def manual_verify(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str,
        evidence: Optional[discord.Attachment] = None,
        evidence_link: Optional[str] = None,
    ):
        await self.manual_action_confirmation(
            interaction, member, "verify", reason, evidence, evidence_link
        )

    @app_commands.command(
        name="unverify",
        description="Manually remove verification for recovery or exceptional cases.",
    )
    @app_commands.describe(
        member="Member to unverify.",
        reason="Required reason for manual unverification.",
        evidence="Optional Discord attachment supporting the action.",
        evidence_link="Optional Discord message or evidence link.",
    )
    async def manual_unverify(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str,
        evidence: Optional[discord.Attachment] = None,
        evidence_link: Optional[str] = None,
    ):
        await self.manual_action_confirmation(
            interaction, member, "unverify", reason, evidence, evidence_link
        )

    async def manual_action_confirmation(
        self,
        interaction: discord.Interaction,
        target: discord.Member,
        action: str,
        reason: str,
        evidence: Optional[discord.Attachment],
        evidence_link: Optional[str],
    ):
        if not interaction.guild:
            await interaction.response.send_message("Server only.", ephemeral=True)
            return

        if not is_sr_mod_or_higher(interaction.user):
            await interaction.response.send_message(
                f"{LOCK} Manual verification controls are **Sr Mod+ only**.",
                ephemeral=True,
            )
            return

        reason = clean_text(reason, 1000)
        if not reason:
            await interaction.response.send_message(
                f"{EXCLAMATION} A reason is required.", ephemeral=True
            )
            return

        evidence_text = self.format_evidence(evidence, evidence_link)
        view = ManualConfirmationView(
            cog=self,
            target=target,
            action=action,
            reason=reason,
            evidence=evidence_text,
            actor_id=interaction.user.id,
        )

        await interaction.response.send_message(
            embed=view.confirmation_embed(),
            view=view,
            ephemeral=True,
        )

    def format_evidence(
        self,
        evidence: Optional[discord.Attachment],
        evidence_link: Optional[str],
    ) -> Optional[str]:
        parts = []
        if evidence:
            parts.append(evidence.url)
        if evidence_link:
            parts.append(clean_text(evidence_link, 1000))
        return " | ".join(parts) if parts else None

    async def execute_manual_action(
        self,
        interaction: discord.Interaction,
        target: discord.Member,
        action: str,
        reason: str,
        evidence: Optional[str],
    ) -> None:
        record = self.record(interaction.guild.id, target.id)

        if action == "verify":
            record["verified"] = True
            record["verified_at"] = time.time()
            record["consecutive_failures"] = 0
            record["sus_triggered"] = False
            record["last_attempt"] = 0
            record["rejoin_count"] = 0
            await self.ensure_verified_role(target)
            await self.remove_sus_and_restore_roles(target, record)
            status = "Manual verification completed"
        else:
            record["verified"] = False
            record["verified_at"] = None
            record["sus_triggered"] = False
            record["consecutive_failures"] = 0
            await self.remove_verified_role(target)
            status = "Manual unverification completed"

        await self.save()

        await self.log_event(
            interaction.guild,
            "Manual verification control",
            member=target,
            status=status,
            staff=interaction.user,
            reason=reason,
            evidence=evidence,
        )

        await interaction.response.edit_message(
            content=f"{TICK} {status} for {target.mention}.",
            embed=None,
            view=None,
        )

    # ========================================================
    # MEMBER-FACING CASE / EVIDENCE
    # ========================================================

    async def send_member_case(self, interaction: discord.Interaction) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return

        record = self.record(interaction.guild.id, interaction.user.id)
        if not record.get("sus_triggered"):
            await interaction.response.send_message(
                "No active verification restriction case is available.", ephemeral=True
            )
            return

        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"{INFO} Your Verification Case",
                description=(
                    "Your current restriction was triggered after three consecutive "
                    "failed verification attempts. You can retry through the SUS recovery panel "
                    "after the cooldown."
                ),
                color=CHATLY_GREEN,
            ),
            ephemeral=True,
        )

    async def send_member_evidence(self, interaction: discord.Interaction) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return

        record = self.record(interaction.guild.id, interaction.user.id)
        if not record.get("sus_triggered"):
            await interaction.response.send_message(
                "No member-facing evidence summary is available.", ephemeral=True
            )
            return

        # Never expose staff-only Case Files or raw internal evidence from this panel.
        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"{INFO} Evidence Information",
                description=(
                    "Any staff evidence associated with your restriction is kept in Chatly's "
                    "private moderation records. This panel does not expose staff-only case files "
                    "or another member's private information."
                ),
                color=CHATLY_GREEN,
            ),
            ephemeral=True,
        )

    # ========================================================
    # LOGGING
    # ========================================================

    async def log_event(
        self,
        guild: discord.Guild,
        event: str,
        *,
        member: Optional[discord.Member] = None,
        staff: Optional[discord.Member] = None,
        status: Optional[str] = None,
        challenge_types: Optional[list[str]] = None,
        attempt_number: Optional[int] = None,
        sus: Optional[bool] = None,
        reason: Optional[str] = None,
        evidence: Optional[str] = None,
    ) -> None:
        channel = guild.get_channel(VERIFICATION_LOG_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            return

        embed = discord.Embed(
            title=f"{INFO} Verification Log — {event}",
            color=CHATLY_GREEN,
            timestamp=discord.utils.utcnow(),
        )

        if member:
            embed.add_field(
                name="Member",
                value=f"{member.mention} (`{member.id}`)",
                inline=False,
            )
        if staff:
            embed.add_field(
                name="Staff",
                value=f"{staff.mention} (`{staff.id}`)",
                inline=False,
            )
        if status:
            embed.add_field(name="Status", value=clean_text(status), inline=False)
        if challenge_types:
            embed.add_field(
                name="Challenge Types",
                value=", ".join(challenge_types),
                inline=True,
            )
        if attempt_number is not None:
            embed.add_field(name="Attempt", value=str(attempt_number), inline=True)
        if sus is not None:
            embed.add_field(name="SUS", value="Yes" if sus else "No", inline=True)
        if reason:
            embed.add_field(name="Reason", value=clean_text(reason, 1000), inline=False)
        if evidence:
            embed.add_field(name="Evidence Reference", value=clean_text(evidence, 1000), inline=False)

        # Answers are deliberately never included.
        try:
            await channel.send(embed=embed)
        except discord.HTTPException:
            pass

    # ========================================================
    # DATA PRIVACY
    # ========================================================

    async def delete_member_data(self, user_id: int) -> None:
        changed = False
        store = verification_store(self.data)
        for guild_id, guild_data in list(store.items()):
            if not isinstance(guild_data, dict):
                continue
            if str(user_id) in guild_data:
                del guild_data[str(user_id)]
                changed = True
            if not guild_data:
                store.pop(guild_id, None)

        self.active_attempts = {
            key: value for key, value in self.active_attempts.items() if key[1] != user_id
        }

        if changed:
            await self.save()


class VerificationAttempt:
    def __init__(
        self,
        cog: VerificationCog,
        guild_id: int,
        user_id: int,
        challenges: list[dict],
        sus_recovery: bool = False,
    ):
        self.cog = cog
        self.guild_id = guild_id
        self.user_id = user_id
        self.challenges = challenges
        self.index = 0
        self.sus_recovery = sus_recovery

    @property
    def current_challenge(self) -> dict:
        return self.challenges[self.index]

    @property
    def current_type(self) -> str:
        return self.current_challenge["type"]

    def current_embed(self) -> discord.Embed:
        challenge = self.current_challenge
        embed = discord.Embed(
            title=f"{LOCK} Verification · {self.index + 1}/{CHALLENGE_COUNT}",
            description="Complete the challenge below to continue.",
            color=CHATLY_GREEN,
        )

        if challenge["type"] == "visual":
            embed.add_field(
                name="Visual Selection",
                value=f"Select the symbol that matches **{challenge['target']}**.",
                inline=False,
            )
        elif challenge["type"] == "interaction":
            embed.add_field(
                name="Interaction Challenge",
                value=f"Click the button showing **{challenge['target']}**.",
                inline=False,
            )
        else:
            embed.add_field(
                name="Pattern / Logic",
                value=(
                    f"Find the missing value in **{'  →  '.join(challenge['sequence'])}**."
                ),
                inline=False,
            )

        embed.set_footer(text=f"Difficulty: {CHALLENGE_DIFFICULTY} • One wrong answer fails the attempt")
        return embed

    def current_view(self) -> discord.ui.View:
        if self.current_type == "visual":
            return VisualChallengeView(self)
        if self.current_type == "interaction":
            return InteractionChallengeView(self)
        return PatternChallengeView(self)


class VerificationPanelView(discord.ui.View):
    def __init__(self, cog: VerificationCog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="Verify Me",
        style=discord.ButtonStyle.secondary,
        custom_id="chatly_verification_verify",
        emoji=TICK,
    )
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.begin_attempt(interaction)


class SUSRecoveryPanelView(discord.ui.View):
    def __init__(self, cog: VerificationCog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="Verify Me",
        style=discord.ButtonStyle.secondary,
        custom_id="chatly_sus_verify",
        emoji=TICK,
    )
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.begin_sus_recovery(interaction)

    @discord.ui.button(
        label="View Case",
        style=discord.ButtonStyle.secondary,
        custom_id="chatly_sus_case",
        emoji="📄",
    )
    async def case_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.send_member_case(interaction)

    @discord.ui.button(
        label="View Evidence",
        style=discord.ButtonStyle.secondary,
        custom_id="chatly_sus_evidence",
        emoji="🔎",
    )
    async def evidence_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.send_member_evidence(interaction)


class ChallengeButton(discord.ui.Button):
    def __init__(self, attempt: VerificationAttempt, label: str, answer: str, row: int = 0):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.secondary,
            custom_id=f"chatly_verify_{attempt.guild_id}_{attempt.user_id}_{random.randint(100000, 999999)}",
            row=row,
        )
        self.attempt = attempt
        self.answer = answer

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.attempt.user_id:
            await interaction.response.send_message(
                "This verification belongs to another member.", ephemeral=True
            )
            return
        await self.attempt.cog.handle_challenge_answer(interaction, self.attempt, self.answer)


class VisualChallengeView(discord.ui.View):
    def __init__(self, attempt: VerificationAttempt):
        super().__init__(timeout=300)
        challenge = attempt.current_challenge
        for index, symbol in enumerate(challenge["options"]):
            self.add_item(ChallengeButton(attempt, symbol, symbol, row=index // 3))


class InteractionChallengeView(discord.ui.View):
    def __init__(self, attempt: VerificationAttempt):
        super().__init__(timeout=300)
        challenge = attempt.current_challenge
        for index, symbol in enumerate(challenge["options"]):
            self.add_item(ChallengeButton(attempt, symbol, symbol, row=index // 3))


class PatternChallengeView(discord.ui.View):
    def __init__(self, attempt: VerificationAttempt):
        super().__init__(timeout=300)
        challenge = attempt.current_challenge
        for index, value in enumerate(challenge["options"]):
            self.add_item(ChallengeButton(attempt, str(value), str(value), row=index // 3))


class ManualConfirmationView(discord.ui.View):
    def __init__(
        self,
        cog: VerificationCog,
        target: discord.Member,
        action: str,
        reason: str,
        evidence: Optional[str],
        actor_id: int,
    ):
        super().__init__(timeout=120)
        self.cog = cog
        self.target = target
        self.action = action
        self.reason = reason
        self.evidence = evidence
        self.actor_id = actor_id

    def confirmation_embed(self) -> discord.Embed:
        action_name = "Manual Verification" if self.action == "verify" else "Manual Unverification"
        embed = discord.Embed(
            title=f"{EXCLAMATION} Confirm {action_name}",
            description=(
                "Manual verification controls are for bugs, corrupted state, or exceptional recovery. "
                "They are **not the normal verification path**."
            ),
            color=CHATLY_GREEN,
        )
        embed.add_field(name="Member", value=f"{self.target.mention} (`{self.target.id}`)", inline=False)
        embed.add_field(name="Reason", value=self.reason, inline=False)
        embed.add_field(name="Evidence", value=self.evidence or "None provided", inline=False)
        embed.set_footer(text="Confirm only if this manual action is necessary.")
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.actor_id:
            await interaction.response.send_message("Only the staff member who started this action can confirm it.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.secondary, emoji=TICK)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.execute_manual_action(
            interaction,
            self.target,
            self.action,
            self.reason,
            self.evidence,
        )
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="<:close:1550533713526399126>")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="Manual verification action cancelled.",
            embed=None,
            view=None,
        )
        self.stop()


async def setup(bot: commands.Bot):
    cog = VerificationCog(bot)
    await bot.add_cog(cog)
