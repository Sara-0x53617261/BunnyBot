import os
import logging
import random

# Discord imports
import discord
from discord import app_commands
import typing


# Setup logging
logs = logging.getLogger("discord")
logs.setLevel(logging.INFO)
logs.name = "BunnyBot"

# Load enviroment variables
from dotenv import load_dotenv
load_dotenv()
bot_secret = os.getenv('SECRET')
guild_id_dev = os.getenv("GUILD_ID_DEV")
guild_id_main = os.getenv("GUILD_ID")


# Discord Client
class myClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.synced = False

    async def on_ready(self):
        await self.wait_until_ready()

        if not self.synced:
            # Sync the slash commands with discord
            logs.info("myClient.on_ready - Syncing commands...")
            await tree.sync()
            self.synced = True

        logs.info("myClient.on_ready - changing presence...")
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="all the cuties in this discord"))

        logs.info("myClient.on_ready - Ready!")
        

# initialize client
client = myClient()
tree = app_commands.CommandTree(client)


"""
    Slash commands
"""

# Calls the user cute
@tree.command(name = "cutie_finder", description="Who is cute?")
async def cutie_finder(interaction: discord.Interaction):

    logs.info(f"cutie_finder - {interaction.user.name}")

    await interaction.response.send_message(f"You, yes **you** are the cutie {interaction.user.mention}")


# Calls a selected user cute
@tree.command(name="call_cute", description="makes sure the given user knows they're a cutie")
async def call_cute(interaction: discord.Interaction, user: discord.Member, option:typing.Optional[app_commands.Range[int, 0, 4]] = None):
    
    logs.info(f"call_cute - {interaction.user.name} | arguments [ user: {user.name}, option: {option}")

    # If someone tries to call the bot cute:
    if user.id == client.user.id:
        await interaction.response.send_message(f"nuh-uh You're way cuter than me {interaction.user.mention}")
        return

    # Hidden message so the selected user is not able to see who used the command
    await interaction.response.send_message("I will let them know they're cute..", ephemeral=True)

    # Message list, random or 'option' will select from this
    messages = [
        f"Wow everyone look at how cute {user.mention} is!",
        f"Hello {user.mention}, a certain user would like to let you know you're a cutie",
        f"Hello there {user.mention}, are you aware that you're currently being **too cute** !?",
        f"Hey {user.mention}, just wanted to let you know that {interaction.user.mention} thinks you're cute (they're correct ofcourse)",
        f"Such a cutieful day with you around, {user.mention}"
    ]

    # Get the channel to send the message
    channel = client.get_channel(interaction.channel_id)

    # Select random choice if no "option" was given (optional parameter)
    if option is None:
        choice = random.choice(messages)
    else:
        choice = messages[option]

    # Post message in channel
    await channel.send(choice)


# Sends a hug to the selected user or the person that called the command
@tree.command(name="hug", description="Hugs either a given person or the user")
async def hug(interaction: discord.Interaction, user:typing.Optional[discord.Member], anonymous:typing.Optional[bool] = False):
    guild = interaction.guild

    logs.info(f"hug - {interaction.user.name} | Trying to get emoji 'MochaHug'")
    emoji = discord.utils.get(guild.emojis, name="MochaHug")

    if not emoji:
        logs.info(f"hug - {interaction.user.name} | 'MochaHug' not found - setting default emoji")
        emoji = "🫂"    # People hugging

    # Send the message anonymously if True and a user is selected
    if anonymous and user:
        await interaction.response.send_message("I will send them hugs for you", ephemeral=True)

        channel = client.get_channel(interaction.channel_id)
        await channel.send(f"{user.mention} Sending many hugs {emoji}")
        return
    # Sends it normally if only a user is selected
    if user:
        logs.info(f"hug - {interaction.user.name} | Sending hugs too {user.name}")
        await interaction.response.send_message(f"{user.mention} Sending many hugs {emoji}")
    else:
        logs.info(f"hug - {interaction.user.name} | Sending hugs to self")
        await interaction.response.send_message(f"{emoji}")



"""
    COLOR COMMANDS & HANDLER
"""

# Gets the color of given user, or the person that made the command if blank
@tree.command(name="get_colors", description="Shows you the current colors of the given user or yourself if blank")
async def get_colors(interaction: discord.Interaction, user:typing.Optional[discord.Member]=None):

    if user is None:
        # No user given, getting colors from self
        usern = interaction.user.name
        user = interaction.user
    else:
        # User was given, usern for easy access to name
        usern = user.name

    success, r, g, b, h = await color_getter(interaction=interaction, user=user)

    if success:
        await interaction.response.send_message(f"Color values of {usern}...\nR: {r}\nG: {g}\nB: {b}\nHEX: {h}")
    else:
        await interaction.response.send_message("Please make sure you or the given user already has the generated color role before running this command", ephemeral=True)


@tree.command(name="steal_colors", description="Steals the colors from the given user")
async def steal_colors(interaction: discord.Interaction, user:discord.Member):

    success, r, g, b, h = await color_getter(interaction, user)

    if success:
        await interaction.response.defer(ephemeral=False)

        await color_role_handler(interaction, r, g, b)

        await interaction.followup.send(f"Color stolen from {user.name}")
    else:
        await interaction.response.send_message("Please make sure the given user already has the generated color role before running this command", ephemeral=True)

async def color_getter(interaction: discord.Interaction, user:discord.Member):
    
    usern = user.name
    
    # What the role's name is supposed to be
    role_name = f"{usern}-color"
    role = None

    for role_ in user.roles:
        if role_.name == role_name:
            # Role found
            role = role_
            break

    if role is None:
        # Role doesnt exist, exit out with False
        logs.info(f"grab_colors - {usern} - Role not found")

        # Error, role doesnt exists return False and "None's" for the rgbh values
        return False, None, None, None, None
    
    logs.info(f"grab_colors - {usern} - Got colors: {role.color.value} | r: {role.color.r} | g: {role.color.g} | b: {role.color.b} | HEX: {hex(role.color.value)}")

    r = role.color.r
    g = role.color.g
    b = role.color.b
    h = hex(role.color.value)

    return True, r, g, b, h

# color role using r,g,b values
@tree.command(name="my_color", description="Makes a color role for the user using the given rgb values")
async def my_color(interaction: discord.Interaction, 
    # Int-type value, between 0 and 255
    r: app_commands.Range[int, 0, 255], g: app_commands.Range[int, 0, 255], b: app_commands.Range[int, 0, 255]):

    # Defer incase the handler takes longer then 3 seconds
    await interaction.response.defer(ephemeral=True)

    # Call my_color using converted r, g, b values
    await color_role_handler(interaction, r=r, g=g, b=b)

    # Finally, send message when done
    await interaction.followup.send(f"Role updated...")

# color role using hex value
@tree.command(name="my_colorh", description="Makes a color role for the user using the given HEX values")
async def my_colorh(interaction: discord.Interaction, hex_code:str):
    try:
        if len(hex_code) == 6:
            # Split hex code into rgb values
            r,g,b = hex_code[0:2], hex_code[2:4], hex_code[4:6]

            # Convert str to int
            r = int(r, 16)
            g = int(g, 16)
            b = int(b, 16)

            logs.info(f"Converted HEX: {hex_code} to rgb : [ r: {r}, g: {g}, b: {b} ]")

            # Defer incase the handler takes longer then 3 seconds
            await interaction.response.defer(ephemeral=True)

            # Call my_color using converted r, g, b values
            await color_role_handler(interaction, r=r, g=g, b=b)

            # Finally, send message when done
            await interaction.followup.send(f"Role updated...")
        else:
            raise ValueError
    except ValueError:
        logs.info(f"Value error - params - Hex code: {hex_code}")
        await interaction.response.send_message(f"Value error - '{hex_code}' is not a valid hex code/color")

# Handles the color role commands logic
async def color_role_handler(interaction: discord.Interaction, r, g, b):
    
    # setup username and role_name for shorter variables
    logs.info(f"color_role_handler - {interaction.user.name} - Values: [ R: {r} | G: {g} | B: {b} ]")
    uname = interaction.user.name
    role_name = f"{uname}-color"

    # Convert to color obj
    color = discord.Color.from_rgb(r, g, b)

    # Get guild
    guild = interaction.guild

    # Get top bot role
    logs.info(f"color_role_handler - {uname} - Getting bot's highest role position")
    bot_role = guild.get_member(client.user.id).top_role
    logs.info(f"color_role_handler - {uname} - got role: '{bot_role}' position: {bot_role.position}")
    max_position = bot_role.position - 1

    # Get user roles, see if "role_name" is in it
    role = None
    user_roles = interaction.user.roles
    logs.info(f"color_role_handler - {uname} - Roles [ {user_roles} ]")

    for rol in user_roles:
        if role_name == rol.name:
            role = rol
            break

    # Role is still None, doesnt seem to exist
    if role is None:
        # Make new role
        logs.info(f"color_role_handler - {uname} - Making new role")
        role = await guild.create_role(
            name=role_name,
            colour=color
        )
        await interaction.user.add_roles(role)
    
    # Pushes the role.edit also required to fix the position if it's a new role
    logs.info(f"color_role_handler - {uname} - Pushing new/existing role position")
    await role.edit(
        name=role_name,
        colour=color,
        position=max_position
    )

    logs.info(f"color_role_handler - {uname} - Role updated")
    return

# Run client
client.run(bot_secret)