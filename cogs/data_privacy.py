import discord
from discord.ext import commands


# Chatly custom emojis from Notion

INFO = "<:info:1550551426269319168>"
USER = "<:user:1550286898126262312>"
STARS = "<:stars:1550289412624093234>"
EXCLAMATION = "<:exclaimation:1550544117249998878>"
DELETE = "<:delete:1550282755017810070>"
CLOSE = "<:close:1550533713526399126>"
BULLET = "<:bullet:1550533745424072714>"


class DeleteConfirmationView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(
        label="Delete My Data",
        style=discord.ButtonStyle.danger,
        custom_id="chatly:delete_data_confirm"
    )
    async def confirm_delete(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        embed = discord.Embed(
            title=f"{EXCLAMATION} Final Confirmation",
            description=(
                f"{EXCLAMATION} **This action is irreversible.**\n\n"
                f"{DELETE} Deleting your Chatly data will remove the data "
                f"stored for your use of Chatly's features, including:\n\n"
                f"{USER} **Profile data**\n"
                f"Your Chatly profile information and related profile data.\n\n"
                f"{STARS} **Economy data**\n"
                f"Your Chatly balance, economy values, and related economy data.\n\n"
                f"{STARS} **Progression data**\n"
                f"Your XP, levels, activity progression, and other applicable "
                f"Chatly progress.\n\n"
                f"{INFO} **Other relevant Chatly data**\n"
                f"Other data stored by Chatly that is required for its "
                f"features and associated with your account.\n\n"
                f"{EXCLAMATION} **Once deleted, this data cannot be restored.**\n\n"
                f"Please confirm only if you understand that your "
                f"**profile, economy balance, and progression may be reset.**"
            ),
            color=discord.Color.red()
        )

        await interaction.response.edit_message(
            embed=embed,
            view=FinalDeleteView()
        )

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.secondary,
        custom_id="chatly:delete_data_cancel"
    )
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.edit_message(
            content=f"{CLOSE} Data deletion cancelled.",
            embed=None,
            view=None
        )


class FinalDeleteView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(
        label="Confirm & Delete",
        style=discord.ButtonStyle.danger,
        custom_id="chatly:delete_data_final"
    )
    async def final_delete(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        levelling_cog = interaction.client.get_cog("Levelling")

        levelling_deleted = False

        if levelling_cog is not None:
            try:
                levelling_deleted = await levelling_cog.delete_member_data(
                    interaction.user.id
                )
            except Exception:
                levelling_deleted = False

        deleted_items = []

        if levelling_deleted:
            deleted_items.append("XP, level and progression data")

        if deleted_items:
            deleted_text = "\n".join(
                f"{BULLET} {item}"
                for item in deleted_items
            )

            message = (
                f"{INFO} **Data deletion request completed.**\n\n"
                f"{DELETE} The following Chatly data was deleted:\n"
                f"{deleted_text}\n\n"
                f"{STARS} Other Chatly data systems will be connected "
                f"to this deletion process as their databases are implemented."
            )
        else:
            message = (
                f"{INFO} **Data deletion request completed.**\n\n"
                f"{STARS} There was no stored progression data found "
                f"for your account to delete.\n\n"
                f"{STARS} Other Chatly data systems will be connected "
                f"to this deletion process as their databases are implemented."
            )

        await interaction.response.edit_message(
            content=message,
            embed=None,
            view=None
        )

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.secondary,
        custom_id="chatly:delete_data_final_cancel"
    )
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.edit_message(
            content=f"{CLOSE} Data deletion cancelled.",
            embed=None,
            view=None
        )


class DataPrivacy(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(
        name="delete-data",
        description="Request deletion of your Chatly data."
    )
    async def delete_data(
        self,
        interaction: discord.Interaction
    ):

        embed = discord.Embed(
            title=f"{INFO} Delete Your Chatly Data",
            description=(
                f"{USER} You can request deletion of the data Chatly "
                f"stores for your account to provide its features.\n\n"
                f"{STARS} This may include data associated with:\n"
                f"{BULLET} Your Chatly profile\n"
                f"{BULLET} Economy balance and economy values\n"
                f"{BULLET} XP, levels, activity and progression\n"
                f"{BULLET} Other relevant data required for Chatly features\n\n"
                f"{EXCLAMATION} **Deleting your data is irreversible.**\n"
                f"Your profile, economy and progression may be reset."
            ),
            color=discord.Color(0x52FB18)
        )

        await interaction.response.send_message(
            embed=embed,
            view=DeleteConfirmationView(),
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(DataPrivacy(bot))