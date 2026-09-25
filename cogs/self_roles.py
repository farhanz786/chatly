import discord
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path



from discord import app_commands



from discord.ext import commands, tasks











# =========================================================



# CONFIGURATION



# =========================================================







OWNER_ROLE_ID = 1467231978813128835



ERROR_CHANNEL_ID = 1550523337631866990







PREMIUM_ROLE_ID = 1503429265415471224



BOOSTER_ROLE_ID = 1504627495784284250



UPGRADE_CHANNEL_ID = 1503429504528548023


# Custom Role configuration
CUSTOM_ROLE_DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "custom_roles.json"
CUSTOM_ROLE_OWNER_ID = 937242913535033404
CUSTOM_ROLE_TICKET_CATEGORY_ID = 1546826352194494464
CUSTOM_ROLE_PAYPAL_URL = "https://www.paypal.com/ncp/payment/GR2EKPMCV5XAN"
CUSTOM_ROLE_ASSET_DIR = Path(__file__).resolve().parent.parent / "data" / "self_roles_assets"
CUSTOM_ROLE_CLOSE_AFTER_DAYS = 3
GREEN_EMBED_COLOR = discord.Color.from_str("#52FB18")
PROFILES_CHANNEL_URL = "https://discord.com/channels/1467231978813128834/1503429516943425607"

CUSTOM_ROLE_TIERS = {
    "Prestige": {
        "amount": "$50/month",
        "styles": ["Gradient", "Holographic"],
    },
    "Elite": {
        "amount": "$25/month",
        "styles": ["Gradient", "Holographic"],
    },
    "Classic": {
        "amount": "$15/month",
        "styles": ["Solid"],
    },
}











ROLE_CHANGE_TICKET_URL = "https://discord.com/channels/1467231978813128834/1503429512078164142"
ROLE_CHANGE_TICKET_CHANNEL_ID = 1503429512078164142







DIVIDER_URL = (



    "https://cdn.discordapp.com/attachments/1010905558624239739/"



    "1550541547219456132/dividerqwe_1.jpg?ex=6aaeb5d8&is=6aad6458&"



    "hm=3c4209eb13b2ca0b60ff07049093ba363de2ea19b0845b35aca84961ef3bfa18"



)











# =========================================================



# CHATLY EMOJIS



# =========================================================







# These are the custom emojis documented in Chatly.py → Emoji IDs.



# They are used directly in Discord components.



EMOJIS = {



    "user": discord.PartialEmoji(name="user", id=1550286898126262312),



    "globe": discord.PartialEmoji(name="globe", id=1550276963728367616),



    "chat": discord.PartialEmoji(name="chat", id=1550278354840588319),



    "mail": discord.PartialEmoji(name="message", id=1550283228072513626),



    "gift": discord.PartialEmoji(name="gift", id=1550282853479358464),
    "booster": discord.PartialEmoji(name="boost", id=1550552457120190585),
    "paypal": discord.PartialEmoji(name="paypal", id=1550551525204566057),
    "close": discord.PartialEmoji(name="close", id=1550533713526399126),



    "event": discord.PartialEmoji(name="event", id=1550282823242485820),



    "uparrow": discord.PartialEmoji(name="uparrow", id=1550289381347295292),



    "refresh": discord.PartialEmoji(name="refresh", id=1550282774714519664),



    "headphone": discord.PartialEmoji(name="headphone", id=1550536441879199835),



    "delete": discord.PartialEmoji(name="delete", id=1550282755017810070),



    "stars": discord.PartialEmoji(name="stars", id=1550289412624093234),



    "brush": discord.PartialEmoji(name="brush", id=1550540251238236301),



    "color_wheel": discord.PartialEmoji(



        name="color_wheel",



        id=1546874046174732350,



    ),



    "info": discord.PartialEmoji(name="info", id=1550551426269319168),



    "link": discord.PartialEmoji(name="link", id=1550536411189616670),



    "tick": discord.PartialEmoji(name="tick", id=1550538067570335764),



    "bullet": discord.PartialEmoji(name="bullet", id=1550533745424072714),



}











# =========================================================



# PANEL IMAGES



# =========================================================







PANEL_IMAGES = {



    "Age": "https://media.discordapp.net/attachments/1010905558624239739/1550535752037699664/23oiurhcn_n-removebg-preview.png?ex=6aaeb072&is=6aad5ef2&hm=ec1f2973d86cda60123c06a6cb70e8ae8e1b587e90f29f3d2bf64f3e6fddb4d8&=&format=webp&quality=lossless",



    "Gender": "https://media.discordapp.net/attachments/1010905558624239739/1550535752381759620/Gender-removebg-preview.png?ex=6aaeb072&is=6aad5ef2&hm=34c6fed79cb92258f6c1379a584d2897deb543e4d4b5f88f7d136e3936799928&=&format=webp&quality=lossless",



    "Region": "https://media.discordapp.net/attachments/1010905558624239739/1550535751714996276/Region-removebg-preview.png?ex=6aaeb072&is=6aad5ef2&hm=9aae362e7ea6248cd32cd65910e7571a528e1dd68a9c49ebb054290fb5ab4395&=&format=webp&quality=lossless",



    "Language": "https://media.discordapp.net/attachments/1010905558624239739/1550535753413431436/Language-removebg-preview.png?ex=6aaeb073&is=6aad5ef3&hm=32599536cc60deec4c61660da403c25b741d02b754ca23573fe4d473561e02af&=&format=webp&quality=lossless",



    "Notification": "https://media.discordapp.net/attachments/1010905558624239739/1550535753078145024/Notification-removebg-preview.png?ex=6aaeb073&is=6aad5ef3&hm=80bdf439b701935f8301df747ecce6e07e67f019ee67f0ca262cd1d1d6735b07&=&format=webp&quality=lossless",





}











# =========================================================



# ROLE CONFIGURATION



# =========================================================







ROLES = {



    "Age": [



        ("13–15", 1503429320318648381),



        ("16–17", 1503429321203646729),



        ("18–20", 1503429322487234790),



        ("21+", 1503429323489677405),



    ],



    "Gender": [



        ("Male", 1503429314220261519),



        ("Female", 1503429315537276969),



        ("Non-binary", 1525910712843763803),



    ],



    "Region": [



        ("Asia", 1503429374186094704),



        ("Africa", 1503429368838357002),



        ("North America", 1503429371795603488),



        ("South America", 1503429370755158167),



        ("Europe", 1503429376119931011),



        ("Oceania", 1503429369866227803),



    ],



    "Language": [



        ("English", 1525808854678638703),



        ("Hindi", 1525808954280644618),



        ("Spanish", 1525809033150201887),



        ("French", 1525809084023177317),



        ("German", 1525809136108048474),



        ("Portuguese", 1525809187848982599),



        ("Russian", 1525809232249618553),



        ("Japanese", 1525809281331367996),



        ("Korean", 1525809326910996580),



        ("Chinese", 1525809368832933908),



    ],



    "Notification": [



        ("Mail", 1525901711984820314),



        ("Giveaways", 1525901901462507520),



        ("Events", 1525902015866343617),



        ("Bump", 1525902078554148934),



        ("Updates", 1525902116793745410),



    ],



}











# =========================================================



# PREMIUM / BOOSTER COLOR ROLES



# =========================================================



PREMIUM_COLOR_ROLES = [

    ("Baby Pink", 1529190987342286968, 1529211744113922254),

    ("Cotton Candy", 1529191324962652270, 1529211741794472027),

    ("Sakura Pink", 1529191335309873244, 1529211739302789352),

    ("Blush Pink", 1529191289243828234, 1529211736626954441),

    ("Rose Quartz", 1529191301461835927, 1529211733858849059),

    ("Peach", 1529191314673893527, 1529211730998198362),

    ("Pastel Coral", 1529192307201544192, 1529211727919583364),

    ("Apricot", 1529192310544269462, 1529211725075714219),

    ("Butter Yellow", 1529192295780450374, 1529211722378903632),

    ("Vanilla Cream", 1529192283809775766, 1529211746718449845),

    ("Honey Gold", 1529192564945584378, 1529211679072714795),

    ("Mint Green", 1529192496490483743, 1529211600404222083),

    ("Pastel Green", 1529192552433975488, 1529211545207443526),

    ("Sage Green", 1529192537233821858, 1529211485178433546),

    ("Matcha", 1529192522793095270, 1529211462159958236),

    ("Baby Blue", 1529192510121840750, 1529211442694455388),

    ("Sky Blue", 1529192975996031137, 1529211424021151975),

    ("Powder Blue", 1529193032027734177, 1529211400667402300),

    ("Ice Blue", 1529193012003864666, 1529211380597657881),

    ("Aqua Mint", 1529192960628101252, 1529211351984246924),

    ("Lavender", 1529192930416525477, 1529211202033553619),

    ("Lilac", 1529192908488704150, 1529211178788851924),

    ("Wisteria", 1529193978124173393, 1529211135012634654),

    ("Periwinkle", 1529193952975130706, 1529211108831920159),

    ("Orchid", 1529193957165371493, 1529211033112154242),

    ("Mauve", 1529193937707732992, 1529211004750266368),

    ("Baby Purple", 1529193913993269329, 1529210978087075850),

    ("Soft Turquoise", 1529194163185258506, 1529210948840067184),

    ("Chatly Green", 1529194268164362291, 1529210900874264616),

    ("Champagne Gold", 1529194209498759349, 1529210918481952908),

]



BOOSTER_COLOR_ROLES = [

    ("Soft Pink", 1529194543281344692, 1529210882381447279),

    ("Baby Peach", 1529194529163313374, 1529210864169779331),

    ("Pale Yellow", 1529194427858419873, 1529210842652872784),

    ("Soft Mint", 1529194432682004624, 1529210825125007543),

    ("Baby Aqua", 1529194409894215782, 1529210808020631622),

    ("Soft Blue", 1529194758419779726, 1529210704572186804),

    ("Light Lavender", 1529194729978331316, 1529210474640441565),

    ("Pale Lilac", 1529194882030243890, 1529210619541061642),

    ("Soft Coral", 1529194846768861274, 1529210511785459866),

    ("Powder Purple", 1529195036510654636, 1529210495188602880),

]



ALL_COLOR_ROLE_IDS = {

    role_id

    for _, role_id, _ in PREMIUM_COLOR_ROLES + BOOSTER_COLOR_ROLES

}



def color_emoji(emoji_id: int, name: str) -> discord.PartialEmoji:

    return discord.PartialEmoji(name=name, id=emoji_id)





# =========================================================



# DROPDOWN CONFIGURATION



# =========================================================







CATEGORY_EMOJIS = {



    "Age": EMOJIS["user"],



    "Gender": EMOJIS["user"],



    "Region": EMOJIS["globe"],



    "Language": EMOJIS["chat"],



    "Notification": EMOJIS["mail"],





}







CLEAR_EMOJI = EMOJIS["delete"]







SINGLE_ROLE_CATEGORIES = {



    "Age",



    "Gender",



    "Region",



}







MULTI_ROLE_CATEGORIES = {



    "Language",



    "Notification",





}











# =========================================================



# ERROR LOGGING



# =========================================================







async def log_error(bot, message: str):



    channel = bot.get_channel(ERROR_CHANNEL_ID)







    if channel is None:



        return







    try:



        await channel.send(



            f"{EMOJIS['info']} **Self Roles Error**\n{message}"



        )



    except Exception:



        pass











# =========================================================



# ROLE ALREADY SELECTED VIEW



# =========================================================







class RoleChangeView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Button(
                label="Open Role Change Request",
                style=discord.ButtonStyle.link,
                emoji=EMOJIS["link"],
                url=ROLE_CHANGE_TICKET_URL,
            )
        )






# =========================================================



# ROLE SELECT



# =========================================================







class RoleSelect(discord.ui.Select):



    def __init__(self, category: str, bot):



        self.category = category



        self.bot_instance = bot







        options = []







        for role_name, role_id in ROLES[category]:



            options.append(



                discord.SelectOption(



                    label=role_name,



                    value=str(role_id),



                    emoji=CATEGORY_EMOJIS[category],



                )



            )







        options.append(



            discord.SelectOption(



                label="Clear all",



                value="clear",



                emoji=CLEAR_EMOJI,



            )



        )







        super().__init__(



            placeholder=f"Choose your {category} role",



            min_values=1,



            max_values=(



                1



                if category in SINGLE_ROLE_CATEGORIES



                else len(options)



            ),



            options=options,



            custom_id=(



                f"chatly:self_roles:"



                f"{category.lower().replace(' ', '_')}"



            ),



        )







    async def callback(self, interaction: discord.Interaction):



        guild = interaction.guild



        member = interaction.user







        if guild is None or not isinstance(member, discord.Member):



            await interaction.response.send_message(
                embed=green_embed(description=f"{EMOJIS['info']} This menu can only be used inside the server."),
                ephemeral=True,
            )



            return







        selected_values = set(self.values)







        category_role_ids = {



            role_id for _, role_id in ROLES[self.category]



        }







        # =================================================



        # AGE / GENDER LOCK



        # =================================================







        if self.category in {"Age", "Gender"}:



            existing_roles = [



                role



                for role in member.roles



                if role.id in category_role_ids



            ]







            if existing_roles:



                await interaction.response.send_message(
                    embed=green_embed(
                        description=(
                            f"{EMOJIS['info']} **Role Already Selected**\n\n"
                            f"{EMOJIS['user']} You already have a **{self.category} role** selected.\n\n"
                            f"{EMOJIS['link']} To change it, open a **Role Change Request** ticket from <#{ROLE_CHANGE_TICKET_CHANNEL_ID}>.\n\n"
                            "Our staff team will help you update it."
                        )
                    ),
                    view=RoleChangeView(),
                    ephemeral=True,
                )


                return







        # =================================================



        # CLEAR ALL



        # =================================================







        if "clear" in selected_values:



            roles_to_remove = [



                role



                for role in member.roles



                if role.id in category_role_ids



            ]







            if roles_to_remove:



                try:



                    await member.remove_roles(



                        *roles_to_remove,



                        reason=f"Self role clear: {self.category}",



                    )



                except discord.Forbidden:



                    await log_error(



                        self.bot_instance,



                        f"Missing permission while removing "



                        f"{self.category} roles from {member.id}.",



                    )



                    await interaction.response.send_message(
                embed=green_embed(description=f"{EMOJIS['info']} I don't have permission to change your roles."),
                ephemeral=True,
            )



                    return



                except discord.HTTPException as error:



                    await log_error(



                        self.bot_instance,



                        f"Discord error while removing {self.category} "



                        f"roles from {member.id}: `{error}`",



                    )



                    await interaction.response.send_message(
                embed=green_embed(description=f"{EMOJIS['info']} Discord could not update your roles."),
                ephemeral=True,
            )



                    return







            await interaction.response.send_message(
                embed=green_embed(description=f"{EMOJIS['tick']} Your **{self.category}** roles have been cleared."),
                ephemeral=True,
            )



            return







        # =================================================



        # SINGLE ROLE CATEGORY



        # =================================================







        if self.category in SINGLE_ROLE_CATEGORIES:



            selected_role_id = int(next(iter(selected_values)))







            role = guild.get_role(selected_role_id)







            if role is None:



                await log_error(



                    self.bot_instance,



                    f"Configured role `{selected_role_id}` for "



                    f"{self.category} does not exist.",



                )



                await interaction.response.send_message(
                embed=green_embed(description=f"{EMOJIS['info']} That role is currently unavailable."),
                ephemeral=True,
            )



                return







            roles_to_remove = [



                existing



                for existing in member.roles



                if existing.id in category_role_ids



                and existing.id != selected_role_id



            ]







            try:



                if roles_to_remove:



                    await member.remove_roles(



                        *roles_to_remove,



                        reason=f"Self role replacement: {self.category}",



                    )







                if role not in member.roles:



                    await member.add_roles(



                        role,



                        reason=f"Self role selection: {self.category}",



                    )







            except discord.Forbidden:



                await log_error(



                    self.bot_instance,



                    f"Missing permission while updating "



                    f"{self.category} for {member.id}.",



                )



                await interaction.response.send_message(
                embed=green_embed(description=f"{EMOJIS['info']} I don't have permission to change your roles."),
                ephemeral=True,
            )



                return



            except discord.HTTPException as error:



                await log_error(



                    self.bot_instance,



                    f"Discord error while updating {self.category} "



                    f"for {member.id}: `{error}`",



                )



                await interaction.response.send_message(
                embed=green_embed(description=f"{EMOJIS['info']} Discord could not update your roles."),
                ephemeral=True,
            )



                return







            await interaction.response.send_message(
                embed=green_embed(description=f"{EMOJIS['tick']} Updated your **{self.category}** role: {role.mention}"),
                ephemeral=True,
            )



            return







        # =================================================



        # MULTI ROLE TOGGLE



        # =================================================







        roles_to_add = []



        roles_to_remove = []







        for role_id in {



            int(value)



            for value in selected_values



            if value != "clear"



        }:



            role = guild.get_role(role_id)







            if role is None:



                await log_error(



                    self.bot_instance,



                    f"Configured role `{role_id}` for "



                    f"{self.category} does not exist.",



                )



                continue







            if role in member.roles:



                roles_to_remove.append(role)



            else:



                roles_to_add.append(role)







        try:



            if roles_to_remove:



                await member.remove_roles(



                    *roles_to_remove,



                    reason=f"Self role toggle removal: {self.category}",



                )







            if roles_to_add:



                await member.add_roles(



                    *roles_to_add,



                    reason=f"Self role toggle addition: {self.category}",



                )







        except discord.Forbidden:



            await log_error(



                self.bot_instance,



                f"Missing permission while toggling "



                f"{self.category} roles for {member.id}.",



            )



            await interaction.response.send_message(
                embed=green_embed(description=f"{EMOJIS['info']} I don't have permission to change your roles."),
                ephemeral=True,
            )



            return



        except discord.HTTPException as error:



            await log_error(



                self.bot_instance,



                f"Discord error while toggling {self.category} "



                f"roles for {member.id}: `{error}`",



            )



            await interaction.response.send_message(
                embed=green_embed(description=f"{EMOJIS['info']} Discord could not update your roles."),
                ephemeral=True,
            )



            return







        changes = []







        if roles_to_add:



            changes.append(



                f"added {', '.join(role.mention for role in roles_to_add)}"



            )







        if roles_to_remove:



            changes.append(



                f"removed {', '.join(role.mention for role in roles_to_remove)}"



            )







        if changes:



            response = (



                f"{EMOJIS['tick']} Updated your **{self.category}** roles: "



                + " and ".join(changes)



                + "."



            )



        else:



            response = (



                f"{EMOJIS['tick']} Your **{self.category}** roles are up to date."



            )







        await interaction.response.send_message(
                embed=green_embed(description=response),
                ephemeral=True,
            )











# =========================================================



def green_embed(*, title: str | None = None, description: str | None = None):
    return discord.Embed(title=title, description=description, color=GREEN_EMBED_COLOR)


def custom_role_asset(name: str) -> Path:
    return CUSTOM_ROLE_ASSET_DIR / name


def asset_file(name: str):
    path = custom_role_asset(name)
    return discord.File(str(path), filename=name) if path.exists() else None


# COLOR ROLE ACCESS / UPGRADE PANEL



# =========================================================



def upgrade_url() -> str:

    return (

        f"https://discord.com/channels/"

        f"1467231978813128834/{UPGRADE_CHANNEL_ID}"

    )





async def send_color_access_denied(interaction: discord.Interaction, required: str):
    if required == "Premium":
        description = f"{EMOJIS['info']} **Premium Colors are locked**\n\nUnlock Chatly Premium from <#{UPGRADE_CHANNEL_ID}> to continue."
        button_label, button_emoji = "Unlock Chatly Premium", EMOJIS["stars"]
    else:
        description = f"{EMOJIS['info']} **Booster Colors are locked**\n\nBoost Chatly to unlock Booster Colors from <#{UPGRADE_CHANNEL_ID}>."
        button_label, button_emoji = "Open Upgrade", EMOJIS["booster"]
    embed = green_embed(description=description)
    view = discord.ui.View(timeout=180)
    view.add_item(discord.ui.Button(label=button_label, style=discord.ButtonStyle.link, emoji=button_emoji, url=upgrade_url()))
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class ColorRoleSelect(discord.ui.Select):

    def __init__(

        self,

        color_type: str,

        colors: list[tuple[str, int, int]],

        bot,

        page: int = 0,

    ):

        self.color_type = color_type

        self.bot_instance = bot

        self.page = page



        options = [

            discord.SelectOption(

                label=name,

                value=str(role_id),

                emoji=color_emoji(emoji_id, name),

            )

            for name, role_id, emoji_id in colors

        ]



        options.append(

            discord.SelectOption(

                label="Clear color",

                value="clear",

                emoji=EMOJIS["delete"],

            )

        )



        placeholder = (

            f"Choose a Premium color · Set {'I' if page == 0 else 'II'}"

            if color_type == "Premium"

            else "Choose a Booster color"

        )



        super().__init__(

            placeholder=placeholder,

            min_values=1,

            max_values=1,

            options=options,

            custom_id=f"chatly:self_roles:{color_type.lower()}_colors:{page}",

        )



    async def callback(self, interaction: discord.Interaction):

        guild = interaction.guild

        member = interaction.user



        if guild is None or not isinstance(member, discord.Member):

            await interaction.response.send_message(
                embed=green_embed(description=f"{EMOJIS['info']} This menu can only be used inside the server."),
                ephemeral=True,
            )

            return



        required_role_id = (

            PREMIUM_ROLE_ID

            if self.color_type == "Premium"

            else BOOSTER_ROLE_ID

        )



        if member.get_role(required_role_id) is None:

            await send_color_access_denied(interaction, self.color_type)

            return



        selected = self.values[0]



        if selected == "clear":

            roles_to_remove = [

                role for role in member.roles

                if role.id in ALL_COLOR_ROLE_IDS

            ]



            try:

                if roles_to_remove:

                    await member.remove_roles(

                        *roles_to_remove,

                        reason="Self role color clear",

                    )

            except discord.Forbidden:

                await log_error(

                    self.bot_instance,

                    f"Missing permission while clearing color roles from {member.id}.",

                )

                await interaction.response.send_message(
                embed=green_embed(description=f"{EMOJIS['info']} I don't have permission to change your color role."),
                ephemeral=True,
            )

                return

            except discord.HTTPException as error:

                await log_error(

                    self.bot_instance,

                    f"Discord error while clearing color roles from {member.id}: `{error}`",

                )

                await interaction.response.send_message(
                embed=green_embed(description=f"{EMOJIS['info']} Discord could not update your color role."),
                ephemeral=True,
            )

                return



            await interaction.response.send_message(
                embed=green_embed(description=f"{EMOJIS['tick']} Your color role has been cleared."),
                ephemeral=True,
            )

            return



        role_id = int(selected)

        role = guild.get_role(role_id)



        if role is None:

            await log_error(

                self.bot_instance,

                f"Configured color role `{role_id}` does not exist.",

            )

            await interaction.response.send_message(
                embed=green_embed(description=f"{EMOJIS['info']} That color role is currently unavailable."),
                ephemeral=True,
            )

            return



        roles_to_remove = [

            existing

            for existing in member.roles

            if existing.id in ALL_COLOR_ROLE_IDS

            and existing.id != role_id

        ]



        try:

            if roles_to_remove:

                await member.remove_roles(

                    *roles_to_remove,

                    reason="Self role color replacement",

                )



            if role not in member.roles:

                await member.add_roles(

                    role,

                    reason=f"Self role color selection: {self.color_type}",

                )

        except discord.Forbidden:

            await log_error(

                self.bot_instance,

                f"Missing permission while updating color role for {member.id}.",

            )

            await interaction.response.send_message(
                embed=green_embed(description=f"{EMOJIS['info']} I don't have permission to change your color role."),
                ephemeral=True,
            )

            return

        except discord.HTTPException as error:

            await log_error(

                self.bot_instance,

                f"Discord error while updating color role for {member.id}: `{error}`",

            )

            await interaction.response.send_message(
                embed=green_embed(description=f"{EMOJIS['info']} Discord could not update your color role."),
                ephemeral=True,
            )

            return



        await interaction.response.send_message(
                embed=green_embed(description=f"{EMOJIS['tick']} Updated your color role: {role.mention}"),
                ephemeral=True,
            )





class ColorPickerView(discord.ui.View):

    def __init__(self, bot):

        super().__init__(timeout=300)

        self.add_item(ColorPickerButton(bot))





class ColorPickerButton(discord.ui.Button):
    def __init__(self, bot):
        self.bot_instance = bot
        super().__init__(label="Choose Your Colors", style=discord.ButtonStyle.secondary, emoji=EMOJIS["color_wheel"], custom_id="chatly:self_roles:choose_colors")

    async def callback(self, interaction: discord.Interaction):
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(embed=green_embed(description=f"{EMOJIS['info']} This button can only be used inside the server."), ephemeral=True)
            return

        premium_embed = green_embed()
        premium_file = asset_file("premium_colors_banner.png")
        if premium_file:
            premium_embed.set_image(url="attachment://premium_colors_banner.png")
        else:
            premium_embed.description = f"{EMOJIS['info']} Premium color banner asset is missing from the bot installation."

        booster_embed = green_embed()
        booster_file = asset_file("booster_colors_banner.png")
        if booster_file:
            booster_embed.set_image(url="attachment://booster_colors_banner.png")
        else:
            booster_embed.description = f"{EMOJIS['info']} Booster color banner asset is missing from the bot installation."

        premium_kwargs = {"embed": premium_embed, "view": PremiumColorPickerView(self.bot_instance), "ephemeral": True}
        booster_kwargs = {"embed": booster_embed, "view": BoosterColorPickerView(self.bot_instance), "ephemeral": True}
        if premium_file: premium_kwargs["file"] = premium_file
        if booster_file: booster_kwargs["file"] = booster_file
        await interaction.response.send_message(**premium_kwargs)
        await interaction.followup.send(**booster_kwargs)


class PremiumColorPickerView(discord.ui.View):

    def __init__(self, bot):

        super().__init__(timeout=300)

        # 31 Premium colors require two menus; this is the minimum possible.

        self.add_item(ColorRoleSelect("Premium", PREMIUM_COLOR_ROLES[:16], bot, page=0))

        self.add_item(ColorRoleSelect("Premium", PREMIUM_COLOR_ROLES[16:], bot, page=1))





class BoosterColorPickerView(discord.ui.View):

    def __init__(self, bot):

        super().__init__(timeout=300)

        self.add_item(ColorRoleSelect("Booster", BOOSTER_COLOR_ROLES, bot))





class RoleView(discord.ui.View):

    def __init__(self, category: str, bot):

        super().__init__(timeout=None)

        self.add_item(RoleSelect(category, bot))






# =========================================================
# CUSTOM ROLES
# =========================================================


def _load_custom_roles():
    try:
        if not CUSTOM_ROLE_DATA_FILE.exists(): return {}
        with CUSTOM_ROLE_DATA_FILE.open("r", encoding="utf-8") as f: return json.load(f)
    except (OSError, json.JSONDecodeError): return {}


def _save_custom_roles(data):
    try:
        CUSTOM_ROLE_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = CUSTOM_ROLE_DATA_FILE.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f: json.dump(data, f, indent=2)
        tmp.replace(CUSTOM_ROLE_DATA_FILE)
    except OSError: pass


def _cr_key(guild_id, user_id): return f"{guild_id}:{user_id}"
def _cr_owner(member): return member.id == CUSTOM_ROLE_OWNER_ID or any(r.id == OWNER_ROLE_ID for r in member.roles)

def _cr_hex(value):
    value = value.strip().upper(); value = value if value.startswith("#") else "#" + value
    return value if re.fullmatch(r"#[0-9A-F]{6}", value) else None

def _cr_embed(record, title="Custom Role"):
    e = green_embed(title=f"{EMOJIS['brush']} {title}", description=f"**Tier:** {record['tier']}\n**Price:** {record['amount']}\n**Buyer:** <@{record['user_id']}>")
    for k, n in (("role_name", "Role Name"), ("style", "Style"), ("primary_hex", "Color 1"), ("secondary_hex", "Color 2"), ("icon_description", "Prestige Icon / Design")):
        if record.get(k): e.add_field(name=n, value=f"`{record[k]}`" if k.endswith("hex") else str(record[k])[:1024], inline=k in {"style", "primary_hex", "secondary_hex"})
    return e

def _cr_touch(record): record["last_activity"] = datetime.now(timezone.utc).isoformat()


class CustomRolePayButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Pay Now", style=discord.ButtonStyle.primary, emoji=EMOJIS["paypal"], custom_id="chatly:self_roles:custom:pay")
    async def callback(self, interaction):
        data = _load_custom_roles(); record = data.get(_cr_key(interaction.guild.id, interaction.user.id)) if interaction.guild else None
        if not record or record.get("ticket_id") != interaction.channel_id:
            return await interaction.response.send_message(embed=green_embed(description=f"{EMOJIS['info']} This is not your Custom Role ticket."), ephemeral=True)
        _cr_touch(record); data[_cr_key(interaction.guild.id, interaction.user.id)] = record; _save_custom_roles(data)
        embed = green_embed(title=f"{EMOJIS['paypal']} Custom Role Payment", description=f"Scan the QR code or use the **PayPal** button below to complete your payment.\n\nAfter payment, send your **payment screenshot** and relevant payment details in this ticket.\n\n{EMOJIS['info']} Processing may take some time because of timezone differences.")
        qr = asset_file("paypal_qr.png")
        if qr: embed.set_image(url="attachment://paypal_qr.png")
        view = discord.ui.View(timeout=180); view.add_item(discord.ui.Button(label="Pay with PayPal", style=discord.ButtonStyle.link, emoji=EMOJIS["paypal"], url=CUSTOM_ROLE_PAYPAL_URL))
        kwargs = {"embed": embed, "view": view, "ephemeral": True};
        if qr: kwargs["file"] = qr
        await interaction.response.send_message(**kwargs)


class CustomRoleCloseButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Close Ticket", style=discord.ButtonStyle.secondary, emoji=EMOJIS["close"], custom_id="chatly:self_roles:custom:close")
    async def callback(self, interaction):
        if interaction.guild is None or not isinstance(interaction.user, discord.Member): return
        data = _load_custom_roles(); key, record = next(((k, v) for k, v in data.items() if v.get("ticket_id") == interaction.channel_id), (None, None))
        if not record: return await interaction.response.send_message(embed=green_embed(description=f"{EMOJIS['info']} This is not an active Custom Role ticket."), ephemeral=True)
        if interaction.user.id != int(record["user_id"]) and not _cr_owner(interaction.user): return await interaction.response.send_message(embed=green_embed(description=f"{EMOJIS['info']} You don't have access to close this ticket."), ephemeral=True)
        record.update({"status": "closed", "active": False, "closed_at": datetime.now(timezone.utc).isoformat()}); _save_custom_roles(data)
        await interaction.response.send_message(embed=green_embed(description=f"{EMOJIS['tick']} **Ticket Closed**\n\nThis Custom Role ticket is being closed."))
        await interaction.channel.delete(reason="Chatly Custom Role ticket closed")


class CustomRoleTierButton(discord.ui.Button):
    def __init__(self, tier):
        super().__init__(label=f"{tier} • {CUSTOM_ROLE_TIERS[tier]['amount']}", style=discord.ButtonStyle.secondary, emoji=EMOJIS["stars"], custom_id=f"chatly:self_roles:custom:{tier.lower()}"); self.tier = tier
    async def callback(self, interaction):
        guild, member = interaction.guild, interaction.user
        if guild is None or not isinstance(member, discord.Member): return await interaction.response.send_message(embed=green_embed(description=f"{EMOJIS['info']} Server only."), ephemeral=True)
        data = _load_custom_roles(); key = _cr_key(guild.id, member.id); old = data.get(key, {})
        if old.get("active"): return await interaction.response.send_message(embed=green_embed(description=f"{EMOJIS['info']} You already have an active Custom Role."), ephemeral=True)
        if old.get("ticket_id") and guild.get_channel(int(old["ticket_id"])): return await interaction.response.send_message(embed=green_embed(description=f"{EMOJIS['info']} You already have an open Custom Role ticket: <#{old['ticket_id']}>"), ephemeral=True)
        category = guild.get_channel(CUSTOM_ROLE_TICKET_CATEGORY_ID)
        if not isinstance(category, discord.CategoryChannel): return await interaction.response.send_message(embed=green_embed(description=f"{EMOJIS['info']} Custom Role tickets are temporarily unavailable."), ephemeral=True)
        overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False), member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, attach_files=True)}
        owner = guild.get_role(OWNER_ROLE_ID)
        if owner: overwrites[owner] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_messages=True)
        if guild.me: overwrites[guild.me] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_channels=True, manage_messages=True)
        try: ticket = await guild.create_text_channel(f"🎨・custom-role-{member.id}", category=category, overwrites=overwrites, topic=f"Custom Role Purchase • {self.tier}", reason="Chatly Custom Role purchase")
        except (discord.Forbidden, discord.HTTPException): return await interaction.response.send_message(embed=green_embed(description=f"{EMOJIS['info']} I couldn't create your Custom Role ticket."), ephemeral=True)
        now = datetime.now(timezone.utc).isoformat(); record = {"guild_id": guild.id, "user_id": member.id, "tier": self.tier, "amount": CUSTOM_ROLE_TIERS[self.tier]["amount"], "ticket_id": ticket.id, "active": False, "status": "payment_pending", "created_at": now, "last_activity": now}; data[key] = record; _save_custom_roles(data)
        e = green_embed(title=f"{EMOJIS['brush']} Custom Role Purchase", description=f"**Tier:** {self.tier}\n**Price:** {record['amount']}\n\nUse **Pay Now** to complete payment, then send your payment screenshot in this ticket and use **Customize Role**.")
        await ticket.send(content=member.mention, embed=e, view=CustomRoleTicketView())
        await interaction.response.send_message(embed=green_embed(description=f"{EMOJIS['tick']} Your Custom Role ticket is ready: {ticket.mention}"), ephemeral=True)


class CustomRoleTierView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        for tier in ("Prestige", "Elite", "Classic"): self.add_item(CustomRoleTierButton(tier))


class CustomRoleTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CustomRolePayButton()); self.add_item(CustomizeRoleButton()); self.add_item(ConfirmCustomRoleButton()); self.add_item(CustomRoleCloseButton())


class CustomizeRoleButton(discord.ui.Button):
    def __init__(self): super().__init__(label="Customize Role", style=discord.ButtonStyle.secondary, emoji=EMOJIS["brush"], custom_id="chatly:self_roles:customize_role")
    async def callback(self, interaction):
        if interaction.guild is None or not isinstance(interaction.user, discord.Member): return await interaction.response.send_message(embed=green_embed(description=f"{EMOJIS['info']} Server only."), ephemeral=True)
        data = _load_custom_roles(); record = data.get(_cr_key(interaction.guild.id, interaction.user.id))
        if not record or record.get("ticket_id") != interaction.channel_id: return await interaction.response.send_message(embed=green_embed(description=f"{EMOJIS['info']} This is not your Custom Role ticket."), ephemeral=True)
        _cr_touch(record); data[_cr_key(interaction.guild.id, interaction.user.id)] = record; _save_custom_roles(data); await interaction.response.send_modal(CustomRoleModal())


class CustomRoleModal(discord.ui.Modal, title="Customize Your Custom Role"):
    name = discord.ui.TextInput(label="Role Name", max_length=100, required=True)
    style = discord.ui.TextInput(label="Style", placeholder="Gradient / Holographic / Solid", max_length=20, required=True)
    color1 = discord.ui.TextInput(label="Primary HEX", placeholder="#52FB18", max_length=7, required=True)
    color2 = discord.ui.TextInput(label="Second HEX", placeholder="#FFFFFF (gradient/holographic only)", max_length=7, required=False)
    icon = discord.ui.TextInput(label="Prestige Icon / Design", style=discord.TextStyle.paragraph, max_length=1000, required=False)
    async def on_submit(self, interaction):
        guild, member = interaction.guild, interaction.user; data = _load_custom_roles(); key = _cr_key(guild.id, member.id); record = data.get(key)
        if not record or record.get("ticket_id") != interaction.channel_id: return await interaction.response.send_message(embed=green_embed(description=f"{EMOJIS['info']} Ticket not found."), ephemeral=True)
        style = str(self.style.value).strip().title(); tier = record["tier"]
        if style not in CUSTOM_ROLE_TIERS[tier]["styles"]: return await interaction.response.send_message(embed=green_embed(description=f"{EMOJIS['info']} {tier} supports: {', '.join(CUSTOM_ROLE_TIERS[tier]['styles'])}."), ephemeral=True)
        c1 = _cr_hex(str(self.color1.value)); c2 = str(self.color2.value).strip()
        if not c1: return await interaction.response.send_message(embed=green_embed(description=f"{EMOJIS['info']} Invalid primary HEX."), ephemeral=True)
        if style in {"Gradient", "Holographic"}:
            c2 = _cr_hex(c2)
            if not c2: return await interaction.response.send_message(embed=green_embed(description=f"{EMOJIS['info']} A valid second HEX is required."), ephemeral=True)
        else: c2 = ""
        icon = str(self.icon.value).strip()
        if tier == "Prestige" and not icon: return await interaction.response.send_message(embed=green_embed(description=f"{EMOJIS['info']} Prestige requires an icon/design description."), ephemeral=True)
        record.update({"role_name": str(self.name.value).strip(), "style": style, "primary_hex": c1, "secondary_hex": c2, "icon_description": icon, "status": "awaiting_owner_review"}); _cr_touch(record); data[key] = record; _save_custom_roles(data)
        await interaction.response.send_message(embed=_cr_embed(record, "Customization Saved"), ephemeral=True)
        await interaction.channel.send(f"{EMOJIS['tick']} Customization saved. <@{CUSTOM_ROLE_OWNER_ID}> can review the payment proof and confirm activation.")


class ConfirmCustomRoleButton(discord.ui.Button):
    def __init__(self): super().__init__(label="Confirm Payment", style=discord.ButtonStyle.success, emoji=EMOJIS["tick"], custom_id="chatly:self_roles:confirm_custom_role")
    async def callback(self, interaction):
        if interaction.guild is None or not isinstance(interaction.user, discord.Member) or not _cr_owner(interaction.user): return await interaction.response.send_message(embed=green_embed(description=f"{EMOJIS['info']} You don't have access to use this button."), ephemeral=True)
        data = _load_custom_roles(); key, record = next(((k, v) for k, v in data.items() if v.get("ticket_id") == interaction.channel_id), (None, None))
        if not record or record.get("status") != "awaiting_owner_review": return await interaction.response.send_message(embed=green_embed(description=f"{EMOJIS['info']} Complete customization is required before activation."), ephemeral=True)
        member = interaction.guild.get_member(int(record["user_id"]))
        if not member: return await interaction.response.send_message(embed=green_embed(description=f"{EMOJIS['info']} Buyer is no longer in the server."), ephemeral=True)
        try:
            role = await interaction.guild.create_role(name=record["role_name"][:100], colour=discord.Colour.from_str(record["primary_hex"]), reason="Chatly Custom Role activation"); await member.add_roles(role, reason="Chatly Custom Role activation")
        except (discord.Forbidden, discord.HTTPException) as error:
            await log_error(interaction.client, f"Custom Role activation failed: {error}"); return await interaction.response.send_message(embed=green_embed(description=f"{EMOJIS['info']} I couldn't create or assign the role."), ephemeral=True)
        expires = datetime.now(timezone.utc) + timedelta(days=30); record.update({"created_role_id": role.id, "active": True, "status": "active", "activated_at": datetime.now(timezone.utc).isoformat(), "expires_at": expires.isoformat()}); _cr_touch(record); data[key] = record; _save_custom_roles(data)
        await interaction.response.send_message(embed=green_embed(description=f"{EMOJIS['tick']} **Custom Role activated.** {role.mention} assigned to <@{record['user_id']}>. Expires <t:{int(expires.timestamp())}:F>."))


class CustomRoleLaunchButton(discord.ui.Button):
    def __init__(self, bot): super().__init__(label="Create Custom Role", style=discord.ButtonStyle.secondary, emoji=EMOJIS["brush"], custom_id="chatly:self_roles:create_custom_role"); self.bot = bot
    async def callback(self, interaction):
        embed = green_embed(); file = asset_file("custom_roles_banner.png")
        if file: embed.set_image(url="attachment://custom_roles_banner.png")
        else: embed.description = f"{EMOJIS['info']} Custom Role banner asset is missing from the bot installation."
        kwargs = {"embed": embed, "view": CustomRoleTierView(), "ephemeral": True}
        if file: kwargs["file"] = file
        await interaction.response.send_message(**kwargs)


class FinalRolesView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None); self.add_item(ColorPickerButton(bot)); self.add_item(CustomRoleLaunchButton(bot))


class SelfRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(FinalRolesView(self.bot)); self.bot.add_view(CustomRoleTicketView())
        for category in ROLES: self.bot.add_view(RoleView(category, self.bot))
        if not self.custom_role_expiry_task.is_running(): self.custom_role_expiry_task.start()

    @tasks.loop(hours=1)
    async def custom_role_expiry_task(self):
        data = _load_custom_roles(); changed = False; now = datetime.now(timezone.utc)
        for key, record in list(data.items()):
            guild = self.bot.get_guild(int(record.get("guild_id", 0)))
            if guild is None: continue
            ticket = guild.get_channel(int(record.get("ticket_id", 0))) if record.get("ticket_id") else None
            if ticket and record.get("status") in {"payment_pending", "awaiting_owner_review"} and record.get("last_activity"):
                try: last_activity = datetime.fromisoformat(record["last_activity"])
                except ValueError: last_activity = now
                if now - last_activity >= timedelta(days=CUSTOM_ROLE_CLOSE_AFTER_DAYS):
                    record.update({"status": "closed_inactive", "active": False, "closed_at": now.isoformat()}); changed = True
                    try: await ticket.delete(reason="Chatly Custom Role ticket inactive for 3 days")
                    except discord.HTTPException: pass
                    continue
            if not record.get("active") or not record.get("expires_at"): continue
            try: expires = datetime.fromisoformat(record["expires_at"])
            except ValueError: continue
            member = guild.get_member(int(record.get("user_id", 0))); role = guild.get_role(int(record.get("created_role_id", 0))) if record.get("created_role_id") else None
            if now >= expires - timedelta(days=3) and not record.get("expiry_reminder_sent") and member:
                try: await member.send(f"{EMOJIS['info']} Your **{record['tier']}** Custom Role expires in 3 days. Renew through the **Create Custom Role** button in the Roles panel.")
                except discord.HTTPException: pass
                record["expiry_reminder_sent"] = True; changed = True
            if now >= expires:
                if member and role and role in member.roles:
                    try: await member.remove_roles(role, reason="Chatly Custom Role subscription expired")
                    except discord.HTTPException: pass
                if member:
                    try: await member.send(f"{EMOJIS['info']} **Your Custom Role has expired.**\n\nYou can purchase a new Custom Role from the **Create Custom Role** button in the Roles panel.")
                    except discord.HTTPException: pass
                record.update({"active": False, "status": "expired", "expired_at": now.isoformat()}); changed = True
        if changed: _save_custom_roles(data)

    @custom_role_expiry_task.before_loop
    async def before_custom_role_expiry_task(self): await self.bot.wait_until_ready()

    async def cog_unload(self): self.custom_role_expiry_task.cancel()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None: return
        data = _load_custom_roles(); changed = False; now = datetime.now(timezone.utc).isoformat()
        for record in data.values():
            if record.get("ticket_id") == message.channel.id and record.get("status") in {"payment_pending", "awaiting_owner_review"}:
                record["last_activity"] = now; changed = True; break
        if changed: _save_custom_roles(data)

    # /SETUP-ROLES



    # =====================================================







    @tasks.loop(hours=1)
    async def custom_role_expiry_task(self):
        data = _load_custom_roles()
        changed = False
        now = datetime.now(timezone.utc)
        for key, record in list(data.items()):
            if not record.get("active") or not record.get("expires_at"):
                continue
            try:
                expires = datetime.fromisoformat(record["expires_at"])
            except ValueError:
                continue
            guild = self.bot.get_guild(int(record.get("guild_id", 0)))
            if guild is None:
                continue
            member = guild.get_member(int(record.get("user_id", 0)))
            role = guild.get_role(int(record.get("created_role_id", 0))) if record.get("created_role_id") else None
            if now >= expires - timedelta(days=3) and not record.get("expiry_reminder_sent") and member:
                try:
                    await member.send(f"{EMOJIS['info']} Your **{record['tier']}** Custom Role expires in 3 days. Renew through the **Create Custom Role** button in the Roles panel.")
                except discord.HTTPException:
                    pass
                record["expiry_reminder_sent"] = True
                changed = True
            if now >= expires:
                if member and role and role in member.roles:
                    try:
                        await member.remove_roles(role, reason="Chatly Custom Role subscription expired")
                    except discord.HTTPException:
                        pass
                if member:
                    try:
                        await member.send(f"{EMOJIS['info']} **Your Custom Role has expired.**\n\nYou can purchase a new Custom Role from the **Create Custom Role** button in the Roles panel.")
                    except discord.HTTPException:
                        pass
                record.update({"active": False, "status": "expired", "expired_at": now.isoformat()})
                changed = True
        if changed:
            _save_custom_roles(data)

    @custom_role_expiry_task.before_loop
    async def before_custom_role_expiry_task(self):
        await self.bot.wait_until_ready()

    @app_commands.command(



        name="setup-roles",



        description="Post a new complete Self Roles panel.",



    )



    async def setup_roles(



        self,



        interaction: discord.Interaction,



    ):



        # -------------------------------------------------



        # OWNER CHECK



        # -------------------------------------------------







        if not isinstance(interaction.user, discord.Member):



            await interaction.response.send_message(



                f"{EMOJIS['info']} You don't have permission to use this command.",



                ephemeral=True,



            )



            return







        if not any(



            role.id == OWNER_ROLE_ID



            for role in interaction.user.roles



        ):



            await interaction.response.send_message(
                embed=green_embed(description=f"{EMOJIS['info']} You don't have permission to use this command."),
                ephemeral=True,
            )



            return







        await interaction.response.defer(ephemeral=True)







        channel = interaction.channel







        if channel is None:



            await interaction.followup.send(



                f"{EMOJIS['info']} This command must be used in a channel.",



                ephemeral=True,



            )



            return











        # =================================================



        # POST ALL SIX PANELS



        # =================================================







        for category in [



            "Age",



            "Gender",



            "Region",



            "Language",



            "Notification",



        ]:



            embed = discord.Embed()



            embed.set_image(url=PANEL_IMAGES[category])







            try:



                message = await channel.send(



                    embed=embed,



                    view=RoleView(category, self.bot),



                )







            except Exception as error:



                await log_error(



                    self.bot,



                    f"Failed to post `{category}` panel.\n"



                    f"Error: `{error}`",



                )



                continue







        # =================================================



                # =================================================



# FINAL PANEL



        # =================================================







        final_embed = discord.Embed(
            color=GREEN_EMBED_COLOR,
            description=(
                "**Make your profile feel more like you.**\n"
                "Use the options below to add a color role or create a custom role and give your profile a more distinctive presence throughout the server.\n\n"
                f"{EMOJIS['info']} Interact with the buttons below to explore your available options.\n\n"
                "**Finished choosing your roles?** Head over to "
                f"**[Profiles]({PROFILES_CHANNEL_URL})** to create and customize your profile.\n\n"
                "**Want to stand out?** Choose a custom profile color from the Premium or Booster collections."
            )
        )


        # Divider is the final visual element.



        final_embed.set_image(url=DIVIDER_URL)







        try:



            await channel.send(



                embed=final_embed,



                view=FinalRolesView(self.bot),



            )







        except Exception as error:



            await log_error(



                self.bot,



                f"Failed to post the final Self Roles panel.\n"



                f"Error: `{error}`",



            )







        # =================================================



        # COMPLETE



        # =================================================







        await interaction.followup.send(
            embed=green_embed(
                description=(
                    f"{EMOJIS['tick']} **Self Roles panels posted successfully.**\n\n"
                    f"{EMOJIS['bullet']} A new complete panel set was created in this channel."
                )
            ),
            ephemeral=True,
        )











# =========================================================



# SETUP



# =========================================================







async def setup(bot):



    await bot.add_cog(SelfRoles(bot))
