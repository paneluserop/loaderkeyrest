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

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Database File for Storing Seller Keys & Webhooks
DATA_FILE = "data.json"

# Load existing seller keys & webhooks from database file
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

# Save seller keys & webhooks to the database file
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
    await bot.change_presence(activity=discord.Game(name="Managing RAPIDFIRE CORPORATION 🔥"))

# Admin-only check function
def is_admin():
    async def predicate(interaction: discord.Interaction):
        return interaction.user.guild_permissions.administrator
    return app_commands.check(predicate)

# Slash Command to Check Bot Ping
@bot.tree.command(name="ping", description="Check bot latency.")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 Bot Latency",
        description=f"📡 **Ping:** `{latency}ms`",
        color=discord.Color.blue()
    )
    embed.set_footer(text="🚀 Powered by RAPIDFIRE CORPORATION")
    await interaction.response.send_message(embed=embed)

# Slash Command to Set Seller Key (Admin Only)
@bot.tree.command(name="setsellerkey", description="Set the KeyAuth seller key for this server.")
@is_admin()
async def setsellerkey(interaction: discord.Interaction, key: str):
    data[str(interaction.guild.id)] = data.get(str(interaction.guild.id), {})
    data[str(interaction.guild.id)]["seller_key"] = key
    save_data()

    embed = discord.Embed(
        title="🔑 Seller Key Updated",
        description="✅ **Seller Key has been successfully set for this server!**",
        color=discord.Color.green()
    )
    embed.set_footer(text="🚀 Powered by RAPIDFIRE CORPORATION")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Slash Command to Set Webhook (Admin Only)
@bot.tree.command(name="setwebhook", description="Set the webhook URL for logging resets.")
@is_admin()
async def setwebhook(interaction: discord.Interaction, url: str):
    data[str(interaction.guild.id)] = data.get(str(interaction.guild.id), {})
    data[str(interaction.guild.id)]["webhook_url"] = url
    save_data()

    embed = discord.Embed(
        title="🌐 Webhook Set",
        description="✅ **Webhook has been successfully set for logging resets!**",
        color=discord.Color.green()
    )
    embed.set_footer(text="🚀 Powered by RAPIDFIRE CORPORATION")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Slash Command to Send Reset Embed (Anonymous & Lifetime)
@bot.tree.command(name="sendresetembed", description="Send an embed for users to reset their license keys.")
@is_admin()
async def sendresetembed(interaction: discord.Interaction, message: str):
    guild_id = str(interaction.guild.id)
    if guild_id not in data or "seller_key" not in data[guild_id]:
        await interaction.response.send_message("⚠️ Seller Key not set! Use `/setsellerkey` first.", ephemeral=True)
        return

    embed = discord.Embed(
        title="🔄 License Key Reset - RAPIDFIRE CORPORATION",
        description=f"{message}\n\nClick the button below to reset your KeyAuth license key.\n\n**@everyone**",
        color=discord.Color.blue()
    )
    embed.set_footer(text="© 2025 RAPIDFIRE CORPORATION - License Reset System")

    view = ResetButton()

    # Delete the original command message and send a new embed in the channel
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

        if guild_id not in data or "seller_key" not in data[guild_id]:
            embed = discord.Embed(
                title="⚠️ Error",
                description="⚠️ **Seller Key is not set! Use `/setsellerkey` first.**",
                color=discord.Color.red()
            )
            embed.set_footer(text="🚀 Powered by RAPIDFIRE CORPORATION")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        seller_key = data[guild_id]["seller_key"]
        api_url = f"https://keyauth.win/api/seller/?sellerkey={seller_key}&type=resetuser&user={license_key}"

        response = requests.get(api_url, timeout=10)
        api_data = response.json()

        embed_color = discord.Color.green() if api_data.get("success", False) else discord.Color.red()
        result_message = "✅ **License successfully reset!**" if api_data.get("success", False) else f"❌ **License reset failed!**\n**Reason:** {api_data.get('message', 'Unknown Error')}"

        embed = discord.Embed(title="🔄 License Reset Result", description=result_message, color=embed_color)
        embed.set_footer(text="🚀 Powered by RAPIDFIRE CORPORATION")
        await interaction.response.send_message(embed=embed, ephemeral=True)

bot.run(BOT_TOKEN)
