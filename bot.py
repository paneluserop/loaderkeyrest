import os
import discord
import requests
from discord.ext import commands
from discord import app_commands
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
    await bot.change_presence(activity=discord.Game(name="Managing Rapid Loader"))

# Admin-only check function
def is_admin():
    async def predicate(interaction: discord.Interaction):
        return interaction.user.guild_permissions.administrator
    return app_commands.check(predicate)

# Slash Command to Check Bot Ping
@bot.tree.command(name="ping", description="Check bot latency.")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! Bot latency is `{latency}ms`.")

# Slash Command to Set Seller Key (Admin Only)
@bot.tree.command(name="setsellerkey", description="Set the KeyAuth seller key for this server.")
@is_admin()
async def setsellerkey(interaction: discord.Interaction, key: str):
    seller_keys[interaction.guild.id] = key
    await interaction.response.send_message("✅ Seller Key set successfully for this server!", ephemeral=True)

# Slash Command to Set Webhook (Admin Only)
@bot.tree.command(name="setwebhook", description="Set the webhook URL for logging resets.")
@is_admin()
async def setwebhook(interaction: discord.Interaction, url: str):
    webhook_urls[interaction.guild.id] = url
    await interaction.response.send_message("✅ Webhook set successfully for this server!", ephemeral=True)

# Slash Command to Send Reset Embed (Admin Only)
@bot.tree.command(name="sendresetembed", description="Send an embed for users to reset their license keys.")
@is_admin()
async def sendresetembed(interaction: discord.Interaction, message: str):
    if interaction.guild.id not in seller_keys:
        await interaction.response.send_message("⚠️ Seller Key not set! Use `/setsellerkey` first.", ephemeral=True)
        return

    embed = discord.Embed(
        title="🔄 License Key Reset",
        description=f"{message}\n\nClick the button below to reset your KeyAuth license key.\n\n**@everyone**",
        color=discord.Color.blue()
    )
    embed.set_footer(text="© 2025 RAPIDFIRE - All Rights Reserved")

    view = ResetButton()
    await interaction.response.send_message("@everyone", embed=embed, view=view)

# Button Handling for License Reset
class ResetButton(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="Reset License", style=discord.ButtonStyle.success, custom_id="reset_license")
    async def reset_license(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔑 Please enter your license key:", ephemeral=True)

        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel

        try:
            msg = await bot.wait_for("message", check=check, timeout=60)
            license_key = msg.content.strip()

            seller_key = seller_keys.get(interaction.guild.id)
            if not seller_key:
                await interaction.followup.send("⚠️ Seller Key not set! Use `/setsellerkey` first.", ephemeral=True)
                return

            api_url = f"https://keyauth.win/api/seller/?sellerkey={seller_key}&type=resetuser&user={license_key}"
            response = requests.get(api_url)

            if response.status_code == 200 and response.json().get("success"):
                await interaction.followup.send(f"✅ License **{license_key}** has been reset!", ephemeral=True)

                # Log the reset to webhook
                webhook_url = webhook_urls.get(interaction.guild.id)
                if webhook_url:
                    log_embed = discord.Embed(
                        title="🔄 KeyAuth License Reset Logged",
                        color=discord.Color.green()
                    )
                    log_embed.add_field(name="🔑 License Key:", value=f"||{license_key}||", inline=False)
                    log_embed.add_field(name="👤 User:", value=f"{interaction.user.mention} (`{interaction.user}`)", inline=False)
                    log_embed.add_field(name="⏳ Timestamp:", value=f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}", inline=False)
                    log_embed.set_footer(text="© 2025 RAPIDFIRE - Auto Log System")

                    requests.post(webhook_url, json={"embeds": [log_embed.to_dict()]})

            else:
                await interaction.followup.send("❌ Failed to reset the key. Check your input.", ephemeral=True)

            await msg.delete()

        except Exception as e:
            await interaction.followup.send("⏳ Timeout! Try again.", ephemeral=True)

bot.run(BOT_TOKEN)
