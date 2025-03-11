import os
import discord
import requests
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Dictionary to store seller keys and webhook URLs per server
seller_keys = {}
webhook_urls = {}

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")

    try:
        await bot.tree.sync()
        print("✅ Slash Commands Synced!")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")

    # Set Bot Status
    await bot.change_presence(activity=discord.Game(name="Managing Rapid Loader 🔥"))

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
        title="🏓 Bot Ping",
        description=f"📡 Bot latency: `{latency}ms`",
        color=discord.Color.blue()
    )
    embed.set_footer(text="🚀 Powered by RAPIDFIRE CORP")
    await interaction.response.send_message(embed=embed)

# Slash Command to Set Seller Key (Admin Only)
@bot.tree.command(name="setsellerkey", description="Set the KeyAuth seller key for this server.")
@is_admin()
async def setsellerkey(interaction: discord.Interaction, key: str):
    seller_keys[interaction.guild.id] = key
    embed = discord.Embed(
        title="🔑 Seller Key Updated",
        description="✅ **Seller Key has been successfully set for this server!**",
        color=discord.Color.green()
    )
    embed.set_footer(text="🚀 Powered by RAPIDFIRE CORP")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Slash Command to Set Webhook (Admin Only)
@bot.tree.command(name="setwebhook", description="Set the webhook URL for logging resets.")
@is_admin()
async def setwebhook(interaction: discord.Interaction, url: str):
    webhook_urls[interaction.guild.id] = url
    embed = discord.Embed(
        title="🌐 Webhook Set",
        description="✅ **Webhook has been successfully set for logging resets!**",
        color=discord.Color.green()
    )
    embed.set_footer(text="🚀 Powered by RAPIDFIRE CORP")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Slash Command to Send Reset Embed (Admin Only)
@bot.tree.command(name="sendresetembed", description="Send an embed for users to reset their license keys.")
@is_admin()
async def sendresetembed(interaction: discord.Interaction, message: str):
    if interaction.guild.id not in seller_keys:
        await interaction.response.send_message("⚠️ Seller Key not set! Use `/setsellerkey` first.", ephemeral=True)
        return

    embed = discord.Embed(
        title="🔄 License Key Reset - RAPIDFIRE CORP",
        description=f"{message}\n\nClick the button below to reset your KeyAuth license key.\n\n**@everyone**",
        color=discord.Color.blue()
    )
    embed.set_footer(text="© 2025 RAPIDFIRE CORP - License Reset System")

    view = ResetButton()
    await interaction.response.send_message("@everyone", embed=embed, view=view)

# Modal Input Box for License Key
class LicenseResetModal(Modal, title="🔑 Enter Your License Key"):
    license_key = TextInput(label="License Key", placeholder="Enter your license key here", required=True)

    def __init__(self, interaction):
        super().__init__()
        self.interaction = interaction

    async def on_submit(self, interaction: discord.Interaction):
        license_key = self.license_key.value.strip()
        seller_key = seller_keys.get(interaction.guild.id)

        if not seller_key:
            embed = discord.Embed(
                title="⚠️ Error",
                description="⚠️ **Seller Key is not set! Use `/setsellerkey` first.**",
                color=discord.Color.red()
            )
            embed.set_footer(text="🚀 Powered by RAPIDFIRE CORP")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Send request to KeyAuth API
        api_url = f"https://keyauth.win/api/seller/?sellerkey={seller_key}&type=resetuser&user={license_key}"
        try:
            response = requests.get(api_url, timeout=10)
            api_data = response.json()

            if response.status_code == 200 and api_data.get("success", False):
                result_message = "✅ **License successfully reset!**"
                embed_color = discord.Color.green()
            else:
                result_message = f"❌ **License reset failed!**\n**Reason:** {api_data.get('message', 'Unknown Error')}"
                embed_color = discord.Color.red()

        except requests.RequestException:
            result_message = "⚠️ **Error contacting KeyAuth API. Please try again later.**"
            embed_color = discord.Color.orange()

        embed = discord.Embed(
            title="🔄 License Reset Result",
            description=result_message,
            color=embed_color
        )
        embed.set_footer(text="🚀 Powered by RAPIDFIRE CORP")
        await interaction.response.send_message(embed=embed, ephemeral=True)

        # Log reset to webhook (if set)
        webhook_url = webhook_urls.get(interaction.guild.id)
        if webhook_url:
            log_embed = discord.Embed(
                title="🔄 KeyAuth License Reset Logged",
                color=embed_color
            )
            log_embed.add_field(name="🔑 License Key:", value=f"||{license_key}||", inline=False)
            log_embed.add_field(name="👤 User:", value=f"{interaction.user.mention} (`{interaction.user}`)", inline=False)
            log_embed.add_field(name="⏳ Timestamp:", value=f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}", inline=False)
            log_embed.set_footer(text="🚀 Powered by RAPIDFIRE CORP")
            requests.post(webhook_url, json={"embeds": [log_embed.to_dict()]})

# Button Handling for License Reset
class ResetButton(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="🔑 Reset License", style=discord.ButtonStyle.success, custom_id="reset_license")
    async def reset_license(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = LicenseResetModal(interaction)
        await interaction.response.send_modal(modal)

bot.run(BOT_TOKEN)
