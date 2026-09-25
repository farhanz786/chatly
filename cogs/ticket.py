import asyncio

import base64
import difflib

import io

import json

import html

import re

from datetime import datetime, timedelta, timezone

from pathlib import Path



import discord

from discord import app_commands

from discord.ext import commands, tasks



# ============================================================

# Chatly Support / Report System

# ============================================================

# This cog is intentionally self-contained.

#

# Add to bot.py:

#     await self.load_extension("cogs.ticket")

#

# Then restart the bot and run:

#     /support setup

# in the channel where you want the Support panel.

# ============================================================



OWNER_ID = 937242913535033404



# Categories

REPORT_CATEGORY_ID = 1503429487633764392

PREMIUM_REPORT_CATEGORY_ID = 1526215939501064273



# Ticket log channel

TICKET_LOG_CHANNEL_ID = 1525107026642862191



# Premium role

PREMIUM_ROLE_ID = 1503429265415471224



# Support emoji IDs

LOCK_EMOJI = "<:lock:1551275905253511238>"

FOLDER_EMOJI = "<:folder:1550538040819318904>"

TICK_EMOJI = "<:tick:1550538067570335764>"

CLOSE_EMOJI = "<:close:1550533713526399126>"

USER_EMOJI = "<:user:1550286898126262312>"

INFO_EMOJI = "<:info:1550551426269319168>"

QUESTION_EMOJI = "<:question:1550551387371343883>"

FLAG_EMOJI = "<:flag:1550551309260693607>"

CONVERSATION_EMOJI = "<:conversation:1550919322476478504>"

NET_EMOJI = "<:net:1551289650969190511>"

MEGAPHONE_EMOJI = "<:megaphone:1551292666753327135>"

SKULL_EMOJI = "<:skull:1550551579751485642>"

PAYMENT_EMOJI = "<:paypal:1550551525204566057>"

SETTINGS_EMOJI = "<:setting:1550551557437661294>"

LINK_EMOJI = "<:link:1550536411189616670>"

EDIT_EMOJI = "<:edit:1550277007961755658>"

DISLIKE_EMOJI = "<:dislike:1550544099214495774>"

BAN_EMOJI = "<:ban:1550542161924325388>"

CHAT_EMOJI = "<:chat:1550278354840588319>"

VC_EMOJI = "<:vc:1550285799306698843>"

EVENT_EMOJI = "<:event:1550282823242485820>"

DELETE_EMOJI = "<:delete:1550282755017810070>"
CODE_EMOJI = "<:code:1550540317298786394>"
MOD_EMOJI = "<:mod:1550551457109901435>"
COINS_EMOJI = "<:chatly_coins:1550907460959866991>"
XP_EMOJI = "<:upvote:1550551638387990620>"
PREMIUM_EMOJI = "<:star:1550289395800743956>"
GAMING_EMOJI = "<:gaming:1550285815303770205>"
STARS_EMOJI = "<:stars:1550289412624093234>"
DOUBLE_TICK_EMOJI = "<:double_tick:1529222183698563174>"

CHATLY_GREEN = 0x52FB18

SUPPORT_HEADER_URL = "https://media.discordapp.net/attachments/1010905558624239739/1551246544844488814/ChatGPT_Image_Sep_20_2026_08_29_36_PM.png?ex=6ab1466d&is=6aaff4ed&hm=e0d0e761bb09f896027dd6723840be743c74a2f2efdc22a0405928e05ca6a170&=&format=webp&quality=lossless"

SUPPORT_DIVIDER_URL = "https://cdn.discordapp.com/attachments/1010905558624239739/1550541547219456132/dividerqwe_1.jpg?ex=6ab0b018&is=6aaf5e98&hm=4420ec9de24193270c812e912f542e4d5a1cf51d9a1b20bd1cd9214faa548bcd"
SUPPORT_THUMBNAIL_URL = "https://media.discordapp.net/attachments/1550931987706028052/1551307824879902851/ChatGPT_Image_Sep_21_2026_12_33_13_AM.png?ex=6ab17f7f&is=6ab02dff&hm=f4bba26dc6b49a39ea7ec4b2075190a9a8d36f66abd1eb3211c5ecbeb2812f49&=&format=webp&quality=lossless"



# Files live beside the bot's working directory.

TICKET_DATA_FILE = Path("support_tickets.json")

TICKET_COUNTER_FILE = Path("support_ticket_counter.json")



AUTO_CLOSE_SECONDS = 24 * 60 * 60

EVIDENCE_PING_COOLDOWN_SECONDS = 60





REPORT_REASONS = [

    (FLAG_EMOJI, "NSFW / Sexual Content"),

    ("<:exclaimation:1550544117249998878>", "Harassment / Bullying"),

    (DISLIKE_EMOJI, "Hate Speech / Discrimination"),

    (BAN_EMOJI, "Threats / Stalking / Blackmail"),

    (USER_EMOJI, "Impersonation"),

    (EDIT_EMOJI, "Inappropriate Profile"),

    (CHAT_EMOJI, "Spam / Flooding"),

    (MEGAPHONE_EMOJI, "Unauthorized Advertising"),

    (LINK_EMOJI, "Scam / Phishing / Malicious Content"),

    (VC_EMOJI, "Voice Chat Disruption"),

    ("<:exclaimation:1550544117249998878>", "Raiding / Mass Pinging"),

    (BAN_EMOJI, "Ban / Punishment Evasion"),

    (USER_EMOJI, "Underage User"),

    (LOCK_EMOJI, "Sharing Personal / Sensitive Information"),

    (EVENT_EMOJI, "Event / Activity Disruption"),

    (SKULL_EMOJI, "Predatory / Suspicious Behavior"),

    (DELETE_EMOJI, "Community Sabotage"),

    (FLAG_EMOJI, "Illegal Content / Activity"),

    ("<:exclaimation:1550544117249998878>", "Other"),

]



STAFF_CLOSE_REASONS = [

    "Inactive",

    "Troll / Misuse",

    "User Left Server",

    "No Evidence",

    "Duplicate Report",

    "Resolved / Action Completed",

    "Invalid Report",

    "Specify",

]



BUG_CATEGORIES = [
    (CODE_EMOJI, "Bot / Commands"),
    (MOD_EMOJI, "Moderation"),
    (COINS_EMOJI, "Economy / Chat Coins"),
    (XP_EMOJI, "XP / Levels"),
    (PREMIUM_EMOJI, "Premium"),
    (USER_EMOJI, "Profiles"),
    (CONVERSATION_EMOJI, "Tickets / Support"),
    (USER_EMOJI, "Roles / Self Roles"),
    (GAMING_EMOJI, "Gaming / Activities"),
    (CHAT_EMOJI, "Chat / Messaging"),
    (VC_EMOJI, "Voice / Voice Messages"),
    (MEGAPHONE_EMOJI, "Notifications / Announcements"),
    (EVENT_EMOJI, "Events / Rewards"),
    (STARS_EMOJI, "Server / Community Features"),
    (LOCK_EMOJI, "Permissions / Access"),
    (LINK_EMOJI, "Website / External Services"),
    (SETTINGS_EMOJI, "Other System"),
    (QUESTION_EMOJI, "Other — Specify where you experienced the bug"),
]

BUG_CLOSE_REASONS = [
    "Inactive", "Troll / Misuse", "Duplicate Bug", "User Left Server",
    "Unable to Reproduce", "Invalid Bug Report", "Fixed / Fix Confirmed", "Specify",
]

GENERAL_CLOSE_REASONS = [
    "Issue Resolved", "No Longer Need Help", "User Left Server",
    "Duplicate Request", "Invalid Request", "Troll / Misuse", "Specify",
]

REPORTER_CLOSE_REASONS = [

    "Issue Resolved",

    "No Longer Need Help",

    "Submitted by Mistake",

    "Duplicate / Already Reported",

    "Other",

]





def utc_now() -> datetime:

    return datetime.now(timezone.utc)





def iso(dt: datetime) -> str:

    return dt.astimezone(timezone.utc).isoformat()





def display_time(dt: datetime) -> str:

    return discord.utils.format_dt(dt, "F")





def load_json(path: Path, default):

    try:

        if not path.exists():

            return default

        return json.loads(path.read_text(encoding="utf-8"))

    except Exception:

        return default





def save_json(path: Path, data):

    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")





def is_admin(member: discord.Member) -> bool:

    return member.guild_permissions.administrator





def is_staff(member: discord.Member) -> bool:

    # Moderator+ is represented by normal Discord moderation/admin

    # permissions so this cog does not depend on undocumented role IDs.

    perms = member.guild_permissions

    return (

        perms.administrator

        or perms.manage_guild

        or perms.manage_channels

        or perms.manage_messages

        or perms.kick_members

        or perms.ban_members

    )





def has_premium(member: discord.Member) -> bool:

    return any(role.id == PREMIUM_ROLE_ID for role in member.roles)





def safe_channel_name(username: str) -> str:

    cleaned = "".join(ch for ch in username if ch.isalnum() or ch in "-_.")

    cleaned = cleaned[:80] or "user"

    return f"❗ㆍ{cleaned}"





def safe_bug_channel_name(username: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]", "-", username.lower())
    cleaned = re.sub(r"-+", "-", cleaned).strip("-_.")
    return (f"🐛・{cleaned[:92] or 'user'}")[:100]



def permission_overwrites(

    guild: discord.Guild,

    reporter: discord.Member,

    bot_member: discord.Member,

) -> dict:

    overwrites = {

        guild.default_role: discord.PermissionOverwrite(view_channel=False),

        reporter: discord.PermissionOverwrite(

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

            manage_channels=True,

            manage_messages=True,

            attach_files=True,

            embed_links=True,

        ),

    }



    # Give all current Moderator+ members access through permission checks

    # rather than requiring hard-coded role IDs.

    for member in guild.members:

        if member.bot or member.id == reporter.id:

            continue

        if is_staff(member):

            overwrites[member] = discord.PermissionOverwrite(

                view_channel=True,

                send_messages=True,

                read_message_history=True,

                attach_files=True,

                embed_links=True,

            )

    return overwrites





class PersistentView(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=None)





class SupportMainView(PersistentView):

    @discord.ui.button(

        label="Report Member",

        emoji=FLAG_EMOJI,

        style=discord.ButtonStyle.secondary,

        custom_id="chatly_support_report",

        row=0,

    )

    async def report_member(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_message(

            embed=discord.Embed(

                title=f"{USER_EMOJI} Member Report",

                description="Select the member you want to report.",

                color=CHATLY_GREEN,

            ),

            view=ReportMemberSelectView(),

            ephemeral=True,

        )



    @discord.ui.button(

        label="Bug Report",

        emoji=NET_EMOJI,

        style=discord.ButtonStyle.secondary,

        custom_id="chatly_support_bug",

        row=0,

    )

    async def bug_report(self, interaction: discord.Interaction, button: discord.ui.Button):

        embed = discord.Embed(

            title=f"{NET_EMOJI} Bug Report",

            description="Select the category that best matches where you experienced the bug.",

            color=CHATLY_GREEN,

        )

        await interaction.response.send_message(

            embed=embed,

            view=BugCategoryView(),

            ephemeral=True,

        )



    @discord.ui.button(

        label="General Support",

        emoji=QUESTION_EMOJI,

        style=discord.ButtonStyle.secondary,

        custom_id="chatly_support_general",

        row=1,

    )

    async def general_support(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_modal(GeneralSupportModal())



    @discord.ui.button(

        label="Payment & Business",

        emoji=PAYMENT_EMOJI,

        style=discord.ButtonStyle.secondary,

        custom_id="chatly_support_payment",

        row=1,

    )

    async def payment_business(self, interaction: discord.Interaction, button: discord.ui.Button):

        embed = discord.Embed(
            title=f"{PAYMENT_EMOJI} Payment & Business",
            description=(
                "For payment, advertising, partnerships, or other business enquiries, "
                "please contact <@937242913535033404> directly. I’m always open to "
                "discussing new opportunities and working together."
            ),
            color=CHATLY_GREEN,
        )
        await interaction.response.send_message(
            embed=embed,
            view=BusinessResourcesView(),
            ephemeral=True,
        )



    @discord.ui.button(

        label="Forms",

        emoji=FOLDER_EMOJI,

        style=discord.ButtonStyle.secondary,

        custom_id="chatly_support_forms",

        row=2,

    )

    async def forms(self, interaction: discord.Interaction, button: discord.ui.Button):

        embed = discord.Embed(

            title=f"{FOLDER_EMOJI} Forms",

            description="Select a form below.",

            color=CHATLY_GREEN,

        )

        view = FormsView()

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)



    @discord.ui.button(

        label="Other Support",

        emoji=SETTINGS_EMOJI,

        style=discord.ButtonStyle.secondary,

        custom_id="chatly_support_other",

        row=2,

    )

    async def other_support(self, interaction: discord.Interaction, button: discord.ui.Button):

        await placeholder(interaction, "Other Support")





class BusinessResourcesView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(AdditionalLinksButton())


class AdditionalLinksButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Additional Links",
            emoji=FOLDER_EMOJI,
            style=discord.ButtonStyle.secondary,
            custom_id="chatly_business_additional_links",
        )

    async def callback(self, interaction: discord.Interaction):
        view = discord.ui.View(timeout=300)
        view.add_item(discord.ui.Button(label="Create an Ad", emoji=PAYMENT_EMOJI, style=discord.ButtonStyle.link, url="https://discord.com/channels/1467231978813128834/1503429553643589755"))
        view.add_item(discord.ui.Button(label="Get a Custom Role", emoji=USER_EMOJI, style=discord.ButtonStyle.link, url="https://discord.com/channels/1467231978813128834/1503429513667674152"))
        view.add_item(discord.ui.Button(label="Get Chatly Premium", emoji=DOUBLE_TICK_EMOJI, style=discord.ButtonStyle.link, url="https://discord.com/channels/1467231978813128834/1503429504528548023"))
        await interaction.response.edit_message(view=view)

class FormsView(PersistentView):

    @discord.ui.button(
        label="Apply for Staff",
        emoji=MOD_EMOJI,
        style=discord.ButtonStyle.secondary,
        custom_id="chatly_form_staff",
    )
    async def staff(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("StaffApplicationCog")
        if cog is None:
            await interaction.response.send_message(
                f"{INFO_EMOJI} The Staff Application system is currently unavailable.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"{MOD_EMOJI} Apply for Staff",
                description=(
                    "Choose how you want to join the Chatly staff team.\n\n"
                    f"{MOD_EMOJI} **Apply for Staff** — Standard route starting at Junior Moderator.\n"
                    f"{STARS_EMOJI} **Direct Staff** — Select a staff position through the paid/direct route."
                ),
                color=CHATLY_GREEN,
            ),
            view=cog.__class__.__dict__["__name__"] and cog.panel_view(),
            ephemeral=True,
        )





async def placeholder(interaction: discord.Interaction, name: str):

    await interaction.response.send_message(

        f"{INFO_EMOJI} **{name}**\n\nThis support option is coming soon.",

        ephemeral=True,

    )





class ReportMemberSelectView(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=180)

        self.add_item(ReportedUserSelect())





class ReportedUserSelect(discord.ui.UserSelect):

    def __init__(self):

        super().__init__(

            placeholder="Select the member you want to report",

            min_values=1,

            max_values=1,

            custom_id="chatly_reported_user_select",

        )



    async def callback(self, interaction: discord.Interaction):

        user = self.values[0]

        if user.id == interaction.user.id:

            await interaction.response.send_message(

                "You cannot report yourself.",

                ephemeral=True,

            )

            return



        await interaction.response.send_message(

            embed=discord.Embed(

                title=f"{FLAG_EMOJI} Select Report Reason",

                description="Choose the reason that best describes the report.",

                color=CHATLY_GREEN,

            ),

            view=ReportReasonView(user),

            ephemeral=True,

        )





class ReportReasonSelect(discord.ui.Select):

    def __init__(self, reported_user: discord.Member):

        self.reported_user = reported_user

        options = [

            discord.SelectOption(

                label=name,

                value=name,

                emoji=emoji,

            )

            for emoji, name in REPORT_REASONS

        ]

        super().__init__(

            placeholder="Select a report reason",

            min_values=1,

            max_values=1,

            options=options,

            custom_id=f"chatly_report_reason_{reported_user.id}",

        )



    async def callback(self, interaction: discord.Interaction):

        reason = self.values[0]

        if reason == "Other":

            await interaction.response.send_modal(

                OtherReportReasonModal(self.reported_user)

            )

            return



        cog = interaction.client.get_cog("Support")

        if cog is None:

            await interaction.response.send_message(

                "The Support system is unavailable right now.",

                ephemeral=True,

            )

            return



        await cog.create_report_ticket(

            interaction=interaction,

            reported_user=self.reported_user,

            reason=reason,

            custom_details=None,

        )





class ReportReasonView(discord.ui.View):

    def __init__(self, reported_user: discord.Member):

        super().__init__(timeout=180)

        self.add_item(ReportReasonSelect(reported_user))





class OtherReportReasonModal(discord.ui.Modal, title="Other Report Reason"):

    details = discord.ui.TextInput(

        label="Explain the reason for this report",

        style=discord.TextStyle.paragraph,

        placeholder="Describe what happened and why you are reporting this member.",

        required=True,

        max_length=4000,

    )



    async def on_submit(self, interaction: discord.Interaction):

        cog = interaction.client.get_cog("Support")

        if cog is None:

            await interaction.response.send_message(

                "The Support system is unavailable right now.",

                ephemeral=True,

            )

            return



        await cog.create_report_ticket(

            interaction=interaction,

            reported_user=self.reported_user,

            reason="Other",

            custom_details=self.details.value,

        )



    def __init__(self, reported_user: discord.Member):

        super().__init__()

        self.reported_user = reported_user





class BugCategoryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(BugCategorySelect())


class BugCategorySelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=name, value=name, emoji=emoji) for emoji, name in BUG_CATEGORIES]
        super().__init__(placeholder="Select a bug category", min_values=1, max_values=1, options=options, custom_id="chatly_bug_category_select")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(BugReportModal(self.values[0]))


class BugReportModal(discord.ui.Modal, title="Bug Report Details"):
    def __init__(self, category: str):
        super().__init__(); self.category=category
        self.title_input=discord.ui.TextInput(label="Bug Title", placeholder="Give the bug a short, clear title.", required=True, max_length=100)
        self.description_input=discord.ui.TextInput(label="Bug Description", style=discord.TextStyle.paragraph, placeholder="Describe exactly what happened and what you expected to happen.", required=True, max_length=4000)
        self.link_input=discord.ui.TextInput(label="Relevant Link (Optional)", placeholder="Paste a Discord message, page, or other relevant link.", required=False, max_length=500)
        self.add_item(self.title_input); self.add_item(self.description_input)
        if category == "Other — Specify where you experienced the bug":
            self.where_input=discord.ui.TextInput(label="Where did you experience the bug?", placeholder="Tell us which Chatly system or area was affected.", required=True, max_length=200); self.add_item(self.where_input)
        else: self.where_input=None
        self.add_item(self.link_input)
    async def on_submit(self, interaction: discord.Interaction):
        cog=interaction.client.get_cog("Support")
        if cog is None:
            await interaction.response.send_message("The Support system is unavailable right now.", ephemeral=True); return
        await cog.create_bug_ticket(interaction,self.title_input.value.strip(),self.description_input.value.strip(),self.category,self.link_input.value.strip() or None,self.where_input.value.strip() if self.where_input else None)


class GeneralSupportModal(discord.ui.Modal, title="General Support"):
    def __init__(self):
        super().__init__()
        self.title_input=discord.ui.TextInput(label="Title", placeholder="Give your support request a short title.", required=True, max_length=100)
        self.description_input=discord.ui.TextInput(label="Description", style=discord.TextStyle.paragraph, placeholder="Explain what you need help with.", required=True, max_length=4000)
        self.add_item(self.title_input); self.add_item(self.description_input)
    async def on_submit(self, interaction: discord.Interaction):
        cog=interaction.client.get_cog("Support")
        if cog is None:
            await interaction.response.send_message("The Support system is unavailable right now.", ephemeral=True); return
        await cog.create_general_ticket(interaction,self.title_input.value.strip(),self.description_input.value.strip())


class TicketControlView(PersistentView):
    def __init__(self, ticket_type: str | None = None):
        super().__init__()
        if ticket_type:
            for child in self.children:
                if getattr(child, "custom_id", "") == "chatly_ticket_mark_fixed":
                    child.disabled = ticket_type != "Bug Report"
                elif getattr(child, "custom_id", "") == "chatly_ticket_mark_solved":
                    child.disabled = ticket_type == "Bug Report"
    @discord.ui.button(label="Close Ticket", emoji=CLOSE_EMOJI, style=discord.ButtonStyle.secondary, custom_id="chatly_ticket_close", row=0)
    async def close(self,i,b):
        c=i.client.get_cog("Support"); c and await c.show_close_menu(i)
    @discord.ui.button(label="Lock", emoji=LOCK_EMOJI, style=discord.ButtonStyle.secondary, custom_id="chatly_ticket_lock", row=0)
    async def lock(self,i,b):
        c=i.client.get_cog("Support"); c and await c.lock_ticket(i)
    @discord.ui.button(label="Add Member", emoji=USER_EMOJI, style=discord.ButtonStyle.secondary, custom_id="chatly_ticket_add_member", row=0)
    async def add_member(self,i,b):
        await i.response.send_message(embed=discord.Embed(title=f"{USER_EMOJI} Add Member",description="Select a member to add to this ticket.",color=CHATLY_GREEN),view=AddMemberView(),ephemeral=True)
    @discord.ui.button(label="Evidence Ping", emoji=FOLDER_EMOJI, style=discord.ButtonStyle.secondary, custom_id="chatly_ticket_evidence_ping", row=0)
    async def evidence(self,i,b):
        c=i.client.get_cog("Support"); c and await c.evidence_ping(i)
    @discord.ui.button(label="Claim Ticket", emoji=USER_EMOJI, style=discord.ButtonStyle.secondary, custom_id="chatly_ticket_claim", row=0)
    async def claim(self,i,b):
        c=i.client.get_cog("Support"); c and await c.claim_ticket(i)
    @discord.ui.button(label="Transfer Ticket", emoji=LINK_EMOJI, style=discord.ButtonStyle.secondary, custom_id="chatly_ticket_transfer", row=1)
    async def transfer(self,i,b):
        c=i.client.get_cog("Support"); c and await c.show_transfer_menu(i)
    @discord.ui.button(label="Rename Ticket", emoji=EDIT_EMOJI, style=discord.ButtonStyle.secondary, custom_id="chatly_ticket_rename", row=1)
    async def rename(self,i,b):
        c=i.client.get_cog("Support"); c and await c.show_rename_modal(i)
    @discord.ui.button(label="Staff Notes", emoji=INFO_EMOJI, style=discord.ButtonStyle.secondary, custom_id="chatly_ticket_staff_notes", row=1)
    async def notes(self,i,b):
        c=i.client.get_cog("Support"); c and await c.show_staff_note_modal(i)
    @discord.ui.button(label="Mark Solved", emoji=DOUBLE_TICK_EMOJI, style=discord.ButtonStyle.secondary, custom_id="chatly_ticket_mark_solved", row=1)
    async def solved(self,i,b):
        c=i.client.get_cog("Support"); c and await c.show_solved_confirmation(i)
    @discord.ui.button(label="Mark Fixed", emoji=DOUBLE_TICK_EMOJI, style=discord.ButtonStyle.secondary, custom_id="chatly_ticket_mark_fixed", row=2)
    async def fixed(self,i,b):
        c=i.client.get_cog("Support"); c and await c.show_fixed_confirmation(i)


class FixedConfirmationView(discord.ui.View):
    @discord.ui.button(label="Confirm Fixed", emoji=TICK_EMOJI, style=discord.ButtonStyle.secondary, custom_id="chatly_fixed_confirm")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("Support")
        if cog:
            await cog.mark_bug_fixed(interaction, "Fix confirmed by staff")

    @discord.ui.button(label="Specify Fix", emoji=EDIT_EMOJI, style=discord.ButtonStyle.secondary, custom_id="chatly_fixed_specify")
    async def specify(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(FixedDetailsModal())

    @discord.ui.button(label="Cancel", emoji=CLOSE_EMOJI, style=discord.ButtonStyle.secondary, custom_id="chatly_fixed_cancel")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Mark Fixed cancelled.", embed=None, view=None)


class FixedDetailsModal(discord.ui.Modal, title="Fix Details"):
    details = discord.ui.TextInput(label="Fix details", style=discord.TextStyle.paragraph, placeholder="Describe what was fixed or changed.", required=True, max_length=2000)

    async def on_submit(self, interaction: discord.Interaction):
        cog = interaction.client.get_cog("Support")
        if cog:
            await cog.mark_bug_fixed(interaction, self.details.value.strip())


class AddMemberView(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=180)

        self.add_item(TicketMemberSelect())





class TicketMemberSelect(discord.ui.UserSelect):

    def __init__(self):

        super().__init__(

            placeholder="Select a member to add",

            min_values=1,

            max_values=1,

            custom_id="chatly_ticket_member_select",

        )



    async def callback(self, interaction: discord.Interaction):

        cog = interaction.client.get_cog("Support")

        if cog:

            await cog.add_ticket_member(interaction, self.values[0])





class CloseMenuView(discord.ui.View):

    def __init__(self, staff: bool, bug: bool = False, general: bool = False):

        super().__init__(timeout=180)

        self.staff = staff

        self.bug = bug
        self.general = general
        reasons = GENERAL_CLOSE_REASONS if (staff and general) else (BUG_CLOSE_REASONS if (staff and bug) else (STAFF_CLOSE_REASONS if staff else REPORTER_CLOSE_REASONS))



        select = discord.ui.Select(

            placeholder="Select a close reason",

            min_values=1,

            max_values=1,

            options=[discord.SelectOption(label=r, value=r) for r in reasons],

            custom_id="chatly_close_reason_select",

        )

        select.callback = self.select_reason

        self.add_item(select)



        cancel = discord.ui.Button(

            label="Cancel",

            style=discord.ButtonStyle.secondary,

            custom_id="chatly_close_cancel",

        )

        cancel.callback = self.cancel

        self.add_item(cancel)



    async def select_reason(self, interaction: discord.Interaction):

        reason = interaction.data["values"][0]

        if reason in ("Specify", "Other", "Duplicate Bug"):

            await interaction.response.send_modal(CloseReasonModal(reason))

            return



        cog = interaction.client.get_cog("Support")

        if cog:

            await cog.close_ticket(interaction, reason, None)



    async def cancel(self, interaction: discord.Interaction):

        await interaction.response.edit_message(

            content="Close cancelled.",

            embed=None,

            view=None,

        )





class CloseReasonModal(discord.ui.Modal, title="Specify Close Reason"):

    reason_text = discord.ui.TextInput(

        label="Reason",

        style=discord.TextStyle.paragraph,

        required=True,

        max_length=2000,

    )



    def __init__(self, mode: str):

        super().__init__()

        self.mode = mode



    async def on_submit(self, interaction: discord.Interaction):

        cog = interaction.client.get_cog("Support")

        if cog:

            await cog.close_ticket(

                interaction,

                self.mode,

                self.reason_text.value,

            )





class Support(commands.Cog):

    def __init__(self, bot: commands.Bot):

        self.bot = bot

        self.tickets = load_json(TICKET_DATA_FILE, {})

        self.counter = int(load_json(TICKET_COUNTER_FILE, {"next": 1}).get("next", 1))
        for _r in self.tickets.values():
            _r.setdefault("claimed_by", None); _r.setdefault("staff_notes", []); _r.setdefault("members_added", []); _r.setdefault("actions", [])

        async def _auto_close_worker():
            await self.bot.wait_until_ready()
            while not self.bot.is_closed():
                await asyncio.sleep(600)
                now = utc_now()
                for channel_id, record in list(self.tickets.items()):
                    if record.get("closed_at"):
                        continue
                    try:
                        last_activity = datetime.fromisoformat(record["last_activity"])
                    except Exception:
                        continue
                    if (now - last_activity).total_seconds() < AUTO_CLOSE_SECONDS:
                        continue
                    channel = self.bot.get_channel(int(channel_id))
                    if not isinstance(channel, discord.TextChannel):
                        continue
                    bot_member = channel.guild.me
                    if bot_member is None:
                        continue
                    record["actions"].append({
                        "action": "Automatic Close",
                        "actor_id": bot_member.id,
                        "timestamp": iso(now),
                    })
                    await self.finalize_ticket(
                        channel, record, closed_by=bot_member,
                        close_reason="Inactive",
                        action_taken=record.get("action_taken"),
                    )

        self.auto_close_task = self.bot.loop.create_task(_auto_close_worker())



    def cog_unload(self):

        self.auto_close_task.cancel()



    async def cog_load(self):

        self.bot.add_view(SupportMainView())

        self.bot.add_view(TicketControlView())



    # -----------------------------

    # Persistence

    # -----------------------------



    def next_ticket_id(self) -> str:

        ticket_id = f"CTY-{self.counter:06d}"

        self.counter += 1

        save_json(TICKET_COUNTER_FILE, {"next": self.counter})

        return ticket_id



    def get_ticket(self, channel_id: int):

        return self.tickets.get(str(channel_id))



    def save(self):

        save_json(TICKET_DATA_FILE, self.tickets)



    # -----------------------------

    # Support panel

    # -----------------------------



    support = app_commands.Group(

        name="support",

        description="Manage the Chatly Support system.",

    )



    @support.command(

        name="setup",

        description="Post the Chatly Support panel.",

    )

    async def setup_support(self, interaction: discord.Interaction):

        if interaction.guild is None or interaction.user.id != OWNER_ID:

            await interaction.response.send_message(

                "You do not have permission to use this command.",

                ephemeral=True,

            )

            return



        embed = discord.Embed(

            title=f"{CONVERSATION_EMOJI} Chatly Support",

            description=(

                "Need help? Choose the option below that best matches your request.\n\n"

                "Our support system is designed to keep requests private, organized, "

                "and easy for staff to handle."

            ),

        )

        embed.set_image(url=SUPPORT_DIVIDER_URL)
        embed.set_thumbnail(url=SUPPORT_THUMBNAIL_URL)



        await interaction.channel.send(embed=embed, view=SupportMainView())

        await interaction.response.send_message(

            f"{TICK_EMOJI} **Support panel sent.**",

            ephemeral=True,

        )



    # -----------------------------

    # Report creation

    # -----------------------------



    async def create_bug_ticket(self, interaction: discord.Interaction, bug_title: str, description: str, category: str, relevant_link: str | None, where_experienced: str | None):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Bug reports can only be created inside a server.", ephemeral=True)
            return
        reporter = guild.get_member(interaction.user.id)
        if reporter is None:
            await interaction.response.send_message("I couldn't find your server membership.", ephemeral=True)
            return

        open_bugs = [r for r in self.tickets.values() if r.get("type") == "Bug Report" and r.get("reporter_id") == reporter.id and not r.get("closed_at")]
        if len(open_bugs) >= 2:
            view = discord.ui.View()
            for r in open_bugs[:2]:
                ch = guild.get_channel(int(r.get("channel_id", 0)))
                if ch:
                    view.add_item(discord.ui.Button(label=r.get("ticket_id", "Open Bug"), style=discord.ButtonStyle.link, url=ch.jump_url))
            await interaction.response.send_message(f"{NET_EMOJI} You already have the maximum of 2 open bug reports.", view=view if view.children else None, ephemeral=True)
            return

        normalized = re.sub(r"[^a-z0-9]+", " ", bug_title.lower()).strip()
        for r in open_bugs:
            if r.get("category") == category:
                other = re.sub(r"[^a-z0-9]+", " ", r.get("bug_title", "").lower()).strip()
                if normalized and other and difflib.SequenceMatcher(None, normalized, other).ratio() >= 0.82:
                    ch = guild.get_channel(int(r.get("channel_id", 0)))
                    view = discord.ui.View()
                    if ch:
                        view.add_item(discord.ui.Button(label="Open Existing Bug", style=discord.ButtonStyle.link, url=ch.jump_url))
                    await interaction.response.send_message(f"{NET_EMOJI} This appears to be a duplicate of one of your open bug reports.", view=view if view.children else None, ephemeral=True)
                    return

        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)
        bot_member = guild.me or guild.get_member(self.bot.user.id)
        if bot_member is None:
            await interaction.followup.send("I couldn't determine the bot member.", ephemeral=True)
            return
        premium = has_premium(reporter)
        category_id = PREMIUM_REPORT_CATEGORY_ID if premium else REPORT_CATEGORY_ID
        ticket_category = guild.get_channel(category_id)
        if not isinstance(ticket_category, discord.CategoryChannel):
            await interaction.followup.send(f"Bug report category `{category_id}` could not be found.", ephemeral=True)
            return

        ticket_id = self.next_ticket_id()
        now = iso(utc_now())
        record = {"ticket_id": ticket_id, "channel_id": None, "type": "Bug Report", "reporter_id": reporter.id, "bug_title": bug_title, "description": description, "category": category, "relevant_link": relevant_link, "where_experienced": where_experienced, "category_id": ticket_category.id, "created_at": now, "last_activity": now, "closed_at": None, "closed_by": None, "close_reason": None, "action_taken": None, "fixed_at": None, "fixed_by": None, "fix_details": None, "members_added": [], "actions": [], "locked": False}
        try:
            channel = await guild.create_text_channel(name=safe_bug_channel_name(reporter.name), category=ticket_category, overwrites=permission_overwrites(guild, reporter, bot_member), topic=f"Chatly Ticket {ticket_id} | Bug Report", reason=f"Chatly Support ticket {ticket_id}")
        except discord.HTTPException as exc:
            await interaction.followup.send(f"Could not create the bug ticket: `{exc}`", ephemeral=True)
            return
        record["channel_id"] = channel.id
        record["actions"].append({"action": "Ticket Created", "actor_id": reporter.id, "timestamp": now})
        self.tickets[str(channel.id)] = record
        self.save()

        embed = discord.Embed(title=f"{NET_EMOJI} Bug Report", color=CHATLY_GREEN)
        embed.add_field(name="Bug Title", value=bug_title, inline=False)
        embed.add_field(name="Description", value=description, inline=False)
        embed.add_field(name="Bug Category", value=category, inline=True)
        if where_experienced:
            embed.add_field(name="Where Experienced", value=where_experienced, inline=False)
        if relevant_link:
            embed.add_field(name="Relevant Link", value=relevant_link, inline=False)
        embed.add_field(name="Additional Details & Evidence", value=">>> **Please add any additional details, screenshots, videos, files, or other evidence directly in this ticket.**", inline=False)
        embed.set_footer(text=f"Ticket ID: {ticket_id}")
        await channel.send(content=reporter.mention, embed=embed, view=TicketControlView("Bug Report"))

        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Open Bug Report", emoji=LINK_EMOJI, style=discord.ButtonStyle.link, url=channel.jump_url))
        if premium:
            desc = f"Ticket ID: `{ticket_id}`\n\nYour bug report has been submitted successfully and will receive **Priority Bug Report handling** as part of your Chatly Premium membership.\n\nThank you for choosing **Chatly Premium**.\n\nPlease add any additional details and evidence in the ticket using the button below."
        else:
            desc = f"Ticket ID: `{ticket_id}`\n\nYour bug report has been submitted successfully. Please add any additional details, screenshots, videos, files, or other evidence in the ticket using the button below."
        await interaction.followup.send(embed=discord.Embed(title=f"{NET_EMOJI} Bug Report Submitted", description=desc, color=CHATLY_GREEN), view=view, ephemeral=True)

    async def create_general_ticket(self, interaction: discord.Interaction, title: str, description: str):
        guild=interaction.guild
        if guild is None:
            await interaction.response.send_message("General Support tickets can only be created inside a server.",ephemeral=True); return
        reporter=guild.get_member(interaction.user.id)
        if reporter is None:
            await interaction.response.send_message("I couldn't find your server membership.",ephemeral=True); return
        if any(r.get("type")=="General Support" and r.get("reporter_id")==reporter.id and not r.get("closed_at") for r in self.tickets.values()):
            await interaction.response.send_message(f"{QUESTION_EMOJI} You already have an open General Support ticket.",ephemeral=True); return
        if not interaction.response.is_done(): await interaction.response.defer(ephemeral=True)
        bot_member=guild.me or guild.get_member(self.bot.user.id)
        premium=has_premium(reporter); cat=guild.get_channel(PREMIUM_REPORT_CATEGORY_ID if premium else REPORT_CATEGORY_ID)
        if bot_member is None or not isinstance(cat,discord.CategoryChannel):
            await interaction.followup.send("The support system could not access the required server resources.",ephemeral=True); return
        tid=self.next_ticket_id(); now=iso(utc_now())
        clean=re.sub(r"[^a-zA-Z0-9_.-]","-",reporter.name.lower())[:92] or "user"
        rec={"ticket_id":tid,"channel_id":None,"type":"General Support","reporter_id":reporter.id,"title":title,"description":description,"category_id":cat.id,"created_at":now,"last_activity":now,"closed_at":None,"closed_by":None,"close_reason":None,"action_taken":None,"members_added":[],"actions":[],"locked":False,"claimed_by":None,"staff_notes":[]}
        try:
            ch=await guild.create_text_channel(name=f"❓・{clean}",category=cat,overwrites=permission_overwrites(guild,reporter,bot_member),topic=f"Chatly Ticket {tid} | General Support",reason=f"Chatly Support ticket {tid}")
        except discord.HTTPException as exc:
            await interaction.followup.send(f"Could not create the support ticket: `{exc}`",ephemeral=True); return
        rec["channel_id"]=ch.id; rec["actions"].append({"action":"Ticket Created","actor_id":reporter.id,"timestamp":now}); self.tickets[str(ch.id)]=rec; self.save()
        e=discord.Embed(title=f"{QUESTION_EMOJI} General Support",color=CHATLY_GREEN); e.add_field(name="Title",value=title,inline=False); e.add_field(name="Description",value=description,inline=False); e.set_footer(text=f"Ticket ID: {tid}")
        await ch.send(content=reporter.mention,embed=e,view=TicketControlView("General Support"))
        v=discord.ui.View(); v.add_item(discord.ui.Button(label="Open Support Ticket",emoji=LINK_EMOJI,style=discord.ButtonStyle.link,url=ch.jump_url))
        desc=f"Ticket ID: `{tid}`\n\nYour support request has been submitted successfully" + (" and will receive **Priority Support handling** as part of your Chatly Premium membership.\n\nThank you for choosing **Chatly Premium**." if premium else ". Please add any additional context directly in the ticket.")
        await interaction.followup.send(embed=discord.Embed(title=f"{TICK_EMOJI} Support Request Submitted",description=desc,color=CHATLY_GREEN),view=v,ephemeral=True)

    async def create_report_ticket(

        self,

        interaction: discord.Interaction,

        reported_user: discord.Member,

        reason: str,

        custom_details: str | None,

    ):

        guild = interaction.guild

        if guild is None:

            await interaction.response.send_message(

                "Reports can only be created inside a server.",

                ephemeral=True,

            )

            return



        reporter = guild.get_member(interaction.user.id)

        if reporter is None:

            await interaction.response.send_message(

                "I couldn't find your server membership.",

                ephemeral=True,

            )

            return



        # Prevent duplicate open reports for the same reported member by the same reporter.

        for record in self.tickets.values():

            if (

                record.get("type") == "Member Report"

                and record.get("reporter_id") == reporter.id

                and record.get("reported_user_id") == reported_user.id

            ):

                existing = guild.get_channel(int(record.get("channel_id", 0)))

                if existing:

                    view = discord.ui.View()

                    view.add_item(

                        discord.ui.Button(

                            label="Open Existing Ticket",

                            style=discord.ButtonStyle.link,

                            url=existing.jump_url,

                        )

                    )

                    await interaction.response.send_message(

                        "You already have an open report for this member.",

                        view=view,

                        ephemeral=True,

                    )

                    return



        if not interaction.response.is_done():

            await interaction.response.defer(ephemeral=True)



        bot_member = guild.me or guild.get_member(self.bot.user.id)

        if bot_member is None:

            await interaction.followup.send(

                "I couldn't determine the bot member.",

                ephemeral=True,

            )

            return



        premium = has_premium(reporter)

        category_id = (

            PREMIUM_REPORT_CATEGORY_ID if premium else REPORT_CATEGORY_ID

        )

        category = guild.get_channel(category_id)



        if not isinstance(category, discord.CategoryChannel):

            await interaction.followup.send(

                f"Report category `{category_id}` could not be found.",

                ephemeral=True,

            )

            return



        ticket_id = self.next_ticket_id()



        try:

            channel = await guild.create_text_channel(

                name=safe_channel_name(reported_user.name),

                category=category,

                overwrites=permission_overwrites(

                    guild, reporter, bot_member

                ),

                topic=f"Chatly Ticket {ticket_id} | Member Report",

                reason=f"Chatly Support ticket {ticket_id}",

            )

        except discord.HTTPException as exc:

            await interaction.followup.send(

                f"Could not create the report ticket: `{exc}`",

                ephemeral=True,

            )

            return



        record = {

            "ticket_id": ticket_id,

            "channel_id": channel.id,

            "type": "Member Report",

            "reporter_id": reporter.id,

            "reported_user_id": reported_user.id,

            "reason": reason,

            "custom_details": custom_details,

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

        }

        self.tickets[str(channel.id)] = record

        self.save()



        initial = discord.Embed(

            title=f"{USER_EMOJI} Member Report",

            color=CHATLY_GREEN,

        )

        initial.add_field(

            name="Reported User",

            value=f"{reported_user.mention} | `{reported_user.id}`",

            inline=False,

        )

        initial.add_field(

            name="Report Reason",

            value=(

                f"{reason}\n\n{custom_details}"

                if reason == "Other" and custom_details

                else reason

            ),

            inline=False,

        )

        initial.add_field(

            name="What happens next?",

            value=(

                ">>> **Please describe what happened and provide any relevant context. "

                "You can send screenshots, videos, files, or Discord message links "

                "directly in this ticket.**"

            ),

            inline=False,

        )

        initial.set_footer(text=f"Ticket ID: {ticket_id}")



        await channel.send(

            content=reporter.mention,

            embed=initial,

            view=TicketControlView("Member Report"),

        )



        view = discord.ui.View()

        view.add_item(

            discord.ui.Button(

                label="Open Report Ticket",

                emoji=LINK_EMOJI,

                style=discord.ButtonStyle.link,

                url=channel.jump_url,

            )

        )



        if premium:

            confirmation_description = (

                f"Ticket ID: `{ticket_id}`\n\n"

                "Your member report has been submitted successfully and will receive **Priority Report handling** "

                "as part of your Chatly Premium membership.\n\n"

                "Thank you for choosing **Chatly Premium**.\n\n"

                "Please add any additional details and evidence in the ticket using the button below."

            )

        else:

            confirmation_description = (

                f"Ticket ID: `{ticket_id}`\n\n"

                "Please add any additional evidence or context in the ticket using the button below."

            )

        confirmation = discord.Embed(

            title=f"{TICK_EMOJI} Report Submitted",

            description=confirmation_description,

            color=CHATLY_GREEN,

        )

        await interaction.followup.send(

            embed=confirmation,

            view=view,

            ephemeral=True,

        )



        record["actions"].append(

            {

                "action": "Ticket Created",

                "actor_id": reporter.id,

                "timestamp": iso(utc_now()),

            }

        )

        self.save()



    # -----------------------------

    # Ticket permissions

    # -----------------------------



    def actor_can_access(self, member: discord.Member, record: dict) -> bool:

        return member.id == record["reporter_id"] or member.id in record.get("members_added", []) or is_staff(member)



    def actor_is_higher_staff(self, member: discord.Member) -> bool:

        return is_admin(member)



    def touch(self, record: dict):

        record["last_activity"] = iso(utc_now())

        self.save()



    async def require_ticket(self, interaction: discord.Interaction):

        if not isinstance(interaction.channel, discord.TextChannel):

            await interaction.response.send_message(

                "This button can only be used inside a ticket.",

                ephemeral=True,

            )

            return None



        record = self.get_ticket(interaction.channel.id)

        if record is None:

            await interaction.response.send_message(

                "This is not an active Chatly ticket.",

                ephemeral=True,

            )

            return None



        member = interaction.guild.get_member(interaction.user.id)

        if member is None or not self.actor_can_access(member, record):

            await interaction.response.send_message(

                "You do not have access to this ticket.",

                ephemeral=True,

            )

            return None



        return record



    # -----------------------------

    # Close

    # -----------------------------



    async def show_close_menu(self, interaction: discord.Interaction):

        record = await self.require_ticket(interaction)

        if not record:

            return



        member = interaction.guild.get_member(interaction.user.id)

        staff = bool(member and is_staff(member))



        embed = discord.Embed(

            title=f"{CLOSE_EMOJI} Close Ticket",

            description="Select the reason for closing this ticket.",

            color=CHATLY_GREEN,

        )

        await interaction.response.send_message(

            embed=embed,

            view=CloseMenuView(staff, record.get("type") == "Bug Report", record.get("type") == "General Support"),

            ephemeral=True,

        )



    async def close_ticket(

        self,

        interaction: discord.Interaction,

        reason: str,

        specified_reason: str | None,

    ):

        record = await self.require_ticket(interaction)

        if not record:

            return



        member = interaction.guild.get_member(interaction.user.id)

        if member is None:

            return



        if reason == "Duplicate Bug":

            final_reason = f"Duplicate Bug — Existing Ticket: {specified_reason}" if specified_reason else "Duplicate Bug"

        elif reason == "Specify" or reason == "Other":

            final_reason = specified_reason or reason

        else:

            final_reason = reason


        await interaction.response.send_message(

            f"{FOLDER_EMOJI} **Preparing transcript...**",

            ephemeral=True,

        )

        if is_staff(member): self.award_points(member,"close_ticket",record,f"close:{record['ticket_id']}")

        await self.finalize_ticket(

            interaction.channel,

            record,

            closed_by=member,

            close_reason=final_reason,

            action_taken=record.get("action_taken"),

        )



    # -----------------------------

    # Mark fixed
    # -----------------------------

    async def show_fixed_confirmation(self, interaction: discord.Interaction):

        record = await self.require_ticket(interaction)

        if not record:

            return

        member = interaction.guild.get_member(interaction.user.id)

        if member is None or not is_admin(member):

            await interaction.response.send_message("Only Administrator+ can mark a bug as fixed.", ephemeral=True)

            return

        if record.get("type") != "Bug Report":

            await interaction.response.send_message("Mark Fixed is only available for Bug Report tickets.", ephemeral=True)

            return

        if record.get("fixed_at"):

            await interaction.response.send_message(f"{DOUBLE_TICK_EMOJI} This bug is already marked as fixed.", ephemeral=True)

            return

        embed = discord.Embed(

            title=f"{DOUBLE_TICK_EMOJI} Mark Fixed",

            description="Are you sure this bug has been fixed?",

            color=CHATLY_GREEN,

        )

        await interaction.response.send_message(embed=embed, view=FixedConfirmationView(), ephemeral=True)


    async def mark_bug_fixed(self, interaction: discord.Interaction, fix_details: str):

        record = await self.require_ticket(interaction)

        if not record:

            return

        member = interaction.guild.get_member(interaction.user.id)

        if member is None or not is_admin(member):

            await interaction.response.send_message("Only Administrator+ can mark a bug as fixed.", ephemeral=True)

            return

        if record.get("type") != "Bug Report":

            await interaction.response.send_message("Mark Fixed is only available for Bug Report tickets.", ephemeral=True)

            return

        now = utc_now()

        record["fixed_at"] = iso(now)

        record["fixed_by"] = member.id

        record["fix_details"] = fix_details

        record["actions"].append({"action": "Bug Marked Fixed", "actor_id": member.id, "fix_details": fix_details, "timestamp": iso(now)})
        self.award_points(member,"mark_fixed",record,f"fixed:{record['ticket_id']}")

        self.touch(record)

        embed = discord.Embed(

            title=f"{DOUBLE_TICK_EMOJI} Bug Marked Fixed",

            description=f"This bug has been marked as fixed by {member.mention}.\n\n**Fix details:**\n{fix_details}",

            color=CHATLY_GREEN,

        )

        embed.set_footer(text=f"Ticket ID: {record['ticket_id']}")

        if not interaction.response.is_done():

            await interaction.response.send_message(embed=embed)

        else:

            await interaction.followup.send(embed=embed)

        await self.finalize_ticket(
            interaction.channel,
            record,
            closed_by=member,
            close_reason="Fixed / Fix Confirmed",
            action_taken=fix_details,
        )


    # -----------------------------

    # Lock

    # -----------------------------



    async def lock_ticket(self, interaction: discord.Interaction):

        record = await self.require_ticket(interaction)

        if not record:

            return



        member = interaction.guild.get_member(interaction.user.id)

        if member is None or not is_admin(member):

            await interaction.response.send_message(

                f"{LOCK_EMOJI} Only Administrator+ can lock tickets.",

                ephemeral=True,

            )

            return



        if record.get("locked"):

            channel = interaction.channel

            for target in list(channel.overwrites.keys()):

                if isinstance(target, discord.Member) and target.id != member.id:

                    await channel.set_permissions(target, view_channel=True, send_messages=True, read_message_history=True, attach_files=True, embed_links=True)

            record["locked"] = False

            record["actions"].append({"action": "Ticket Unlocked", "actor_id": member.id, "timestamp": iso(utc_now())})
            self.award_points(member,"unlock_ticket",record,f"unlock:{record['ticket_id']}")

            self.touch(record)

            await channel.send(embed=discord.Embed(title=f"{LOCK_EMOJI} Ticket Unlocked", description="This ticket has been unlocked by Administrator+ staff.", color=CHATLY_GREEN))

            await interaction.response.send_message(f"{LOCK_EMOJI} Ticket unlocked.", ephemeral=True)

            return



        channel = interaction.channel

        reporter = interaction.guild.get_member(record["reporter_id"])

        if reporter:

            await channel.set_permissions(

                reporter,

                send_messages=False,

                add_reactions=False,

            )

        for target in list(channel.overwrites.keys()):

            if isinstance(target, discord.Member) and target.id != member.id and is_staff(target) and not is_admin(target):

                await channel.set_permissions(target, view_channel=True, send_messages=False, read_message_history=True, attach_files=False, embed_links=False)

        for target_id in record.get("members_added", []):

            target = interaction.guild.get_member(target_id)

            if target:

                await channel.set_permissions(target, view_channel=True, send_messages=False, read_message_history=True, attach_files=False, embed_links=False)



        record["locked"] = True
        self.award_points(member,"lock_ticket",record,f"lock:{record['ticket_id']}")

        record["actions"].append(

            {

                "action": "Ticket Locked",

                "actor_id": member.id,

                "timestamp": iso(utc_now()),

            }

        )

        self.touch(record)



        embed = discord.Embed(

            title=f"{LOCK_EMOJI} Ticket Locked",

            description=(

                "This ticket has been locked by staff. Only Administrator+ staff can interact "

                "with the ticket until it is unlocked."

            ),

            color=CHATLY_GREEN,

        )

        await channel.send(embed=embed)

        await interaction.response.send_message(

            f"{LOCK_EMOJI} Ticket locked.",

            ephemeral=True,

        )



    # -----------------------------

    # Add member

    # -----------------------------



    async def add_ticket_member(

        self,

        interaction: discord.Interaction,

        member_to_add: discord.Member,

    ):

        record = await self.require_ticket(interaction)

        if not record:

            return



        actor = interaction.guild.get_member(interaction.user.id)

        if actor is None:

            return



        channel = interaction.channel



        if member_to_add.bot:

            await interaction.response.send_message(

                "Bots cannot be added as witnesses.",

                ephemeral=True,

            )

            return



        if record.get("reported_user_id") and member_to_add.id == record["reported_user_id"]:

            await interaction.response.send_message(

                "The reported user cannot be added to this private report ticket.",

                ephemeral=True,

            )

            return



        if member_to_add.id in record["members_added"]:

            await interaction.response.send_message(

                "That member is already in this ticket.",

                ephemeral=True,

            )

            return



        await channel.set_permissions(

            member_to_add,

            view_channel=True,

            send_messages=True,

            read_message_history=True,

            attach_files=True,

            embed_links=True,

        )



        record["members_added"].append(member_to_add.id)

        record["actions"].append(

            {

                "action": "Member Added",

                "actor_id": actor.id,

                "target_id": member_to_add.id,

                "timestamp": iso(utc_now()),

            }

        )

        self.award_points(actor,"add_member",record,f"add_member:{record['ticket_id']}:{member_to_add.id}")
        self.touch(record)



        await interaction.response.send_message(

            f"{TICK_EMOJI} {member_to_add.mention} has been added to the ticket.",

            ephemeral=False,

        )



    # -----------------------------

    # Evidence ping

    # -----------------------------



    async def evidence_ping(self, interaction: discord.Interaction):

        record = await self.require_ticket(interaction)

        if not record:

            return



        member = interaction.guild.get_member(interaction.user.id)

        if member is None:

            return



        if not (member.id == record["reporter_id"] or is_staff(member)):

            await interaction.response.send_message(

                "Only the reporter and staff can use Evidence Ping.",

                ephemeral=True,

            )

            return



        now = utc_now()

        last = record.get("last_evidence_ping")

        if last:

            try:

                last_dt = datetime.fromisoformat(last)

                if (now - last_dt).total_seconds() < EVIDENCE_PING_COOLDOWN_SECONDS:

                    await interaction.response.send_message(

                        "Evidence Ping is on cooldown. Please wait before using it again.",

                        ephemeral=True,

                    )

                    return

            except ValueError:

                pass



        reporter = interaction.guild.get_member(record["reporter_id"])

        if reporter is None:

            await interaction.response.send_message(

                "The original reporter is no longer in the server.",

                ephemeral=True,

            )

            return



        record["last_evidence_ping"] = iso(now)

        record["actions"].append(

            {

                "action": "Evidence Ping",

                "actor_id": member.id,

                "timestamp": iso(now),

            }

        )

        self.award_points(member,"evidence_ping",record,f"evidence:{record['ticket_id']}")
        self.touch(record)



        await interaction.response.send_message(

            f"{reporter.mention}\n{FOLDER_EMOJI} **Evidence Requested**\nPlease provide any relevant screenshots, videos, files, or other evidence that may help staff handle this ticket.",

            allowed_mentions=discord.AllowedMentions(users=True),

        )



    # -----------------------------

    # Staff workflow / Mod Points

    def award_points(self, member, action, record, reference=None):
        cog=self.bot.get_cog("StaffStats")
        if cog is not None and is_staff(member):
            try: cog.record_action(member.id,action,reference=reference or f"{action}:{record.get('ticket_id')}")
            except Exception: pass

    async def claim_ticket(self, interaction):
        r=await self.require_ticket(interaction); m=interaction.guild.get_member(interaction.user.id)
        if not r or m is None: return
        if not is_staff(m): await interaction.response.send_message("Only staff can claim tickets.",ephemeral=True); return
        if r.get("claimed_by")==m.id: await interaction.response.send_message("You already have this ticket claimed.",ephemeral=True); return
        r["claimed_by"]=m.id; r["actions"].append({"action":"Ticket Claimed","actor_id":m.id,"timestamp":iso(utc_now())}); self.award_points(m,"claim_ticket",r,f"claim:{r['ticket_id']}"); self.touch(r)
        await interaction.response.send_message(embed=discord.Embed(title=f"{USER_EMOJI} Ticket Claimed",description=f"This ticket has been claimed by {m.mention}. Other staff can still interact with it.",color=CHATLY_GREEN))

    async def show_transfer_menu(self, interaction):
        r=await self.require_ticket(interaction); m=interaction.guild.get_member(interaction.user.id)
        if not r or m is None: return
        if not is_staff(m): await interaction.response.send_message("Only staff can transfer tickets.",ephemeral=True); return
        v=discord.ui.View(timeout=180); sel=discord.ui.Select(placeholder="Select the new ticket type",options=[discord.SelectOption(label=x,value=x) for x in ("Member Report","Bug Report","General Support")])
        async def cb(i): await self.transfer_ticket(i,sel.values[0])
        sel.callback=cb; v.add_item(sel)
        await interaction.response.send_message(embed=discord.Embed(title=f"{LINK_EMOJI} Transfer Ticket",description="Choose the new ticket type. The ticket remains in its current normal/premium category.",color=CHATLY_GREEN),view=v,ephemeral=True)

    async def transfer_ticket(self, interaction, new_type):
        r=await self.require_ticket(interaction); m=interaction.guild.get_member(interaction.user.id)
        if not r or m is None: return
        if not is_staff(m): await interaction.response.send_message("Only staff can transfer tickets.",ephemeral=True); return
        old=r.get("type"); r["type"]=new_type; r["actions"].append({"action":"Ticket Transferred","actor_id":m.id,"from_type":old,"to_type":new_type,"timestamp":iso(utc_now())}); self.award_points(m,"transfer_ticket",r,f"transfer:{r['ticket_id']}:{new_type}"); self.touch(r); await self.rename_channel_for_type(interaction.channel,r)
        await interaction.response.send_message(f"{LINK_EMOJI} Ticket `{r['ticket_id']}` transferred from **{old}** to **{new_type}**.")

    async def rename_channel_for_type(self,ch,r):
        reporter=ch.guild.get_member(r.get("reporter_id")); username=reporter.name if reporter else str(r.get("reporter_id","user")); clean=re.sub(r"[^a-zA-Z0-9_.-]","-",username.lower())[:92] or "user"; prefix={"Member Report":"❗","Bug Report":"🐛","General Support":"❓"}.get(r.get("type"),"❓"); await ch.edit(name=f"{prefix}・{clean}")

    async def show_rename_modal(self,interaction):
        r=await self.require_ticket(interaction); m=interaction.guild.get_member(interaction.user.id)
        if not r or m is None: return
        if not is_staff(m): await interaction.response.send_message("Only Moderator+ staff can rename tickets.",ephemeral=True); return
        await interaction.response.send_modal(RenameTicketModal())

    async def rename_ticket(self,interaction,name):
        r=await self.require_ticket(interaction); m=interaction.guild.get_member(interaction.user.id)
        if not r or m is None: return
        if not is_staff(m): await interaction.response.send_message("Only Moderator+ staff can rename tickets.",ephemeral=True); return
        clean=re.sub(r"[^a-zA-Z0-9_.-]","-",name.lower()).strip("-_.")[:92]
        if not clean: await interaction.response.send_message("Please provide a valid ticket name.",ephemeral=True); return
        prefix={"Member Report":"❗","Bug Report":"🐛","General Support":"❓"}.get(r.get("type"),"❓"); await interaction.channel.edit(name=f"{prefix}・{clean}"); r["actions"].append({"action":"Ticket Renamed","actor_id":m.id,"name":clean,"timestamp":iso(utc_now())}); self.award_points(m,"rename_ticket",r,f"rename:{r['ticket_id']}:{clean}"); self.touch(r); await interaction.response.send_message(f"{EDIT_EMOJI} Ticket renamed.",ephemeral=True)

    async def show_staff_note_modal(self,interaction):
        r=await self.require_ticket(interaction); m=interaction.guild.get_member(interaction.user.id)
        if not r or m is None: return
        if not is_staff(m): await interaction.response.send_message("Only staff can add staff notes.",ephemeral=True); return
        await interaction.response.send_modal(StaffNoteModal())

    async def add_staff_note(self,interaction,note):
        r=await self.require_ticket(interaction); m=interaction.guild.get_member(interaction.user.id)
        if not r or m is None: return
        if not is_staff(m): await interaction.response.send_message("Only staff can add staff notes.",ephemeral=True); return
        r.setdefault("staff_notes",[]).append({"actor_id":m.id,"note":note,"timestamp":iso(utc_now())}); r["actions"].append({"action":"Staff Note","actor_id":m.id,"note":note,"timestamp":iso(utc_now())}); self.award_points(m,"staff_note",r,f"note:{r['ticket_id']}:{note[:100]}"); self.touch(r); await interaction.response.send_message(f"{INFO_EMOJI} **Staff Note**\n{note}", ephemeral=True)

    async def show_solved_confirmation(self,interaction):
        r=await self.require_ticket(interaction); m=interaction.guild.get_member(interaction.user.id)
        if not r or m is None: return
        if not is_staff(m): await interaction.response.send_message("Only Jr Moderator+ staff can mark tickets as solved.",ephemeral=True); return
        if r.get("type")=="Bug Report": await interaction.response.send_message("Use Mark Fixed for Bug Report tickets.",ephemeral=True); return
        await interaction.response.send_message(embed=discord.Embed(title=f"{DOUBLE_TICK_EMOJI} Mark Solved",description="Are you sure this ticket has been resolved?",color=CHATLY_GREEN),view=SolvedConfirmationView(),ephemeral=True)

    async def mark_solved(self,interaction,action):
        r=await self.require_ticket(interaction); m=interaction.guild.get_member(interaction.user.id)
        if not r or m is None: return
        if not is_staff(m): await interaction.response.send_message("Only Jr Moderator+ staff can mark tickets as solved.",ephemeral=True); return
        r["action_taken"]=action; r["solved_by"]=m.id; r["solved_at"]=iso(utc_now()); r["actions"].append({"action":"Ticket Marked Solved","actor_id":m.id,"action_taken":action,"timestamp":iso(utc_now())}); self.award_points(m,"mark_solved",r,f"solve:{r['ticket_id']}"); self.touch(r); await interaction.response.send_message(f"{DOUBLE_TICK_EMOJI} **Appropriate action has been taken.**\n\nThe ticket is being transcribed and closed.",ephemeral=True); await self.finalize_ticket(interaction.channel,r,m,"Resolved / Action Completed",action)


class SolvedConfirmationView(discord.ui.View):
    @discord.ui.button(label="Confirm Solved & Action Taken",emoji=TICK_EMOJI,style=discord.ButtonStyle.secondary)
    async def confirm(self,i,b):
        c=i.client.get_cog("Support"); c and await c.mark_solved(i,"Appropriate action has been taken")
    @discord.ui.button(label="Confirm & Specify Action",emoji=EDIT_EMOJI,style=discord.ButtonStyle.secondary)
    async def specify(self,i,b): await i.response.send_modal(SolvedDetailsModal())
    @discord.ui.button(label="Cancel",emoji=CLOSE_EMOJI,style=discord.ButtonStyle.secondary)
    async def cancel(self,i,b): await i.response.edit_message(content="Mark Solved cancelled.",embed=None,view=None)

class SolvedDetailsModal(discord.ui.Modal,title="Action Taken"):
    details=discord.ui.TextInput(label="Action taken",style=discord.TextStyle.paragraph,required=True,max_length=2000)
    async def on_submit(self,i):
        c=i.client.get_cog("Support"); c and await c.mark_solved(i,self.details.value.strip())

class RenameTicketModal(discord.ui.Modal,title="Rename Ticket"):
    name=discord.ui.TextInput(label="New ticket name",required=True,max_length=92)
    async def on_submit(self,i):
        c=i.client.get_cog("Support"); c and await c.rename_ticket(i,self.name.value.strip())

class StaffNoteModal(discord.ui.Modal,title="Staff Note"):
    note=discord.ui.TextInput(label="Staff note",style=discord.TextStyle.paragraph,required=True,max_length=2000)
    async def on_submit(self,i):
        c=i.client.get_cog("Support"); c and await c.add_staff_note(i,self.note.value.strip())

    # Transcript / logging

    # -----------------------------



    async def build_transcript(

        self,

        channel: discord.TextChannel,

        record: dict,

    ) -> bytes:

        '''Build a browser-viewable Discord-style HTML transcript.'''

        try:

            messages = [m async for m in channel.history(limit=None, oldest_first=True)]

        except discord.HTTPException:

            messages = []



        def esc(value: object) -> str:

            return html.escape(str(value), quote=True)



        def linkify(value: str) -> str:

            value = esc(value).replace("\n", "<br>")

            return re.sub(r'(https?://[^\s<]+)', lambda m: f'<a href="{m.group(1)}" target="_blank" rel="noopener noreferrer">{m.group(1)}</a>', value)



        async def attachment_html(attachment: discord.Attachment) -> str:

            url = esc(attachment.url)

            name = esc(attachment.filename)

            content_type = (attachment.content_type or "").lower()

            ext = attachment.filename.lower().rsplit(".", 1)[-1] if "." in attachment.filename else ""



            is_image = (

                content_type.startswith("image/")

                or ext in {"png", "jpg", "jpeg", "gif", "webp", "bmp", "svg"}

            )



            if is_image:

                try:

                    image_bytes = await attachment.read()

                    mime = content_type or {

                        "jpg": "image/jpeg",

                        "jpeg": "image/jpeg",

                        "png": "image/png",

                        "gif": "image/gif",

                        "webp": "image/webp",

                        "bmp": "image/bmp",

                        "svg": "image/svg+xml",

                    }.get(ext, "application/octet-stream")

                    data_uri = f"data:{mime};base64,{base64.b64encode(image_bytes).decode('ascii')}"

                    return (

                        '<div class="attachment image-attachment">'

                        f'<img src="{data_uri}" alt="{name}" loading="lazy">'

                        f'<div class="attachment-name">{name}</div>'

                        "</div>"

                    )

                except (discord.HTTPException, discord.NotFound, discord.Forbidden):

                    return (

                        '<div class="attachment image-attachment">'

                        f'<a href="{url}" target="_blank" rel="noopener noreferrer">'

                        f'<img src="{url}" alt="{name}" loading="lazy"></a>'

                        f'<div class="attachment-name">{name} '

                        f'<a href="{url}" target="_blank" rel="noopener noreferrer">(open)</a></div>'

                        "</div>"

                    )



            if content_type.startswith("video/") or ext in {"mp4", "webm", "mov", "m4v"}:

                return (

                    '<div class="attachment">'

                    f'<video controls preload="metadata" src="{url}"></video>'

                    f'<div class="attachment-name"><a href="{url}" target="_blank" '

                    f'rel="noopener noreferrer">{name}</a></div></div>'

                )



            if content_type.startswith("audio/") or ext in {"mp3", "wav", "ogg", "m4a"}:

                return (

                    '<div class="attachment">'

                    f'<audio controls preload="metadata" src="{url}"></audio>'

                    f'<div class="attachment-name"><a href="{url}" target="_blank" '

                    f'rel="noopener noreferrer">{name}</a></div></div>'

                )



            return (

                '<div class="file">📎 '

                f'<a href="{url}" target="_blank" rel="noopener noreferrer">{name}</a>'

                "</div>"

            )



        blocks = []

        for message in messages:

            avatar_url = getattr(message.author.display_avatar, "url", None)

            avatar = f'<img class="avatar" src="{esc(avatar_url)}" alt="">' if avatar_url else '<div class="avatar placeholder"></div>'

            timestamp = message.created_at.strftime("%d %b %Y, %I:%M %p UTC")

            content = linkify(message.content) if message.content else ""

            attachment_parts = []

            for attachment in message.attachments:

                attachment_parts.append(await attachment_html(attachment))

            attachments = "".join(attachment_parts)

            reply = f'<div class="reply">Reply to message <code>{message.reference.message_id}</code></div>' if message.reference and message.reference.message_id else ""

            embeds = f'<div class="embed-note">{len(message.embeds)} embedded item(s)</div>' if message.embeds else ""

            blocks.append(f'''<div class="message">{avatar}<div class="message-body"><div class="message-meta"><span class="author">{esc(message.author.display_name)}</span><span class="user-tag">{esc(str(message.author))}</span><span class="timestamp">{esc(timestamp)}</span></div>{reply}<div class="content">{content}</div>{attachments}{embeds}</div></div>''')

        if not blocks:

            blocks.append('<div class="empty">No messages were available in this ticket.</div>')



        actions=[]

        for action in record.get("actions", []):

            extras=[]

            if action.get("target_id"): extras.append(f"Target: {action['target_id']}")

            if action.get("close_reason"): extras.append(f"Close reason: {action['close_reason']}")

            if action.get("action_taken"): extras.append(f"Action taken: {action['action_taken']}")

            detail = (" — " + " | ".join(extras)) if extras else ""

            actions.append(f'<li><strong>{esc(action.get("action", "Action"))}</strong> — actor {esc(action.get("actor_id", "Unknown"))} — {esc(action.get("timestamp", ""))}{esc(detail)}</li>')

        action_list="".join(actions) or "<li>No recorded actions.</li>"

        custom=esc(record.get("custom_details") or "")

        bug_extra = ""

        if record.get("type") == "Bug Report":

            parts = []

            if record.get("description"): parts.append(f"<strong>Description</strong><br>{esc(record.get('description'))}")

            if record.get("where_experienced"): parts.append(f"<strong>Where Experienced</strong><br>{esc(record.get('where_experienced'))}")

            if record.get("relevant_link"): parts.append(f"<strong>Relevant Link</strong><br>{linkify(record.get('relevant_link'))}")

            if record.get("fix_details"): parts.append(f"<strong>Fix Details</strong><br>{esc(record.get('fix_details'))}")

            bug_extra = f'<div class="custom">{"<hr>".join(parts)}</div>' if parts else ""

        custom_block=f'<div class="custom"><span>Custom Details</span><p>{custom}</p></div>' if custom else ""
        if record.get("type")=="General Support" and record.get("description"): custom_block += f'<div class="custom"><strong>Description</strong><p>{esc(record["description"])}</p></div>'
        custom_block += bug_extra

        if record.get("type") == "Bug Report":
            bug_meta=(f'<div class="meta-item"><span class="label">Bug Title</span><span class="value">{esc(record.get("bug_title") or "Unknown")}</span></div>' f'<div class="meta-item"><span class="label">Bug Category</span><span class="value">{esc(record.get("category") or "Unknown")}</span></div>' f'<div class="meta-item"><span class="label">Fixed By</span><span class="value">{esc(record.get("fixed_by") or "Not fixed")}</span></div>')
        elif record.get("type") == "General Support":
            bug_meta=f'<div class="meta-item"><span class="label">Support Title</span><span class="value">{esc(record.get("title") or "Unknown")}</span></div>'
        else:
            bug_meta=(f'<div class="meta-item"><span class="label">Reported User</span><span class="value">{esc(record.get("reported_user_id") or "Unknown")}</span></div>' f'<div class="meta-item"><span class="label">Report Reason</span><span class="value">{esc(record.get("reason") or "Unknown")}</span></div>')

        document = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Chatly Transcript — {esc(record['ticket_id'])}</title><style>

:root{{--g:#52FB18;--bg:#0b0d0f;--p:#111418;--p2:#181c21;--t:#e6e9ed;--m:#9aa3ad;--b:#2b3138}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--t);font-family:Inter,Segoe UI,Arial,sans-serif}}.container{{max-width:1100px;margin:auto;padding:32px 20px 60px}}.header,.messages,.actions{{background:var(--p);border:1px solid var(--b);border-radius:12px}}.header{{border-left:4px solid var(--g);padding:24px;margin-bottom:20px}}h1{{margin:0 0 8px}}.sub,.muted{{color:var(--m)}}.meta{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px;margin-top:18px}}.meta-item{{background:var(--p2);border:1px solid var(--b);border-radius:8px;padding:11px 13px}}.label{{display:block;color:var(--m);font-size:11px;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px}}.value{{font-size:14px;word-break:break-word}}.section{{margin-top:20px}}.section-title{{color:var(--g);font-size:14px;text-transform:uppercase;letter-spacing:.08em;margin:0 0 12px}}.messages{{padding:10px 0}}.message{{display:flex;gap:12px;padding:12px 18px}}.message:hover{{background:#15191e}}.avatar{{width:40px;height:40px;border-radius:50%;object-fit:cover;flex:0 0 40px}}.placeholder{{background:#30363d}}.message-body{{min-width:0;flex:1}}.message-meta{{display:flex;gap:8px;align-items:baseline;flex-wrap:wrap}}.author{{font-weight:700;color:#fff}}.user-tag,.timestamp{{color:var(--m);font-size:12px}}.content{{margin-top:4px;line-height:1.5;word-break:break-word}}.attachment{{margin-top:8px;max-width:560px}}.attachment img,.attachment video{{max-width:100%;max-height:520px;border-radius:8px;border:1px solid var(--b);display:block}}.attachment-name,.file{{margin-top:6px;color:var(--m);font-size:13px}}a{{color:#8ab4ff;text-decoration:none}}a:hover{{text-decoration:underline}}.reply,.embed-note{{margin-top:6px;color:var(--m);font-size:12px;background:#15191e;border-left:3px solid var(--b);padding:5px 8px;border-radius:4px}}.actions{{padding:16px 22px}}.actions ul{{margin:0;padding-left:20px;line-height:1.7}}.custom{{margin-top:12px;background:var(--p2);border:1px solid var(--b);border-radius:8px;padding:12px}}.custom span{{color:var(--m);font-size:12px;text-transform:uppercase}}.footer{{margin-top:24px;color:var(--m);text-align:center;font-size:12px}}code{{background:#20252b;padding:2px 5px;border-radius:4px}}</style></head><body><div class="container"><div class="header"><h1>Chatly Support Transcript</h1><div class="sub">Ticket <strong>{esc(record['ticket_id'])}</strong> · {esc(record['type'])}</div><div class="meta"><div class="meta-item"><span class="label">Reporter</span><span class="value">{esc(record['reporter_id'])}</span></div>{bug_meta}<div class="meta-item"><span class="label">Created</span><span class="value">{esc(record.get('created_at'))}</span></div><div class="meta-item"><span class="label">Closed</span><span class="value">{esc(record.get('closed_at') or 'Unknown')}</span></div><div class="meta-item"><span class="label">Closed By</span><span class="value">{esc(record.get('closed_by') or 'Unknown')}</span></div><div class="meta-item"><span class="label">Close Reason</span><span class="value">{esc(record.get('close_reason') or 'Unknown')}</span></div><div class="meta-item"><span class="label">Action Taken</span><span class="value">{esc(record.get('action_taken') or 'Not specified')}</span></div><div class="meta-item"><span class="label">Members Added</span><span class="value">{esc(', '.join(str(x) for x in record.get('members_added', [])) or 'None')}</span></div></div>{custom_block}</div><div class="section"><h2 class="section-title">Message History</h2><div class="messages">{''.join(blocks)}</div></div><div class="section"><h2 class="section-title">Ticket Actions</h2><div class="actions"><ul>{action_list}</ul></div></div><div class="footer">Generated by Chatly.py · {esc(record['ticket_id'])}</div></div></body></html>'''

        return document.encode("utf-8")



    async def log_ticket(self, record: dict, transcript: bytes):
        channel=self.bot.get_channel(TICKET_LOG_CHANNEL_ID)
        if not isinstance(channel,discord.TextChannel): return
        typ=record.get("type","Support"); icon=NET_EMOJI if typ=="Bug Report" else QUESTION_EMOJI if typ=="General Support" else FOLDER_EMOJI
        e=discord.Embed(title=f"{icon} {typ} Log",color=CHATLY_GREEN); e.add_field(name="Ticket ID",value=record["ticket_id"],inline=True); e.add_field(name="Ticket Type",value=typ,inline=True); e.add_field(name="Reporter",value=f"<@{record['reporter_id']}> | `{record['reporter_id']}`",inline=False)
        if typ=="Bug Report":
            e.add_field(name="Bug Title",value=record.get("bug_title","Unknown"),inline=False); e.add_field(name="Bug Category",value=record.get("category","Unknown"),inline=True); e.add_field(name="Description",value=record.get("description","Unknown"),inline=False)
            if record.get("where_experienced"): e.add_field(name="Where Experienced",value=record["where_experienced"],inline=False)
            if record.get("relevant_link"): e.add_field(name="Relevant Link",value=record["relevant_link"],inline=False)
            e.add_field(name="Fixed By",value=f"<@{record['fixed_by']}> | `{record['fixed_by']}`" if record.get("fixed_by") else "Not fixed",inline=False); e.add_field(name="Fix Details",value=record.get("fix_details") or "Not specified",inline=False)
        elif typ=="General Support":
            e.add_field(name="Title",value=record.get("title","Unknown"),inline=False); e.add_field(name="Description",value=record.get("description","Unknown"),inline=False)
        else:
            if record.get("reported_user_id"): e.add_field(name="Reported User",value=f"<@{record['reported_user_id']}> | `{record['reported_user_id']}`",inline=False)
            e.add_field(name="Report Reason",value=record.get("reason","Unknown"),inline=False)
            if record.get("custom_details"): e.add_field(name="Custom Details",value=record["custom_details"],inline=False)
        e.add_field(name="Ticket Category",value=f"`{record['category_id']}`",inline=True); e.add_field(name="Created",value=record["created_at"],inline=True); e.add_field(name="Closed",value=record.get("closed_at") or "Unknown",inline=True); e.add_field(name="Closed By",value=f"<@{record['closed_by']}> | `{record['closed_by']}`" if record.get("closed_by") else "Unknown",inline=False); e.add_field(name="Close Reason",value=record.get("close_reason") or "Unknown",inline=False); e.add_field(name="Action Taken / Fix",value=record.get("action_taken") or record.get("fix_details") or "Not specified",inline=False); e.add_field(name="Claimed By",value=f"<@{record['claimed_by']}>" if record.get("claimed_by") else "Unclaimed",inline=True); e.add_field(name="Members Added",value=", ".join(f"<@{x}>" for x in record.get("members_added",[])) or "None",inline=False)
        await channel.send(embed=e,file=discord.File(io.BytesIO(transcript),filename=f"{record['ticket_id']}_transcript.html"))

    async def finalize_ticket(

        self,

        channel: discord.TextChannel,

        record: dict,

        closed_by: discord.Member,

        close_reason: str,

        action_taken: str | None,

    ):

        if record.get("closed_at"):

            return



        record["closed_at"] = iso(utc_now())

        record["closed_by"] = closed_by.id

        record["close_reason"] = close_reason

        if action_taken:

            record["action_taken"] = action_taken



        record["actions"].append(

            {

                "action": "Ticket Closed",

                "actor_id": closed_by.id,

                "close_reason": close_reason,

                "action_taken": action_taken,

                "timestamp": iso(utc_now()),

            }

        )

        self.save()



        # Keep the final close notice in the transcript.

        try:

            await channel.send(

                f"{CLOSE_EMOJI} **Ticket is closing.** The transcript and report log are being secured."

            )

        except discord.HTTPException:

            pass



        transcript = await self.build_transcript(channel, record)

        await self.log_ticket(record, transcript)



        # Delete after the transcript is safely sent.

        try:

            await channel.delete(reason=f"Chatly ticket {record['ticket_id']} closed")

        except discord.HTTPException:

            pass



        self.tickets.pop(str(channel.id), None)

        self.save()



    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        if message.author.bot or not isinstance(message.channel, discord.TextChannel):

            return

        record = self.get_ticket(message.channel.id)

        if record and not record.get("closed_at"):

            record["last_activity"] = iso(message.created_at)

            self.save()


    # -----------------------------



async def setup(bot: commands.Bot):

    await bot.add_cog(Support(bot))
