import os
import json
import discord
import requests
from discord.ext import commands
from discord import app_commands
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

# Slash Command: Ping
@bot.tree.command(name="ping", description="Check bot latency.")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    branding = get_branding(interaction.guild.id)
    
    embed = discord.Embed(
        title="🏓 Bot Latency",
        description=f"📡 **Ping:** `{latency}ms`",
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"🚀 Powered by {branding}")
    await interaction.response.send_message(embed=embed, ephemeral=True)

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
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Slash Command: Help Menu
@bot.tree.command(name="help", description="View all available bot commands.")
async def help_command(interaction: discord.Interaction):
    branding = get_branding(interaction.guild.id)
    embed = discord.Embed(
        title=f"🆘 {branding} - Help Menu",
        description="Here are all available bot commands and their functions:",
        color=discord.Color.blue()
    )
    embed.add_field(name="🏓 `/ping`", value="Check bot latency.", inline=False)
    embed.add_field(name="🔄 `/sendresetembed <message>`", value="Send a reset embed for users.", inline=False)
    embed.add_field(name="🔑 `/setsellerkey <key>`", value="Set the KeyAuth seller key for this server (Admin Only).", inline=False)
    embed.add_field(name="🌐 `/setwebhook <url>`", value="Set the webhook URL for logs (Admin Only).", inline=False)
    embed.add_field(name="📡 `/apistatus`", value="Check if KeyAuth API is online.", inline=False)
    embed.add_field(name="🔍 `/testlicense <license>`", value="Check if a license key is valid **without resetting**.", inline=False)
    embed.add_field(name="🚀 `/setbranding <name>`", value="Change bot branding for the server (Admin Only).", inline=False)
    embed.set_footer(text=f"🚀 Powered by {branding}")
    await interaction.response.send_message(embed=embed, ephemeral=True)

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

    await interaction.channel.send(embed=embed)

bot.run(BOT_TOKEN)
