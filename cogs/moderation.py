
import asyncio
import io
import json
import os
import re
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands


# ============================================================
# CHATLY MODERATION
# ============================================================
# This cog uses the existing StaffStats cog for Mod Points.
# It does NOT create a second points system.
#
# Commands:
# /warn
# /warnings
# /clearwarnings
# /remove warn
# /timeout
# /untimeout
# /ban
# /unban
# /jail
# /unjail
# /sus
# /purge
# /modhistory
# /nick
# ============================================================


# -------------------------
# SERVER / ROLE CONFIG
# -------------------------

GUILD_ID = 1467231978813128834
OWNER_ID = 937242913535033404

JAIL_ROLE_ID = 1503429235144921208

# Set these after creating the roles/channels.
SUS_ROLE_ID = 1503429236239634656
CAPTCHA_CHANNEL_ID = 1503429624200429678
JAIL_CHANNEL_ID = 1503429621146976319

# Approval requests.
APPROVAL_CHANNEL_ID = 1503429593674289382

# Permanent moderation logs.
# Final moderation/evidence channels.
CASE_FILES_CHANNEL_ID = 1508221549872939070
DENIAL_LOG_CHANNEL_ID = 1551943529528565790
PURGE_LOG_CHANNEL_ID = 1551941521861779567
MOD_LOG_CHANNEL_ID = CASE_FILES_CHANNEL_ID

# Existing Chatly Support ticket system.
WARNING_APPEAL_CATEGORY_ID = 1503429487633764392
TICKET_LOG_CHANNEL_ID = 1525107026642862191
PREMIUM_ROLE_ID = 1503429265415471224
BOT_TESTER_ROLE_ID = 1532125673550774673

# Put your ban-appeal server invite here.
BAN_APPEAL_SERVER_URL = "https://discord.gg/kHvkmW9pMd"

DATA_FILE = Path("moderation_data.json")
EVIDENCE_DIR = Path("moderation_evidence")
EVIDENCE_DIR.mkdir(exist_ok=True)


# -------------------------
# STAFF HIERARCHY
# -------------------------

STAFF_RANKS = {
    "jr mod": 1,
    "jr moderator": 1,
    "junior moderator": 1,
    "mod": 2,
    "moderator": 2,
    "sr mod": 3,
    "sr moderator": 3,
    "senior moderator": 3,
    "admin": 4,
    "administrator": 4,
    "manager": 5,
    "executive": 6,
    "co owner": 7,
    "co-owner": 7,
    "owner": 8,
}


# -------------------------
# COOLDOWNS
# -------------------------
# Cooldowns are consumed ONLY after a successful action.
# They persist in moderation_data.json.

COOLDOWNS = {
    "warn": 5 * 60,        # 5 min / moderator
    "ban": 10 * 60,        # 10 min / server
    "timeout": 3 * 60,     # 3 min / moderator
    "jail": 5 * 60,        # 5 min / moderator
    "sus": 3 * 60,         # 3 min / moderator
    "purge": 10 * 60,      # 10 min / server
}

COOLDOWN_MODERATOR = {
    "warn": True,
    "ban": False,
    "timeout": True,
    "jail": True,
    "sus": True,
    "purge": False,
}

# 1st and 2nd active warning escalation.
WARNING_TIMEOUTS = {
    1: 1 * 60 * 60,      # 1 hour
    2: 6 * 60 * 60,      # 6 hours
}

MAX_TIMEOUT_SECONDS = 28 * 24 * 60 * 60
WARNING_EXPIRY_DAYS = 365
APPROVAL_EXPIRY_SECONDS = 30 * 60
WARNING_APPEAL_ABUSE_MIN = 1 * 60 * 60
WARNING_APPEAL_ABUSE_MAX = 6 * 60 * 60


# -------------------------
# CHATLY CUSTOM EMOJIS
# -------------------------
# Central source of truth: Chatly Notion -> Emoji IDs.
EMOJIS = {
    "bullet": "<:bullet:1550533745424072714>",
    "tick": "<:tick:1550538067570335764>",
    "user": "<:user:1550286898126262312>",
    "link": "<:link:1550536411189616670>",
    "settings": "<:setting:1550551557437661294>",
    "flag": "<:flag:1550551309260693607>",
    "exclaim": "<:exclaimation:1550544117249998878>",
    "chat": "<:chat:1550278354840588319>",
    "poll": "<:poll:1550282798428983307>",
    "refresh": "<:refresh:1550282774714519664>",
    "event": "<:event:1550282823242485820>",
    "gift": "<:gift:1550282853479358464>",
    "mail": "<:message:1550283228072513626>",
    "music": "<:music:1526240888408248422>",
    "tv": "<:tv:1526240870955745300>",
    "game": "<:game:1526238595780968499>",
    "uparrow": "<:uparrow:1550289381347295292>",
    "stars": "<:stars:1550289412624093234>",
    "globe": "<:globe:1550276963728367616>",
    "premium": "<:star:1550289395800743956>",
    "boost": "<:boost:1550552457120190585>",
    "heart": "<:heart:1550551354508836905>",
    "paypal": "<:paypal:1550551525204566057>",
    "upvote": "<:upvote:1550551638387990620>",
    "info": "<:info:1550551426269319168>",
    "help": "<:question:1550551387371343883>",
    "mod": "<:mod:1550551457109901435>",
    "folder": "<:folder:1550538040819318904>",
    "vc": "<:vc:1550285799306698843>",
    "timeout": "<:timeout:1550551605584072855>",
    "mute": "<:mute:1550538092983619737>",
    "headphone": "<:headphone:1550536441879199835>",
    "delete": "<:delete:1550282755017810070>",
    "double_tick": "<:double_tick:1529222183698563174>",
    "colorwheel": "<:colorwheel:1546874046174732350>",
    "edit": "<:edit:1550277007961755658>",
    "close": "<:close:1550533713526399126>",
    "ban": "<:ban:1550542161924325388>",
    "lock": "<:lock:1551275905253511238>",
    "skull": "<:skull:1550551579751485642>",
    "code": "<:code:1550540317298786394>",
    "gaming": "<:gaming:1550285815303770205>",
    "net": "<:net:1551289650969190511>",
    "megaphone": "<:megaphone:1551292666753327135>",
    "conversation": "<:conversation:1550919322476478504>",
    "apps": "<:apps:1550920307596853340>",
    "camera": "<:camera:1550917998024458352>",
    "tools": "<:tools:1550918453995769886>",
    "coins": "<:chatly_coins:1550907460959866991>",
    "emoji": "<:emoji:1550906717473341451>",
    "one": "<:one:1550553897960083456>",
    "two": "<:two:1550553928293154966>",
    "three": "<:three:1550553954730115132>",
    "four": "<:fourchatly:1550553985474109440>",
    "five": "<:five:1550554017590018069>",
    "six": "<:six:1550554046786445333>",
    "seven": "<:seven:1550554075681259590>",
    "eight": "<:eight:1550554103904473118>",
    "nine": "<:nine:1550554132883185664>",
}

def partial_emoji(name: str) -> discord.PartialEmoji:
    return discord.PartialEmoji.from_str(EMOJIS[name])

# -------------------------
# HELPERS
# -------------------------

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def parse_iso(value: str | None):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def normalize_name(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower().strip())


def rank_of(member: discord.Member) -> int:
    if member.id == OWNER_ID:
        return 8

    highest = 0
    for role in member.roles:
        highest = max(highest, STAFF_RANKS.get(normalize_name(role.name), 0))
    return highest


def rank_name(rank: int) -> str:
    return {
        0: "Member",
        1: "Jr Mod",
        2: "Mod",
        3: "Sr Mod",
        4: "Admin",
        5: "Manager",
        6: "Executive",
        7: "Co Owner",
        8: "Owner",
    }.get(rank, "Staff")


def is_staff(member: discord.Member) -> bool:
    return rank_of(member) > 0


def is_higher_than(actor: discord.Member, target: discord.Member) -> bool:
    if target.id == OWNER_ID:
        return False
    if actor.id == OWNER_ID:
        return True
    return rank_of(actor) > rank_of(target)


def unique_id() -> str:
    return uuid.uuid4().hex[:12]

def sanitize_ticket_username(username: str) -> str:
    cleaned = "".join(ch for ch in username if ch.isalnum() or ch in "-_.")
    return (cleaned[:80] or "user")

def is_premium_member(member: discord.Member) -> bool:
    return any(role.id == PREMIUM_ROLE_ID for role in member.roles)

def role_overwrites_for_warning_appeal(
    guild: discord.Guild,
    member: discord.Member,
    bot_member: discord.Member,
) -> dict:
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        member: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            attach_files=True,
            embed_links=True,
        ),
        bot_member: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            attach_files=True,
            embed_links=True,
            manage_channels=True,
            manage_messages=True,
        ),
    }
    for role in guild.roles:
        if role.managed:
            continue
        if STAFF_RANKS.get(normalize_name(role.name), 0) >= 3:
            overwrites[role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True,
            )
    return overwrites

def parse_modified_punishment(value: str) -> tuple[str, int | None] | None:
    normalized = re.sub(r"\s+", " ", value.lower().strip())
    if normalized in {"none", "no punishment", "remove punishment", "no timeout"}:
        return ("none", None)
    if normalized in {"jail", "jailed"}:
        return ("jail", None)
    if normalized.startswith("timeout "):
        normalized = normalized[len("timeout "):].strip()
    seconds = parse_duration(normalized)
    if seconds is not None:
        return ("timeout", seconds)
    return None

async def get_guild_channel(bot: commands.Bot, channel_id: int):
    channel = bot.get_channel(channel_id)
    if channel is not None:
        return channel
    try:
        return await bot.fetch_channel(channel_id)
    except (discord.NotFound, discord.HTTPException):
        return None


def parse_duration(value: str) -> int | None:
    match = re.fullmatch(r"\s*(\d+)\s*([smhdw])\s*", value.lower())
    if not match:
        return None

    number = int(match.group(1))
    unit = match.group(2)
    multiplier = {
        "s": 1,
        "m": 60,
        "h": 60 * 60,
        "d": 24 * 60 * 60,
        "w": 7 * 24 * 60 * 60,
    }[unit]

    seconds = number * multiplier
    if seconds <= 0 or seconds > MAX_TIMEOUT_SECONDS:
        return None
    return seconds


def duration_text(seconds: int) -> str:
    if seconds % (7 * 86400) == 0:
        return f"{seconds // (7 * 86400)}w"
    if seconds % 86400 == 0:
        return f"{seconds // 86400}d"
    if seconds % 3600 == 0:
        return f"{seconds // 3600}h"
    if seconds % 60 == 0:
        return f"{seconds // 60}m"
    return f"{seconds}s"


def load_data():
    if not DATA_FILE.exists():
        return {
            "case_counter": 0,
            "records": [],
            "warnings": {},
            "role_snapshots": {},
            "cooldowns": {},
            "approvals": {},
            "warning_appeals": {},
            "sus_captchas": {},
        }

    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        data.setdefault("case_counter", 0)
        data.setdefault("records", [])
        data.setdefault("warnings", {})
        data.setdefault("role_snapshots", {})
        data.setdefault("cooldowns", {})
        data.setdefault("approvals", {})
        data.setdefault("warning_appeals", {})
        data.setdefault("sus_captchas", {})
        return data
    except (json.JSONDecodeError, OSError):
        return {
            "case_counter": 0,
            "records": [],
            "warnings": {},
            "role_snapshots": {},
            "cooldowns": {},
            "approvals": {},
            "warning_appeals": {},
            "sus_captchas": {},
        }


def save_data(data):
    temp = DATA_FILE.with_suffix(".tmp")
    temp.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    temp.replace(DATA_FILE)


def next_case_id(data) -> str:
    data["case_counter"] += 1
    return f"CASE-{data['case_counter']:06d}"


def get_active_warnings(data, user_id: int):
    now = utc_now()
    active = []

    for warning in data["warnings"].get(str(user_id), []):
        if not warning.get("removed", False):
            expires = parse_iso(warning.get("expires_at"))
            if expires is None or expires > now:
                active.append(warning)

    return active


def get_all_warnings(data, user_id: int):
    return data["warnings"].get(str(user_id), [])


def set_cooldown(data, action: str, actor_id: int, guild_id: int):
    key = action if not COOLDOWN_MODERATOR.get(action, True) else f"{action}:{actor_id}"
    data["cooldowns"][key] = time.time()


def cooldown_remaining(data, action: str, actor_id: int, guild_id: int) -> int:
    if action not in COOLDOWNS:
        return 0

    key = action if not COOLDOWN_MODERATOR.get(action, True) else f"{action}:{actor_id}"
    last = float(data["cooldowns"].get(key, 0))
    remaining = COOLDOWNS[action] - (time.time() - last)
    return max(0, int(remaining))


def format_remaining(seconds: int) -> str:
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {sec}s"
    return f"{sec}s"


def evidence_is_image(attachment: discord.Attachment | None) -> bool:
    if attachment is None:
        return False
    return bool(attachment.content_type and attachment.content_type.startswith("image/"))


async def archive_evidence(
    attachment: discord.Attachment,
    case_id: str,
) -> Path:
    data = await attachment.read()
    extension = Path(attachment.filename).suffix.lower() or ".img"
    path = EVIDENCE_DIR / f"{case_id}{extension}"
    path.write_bytes(data)
    return path


async def restore_roles(member: discord.Member, role_ids: list[int], bot_top_role: discord.Role):
    roles = []
    for role_id in role_ids:
        role = member.guild.get_role(role_id)
        if role and role < bot_top_role and not role.managed:
            roles.append(role)

    if roles:
        await member.add_roles(*roles, reason="Chatly moderation role restoration")


def build_log_embed(record: dict) -> discord.Embed:
    status = record.get("outcome", "Success")
    color = discord.Color.green() if status == "Success" else discord.Color.red()

    title = (
        f"{EMOJIS['flag']} Warning Appeal • {record['case_id']}"
        if record.get("action") == "warning_appeal"
        else f"{EMOJIS['mod']} {record['action'].upper()} • {record['case_id']}"
    )
    embed = discord.Embed(
        title=title,
        color=color,
        timestamp=parse_iso(record["timestamp"]) or utc_now(),
    )

    embed.add_field(name=f"{EMOJIS['user']} Target", value=f"<@{record['target_id']}> (`{record['target_id']}`)", inline=False)
    embed.add_field(name=f"{EMOJIS['mod']} Moderator", value=f"<@{record['moderator_id']}> (`{record['moderator_id']}`)", inline=False)
    embed.add_field(name=f"{EMOJIS['info']} Reason", value=record.get("reason", "—"), inline=False)
    embed.add_field(name=f"{EMOJIS['info']} Outcome", value=status, inline=True)

    if record.get("approval_status"):
        embed.add_field(
            name=f"{EMOJIS['tick']} Approval",
            value=record["approval_status"],
            inline=True,
        )

    if record.get("approver_id"):
        embed.add_field(
            name=f"{EMOJIS['user']} Approver",
            value=f"<@{record['approver_id']}>",
            inline=True,
        )

    if record.get("warning_number"):
        embed.add_field(
            name=f"{EMOJIS['exclaim']} Warning",
            value=f"#{record['warning_number']}",
            inline=True,
        )

    if record.get("timeout_seconds"):
        embed.add_field(
            name=f"{EMOJIS['timeout']} Timeout",
            value=duration_text(record["timeout_seconds"]),
            inline=True,
        )

    if record.get("evidence_filename"):
        embed.add_field(
            name=f"{EMOJIS['flag']} Evidence",
            value=record["evidence_filename"],
            inline=False,
        )

    if record.get("action") == "warning_appeal":
        if record.get("appeal_id"):
            embed.add_field(name=f"{EMOJIS['folder']} Appeal ID", value=f"`{record['appeal_id']}`", inline=True)
        if record.get("original_case_id"):
            embed.add_field(name=f"{EMOJIS['folder']} Original Case", value=f"`{record['original_case_id']}`", inline=True)
        if record.get("ticket_id"):
            embed.add_field(name=f"{EMOJIS['link']} Ticket ID", value=f"`{record['ticket_id']}`", inline=True)
        if record.get("warning_number"):
            embed.add_field(name=f"{EMOJIS['exclaim']} Warning", value=f"#{record['warning_number']}", inline=True)
        if record.get("original_moderator_id"):
            embed.add_field(
                name=f"{EMOJIS['mod']} Original Moderator",
                value=f"<@{record['original_moderator_id']}> | `{record['original_moderator_id']}`",
                inline=True,
            )
        if record.get("reviewer_id"):
            embed.add_field(
                name=f"{EMOJIS['user']} Reviewer",
                value=f"<@{record['reviewer_id']}> | `{record['reviewer_id']}`",
                inline=True,
            )
        if record.get("decision"):
            embed.add_field(name=f"{EMOJIS['info']} Decision", value=str(record['decision']).title(), inline=True)
        if record.get("decision_reason"):
            embed.add_field(name=f"{EMOJIS['info']} Decision Reason", value=str(record['decision_reason'])[:1024], inline=False)
        if record.get("old_punishment") is not None:
            embed.add_field(name=f"{EMOJIS['timeout']} Previous Punishment", value=str(record['old_punishment'])[:1024], inline=False)
        if record.get("new_punishment") is not None:
            embed.add_field(name=f"{EMOJIS['edit']} New Punishment", value=str(record['new_punishment'])[:1024], inline=False)
        if record.get("appeal_statement"):
            embed.add_field(name=f"{EMOJIS['chat']} Appellant Statement", value=str(record['appeal_statement'])[:1024], inline=False)
        if record.get("abuse_timeout_seconds"):
            embed.add_field(name=f"{EMOJIS['timeout']} Appeal Abuse Timeout", value=duration_text(int(record['abuse_timeout_seconds'])), inline=True)

    embed.set_footer(text="Chatly Moderation")
    return embed


# -------------------------
# CAPTCHA UI
# -------------------------

class CaptchaSubmitButton(discord.ui.Button):
    def __init__(self, user_id: int):
        super().__init__(
            label="Enter CAPTCHA",
            emoji=partial_emoji("tick"),
            style=discord.ButtonStyle.success,
            custom_id=f"chatly_captcha_submit:{user_id}",
        )
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This CAPTCHA belongs to another user.",
                ephemeral=True,
            )
            return

        await interaction.response.send_modal(CaptchaModal(self.user_id))


class CaptchaPromptView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.add_item(CaptchaSubmitButton(user_id))


class CaptchaModal(discord.ui.Modal, title="CAPTCHA Verification"):
    answer = discord.ui.TextInput(
        label="Enter the CAPTCHA",
        placeholder="Enter the code shown to you",
        required=True,
        max_length=20,
    )

    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id

    async def on_submit(self, interaction: discord.Interaction):
        cog = interaction.client.get_cog("Moderation")
        if cog:
            await cog.handle_captcha_submission(interaction, self.user_id, self.answer.value)


class CaptchaVerifyButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Verify CAPTCHA",
            emoji=partial_emoji("tick"),
            style=discord.ButtonStyle.success,
            custom_id="chatly_captcha_verify",
        )

    async def callback(self, interaction: discord.Interaction):
        cog = interaction.client.get_cog("Moderation")
        if cog:
            await cog.start_captcha(interaction)


class CaptchaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CaptchaVerifyButton())


# -------------------------
# APPROVAL UI
# -------------------------

class DenyModal(discord.ui.Modal, title="Deny Moderation Request"):
    reason = discord.ui.TextInput(
        label="Denial reason",
        placeholder="Why are you denying this request?",
        required=True,
        max_length=500,
    )

    def __init__(self, request_id: str):
        super().__init__(timeout=300)
        self.request_id = request_id

    async def on_submit(self, interaction: discord.Interaction):
        cog = interaction.client.get_cog("Moderation")
        if cog:
            await cog.deny_request(interaction, self.request_id, self.reason.value)


class ApprovalView(discord.ui.View):
    def __init__(self, request_id: str):
        super().__init__(timeout=None)
        self.request_id = request_id

        approve = discord.ui.Button(
            label="Approve",
            emoji=partial_emoji("tick"),
            style=discord.ButtonStyle.success,
            custom_id=f"chatly_approval_approve:{request_id}",
        )
        approve.callback = self.approve_callback

        deny = discord.ui.Button(
            label="Deny",
            emoji=partial_emoji("close"),
            style=discord.ButtonStyle.danger,
            custom_id=f"chatly_approval_deny:{request_id}",
        )
        deny.callback = self.deny_callback

        self.add_item(approve)
        self.add_item(deny)

    async def approve_callback(self, interaction: discord.Interaction):
        cog = interaction.client.get_cog("Moderation")
        if cog:
            await cog.approve_request(interaction, self.request_id)

    async def deny_callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(DenyModal(self.request_id))


# -------------------------
# WARNING APPEAL UI
# -------------------------

class WarningAppealButton(discord.ui.Button):
    def __init__(self, case_id: str, user_id: int):
        super().__init__(
            label="Appeal Warning",
            emoji=partial_emoji("flag"),
            style=discord.ButtonStyle.secondary,
            custom_id=f"chatly_warning_appeal:{case_id}:{user_id}",
        )
        self.case_id = case_id
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                f"{EMOJIS['close']} This warning belongs to another member.",
                ephemeral=True,
            )
            return
        cog = interaction.client.get_cog("Moderation")
        if cog:
            await cog.start_warning_appeal_confirmation(interaction, self.case_id)


class WarningAppealView(discord.ui.View):
    def __init__(self, case_id: str, user_id: int):
        super().__init__(timeout=None)
        self.add_item(WarningAppealButton(case_id, user_id))


class WarningAppealConfirmationView(discord.ui.View):
    def __init__(self, case_id: str, user_id: int):
        super().__init__(timeout=180)
        self.case_id = case_id
        self.user_id = user_id

        continue_button = discord.ui.Button(
            label="Continue Appeal",
            emoji=partial_emoji("tick"),
            style=discord.ButtonStyle.success,
        )
        cancel_button = discord.ui.Button(
            label="Cancel",
            emoji=partial_emoji("close"),
            style=discord.ButtonStyle.secondary,
        )
        continue_button.callback = self.continue_callback
        cancel_button.callback = self.cancel_callback
        self.add_item(continue_button)
        self.add_item(cancel_button)

    async def continue_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                f"{EMOJIS['close']} This confirmation does not belong to you.",
                ephemeral=True,
            )
            return
        cog = interaction.client.get_cog("Moderation")
        if cog:
            await cog.create_warning_appeal_ticket(interaction, self.case_id)

    async def cancel_callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            content=f"{EMOJIS['close']} Warning appeal cancelled.",
            embed=None,
            view=None,
        )


class SubmitAppealModal(discord.ui.Modal, title="Submit Warning Appeal"):
    explanation = discord.ui.TextInput(
        label="Why should this warning be reviewed?",
        placeholder="Explain what happened and why you believe the warning should be reviewed.",
        required=True,
        max_length=1800,
        style=discord.TextStyle.paragraph,
    )

    def __init__(self, appeal_id: str):
        super().__init__(timeout=300)
        self.appeal_id = appeal_id

    async def on_submit(self, interaction: discord.Interaction):
        cog = interaction.client.get_cog("Moderation")
        if cog:
            await cog.submit_warning_appeal_statement(
                interaction,
                self.appeal_id,
                self.explanation.value,
            )


class AppealDecisionModal(discord.ui.Modal):
    def __init__(self, appeal_id: str, decision: str):
        title_map = {
            "uphold": "Uphold Warning",
            "remove": "Remove Warning",
            "modify": "Modify Warning",
        }
        super().__init__(title=title_map[decision])
        self.appeal_id = appeal_id
        self.decision = decision

        self.reason = discord.ui.TextInput(
            label="Decision reason",
            placeholder="Explain the decision clearly.",
            required=True,
            max_length=1000,
            style=discord.TextStyle.paragraph,
        )
        self.add_item(self.reason)

        self.new_punishment = None
        if decision == "modify":
            self.new_punishment = discord.ui.TextInput(
                label="New punishment",
                placeholder="Examples: 1h, 6h, 1d, jail, none",
                required=True,
                max_length=40,
            )
            self.add_item(self.new_punishment)

    async def on_submit(self, interaction: discord.Interaction):
        cog = interaction.client.get_cog("Moderation")
        if cog:
            await cog.resolve_warning_appeal(
                interaction,
                self.appeal_id,
                self.decision,
                self.reason.value,
                self.new_punishment.value if self.new_punishment else None,
            )


class AppealAbuseModal(discord.ui.Modal, title="Appeal Abuse Action"):
    duration = discord.ui.TextInput(
        label="Additional timeout",
        placeholder="Choose 1h to 6h",
        required=True,
        max_length=10,
    )
    reason = discord.ui.TextInput(
        label="Reason",
        placeholder="Why is this appeal clearly false, misleading, or abusive?",
        required=True,
        max_length=800,
        style=discord.TextStyle.paragraph,
    )

    def __init__(self, appeal_id: str):
        super().__init__(timeout=300)
        self.appeal_id = appeal_id

    async def on_submit(self, interaction: discord.Interaction):
        cog = interaction.client.get_cog("Moderation")
        if cog:
            await cog.apply_warning_appeal_abuse(
                interaction,
                self.appeal_id,
                self.duration.value,
                self.reason.value,
            )


class WarningAppealTicketView(discord.ui.View):
    def __init__(self, appeal_id: str):
        super().__init__(timeout=None)
        self.appeal_id = appeal_id

        submit = discord.ui.Button(
            label="Submit Explanation",
            emoji=partial_emoji("chat"),
            style=discord.ButtonStyle.secondary,
            custom_id=f"chatly_warning_appeal_submit:{appeal_id}",
        )
        submit.callback = self.submit_callback

        uphold = discord.ui.Button(
            label="Uphold",
            emoji=partial_emoji("info"),
            style=discord.ButtonStyle.secondary,
            custom_id=f"chatly_warning_appeal_uphold:{appeal_id}",
        )
        uphold.callback = self.uphold_callback

        modify = discord.ui.Button(
            label="Modify",
            emoji=partial_emoji("edit"),
            style=discord.ButtonStyle.primary,
            custom_id=f"chatly_warning_appeal_modify:{appeal_id}",
        )
        modify.callback = self.modify_callback

        remove = discord.ui.Button(
            label="Remove",
            emoji=partial_emoji("delete"),
            style=discord.ButtonStyle.danger,
            custom_id=f"chatly_warning_appeal_remove:{appeal_id}",
        )
        remove.callback = self.remove_callback

        abuse = discord.ui.Button(
            label="Appeal Abuse",
            emoji=partial_emoji("exclaim"),
            style=discord.ButtonStyle.danger,
            custom_id=f"chatly_warning_appeal_abuse:{appeal_id}",
        )
        abuse.callback = self.abuse_callback

        reopen = discord.ui.Button(
            label="Allow Another Appeal",
            emoji=partial_emoji("refresh"),
            style=discord.ButtonStyle.secondary,
            custom_id=f"chatly_warning_appeal_reopen:{appeal_id}",
        )
        reopen.callback = self.reopen_callback

        for item in (submit, uphold, modify, remove, abuse, reopen):
            self.add_item(item)

    async def submit_callback(self, interaction: discord.Interaction):
        cog = interaction.client.get_cog("Moderation")
        if cog:
            await cog.open_appeal_statement(interaction, self.appeal_id)

    async def uphold_callback(self, interaction: discord.Interaction):
        cog = interaction.client.get_cog("Moderation")
        if cog:
            await cog.open_staff_decision(interaction, self.appeal_id, "uphold")

    async def modify_callback(self, interaction: discord.Interaction):
        cog = interaction.client.get_cog("Moderation")
        if cog:
            await cog.open_staff_decision(interaction, self.appeal_id, "modify")

    async def remove_callback(self, interaction: discord.Interaction):
        cog = interaction.client.get_cog("Moderation")
        if cog:
            await cog.open_staff_decision(interaction, self.appeal_id, "remove")

    async def abuse_callback(self, interaction: discord.Interaction):
        cog = interaction.client.get_cog("Moderation")
        if cog:
            await cog.open_appeal_abuse(interaction, self.appeal_id)

    async def reopen_callback(self, interaction: discord.Interaction):
        cog = interaction.client.get_cog("Moderation")
        if cog:
            await cog.allow_another_warning_appeal(interaction, self.appeal_id)

# -------------------------
# MODERATION COG
# -------------------------

class BotTesterView(discord.ui.View):
    """Self-service role testing panel for the authorized Bot Tester role."""

    def __init__(self):
        super().__init__(timeout=None)

    async def _get_cog(self, interaction: discord.Interaction):
        cog = interaction.client.get_cog("Moderation")
        if cog is None:
            await interaction.response.send_message(
                f"{EMOJIS['close']} The moderation system is not ready.",
                ephemeral=True,
            )
        return cog

    async def _authorized(self, interaction: discord.Interaction) -> bool:
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                f"{EMOJIS['close']} This panel can only be used inside Chatly.",
                ephemeral=True,
            )
            return False
        tester_role = interaction.guild.get_role(BOT_TESTER_ROLE_ID)
        if tester_role is None or tester_role not in interaction.user.roles:
            await interaction.response.send_message(
                f"{EMOJIS['close']} You need the **Bot Tester** role to use this panel.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.select(
        placeholder="Select a staff rank to test",
        custom_id="chatly_bot_tester_rank",
        options=[
            discord.SelectOption(label="Jr Mod", value="1", emoji=partial_emoji("mod")),
            discord.SelectOption(label="Mod", value="2", emoji=partial_emoji("mod")),
            discord.SelectOption(label="Sr Mod", value="3", emoji=partial_emoji("mod")),
            discord.SelectOption(label="Admin", value="4", emoji=partial_emoji("settings")),
            discord.SelectOption(label="Manager", value="5", emoji=partial_emoji("settings")),
        ],
    )
    async def rank_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        if not await self._authorized(interaction):
            return
        cog = await self._get_cog(interaction)
        if cog:
            await cog.bot_tester_set_rank(interaction, int(select.values[0]))

    @discord.ui.button(
        label="Add Premium",
        style=discord.ButtonStyle.success,
        emoji=partial_emoji("premium"),
        custom_id="chatly_bot_tester_add_premium",
        row=1,
    )
    async def add_premium(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._authorized(interaction):
            return
        cog = await self._get_cog(interaction)
        if cog:
            await cog.bot_tester_premium(interaction, True)

    @discord.ui.button(
        label="Remove Premium",
        style=discord.ButtonStyle.danger,
        emoji=partial_emoji("close"),
        custom_id="chatly_bot_tester_remove_premium",
        row=1,
    )
    async def remove_premium(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._authorized(interaction):
            return
        cog = await self._get_cog(interaction)
        if cog:
            await cog.bot_tester_premium(interaction, False)

    @discord.ui.button(
        label="Restore Original Roles",
        style=discord.ButtonStyle.secondary,
        emoji=partial_emoji("refresh"),
        custom_id="chatly_bot_tester_restore",
        row=2,
    )
    async def restore(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._authorized(interaction):
            return
        cog = await self._get_cog(interaction)
        if cog:
            await cog.bot_tester_restore(interaction)


class Moderation(commands.Cog):
    remove = app_commands.Group(
        name="remove",
        description="Remove moderation records.",
    )

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data = load_data()
        self.data_lock = asyncio.Lock()

    async def cog_load(self):
        # Persistent approval buttons.
        for request_id, request in self.data["approvals"].items():
            if request.get("status") == "pending" and request.get("message_id"):
                self.bot.add_view(
                    ApprovalView(request_id),
                    message_id=int(request["message_id"]),
                )

        # Persistent CAPTCHA button.
        self.bot.add_view(CaptchaView())

        # Persistent Bot Tester panel.
        self.bot.add_view(BotTesterView())

        # Persistent warning appeal buttons in existing warning DMs.
        for user_id, warnings in self.data.get("warnings", {}).items():
            for warning in warnings:
                case_id = warning.get("case_id")
                if case_id:
                    self.bot.add_view(
                        WarningAppealView(case_id, int(user_id))
                    )

        # Persistent appeal ticket controls.
        for appeal_id, appeal in self.data.get("warning_appeals", {}).items():
            if appeal.get("status") in {"open", "pending_review", "resolved"}:
                self.bot.add_view(WarningAppealTicketView(appeal_id))

    async def save(self):
        async with self.data_lock:
            save_data(self.data)

    def member_from_interaction(
        self,
        interaction: discord.Interaction,
        target: discord.Member,
    ) -> tuple[bool, str]:
        actor = interaction.user

        if not isinstance(actor, discord.Member):
            return False, "This command can only be used inside the server."

        if not is_staff(actor):
            return False, "You do not have a Chatly staff role."

        if target.id == actor.id:
            return False, "You cannot moderate yourself."

        if target.id == OWNER_ID:
            return False, "The Owner is protected from moderation."

        if not is_higher_than(actor, target):
            return False, "You cannot moderate a member with an equal or higher staff rank."

        bot_member = interaction.guild.me
        if bot_member and target.top_role >= bot_member.top_role:
            return False, "I cannot moderate this member because their highest role is above my role."

        return True, ""

    def permission_result(self, actor: discord.Member, minimum_rank: int) -> tuple[bool, str]:
        rank = rank_of(actor)

        if rank < minimum_rank:
            return False, f"You need **{rank_name(minimum_rank)}+** to use this command."

        return True, ""

    async def get_target(
        self,
        interaction: discord.Interaction,
        user_id: int,
    ) -> discord.Member | None:
        member = interaction.guild.get_member(user_id)
        if member:
            return member

        try:
            return await interaction.guild.fetch_member(user_id)
        except (discord.NotFound, discord.HTTPException):
            return None

    async def send_log(
        self,
        record: dict,
        evidence_path: Path | None = None,
    ):
        log_channel_id = PURGE_LOG_CHANNEL_ID if record.get("action") == "purge" else CASE_FILES_CHANNEL_ID
        channel = self.bot.get_channel(log_channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(log_channel_id)
            except (discord.NotFound, discord.HTTPException):
                return

        embed = build_log_embed(record)

        try:
            if evidence_path and evidence_path.exists():
                file = discord.File(str(evidence_path), filename=evidence_path.name)
                embed.set_image(url=f"attachment://{evidence_path.name}")
                await channel.send(embed=embed, file=file)
            else:
                await channel.send(embed=embed)
        except Exception:
            # Logging must never break an otherwise successful moderation action.
            return

    async def award_points(
        self,
        staff_id: int,
        action: str,
        target_id: int,
        case_id: str,
    ):
        staff_stats = self.bot.get_cog("StaffStats")
        if staff_stats is None:
            return

        reference = f"moderation:{action}:{target_id}:{case_id}"

        try:
            staff_stats.record_action(
                staff_id=staff_id,
                action=action,
                reference=reference,
            )
        except Exception:
            # Stats must never break moderation.
            return

    def create_record(
        self,
        case_id: str,
        action: str,
        target_id: int,
        moderator_id: int,
        reason: str,
        outcome: str = "Success",
        **extra,
    ) -> dict:
        record = {
            "case_id": case_id,
            "action": action,
            "target_id": target_id,
            "moderator_id": moderator_id,
            "reason": reason,
            "timestamp": iso(utc_now()),
            "outcome": outcome,
            **extra,
        }

        self.data["records"].append(record)
        return record

    async def create_approval_request(
        self,
        interaction: discord.Interaction,
        action: str,
        target: discord.Member,
        reason: str,
        evidence_path: Path | None,
        required_rank: int,
        extra: dict | None = None,
    ):
        extra = dict(extra or {})
        case_id = extra.pop("case_id", None) or next_case_id(self.data)
        request_id = uuid.uuid4().hex
        request = {
            "request_id": request_id,
            "case_id": case_id,
            "action": action,
            "target_id": target.id,
            "target_name": str(target),
            "requester_id": interaction.user.id,
            "reason": reason,
            "required_rank": required_rank,
            "evidence_path": str(evidence_path) if evidence_path else None,
            "requested_at": iso(utc_now()),
            "status": "pending",
            **extra,
        }

        channel = self.bot.get_channel(APPROVAL_CHANNEL_ID)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(APPROVAL_CHANNEL_ID)
            except (discord.NotFound, discord.HTTPException):
                return False, "The approval channel is unavailable."

        active_warnings = get_active_warnings(self.data, target.id)
        description_lines = [
            f"{EMOJIS['user']} **Requester:** <@{interaction.user.id}>",
            f"{EMOJIS['user']} **Target:** <@{target.id}> (`{target.id}`)",
            f"{EMOJIS['info']} **Reason:** {reason}",
            f"{EMOJIS['tick']} **Required approval:** {rank_name(required_rank)}+",
        ]

        embed = discord.Embed(
            title=f"{EMOJIS['mod']} Moderation Approval • {action.upper()}",
            color=discord.Color.orange(),
            description="\n".join(description_lines),
            timestamp=utc_now(),
        )
        embed.add_field(name=f"{EMOJIS['folder']} Case ID", value=f"`{case_id}`", inline=True)
        embed.add_field(name=f"{EMOJIS['folder']} Request ID", value=f"`{request_id}`", inline=True)

        if action == "warn":
            next_warning_number = max([int(w.get("warning_number", 0)) for w in self.data["warnings"].get(str(target.id), [])] or [0]) + 1
            warning_timeout = request.get("warning_timeout")
            result = f"Warning #{next_warning_number}"
            if warning_timeout:
                result += f" → {EMOJIS['timeout']} {duration_text(int(warning_timeout))} timeout"
            elif len(active_warnings) + 1 >= 3:
                result += f" → {EMOJIS['mod']} Jail"
            embed.add_field(name=f"{EMOJIS['exclaim']} Current Warnings", value=f"{len(active_warnings)} active", inline=True)
            embed.add_field(name=f"{EMOJIS['mod']} Result if Approved", value=result, inline=False)
        elif action == "timeout":
            seconds = int(request.get("timeout_seconds", 0))
            embed.add_field(name=f"{EMOJIS['timeout']} Duration", value=duration_text(seconds), inline=True)
        elif action == "untimeout":
            embed.add_field(name=f"{EMOJIS['timeout']} Action", value="Remove current timeout", inline=True)
        elif action == "sus":
            embed.add_field(name=f"{EMOJIS['lock']} Action", value="Restrict member to CAPTCHA verification", inline=True)
        elif action == "ban":
            embed.add_field(name=f"{EMOJIS['ban']} Action", value="Permanent server ban", inline=True)

        file = None
        if evidence_path and evidence_path.exists():
            file = discord.File(str(evidence_path), filename=evidence_path.name)
            embed.set_image(url=f"attachment://{evidence_path.name}")

        embed.set_footer(text="Chatly • Pending approval")

        try:
            message = await channel.send(
                embed=embed,
                file=file,
                view=ApprovalView(request_id),
            )
        except discord.HTTPException:
            return False, "I could not create the approval request."

        request["message_id"] = message.id
        self.data["approvals"][request_id] = request
        await self.save()

        await interaction.response.send_message(
            f"{EMOJIS['tick']} Your **{action}** request has been sent for approval.",
            ephemeral=True,
        )
        return True, request_id

    async def delete_approval_message(self, request: dict):
        message_id = request.get("message_id")
        if not message_id:
            return
        channel = await get_guild_channel(self.bot, APPROVAL_CHANNEL_ID)
        if channel is None:
            return
        try:
            message = await channel.fetch_message(int(message_id))
            await message.delete()
        except (discord.NotFound, discord.HTTPException):
            pass

    async def approve_request(self, interaction: discord.Interaction, request_id: str):
        request = self.data["approvals"].get(request_id)
        if not request or request.get("status") != "pending":
            await interaction.response.send_message(
                f"{EMOJIS['info']} This approval request is no longer active.",
                ephemeral=True,
            )
            return

        actor = interaction.user
        if not isinstance(actor, discord.Member):
            await interaction.response.send_message(f"{EMOJIS['close']} Invalid staff account.", ephemeral=True)
            return

        if rank_of(actor) < int(request["required_rank"]):
            await interaction.response.send_message(
                f"{EMOJIS['close']} You need **{rank_name(int(request['required_rank']))}+** to approve this request.",
                ephemeral=True,
            )
            return

        if actor.id == int(request["requester_id"]):
            await interaction.response.send_message(
                f"{EMOJIS['close']} You cannot approve your own moderation request.",
                ephemeral=True,
            )
            return

        requested_at = parse_iso(request["requested_at"])
        if requested_at and (utc_now() - requested_at).total_seconds() > APPROVAL_EXPIRY_SECONDS:
            request["status"] = "expired"
            await self.save()
            await self.delete_approval_message(request)
            await interaction.response.send_message(
                f"{EMOJIS['close']} This approval request has expired and was removed from the approval queue.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        target = None
        if request["action"] == "ban":
            try:
                target = await self.bot.fetch_user(int(request["target_id"]))
            except (discord.NotFound, discord.HTTPException):
                request["status"] = "failed"
                await self.save()
                await self.delete_approval_message(request)
                await interaction.followup.send(
                    f"{EMOJIS['close']} The target user could not be found.",
                    ephemeral=True,
                )
                return
        else:
            target = await self.get_target(interaction, int(request["target_id"]))
            if target is None:
                request["status"] = "failed"
                await self.save()
                await self.delete_approval_message(request)
                await interaction.followup.send(
                    f"{EMOJIS['close']} The target is no longer in the server.",
                    ephemeral=True,
                )
                return

        try:
            case_id = request.get("case_id") or next_case_id(self.data)
            evidence_path = Path(request["evidence_path"]) if request.get("evidence_path") else None

            if request["action"] == "warn":
                await self.execute_warn(
                    interaction=interaction,
                    target=target,
                    reason=request["reason"],
                    evidence_path=evidence_path,
                    requester_id=int(request["requester_id"]),
                    case_id=case_id,
                    approval_status="Approved",
                    approver_id=actor.id,
                    warning_timeout_override=request.get("warning_timeout"),
                )

            elif request["action"] == "timeout":
                seconds = int(request["timeout_seconds"])
                await target.timeout(
                    timedelta(seconds=seconds),
                    reason=request["reason"],
                )

                record = self.create_record(
                    case_id,
                    "timeout",
                    target.id,
                    int(request["requester_id"]),
                    request["reason"],
                    timeout_seconds=seconds,
                    approval_status="Approved",
                    approver_id=actor.id,
                )
                await self.save()
                await self.send_log(record)
                await self.award_points(
                    int(request["requester_id"]),
                    "timeout",
                    target.id,
                    case_id,
                )

            elif request["action"] == "sus":
                await self.execute_sus(
                    interaction=interaction,
                    target=target,
                    reason=request["reason"],
                    requester_id=int(request["requester_id"]),
                    case_id=case_id,
                    approval_status="Approved",
                    approver_id=actor.id,
                )

            elif request["action"] == "untimeout":
                await target.timeout(None, reason=request["reason"])

                record = self.create_record(
                    case_id,
                    "untimeout",
                    target.id,
                    int(request["requester_id"]),
                    request["reason"],
                    approval_status="Approved",
                    approver_id=actor.id,
                )
                await self.save()
                await self.send_log(record)

            elif request["action"] == "ban":
                await interaction.guild.ban(
                    target,
                    reason=request["reason"],
                    delete_message_days=0,
                )

                evidence_path = Path(request["evidence_path"]) if request.get("evidence_path") else None
                record = self.create_record(
                    case_id,
                    "ban",
                    target.id,
                    int(request["requester_id"]),
                    request["reason"],
                    approval_status="Approved",
                    approver_id=actor.id,
                    evidence_filename=evidence_path.name if evidence_path else None,
                )
                await self.save()
                await self.send_log(record, evidence_path)
                await self.award_points(
                    int(request["requester_id"]),
                    "ban",
                    target.id,
                    case_id,
                )

                try:
                    if BAN_APPEAL_SERVER_URL.startswith("http"):
                        user = await self.bot.fetch_user(target.id)
                        await user.send(
                            f"You have been permanently banned from **Chatly**.\n\n"
                            f"**Reason:** {request['reason']}\n\n"
                            f"Ban appeals: {BAN_APPEAL_SERVER_URL}"
                        )
                except discord.HTTPException:
                    pass

            else:
                raise RuntimeError("Unsupported approval action.")

        except discord.Forbidden:
            request["status"] = "failed"
            await self.save()
            await self.delete_approval_message(request)
            await interaction.followup.send(
                f"{EMOJIS['close']} Discord denied the moderation action. No Mod Points were awarded.",
                ephemeral=True,
            )
            return
        except discord.HTTPException:
            request["status"] = "failed"
            await self.save()
            await self.delete_approval_message(request)
            await interaction.followup.send(
                f"{EMOJIS['close']} The moderation action failed. No Mod Points were awarded.",
                ephemeral=True,
            )
            return
        except Exception as exc:
            request["status"] = "failed"
            await self.save()
            await self.delete_approval_message(request)
            await interaction.followup.send(
                f"{EMOJIS['close']} The moderation action failed: `{type(exc).__name__}`",
                ephemeral=True,
            )
            return

        request["status"] = "approved"
        request["approved_by"] = actor.id
        request["approved_at"] = iso(utc_now())

        # Consume the command cooldown only after the approved action succeeds.
        requested_by = int(request["requester_id"])
        if request["action"] in COOLDOWNS:
            set_cooldown(self.data, request["action"], requested_by, interaction.guild.id)

        await self.save()

        await self.delete_approval_message(request)
        await self.log_approval(
            request,
            status="Approved",
            actor_id=actor.id,
            reason="Approved",
        )

        await interaction.followup.send(
            f"{EMOJIS['tick']} Moderation action approved and completed."
        )

    async def deny_request(
        self,
        interaction: discord.Interaction,
        request_id: str,
        denial_reason: str,
    ):
        request = self.data["approvals"].get(request_id)
        if not request or request.get("status") != "pending":
            await interaction.response.send_message(
                f"{EMOJIS['info']} This approval request is no longer active.",
                ephemeral=True,
            )
            return

        actor = interaction.user
        if not isinstance(actor, discord.Member):
            await interaction.response.send_message(f"{EMOJIS['close']} Invalid staff account.", ephemeral=True)
            return

        if rank_of(actor) < int(request["required_rank"]):
            await interaction.response.send_message(
                f"{EMOJIS['close']} You need **{rank_name(int(request['required_rank']))}+** to deny this request.",
                ephemeral=True,
            )
            return

        if actor.id == int(request["requester_id"]):
            await interaction.response.send_message(
                f"{EMOJIS['close']} You cannot deny your own moderation request.",
                ephemeral=True,
            )
            return

        if not denial_reason.strip():
            await interaction.response.send_message(
                f"{EMOJIS['close']} A denial reason is required.",
                ephemeral=True,
            )
            return

        request["status"] = "denied"
        request["denied_by"] = actor.id
        request["denial_reason"] = denial_reason
        request["denied_at"] = iso(utc_now())
        await self.save()

        await self.delete_approval_message(request)
        await self.log_approval(
            request,
            status="Denied",
            actor_id=actor.id,
            reason=denial_reason.strip(),
        )

        await interaction.response.send_message(
            f"{EMOJIS['close']} Request denied.",
            ephemeral=True,
        )

    async def log_approval(self, request: dict, status: str, actor_id: int, reason: str):
        channel_id = CASE_FILES_CHANNEL_ID if status == "Approved" else DENIAL_LOG_CHANNEL_ID
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except (discord.NotFound, discord.HTTPException):
                return

        title = (
            f"{EMOJIS['tick']} Moderation Approval • Approved"
            if status == "Approved"
            else f"{EMOJIS['close']} Moderation Approval • Denied"
        )
        embed = discord.Embed(
            title=title,
            color=discord.Color.green() if status == "Approved" else discord.Color.red(),
            timestamp=utc_now(),
        )
        embed.add_field(name=f"{EMOJIS['folder']} Case ID", value=f"`{request.get("case_id", "Unknown")}`", inline=True)
        embed.add_field(name=f"{EMOJIS['folder']} Request", value=f"`{request['request_id']}`", inline=True)
        embed.add_field(name=f"{EMOJIS['mod']} Action", value=request["action"], inline=True)
        embed.add_field(name=f"{EMOJIS['user']} Target", value=f"<@{request['target_id']}>", inline=True)
        embed.add_field(name=f"{EMOJIS['user']} Requester", value=f"<@{request['requester_id']}>", inline=True)
        embed.add_field(name=f"{EMOJIS['user']} Reviewer", value=f"<@{actor_id}>", inline=True)
        embed.add_field(name=f"{EMOJIS['info']} Reason", value=reason, inline=False)
        try:
            if request.get("evidence_path") and Path(request["evidence_path"]).exists():
                file = discord.File(request["evidence_path"], filename=Path(request["evidence_path"]).name)
                embed.set_image(url=f"attachment://{Path(request['evidence_path']).name}")
                await channel.send(embed=embed, file=file)
            else:
                await channel.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            return

    async def start_warning_appeal_confirmation(self, interaction: discord.Interaction, case_id: str):
        warning = None
        warning_owner = None
        for user_id, warnings in self.data.get("warnings", {}).items():
            for item in warnings:
                if item.get("case_id") == case_id:
                    warning = item
                    warning_owner = int(user_id)
                    break
            if warning:
                break

        if warning is None:
            await interaction.response.send_message(
                f"{EMOJIS['close']} This warning could not be found.",
                ephemeral=True,
            )
            return
        if warning.get("removed"):
            await interaction.response.send_message(
                f"{EMOJIS['close']} This warning has already been removed and cannot normally be appealed.",
                ephemeral=True,
            )
            return
        if warning_owner != interaction.user.id:
            await interaction.response.send_message(
                f"{EMOJIS['close']} This warning does not belong to you.",
                ephemeral=True,
            )
            return

        current_appeal_id = warning.get("current_appeal_id")
        if current_appeal_id:
            current = self.data.get("warning_appeals", {}).get(current_appeal_id)
            if current and current.get("status") in {"open", "pending_review"}:
                channel_id = int(current.get("ticket_channel_id", 0) or 0)
                channel = self.bot.get_channel(channel_id) if channel_id else None
                if channel:
                    await interaction.response.send_message(
                        f"{EMOJIS['info']} You already have an open appeal ticket: {channel.mention}",
                        ephemeral=True,
                    )
                    return
                current["status"] = "closed_without_decision"

        if warning.get("appeal_count", 0) >= 1 and not warning.get("appeal_reopened"):
            await interaction.response.send_message(
                f"{EMOJIS['info']} This warning has already been appealed. Another appeal requires staff permission.",
                ephemeral=True,
            )
            return

        status = "Active"
        expires = parse_iso(warning.get("expires_at"))
        if expires and expires <= utc_now():
            status = "Expired — record correction appeal"

        embed = discord.Embed(
            title=f"{EMOJIS['flag']} Before You Submit Your Appeal",
            description=(
                "Appeals are intended for genuine concerns about a warning.\n\n"
                f"{EMOJIS['exclaim']} False, misleading, or abusive appeals may result in additional moderation action, "
                "including a longer timeout.\n\n"
                "Please continue only if you believe this warning should be reviewed."
            ),
            color=discord.Color.orange(),
        )
        embed.add_field(name=f"{EMOJIS['folder']} Case", value=f"`{case_id}`", inline=True)
        embed.add_field(name=f"{EMOJIS['exclaim']} Warning", value=f"#{warning['warning_number']}", inline=True)
        embed.add_field(name=f"{EMOJIS['info']} Status", value=status, inline=True)
        await interaction.response.send_message(
            embed=embed,
            view=WarningAppealConfirmationView(case_id, interaction.user.id),
            ephemeral=True,
        )

    async def create_warning_appeal_ticket(self, interaction: discord.Interaction, case_id: str):
        guild = self.bot.get_guild(GUILD_ID)
        if guild is None:
            await interaction.response.send_message(
                f"{EMOJIS['close']} Chatly server is unavailable.",
                ephemeral=True,
            )
            return

        member = guild.get_member(interaction.user.id)
        if member is None:
            try:
                member = await guild.fetch_member(interaction.user.id)
            except (discord.NotFound, discord.HTTPException):
                member = None
        if member is None:
            await interaction.response.send_message(
                f"{EMOJIS['close']} You must still be a member of Chatly to appeal a warning.",
                ephemeral=True,
            )
            return

        warning = None
        for item in self.data.get("warnings", {}).get(str(member.id), []):
            if item.get("case_id") == case_id:
                warning = item
                break
        if warning is None or warning.get("removed"):
            await interaction.response.send_message(
                f"{EMOJIS['close']} This warning is no longer eligible for appeal.",
                ephemeral=True,
            )
            return

        current_appeal_id = warning.get("current_appeal_id")
        if warning.get("appeal_count", 0) >= 1 and not warning.get("appeal_reopened"):
            if current_appeal_id:
                current = self.data.get("warning_appeals", {}).get(current_appeal_id)
                channel = guild.get_channel(int(current.get("ticket_channel_id", 0))) if current else None
                if channel:
                    await interaction.response.send_message(
                        f"{EMOJIS['info']} You already appealed this warning: {channel.mention}",
                        ephemeral=True,
                    )
                    return
            await interaction.response.send_message(
                f"{EMOJIS['info']} This warning has already been appealed. Another appeal requires staff permission.",
                ephemeral=True,
            )
            return

        if current_appeal_id:
            existing = self.data.get("warning_appeals", {}).get(current_appeal_id)
            if existing and existing.get("status") in {"open", "pending_review"}:
                channel = guild.get_channel(int(existing.get("ticket_channel_id", 0)))
                if channel:
                    await interaction.response.send_message(
                        f"{EMOJIS['info']} Your appeal is already open: {channel.mention}",
                        ephemeral=True,
                    )
                    return

        support = self.bot.get_cog("Support")
        if support is None or not hasattr(support, "next_ticket_id") or not hasattr(support, "tickets"):
            await interaction.response.send_message(
                f"{EMOJIS['close']} The Chatly Support system is not loaded. Please try again later.",
                ephemeral=True,
            )
            return

        category = guild.get_channel(WARNING_APPEAL_CATEGORY_ID)
        bot_member = guild.me or guild.get_member(self.bot.user.id if self.bot.user else 0)
        if not isinstance(category, discord.CategoryChannel) or bot_member is None:
            await interaction.response.send_message(
                f"{EMOJIS['close']} The warning appeal ticket system is not configured correctly.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        ticket_id = support.next_ticket_id()
        appeal_id = f"WAP-{uuid.uuid4().hex[:10].upper()}"
        channel_name = f"⚠️・{sanitize_ticket_username(member.name)}"

        try:
            channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=role_overwrites_for_warning_appeal(guild, member, bot_member),
                topic=f"Chatly Ticket {ticket_id} | Warning Appeal {appeal_id} | Case {case_id}",
                reason=f"Chatly warning appeal ticket {ticket_id}",
            )
        except discord.HTTPException as exc:
            await interaction.followup.send(
                f"{EMOJIS['close']} I could not create the appeal ticket: `{exc}`",
                ephemeral=True,
            )
            return

        appeal = {
            "appeal_id": appeal_id,
            "ticket_id": ticket_id,
            "ticket_channel_id": channel.id,
            "type": "Warning Appeal",
            "user_id": member.id,
            "case_id": case_id,
            "warning_number": warning.get("warning_number"),
            "original_moderator_id": warning.get("moderator_id"),
            "original_reason": warning.get("reason"),
            "evidence_path": warning.get("evidence_path"),
            "created_at": iso(utc_now()),
            "status": "open",
            "statement": None,
            "statement_at": None,
            "decision": None,
            "decision_reason": None,
            "reviewer_id": None,
            "resolved_at": None,
            "abuse_timeout_seconds": None,
        }
        self.data["warning_appeals"][appeal_id] = appeal
        warning["current_appeal_id"] = appeal_id
        warning["appeal_count"] = int(warning.get("appeal_count", 0)) + 1
        warning["appeal_reopened"] = False
        warning["appeal_status"] = "open"

        # Register the channel inside the existing universal Support / CTY system.
        support.tickets[str(channel.id)] = {
            "ticket_id": ticket_id,
            "channel_id": channel.id,
            "type": "Warning Appeal",
            "reporter_id": member.id,
            "reported_user_id": member.id,
            "reason": warning.get("reason", "Warning appeal"),
            "custom_details": (
                f"Appeal ID: {appeal_id}\n"
                f"Original Case ID: {case_id}\n"
                f"Warning #: {warning.get('warning_number')}"
            ),
            "category_id": category.id,
            "created_at": iso(utc_now()),
            "last_activity": iso(utc_now()),
            "closed_at": None,
            "closed_by": None,
            "close_reason": None,
            "action_taken": None,
            "solved_by": None,
            "members_added": [],
            "actions": [],
            "locked": False,
            "appeal_id": appeal_id,
            "original_case_id": case_id,
            "warning_number": warning.get("warning_number"),
            "decision": None,
            "decision_reason": None,
            "reviewer_id": None,
        }
        support.save()
        await self.save()

        status = "Active"
        expires = parse_iso(warning.get("expires_at"))
        if expires and expires <= utc_now():
            status = "Expired — record correction appeal"

        embed = discord.Embed(
            title=f"{EMOJIS['flag']} Warning Appeal",
            color=discord.Color.orange(),
        )
        embed.add_field(name=f"{EMOJIS['folder']} Ticket ID", value=f"`{ticket_id}`", inline=True)
        embed.add_field(name=f"{EMOJIS['folder']} Appeal ID", value=f"`{appeal_id}`", inline=True)
        embed.add_field(name=f"{EMOJIS['folder']} Case ID", value=f"`{case_id}`", inline=True)
        embed.add_field(name=f"{EMOJIS['user']} Member", value=f"{member.mention} | `{member.id}`", inline=False)
        embed.add_field(name=f"{EMOJIS['exclaim']} Warning", value=f"#{warning.get('warning_number')} • {status}", inline=False)
        embed.add_field(name=f"{EMOJIS['mod']} Original Moderator", value=f"<@{warning.get('moderator_id')}>", inline=False)
        embed.add_field(name=f"{EMOJIS['info']} Original Reason", value=warning.get("reason", "—"), inline=False)
        if is_premium_member(member):
            embed.add_field(
                name=f"{EMOJIS['premium']} Premium Priority Review",
                value="This appeal receives priority review order only. Premium status does not influence the decision.",
                inline=False,
            )
        embed.add_field(
            name=f"{EMOJIS['chat']} What happens next?",
            value=(
                "Explain why you believe the warning should be reviewed using **Submit Explanation**. "
                "You may also send additional evidence, screenshots, files, or relevant Discord message links directly in this ticket."
            ),
            inline=False,
        )
        embed.set_footer(text=f"Chatly • {ticket_id}")

        file = None
        evidence_path = Path(warning["evidence_path"]) if warning.get("evidence_path") else None
        if evidence_path and evidence_path.exists():
            file = discord.File(str(evidence_path), filename=evidence_path.name)
            embed.set_image(url=f"attachment://{evidence_path.name}")

        try:
            await channel.send(
                content=member.mention,
                embed=embed,
                file=file,
                view=WarningAppealTicketView(appeal_id),
            )
        except discord.HTTPException:
            try:
                await channel.delete(reason=f"Chatly warning appeal {appeal_id} failed to initialize")
            except discord.HTTPException:
                pass
            support.tickets.pop(str(channel.id), None)
            support.save()
            self.data["warning_appeals"].pop(appeal_id, None)
            warning["current_appeal_id"] = None
            warning["appeal_count"] = max(0, int(warning.get("appeal_count", 1)) - 1)
            warning["appeal_reopened"] = True
            warning["appeal_status"] = "reopened"
            await self.save()
            await interaction.followup.send(
                f"{EMOJIS['close']} I could not initialize the appeal ticket.",
                ephemeral=True,
            )
            return

        jump = discord.ui.View()
        jump.add_item(discord.ui.Button(
            label="Open Appeal Ticket",
            emoji=partial_emoji("link"),
            style=discord.ButtonStyle.link,
            url=channel.jump_url,
        ))
        notice = (
            f"{EMOJIS['tick']} Your warning appeal ticket has been created. {channel.mention}"
        )
        if is_premium_member(member):
            notice += (
                f"\n{EMOJIS['premium']} **Premium Priority Review:** your appeal is placed in the priority review order."
            )
        await interaction.followup.send(notice, view=jump, ephemeral=True)

    async def open_appeal_statement(self, interaction: discord.Interaction, appeal_id: str):
        appeal = self.data.get("warning_appeals", {}).get(appeal_id)
        if not appeal or appeal.get("status") not in {"open", "pending_review"}:
            await interaction.response.send_message(
                f"{EMOJIS['info']} This appeal is no longer accepting statements.", ephemeral=True
            )
            return
        if interaction.user.id != int(appeal["user_id"]):
            await interaction.response.send_message(
                f"{EMOJIS['close']} Only the appellant can submit the appeal statement.", ephemeral=True
            )
            return
        await interaction.response.send_modal(SubmitAppealModal(appeal_id))

    async def submit_warning_appeal_statement(self, interaction: discord.Interaction, appeal_id: str, statement: str):
        appeal = self.data.get("warning_appeals", {}).get(appeal_id)
        if not appeal or appeal.get("status") not in {"open", "pending_review"}:
            await interaction.response.send_message(
                f"{EMOJIS['info']} This appeal is already resolved.", ephemeral=True
            )
            return
        if interaction.user.id != int(appeal["user_id"]):
            await interaction.response.send_message(
                f"{EMOJIS['close']} Only the appellant can submit the appeal statement.", ephemeral=True
            )
            return

        appeal["statement"] = statement.strip()
        appeal["statement_at"] = iso(utc_now())
        appeal["status"] = "pending_review"
        appeal["statement_submitted"] = True
        await self.save()

        channel = interaction.channel
        if isinstance(channel, discord.TextChannel):
            embed = discord.Embed(
                title=f"{EMOJIS['chat']} Appeal Statement Submitted",
                description=statement.strip(),
                color=discord.Color.blue(),
                timestamp=utc_now(),
            )
            embed.add_field(name=f"{EMOJIS['user']} Submitted by", value=interaction.user.mention, inline=True)
            await channel.send(embed=embed)

        await interaction.response.send_message(
            f"{EMOJIS['tick']} Your appeal statement has been submitted for staff review.",
            ephemeral=True,
        )

    def appeal_is_staff(self, member: discord.Member) -> bool:
        return rank_of(member) >= 3

    async def open_staff_decision(self, interaction: discord.Interaction, appeal_id: str, decision: str):
        actor = interaction.user
        if not isinstance(actor, discord.Member) or not self.appeal_is_staff(actor):
            await interaction.response.send_message(
                f"{EMOJIS['close']} You need **Sr Mod+** to review warning appeals.",
                ephemeral=True,
            )
            return
        appeal = self.data.get("warning_appeals", {}).get(appeal_id)
        if not appeal or appeal.get("status") not in {"open", "pending_review"}:
            await interaction.response.send_message(
                f"{EMOJIS['info']} This appeal has already been resolved.",
                ephemeral=True,
            )
            return
        await interaction.response.send_modal(AppealDecisionModal(appeal_id, decision))

    async def resolve_warning_appeal(
        self,
        interaction: discord.Interaction,
        appeal_id: str,
        decision: str,
        decision_reason: str,
        new_punishment: str | None,
    ):
        actor = interaction.user
        if not isinstance(actor, discord.Member) or not self.appeal_is_staff(actor):
            await interaction.response.send_message(
                f"{EMOJIS['close']} You need **Sr Mod+** to resolve warning appeals.", ephemeral=True
            )
            return

        appeal = self.data.get("warning_appeals", {}).get(appeal_id)
        if not appeal or appeal.get("status") not in {"open", "pending_review"}:
            await interaction.response.send_message(
                f"{EMOJIS['info']} This appeal is already resolved.", ephemeral=True
            )
            return

        user_id = int(appeal["user_id"])
        warnings = self.data.get("warnings", {}).get(str(user_id), [])
        warning = next((w for w in warnings if w.get("case_id") == appeal["case_id"]), None)
        if warning is None:
            await interaction.response.send_message(
                f"{EMOJIS['close']} The original warning record could not be found.", ephemeral=True
            )
            return

        if decision == "modify":
            parsed = parse_modified_punishment(new_punishment or "")
            if parsed is None:
                await interaction.response.send_message(
                    f"{EMOJIS['close']} Invalid punishment. Use `1h`, `6h`, `1d`, `jail`, or `none`.",
                    ephemeral=True,
                )
                return
            new_type, new_seconds = parsed
        else:
            new_type, new_seconds = (None, None)

        member = interaction.guild.get_member(user_id) if interaction.guild else None
        if member is None and interaction.guild:
            try:
                member = await interaction.guild.fetch_member(user_id)
            except (discord.NotFound, discord.HTTPException):
                member = None

        # Preserve the original values for the audit trail.
        old_punishment = {
            "type": warning.get("escalation_type", "none"),
            "seconds": warning.get("escalation_seconds"),
        }

        try:
            if decision == "modify" and member is not None:
                await self.apply_warning_punishment_change(
                    member,
                    warning,
                    new_type,
                    new_seconds,
                    decision_reason,
                )
            elif decision == "remove":
                await self.remove_warning_with_recalculation(member, warning, decision_reason, source="appeal", actor_id=actor.id)
        except (discord.Forbidden, discord.HTTPException, RuntimeError) as exc:
            await interaction.response.send_message(
                f"{EMOJIS['close']} I could not apply the selected decision: `{type(exc).__name__}`",
                ephemeral=True,
            )
            return

        appeal["status"] = "resolved"
        appeal["decision"] = decision
        appeal["decision_reason"] = decision_reason.strip()
        appeal["reviewer_id"] = actor.id
        appeal["resolved_at"] = iso(utc_now())
        if decision == "modify":
            appeal["new_punishment"] = {"type": new_type, "seconds": new_seconds}
            warning["modified_punishment"] = {"type": new_type, "seconds": new_seconds}
            warning["modified_at"] = iso(utc_now())
            warning["modified_by"] = actor.id
            warning["modified_reason"] = decision_reason.strip()

        record_case_id = next_case_id(self.data)
        record = self.create_record(
            record_case_id,
            "warning_appeal",
            user_id,
            actor.id,
            decision_reason.strip(),
            outcome="Success",
            appeal_id=appeal_id,
            original_case_id=appeal["case_id"],
            warning_number=warning.get("warning_number"),
            original_moderator_id=appeal.get("original_moderator_id"),
            decision=decision,
            original_reason=appeal.get("original_reason"),
            appeal_statement=appeal.get("statement"),
            new_punishment={"type": new_type, "seconds": new_seconds} if decision == "modify" else None,
            old_punishment=old_punishment,
            reviewer_id=actor.id,
            ticket_id=appeal.get("ticket_id"),
            ticket_channel_id=appeal.get("ticket_channel_id"),
        )
        await self.save()

        evidence_path = Path(appeal["evidence_path"]) if appeal.get("evidence_path") else None
        await self.send_log(record, evidence_path)

        # Update the warning's appeal status and keep all evidence/case records.
        warning["appeal_status"] = "resolved"
        warning["appeal_decision"] = decision
        warning["appeal_decision_reason"] = decision_reason.strip()
        warning["appeal_reviewed_by"] = actor.id
        warning["appeal_resolved_at"] = iso(utc_now())

        support = self.bot.get_cog("Support")
        if support is not None and hasattr(support, "tickets"):
            ticket_record = support.tickets.get(str(appeal.get("ticket_channel_id")))
            if ticket_record is not None:
                ticket_record["appeal_id"] = appeal_id
                ticket_record["original_case_id"] = appeal["case_id"]
                ticket_record["warning_number"] = warning.get("warning_number")
                ticket_record["decision"] = decision
                ticket_record["decision_reason"] = decision_reason.strip()
                ticket_record["reviewer_id"] = actor.id
                ticket_record["actions"].append({
                    "action": "Warning Appeal Resolved",
                    "actor_id": actor.id,
                    "decision": decision,
                    "reason": decision_reason.strip(),
                    "timestamp": iso(utc_now()),
                })
                support.save()
        await self.save()

        # Notify the appellant and leave the ticket accessible for the existing ticket lifecycle.
        user = self.bot.get_user(user_id)
        if user is None:
            try:
                user = await self.bot.fetch_user(user_id)
            except (discord.NotFound, discord.HTTPException):
                user = None
        decision_label = {"uphold": "Warning Upheld", "modify": "Warning Modified", "remove": "Warning Removed"}[decision]
        dm_embed = discord.Embed(
            title=f"{EMOJIS['mod']} Warning Appeal Decision",
            description=f"**{decision_label}**\n\n{decision_reason.strip()}",
            color=discord.Color.green() if decision == "remove" else discord.Color.orange(),
        )
        dm_embed.add_field(name=f"{EMOJIS['folder']} Original Case", value=f"`{appeal['case_id']}`", inline=True)
        dm_embed.add_field(name=f"{EMOJIS['folder']} Appeal ID", value=f"`{appeal_id}`", inline=True)
        if decision == "modify":
            dm_embed.add_field(
                name=f"{EMOJIS['edit']} New Punishment",
                value=(new_type if new_type != "timeout" else f"timeout {duration_text(new_seconds or 0)}"),
                inline=False,
            )
        try:
            if user:
                await user.send(embed=dm_embed)
        except discord.HTTPException:
            pass

        if isinstance(interaction.channel, discord.TextChannel):
            channel_embed = discord.Embed(
                title=f"{EMOJIS['tick']} Appeal Resolved",
                description=f"**Decision:** {decision_label}\n**Reason:** {decision_reason.strip()}",
                color=discord.Color.green() if decision == "remove" else discord.Color.orange(),
            )
            channel_embed.add_field(name=f"{EMOJIS['user']} Reviewed by", value=actor.mention, inline=True)
            channel_embed.add_field(name=f"{EMOJIS['folder']} Appeal ID", value=f"`{appeal_id}`", inline=True)
            await interaction.channel.send(embed=channel_embed)

        await interaction.response.send_message(
            f"{EMOJIS['tick']} Appeal resolved: **{decision_label}**.",
            ephemeral=True,
        )

    async def apply_warning_punishment_change(
        self,
        member: discord.Member,
        warning: dict,
        new_type: str,
        new_seconds: int | None,
        reason: str,
    ):
        # Remove punishment that was directly attached to this warning when tracked.
        old_type = warning.get("escalation_type")
        old_until = parse_iso(warning.get("timeout_until"))
        if old_type == "jail" and new_type != "jail":
            await self.remove_warning_jail_if_source(member, warning)
        if old_type == "timeout" and old_until and member.timed_out_until:
            current = member.timed_out_until
            if abs((current - old_until).total_seconds()) <= 5:
                await member.timeout(None, reason=f"Chatly warning appeal modification: {reason}")

        if new_type == "timeout":
            await member.timeout(
                timedelta(seconds=int(new_seconds or 0)),
                reason=f"Chatly warning appeal modification: {reason}",
            )
            warning["escalation_type"] = "timeout"
            warning["escalation_seconds"] = int(new_seconds or 0)
            warning["timeout_until"] = iso(utc_now() + timedelta(seconds=int(new_seconds or 0)))
        elif new_type == "jail":
            await self.apply_jail(member, f"Warning appeal modified to jail: {reason}")
            warning["escalation_type"] = "jail"
            warning["escalation_seconds"] = None
            warning["jail_trigger_case_id"] = warning.get("case_id")
        else:
            warning["escalation_type"] = "none"
            warning["escalation_seconds"] = None
            warning["timeout_until"] = None
            await self.remove_warning_jail_if_source(member, warning)


    async def remove_warning_jail_if_source(self, member: discord.Member | None, warning: dict):
        if member is None:
            return
        snapshot = self.data.get("role_snapshots", {}).get(str(member.id), {})
        if snapshot.get("type") != "jail" or snapshot.get("source") != "warning":
            return
        if snapshot.get("source_case_id") != warning.get("case_id"):
            return
        jail_role = member.guild.get_role(JAIL_ROLE_ID)
        if jail_role and jail_role in member.roles:
            try:
                await member.remove_roles(jail_role, reason="Warning appeal removed warning-triggered jail")
            except (discord.Forbidden, discord.HTTPException):
                return
        bot_member = member.guild.me
        if bot_member:
            await restore_roles(member, snapshot.get("roles", []), bot_member.top_role)
        self.data["role_snapshots"].pop(str(member.id), None)

    async def recalculate_warning_escalation(self, member: discord.Member | None):
        if member is None:
            return
        active = get_active_warnings(self.data, member.id)
        if len(active) < 3:
            snapshot = self.data.get("role_snapshots", {}).get(str(member.id), {})
            if snapshot.get("type") == "jail" and snapshot.get("source") == "warning":
                await self.remove_warning_jail_if_source(member, snapshot.get("source_case_warning") or {})
            return
        # Three or more active warnings require warning-triggered jail.
        jail_warning = max(active, key=lambda w: int(w.get("warning_number", 0)))
        jail_role = member.guild.get_role(JAIL_ROLE_ID)
        if jail_role and jail_role not in member.roles:
            snapshot = self.data.get("role_snapshots", {}).get(str(member.id))
            if not snapshot or snapshot.get("type") != "jail":
                await self.apply_jail(
                    member,
                    f"Warning escalation recalculation: {len(active)} active warnings",
                    source="warning",
                    source_case_id=jail_warning.get("case_id"),
                )
            jail_warning["escalation_type"] = "jail"
            jail_warning["jail_trigger_case_id"] = jail_warning.get("case_id")

    async def remove_warning_with_recalculation(
        self,
        member: discord.Member | None,
        warning: dict,
        reason: str,
        source: str,
        actor_id: int | None = None,
    ):
        warning["removed"] = True
        warning["removed_at"] = iso(utc_now())
        warning["removed_by"] = actor_id
        warning["removed_reason"] = reason
        warning["removed_source"] = source
        if warning.get("current_appeal_id"):
            warning["appeal_status"] = "resolved"
        if member is not None:
            old_until = parse_iso(warning.get("timeout_until"))
            if warning.get("escalation_type") == "timeout" and old_until and member.timed_out_until:
                if abs((member.timed_out_until - old_until).total_seconds()) <= 5:
                    await member.timeout(None, reason=f"Chatly warning removed: {reason}")
            await self.remove_warning_jail_if_source(member, warning)
            await self.recalculate_warning_escalation(member)

    async def open_appeal_abuse(self, interaction: discord.Interaction, appeal_id: str):
        actor = interaction.user
        if not isinstance(actor, discord.Member) or not self.appeal_is_staff(actor):
            await interaction.response.send_message(
                f"{EMOJIS['close']} You need **Sr Mod+** to apply appeal-abuse action.",
                ephemeral=True,
            )
            return
        appeal = self.data.get("warning_appeals", {}).get(appeal_id)
        if not appeal or appeal.get("status") not in {"open", "pending_review"}:
            await interaction.response.send_message(
                f"{EMOJIS['info']} This appeal is already resolved.", ephemeral=True
            )
            return
        await interaction.response.send_modal(AppealAbuseModal(appeal_id))

    async def apply_warning_appeal_abuse(
        self,
        interaction: discord.Interaction,
        appeal_id: str,
        duration_value: str,
        reason: str,
    ):
        actor = interaction.user
        if not isinstance(actor, discord.Member) or not self.appeal_is_staff(actor):
            await interaction.response.send_message(
                f"{EMOJIS['close']} You need **Sr Mod+** to apply appeal-abuse action.", ephemeral=True
            )
            return
        appeal = self.data.get("warning_appeals", {}).get(appeal_id)
        if not appeal or appeal.get("status") not in {"open", "pending_review"}:
            await interaction.response.send_message(
                f"{EMOJIS['info']} This appeal is already resolved.", ephemeral=True
            )
            return
        seconds = parse_duration(duration_value)
        if seconds is None or not (WARNING_APPEAL_ABUSE_MIN <= seconds <= WARNING_APPEAL_ABUSE_MAX):
            await interaction.response.send_message(
                f"{EMOJIS['close']} Use an additional timeout between **1h and 6h**.", ephemeral=True
            )
            return

        member = interaction.guild.get_member(int(appeal["user_id"])) if interaction.guild else None
        if member is None:
            await interaction.response.send_message(
                f"{EMOJIS['close']} The appellant is no longer in Chatly, so the additional timeout cannot be applied.",
                ephemeral=True,
            )
            return
        try:
            now = utc_now()
            current_until = member.timed_out_until
            base_until = current_until if current_until and current_until > now else now
            new_until = min(base_until + timedelta(seconds=seconds), now + timedelta(seconds=MAX_TIMEOUT_SECONDS))
            await member.timeout(new_until, reason=f"Chatly appeal abuse: {reason}")
        except (discord.Forbidden, discord.HTTPException) as exc:
            await interaction.response.send_message(
                f"{EMOJIS['close']} I could not apply the additional timeout: `{type(exc).__name__}`",
                ephemeral=True,
            )
            return

        appeal["status"] = "resolved"
        appeal["decision"] = "uphold"
        appeal["decision_reason"] = reason.strip()
        appeal["reviewer_id"] = actor.id
        appeal["resolved_at"] = iso(utc_now())
        appeal["abuse_timeout_seconds"] = seconds

        support = self.bot.get_cog("Support")
        if support is not None and hasattr(support, "tickets"):
            ticket_record = support.tickets.get(str(appeal.get("ticket_channel_id")))
            if ticket_record is not None:
                ticket_record["appeal_id"] = appeal_id
                ticket_record["original_case_id"] = appeal["case_id"]
                ticket_record["warning_number"] = appeal.get("warning_number")
                ticket_record["decision"] = "uphold"
                ticket_record["decision_reason"] = reason.strip()
                ticket_record["reviewer_id"] = actor.id
                ticket_record["abuse_timeout_seconds"] = seconds
                ticket_record["actions"].append({
                    "action": "Warning Appeal Abuse Action",
                    "actor_id": actor.id,
                    "timeout_seconds": seconds,
                    "reason": reason.strip(),
                    "timestamp": iso(utc_now()),
                })
                support.save()

        record_case_id = next_case_id(self.data)
        record = self.create_record(
            record_case_id,
            "warning_appeal",
            member.id,
            actor.id,
            reason.strip(),
            outcome="Success",
            appeal_id=appeal_id,
            original_case_id=appeal["case_id"],
            warning_number=appeal.get("warning_number"),
            original_moderator_id=appeal.get("original_moderator_id"),
            decision="uphold",
            appeal_statement=appeal.get("statement"),
            abuse_timeout_seconds=seconds,
            abuse_action=True,
            ticket_id=appeal.get("ticket_id"),
            ticket_channel_id=appeal.get("ticket_channel_id"),
        )
        await self.save()
        await self.send_log(record, Path(appeal["evidence_path"]) if appeal.get("evidence_path") else None)

        user = self.bot.get_user(member.id)
        try:
            if user:
                await user.send(
                    embed=discord.Embed(
                        title=f"{EMOJIS['exclaim']} Warning Appeal Decision",
                        description=(
                            f"Your appeal was **upheld**.\n\n{reason.strip()}\n\n"
                            f"An additional timeout of **{duration_text(seconds)}** was applied due to appeal abuse."
                        ),
                        color=discord.Color.red(),
                    )
                )
        except discord.HTTPException:
            pass

        if isinstance(interaction.channel, discord.TextChannel):
            await interaction.channel.send(
                embed=discord.Embed(
                    title=f"{EMOJIS['exclaim']} Appeal Abuse Action",
                    description=f"An additional **{duration_text(seconds)}** timeout was applied.\n\n**Reason:** {reason.strip()}",
                    color=discord.Color.red(),
                )
            )
        await interaction.response.send_message(
            f"{EMOJIS['tick']} Appeal upheld and additional timeout applied.", ephemeral=True
        )

    async def allow_another_warning_appeal(self, interaction: discord.Interaction, appeal_id: str):
        actor = interaction.user
        if not isinstance(actor, discord.Member) or not self.appeal_is_staff(actor):
            await interaction.response.send_message(
                f"{EMOJIS['close']} You need **Sr Mod+** to allow another appeal.", ephemeral=True
            )
            return
        appeal = self.data.get("warning_appeals", {}).get(appeal_id)
        if not appeal or appeal.get("status") != "resolved":
            await interaction.response.send_message(
                f"{EMOJIS['info']} Another appeal can only be allowed after a previous appeal is resolved.",
                ephemeral=True,
            )
            return
        warning = next(
            (
                w for w in self.data.get("warnings", {}).get(str(appeal["user_id"]), [])
                if w.get("case_id") == appeal["case_id"]
            ),
            None,
        )
        if warning is None:
            await interaction.response.send_message(
                f"{EMOJIS['close']} The original warning could not be found.", ephemeral=True
            )
            return
        warning["appeal_reopened"] = True
        warning["appeal_status"] = "reopened"
        warning["appeal_reopened_by"] = actor.id
        warning["appeal_reopened_at"] = iso(utc_now())
        await self.save()
        await interaction.response.send_message(
            f"{EMOJIS['refresh']} Another appeal has been permitted for warning **#{warning['warning_number']}**.",
            ephemeral=True,
        )
        if isinstance(interaction.channel, discord.TextChannel):
            await interaction.channel.send(
                f"{EMOJIS['refresh']} <@{appeal['user_id']}> may submit another appeal for this warning."
            )

    # -------------------------
    # WARN
    # -------------------------

    @app_commands.command(name="warn", description="Warn a member.")
    @app_commands.describe(
        target="Member to warn",
        reason="Reason for the warning",
        evidence="Required image evidence",
    )
    async def warn(
        self,
        interaction: discord.Interaction,
        target: discord.Member,
        reason: str,
        evidence: discord.Attachment,
    ):
        actor = interaction.user
        if not isinstance(actor, discord.Member):
            await interaction.response.send_message("Server only.", ephemeral=True)
            return

        allowed, message = self.permission_result(actor, 1)
        if not allowed:
            await interaction.response.send_message(message, ephemeral=True)
            return

        allowed, message = self.member_from_interaction(interaction, target)
        if not allowed:
            await interaction.response.send_message(message, ephemeral=True)
            return

        if not evidence_is_image(evidence):
            await interaction.response.send_message(
                f"{EMOJIS['close']} Evidence must be an uploaded image.",
                ephemeral=True,
            )
            return

        remaining = cooldown_remaining(
            self.data, "warn", actor.id, interaction.guild.id
        )
        if remaining:
            await interaction.response.send_message(
                f"{EMOJIS['timeout']} `/warn` cooldown: **{format_remaining(remaining)}** remaining.",
                ephemeral=True,
            )
            return

        if not reason.strip():
            await interaction.response.send_message(
                f"{EMOJIS['close']} A reason is required.",
                ephemeral=True,
            )
            return

        case_id = next_case_id(self.data)

        try:
            evidence_path = await archive_evidence(evidence, case_id)
        except Exception:
            await interaction.response.send_message(
                f"{EMOJIS['close']} I could not save the evidence image.",
                ephemeral=True,
            )
            return

        active_count = len(get_active_warnings(self.data, target.id)) + 1
        warning_timeout = WARNING_TIMEOUTS.get(active_count)

        # Jr Mod requires Mod+ approval.
        if rank_of(actor) == 1:
            await self.create_approval_request(
                interaction=interaction,
                action="warn",
                target=target,
                reason=reason,
                evidence_path=evidence_path,
                required_rank=2,
                extra={"warning_timeout": warning_timeout, "case_id": case_id},
            )
            return

        await interaction.response.defer(ephemeral=True)

        try:
            await self.execute_warn(
                interaction=interaction,
                target=target,
                reason=reason,
                evidence_path=evidence_path,
                requester_id=actor.id,
                case_id=case_id,
                approval_status="Direct",
                approver_id=None,
                warning_timeout_override=warning_timeout,
            )
        except discord.Forbidden:
            await interaction.followup.send(
                f"{EMOJIS['close']} Discord denied the moderation action. No Mod Points were awarded.",
                ephemeral=True,
            )
            return
        except discord.HTTPException:
            await interaction.followup.send(
                f"{EMOJIS['close']} The moderation action failed. No Mod Points were awarded.",
                ephemeral=True,
            )
            return

        set_cooldown(self.data, "warn", actor.id, interaction.guild.id)
        await self.save()

        await interaction.followup.send(
            f"{EMOJIS['tick']} Warning issued to **{target.display_name}**."
        )

    async def execute_warn(
        self,
        interaction: discord.Interaction,
        target: discord.Member,
        reason: str,
        evidence_path: Path,
        requester_id: int,
        case_id: str,
        approval_status: str,
        approver_id: int | None,
        warning_timeout_override: int | None = None,
    ):
        user_key = str(target.id)
        warnings = self.data["warnings"].setdefault(user_key, [])

        warning_number = max(
            [int(w.get("warning_number", 0)) for w in warnings] or [0]
        ) + 1

        expires_at = utc_now() + timedelta(days=WARNING_EXPIRY_DAYS)

        warning = {
            "case_id": case_id,
            "warning_number": warning_number,
            "reason": reason,
            "moderator_id": requester_id,
            "created_at": iso(utc_now()),
            "expires_at": iso(expires_at),
            "removed": False,
            "removed_at": None,
            "removed_by": None,
            "removed_reason": None,
            "evidence_path": str(evidence_path),
            "appeal_count": 0,
            "current_appeal_id": None,
            "appeal_reopened": False,
            "appeal_status": None,
            "escalation_type": "none",
            "escalation_seconds": None,
            "timeout_until": None,
            "jail_trigger_case_id": None,
        }
        warnings.append(warning)

        active_count = len(get_active_warnings(self.data, target.id))

        timeout_seconds = warning_timeout_override
        if timeout_seconds is None:
            timeout_seconds = WARNING_TIMEOUTS.get(active_count)

        # Warning 1 / 2: timeout.
        if timeout_seconds:
            await target.timeout(
                timedelta(seconds=timeout_seconds),
                reason=f"Chatly Warning #{warning_number}: {reason}",
            )
            warning["escalation_type"] = "timeout"
            warning["escalation_seconds"] = timeout_seconds
            warning["timeout_until"] = iso(utc_now() + timedelta(seconds=timeout_seconds))

        # Warning 3: jail, but no automatic ban.
        auto_jail = active_count >= 3 and JAIL_ROLE_ID != 0
        if auto_jail:
            await self.apply_jail(
                target,
                reason=f"Third active warning: {reason}",
                source="warning",
                source_case_id=case_id,
            )
            warning["escalation_type"] = "jail"
            warning["jail_trigger_case_id"] = case_id

        record = self.create_record(
            case_id,
            "warn",
            target.id,
            requester_id,
            reason,
            warning_number=warning_number,
            timeout_seconds=timeout_seconds,
            approval_status=approval_status,
            approver_id=approver_id,
            evidence_filename=evidence_path.name,
        )

        if active_count >= 3:
            record["escalation"] = (
                "Third active warning reached. User may appeal jail; "
                "no automatic ban was issued."
            )

        await self.save()
        await self.send_log(record, evidence_path)
        await self.award_points(
            requester_id,
            "warn",
            target.id,
            case_id,
        )

        try:
            warning_embed = discord.Embed(
                title=f"{EMOJIS['exclaim']} Chatly Warning",
                description=(
                    f"You have received **Warning #{warning_number}** in Chatly.\n\n"
                    f"{EMOJIS['info']} **Reason:** {reason}\n"
                    f"{EMOJIS['folder']} **Case ID:** `{case_id}`\n"
                    f"{EMOJIS['info']} **Expires:** <t:{int(expires_at.timestamp())}:R>\n\n"
                    f"{EMOJIS['flag']} You may appeal this warning using the button below."
                ),
                color=discord.Color.orange(),
            )
            warning_embed.set_footer(text="Chatly Moderation")
            evidence_file = discord.File(str(evidence_path), filename=evidence_path.name) if evidence_path.exists() else None
            if evidence_file:
                warning_embed.set_image(url=f"attachment://{evidence_path.name}")
            await target.send(
                embed=warning_embed,
                file=evidence_file,
                view=WarningAppealView(case_id, target.id),
            )
        except discord.HTTPException:
            pass

    # -------------------------
    # WARNINGS
    # -------------------------

    @app_commands.command(name="warnings", description="View a member's warning history.")
    @app_commands.describe(target="Member to inspect")
    async def warnings(
        self,
        interaction: discord.Interaction,
        target: discord.Member,
    ):
        actor = interaction.user
        if not isinstance(actor, discord.Member):
            await interaction.response.send_message("Server only.", ephemeral=True)
            return

        allowed, message = self.permission_result(actor, 1)
        if not allowed:
            await interaction.response.send_message(message, ephemeral=True)
            return

        all_warnings = get_all_warnings(self.data, target.id)
        if not all_warnings:
            await interaction.response.send_message(
                f"**{target.display_name}** has no warning history.",
                ephemeral=True,
            )
            return

        active = get_active_warnings(self.data, target.id)
        lines = []

        for warning in all_warnings[-10:]:
            status = "Active"
            if warning.get("removed"):
                status = "Removed"
            elif parse_iso(warning.get("expires_at")) and parse_iso(warning["expires_at"]) <= utc_now():
                status = "Expired"

            lines.append(
                f"**#{warning['warning_number']}** • {status}\n"
                f"Reason: {warning['reason']}\n"
                f"Moderator: <@{warning['moderator_id']}>\n"
                f"Created: <t:{int(parse_iso(warning['created_at']).timestamp())}:f>"
            )

        embed = discord.Embed(
            title=f"{EMOJIS['exclaim']} Warning History",
            description="\n\n".join(lines),
            color=discord.Color.orange(),
        )
        embed.set_footer(text=f"Active warnings: {len(active)}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="clearwarnings", description="Clear all active warnings from a member.")
    @app_commands.describe(
        target="Member whose active warnings should be cleared",
        reason="Reason for clearing the warnings",
    )
    async def clearwarnings(
        self,
        interaction: discord.Interaction,
        target: discord.Member,
        reason: str,
    ):
        actor = interaction.user
        if not isinstance(actor, discord.Member):
            await interaction.response.send_message("Server only.", ephemeral=True)
            return

        allowed, message = self.permission_result(actor, 3)
        if not allowed:
            await interaction.response.send_message(message, ephemeral=True)
            return

        count = 0
        for warning in self.data["warnings"].get(str(target.id), []):
            if not warning.get("removed") and (
                parse_iso(warning.get("expires_at")) is None
                or parse_iso(warning["expires_at"]) > utc_now()
            ):
                warning["removed"] = True
                warning["removed_at"] = iso(utc_now())
                warning["removed_by"] = actor.id
                warning["removed_reason"] = reason
                warning["removed_source"] = "clearwarnings"
                count += 1

        case_id = next_case_id(self.data)
        record = self.create_record(
            case_id,
            "clearwarnings",
            target.id,
            actor.id,
            reason,
            cleared_count=count,
        )
        await self.save()
        await self.send_log(record)
        await self.recalculate_warning_escalation(target)
        await self.save()

        await interaction.response.send_message(
            f"{EMOJIS['tick']} Cleared **{count}** active warning(s) from **{target.display_name}**.",
            ephemeral=True,
        )

    @remove.command(name="warn", description="Remove one specific warning.")
    @app_commands.describe(
        target="Member whose warning should be removed",
        warning_number="Warning number to remove",
        reason="Reason for removing the warning",
    )
    async def remove_warn(
        self,
        interaction: discord.Interaction,
        target: discord.Member,
        warning_number: int,
        reason: str,
    ):
        actor = interaction.user
        if not isinstance(actor, discord.Member):
            await interaction.response.send_message("Server only.", ephemeral=True)
            return

        allowed, message = self.permission_result(actor, 3)
        if not allowed:
            await interaction.response.send_message(message, ephemeral=True)
            return

        warnings = self.data["warnings"].get(str(target.id), [])
        found = None

        for warning in warnings:
            if int(warning["warning_number"]) == warning_number and not warning.get("removed"):
                found = warning
                break

        if found is None:
            await interaction.response.send_message(
                f"{EMOJIS['close']} That active warning was not found.",
                ephemeral=True,
            )
            return

        found["removed"] = True
        found["removed_at"] = iso(utc_now())
        found["removed_by"] = actor.id
        found["removed_reason"] = reason
        found["removed_source"] = "remove_warn"

        case_id = next_case_id(self.data)
        record = self.create_record(
            case_id,
            "remove_warn",
            target.id,
            actor.id,
            reason,
            warning_number=warning_number,
        )

        await self.save()
        await self.send_log(record)
        await self.recalculate_warning_escalation(target)
        await self.save()

        await interaction.response.send_message(
            f"{EMOJIS['tick']} Warning **#{warning_number}** removed.",
            ephemeral=True,
        )

    # -------------------------
    # TIMEOUT
    # -------------------------

    @app_commands.command(name="timeout", description="Timeout a member.")
    @app_commands.describe(
        target="Member to timeout",
        duration="Examples: 30m, 2h, 1d, 1w",
        reason="Reason for the timeout",
    )
    async def timeout(
        self,
        interaction: discord.Interaction,
        target: discord.Member,
        duration: str,
        reason: str,
    ):
        actor = interaction.user
        if not isinstance(actor, discord.Member):
            await interaction.response.send_message("Server only.", ephemeral=True)
            return

        allowed, message = self.permission_result(actor, 1)
        if not allowed:
            await interaction.response.send_message(message, ephemeral=True)
            return

        allowed, message = self.member_from_interaction(interaction, target)
        if not allowed:
            await interaction.response.send_message(message, ephemeral=True)
            return

        seconds = parse_duration(duration)
        if seconds is None:
            await interaction.response.send_message(
                f"{EMOJIS['close']} Invalid duration. Use values like `30m`, `2h`, `1d`, or `1w` (max 28d).",
                ephemeral=True,
            )
            return

        remaining = cooldown_remaining(
            self.data, "timeout", actor.id, interaction.guild.id
        )
        if remaining:
            await interaction.response.send_message(
                f"{EMOJIS['timeout']} `/timeout` cooldown: **{format_remaining(remaining)}** remaining.",
                ephemeral=True,
            )
            return

        if rank_of(actor) == 1:
            case_id = next_case_id(self.data)
            await self.create_approval_request(
                interaction=interaction,
                action="timeout",
                target=target,
                reason=reason,
                evidence_path=None,
                required_rank=2,
                extra={"timeout_seconds": seconds, "case_id": case_id},
            )
            return

        await interaction.response.defer(ephemeral=True)

        try:
            await target.timeout(
                timedelta(seconds=seconds),
                reason=reason,
            )
        except (discord.Forbidden, discord.HTTPException):
            await interaction.followup.send(
                f"{EMOJIS['close']} The timeout failed. No Mod Points were awarded."
            )
            return

        case_id = next_case_id(self.data)
        record = self.create_record(
            case_id,
            "timeout",
            target.id,
            actor.id,
            reason,
            timeout_seconds=seconds,
            approval_status="Direct",
        )

        await self.save()
        await self.send_log(record)
        await self.award_points(actor.id, "timeout", target.id, case_id)

        set_cooldown(self.data, "timeout", actor.id, interaction.guild.id)
        await self.save()

        await interaction.followup.send(
            f"{EMOJIS['tick']} **{target.display_name}** timed out for **{duration_text(seconds)}**."
        )

    @app_commands.command(name="untimeout", description="Remove a member's timeout.")
    @app_commands.describe(
        target="Member to untimeout",
        reason="Reason for removing the timeout",
    )
    async def untimeout(
        self,
        interaction: discord.Interaction,
        target: discord.Member,
        reason: str,
    ):
        actor = interaction.user
        if not isinstance(actor, discord.Member):
            await interaction.response.send_message("Server only.", ephemeral=True)
            return

        allowed, message = self.permission_result(actor, 1)
        if not allowed:
            await interaction.response.send_message(message, ephemeral=True)
            return

        if rank_of(actor) == 1:
            case_id = next_case_id(self.data)
            await self.create_approval_request(
                interaction=interaction,
                action="untimeout",
                target=target,
                reason=reason,
                evidence_path=None,
                required_rank=2,
                extra={"case_id": case_id},
            )
            return

        try:
            await target.timeout(None, reason=reason)
        except (discord.Forbidden, discord.HTTPException):
            await interaction.response.send_message(
                f"{EMOJIS['close']} I could not remove the timeout.",
                ephemeral=True,
            )
            return

        case_id = next_case_id(self.data)
        record = self.create_record(
            case_id,
            "untimeout",
            target.id,
            actor.id,
            reason,
            approval_status="Direct",
        )
        await self.save()
        await self.send_log(record)

        await interaction.response.send_message(
            f"{EMOJIS['tick']} Timeout removed from **{target.display_name}**.",
            ephemeral=True,
        )

    # -------------------------
    # BAN / UNBAN
    # -------------------------

    @app_commands.command(name="ban", description="Ban a member.")
    @app_commands.describe(
        target="Member to ban",
        reason="Reason for the ban",
        evidence="Required image evidence",
    )
    async def ban(
        self,
        interaction: discord.Interaction,
        target: discord.Member,
        reason: str,
        evidence: discord.Attachment,
    ):
        actor = interaction.user
        if not isinstance(actor, discord.Member):
            await interaction.response.send_message("Server only.", ephemeral=True)
            return

        actor_rank = rank_of(actor)

        if actor_rank < 4:
            await interaction.response.send_message(
                f"{EMOJIS['close']} Only **Admin+** staff can request a ban.",
                ephemeral=True,
            )
            return

        if target.id == OWNER_ID:
            await interaction.response.send_message(
                f"{EMOJIS['close']} The Owner is protected from bans.",
                ephemeral=True,
            )
            return

        if actor_rank < 8:
            allowed, message = self.member_from_interaction(interaction, target)
            if not allowed:
                await interaction.response.send_message(message, ephemeral=True)
                return

        if not evidence_is_image(evidence):
            await interaction.response.send_message(
                f"{EMOJIS['close']} Ban evidence must be an uploaded image.",
                ephemeral=True,
            )
            return

        remaining = cooldown_remaining(
            self.data, "ban", actor.id, interaction.guild.id
        )
        if remaining:
            await interaction.response.send_message(
                f"{EMOJIS['timeout']} `/ban` server cooldown: **{format_remaining(remaining)}** remaining.",
                ephemeral=True,
            )
            return

        case_id = next_case_id(self.data)
        try:
            evidence_path = await archive_evidence(evidence, case_id)
        except Exception:
            await interaction.response.send_message(
                f"{EMOJIS['close']} I could not save the evidence image.",
                ephemeral=True,
            )
            return

        # Admin and Manager require Executive+ approval.
        # Executive, Co Owner and Owner can ban directly.
        if actor_rank < 6:
            await self.create_approval_request(
                interaction=interaction,
                action="ban",
                target=target,
                reason=reason,
                evidence_path=evidence_path,
                required_rank=6,
                extra={"case_id": case_id},
            )
            return

        await interaction.response.defer(ephemeral=True)

        try:
            await interaction.guild.ban(
                target,
                reason=reason,
                delete_message_days=0,
            )
        except (discord.Forbidden, discord.HTTPException):
            await interaction.followup.send(
                f"{EMOJIS['close']} The ban failed. No Mod Points were awarded."
            )
            return

        record = self.create_record(
            case_id,
            "ban",
            target.id,
            actor.id,
            reason,
            approval_status="Direct",
            evidence_filename=evidence_path.name,
        )

        await self.save()
        await self.send_log(record, evidence_path)
        await self.award_points(actor.id, "ban", target.id, case_id)

        set_cooldown(self.data, "ban", actor.id, interaction.guild.id)
        await self.save()

        try:
            if BAN_APPEAL_SERVER_URL.startswith("http"):
                await target.send(
                    f"You have been permanently banned from **Chatly**.\n\n"
                    f"**Reason:** {reason}\n\n"
                    f"Ban appeals: {BAN_APPEAL_SERVER_URL}"
                )
        except discord.HTTPException:
            pass

        await interaction.followup.send(
            f"{EMOJIS['tick']} **{target.display_name}** was permanently banned."
        )

    @app_commands.command(name="unban", description="Unban a user.")
    @app_commands.describe(
        user_id="Discord user ID",
        reason="Reason for the unban",
    )
    async def unban(
        self,
        interaction: discord.Interaction,
        user_id: str,
        reason: str,
    ):
        actor = interaction.user
        if not isinstance(actor, discord.Member):
            await interaction.response.send_message("Server only.", ephemeral=True)
            return

        allowed, message = self.permission_result(actor, 4)
        if not allowed:
            await interaction.response.send_message(message, ephemeral=True)
            return

        try:
            target_id = int(user_id)
        except ValueError:
            await interaction.response.send_message(
                f"{EMOJIS['close']} Invalid user ID.",
                ephemeral=True,
            )
            return

        try:
            user = await self.bot.fetch_user(target_id)
            await interaction.guild.unban(user, reason=reason)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            await interaction.response.send_message(
                f"{EMOJIS['close']} I could not unban that user.",
                ephemeral=True,
            )
            return

        case_id = next_case_id(self.data)
        record = self.create_record(
            case_id,
            "unban",
            target_id,
            actor.id,
            reason,
            approval_status="Direct",
        )
        await self.save()
        await self.send_log(record)

        await interaction.response.send_message(
            f"{EMOJIS['tick']} <@{target_id}> has been unbanned.",
            ephemeral=True,
        )

    # -------------------------
    # JAIL
    # -------------------------

    async def apply_jail(
        self,
        target: discord.Member,
        reason: str,
        source: str = "manual",
        source_case_id: str | None = None,
    ):
        jail_role = target.guild.get_role(JAIL_ROLE_ID)
        if jail_role is None:
            raise RuntimeError("Jail role is not configured.")

        bot_member = target.guild.me
        if bot_member is None or jail_role >= bot_member.top_role:
            raise RuntimeError("Jail role is not below the bot's role.")

        key = str(target.id)

        if key not in self.data["role_snapshots"]:
            self.data["role_snapshots"][key] = {
                "type": "jail",
                "source": source,
                "source_case_id": source_case_id,
                "roles": [
                    role.id
                    for role in target.roles
                    if role != target.guild.default_role
                    and not role.managed
                    and role < bot_member.top_role
                ],
                "created_at": iso(utc_now()),
                "source_case_warning": {"case_id": source_case_id} if source == "warning" else None,
            }

        removable_roles = [
            role
            for role in target.roles
            if role != target.guild.default_role
            and not role.managed
            and role < bot_member.top_role
            and role != jail_role
        ]

        if removable_roles:
            await target.remove_roles(
                *removable_roles,
                reason=f"Chatly jail: {reason}",
            )

        if jail_role not in target.roles:
            await target.add_roles(
                jail_role,
                reason=f"Chatly jail: {reason}",
            )

    @app_commands.command(name="jail", description="Jail a member.")
    @app_commands.describe(
        target="Member to jail",
        reason="Reason for the jail",
    )
    async def jail(
        self,
        interaction: discord.Interaction,
        target: discord.Member,
        reason: str,
    ):
        actor = interaction.user
        if not isinstance(actor, discord.Member):
            await interaction.response.send_message("Server only.", ephemeral=True)
            return

        allowed, message = self.permission_result(actor, 3)
        if not allowed:
            await interaction.response.send_message(message, ephemeral=True)
            return

        allowed, message = self.member_from_interaction(interaction, target)
        if not allowed:
            await interaction.response.send_message(message, ephemeral=True)
            return

        remaining = cooldown_remaining(
            self.data, "jail", actor.id, interaction.guild.id
        )
        if remaining:
            await interaction.response.send_message(
                f"{EMOJIS['timeout']} `/jail` cooldown: **{format_remaining(remaining)}** remaining.",
                ephemeral=True,
            )
            return

        try:
            await self.apply_jail(target, reason)
        except (discord.Forbidden, discord.HTTPException, RuntimeError) as exc:
            await interaction.response.send_message(
                f"{EMOJIS['close']} Jail failed: `{type(exc).__name__}`",
                ephemeral=True,
            )
            return

        case_id = next_case_id(self.data)
        record = self.create_record(
            case_id,
            "jail",
            target.id,
            actor.id,
            reason,
            approval_status="Direct",
        )
        await self.save()
        await self.send_log(record)
        await self.award_points(actor.id, "jail", target.id, case_id)

        set_cooldown(self.data, "jail", actor.id, interaction.guild.id)
        await self.save()

        try:
            await target.send(
                f"You have been **jailed in Chatly**.\n\n"
                f"**Reason:** {reason}\n"
                f"Appeal in the jailed channel: "
                f"{f'<#{JAIL_CHANNEL_ID}>' if JAIL_CHANNEL_ID else 'Jail channel not configured yet.'}"
            )
        except discord.HTTPException:
            pass

        await interaction.response.send_message(
            f"{EMOJIS['tick']} **{target.display_name}** has been jailed.",
            ephemeral=True,
        )

    @app_commands.command(name="unjail", description="Release a jailed member.")
    @app_commands.describe(
        target="Member to unjail",
        reason="Reason for the unjail",
    )
    async def unjail(
        self,
        interaction: discord.Interaction,
        target: discord.Member,
        reason: str,
    ):
        actor = interaction.user
        if not isinstance(actor, discord.Member):
            await interaction.response.send_message("Server only.", ephemeral=True)
            return

        allowed, message = self.permission_result(actor, 3)
        if not allowed:
            await interaction.response.send_message(message, ephemeral=True)
            return

        jail_role = interaction.guild.get_role(JAIL_ROLE_ID)
        if jail_role and jail_role in target.roles:
            try:
                await target.remove_roles(jail_role, reason=reason)
            except (discord.Forbidden, discord.HTTPException):
                await interaction.response.send_message(
                    f"{EMOJIS['close']} I could not remove the jail role.",
                    ephemeral=True,
                )
                return

        snapshot = self.data["role_snapshots"].get(str(target.id), {})
        if snapshot.get("type") == "jail":
            bot_member = interaction.guild.me
            if bot_member:
                await restore_roles(
                    target,
                    snapshot.get("roles", []),
                    bot_member.top_role,
                )
            del self.data["role_snapshots"][str(target.id)]

        case_id = next_case_id(self.data)
        record = self.create_record(
            case_id,
            "unjail",
            target.id,
            actor.id,
            reason,
            approval_status="Direct",
        )
        await self.save()
        await self.send_log(record)

        await interaction.response.send_message(
            f"{EMOJIS['tick']} **{target.display_name}** has been released from jail.",
            ephemeral=True,
        )

    # -------------------------
    # SUS / CAPTCHA
    # -------------------------

    async def execute_sus(
        self,
        interaction: discord.Interaction,
        target: discord.Member,
        reason: str,
        requester_id: int,
        case_id: str,
        approval_status: str,
        approver_id: int | None,
    ):
        sus_role = interaction.guild.get_role(SUS_ROLE_ID)
        if sus_role is None:
            raise RuntimeError("SUS role is not configured.")

        bot_member = interaction.guild.me
        if bot_member is None or sus_role >= bot_member.top_role:
            raise RuntimeError("SUS role is not below the bot's role.")

        key = str(target.id)

        if key not in self.data["role_snapshots"]:
            self.data["role_snapshots"][key] = {
                "type": "sus",
                "roles": [
                    role.id
                    for role in target.roles
                    if role != interaction.guild.default_role
                    and not role.managed
                    and role < bot_member.top_role
                ],
                "created_at": iso(utc_now()),
            }

        removable_roles = [
            role
            for role in target.roles
            if role != interaction.guild.default_role
            and not role.managed
            and role < bot_member.top_role
            and role != sus_role
        ]

        if removable_roles:
            await target.remove_roles(
                *removable_roles,
                reason=f"Chatly suspicious account restriction: {reason}",
            )

        if sus_role not in target.roles:
            await target.add_roles(
                sus_role,
                reason=f"Chatly suspicious account restriction: {reason}",
            )

        record = self.create_record(
            case_id,
            "sus",
            target.id,
            requester_id,
            reason,
            approval_status=approval_status,
            approver_id=approver_id,
        )

        await self.save()
        await self.send_log(record)
        await self.award_points(requester_id, "sus", target.id, case_id)

        try:
            await target.send(
                "Your Chatly account has been temporarily restricted for verification.\n"
                "Complete the CAPTCHA in the CAPTCHA channel to restore your normal roles."
            )
        except discord.HTTPException:
            pass

    @app_commands.command(name="sus", description="Restrict a suspicious account to CAPTCHA verification.")
    @app_commands.describe(
        target="Member to restrict",
        reason="Reason for the restriction",
    )
    async def sus(
        self,
        interaction: discord.Interaction,
        target: discord.Member,
        reason: str,
    ):
        actor = interaction.user
        if not isinstance(actor, discord.Member):
            await interaction.response.send_message("Server only.", ephemeral=True)
            return

        actor_rank = rank_of(actor)
        if actor_rank < 2:
            await interaction.response.send_message(
                f"{EMOJIS['close']} You need **Mod+** to use `/sus`.",
                ephemeral=True,
            )
            return

        allowed, message = self.member_from_interaction(interaction, target)
        if not allowed:
            await interaction.response.send_message(message, ephemeral=True)
            return

        if SUS_ROLE_ID == 0 or CAPTCHA_CHANNEL_ID == 0:
            await interaction.response.send_message(
                f"{EMOJIS['close']} SUS role and CAPTCHA channel are not configured yet.",
                ephemeral=True,
            )
            return

        remaining = cooldown_remaining(
            self.data, "sus", actor.id, interaction.guild.id
        )
        if remaining:
            await interaction.response.send_message(
                f"{EMOJIS['timeout']} `/sus` cooldown: **{format_remaining(remaining)}** remaining.",
                ephemeral=True,
            )
            return

        case_id = next_case_id(self.data)

        if actor_rank == 2:
            await self.create_approval_request(
                interaction=interaction,
                action="sus",
                target=target,
                reason=reason,
                evidence_path=None,
                required_rank=3,
                extra={"case_id": case_id},
            )
            return

        try:
            await self.execute_sus(
                interaction=interaction,
                target=target,
                reason=reason,
                requester_id=actor.id,
                case_id=case_id,
                approval_status="Direct",
                approver_id=None,
            )
        except (discord.Forbidden, discord.HTTPException, RuntimeError):
            await interaction.response.send_message(
                f"{EMOJIS['close']} SUS restriction failed. No Mod Points were awarded.",
                ephemeral=True,
            )
            return

        set_cooldown(self.data, "sus", actor.id, interaction.guild.id)
        await self.save()

        await interaction.response.send_message(
            f"{EMOJIS['tick']} **{target.display_name}** has been placed into CAPTCHA verification.",
            ephemeral=True,
        )

    async def start_captcha(self, interaction: discord.Interaction):
        if CAPTCHA_CHANNEL_ID and interaction.channel_id != CAPTCHA_CHANNEL_ID:
            await interaction.response.send_message(
                f"Use the CAPTCHA channel <#{CAPTCHA_CHANNEL_ID}>.",
                ephemeral=True,
            )
            return

        snapshot = self.data["role_snapshots"].get(str(interaction.user.id))
        if not snapshot or snapshot.get("type") != "sus":
            await interaction.response.send_message(
                "You do not have an active CAPTCHA restriction.",
                ephemeral=True,
            )
            return

        code = uuid.uuid4().hex[:6].upper()

        self.data["sus_captchas"][str(interaction.user.id)] = {
            "code": code,
            "expires_at": iso(utc_now() + timedelta(minutes=10)),
        }
        await self.save()

        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"{EMOJIS['lock']} CAPTCHA Verification",
                description=f"Enter this code:\n\n**`{code}`**",
                color=discord.Color.green(),
            ),
            view=CaptchaPromptView(interaction.user.id),
            ephemeral=True,
        )

    async def handle_captcha_submission(
        self,
        interaction: discord.Interaction,
        user_id: int,
        answer: str,
    ):
        record = self.data["sus_captchas"].get(str(user_id))
        if not record:
            await interaction.response.send_message(
                "No active CAPTCHA challenge was found.",
                ephemeral=True,
            )
            return

        expires_at = parse_iso(record.get("expires_at"))
        if expires_at and expires_at <= utc_now():
            del self.data["sus_captchas"][str(user_id)]
            await self.save()
            await interaction.response.send_message(
                "This CAPTCHA expired. Start a new one.",
                ephemeral=True,
            )
            return

        if answer.strip().upper() != record["code"]:
            await interaction.response.send_message(
                f"{EMOJIS['close']} Incorrect CAPTCHA. You are still restricted.",
                ephemeral=True,
            )
            return

        member = interaction.guild.get_member(user_id)
        if member is None:
            await interaction.response.send_message(
                "You are no longer in Chatly.",
                ephemeral=True,
            )
            return

        sus_role = interaction.guild.get_role(SUS_ROLE_ID)
        if sus_role and sus_role in member.roles:
            try:
                await member.remove_roles(
                    sus_role,
                    reason="Successful CAPTCHA verification",
                )
            except (discord.Forbidden, discord.HTTPException):
                await interaction.response.send_message(
                    f"{EMOJIS['close']} I could not remove the SUS role.",
                    ephemeral=True,
                )
                return

        snapshot = self.data["role_snapshots"].get(str(user_id), {})
        if snapshot.get("type") == "sus":
            bot_member = interaction.guild.me
            if bot_member:
                try:
                    await restore_roles(
                        member,
                        snapshot.get("roles", []),
                        bot_member.top_role,
                    )
                except (discord.Forbidden, discord.HTTPException):
                    pass
            del self.data["role_snapshots"][str(user_id)]

        del self.data["sus_captchas"][str(user_id)]
        await self.save()

        await interaction.response.send_message(
            f"{EMOJIS['tick']} CAPTCHA verified. Your normal roles have been restored.",
            ephemeral=True,
        )

    # -------------------------
    # PURGE
    # -------------------------

    @app_commands.command(name="purge", description="Delete recent messages.")
    @app_commands.describe(
        amount="Number of messages to delete (1-100)",
        reason="Reason for the purge",
    )
    async def purge(
        self,
        interaction: discord.Interaction,
        amount: int,
        reason: str = "Moderation cleanup",
    ):
        actor = interaction.user
        if not isinstance(actor, discord.Member):
            await interaction.response.send_message("Server only.", ephemeral=True)
            return

        allowed, message = self.permission_result(actor, 1)
        if not allowed:
            await interaction.response.send_message(message, ephemeral=True)
            return

        if amount < 1 or amount > 100:
            await interaction.response.send_message(
                f"{EMOJIS['close']} Amount must be between 1 and 100.",
                ephemeral=True,
            )
            return

        if actor.id != OWNER_ID:
            remaining = cooldown_remaining(
                self.data, "purge", actor.id, interaction.guild.id
            )
            if remaining:
                await interaction.response.send_message(
                    f"{EMOJIS['timeout']} `/purge` server cooldown: **{format_remaining(remaining)}** remaining.",
                    ephemeral=True,
                )
                return

        await interaction.response.defer(ephemeral=True)

        try:
            deleted = await interaction.channel.purge(limit=amount)
        except (discord.Forbidden, discord.HTTPException):
            await interaction.followup.send(f"{EMOJIS['close']} Purge failed.")
            return

        case_id = next_case_id(self.data)
        record = self.create_record(
            case_id,
            "purge",
            interaction.user.id,
            actor.id,
            reason,
            deleted_count=len(deleted),
        )
        await self.save()
        await self.send_log(record)

        if actor.id != OWNER_ID:
            set_cooldown(self.data, "purge", actor.id, interaction.guild.id)
            await self.save()

        await interaction.followup.send(
            f"{EMOJIS['tick']} Deleted **{len(deleted)}** messages."
        )

    # -------------------------
    # MOD HISTORY
    # -------------------------

    @app_commands.command(name="modhistory", description="View a member's moderation history.")
    @app_commands.describe(target="Member to inspect")
    async def modhistory(
        self,
        interaction: discord.Interaction,
        target: discord.Member,
    ):
        actor = interaction.user
        if not isinstance(actor, discord.Member):
            await interaction.response.send_message("Server only.", ephemeral=True)
            return

        allowed, message = self.permission_result(actor, 1)
        if not allowed:
            await interaction.response.send_message(message, ephemeral=True)
            return

        records = [
            record
            for record in self.data["records"]
            if int(record["target_id"]) == target.id
        ][-10:]

        if not records:
            await interaction.response.send_message(
                f"No moderation history found for **{target.display_name}**.",
                ephemeral=True,
            )
            return

        lines = []
        for record in reversed(records):
            timestamp = parse_iso(record["timestamp"]) or utc_now()
            lines.append(
                f"`{record['case_id']}` • **{record['action']}** • "
                f"{record.get('outcome', 'Success')}\n"
                f"Moderator: <@{record['moderator_id']}> • "
                f"<t:{int(timestamp.timestamp())}:R>\n"
                f"Reason: {record.get('reason', '—')}"
            )

        embed = discord.Embed(
            title=f"{EMOJIS['folder']} Moderation History • {target.display_name}",
            description="\n\n".join(lines),
            color=discord.Color.green(),
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # -------------------------
    # NICK
    # -------------------------

    @app_commands.command(name="nick", description="Change a member's nickname.")
    @app_commands.describe(
        target="Member whose nickname should change",
        nickname="New nickname",
        reason="Reason for the nickname change",
    )
    async def nick(
        self,
        interaction: discord.Interaction,
        target: discord.Member,
        nickname: str,
        reason: str = "Staff nickname change",
    ):
        actor = interaction.user
        if not isinstance(actor, discord.Member):
            await interaction.response.send_message("Server only.", ephemeral=True)
            return

        allowed, message = self.permission_result(actor, 1)
        if not allowed:
            await interaction.response.send_message(message, ephemeral=True)
            return

        allowed, message = self.member_from_interaction(interaction, target)
        if not allowed:
            await interaction.response.send_message(message, ephemeral=True)
            return

        try:
            await target.edit(nick=nickname, reason=reason)
        except (discord.Forbidden, discord.HTTPException):
            await interaction.response.send_message(
                f"{EMOJIS['close']} I could not change that nickname.",
                ephemeral=True,
            )
            return

        case_id = next_case_id(self.data)
        record = self.create_record(
            case_id,
            "nick",
            target.id,
            actor.id,
            reason,
            nickname=nickname,
        )
        await self.save()
        await self.send_log(record)

        await interaction.response.send_message(
            f"{EMOJIS['tick']} Nickname updated for **{target.display_name}**.",
            ephemeral=True,
        )

    # -------------------------
    # BOT TESTER PANEL
    # -------------------------

    @app_commands.command(
        name="bot-tester-panel",
        description="Summon the Chatly Bot Tester panel.",
    )
    async def tester_panel(self, interaction: discord.Interaction):
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                f"{EMOJIS['close']} This command can only be used inside Chatly.",
                ephemeral=True,
            )
            return

        tester_role = interaction.guild.get_role(BOT_TESTER_ROLE_ID)
        if tester_role is None or tester_role not in interaction.user.roles:
            await interaction.response.send_message(
                f"{EMOJIS['close']} You need the **Bot Tester** role to summon this panel.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title=f"{EMOJIS['code']} Chatly Bot Tester",
            description=(
                f"{EMOJIS['info']} **What is this?**\n"
                "This panel is for testing how Chatly reacts to different roles and Premium status. "
                "Changes made here apply **only to you**.\n\n"
                f"{EMOJIS['mod']} **Staff Rank Testing**\n"
                "Select a rank below to temporarily test the bot as **Jr Mod, Mod, Sr Mod, Admin, or Manager**. "
                "Executive and higher ranks cannot be granted from this panel.\n\n"
                f"{EMOJIS['premium']} **Premium Testing**\n"
                "Use the buttons to add or remove the Premium role from yourself.\n\n"
                f"{EMOJIS['refresh']} **Restore Original Roles**\n"
                "Use this after testing to restore your original eligible staff-rank state.\n\n"
                f"{EMOJIS['exclaim']} **Important**\n"
                "Only use this panel for legitimate bot testing. Do not use role testing to perform moderation actions against other members or bypass normal staff permissions."
            ),
            color=discord.Color(0x52FB18),
        )
        embed.set_footer(text="Chatly Bot Tester • Changes affect only the tester")

        await interaction.channel.send(embed=embed, view=BotTesterView())
        await interaction.response.send_message(
            f"{EMOJIS['tick']} Bot Tester panel summoned.",
            ephemeral=True,
        )

    async def _tester_roles(self, guild: discord.Guild) -> dict[int, discord.Role]:
        result = {}
        for role in guild.roles:
            rank = STAFF_RANKS.get(normalize_name(role.name), 0)
            if 1 <= rank <= 5:
                result[rank] = role
        return result

    async def _tester_snapshot(self, member: discord.Member) -> dict:
        snapshots = self.data.setdefault("bot_tester_snapshots", {})
        key = str(member.id)
        if key not in snapshots:
            snapshots[key] = {
                "staff_role_ids": [r.id for r in member.roles if 1 <= STAFF_RANKS.get(normalize_name(r.name), 0) <= 5],
                "premium": PREMIUM_ROLE_ID in {r.id for r in member.roles},
            }
            await self.save()
        return snapshots[key]

    async def bot_tester_set_rank(self, interaction: discord.Interaction, rank: int):
        member = interaction.user
        if not isinstance(member, discord.Member):
            return
        if rank not in range(1, 6):
            await interaction.response.send_message(f"{EMOJIS['close']} That rank cannot be tested.", ephemeral=True)
            return

        await self._tester_snapshot(member)
        roles = await self._tester_roles(member.guild)
        target_role = roles.get(rank)
        if target_role is None:
            await interaction.response.send_message(
                f"{EMOJIS['close']} I could not find the **{rank_name(rank)}** role in this server.",
                ephemeral=True,
            )
            return

        bot_member = member.guild.me
        if bot_member is None or target_role >= bot_member.top_role:
            await interaction.response.send_message(
                f"{EMOJIS['close']} I cannot manage the **{target_role.name}** role because it is above my highest role.",
                ephemeral=True,
            )
            return

        removable = [r for r in member.roles if 1 <= STAFF_RANKS.get(normalize_name(r.name), 0) <= 5 and r < bot_member.top_role]
        try:
            if removable:
                await member.remove_roles(*removable, reason="Chatly Bot Tester role simulation")
            await member.add_roles(target_role, reason="Chatly Bot Tester role simulation")
        except (discord.Forbidden, discord.HTTPException):
            await interaction.response.send_message(
                f"{EMOJIS['close']} I could not change your test role. Check the bot's role hierarchy.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"{EMOJIS['tick']} You are now testing as **{target_role.name}**.\n"
            f"{EMOJIS['info']} This changes only your test staff rank.",
            ephemeral=True,
        )

    async def bot_tester_premium(self, interaction: discord.Interaction, enabled: bool):
        member = interaction.user
        if not isinstance(member, discord.Member):
            return
        await self._tester_snapshot(member)
        role = interaction.guild.get_role(PREMIUM_ROLE_ID)
        if role is None:
            await interaction.response.send_message(f"{EMOJIS['close']} Premium role was not found.", ephemeral=True)
            return
        bot_member = interaction.guild.me
        if bot_member is None or role >= bot_member.top_role:
            await interaction.response.send_message(f"{EMOJIS['close']} I cannot manage the Premium role.", ephemeral=True)
            return
        try:
            if enabled:
                await member.add_roles(role, reason="Chatly Bot Tester Premium simulation")
            else:
                await member.remove_roles(role, reason="Chatly Bot Tester Premium simulation")
        except (discord.Forbidden, discord.HTTPException):
            await interaction.response.send_message(f"{EMOJIS['close']} I could not change your Premium role.", ephemeral=True)
            return
        state = "added" if enabled else "removed"
        await interaction.response.send_message(
            f"{EMOJIS['tick']} Premium role **{state}** for you.",
            ephemeral=True,
        )

    async def bot_tester_restore(self, interaction: discord.Interaction):
        member = interaction.user
        if not isinstance(member, discord.Member):
            return
        snapshot = self.data.setdefault("bot_tester_snapshots", {}).get(str(member.id))
        if not snapshot:
            await interaction.response.send_message(
                f"{EMOJIS['info']} No saved tester state was found for you.",
                ephemeral=True,
            )
            return
        bot_member = interaction.guild.me
        if bot_member is None:
            await interaction.response.send_message(f"{EMOJIS['close']} I could not determine my server role.", ephemeral=True)
            return
        eligible = [r for r in member.roles if 1 <= STAFF_RANKS.get(normalize_name(r.name), 0) <= 5 and r < bot_member.top_role]
        try:
            if eligible:
                await member.remove_roles(*eligible, reason="Chatly Bot Tester restore")
            for role_id in snapshot.get("staff_role_ids", []):
                role = interaction.guild.get_role(int(role_id))
                if role and role < bot_member.top_role:
                    await member.add_roles(role, reason="Chatly Bot Tester restore")
            premium = interaction.guild.get_role(PREMIUM_ROLE_ID)
            if premium and premium < bot_member.top_role:
                if snapshot.get("premium"):
                    await member.add_roles(premium, reason="Chatly Bot Tester restore")
                else:
                    await member.remove_roles(premium, reason="Chatly Bot Tester restore")
        except (discord.Forbidden, discord.HTTPException):
            await interaction.response.send_message(f"{EMOJIS['close']} I could not fully restore your original roles.", ephemeral=True)
            return

        self.data["bot_tester_snapshots"].pop(str(member.id), None)
        await self.save()
        await interaction.response.send_message(
            f"{EMOJIS['refresh']} Your original tester state has been restored.",
            ephemeral=True,
        )

    # -------------------------
    # MEMBER JOIN RESTORATION
    # -------------------------

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id != GUILD_ID:
            return

        snapshot = self.data["role_snapshots"].get(str(member.id))
        if not snapshot:
            return

        role_id = JAIL_ROLE_ID if snapshot.get("type") == "jail" else SUS_ROLE_ID
        role = member.guild.get_role(role_id)

        if role and role not in member.roles:
            try:
                await member.add_roles(
                    role,
                    reason=f"Restore Chatly {snapshot.get('type', 'moderation')} restriction",
                )
            except (discord.Forbidden, discord.HTTPException):
                pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
