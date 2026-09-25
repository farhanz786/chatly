import asyncio
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import discord
import gspread
from google.oauth2.service_account import Credentials
from discord import app_commands
from discord.ext import commands, tasks


# ============================================================
# CHATLY — APPLY FOR STAFF
# ============================================================

GUILD_ID = 1467231978813128834
OWNER_ID = 937242913535033404

APPLICATION_CHANNEL_ID = 1503429599022022816
APPLICATION_LOG_CHANNEL_ID = 1552652540343091262
STAFF_WELCOME_CHANNEL_ID = 1503429580382404628

VERIFIED_ROLE_ID = 1503429447322435725
DEFAULT_VERIFICATION_CHANNEL_ID = 1503429521087398019
PREMIUM_ROLE_ID = 1503429265415471224

AGE_ROLE_IDS = {
    "13-15": 1503429320318648381,
    "16-17": 1503429321203646729,
    "18-20": 1503429322487234790,
    "21+": 1503429323489677405,
}

DATA_FILE = Path("staff_applications.json")
CHATLY_GREEN = 0x52FB18

# Direct Staff payment / pricing
PAYPAL_URL = "https://www.paypal.com/ncp/payment/GR2EKPMCV5XAN"
QR_CODE_URL = "https://media.discordapp.net/attachments/1010905558624239739/1550880410140016752/qrcode_402529378_a97193817f8de9877f385680d78316b4.png?ex=6aaff16f&is=6aae9fef&hm=2f765fc8be72e5cd64f5d82d13ea460f046130fab33a50e4ab60e81ceac680&=&format=webp&quality=lossless"
DIRECT_STAFF_PRICING_IMAGE_URL = os.getenv("CHATLY_DIRECT_STAFF_PRICING_IMAGE_URL", "")
GOOGLE_CREDENTIALS_FILE = Path(__file__).resolve().parent.parent / "google_credentials.json"
GOOGLE_SHEET_ID = "1H9yQIJn86lqZLBROZvnkJ_BCEoYuf5jkQqmEBbryvP8"
PURCHASES_SHEET_NAME = "Purchases"
PURCHASE_HEADERS = ["User", "Purchase Type", "Plan", "Amount", "Activated", "Expires", "Status", "Notes"]

# Existing Chatly custom emojis — use only the Notion emoji source of truth.
TICK = "<:tick:1550538067570335764>"
DISLIKE = "<:dislike:1550544099214495774>"
UPVOTE = "<:upvote:1550551638387990620>"
INFO = "<:info:1550551426269319168>"
QUESTION = "<:question:1550551387371343883>"
USER = "<:user:1550286898126262312>"
MOD = "<:mod:1550551457109901435>"
EDIT = "<:edit:1550277007961755658>"
CLOSE = "<:close:1550533713526399126>"
FOLDER = "<:folder:1550538040819318904>"
REFRESH = "<:refresh:1550282774714519664>"
LOCK = "<:lock:1551275905253511238>"
STARS = "<:stars:1550289412624093234>"

STATUS_PENDING = "Pending"
STATUS_APPROVED = "Approved"
STATUS_INTERVIEW = "Interview"
STATUS_ACCEPTED = "Accepted"
STATUS_DENIED = "Denied"
STATUS_MORE_INFO = "More Information Required"
STATUS_INACTIVE = "Inactive"
STATUS_CANCELLED = "Cancelled"
STATUS_WITHDRAWN = "Withdrawn"

FINAL_STATUSES = {
    STATUS_ACCEPTED,
    STATUS_DENIED,
    STATUS_WITHDRAWN,
    STATUS_INACTIVE,
    STATUS_CANCELLED,
}

STANDARD_QUESTIONS = [
    ("about", "Tell us a little about yourself."),
    ("interests", "What are your main interests/hobbies?"),
    ("experience", "Have you had previous staff/moderation experience? If yes, briefly describe it."),
    ("experience_learned", "What did you learn from your previous staff experience, if applicable?"),
    ("timezone", "What timezone are you in?"),
    ("time", "Approximately how much time can you regularly dedicate to Chatly?"),
    ("availability", "When are you usually available for Chatly (days/time periods)?"),
    ("motivation", "Why do you want to become Chatly staff?"),
    ("contribution", "What do you think you could contribute to the Chatly staff team?"),
    ("anything_else", "Is there anything else you want the staff team to know about you?"),
]


# -------------------------
# Storage helpers
# -------------------------

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: Optional[datetime] = None) -> str:
    return (dt or utc_now()).isoformat()


def parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def load_data() -> dict:
    if not DATA_FILE.exists():
        return {"counter": 0, "applications": {}}
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError
        data.setdefault("counter", 0)
        data.setdefault("applications", {})
        return data
    except (json.JSONDecodeError, OSError, ValueError):
        return {"counter": 0, "applications": {}}


def save_data(data: dict) -> None:
    temp = DATA_FILE.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    temp.replace(DATA_FILE)


def clean_text(value: str, limit: int = 2000) -> str:
    value = re.sub(r"@everyone|@here", "@\u200beveryone", str(value).strip(), flags=re.I)
    return value[:limit]


def normalize_role_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


def role_rank(role: discord.Role) -> int:
    ranks = {
        "junior moderator": 1,
        "jr moderator": 1,
        "jr mod": 1,
        "moderator": 2,
        "mod": 2,
        "senior moderator": 3,
        "sr moderator": 3,
        "sr mod": 3,
        "admin": 4,
        "administrator": 4,
        "manager": 5,
        "executive": 6,
        "exec": 6,
        "co owner": 7,
        "owner": 8,
    }
    return ranks.get(normalize_role_name(role.name), 0)


def find_staff_role(member: discord.Member, minimum_rank: int = 1) -> int:
    if member.id == OWNER_ID:
        return 8
    return max((role_rank(r) for r in member.roles), default=0)


def is_reviewer(member: discord.Member) -> bool:
    return find_staff_role(member) >= 2


def is_final_reviewer(member: discord.Member) -> bool:
    return member.id == OWNER_ID or find_staff_role(member) >= 6


def is_higher_staff(member: discord.Member) -> bool:
    return is_final_reviewer(member)


def age_label(member: discord.Member) -> Optional[str]:
    ids = {r.id for r in member.roles}
    for label, role_id in AGE_ROLE_IDS.items():
        if role_id in ids:
            return label
    return None


def age_is_eligible(member: discord.Member) -> bool:
    label = age_label(member)
    return label in {"16-17", "18-20", "21+"}


def age_role_text(member: discord.Member) -> str:
    label = age_label(member)
    return label or "No eligible age role"


def account_age_ok(member: discord.Member) -> bool:
    created = member.created_at
    return utc_now() - created >= timedelta(days=90)


def membership_age_ok(member: discord.Member) -> bool:
    joined = member.joined_at
    return bool(joined and utc_now() - joined >= timedelta(days=30))


# -------------------------
# UI helpers
# -------------------------

def _append_staff_purchase_sync(member_name: str, position: str, amount: str, activated_at: datetime, expires_at: Optional[datetime] = None):
    credentials = Credentials.from_service_account_file(
        GOOGLE_CREDENTIALS_FILE,
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"],
    )
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
    try:
        worksheet = spreadsheet.worksheet(PURCHASES_SHEET_NAME)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=PURCHASES_SHEET_NAME, rows=1000, cols=len(PURCHASE_HEADERS))
        worksheet.update("A1:H1", [PURCHASE_HEADERS])
    if worksheet.row_values(1)[:8] != PURCHASE_HEADERS:
        worksheet.update("A1:H1", [PURCHASE_HEADERS])
    from zoneinfo import ZoneInfo
    ist = ZoneInfo("Asia/Kolkata")
    row = [
        member_name,
        "Direct Staff",
        position,
        amount,
        activated_at.astimezone(ist).strftime("%d %b %Y, %I:%M %p IST"),
        expires_at.astimezone(ist).strftime("%d %b %Y, %I:%M %p IST") if expires_at else "Permanent",
        "Active",
        "Payment verified",
    ]
    worksheet.append_row(row, value_input_option="USER_ENTERED")


async def append_staff_purchase_to_sheet(member: discord.Member, position: str, amount: str):
    try:
        await asyncio.to_thread(_append_staff_purchase_sync, member.name, position, amount, utc_now(), None)
    except Exception as exc:
        print(f"Google Sheets Direct Staff purchase sync failed: {exc}")


class StaffApplicationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data = load_data()
        self.lock = asyncio.Lock()
        self.views_registered = False
        self.more_info_watcher.start()

    def cog_unload(self):
        self.more_info_watcher.cancel()

    async def cog_load(self):
        self.bot.loop.create_task(self.register_views())

    async def register_views(self):
        await self.bot.wait_until_ready()
        if self.views_registered:
            return
        self.bot.add_view(StaffApplicationPanelView(self))
        self.bot.add_view(ApplicationReviewView(self))
        self.bot.add_view(DirectStaffPositionView(self))
        self.views_registered = True

    async def save(self):
        async with self.lock:
            save_data(self.data)

    def next_application_id(self) -> str:
        self.data["counter"] = int(self.data.get("counter", 0)) + 1
        return f"APP-{self.data['counter']:04d}"

    def active_for(self, user_id: int) -> Optional[dict]:
        for app in self.data["applications"].values():
            if app.get("draft"):
                continue
            if int(app.get("applicant_id", 0)) == user_id and app.get("status") not in FINAL_STATUSES:
                return app
        return None

    def get(self, app_id: str) -> Optional[dict]:
        return self.data["applications"].get(app_id)

    def status_text(self, app: dict) -> str:
        return app.get("status", STATUS_PENDING)

    def moderation_summary(self, member: discord.Member) -> str:
        moderation = self.bot.get_cog("Moderation")
        if moderation is None or not hasattr(moderation, "data"):
            return "Active moderation history could not be read automatically. Staff review may be required."
        try:
            warnings = moderation.data.get("warnings", {}).get(str(member.id), [])
            now = utc_now()
            active = []
            for warning in warnings:
                if warning.get("removed"):
                    continue
                expires = parse_iso(warning.get("expires_at"))
                if expires is None or expires > now:
                    active.append(warning)
            if not active:
                return "No active moderation cases found."
            lines = [f"{len(active)} active warning/case(s):"]
            for warning in active[:5]:
                lines.append(f"• Warning #{warning.get('warning_number', '?')}: {clean_text(warning.get('reason', 'No reason'), 180)}")
            return "\n".join(lines)
        except Exception:
            return "Active moderation history could not be read automatically. Staff review may be required."

    def level_for(self, member: discord.Member) -> Optional[int]:
        levelling = self.bot.get_cog("Levelling")
        if levelling is None:
            return None
        try:
            data = levelling.get_member_data(member.guild.id, member.id)
            stored_level = int(data.get("level", 0) or 0)
            total_xp = int(data.get("total_xp", 0) or 0)
            calculated_level = int(levelling.calculate_level(total_xp))
            return max(stored_level, calculated_level)
        except Exception:
            try:
                data = levelling.data.get(str(member.guild.id), {}).get(str(member.id), {})
                stored_level = int(data.get("level", 0) or 0)
                total_xp = int(data.get("total_xp", 0) or 0)
                calculated_level = int(levelling.calculate_level(total_xp))
                return max(stored_level, calculated_level)
            except Exception:
                return None

    def premium(self, member: discord.Member) -> bool:
        return member.get_role(PREMIUM_ROLE_ID) is not None

    def panel_view(self):
        return StaffApplicationPanelView(self)

    def application_embed(self, app: dict, guild: discord.Guild) -> discord.Embed:
        applicant = guild.get_member(int(app["applicant_id"]))
        name = applicant.mention if applicant else f"<@{app['applicant_id']}>"
        premium = "Yes" if app.get("premium") else "No"
        status = app.get("status", STATUS_PENDING)
        embed = discord.Embed(
            title=f"{MOD} Staff Application · {app['application_id']}",
            description=f"**Applicant:** {name}\n**Route:** {app.get('route', 'Standard')}\n**Status:** **{status}**",
            color=CHATLY_GREEN,
            timestamp=parse_iso(app.get("submitted_at")) or utc_now(),
        )
        embed.add_field(name="Age", value=app.get("age_role", "Unknown"), inline=True)
        embed.add_field(name="Premium", value=premium, inline=True)
        embed.add_field(name="Level", value=str(app.get("level", "Unknown")), inline=True)
        embed.add_field(name="Account Age", value=app.get("account_age", "Unknown"), inline=True)
        embed.add_field(name="Membership", value=app.get("membership_age", "Unknown"), inline=True)
        embed.add_field(name="Moderation History", value=clean_text(app.get("moderation_summary", "Not available"), 1024), inline=False)

        questions = app.get("answers", {})
        for key, question in STANDARD_QUESTIONS:
            answer = questions.get(key, "") or "—"
            embed.add_field(name=question, value=clean_text(answer, 1024), inline=False)

        votes = app.get("votes", {})
        embed.add_field(
            name="Review Votes",
            value=f"{UPVOTE} **{sum(v == 'upvote' for v in votes.values())}**  {DISLIKE} **{sum(v == 'dislike' for v in votes.values())}",
            inline=False,
        )
        if app.get("denial_reason"):
            embed.add_field(name="Denial Reason", value=clean_text(app["denial_reason"], 1024), inline=False)
        if app.get("interview_notes"):
            embed.add_field(name="Interview Outcome", value=clean_text(app["interview_notes"], 1024), inline=False)
        embed.set_footer(text=f"Application ID: {app['application_id']}")
        return embed

    async def log_event(self, app: dict, action: str, actor_id: Optional[int] = None, details: Optional[str] = None):
        channel = self.bot.get_channel(APPLICATION_LOG_CHANNEL_ID)
        if not channel:
            return
        embed = discord.Embed(title=f"{INFO} Application Log — {action}", color=CHATLY_GREEN, timestamp=utc_now())
        embed.add_field(name="Application", value=f"`{app['application_id']}`", inline=True)
        embed.add_field(name="Applicant", value=f"<@{app['applicant_id']}> (`{app['applicant_id']}`)", inline=True)
        embed.add_field(name="Status", value=app.get("status", "Unknown"), inline=True)
        if actor_id:
            embed.add_field(name="Actor", value=f"<@{actor_id}> (`{actor_id}`)", inline=False)
        if details:
            embed.add_field(name="Details", value=clean_text(details, 1024), inline=False)
        try:
            await channel.send(embed=embed)
        except discord.HTTPException:
            pass

    async def log_full_application(self, app: dict, reason: str):
        channel = self.bot.get_channel(APPLICATION_LOG_CHANNEL_ID)
        if not channel:
            return
        guild = self.bot.get_guild(int(app.get("guild_id", GUILD_ID)))
        if guild is None:
            return
        embed = self.application_embed(app, guild)
        embed.title = f"{FOLDER} Archived Application · {app['application_id']} · {reason}"
        try:
            await channel.send(embed=embed)
        except discord.HTTPException:
            pass

    async def delete_application_message(self, app: dict):
        channel = self.bot.get_channel(APPLICATION_CHANNEL_ID)
        message_id = app.get("message_id")
        if not channel or not message_id:
            return
        try:
            message = await channel.fetch_message(int(message_id))
            await message.delete()
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass

    async def refresh_application_message(self, app: dict):
        channel = self.bot.get_channel(APPLICATION_CHANNEL_ID)
        message_id = app.get("message_id")
        if not channel or not message_id:
            return
        try:
            message = await channel.fetch_message(int(message_id))
            await message.edit(embed=self.application_embed(app, channel.guild), view=ApplicationReviewView(self))
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass

    async def send_applicant_dm(self, app: dict, content: str, view: Optional[discord.ui.View] = None):
        user = self.bot.get_user(int(app["applicant_id"]))
        if user is None:
            try:
                user = await self.bot.fetch_user(int(app["applicant_id"]))
            except discord.HTTPException:
                return
        try:
            await user.send(content=content, view=view)
        except discord.HTTPException:
            pass

    def reapplication_remaining(self, user_id: int) -> Optional[timedelta]:
        latest = None
        for app in self.data["applications"].values():
            if int(app.get("applicant_id", 0)) != user_id:
                continue
            deadline = parse_iso(app.get("reapply_after"))
            if deadline and (latest is None or deadline > latest):
                latest = deadline
        if latest is None:
            return None
        remaining = latest - utc_now()
        return remaining if remaining.total_seconds() > 0 else None

    async def start_application(self, interaction: discord.Interaction, route: str):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(f"{CLOSE} This can only be used inside Chatly.", ephemeral=True)
            return
        member = interaction.user
        cooldown = self.reapplication_remaining(member.id)
        if cooldown:
            days = cooldown.days
            hours = cooldown.seconds // 3600
            await interaction.response.send_message(
                f"{INFO} You cannot reapply yet. Your 30-day cooldown has **{days}d {hours}h** remaining.",
                ephemeral=True,
            )
            return
        active = self.active_for(member.id)
        if active:
            await interaction.response.send_message(f"{INFO} You already have an active application: `{active['application_id']}`.", ephemeral=True)
            return

        if route == "Standard":
            ok, failures = self.eligibility(member)
            if not ok:
                await interaction.response.send_message(
                    f"{CLOSE} You are not currently eligible for the standard Apply for Staff route.\n\n" + "\n".join(f"• {x}" for x in failures),
                    ephemeral=True,
                )
                return

        if route == "Direct Staff" and (not age_is_eligible(member) or member.guild.get_role(VERIFIED_ROLE_ID) not in member.roles):
            await interaction.response.send_message(f"{CLOSE} Direct Staff still requires **age eligibility and Chatly verification**.", ephemeral=True)
            return

        app_id = self.next_application_id()
        app = {
            "application_id": app_id,
            "applicant_id": member.id,
            "guild_id": member.guild.id,
            "route": route,
            "status": STATUS_PENDING,
            "submitted_at": None,
            "message_id": None,
            "age_role": age_role_text(member),
            "premium": self.premium(member),
            "level": self.level_for(member) if route == "Standard" else self.level_for(member),
            "account_age": str(utc_now() - member.created_at).split(".")[0],
            "membership_age": str(utc_now() - member.joined_at).split(".")[0] if member.joined_at else "Unknown",
            "moderation_summary": self.moderation_summary(member),
            "answers": {},
            "votes": {},
            "notes": [],
            "requested_information": None,
            "more_info_deadline": None,
            "interview_attempts": 0,
            "denial_reason": None,
            "interview_notes": None,
            "staff_position": None,
            "created_at": iso(),
            "draft": True,
        }
        self.data["applications"][app_id] = app
        await self.save()
        await interaction.response.send_modal(StaffApplicationModalOne(self, app_id))

    async def collect_answers_one(self, interaction: discord.Interaction, app_id: str, values: dict[str, str]):
        app = self.get(app_id)
        if not app or app.get("status") != STATUS_PENDING:
            await interaction.response.send_message(f"{CLOSE} This application is no longer active.", ephemeral=True)
            return
        app["answers"].update(values)
        await self.save()
        await interaction.response.send_modal(StaffApplicationModalTwo(self, app_id))

    async def collect_answers_two(self, interaction: discord.Interaction, app_id: str, values: dict[str, str]):
        app = self.get(app_id)
        if not app or app.get("status") != STATUS_PENDING:
            await interaction.response.send_message(f"{CLOSE} This application is no longer active.", ephemeral=True)
            return
        app["answers"].update(values)
        await self.save()
        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"{INFO} Review Before Submission",
                description=(
                    "Your application is ready to submit.\n\n"
                    f"{LOCK} **Important:** Once submitted, the application **cannot be edited or updated**. "
                    "Make any changes you need before continuing."
                ),
                color=CHATLY_GREEN,
            ),
            view=FinalSubmitView(self, app_id),
            ephemeral=True,
        )

    async def submit_application(self, interaction: discord.Interaction, app_id: str):
        app = self.get(app_id)
        if not app or app.get("status") != STATUS_PENDING:
            await interaction.response.send_message(f"{CLOSE} This application is no longer active.", ephemeral=True)
            return
        app["submitted_at"] = iso()
        app["status"] = STATUS_PENDING
        app["draft"] = False
        await self.save()

        channel = self.bot.get_channel(APPLICATION_CHANNEL_ID)
        if channel is None:
            await interaction.response.send_message(f"{CLOSE} The application channel could not be found.", ephemeral=True)
            return

        message = await channel.send(embed=self.application_embed(app, interaction.guild), view=ApplicationReviewView(self))
        app["message_id"] = message.id
        await self.save()
        await self.log_event(app, "Submitted", interaction.user.id)
        await interaction.response.send_message(f"{TICK} Your application **{app_id}** has been submitted successfully.", ephemeral=True)

    async def withdraw(self, interaction: discord.Interaction, app_id: str):
        app = self.get(app_id)
        if not app or int(app.get("applicant_id", 0)) != interaction.user.id:
            await interaction.response.send_message(f"{CLOSE} You can only withdraw your own active application.", ephemeral=True)
            return
        if app.get("status") in FINAL_STATUSES:
            await interaction.response.send_message(f"{INFO} This application is already closed.", ephemeral=True)
            return
        app["status"] = STATUS_WITHDRAWN
        app["withdrawn_at"] = iso()
        await self.save()
        await self.log_event(app, "Withdrawn", interaction.user.id)
        await self.log_full_application(app, "Withdrawn")
        await self.delete_application_message(app)
        await interaction.response.edit_message(content=f"{TICK} Application `{app_id}` withdrawn. You may apply again immediately.", embed=None, view=None)

    async def start_direct_position_application(self, interaction: discord.Interaction, position: str):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(f"{CLOSE} This can only be used inside Chatly.", ephemeral=True)
            return
        member = interaction.user
        cooldown = self.reapplication_remaining(member.id)
        if cooldown:
            days = cooldown.days
            hours = cooldown.seconds // 3600
            await interaction.response.send_message(f"{INFO} Your 30-day reapplication cooldown has **{days}d {hours}h** remaining.", ephemeral=True)
            return
        if not age_is_eligible(member) or interaction.guild.get_role(VERIFIED_ROLE_ID) not in member.roles:
            await interaction.response.send_message(f"{CLOSE} Direct Staff still requires age eligibility and Chatly verification.", ephemeral=True)
            return
        app_id = self.next_application_id()
        app = {
            "application_id": app_id,
            "applicant_id": member.id,
            "guild_id": member.guild.id,
            "route": "Direct Staff",
            "staff_position": position,
            "status": STATUS_PENDING,
            "submitted_at": None,
            "message_id": None,
            "age_role": age_role_text(member),
            "premium": self.premium(member),
            "level": self.level_for(member),
            "account_age": str(utc_now() - member.created_at).split(".")[0],
            "membership_age": str(utc_now() - member.joined_at).split(".")[0] if member.joined_at else "Unknown",
            "moderation_summary": self.moderation_summary(member),
            "answers": {},
            "votes": {},
            "notes": [],
            "requested_information": None,
            "more_info_deadline": None,
            "interview_attempts": 0,
            "denial_reason": None,
            "interview_notes": None,
            "created_at": iso(),
            "draft": True,
            "payment_status": "Pending Verification",
        }
        self.data["applications"][app_id] = app
        await self.save()
        amount = dict([("Owner", "$9,500"), ("Co-Owner", "$2,000"), ("Executive", "$1,500"), ("Manager", "$1,100"), ("Admin", "$700"), ("Sr. Moderator", "$450"), ("Moderator", "$300"), ("Junior Moderator", "$200")])[position]
        embed = discord.Embed(
            title=f"{STARS} Direct Staff Payment",
            description=(
                f"**Selected Position:** {position}\n"
                f"**Amount:** {amount}\n\n"
                f"<:paypal:1550551525204566057> **Payment**\n"
                f"Send **{amount}** through PayPal using the button below, or scan the QR code to complete your payment.\n\n"
                f"Once your payment is complete, please DM <@{OWNER_ID}> with your **payment screenshot** so we can verify and process your Direct Staff purchase.\n\n"
                f"{INFO} **Processing Time**\n"
                "Activation is completed after payment verification and the required Direct Staff application/interview process."
            ),
            color=CHATLY_GREEN,
        )
        embed.set_thumbnail(url=QR_CODE_URL)
        embed.set_footer(text="Chatly Direct Staff")
        payment_view = discord.ui.View(timeout=None)
        payment_view.add_item(discord.ui.Button(label="Pay with PayPal", emoji="<:paypal:1550551525204566057>", style=discord.ButtonStyle.link, url=PAYPAL_URL))
        await interaction.response.send_message(embed=embed, view=payment_view, ephemeral=True)
        await self.send_applicant_dm(app, f"{STARS} Direct Staff purchase selected for **{position}** (application `{app_id}`). Amount: **{amount}**. Complete payment through the PayPal link and DM <@{OWNER_ID}> with your payment screenshot for verification.")

    async def unlock_direct_application(self, interaction: discord.Interaction, app_id: str):
        app = self.get(app_id)
        if not app or app.get("route") != "Direct Staff":
            await interaction.response.send_message(f"{CLOSE} Direct Staff application not found.", ephemeral=True)
            return
        if app.get("payment_status") != "Verified":
            await interaction.response.send_message(f"{INFO} Payment has not been verified for `{app_id}`.", ephemeral=True)
            return
        app["payment_verified_by"] = interaction.user.id
        app["payment_verified_at"] = iso()
        app["draft"] = False
        await self.save()
        await self.send_applicant_dm(app, f"{TICK} Your payment for Direct Staff `{app_id}` has been verified. Use the button below to complete the short application.", DirectApplicationContinueView(self, app_id))
        await self.log_event(app, "Direct Staff Payment Verified", interaction.user.id, f"Position: {app.get('staff_position')}")
        await interaction.response.send_message(f"{TICK} Payment verified for `{app_id}`. The applicant has been sent the application link.", ephemeral=True)

    async def collect_direct_answers(self, interaction: discord.Interaction, app_id: str, values: dict[str, str]):
        app = self.get(app_id)
        if not app or app.get("route") != "Direct Staff" or app.get("payment_status") != "Verified":
            await interaction.response.send_message(f"{CLOSE} This Direct Staff application is not available.", ephemeral=True)
            return
        app["answers"].update(values)
        await self.save()
        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"{INFO} Review Before Submission",
                description=(f"Your Direct Staff application for **{app.get('staff_position')}** is ready to submit.\n\n"
                             f"{LOCK} **Once submitted, it cannot be edited or updated.**"),
                color=CHATLY_GREEN,
            ),
            view=FinalSubmitView(self, app_id),
            ephemeral=True,
        )

    @app_commands.command(name="verify-direct-staff-payment", description="Verify payment for a Direct Staff application.")
    @app_commands.describe(application_id="Direct Staff application ID")
    async def verify_direct_staff_payment(self, interaction: discord.Interaction, application_id: str):
        if not is_final_reviewer(interaction.user):
            await interaction.response.send_message(f"{LOCK} Owner/Co-Owner/Exec only.", ephemeral=True)
            return
        app = self.get(application_id.upper())
        if not app or app.get("route") != "Direct Staff":
            await interaction.response.send_message(f"{CLOSE} Direct Staff application not found.", ephemeral=True)
            return
        app["payment_status"] = "Verified"
        await self.save()
        guild_member = interaction.guild.get_member(int(app["applicant_id"])) if interaction.guild else None
        if guild_member:
            amounts = {"Owner": "$9,500", "Co-Owner": "$2,000", "Executive": "$1,500", "Manager": "$1,100", "Admin": "$700", "Sr. Moderator": "$450", "Moderator": "$300", "Junior Moderator": "$200"}
            await append_staff_purchase_to_sheet(guild_member, app.get("staff_position", "Unknown"), amounts.get(app.get("staff_position"), "Unknown"))
        await self.unlock_direct_application(interaction, app["application_id"])

    async def vote(self, interaction: discord.Interaction, app_id: str, choice: str):
        app = self.get(app_id)
        if not app or app.get("status") in FINAL_STATUSES or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(f"{CLOSE} This application is no longer open for review.", ephemeral=True)
            return
        if not is_reviewer(interaction.user):
            await interaction.response.send_message(f"{LOCK} You need **Moderator or higher** to vote on applications.", ephemeral=True)
            return
        old = app.setdefault("votes", {}).get(str(interaction.user.id))
        if old == choice:
            del app["votes"][str(interaction.user.id)]
            action = "Vote removed"
        else:
            app["votes"][str(interaction.user.id)] = choice
            action = "Vote changed" if old else "Vote added"
        await self.save()
        await self.log_event(app, action, interaction.user.id, f"Vote: {choice}")
        await interaction.response.edit_message(embed=self.application_embed(app, interaction.guild), view=ApplicationReviewView(self))

    async def approve(self, interaction: discord.Interaction, app_id: str):
        app = self.get(app_id)
        if not app or not is_final_reviewer(interaction.user) or app.get("status") in FINAL_STATUSES:
            await interaction.response.send_message(f"{LOCK} You are not authorized to approve this application.", ephemeral=True)
            return
        app["status"] = STATUS_APPROVED
        await self.save()
        await self.log_event(app, "Approved", interaction.user.id)
        await self.send_applicant_dm(app, f"{TICK} Your Chatly staff application `{app_id}` has been approved for the interview stage.\n\nPlease contact <@{OWNER_ID}> directly to arrange your interview.\n\nYour interview will include additional and scenario-based questions.")
        await self.refresh_application_message(app)
        await interaction.response.send_message(f"{TICK} `{app_id}` approved. Interview instructions sent to the applicant.", ephemeral=True)

    async def deny(self, interaction: discord.Interaction, app_id: str):
        app = self.get(app_id)
        if not app or not is_final_reviewer(interaction.user) or app.get("status") in FINAL_STATUSES:
            await interaction.response.send_message(f"{LOCK} You are not authorized to deny this application.", ephemeral=True)
            return
        await interaction.response.send_modal(DenialReasonModal(self, app_id))

    async def complete_denial(self, interaction: discord.Interaction, app_id: str, reason: str):
        app = self.get(app_id)
        if not app:
            await interaction.response.send_message(f"{CLOSE} Application not found.", ephemeral=True)
            return
        app["status"] = STATUS_DENIED
        app["denial_reason"] = clean_text(reason, 2000) if reason.strip() else None
        app["reapply_after"] = iso(utc_now() + timedelta(days=30))
        await self.save()
        await self.log_event(app, "Denied", interaction.user.id, app.get("denial_reason") or "No denial reason provided")
        await self.log_full_application(app, "Denied")
        message = f"{DISLIKE} Your Chatly staff application `{app_id}` was denied.\n\n"
        message += f"Reason: {app['denial_reason']}\n\n" if app.get("denial_reason") else "No denial reason was provided.\n\n"
        message += "You may reapply after the 30-day reapplication cooldown."
        await self.send_applicant_dm(app, message)
        await self.delete_application_message(app)
        await interaction.response.send_message(f"{DISLIKE} `{app_id}` denied. The application was removed from the applications channel.", ephemeral=True)

    async def request_more_info(self, interaction: discord.Interaction, app_id: str):
        if not is_final_reviewer(interaction.user):
            await interaction.response.send_message(f"{LOCK} Only Owner/Co-Owner/Exec can request more information.", ephemeral=True)
            return
        await interaction.response.send_modal(MoreInfoModal(self, app_id))

    async def set_more_info(self, interaction: discord.Interaction, app_id: str, request: str):
        app = self.get(app_id)
        if not app:
            await interaction.response.send_message(f"{CLOSE} Application not found.", ephemeral=True)
            return
        app["status"] = STATUS_MORE_INFO
        app["requested_information"] = clean_text(request, 2000)
        app["more_info_deadline"] = iso(utc_now() + timedelta(days=7))
        await self.save()
        await self.log_event(app, "More Information Required", interaction.user.id, request)
        await self.send_applicant_dm(app, f"{INFO} Additional information is required for your staff application `{app_id}`.\n\n**Please provide:**\n{request}\n\nYou have **7 days** to respond.", MoreInfoResponseView(self, app_id))
        await self.refresh_application_message(app)
        await interaction.response.send_message(f"{INFO} More Information Required sent to the applicant.", ephemeral=True)

    async def submit_more_info(self, interaction: discord.Interaction, app_id: str, response_text: str):
        app = self.get(app_id)
        if not app or app.get("status") != STATUS_MORE_INFO or int(app.get("applicant_id", 0)) != interaction.user.id:
            await interaction.response.send_message(f"{CLOSE} This information request is no longer active.", ephemeral=True)
            return
        app["more_info_response"] = clean_text(response_text, 4000)
        app["status"] = STATUS_PENDING
        app["more_info_deadline"] = None
        await self.save()
        await self.log_event(app, "Additional Information Submitted", interaction.user.id, response_text)
        await self.refresh_application_message(app)
        await interaction.response.send_message(f"{TICK} Your additional information has been submitted to the staff team.", ephemeral=True)

    async def interview_outcome(self, interaction: discord.Interaction, app_id: str, outcome: str):
        app = self.get(app_id)
        if not app or not is_final_reviewer(interaction.user):
            await interaction.response.send_message(f"{LOCK} Only Owner/Co-Owner/Exec can record interview outcomes.", ephemeral=True)
            return
        if outcome == "request":
            app["interview_attempts"] = int(app.get("interview_attempts", 0)) + 1
            app["status"] = STATUS_INTERVIEW
            await self.save()
            await self.log_event(app, "Interview — Another Interview Requested", interaction.user.id)
            await self.send_applicant_dm(app, f"{REFRESH} The staff team would like another interview for application `{app_id}`. Please contact <@{OWNER_ID}> again to arrange it.")
            await self.refresh_application_message(app)
            await interaction.response.send_message(f"{REFRESH} Another interview requested.", ephemeral=True)
            return
        if outcome == "deny":
            await interaction.response.send_modal(InterviewDenyModal(self, app_id))
            return
        await self.accept_application(interaction, app_id)

    async def accept_application(self, interaction: discord.Interaction, app_id: str):
        app = self.get(app_id)
        if not app:
            await interaction.response.send_message(f"{CLOSE} Application not found.", ephemeral=True)
            return
        if app.get("status") not in {STATUS_APPROVED, STATUS_INTERVIEW}:
            await interaction.response.send_message(f"{INFO} This application is not currently at the interview stage.", ephemeral=True)
            return
        guild = interaction.guild
        member = guild.get_member(int(app["applicant_id"])) if guild else None
        if member is None:
            await interaction.response.send_message(f"{CLOSE} Applicant is no longer in Chatly.", ephemeral=True)
            return
        if app.get("route") == "Standard":
            role = self.find_role_by_rank(guild, 1)
            if role is None:
                await interaction.response.send_message(f"{CLOSE} The Junior Moderator role could not be found.", ephemeral=True)
                return
            try:
                await member.add_roles(role, reason=f"Chatly staff application {app_id} accepted")
            except discord.HTTPException:
                await interaction.response.send_message(f"{CLOSE} I could not assign the Junior Moderator role. Check the bot's role hierarchy.", ephemeral=True)
                return
        else:
            position = app.get("staff_position")
            role = self.find_role_by_name(guild, position) if position else None
            if role is None:
                await interaction.response.send_message(f"{CLOSE} The purchased staff position role could not be found.", ephemeral=True)
                return
            try:
                await member.add_roles(role, reason=f"Chatly direct staff application {app_id} accepted")
            except discord.HTTPException:
                await interaction.response.send_message(f"{CLOSE} I could not assign the selected staff role. Check the bot's role hierarchy.", ephemeral=True)
                return
        app["status"] = STATUS_ACCEPTED
        app["accepted_at"] = iso()
        app["accepted_by"] = interaction.user.id
        await self.save()
        await self.log_event(app, "Accepted", interaction.user.id, f"Position: {app.get('staff_position') or 'Junior Moderator'}")
        await self.log_full_application(app, "Accepted")
        await self.delete_application_message(app)
        welcome = self.bot.get_channel(STAFF_WELCOME_CHANNEL_ID)
        if welcome:
            await welcome.send(f"{TICK} Welcome {member.mention} to the Chatly staff team! You have been accepted as **{app.get('staff_position') or 'Junior Moderator'}**. Please review the Staff Guide and follow the staff code.")
        await self.send_applicant_dm(app, f"{TICK} Congratulations! Your Chatly staff application `{app_id}` has been accepted.\n\n**Position:** {app.get('staff_position') or 'Junior Moderator'}\n\nWelcome to the Chatly staff team. Your next step is to review the Staff Guide and staff code.")
        await interaction.response.send_message(f"{TICK} `{app_id}` accepted and the staff role has been assigned.", ephemeral=True)

    def find_role_by_rank(self, guild: discord.Guild, rank: int) -> Optional[discord.Role]:
        for role in guild.roles:
            if role_rank(role) == rank:
                return role
        return None

    def find_role_by_name(self, guild: discord.Guild, name: Optional[str]) -> Optional[discord.Role]:
        if not name:
            return None
        wanted = normalize_role_name(name)
        for role in guild.roles:
            if normalize_role_name(role.name) == wanted:
                return role
        return None

    async def staff_notes(self, interaction: discord.Interaction, app_id: str):
        if not is_higher_staff(interaction.user):
            await interaction.response.send_message(f"{LOCK} Staff notes are restricted to Owner/Co-Owner/Exec.", ephemeral=True)
            return
        app = self.get(app_id)
        if not app:
            await interaction.response.send_message(f"{CLOSE} Application not found.", ephemeral=True)
            return
        notes = app.get("notes", [])
        if not notes:
            description = "No staff notes have been added."
        else:
            description = "\n\n".join(f"**#{i+1}** — <@{n['author_id']}>\n{clean_text(n['text'], 600)}" for i, n in enumerate(notes[-10:]))
        await interaction.response.send_message(
            embed=discord.Embed(title=f"{MOD} Staff Notes · {app_id}", description=description, color=CHATLY_GREEN),
            view=StaffNotesView(self, app_id),
            ephemeral=True,
        )

    async def add_note(self, interaction: discord.Interaction, app_id: str, text: str):
        app = self.get(app_id)
        if not app or not is_higher_staff(interaction.user):
            await interaction.response.send_message(f"{LOCK} You are not authorized to add staff notes.", ephemeral=True)
            return
        app.setdefault("notes", []).append({"author_id": interaction.user.id, "text": clean_text(text, 2000), "created_at": iso()})
        await self.save()
        await self.log_event(app, "Staff Note Added", interaction.user.id, text)
        await interaction.response.send_message(f"{TICK} Staff note added.", ephemeral=True)

    async def edit_note(self, interaction: discord.Interaction, app_id: str, index: int, text: str):
        app = self.get(app_id)
        if not app or not is_higher_staff(interaction.user):
            await interaction.response.send_message(f"{LOCK} You are not authorized to edit staff notes.", ephemeral=True)
            return
        notes = app.get("notes", [])
        if index < 1 or index > len(notes):
            await interaction.response.send_message(f"{CLOSE} Note number not found.", ephemeral=True)
            return
        old = notes[index - 1].get("text", "")
        notes[index - 1]["text"] = clean_text(text, 2000)
        notes[index - 1]["edited_at"] = iso()
        notes[index - 1]["edited_by"] = interaction.user.id
        await self.save()
        await self.log_event(app, "Staff Note Edited", interaction.user.id, f"Note #{index}: {old} -> {text}")
        await interaction.response.send_message(f"{EDIT} Staff note #{index} updated.", ephemeral=True)

    async def delete_note(self, interaction: discord.Interaction, app_id: str, index: int):
        app = self.get(app_id)
        if not app or not is_higher_staff(interaction.user):
            await interaction.response.send_message(f"{LOCK} You are not authorized to delete staff notes.", ephemeral=True)
            return
        notes = app.get("notes", [])
        if index < 1 or index > len(notes):
            await interaction.response.send_message(f"{CLOSE} Note number not found.", ephemeral=True)
            return
        removed = notes.pop(index - 1)
        await self.save()
        await self.log_event(app, "Staff Note Deleted", interaction.user.id, f"Note #{index}: {removed.get('text', '')}")
        await interaction.response.send_message(f"{CLOSE} Staff note #{index} deleted from the active notes list. The deletion is logged.", ephemeral=True)

    async def cancel_application(self, interaction: discord.Interaction, app_id: str):
        if not is_final_reviewer(interaction.user):
            await interaction.response.send_message(f"{LOCK} Only Owner/Co-Owner/Exec can cancel applications.", ephemeral=True)
            return
        await interaction.response.send_modal(CancelApplicationModal(self, app_id))

    async def complete_cancel(self, interaction: discord.Interaction, app_id: str, reason: str):
        app = self.get(app_id)
        if not app:
            await interaction.response.send_message(f"{CLOSE} Application not found.", ephemeral=True)
            return
        app["status"] = STATUS_CANCELLED
        app["cancelled_at"] = iso()
        app["cancellation_reason"] = clean_text(reason, 2000)
        await self.save()
        await self.log_event(app, "Cancelled", interaction.user.id, reason)
        await self.log_full_application(app, "Cancelled")
        await self.delete_application_message(app)
        await interaction.response.send_message(f"{CLOSE} `{app_id}` cancelled and removed from the applications channel.", ephemeral=True)

    @tasks.loop(minutes=30)
    async def more_info_watcher(self):
        now = utc_now()
        changed = False
        for app in self.data["applications"].values():
            if app.get("status") != STATUS_MORE_INFO:
                continue
            deadline = parse_iso(app.get("more_info_deadline"))
            if deadline and deadline <= now:
                app["status"] = STATUS_INACTIVE
                app["inactive_at"] = iso()
                app["more_info_deadline"] = None
                changed = True
                await self.log_event(app, "Inactive — More Information Deadline Expired", None, "No response within 7 days")
                await self.delete_application_message(app)
                await self.send_applicant_dm(app, f"{INFO} Your staff application `{app['application_id']}` is now **Inactive** because the requested information was not received within 7 days. You may apply again normally.")
        if changed:
            await self.save()

    @more_info_watcher.before_loop
    async def before_more_info_watcher(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="setup-staff-applications", description="Post the Chatly Apply for Staff panel.")
    async def setup_staff_applications(self, interaction: discord.Interaction):
        if not interaction.guild or interaction.guild.id != GUILD_ID:
            await interaction.response.send_message(f"{CLOSE} This command can only be used in Chatly.", ephemeral=True)
            return
        if not is_final_reviewer(interaction.user):
            await interaction.response.send_message(f"{LOCK} Owner/Co-Owner/Exec only.", ephemeral=True)
            return
        embed = discord.Embed(
            title=f"{MOD} Apply for Staff",
            description=(
                "Interested in joining the Chatly staff team?\n\n"
                "Choose the standard staff application route below, or explore the direct staff route if you want to purchase a staff position.\n\n"
                f"{INFO} Standard applications begin at **Junior Moderator** and are reviewed by the staff team."
            ),
            color=CHATLY_GREEN,
        )
        await interaction.channel.send(embed=embed, view=StaffApplicationPanelView(self))
        await interaction.response.send_message(f"{TICK} Apply for Staff panel posted.", ephemeral=True)

    @app_commands.command(name="staff-application-status", description="View your current Chatly staff application status.")
    async def staff_application_status(self, interaction: discord.Interaction):
        app = self.active_for(interaction.user.id)
        if not app:
            await interaction.response.send_message(f"{INFO} You do not have an active staff application.", ephemeral=True)
            return
        await interaction.response.send_message(
            embed=discord.Embed(title=f"{MOD} Staff Application Status", description=f"Application: `{app['application_id']}`\nStatus: **{app['status']}**", color=CHATLY_GREEN),
            ephemeral=True,
        )


# ============================================================
# Persistent views
# ============================================================

class StaffApplicationPanelView(discord.ui.View):
    def __init__(self, cog: StaffApplicationCog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Apply for Staff", emoji=MOD, style=discord.ButtonStyle.primary, custom_id="chatly_staff_apply_standard")
    async def standard(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.start_application(interaction, "Standard")

    @discord.ui.button(label="Direct Staff", emoji=STARS, style=discord.ButtonStyle.secondary, custom_id="chatly_staff_apply_direct")
    async def direct(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(f"{CLOSE} This can only be used inside Chatly.", ephemeral=True)
            return
        member = interaction.user
        age_ok = age_is_eligible(member)
        verified = interaction.guild.get_role(VERIFIED_ROLE_ID) in member.roles
        if not age_ok or not verified:
            if age_ok and not verified:
                channel = interaction.guild.get_channel(DEFAULT_VERIFICATION_CHANNEL_ID)
                location = channel.mention if channel else f"<#${DEFAULT_VERIFICATION_CHANNEL_ID}>".replace("$", "")
                await interaction.response.send_message(
                    f"{CLOSE} Direct Staff still requires **age eligibility and Chatly verification**.\n\n"
                    f"{TICK} Your age eligibility is valid.\n"
                    f"{INFO} You are not verified yet. Complete verification in {location}.",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    f"{CLOSE} Direct Staff still requires **age eligibility and Chatly verification**.\n\n"
                    f"{INFO} You must have an eligible **16+ Chatly age role** and be verified.",
                    ephemeral=True,
                )
            return
        embed = discord.Embed(
            title=f"{STARS} Direct Staff",
            description="Select the staff position you want to purchase.",
            color=CHATLY_GREEN,
        )
        if DIRECT_STAFF_PRICING_IMAGE_URL:
            embed.set_image(url=DIRECT_STAFF_PRICING_IMAGE_URL)
        await interaction.response.send_message(embed=embed, view=DirectStaffPositionView(self.cog), ephemeral=True)


class DirectStaffPositionView(discord.ui.View):
    def __init__(self, cog: StaffApplicationCog):
        super().__init__(timeout=300)
        self.cog = cog
        options = [
            ("Owner", "9,500"), ("Co-Owner", "2,000"), ("Executive", "1,500"), ("Manager", "1,100"),
            ("Admin", "700"), ("Sr. Moderator", "450"), ("Moderator", "300"), ("Junior Moderator", "200"),
        ]
        self.select = discord.ui.Select(placeholder="Select a Staff Position", options=[discord.SelectOption(label=n, description=f"${p}") for n, p in options])
        self.select.callback = self.callback
        self.add_item(self.select)

    async def callback(self, interaction: discord.Interaction):
        position = self.select.values[0]
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(f"{CLOSE} This can only be used inside Chatly.", ephemeral=True)
            return
        active = self.cog.active_for(interaction.user.id)
        if active:
            await interaction.response.send_message(f"{INFO} You already have an active application: `{active['application_id']}`.", ephemeral=True)
            return
        # Payment must happen before application/interview. This build records the selected position;
        # actual payment verification remains external to this application workflow.
        await self.cog.start_direct_position_application(interaction, position)


class DirectApplicationContinueView(discord.ui.View):
    def __init__(self, cog, app_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.app_id = app_id

    @discord.ui.button(label="Continue Direct Staff Application", emoji=STARS, style=discord.ButtonStyle.primary, custom_id="chatly_direct_staff_continue")
    async def continue_application(self, interaction, button):
        app = self.cog.get(self.app_id)
        if not app or app.get("payment_status") != "Verified":
            await interaction.response.send_message(f"{CLOSE} This Direct Staff application is not available.", ephemeral=True)
            return
        await interaction.response.send_modal(DirectStaffApplicationModal(self.cog, self.app_id))


class FinalSubmitView(discord.ui.View):
    def __init__(self, cog, app_id):
        super().__init__(timeout=300)
        self.cog = cog
        self.app_id = app_id

    @discord.ui.button(label="Submit Application", emoji=TICK, style=discord.ButtonStyle.success)
    async def submit(self, interaction, button):
        await self.cog.submit_application(interaction, self.app_id)

    @discord.ui.button(label="Withdraw", emoji=CLOSE, style=discord.ButtonStyle.secondary)
    async def withdraw(self, interaction, button):
        app = self.cog.get(self.app_id)
        if not app or app.get("applicant_id") != interaction.user.id:
            await interaction.response.send_message(f"{CLOSE} You cannot withdraw this application.", ephemeral=True)
            return
        await interaction.response.send_message(f"{INFO} Are you sure you want to withdraw `{self.app_id}`?", view=ConfirmWithdrawView(self.cog, self.app_id), ephemeral=True)


class ConfirmWithdrawView(discord.ui.View):
    def __init__(self, cog, app_id):
        super().__init__(timeout=120)
        self.cog = cog
        self.app_id = app_id

    @discord.ui.button(label="Confirm Withdrawal", emoji=CLOSE, style=discord.ButtonStyle.danger)
    async def confirm(self, interaction, button):
        await self.cog.withdraw(interaction, self.app_id)

    @discord.ui.button(label="Cancel", emoji=REFRESH, style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction, button):
        await interaction.response.edit_message(content=f"{INFO} Withdrawal cancelled.", view=None)


class ApplicationReviewView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Upvote", emoji=UPVOTE, style=discord.ButtonStyle.secondary, custom_id="chatly_staff_vote_up")
    async def upvote(self, interaction, button):
        app = self.cog.application_from_message(interaction)
        if app: await self.cog.vote(interaction, app["application_id"], "upvote")

    @discord.ui.button(label="Dislike", emoji=DISLIKE, style=discord.ButtonStyle.secondary, custom_id="chatly_staff_vote_down")
    async def dislike(self, interaction, button):
        app = self.cog.application_from_message(interaction)
        if app: await self.cog.vote(interaction, app["application_id"], "dislike")

    @discord.ui.button(label="Approve", emoji=TICK, style=discord.ButtonStyle.success, custom_id="chatly_staff_approve", row=1)
    async def approve(self, interaction, button):
        app = self.cog.application_from_message(interaction)
        if app: await self.cog.approve(interaction, app["application_id"])

    @discord.ui.button(label="Deny", emoji=DISLIKE, style=discord.ButtonStyle.danger, custom_id="chatly_staff_deny", row=1)
    async def deny(self, interaction, button):
        app = self.cog.application_from_message(interaction)
        if app: await self.cog.deny(interaction, app["application_id"])

    @discord.ui.button(label="More Information", emoji=INFO, style=discord.ButtonStyle.secondary, custom_id="chatly_staff_more_info", row=1)
    async def more_info(self, interaction, button):
        app = self.cog.application_from_message(interaction)
        if app: await self.cog.request_more_info(interaction, app["application_id"])

    @discord.ui.button(label="Interview Outcome", emoji=QUESTION, style=discord.ButtonStyle.primary, custom_id="chatly_staff_interview", row=2)
    async def interview(self, interaction, button):
        app = self.cog.application_from_message(interaction)
        if not app:
            return
        await interaction.response.send_message(f"{QUESTION} Select the interview outcome for `{app['application_id']}`.", view=InterviewOutcomeView(self.cog, app["application_id"]), ephemeral=True)

    @discord.ui.button(label="Staff Notes", emoji=MOD, style=discord.ButtonStyle.secondary, custom_id="chatly_staff_notes", row=2)
    async def notes(self, interaction, button):
        app = self.cog.application_from_message(interaction)
        if app: await self.cog.staff_notes(interaction, app["application_id"])

    @discord.ui.button(label="Cancel Application", emoji=CLOSE, style=discord.ButtonStyle.secondary, custom_id="chatly_staff_cancel", row=2)
    async def cancel(self, interaction, button):
        app = self.cog.application_from_message(interaction)
        if app: await self.cog.cancel_application(interaction, app["application_id"])


class InterviewOutcomeView(discord.ui.View):
    def __init__(self, cog, app_id):
        super().__init__(timeout=180)
        self.cog = cog
        self.app_id = app_id

    @discord.ui.button(label="Accept", emoji=TICK, style=discord.ButtonStyle.success)
    async def accept(self, interaction, button):
        await self.cog.interview_outcome(interaction, self.app_id, "accept")

    @discord.ui.button(label="Deny", emoji=DISLIKE, style=discord.ButtonStyle.danger)
    async def deny(self, interaction, button):
        await self.cog.interview_outcome(interaction, self.app_id, "deny")

    @discord.ui.button(label="Request Another Interview", emoji=REFRESH, style=discord.ButtonStyle.secondary)
    async def request(self, interaction, button):
        await self.cog.interview_outcome(interaction, self.app_id, "request")


class StaffNotesView(discord.ui.View):
    def __init__(self, cog, app_id):
        super().__init__(timeout=300)
        self.cog = cog
        self.app_id = app_id

    @discord.ui.button(label="Add Note", emoji=EDIT, style=discord.ButtonStyle.primary)
    async def add(self, interaction, button):
        await interaction.response.send_modal(AddNoteModal(self.cog, self.app_id))

    @discord.ui.button(label="Edit Note", emoji=EDIT, style=discord.ButtonStyle.secondary)
    async def edit(self, interaction, button):
        await interaction.response.send_modal(EditNoteModal(self.cog, self.app_id))

    @discord.ui.button(label="Delete Note", emoji=CLOSE, style=discord.ButtonStyle.danger)
    async def delete(self, interaction, button):
        await interaction.response.send_modal(DeleteNoteModal(self.cog, self.app_id))


class MoreInfoResponseView(discord.ui.View):
    def __init__(self, cog, app_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.app_id = app_id

    @discord.ui.button(label="Provide Information", emoji=INFO, style=discord.ButtonStyle.primary, custom_id="chatly_staff_more_info_response")
    async def respond(self, interaction, button):
        await interaction.response.send_modal(MoreInfoResponseModal(self.cog, self.app_id))


# -------------------------
# Modals
# -------------------------

class DirectStaffApplicationModal(discord.ui.Modal, title="Direct Staff Application"):
    def __init__(self, cog, app_id):
        super().__init__()
        self.cog = cog
        self.app_id = app_id
        self.about = discord.ui.TextInput(label="Tell us a little about yourself", style=discord.TextStyle.paragraph, max_length=1200)
        self.experience = discord.ui.TextInput(label="Previous staff / moderation experience", style=discord.TextStyle.paragraph, required=False, max_length=1200)
        self.availability = discord.ui.TextInput(label="Usual availability for Chatly", style=discord.TextStyle.paragraph, max_length=700)
        self.motivation = discord.ui.TextInput(label="Why do you want this staff position?", style=discord.TextStyle.paragraph, max_length=1200)
        self.anything = discord.ui.TextInput(label="Anything else we should know?", style=discord.TextStyle.paragraph, required=False, max_length=1200)
        for item in (self.about, self.experience, self.availability, self.motivation, self.anything):
            self.add_item(item)

    async def on_submit(self, interaction):
        await self.cog.collect_direct_answers(interaction, self.app_id, {
            "about": self.about.value,
            "experience": self.experience.value,
            "availability": self.availability.value,
            "motivation": self.motivation.value,
            "anything_else": self.anything.value,
        })


class StaffApplicationModalOne(discord.ui.Modal, title="Apply for Staff · 1/2"):
    def __init__(self, cog, app_id):
        super().__init__()
        self.cog = cog
        self.app_id = app_id
        self.about = discord.ui.TextInput(label="Tell us a little about yourself", style=discord.TextStyle.paragraph, max_length=1500)
        self.interests = discord.ui.TextInput(label="Main interests / hobbies", style=discord.TextStyle.paragraph, max_length=1000)
        self.experience = discord.ui.TextInput(label="Previous staff / moderation experience", style=discord.TextStyle.paragraph, required=False, max_length=1500)
        self.learned = discord.ui.TextInput(label="What did you learn from it?", style=discord.TextStyle.paragraph, required=False, max_length=1500)
        self.timezone = discord.ui.TextInput(label="What timezone are you in?", max_length=100)
        for item in (self.about, self.interests, self.experience, self.learned, self.timezone):
            self.add_item(item)

    async def on_submit(self, interaction):
        await self.cog.collect_answers_one(interaction, self.app_id, {
            "about": self.about.value,
            "interests": self.interests.value,
            "experience": self.experience.value,
            "experience_learned": self.learned.value,
            "timezone": self.timezone.value,
        })


class StaffApplicationModalTwo(discord.ui.Modal, title="Apply for Staff · 2/2"):
    def __init__(self, cog, app_id):
        super().__init__()
        self.cog = cog
        self.app_id = app_id
        self.time = discord.ui.TextInput(label="Time you can regularly dedicate", style=discord.TextStyle.paragraph, max_length=500)
        self.availability = discord.ui.TextInput(label="Usual availability", style=discord.TextStyle.paragraph, max_length=700)
        self.motivation = discord.ui.TextInput(label="Why do you want to become Chatly staff?", style=discord.TextStyle.paragraph, max_length=1500)
        self.contribution = discord.ui.TextInput(label="What could you contribute to the staff team?", style=discord.TextStyle.paragraph, max_length=1500)
        self.anything = discord.ui.TextInput(label="Anything else we should know?", style=discord.TextStyle.paragraph, required=False, max_length=1500)
        for item in (self.time, self.availability, self.motivation, self.contribution, self.anything):
            self.add_item(item)

    async def on_submit(self, interaction):
        await self.cog.collect_answers_two(interaction, self.app_id, {
            "time": self.time.value,
            "availability": self.availability.value,
            "motivation": self.motivation.value,
            "contribution": self.contribution.value,
            "anything_else": self.anything.value,
        })


class DenialReasonModal(discord.ui.Modal, title="Deny Application"):
    reason = discord.ui.TextInput(label="Denial reason (optional)", style=discord.TextStyle.paragraph, required=False, max_length=2000)
    def __init__(self, cog, app_id):
        super().__init__()
        self.cog = cog
        self.app_id = app_id
    async def on_submit(self, interaction):
        await self.cog.complete_denial(interaction, self.app_id, self.reason.value)


class MoreInfoModal(discord.ui.Modal, title="Request More Information"):
    request = discord.ui.TextInput(label="What information is needed?", style=discord.TextStyle.paragraph, max_length=2000)
    def __init__(self, cog, app_id):
        super().__init__()
        self.cog = cog
        self.app_id = app_id
    async def on_submit(self, interaction):
        await self.cog.set_more_info(interaction, self.app_id, self.request.value)


class MoreInfoResponseModal(discord.ui.Modal, title="Additional Information"):
    response = discord.ui.TextInput(label="Your response", style=discord.TextStyle.paragraph, max_length=4000)
    def __init__(self, cog, app_id):
        super().__init__()
        self.cog = cog
        self.app_id = app_id
    async def on_submit(self, interaction):
        await self.cog.submit_more_info(interaction, self.app_id, self.response.value)


class InterviewDenyModal(discord.ui.Modal, title="Interview Denial"):
    reason = discord.ui.TextInput(label="Denial reason (optional)", style=discord.TextStyle.paragraph, required=False, max_length=2000)
    def __init__(self, cog, app_id):
        super().__init__()
        self.cog = cog
        self.app_id = app_id
    async def on_submit(self, interaction):
        await self.cog.complete_denial(interaction, self.app_id, self.reason.value)


class AddNoteModal(discord.ui.Modal, title="Add Staff Note"):
    note = discord.ui.TextInput(label="Staff note", style=discord.TextStyle.paragraph, max_length=2000)
    def __init__(self, cog, app_id):
        super().__init__()
        self.cog = cog
        self.app_id = app_id
    async def on_submit(self, interaction):
        await self.cog.add_note(interaction, self.app_id, self.note.value)


class EditNoteModal(discord.ui.Modal, title="Edit Staff Note"):
    number = discord.ui.TextInput(label="Note number", max_length=5)
    text = discord.ui.TextInput(label="Updated note", style=discord.TextStyle.paragraph, max_length=2000)
    def __init__(self, cog, app_id):
        super().__init__()
        self.cog = cog
        self.app_id = app_id
    async def on_submit(self, interaction):
        try:
            number = int(self.number.value)
        except ValueError:
            await interaction.response.send_message(f"{CLOSE} Note number must be numeric.", ephemeral=True)
            return
        await self.cog.edit_note(interaction, self.app_id, number, self.text.value)


class DeleteNoteModal(discord.ui.Modal, title="Delete Staff Note"):
    number = discord.ui.TextInput(label="Note number", max_length=5)
    def __init__(self, cog, app_id):
        super().__init__()
        self.cog = cog
        self.app_id = app_id
    async def on_submit(self, interaction):
        try:
            number = int(self.number.value)
        except ValueError:
            await interaction.response.send_message(f"{CLOSE} Note number must be numeric.", ephemeral=True)
            return
        await self.cog.delete_note(interaction, self.app_id, number)


class CancelApplicationModal(discord.ui.Modal, title="Cancel Application"):
    reason = discord.ui.TextInput(label="Cancellation reason", style=discord.TextStyle.paragraph, max_length=2000)
    def __init__(self, cog, app_id):
        super().__init__()
        self.cog = cog
        self.app_id = app_id
    async def on_submit(self, interaction):
        await self.cog.complete_cancel(interaction, self.app_id, self.reason.value)


# -------------------------
# Message-to-application lookup
# -------------------------

def _app_from_message(cog: StaffApplicationCog, interaction: discord.Interaction) -> Optional[dict]:
    message_id = interaction.message.id if interaction.message else None
    if not message_id:
        return None
    for app in cog.data["applications"].values():
        if int(app.get("message_id", 0)) == message_id:
            return app
    return None


StaffApplicationCog.application_from_message = _app_from_message


async def setup(bot: commands.Bot):
    await bot.add_cog(StaffApplicationCog(bot))
