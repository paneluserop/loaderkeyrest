import os
import json
import discord
import requests
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Database File for Storing Seller Keys, Webhooks, and Branding
DATA_FILE = "data.json"

# Load existing seller keys, webhooks, and branding from database file
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

# Save seller keys, webhooks, and branding to the database file
def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Load data at startup
data = load_data()

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")

    try:
        await bot.tree.sync()
        print("✅ Slash Commands Synced!")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")

    # Set Bot Status
    await bot.change_presence(activity=discord.Game(name="Managing Licensing System 🔥"))

# Function to Get Custom Branding
def get_branding(guild_id):
    return data.get(str(guild_id), {}).get("branding", "Your Brand Here")

# Admin-only check function
def is_admin():
    async def predicate(interaction: discord.Interaction):
        return interaction.user.guild_permissions.administrator
    return app_commands.check(predicate)

# Slash Command: Set Branding
@bot.tree.command(name="setbranding", description="Change the branding for this server.")
@is_admin()
async def setbranding(interaction: discord.Interaction, name: str):
    data[str(interaction.guild.id)] = data.get(str(interaction.guild.id), {})
    data[str(interaction.guild.id)]["branding"] = name
    save_data()

    embed = discord.Embed(
        title="🚀 Branding Updated",
        description=f"✅ **All bot responses will now display:** `{name}`",
        color=discord.Color.orange()
    )
    embed.set_footer(text=f"🚀 Powered by {name}")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Slash Command: Help Menu (Lists all commands)
@bot.tree.command(name="help", description="View all available bot commands.")
async def help_command(interaction: discord.Interaction):
    branding = get_branding(interaction.guild.id)
    embed = discord.Embed(
        title=f"🆘 {branding} - Help Menu",
        description="Here are the available commands:",
        color=discord.Color.blue()
    )
    embed.add_field(name="🔄 `/sendresetembed <message>`", value="Send a reset embed for users to reset their license keys.", inline=False)
    embed.add_field(name="🔑 `/setsellerkey <key>`", value="Set the KeyAuth seller key for this server.", inline=False)
    embed.add_field(name="🌐 `/setwebhook <url>`", value="Set the webhook URL for logging resets.", inline=False)
    embed.add_field(name="📡 `/apistatus`", value="Check if KeyAuth API is online.", inline=False)
    embed.add_field(name="🔍 `/testlicense <license>`", value="Check if a license key is valid without resetting it.", inline=False)
    embed.set_footer(text=f"🚀 Powered by {branding}")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Slash Command: Test License Validity (Without Resetting)
@bot.tree.command(name="testlicense", description="Check if a license key is valid without resetting it.")
async def testlicense(interaction: discord.Interaction, license_key: str):
    guild_id = str(interaction.guild.id)
    if guild_id not in data or "seller_key" not in data[guild_id]:
        await interaction.response.send_message("⚠️ Seller Key not set! Use `/setsellerkey` first.", ephemeral=True)
        return

    seller_key = data[guild_id]["seller_key"]
    api_url = f"https://keyauth.win/api/seller/?sellerkey={seller_key}&type=userdata&user={license_key}"

    response = requests.get(api_url, timeout=10)
    api_data = response.json()

    if api_data.get("success", False):
        status_msg = "✅ **Valid License!**"
        color = discord.Color.green()
    else:
        status_msg = "❌ **Invalid License!**"
        color = discord.Color.red()

    embed = discord.Embed(
        title="🔍 License Check Result",
        description=status_msg,
        color=color
    )
    embed.set_footer(text=f"🚀 Powered by {get_branding(interaction.guild.id)}")
    await interaction.response.send_message(embed=embed)

# Send DM Notification After Reset
async def send_dm(user, license_key, guild_id):
    branding = get_branding(guild_id)
    try:
        embed = discord.Embed(
            title="🔑 License Reset Successful!",
            description=f"✅ **Your license key `{license_key}` has been reset successfully!**",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"🚀 Powered by {branding}")
        await user.send(embed=embed)
    except:
        print(f"❌ Could not send DM to {user}")

# Slash Command to Send Reset Embed (Anonymous & Lifetime)
@bot.tree.command(name="sendresetembed", description="Send an embed for users to reset their license keys.")
@is_admin()
async def sendresetembed(interaction: discord.Interaction, message: str):
    guild_id = str(interaction.guild.id)
    branding = get_branding(guild_id)

    if guild_id not in data or "seller_key" not in data[guild_id]:
        await interaction.response.send_message("⚠️ Seller Key not set! Use `/setsellerkey` first.", ephemeral=True)
        return

    embed = discord.Embed(
        title=f"🔄 License Key Reset - {branding}",
        description=f"{message}\n\nClick the button below to reset your KeyAuth license key.\n\n**@everyone**",
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"© 2025 {branding} - License Reset System")

    view = ResetButton()
    await interaction.response.defer(ephemeral=True)
    channel = interaction.channel
    await channel.send(embed=embed, view=view)

# Button Handling for License Reset
class ResetButton(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="🔑 Reset License", style=discord.ButtonStyle.success, custom_id="reset_license")
    async def reset_license(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = LicenseResetModal(interaction)
        await interaction.response.send_modal(modal)

# Modal Input Box for License Key
class LicenseResetModal(Modal, title="🔑 Enter Your License Key"):
    license_key = TextInput(label="License Key", placeholder="Enter your license key here", required=True)

    def __init__(self, interaction):
        super().__init__()
        self.interaction = interaction

    async def on_submit(self, interaction: discord.Interaction):
        license_key = self.license_key.value.strip()
        guild_id = str(interaction.guild.id)
        await send_dm(interaction.user, license_key, guild_id)  # Send DM Confirmation

bot.run(BOT_TOKEN)
