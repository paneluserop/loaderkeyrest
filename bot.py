import os
import json
import discord
import requests
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View, Modal, InputText
from dotenv import load_dotenv

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

# Function to reset the license key
async def reset_license(interaction: discord.Interaction, license_key: str):
    guild_id = str(interaction.guild.id)
    seller_key = data[guild_id]["seller_key"]
    api_url = f"https://keyauth.win/api/seller/?sellerkey={seller_key}&type=reset&user={license_key}"

    try:
        response = requests.get(api_url, timeout=10)
        api_data = response.json()

        if api_data.get("success", False):
            await interaction.user.send(f"✅ Your license key `{license_key}` has been reset successfully!")
            # Log to webhook if set
            webhook_url = data[guild_id].get("webhook_url")
            if webhook_url:
                requests.post(webhook_url, json={"content": f"License key `{license_key}` has been reset by {interaction.user.name}."})
        else:
            await interaction.user.send(f"❌ Failed to reset your license key `{license_key}`. Please check the key and try again.")
    except Exception as e:
        await interaction.user.send(f"❌ An error occurred while resetting the license: {str(e)}")

# Modal for License Key Input
class LicenseKeyModal(Modal):
    def __init__(self):
        super().__init__(title="Enter License Key")
        self.add_item(InputText(label="License Key", placeholder="Enter your license key here"))

    async def callback(self, interaction: discord.Interaction):
        license_key = self.children[0].value
        await reset_license(interaction, license_key)

# Slash Command: Send Reset Embed
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

    button = Button(label="Reset License Key", style=discord.ButtonStyle.primary)

    async def button_callback(interaction: discord.Interaction):
        modal = LicenseKeyModal()
        await interaction.response.send_modal(modal)

    button.callback = button_callback
    view = View()
    view.add_item(button)

    await interaction.channel.send(embed=embed, view=view)

# Slash Command: Set Seller Key
@bot.tree.command(name="setsellerkey", description="Set the KeyAuth seller key for this server.")
@is_admin()
async def setsellerkey(interaction: discord.Interaction, key: str):
    data[str(interaction.guild.id)] = data.get(str(interaction.guild.id), {})
    data[str(interaction.guild.id)]["seller_key"] = key
    save_data()

    embed = discord.Embed(
        title="🔑 Seller Key Updated",
        description="✅ **Your server's seller key has been set successfully!**",
        color=discord.Color.green()
    )
    embed.set_footer(text=f"🚀 Powered by {get_branding(interaction.guild.id)}")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Slash Command: Set Webhook
@bot.tree.command(name="setwebhook", description="Set the webhook URL for logging resets.")
@is_admin()
async def setwebhook(interaction: discord.Interaction, url: str):
    data[str(interaction.guild.id)] = data.get(str(interaction.guild.id), {})
    data[str(interaction.guild.id)]["webhook_url"] = url
    save_data()

    embed = discord.Embed(
        title="🌐 Webhook Set",
        description="✅ **Your webhook for logging resets has been updated!**",
        color=discord.Color.green()
    )
    embed.set_footer(text=f"🚀 Powered by {get_branding(interaction.guild.id)}")
    await interaction.response.send_message(embed=embed, ephemeral=True)

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

# Slash Command: Test License
@bot.tree.command(name="testlicense", description="Check if a license key is valid without resetting it.")
async def testlicense(interaction: discord.Interaction, license_key: str):
    guild_id = str(interaction.guild.id)
    if guild_id not in data or "seller_key" not in data[guild_id]:
        await interaction.response.send_message("⚠️ Seller Key not set! Use `/setsellerkey` first.", ephemeral=True)
        return

    seller_key = data[guild_id]["seller_key"]
    api_url = f"https://keyauth.win/api/seller/?sellerkey={seller_key}&type=userdata&user={license_key}"

    try:
        response = requests.get(api_url, timeout=10)
        api_data = response.json()

        if api_data.get("success", False):
            status_msg = "✅ **Valid License!**"
            color = discord.Color.green()
        else:
            status_msg = "❌ **Invalid License!**"
            color = discord.Color.red()
    except Exception as e:
        status_msg = f"❌ An error occurred: {str(e)}"
        color = discord.Color.red()

    embed = discord.Embed(
        title="🔍 License Check Result",
        description=status_msg,
        color=color
    )
    embed.set_footer(text=f"🚀 Powered by {get_branding(interaction.guild.id)}")
    await interaction.response.send_message(embed=embed)

# Slash Command: API Status
@bot.tree.command(name="apistatus", description="Check if KeyAuth API is online.")
async def apistatus(interaction: discord.Interaction):
    api_url = "https://keyauth.win/api/seller/"
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            status_msg = "✅ **KeyAuth API is Online!**"
            color = discord.Color.green()
        else:
            status_msg = "⚠️ **KeyAuth API is having issues!**"
            color = discord.Color.orange()
    except requests.RequestException:
        status_msg = "❌ **KeyAuth API is Down!**"
        color = discord.Color.red()

    embed = discord.Embed(
        title="📡 KeyAuth API Status",
        description=status_msg,
        color=color
    )
    embed.set_footer(text=f"🚀 Powered by {get_branding(interaction.guild.id)}")
    await interaction.response.send_message(embed=embed)

# Slash Command: Ping
@bot.tree.command(name="ping", description="Check bot latency.")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    branding = get_branding(interaction.guild.id)
    
    embed = discord.Embed(
        title="🏓 Bot Latency",
        description=f"📡 **Current Ping:** `{latency}ms`",
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"🚀 Powered by {branding}")
    await interaction.response.send_message(embed=embed)

# Slash Command: Help
@bot.tree.command(name="help", description="View all available bot commands.")
async def help_command(interaction: discord.Interaction):
    branding = get_branding(interaction.guild.id)
    embed = discord.Embed(
        title=f"🆘 {branding} - Help Menu",
        description="Here are all available bot commands and their functions:",
        color=discord.Color.blue()
    )
    embed.add_field(name="🏓 `/ping`", value="Check bot latency.", inline=False)
    embed.add_field(name="🔑 `/setsellerkey <key>`", value="Set the KeyAuth seller key for this server (Admin Only).", inline=False)
    embed.add_field(name="🌐 `/setwebhook <url>`", value="Set the webhook URL for logs (Admin Only).", inline=False)
    embed.add_field(name="🚀 `/setbranding <name>`", value="Change bot branding for the server (Admin Only).", inline=False)
    embed.add_field(name="📡 `/apistatus`", value="Check if KeyAuth API is online.", inline=False)
    embed.add_field(name="🔍 `/testlicense <license>`", value="Check if a license key is valid **without resetting**.", inline=False)
    embed.add_field(name="🔄 `/sendresetembed <message>`", value="Send a reset embed for users (Admin Only).", inline=False)
    embed.set_footer(text=f"🚀 Powered by {branding}")
    await interaction.response.send_message(embed=embed)

bot.run(BOT_TOKEN)
