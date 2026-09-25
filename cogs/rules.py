import discord
from discord.ext import commands
from discord import app_commands


# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

OWNER_ROLE_ID = 1467231978813128835

DIVIDER = (
    "https://media.discordapp.net/attachments/1010905558624239739/"
    "1507084201063616653/dividerqwe.jpg"
    "?ex=6aaed109&is=6aad7f89&hm="
    "48ef6afb347a9119b19fd20770e94b2e16a76176c25b050f9785835125366355"
    "&=&format=webp&width=512&height=2"
)

DIVIDER_FINAL = (
    "https://media.discordapp.net/attachments/1010905558624239739/"
    "1507083696744960131/dividerqwe.png"
    "?ex=6aaed091&is=6aad7f11&hm="
    "6e4162a5ea94316e8c55d2dceedb097ff4217d85b33e96b354fce60e72ae6206"
    "&=&format=webp&quality=lossless&width=512&height=2"
)


# ─────────────────────────────────────────────
# HEADER ARTWORK
# ─────────────────────────────────────────────

HEADERS = {
    # New first / Chatly banner
    "chatly": (
        "https://media.discordapp.net/attachments/1010905558624239739/"
        "1550633076428906576/"
        "Copy_of_Brown_Aesthetic_Corporate_Personal_Profile_LinkedIn_Banner-removebg-preview_1.png"
        "?ex=6aaf0b16&is=6aadb996&hm="
        "e9f9cef3f69386529776e1045edb4f7d641fee98ada7e5d50a206487cdb958bb"
        "&=&format=webp&quality=lossless"
    ),

    # NEW Safety Rules banner
    "safety": (
        "https://media.discordapp.net/attachments/1010905558624239739/"
        "1550627688287444992/du-removebg-preview.png"
        "?ex=6aaf0612&is=6aadb492&hm="
        "b7f46246d9e4041b310bed56800b7d5ccdc9f1de7c923d3b20d71cac7a58bed7"
        "&=&format=webp&quality=lossless"
    ),

    # NEW Conduct banner
    "community": (
        "https://media.discordapp.net/attachments/1010905558624239739/"
        "1550627688601882705/casd-removebg-preview.png"
        "?ex=6aaf0612&is=6aadb492&hm="
        "1a9ed70a79c0b1ac21e1645df1f6d8c127f5257ec8cf6bec6827dcea67b9959b"
        "&=&format=webp&quality=lossless"
    ),

    # NEW Profile Rules banner
    "profile": (
        "https://media.discordapp.net/attachments/1010905558624239739/"
        "1550627688945942629/asdq3-removebg-preview.png"
        "?ex=6aaf0612&is=6aadb492&hm="
        "cf76c35268e5c09b4663e453457f31df2f3502161289763f22255f6c614334b0"
        "&=&format=webp&quality=lossless"
    ),

    # NEW Chat & Voice banner
    "server": (
        "https://media.discordapp.net/attachments/1010905558624239739/"
        "1550627689264578701/ae2q3-removebg-preview.png"
        "?ex=6aaf0612&is=6aadb492&hm="
        "e3253ad89fff6d541f69fbb76c62c3d32d6c7a33a1f807da1496a5d7f14b698c"
        "&=&format=webp&quality=lossless"
    ),

    # NEW Staff banner
    "staff": (
        "https://media.discordapp.net/attachments/1010905558624239739/"
        "1550627689675624498/wd123123-removebg-preview.png"
        "?ex=6aaf0612&is=6aadb492&hm="
        "648625d36124b5ae66c1fbe2656728ee7c6f917f51866b03b776db2220719c58"
        "&=&format=webp&quality=lossless"
    ),

    # NEW Prohibited banner
    "security": (
        "https://media.discordapp.net/attachments/1010905558624239739/"
        "1550627687888982127/qwe-removebg-preview.png"
        "?ex=6aaf0612&is=6aadb492&hm="
        "a05f605230f5bfc061ca5117517893ec9eea3b4ddc7de6adf201baf93313b676"
        "&=&format=webp&quality=lossless"
    ),

    # Final Notes — unchanged
    "final": (
        "https://media.discordapp.net/attachments/1010905558624239739/"
        "1507095935640014879/3sadq2e-removebg-preview.png"
        "?ex=6aaedbf7&is=6aad8a77&hm="
        "1b84bdb6c253e6f734d6d4a24e5b2dc82756fd8dd7cf52bbee16cd3759e57cfc"
        "&=&format=webp&quality=lossless&width=512&height=129"
    ),

    # NEW Farhanz banner
    "farhanz": (
        "https://media.discordapp.net/attachments/1010905558624239739/"
        "1550627690187456562/wiuendwjkde-removebg-preview.png"
        "?ex=6aaf0612&is=6aadb492&hm="
        "93bd25cdcb9de3882944015326d9bed68e8c771c06a50fae07cdbedc80e2b818"
        "&=&format=webp&quality=lossless"
    ),
}


# ─────────────────────────────────────────────
# CHATLY NUMBERED EMOJIS
# ─────────────────────────────────────────────

NUMBERS = [
    "<:one:1550553897960083456>",
    "<:two:1550553928293154966>",
    "<:three:1550553954730115132>",
    "<:four:1550553985474109440>",
    "<:five:1550554017590018069>",
    "<:six:1550554046786445333>",
    "<:seven:1550554075681259590>",
    "<:eight:1550554103904473118>",
    "<:nine:1550554132883185664>",
]


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def header_embed(url: str) -> discord.Embed:
    embed = discord.Embed()
    embed.set_image(url=url)
    return embed


def rules_embed(items: list[tuple[str, str]]) -> discord.Embed:
    embed = discord.Embed()

    text = []

    for number, (title, description) in enumerate(items):
        emoji = NUMBERS[number]

        text.append(
            f"{emoji} **{title}**\n\n"
            f"{description}"
        )

    embed.description = "\n\n".join(text)

    # Divider is directly below the text in the same embed.
    embed.set_image(url=DIVIDER)

    return embed


# Current Chatly button emoji IDs from the Notion Emoji IDs reference.
BUTTON_EMOJI_IDS = {
    "uparrow": 1550289381347295292,
    "info": 1550551426269319168,
    "mod": 1550551457109901435,
    "help": 1550551387371343883,
    "star": 1550289395800743956,
}


# ─────────────────────────────────────────────
# BUTTONS
# ─────────────────────────────────────────────

async def find_external_emoji(
    bot: commands.Bot,
    emoji_id: int
) -> discord.Emoji | None:
    """
    Find the real custom Emoji object in any guild the bot belongs to.

    This is important for external custom emojis: discord.py can serialize an
    Emoji object with the source guild context, while a raw PartialEmoji may be
    rejected by Discord component validation for some external emojis.
    """
    for guild in bot.guilds:
        emoji = guild.get_emoji(emoji_id)

        if emoji is not None:
            return emoji

        try:
            emoji = await guild.fetch_emoji(emoji_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            continue

        if emoji is not None:
            return emoji

    return None


class RulesButtons(discord.ui.View):
    def __init__(
        self,
        emojis: dict[str, discord.Emoji | None],
        top_url: str
    ):
        super().__init__(timeout=None)

        self.add_item(
            discord.ui.Button(
                label="Scroll to Top",
                emoji=emojis.get("uparrow"),
                style=discord.ButtonStyle.link,
                url=top_url
            )
        )

        self.add_item(
            discord.ui.Button(
                label="Tos",
                emoji=emojis.get("info"),
                style=discord.ButtonStyle.link,
                url="https://discord.com/terms"
            )
        )

        self.add_item(
            discord.ui.Button(
                label="Guidelines",
                emoji=emojis.get("mod"),
                style=discord.ButtonStyle.link,
                url="https://discord.com/guidelines"
            )
        )

        self.add_item(
            discord.ui.Button(
                label="Help",
                emoji=emojis.get("help"),
                style=discord.ButtonStyle.link,
                url="https://discord.com/channels/1467231978813128834/1503429512078164142"
            )
        )

        self.add_item(
            discord.ui.Button(
                label="Premium",
                emoji=emojis.get("star"),
                style=discord.ButtonStyle.link,
                url="https://discord.com/channels/1467231978813128834/1503429504528548023"
            )
        )


# ─────────────────────────────────────────────
# COG
# ─────────────────────────────────────────────

class Rules(commands.Cog):
    rules = app_commands.Group(
        name="rules",
        description="Manage the Chatly rules panel."
    )

    def __init__(self, bot):
        self.bot = bot

    @rules.command(
        name="setup",
        description="Post the complete Chatly rules panel."
    )
    async def setup_rules(self, interaction: discord.Interaction):

        has_owner_role = any(
            role.id == OWNER_ROLE_ID
            for role in interaction.user.roles
        )

        if not has_owner_role:
            await interaction.response.send_message(
                "You do not have permission to use this command.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        channel = interaction.channel

        # ─────────────────────────────────────
        # CHATLY INTRO
        # ─────────────────────────────────────

        top_message = await channel.send(
            embed=header_embed(HEADERS["chatly"])
        )

        intro = discord.Embed(
            description=(
                "Welcome to **Chatly** — a social community server focused on "
                "chatting, making friends, gaming, entertainment, voice chats, "
                "events, and meeting new people in a fun and safe environment.\n\n"

                "Before participating, please read all rules carefully. "
                "By remaining in this server, you agree to follow these rules "
                "along with the Discord Terms of Service and Community Guidelines. "
                "Failure to comply may result in warnings, mutes, kicks, or "
                "permanent bans depending on the severity of the situation.\n\n"

                "Let’s work together to keep Chatly active, welcoming, and "
                "enjoyable for everyone."
            )
        )

        intro.set_image(url=DIVIDER)
        await channel.send(embed=intro)

        # ─────────────────────────────────────
        # SAFETY
        # ─────────────────────────────────────

        await channel.send(
            embed=header_embed(HEADERS["safety"])
        )

        await channel.send(
            embed=rules_embed([
                (
                    "Minimum Age Requirement",
                    "Chatly is a 13+ community server. Anyone under the age of "
                    "13 is strictly prohibited as it violates Discord Terms of Service."
                ),
                (
                    "Keep Yourself Safe",
                    "Do not share sensitive personal information such as passwords, "
                    "addresses, phone numbers, banking information, school details, "
                    "or private documents."
                ),
                (
                    "Report Dangerous Behavior",
                    "If you encounter harassment, scams, threats, predatory behavior, "
                    "or suspicious activity, report it to staff immediately instead "
                    "of handling it publicly."
                ),
                (
                    "No NSFW Content",
                    "Sexual content, nudity, explicit discussions, gore, or highly "
                    "inappropriate media/content is not allowed anywhere in the server."
                ),
            ])
        )

        # ─────────────────────────────────────
        # COMMUNITY
        # ─────────────────────────────────────

        await channel.send(
            embed=header_embed(HEADERS["community"])
        )

        await channel.send(
            embed=rules_embed([
                (
                    "Respect Everyone",
                    "Discrimination, hate speech, harassment, bullying, racism, "
                    "sexism, homophobia, transphobia, or targeted insults toward "
                    "any individual or group are strictly prohibited."
                ),
                (
                    "No Threats or Harassment",
                    "Do not threaten, stalk, blackmail, manipulate, impersonate, "
                    "or repeatedly disturb other members."
                ),
                (
                    "Keep Chats Friendly",
                    "This server is designed for socializing, conversations, gaming, "
                    "memes, media sharing, events, and community interactions. "
                    "Keep discussions appropriate and enjoyable."
                ),
                (
                    "No Public Drama",
                    "Do not publicly expose, shame, or start arguments against "
                    "other users. Sharing DMs or private conversations without "
                    "permission is not allowed."
                ),
                (
                    "English Only in Public Chats",
                    "Please use English in public channels so moderation can be "
                    "handled fairly and everyone can participate."
                ),
                (
                    "No Trolling or Ragebait",
                    "Joining solely to troll, bait reactions, spread negativity, "
                    "or intentionally disrupt the community will result in punishment."
                ),
            ])
        )

        # ─────────────────────────────────────
        # PROFILE
        # ─────────────────────────────────────

        await channel.send(
            embed=header_embed(HEADERS["profile"])
        )

        await channel.send(
            embed=rules_embed([
                (
                    "No Impersonation",
                    "Do not pretend to be another member, creator, staff member, "
                    "or public figure."
                ),
                (
                    "Appropriate Profiles",
                    "Usernames, profile pictures, banners, bios, and statuses "
                    "must remain appropriate and follow Discord Terms of Service."
                ),
                (
                    "No Offensive Content",
                    "Profiles containing hateful, NSFW, violent, or disturbing "
                    "content are prohibited."
                ),
            ])
        )

        # ─────────────────────────────────────
        # SERVER / CHAT AND VOICE
        # ─────────────────────────────────────

        await channel.send(
            embed=header_embed(HEADERS["server"])
        )

        await channel.send(
            embed=rules_embed([
                (
                    "No Spam or Flooding",
                    "Mass messaging, repeated text, excessive emoji spam, mic spam, "
                    "or flooding chats/channels is not allowed."
                ),
                (
                    "Use Channels Properly",
                    "Keep conversations in their relevant channels based on "
                    "the channel topics."
                ),
                (
                    "Voice Chat Etiquette",
                    "Extremely loud noises, earrape, disruptive soundboards, "
                    "or intentionally disturbing behavior in VC are prohibited."
                ),
                (
                    "No Advertising",
                    "Advertising Discord servers, websites, social media accounts, "
                    "products, or services without staff approval is not allowed."
                ),
                (
                    "No Scams or Malicious Content",
                    "Scamming, phishing, fake giveaways, malware, IP grabbers, "
                    "token loggers, or suspicious links/files are strictly prohibited."
                ),
                (
                    "Respect Events & Activities",
                    "Do not intentionally disrupt events, game nights, stage activities, "
                    "or community sessions hosted within the server."
                ),
            ])
        )

        # ─────────────────────────────────────
        # STAFF
        # ─────────────────────────────────────

        await channel.send(
            embed=header_embed(HEADERS["staff"])
        )

        await channel.send(
            embed=rules_embed([
                (
                    "Listen to Staff",
                    "If a staff member asks you to stop doing something, you are "
                    "expected to comply respectfully."
                ),
                (
                    "Do Not Mini-Moderate",
                    "Do not act as staff or attempt to punish members yourself. "
                    "Report issues instead."
                ),
                (
                    "Punishment Evasion",
                    "Attempting to bypass mutes, bans, or restrictions using alternate "
                    "accounts will result in permanent removal."
                ),
                (
                    "Staff Discretion",
                    "Staff reserve the right to take action against harmful behavior "
                    "even if every situation is not explicitly listed in the rules."
                ),
                (
                    "False Reports",
                    "Submitting fake reports or intentionally wasting staff time "
                    "may result in punishment."
                ),
            ])
        )

        # ─────────────────────────────────────
        # SECURITY / PROHIBITED
        # ─────────────────────────────────────

        await channel.send(
            embed=header_embed(HEADERS["security"])
        )

        await channel.send(
            embed=rules_embed([
                (
                    "No Raiding",
                    "Raiding, mass pinging, coordinated spam, or attempts to disrupt "
                    "the server are strictly forbidden."
                ),
                (
                    "No Community Sabotage",
                    "Creating copycat communities or attempting to mass invite "
                    "members away from Chatly is prohibited."
                ),
                (
                    "No Illegal Content",
                    "Any illegal content or activity will be immediately reported "
                    "to Discord Trust & Safety."
                ),
                (
                    "No Ban Evasion",
                    "Using alternate accounts to evade punishments is prohibited."
                ),
            ])
        )

        # ─────────────────────────────────────
        # FINAL NOTES
        # ─────────────────────────────────────

        await channel.send(
            embed=header_embed(HEADERS["final"])
        )

        final_notes = discord.Embed(
            description=(
                "By remaining in this server, you agree to follow all server rules, "
                "Discord Terms of Service, and Discord Community Guidelines.\n\n"

                "Staff decisions are final unless appealed through the appropriate "
                "support channels.\n\n"

                "Thank you for being part of Chatly and helping us build a fun, "
                "active, safe, and welcoming community for everyone."
            )
        )

        final_notes.set_image(url=DIVIDER)
        await channel.send(embed=final_notes)

        # ─────────────────────────────────────
        # FARHANZ
        # ─────────────────────────────────────

        await channel.send(
            embed=header_embed(HEADERS["farhanz"])
        )

        ownership = discord.Embed(
            description=(
                "<:user:1550286898126262312> **Owner**\n\n"
                "(@farhanz67) | <@937242913535033404>\n\n"

                "<:stars:1550289412624093234> **Credit & Ownership**\n\n"
                "Credit and ownership of the design, build, and development "
                "of the server and the Chatly bot belong to the Owner.\n\n"

                "<:paypal:1550551525204566057> **Payments & Business**\n\n"
                "All donations, purchases, and business inquiries are handled "
                "by the Owner and are strictly non-refundable.\n\n"

                "<:ban:1550542161924325388> **Punishments & Responsibility**\n\n"
                "Any punishments, including bans received for violating server "
                "rules or Discord Terms of Service, are solely the responsibility "
                "of the user, and no claims may be made regarding such actions.\n\n"

                "<:info:1550551426269319168> **Agreement**\n\n"
                "By remaining in this server, you agree to comply with all Chatly "
                "rules, Discord Terms of Service, and Discord Community Guidelines.\n\n"

                "<:tick:1550538067570335764> **Thank you for being part of Chatly.**"
            )
        )

        ownership.set_image(url=DIVIDER_FINAL)

        # Send the ownership embed separately so a component/emoji problem
        # cannot prevent the final content from being posted.
        await channel.send(embed=ownership)

        # Resolve the real Emoji objects from any server the bot belongs to.
        # This is different from searching interaction.guild: the emojis may
        # live on another server where the bot is also present.
        button_emojis = {
            name: await find_external_emoji(self.bot, emoji_id)
            for name, emoji_id in BUTTON_EMOJI_IDS.items()
        }

        # Send the five buttons only after resolving the source-server emojis.
        # If Discord cannot access one emoji, the button still renders without
        # that emoji rather than causing the whole component request to fail.
        await channel.send(
            view=RulesButtons(
                emojis=button_emojis,
                top_url=top_message.jump_url
            )
        )

        await interaction.followup.send(
            "Rules panel posted successfully.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Rules(bot))