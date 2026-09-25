import json
import io
import re
from datetime import datetime, timezone
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands


# ============================================================
# CONFIGURATION
# ============================================================

OWNER_ROLE_ID = 1467231978813128835
PROFILE_ROLE_ID = 1503429332318552077

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "owner_tools_data"
ROLES_FILE = DATA_DIR / "roles.json"
CHANNELS_FILE = DATA_DIR / "channels.json"


# ============================================================
# DATABASE HELPERS
# ============================================================

def ensure_data_directory() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_role_database() -> dict:
    ensure_data_directory()

    if not ROLES_FILE.exists():
        return {}

    try:
        with ROLES_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

    except json.JSONDecodeError as error:
        # Never silently replace a corrupted database with {}.
        raise RuntimeError(
            f"Could not decode {ROLES_FILE}: {error}"
        ) from error

    except OSError as error:
        raise RuntimeError(
            f"Could not read {ROLES_FILE}: {error}"
        ) from error

    if not isinstance(data, dict):
        raise RuntimeError(
            f"{ROLES_FILE} does not contain a valid database object."
        )

    return data


def save_role_database(data: dict) -> None:
    ensure_data_directory()

    temp_file = ROLES_FILE.with_suffix(".tmp")

    try:
        with temp_file.open("w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False
            )

        # Replace the old database only after the new file
        # has been written successfully.
        temp_file.replace(ROLES_FILE)

    except OSError as error:
        try:
            if temp_file.exists():
                temp_file.unlink()
        except OSError:
            pass

        raise RuntimeError(
            f"Could not save {ROLES_FILE}: {error}"
        ) from error


# ============================================================
# CHANNEL DATABASE HELPERS
# ============================================================

def load_channel_database() -> dict:
    ensure_data_directory()
    if not CHANNELS_FILE.exists():
        return {}
    try:
        with CHANNELS_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Could not decode {CHANNELS_FILE}: {error}") from error
    except OSError as error:
        raise RuntimeError(f"Could not read {CHANNELS_FILE}: {error}") from error
    if not isinstance(data, dict):
        raise RuntimeError(f"{CHANNELS_FILE} does not contain a valid database object.")
    return data


def save_channel_database(data: dict) -> None:
    ensure_data_directory()
    temp_file = CHANNELS_FILE.with_suffix(".tmp")
    try:
        with temp_file.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        temp_file.replace(CHANNELS_FILE)
    except OSError as error:
        try:
            if temp_file.exists():
                temp_file.unlink()
        except OSError:
            pass
        raise RuntimeError(f"Could not save {CHANNELS_FILE}: {error}") from error


CUSTOM_EMOJI_PATTERN = re.compile(r"<a?:([A-Za-z0-9_]+):(\d+)>")


def extract_custom_emojis(*values: str | None) -> list[dict]:
    found = {}
    for value in values:
        if not value:
            continue
        for match in CUSTOM_EMOJI_PATTERN.finditer(value):
            emoji_id = match.group(2)
            found[emoji_id] = {
                "emoji_id": emoji_id,
                "emoji_name": match.group(1),
                "animated": match.group(0).startswith("<a:"),
            }
    return sorted(
        found.values(),
        key=lambda item: (item["emoji_name"].lower(), item["emoji_id"]),
    )


def serialize_channel_overwrites(channel) -> list[dict]:
    overwrites = []
    try:
        items = channel.overwrites.items()
    except AttributeError:
        return overwrites
    for target, overwrite in items:
        try:
            allow, deny = overwrite.pair()
            if isinstance(target, discord.Role):
                target_type = "role"
            elif isinstance(target, discord.Member):
                target_type = "member"
            else:
                target_type = type(target).__name__.lower()
            overwrites.append({
                "target_type": target_type,
                "target_id": str(target.id),
                "target_name": getattr(target, "name", str(target)),
                "allow": str(allow.value),
                "deny": str(deny.value),
            })
        except Exception as error:
            overwrites.append({
                "target_type": type(target).__name__.lower(),
                "target_id": str(getattr(target, "id", "unknown")),
                "target_name": str(getattr(target, "name", target)),
                "error": f"{type(error).__name__}: {error}",
            })
    return sorted(
        overwrites,
        key=lambda item: (
            item.get("target_type", ""),
            item.get("target_name", "").lower(),
            item.get("target_id", ""),
        ),
    )


# ============================================================
# OWNER CHECK
# ============================================================

async def owner_only(interaction: discord.Interaction) -> bool:
    if not isinstance(interaction.user, discord.Member):
        return False

    return any(
        role.id == OWNER_ROLE_ID
        for role in interaction.user.roles
    )


# ============================================================
# OWNER TOOLS
# ============================================================

class OwnerTools(commands.Cog):
    """Owner-only administrative tools for Chatly."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    owner = app_commands.Group(
        name="owner",
        description="Owner-only Chatly administration tools."
    )

    # ========================================================
    # /owner role-scan
    # ========================================================

    @owner.command(
        name="role-scan",
        description="Scan and save the current server role hierarchy."
    )
    @app_commands.check(owner_only)
    @app_commands.guild_only()
    async def role_scan(
        self,
        interaction: discord.Interaction
    ):
        """Fetch the current Discord role state and save it to roles.json."""

        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                "❌ This command can only be used inside a server.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        try:
            # ====================================================
            # IMPORTANT:
            # Fetch roles directly from Discord instead of using
            # the cached guild.roles collection.
            # ====================================================

            roles = await guild.fetch_roles()

            # Highest role first.
            roles = sorted(
                roles,
                key=lambda role: role.position,
                reverse=True
            )

            scanned_at = datetime.now(timezone.utc).isoformat()

            role_records = []
            failures = []

            # ====================================================
            # BUILD ROLE SNAPSHOT
            # ====================================================

            for display_order, role in enumerate(roles, start=1):
                try:
                    bot_id = None

                    if role.managed and role.tags is not None:
                        bot_id = getattr(
                            role.tags,
                            "bot_id",
                            None
                        )

                    role_records.append({
                        "role_id": str(role.id),
                        "role_name": role.name,
                        "position": role.position,
                        "display_order": display_order,
                        "color": str(role.color),
                        "hoist": role.hoist,
                        "mentionable": role.mentionable,
                        "managed": role.managed,
                        "is_everyone": role.is_default(),
                        "is_bot_role": bot_id is not None,
                        "created_at": role.created_at.isoformat(),
                        "permissions": str(
                            role.permissions.value
                        ),
                        "scanned_at": scanned_at,
                        "guild_id": str(guild.id),
                    })

                except Exception as error:
                    failures.append({
                        "role_id": str(role.id),
                        "role_name": role.name,
                        "error": f"{type(error).__name__}: {error}",
                    })

            # ====================================================
            # ROLE COUNTS
            # ====================================================

            managed_roles = [
                role
                for role in roles
                if role.managed
            ]

            ordinary_roles = [
                role
                for role in roles
                if not role.managed
            ]

            # ====================================================
            # FETCH CURRENT BOT MEMBER
            # ====================================================

            highest_manageable_role = None

            if self.bot.user is not None:
                try:
                    bot_member = await guild.fetch_member(
                        self.bot.user.id
                    )

                    # Get the bot's actual role IDs from the
                    # freshly fetched Member.
                    bot_role_ids = {
                        role.id
                        for role in bot_member.roles
                    }

                    # Match those IDs against the freshly fetched
                    # role list so the hierarchy position is current.
                    bot_roles = [
                        role
                        for role in roles
                        if role.id in bot_role_ids
                    ]

                    if bot_roles:
                        bot_top_role = max(
                            bot_roles,
                            key=lambda role: role.position
                        )

                        manageable_roles = [
                            role
                            for role in roles
                            if (
                                not role.managed
                                and not role.is_default()
                                and role.position < bot_top_role.position
                            )
                        ]

                        if manageable_roles:
                            highest_manageable_role = max(
                                manageable_roles,
                                key=lambda role: role.position
                            )

                except discord.HTTPException as error:
                    failures.append({
                        "role_id": str(self.bot.user.id),
                        "role_name": "Bot hierarchy lookup",
                        "error": (
                            f"{type(error).__name__}: {error}"
                        ),
                    })

            # ====================================================
            # LOAD EXISTING DATABASE
            # ====================================================

            database = load_role_database()

            # Only replace this guild's snapshot.
            # Other guilds remain untouched.
            database[str(guild.id)] = {
                "guild_id": str(guild.id),
                "guild_name": guild.name,
                "scanned_at": scanned_at,
                "total_roles": len(roles),
                "managed_roles": len(managed_roles),
                "ordinary_roles": len(ordinary_roles),
                "highest_bot_manageable_role": (
                    {
                        "role_id": str(
                            highest_manageable_role.id
                        ),
                        "role_name": (
                            highest_manageable_role.name
                        ),
                        "position": (
                            highest_manageable_role.position
                        ),
                    }
                    if highest_manageable_role
                    else None
                ),
                "roles": role_records,
            }

            # ====================================================
            # SAVE FRESH SNAPSHOT EVERY RUN
            # ====================================================

            save_role_database(database)
            print(f"ACTUAL FILE: {ROLES_FILE.resolve()}")
            print(f"FILE TIME: {ROLES_FILE.stat().st_mtime}")

            # ====================================================
            # RESPONSE
            # ====================================================

            manageable_text = (
                f"{highest_manageable_role.name} "
                f"(`{highest_manageable_role.id}`)"
                if highest_manageable_role
                else "None"
            )

            snapshot_timestamp = int(
                datetime.fromisoformat(
                    scanned_at
                ).timestamp()
            )

            failure_text = (
                str(len(failures))
                if failures
                else "0"
            )

            await interaction.followup.send(
                (
                    "✅ **Role scan completed.**\n\n"
                    f"**Server:** {guild.name}\n"
                    f"**Total roles:** {len(roles)}\n"
                    f"**Managed roles:** {len(managed_roles)}\n"
                    f"**Ordinary roles:** {len(ordinary_roles)}\n"
                    f"**Highest manageable role:** "
                    f"{manageable_text}\n"
                    f"**Failures:** {failure_text}\n"
                    f"**Snapshot:** "
                    f"<t:{snapshot_timestamp}:F>\n\n"
                    f"📁 Saved to `{ROLES_FILE.resolve()}`."
                ),
                ephemeral=True
            )

        except Exception as error:
            await interaction.followup.send(
                (
                    "❌ **Role scan failed.**\n"
                    f"```text\n"
                    f"{type(error).__name__}: {error}\n"
                    f"```"
                ),
                ephemeral=True
            )

    # ========================================================
    # /owner permission-review
    # ========================================================

    @owner.command(
        name="permission-review",
        description="Preview planned staff permission changes without modifying roles."
    )
    @app_commands.check(owner_only)
    @app_commands.guild_only()
    async def permission_review(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "❌ This command can only be used inside a server.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        staff_roles = {
            "Jr Mod": 1503429248067703044,
            "Mod": 1503429244502413332,
            "Sr Mod": 1503429242921418925,
            "Admin": 1503429242392809604,
            "Manager": 1503429241423925268,
            "Executive": 1503429239825891457,
            "Co Owner": 1503429238894624899,
        }

        remove_all = {
            "Manage Nicknames": "manage_nicknames",
            "View Audit Log": "view_audit_log",
            "Moderate Members": "moderate_members",
            "Manage Messages": "manage_messages",
            "Manage Expressions": "manage_expressions",
            "Manage Events": "manage_events",
            "Manage Threads": "manage_threads",
            "Create Expressions": "create_expressions",
            "Create Events": "create_events",
        }

        roles = await guild.fetch_roles()
        role_map = {role.id: role for role in roles}
        lines = ["🔎 **Staff Permission Review — READ ONLY**", ""]

        for role_name, role_id in staff_roles.items():
            role = role_map.get(role_id)
            if role is None:
                lines.append(f"❌ **{role_name}** — role not found")
                continue

            lines.append(f"**{role_name}**")

            for display_name, attr in remove_all.items():
                if getattr(role.permissions, attr, False):
                    lines.append(f"  ❌ Remove: {display_name}")

            if role_name in {"Jr Mod", "Mod"}:
                if role.permissions.bypass_slowmode:
                    lines.append("  ❌ Remove: Bypass Slowmode")
            else:
                if role.permissions.bypass_slowmode:
                    lines.append("  ✅ Keep: Bypass Slowmode")

            if role_name in {"Executive", "Co Owner"}:
                if role.permissions.mention_everyone:
                    lines.append("  ✅ Keep: Mention Everyone")
                else:
                    lines.append("  ⚠️ Expected: Mention Everyone is currently OFF")
            elif role.permissions.mention_everyone:
                lines.append("  ❌ Remove: Mention Everyone")

            lines.append("")

        lines.append("🔒 **No permissions were changed.**")
        lines.append("🎙️ Voice permissions remain untouched.")

        output = "\n".join(lines)
        for i in range(0, len(output), 1900):
            await interaction.followup.send(output[i:i + 1900], ephemeral=True)


    # ========================================================
    # /owner permission-apply
    # ========================================================

    @owner.command(
        name="permission-apply",
        description="Preview, confirm, and apply staff permission hardening.",
    )
    @app_commands.check(owner_only)
    @app_commands.guild_only()
    async def permission_apply(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "❌ This command can only be used inside a server.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        staff_roles = {
            "Jr Mod": 1503429248067703044,
            "Mod": 1503429244502413332,
            "Sr Mod": 1503429242921418925,
            "Admin": 1503429242392809604,
            "Manager": 1503429241423925268,
            "Executive": 1503429239825891457,
            "Co Owner": 1503429238894624899,
        }

        remove_all = {
            "Manage Nicknames": "manage_nicknames",
            "View Audit Log": "view_audit_log",
            "Moderate Members": "moderate_members",
            "Manage Messages": "manage_messages",
            "Manage Expressions": "manage_expressions",
            "Manage Events": "manage_events",
            "Manage Threads": "manage_threads",
            "Create Expressions": "create_expressions",
            "Create Events": "create_events",
        }

        roles = await guild.fetch_roles()
        role_map = {role.id: role for role in roles}

        changes = []
        warnings = []
        originals = {}

        for role_name, role_id in staff_roles.items():
            role = role_map.get(role_id)

            if role is None:
                warnings.append(f"{role_name}: role not found")
                continue

            if role.managed or role.is_default():
                warnings.append(f"{role_name}: protected/managed role — skipped")
                continue

            if role.position >= guild.me.top_role.position:
                warnings.append(
                    f"{role_name}: above bot hierarchy — skipped"
                )
                continue

            originals[role.id] = role.permissions.value
            permissions = role.permissions

            removed = []

            for display_name, attr in remove_all.items():
                if getattr(permissions, attr, False):
                    setattr(permissions, attr, False)
                    removed.append(display_name)

            if role_name in {"Jr Mod", "Mod"}:
                if permissions.bypass_slowmode:
                    permissions.bypass_slowmode = False
                    removed.append("Bypass Slowmode")

            if role_name not in {"Executive", "Co Owner"}:
                if permissions.mention_everyone:
                    permissions.mention_everyone = False
                    removed.append("Mention Everyone")

            if removed:
                changes.append((role_name, role, permissions, removed))

        if not changes:
            await interaction.followup.send(
                "✅ No approved permission changes are currently needed."
                + (f"\n⚠️ {'; '.join(warnings)}" if warnings else ""),
                ephemeral=True,
            )
            return

        preview = ["⚠️ **Staff Permission Apply — Confirmation Required**", ""]
        for role_name, _, _, removed in changes:
            preview.append(f"**{role_name}**")
            for permission in removed:
                preview.append(f"  ❌ Remove: {permission}")
            preview.append("")

        if warnings:
            preview.append("⚠️ **Skipped:**")
            for warning in warnings:
                preview.append(f"• {warning}")
            preview.append("")

        preview.append(
            "Press **Confirm Apply** to apply the changes."
        )

        # Discord slash commands cannot safely wait for arbitrary message
        # input here, so use a button confirmation.
        class ConfirmView(discord.ui.View):
            def __init__(self, owner_id: int):
                super().__init__(timeout=60)
                self.owner_id = owner_id
                self.confirmed = None

            async def interaction_check(self, button_interaction):
                if button_interaction.user.id != self.owner_id:
                    await button_interaction.response.send_message(
                        "❌ Only the Owner who started this operation can confirm it.",
                        ephemeral=True,
                    )
                    return False
                return True

            @discord.ui.button(
                label="Confirm Apply",
                style=discord.ButtonStyle.danger,
            )
            async def confirm(self, button_interaction, button):
                self.confirmed = True
                self.stop()
                await button_interaction.response.defer()

            @discord.ui.button(
                label="Cancel",
                style=discord.ButtonStyle.secondary,
            )
            async def cancel(self, button_interaction, button):
                self.confirmed = False
                self.stop()
                await button_interaction.response.defer()

        view = ConfirmView(interaction.user.id)
        await interaction.followup.send(
            "\n".join(preview),
            view=view,
            ephemeral=True,
        )

        await view.wait()

        if view.confirmed is not True:
            await interaction.followup.send(
                "🔒 Permission changes cancelled. No roles were modified.",
                ephemeral=True,
            )
            return

        applied = []
        failed = []

        try:
            for role_name, role, new_permissions, removed in changes:
                try:
                    await role.edit(
                        permissions=new_permissions,
                        reason="Chatly Owner Tools — staff permission hardening",
                    )
                    applied.append((role_name, role.id, removed))
                except Exception as error:
                    failed.append(
                        f"{role_name}: {type(error).__name__}: {error}"
                    )

            # Re-fetch and verify the exact intended removals.
            refreshed_roles = await guild.fetch_roles()
            refreshed = {role.id: role for role in refreshed_roles}

            verification_failures = []

            for role_name, role, _, removed in changes:
                updated_role = refreshed.get(role.id)
                if updated_role is None:
                    verification_failures.append(
                        f"{role_name}: role disappeared during verification"
                    )
                    continue

                for display_name, attr in remove_all.items():
                    if getattr(updated_role.permissions, attr, False):
                        verification_failures.append(
                            f"{role_name}: {display_name} still enabled"
                        )

                if role_name in {"Jr Mod", "Mod"}:
                    if updated_role.permissions.bypass_slowmode:
                        verification_failures.append(
                            f"{role_name}: Bypass Slowmode still enabled"
                        )

                if role_name not in {"Executive", "Co Owner"}:
                    if updated_role.permissions.mention_everyone:
                        verification_failures.append(
                            f"{role_name}: Mention Everyone still enabled"
                        )

            # Save a fresh snapshot using the same database structure as role-scan.
            scanned_at = datetime.now(timezone.utc).isoformat()
            refreshed_roles = sorted(
                refreshed_roles,
                key=lambda role: role.position,
                reverse=True,
            )

            role_records = []
            for display_order, role in enumerate(refreshed_roles, start=1):
                bot_id = None
                if role.managed and role.tags is not None:
                    bot_id = getattr(role.tags, "bot_id", None)

                role_records.append({
                    "role_id": str(role.id),
                    "role_name": role.name,
                    "position": role.position,
                    "display_order": display_order,
                    "color": str(role.color),
                    "hoist": role.hoist,
                    "mentionable": role.mentionable,
                    "managed": role.managed,
                    "is_everyone": role.is_default(),
                    "is_bot_role": bot_id is not None,
                    "created_at": role.created_at.isoformat(),
                    "permissions": str(role.permissions.value),
                    "scanned_at": scanned_at,
                    "guild_id": str(guild.id),
                })

            managed_roles = [role for role in refreshed_roles if role.managed]
            ordinary_roles = [role for role in refreshed_roles if not role.managed]

            bot_member = await guild.fetch_member(self.bot.user.id)
            bot_role_ids = {role.id for role in bot_member.roles}
            bot_roles = [
                role for role in refreshed_roles
                if role.id in bot_role_ids
            ]
            bot_top_role = (
                max(bot_roles, key=lambda role: role.position)
                if bot_roles else None
            )
            manageable_roles = [
                role for role in refreshed_roles
                if (
                    not role.managed
                    and not role.is_default()
                    and bot_top_role is not None
                    and role.position < bot_top_role.position
                )
            ]
            highest_manageable_role = (
                max(manageable_roles, key=lambda role: role.position)
                if manageable_roles else None
            )

            database = load_role_database()
            database[str(guild.id)] = {
                "guild_id": str(guild.id),
                "guild_name": guild.name,
                "scanned_at": scanned_at,
                "total_roles": len(refreshed_roles),
                "managed_roles": len(managed_roles),
                "ordinary_roles": len(ordinary_roles),
                "highest_bot_manageable_role": (
                    {
                        "role_id": str(highest_manageable_role.id),
                        "role_name": highest_manageable_role.name,
                        "position": highest_manageable_role.position,
                    }
                    if highest_manageable_role else None
                ),
                "roles": role_records,
            }
            save_role_database(database)

            result = [
                "✅ **Staff permission hardening completed.**",
                "",
                f"**Roles changed:** {len(applied)}",
                f"**Failures:** {len(failed)}",
                f"**Verification failures:** {len(verification_failures)}",
                f"**Snapshot:** <t:{int(datetime.fromisoformat(scanned_at).timestamp())}:F>",
            ]

            if applied:
                result.append("\n**Applied:**")
                for role_name, role_id, removed in applied:
                    result.append(
                        f"• **{role_name}** (`{role_id}`): "
                        + ", ".join(removed)
                    )

            if failed:
                result.append("\n❌ **API failures:**")
                result.extend(f"• {item}" for item in failed)

            if verification_failures:
                result.append("\n❌ **Verification failures:**")
                result.extend(f"• {item}" for item in verification_failures)

            await interaction.followup.send(
                "\n".join(result),
                ephemeral=True,
            )

        except Exception as error:
            await interaction.followup.send(
                "❌ **Permission apply failed.**\n"
                f"```text\n{type(error).__name__}: {error}\n```",
                ephemeral=True,
            )



    # ========================================================
    # /owner permission-audit
    # ========================================================

    @owner.command(
        name="permission-audit",
        description="Audit all role permissions for security-sensitive access.",
    )
    @app_commands.check(owner_only)
    @app_commands.guild_only()
    async def permission_audit(self, interaction: discord.Interaction):
        """Read-only audit of security-sensitive permissions on every role."""

        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "❌ This command can only be used inside a server.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        # Role-level permissions only. Channel overwrites and member-specific
        # permissions are intentionally outside this audit.
        sensitive_permissions = {
            "administrator": ("Administrator", "CRITICAL"),
            "manage_guild": ("Manage Server", "CRITICAL"),
            "manage_roles": ("Manage Roles", "CRITICAL"),
            "manage_channels": ("Manage Channels", "CRITICAL"),
            "manage_webhooks": ("Manage Webhooks", "HIGH"),
            "view_audit_log": ("View Audit Log", "HIGH"),
            "ban_members": ("Ban Members", "HIGH"),
            "kick_members": ("Kick Members", "HIGH"),
            "moderate_members": ("Moderate Members", "HIGH"),
            "manage_messages": ("Manage Messages", "HIGH"),
            "manage_threads": ("Manage Threads", "HIGH"),
            "mention_everyone": ("Mention Everyone", "HIGH"),
            "manage_nicknames": ("Manage Nicknames", "MEDIUM"),
            "manage_emojis_and_stickers": (
                "Manage Expressions",
                "MEDIUM",
            ),
            "manage_events": ("Manage Events", "MEDIUM"),
            "create_expressions": ("Create Expressions", "MEDIUM"),
            "create_events": ("Create Events", "MEDIUM"),
            "move_members": ("Move Members", "MEDIUM"),
            "mute_members": ("Mute Members", "MEDIUM"),
            "deafen_members": ("Deafen Members", "MEDIUM"),
        }

        risk_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}

        try:
            roles = await guild.fetch_roles()
            roles = sorted(
                roles,
                key=lambda role: role.position,
                reverse=True,
            )

            findings = []
            permission_totals = {
                "CRITICAL": 0,
                "HIGH": 0,
                "MEDIUM": 0,
            }

            for role in roles:
                matched = []

                for attr, (display_name, risk) in sensitive_permissions.items():
                    if getattr(role.permissions, attr, False):
                        matched.append((risk, display_name, attr))

                if not matched:
                    continue

                matched.sort(key=lambda item: (risk_order[item[0]], item[1]))

                for risk, _, _ in matched:
                    permission_totals[risk] += 1

                findings.append({
                    "role": role,
                    "permissions": matched,
                    "highest_risk": matched[0][0],
                })

            findings.sort(
                key=lambda item: (
                    risk_order[item["highest_risk"]],
                    -item["role"].position,
                )
            )

            managed_count = sum(1 for role in roles if role.managed)
            ordinary_count = len(roles) - managed_count

            lines = [
                "🔎 **Chatly Permission Audit**",
                "",
                f"**Server:** {guild.name}",
                f"**Roles scanned:** {len(roles)}",
                f"**Managed:** {managed_count}",
                f"**Ordinary:** {ordinary_count}",
                f"**Roles with sensitive permissions:** {len(findings)}",
                "",
                "**Finding counts**",
                f"🔴 Critical permissions: {permission_totals['CRITICAL']}",
                f"🟠 High-risk permissions: {permission_totals['HIGH']}",
                f"🟡 Medium-risk permissions: {permission_totals['MEDIUM']}",
                "",
            ]

            if not findings:
                lines.append(
                    "✅ No roles have any of the audited sensitive permissions."
                )
            else:
                lines.append("**Sensitive role findings**")

                for item in findings:
                    role = item["role"]
                    managed_text = " • managed" if role.managed else ""
                    lines.append(
                        f"**{role.name}** — pos {role.position} — "
                        f"`{role.id}`{managed_text}"
                    )

                    for risk, display_name, attr in item["permissions"]:
                        lines.append(
                            f"  • {risk}: {display_name} (`{attr}`)"
                        )

            lines.extend([
                "",
                "ℹ️ **Scope:** role permissions only. Channel overwrites and "
                "member-specific permissions are not included.",
                "🔒 **Read-only:** no roles or permissions were changed.",
            ])

            output = "\n".join(lines)

            # Full audit is also attached as a text file so large guilds do not
            # lose findings to Discord's 2000-character message limit.
            audit_file = io.BytesIO(output.encode("utf-8"))
            audit_file.seek(0)

            if len(output) <= 1850:
                await interaction.followup.send(
                    output,
                    file=discord.File(
                        audit_file,
                        filename="permission-audit.txt",
                    ),
                    ephemeral=True,
                )
            else:
                summary_lines = lines[:16]
                summary_lines.extend([
                    "",
                    f"📄 Full audit attached: {len(findings)} sensitive role finding(s).",
                ])
                await interaction.followup.send(
                    "\n".join(summary_lines),
                    file=discord.File(
                        audit_file,
                        filename="permission-audit.txt",
                    ),
                    ephemeral=True,
                )

        except Exception as error:
            await interaction.followup.send(
                "❌ **Permission audit failed.**\n"
                f"```text\n{type(error).__name__}: {error}\n```",
                ephemeral=True,
            )


    # ========================================================
    # /owner role-color-theme
    # ========================================================

    @owner.command(
        name="role-color-theme",
        description="Preview and apply the Chatly green/teal role color theme.",
    )
    @app_commands.check(owner_only)
    @app_commands.guild_only()
    async def role_color_theme(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "❌ This command can only be used inside a server.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        # These are Chatly's dedicated color-selection roles from the
        # current role database. They are NEVER recolored by this command.
        # IDs are used so similarly named roles cannot be affected.
        COLOR_ROLE_IDS = {
            1529190987342286968, 1529191324962652270,
            1529191335309873244, 1529191289243828234,
            1529191301461835927, 1529191314673893527,
            1529192307201544192, 1529192310544269462,
            1529192295780450374, 1529192283809775766,
            1529192564945584378, 1529192496490483743,
            1529192552433975488, 1529192537233821858,
            1529192522793095270, 1529192510121840750,
            1529192975996031137, 1529193032027734177,
            1529193012003864666, 1529192960628101252,
            1529192930416525477, 1529192908488704150,
            1529193978124173393, 1529193952975130706,
            1529193957165371493, 1529193937707732992,
            1529193913993269329, 1529194163185258506,
            1529194209498759349, 1529194543281344692,
            1529194529163313374, 1529194427858419873,
            1529194432682004624, 1529194409894215782,
            1529194758419779726, 1529194729978331316,
            1529194882030243890, 1529194846768861274,
            1529195036510654636,
        }

        # Bright-only Chatly palette.
        # The colors stay in the green → lime → mint → aqua → cyan family,
        # but every stop is intentionally high-lightness so no dark/dull
        # role colors are generated.
        palette_stops = [
            (0.00, "#52FB18"),  # Chatly brand green
            (0.12, "#63FF2A"),
            (0.24, "#75FF3C"),
            (0.36, "#87FF52"),
            (0.48, "#99FF68"),
            (0.60, "#A8FF80"),
            (0.70, "#9CFFD0"),
            (0.80, "#82FFE1"),
            (0.90, "#69F7E9"),
            (1.00, "#63E8F7"),
        ]

        def interpolate_rgb(start_hex: str, end_hex: str, ratio: float) -> str:
            start = tuple(int(start_hex[i:i + 2], 16) for i in (1, 3, 5))
            end = tuple(int(end_hex[i:i + 2], 16) for i in (1, 3, 5))
            rgb = [
                round(start[index] + (end[index] - start[index]) * ratio)
                for index in range(3)
            ]
            return "#%02X%02X%02X" % tuple(rgb)

        def build_palette(count: int) -> list[str]:
            if count <= 0:
                return []
            if count == 1:
                return ["#52FB18"]

            palette = []
            for index in range(count):
                position = index / (count - 1)

                for stop_index in range(len(palette_stops) - 1):
                    left_position, left_hex = palette_stops[stop_index]
                    right_position, right_hex = palette_stops[stop_index + 1]

                    if position <= right_position:
                        local_ratio = (position - left_position) / (
                            right_position - left_position
                        )
                        palette.append(
                            interpolate_rgb(left_hex, right_hex, local_ratio)
                        )
                        break

            return palette

        roles = sorted(
            await guild.fetch_roles(),
            key=lambda role: role.position,
            reverse=True,
        )

        bot_member = await guild.fetch_member(self.bot.user.id)
        bot_top_role = max(
            bot_member.roles,
            key=lambda role: role.position,
        )

        profile_role = next(
            (role for role in roles if role.id == PROFILE_ROLE_ID),
            None,
        )

        if profile_role is None:
            await interaction.followup.send(
                "❌ **Profiles role not found.** No role colors were changed.",
                ephemeral=True,
            )
            return

        editable = []
        skipped = []
        eligible_roles = []
        color_roles = []
        top_protected_roles = []

        for role in roles:
            if role.id in COLOR_ROLE_IDS:
                color_roles.append(role)
                continue

            # Profiles and every role above it are protected from recoloring.
            if role.position >= profile_role.position:
                top_protected_roles.append(role)
                continue

            if role.is_default():
                skipped.append(f"{role.name}: @everyone cannot be recolored")
                continue

            if role.managed:
                skipped.append(f"{role.name}: managed role")
                continue

            if role.position >= bot_top_role.position:
                skipped.append(f"{role.name}: above/equal bot role")
                continue

            eligible_roles.append(role)

        palette = build_palette(len(eligible_roles))

        for theme_index, role in enumerate(eligible_roles):
            new_hex = palette[theme_index]
            old_hex = str(role.color)

            if old_hex.lower() != new_hex.lower():
                editable.append((role, old_hex, new_hex))

        color_roles.sort(key=lambda role: role.position, reverse=True)
        color_lines = [
            "🔒 **COLOR ROLES — 100% SKIPPED**",
            f"**Total protected color roles:** {len(color_roles)}",
            "**No color role will be modified by this command.**",
            "",
        ]
        for role in color_roles:
            color_lines.append(
                f"• **{role.name}** (`{role.id}`) — `{role.color}`"
            )

        # Discord's 2000-character limit applies to the final message,
        # not the number of lines. Split the protected-role list by characters.
        color_chunks = []
        current_chunk = ""

        for line in color_lines:
            candidate = (
                f"{current_chunk}\n{line}"
                if current_chunk
                else line
            )

            if len(candidate) > 1900:
                if current_chunk:
                    color_chunks.append(current_chunk)
                current_chunk = line
            else:
                current_chunk = candidate

        if current_chunk:
            color_chunks.append(current_chunk)

        for chunk in color_chunks:
            await interaction.followup.send(
                chunk,
                ephemeral=True,
            )

        if not editable:
            await interaction.followup.send(
                "✅ No non-color roles need recoloring.\n"
                "🔒 Color roles were skipped completely.",
                ephemeral=True,
            )
            return

        preview_lines = [
            "🎨 **Chatly Role Color Theme — Preview**",
            "",
            f"**Non-color roles to recolor:** {len(editable)}",
            f"**Protected color roles skipped:** {len(color_roles)}",
            f"**Other skipped roles:** {len(skipped)}",
            f"**Apply only below:** **{profile_role.name}** (`{profile_role.id}`)",
            f"**Top roles protected:** {len(top_protected_roles)}",
            "**Theme:** Bright Chatly Green → Lime → Mint → Aqua → Cyan",
            "**No dark or dull shades are generated.**",
            "",
        ]

        for role, old_hex, new_hex in editable:
            preview_lines.append(
                f"• **{role.name}** (`{role.id}`): `{old_hex}` → `{new_hex}`"
            )

        preview_text = "\n".join(preview_lines)
        preview_file = io.BytesIO(preview_text.encode("utf-8"))
        preview_file.seek(0)

        class ConfirmView(discord.ui.View):
            def __init__(self, owner_id: int):
                super().__init__(timeout=60)
                self.owner_id = owner_id
                self.confirmed = None

            async def interaction_check(self, button_interaction):
                if button_interaction.user.id != self.owner_id:
                    await button_interaction.response.send_message(
                        "❌ Only the Owner who started this operation can confirm it.",
                        ephemeral=True,
                    )
                    return False
                return True

            @discord.ui.button(
                label="Confirm Apply",
                style=discord.ButtonStyle.primary,
            )
            async def confirm(self, button_interaction, button):
                self.confirmed = True
                self.stop()
                await button_interaction.response.defer()

            @discord.ui.button(
                label="Cancel",
                style=discord.ButtonStyle.secondary,
            )
            async def cancel(self, button_interaction, button):
                self.confirmed = False
                self.stop()
                await button_interaction.response.defer()

        view = ConfirmView(interaction.user.id)

        await interaction.followup.send(
            preview_text[:1900],
            file=discord.File(preview_file, filename="role-color-theme-preview.txt"),
            view=view,
            ephemeral=True,
        )

        await view.wait()

        if view.confirmed is not True:
            await interaction.followup.send(
                "🔒 Role color theme cancelled. No roles were modified.",
                ephemeral=True,
            )
            return

        applied = []
        failed = []

        for role, old_hex, new_hex in editable:
            try:
                await role.edit(
                    colour=discord.Colour(int(new_hex[1:], 16)),
                    reason="Chatly Owner Tools — role color theme",
                )
                applied.append((role.name, role.id, old_hex, new_hex))
            except Exception as error:
                failed.append(
                    f"{role.name}: {type(error).__name__}: {error}"
                )

        # Verify applied colors directly from Discord.
        refreshed = await guild.fetch_roles()
        refreshed_map = {role.id: role for role in refreshed}
        verification_failures = []

        for role_name, role_id, _, new_hex in applied:
            current = refreshed_map.get(role_id)
            if current is None:
                verification_failures.append(
                    f"{role_name}: role missing during verification"
                )
                continue

            if current.color.value != int(new_hex[1:], 16):
                verification_failures.append(
                    f"{role_name}: expected {new_hex}, found {current.color}"
                )

        # Explicitly verify every protected color role remained unchanged.
        untouched_color_failures = []
        original_color_map = {role.id: role.color.value for role in color_roles}
        for role_id, original_value in original_color_map.items():
            current = refreshed_map.get(role_id)
            if current is None:
                untouched_color_failures.append(
                    f"Color role `{role_id}` missing during verification"
                )
                continue
            if current.color.value != original_value:
                untouched_color_failures.append(
                    f"Color role **{current.name}** (`{role_id}`) changed unexpectedly"
                )

        await interaction.followup.send(
            "✅ **Chatly role color theme completed.**\n\n"
            f"**Applied:** {len(applied)}\n"
            f"**Failures:** {len(failed)}\n"
            f"**Verification failures:** {len(verification_failures)}\n"
            f"**Color roles changed:** 0 / {len(color_roles)}\n"
            f"**Color-role verification failures:** {len(untouched_color_failures)}\n"
            f"**Other skipped:** {len(skipped)}",
            ephemeral=True,
        )

        if failed:
            await interaction.followup.send(
                "❌ **Failures:**\n" + "\n".join(f"• {item}" for item in failed),
                ephemeral=True,
            )

        if verification_failures:
            await interaction.followup.send(
                "❌ **Verification failures:**\n"
                + "\n".join(f"• {item}" for item in verification_failures),
                ephemeral=True,
            )

        if untouched_color_failures:
            await interaction.followup.send(
                "🚨 **Protected color-role verification failure:**\n"
                + "\n".join(f"• {item}" for item in untouched_color_failures),
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                f"🔒 **Verified:** all {len(color_roles)} color roles remained exactly unchanged.",
                ephemeral=True,
            )

        # Keep the local role snapshot's color data in sync with Discord.
        try:
            database = load_role_database()
            guild_snapshot = database.get(str(guild.id))

            if guild_snapshot and isinstance(guild_snapshot.get("roles"), list):
                scanned_at = datetime.now(timezone.utc).isoformat()
                color_map = {
                    str(role.id): str(role.color)
                    for role in refreshed
                }

                for record in guild_snapshot["roles"]:
                    role_id = str(record.get("role_id"))
                    if role_id in color_map:
                        record["color"] = color_map[role_id]
                        record["scanned_at"] = scanned_at

                guild_snapshot["scanned_at"] = scanned_at
                save_role_database(database)

        except Exception as error:
            await interaction.followup.send(
                "⚠️ Theme applied, but the local role snapshot could not be "
                f"updated: `{type(error).__name__}: {error}`",
                ephemeral=True,
            )


    # ========================================================
    # /owner channel-scan
    # ========================================================

    @owner.command(
        name="channel-scan",
        description="Scan and save the current server channel layout.",
    )
    @app_commands.check(owner_only)
    @app_commands.guild_only()
    async def channel_scan(self, interaction: discord.Interaction):
        """Read-only scan of the current Discord channel/category layout."""

        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "❌ This command can only be used inside a server.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        try:
            # Fetch the current channel list from Discord rather than relying
            # only on the local cache.
            channels = await guild.fetch_channels()
            channels = sorted(
                channels,
                key=lambda channel: (
                    getattr(channel, "position", 0),
                    str(channel.id),
                ),
                reverse=True,
            )

            scanned_at = datetime.now(timezone.utc).isoformat()
            records = []
            failures = []
            emoji_database = {}

            for display_order, channel in enumerate(channels, start=1):
                try:
                    category = getattr(channel, "category", None)
                    topic = getattr(channel, "topic", None)
                    name = getattr(channel, "name", "")
                    emoji_mentions = extract_custom_emojis(name, topic)

                    for emoji in emoji_mentions:
                        emoji_database[emoji["emoji_id"]] = emoji

                    record = {
                        "channel_id": str(channel.id),
                        "channel_name": name,
                        "channel_type": str(channel.type),
                        "position": getattr(channel, "position", None),
                        "display_order": display_order,
                        "category_id": str(category.id) if category else None,
                        "category_name": category.name if category else None,
                        "parent_id": str(getattr(channel, "category_id", None))
                        if getattr(channel, "category_id", None) else None,
                        "created_at": channel.created_at.isoformat()
                        if getattr(channel, "created_at", None) else None,
                        "topic": topic,
                        "nsfw": getattr(channel, "nsfw", None),
                        "slowmode_delay": getattr(channel, "slowmode_delay", None),
                        "default_auto_archive_duration": getattr(
                            channel, "default_auto_archive_duration", None
                        ),
                        "default_thread_slowmode_delay": getattr(
                            channel, "default_thread_slowmode_delay", None
                        ),
                        "default_sort_order": str(
                            getattr(channel, "default_sort_order", None)
                        ) if getattr(channel, "default_sort_order", None) is not None else None,
                        "default_forum_layout": str(
                            getattr(channel, "default_forum_layout", None)
                        ) if getattr(channel, "default_forum_layout", None) is not None else None,
                        "permission_overwrites": serialize_channel_overwrites(channel),
                        "emoji_mentions": emoji_mentions,
                        "guild_id": str(guild.id),
                        "scanned_at": scanned_at,
                    }

                    records.append(record)

                except Exception as error:
                    failures.append({
                        "channel_id": str(getattr(channel, "id", "unknown")),
                        "channel_name": getattr(channel, "name", "unknown"),
                        "error": f"{type(error).__name__}: {error}",
                    })

            category_count = sum(
                1 for channel in channels
                if isinstance(channel, discord.CategoryChannel)
            )
            text_count = sum(
                1 for channel in channels
                if isinstance(channel, discord.TextChannel)
            )
            voice_count = sum(
                1 for channel in channels
                if isinstance(channel, discord.VoiceChannel)
            )
            stage_count = sum(
                1 for channel in channels
                if isinstance(channel, discord.StageChannel)
            )
            forum_count = sum(
                1 for channel in channels
                if isinstance(channel, discord.ForumChannel)
            )
            news_count = sum(
                1 for channel in channels
                if getattr(channel, "type", None) == discord.ChannelType.news
            )

            database = load_channel_database()
            database[str(guild.id)] = {
                "guild_id": str(guild.id),
                "guild_name": guild.name,
                "scanned_at": scanned_at,
                "total_channels": len(channels),
                "categories": category_count,
                "text_channels": text_count,
                "voice_channels": voice_count,
                "stage_channels": stage_count,
                "forum_channels": forum_count,
                "news_channels": news_count,
                "custom_emojis_found": len(emoji_database),
                "failures": failures,
                "channels": records,
                "emoji_mentions": sorted(
                    emoji_database.values(),
                    key=lambda item: (
                        item["emoji_name"].lower(),
                        item["emoji_id"],
                    ),
                ),
            }
            save_channel_database(database)

            # Keep the Discord response safely below the 2000-character limit.
            summary = [
                "✅ **Chatly Channel Scan Complete**",
                "",
                f"**Server:** {guild.name}",
                f"**Total channels:** {len(channels)}",
                f"**Categories:** {category_count}",
                f"**Text:** {text_count}",
                f"**Voice:** {voice_count}",
                f"**Stage:** {stage_count}",
                f"**Forum:** {forum_count}",
                f"**News:** {news_count}",
                f"**Custom emojis found:** {len(emoji_database)}",
                f"**Failures:** {len(failures)}",
                "",
                "🔒 **Read-only:** no channels or permissions were changed.",
                "💾 Saved to `owner_tools_data/channels.json`.",
            ]

            json_bytes = json.dumps(
                database[str(guild.id)],
                indent=4,
                ensure_ascii=False,
            ).encode("utf-8")

            await interaction.followup.send(
                "\n".join(summary),
                file=discord.File(
                    io.BytesIO(json_bytes),
                    filename="channel-scan.json",
                ),
                ephemeral=True,
            )

        except Exception as error:
            await interaction.followup.send(
                "❌ **Channel scan failed.**\n"
                f"```text\n{type(error).__name__}: {error}\n```",
                ephemeral=True,
            )

    
# ========================================================
    # ERROR HANDLING
    # ========================================================

    @channel_scan.error
    async def channel_scan_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.CheckFailure):
            message = "❌ You must have the **Owner** role to use Owner Tools."
        elif isinstance(error, app_commands.NoPrivateMessage):
            message = "❌ This command can only be used inside a server."
        else:
            raise error
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)


    @role_scan.error
    async def role_scan_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.CheckFailure):
            if interaction.response.is_done():
                await interaction.followup.send(
                    (
                        "❌ You must have the **Owner** role "
                        "to use Owner Tools."
                    ),
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    (
                        "❌ You must have the **Owner** role "
                        "to use Owner Tools."
                    ),
                    ephemeral=True
                )
            return

        if isinstance(error, app_commands.NoPrivateMessage):
            if interaction.response.is_done():
                await interaction.followup.send(
                    (
                        "❌ This command can only be used "
                        "inside a server."
                    ),
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    (
                        "❌ This command can only be used "
                        "inside a server."
                    ),
                    ephemeral=True
                )
            return

        raise error


# ============================================================
# SETUP
# ============================================================

async def setup(bot: commands.Bot):
    await bot.add_cog(OwnerTools(bot))