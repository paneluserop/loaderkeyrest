import os
import discord
import requests
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Dictionary to store seller keys per server
seller_keys = {}

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")

# Command to set seller key (Admin only)
@bot.command()
@commands.has_permissions(administrator=True)
async def setsellerkey(ctx, key: str):
    seller_keys[ctx.guild.id] = key
    await ctx.send(f"✅ Seller key set for this server!")

# Command to send KeyAuth reset embed
@bot.command()
@commands.has_permissions(administrator=True)
async def sendresetembed(ctx, *, message: str):
    if ctx.guild.id not in seller_keys:
        await ctx.send("⚠️ Seller Key not set! Use `!setsellerkey <key>` first.")
        return

    embed = discord.Embed(
        title="🔄 License Key Reset",
        description=f"{message}\n\nClick the button below to reset your KeyAuth license key.\n\n**@everyone**",
        color=discord.Color.blue()
    )
    embed.set_footer(text="© 2025 RAPIDFIRE - All Rights Reserved")

    view = ResetButton()
    await ctx.send(embed=embed, view=view)

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
                await interaction.followup.send("⚠️ Seller Key not set! Use `!setsellerkey <key>` first.", ephemeral=True)
                return

            api_url = f"https://keyauth.win/api/seller/?sellerkey={seller_key}&type=resetuser&user={license_key}"
            response = requests.get(api_url)

            if response.status_code == 200 and response.json().get("success"):
                await interaction.followup.send(f"✅ License **{license_key}** has been reset!", ephemeral=True)
            else:
                await interaction.followup.send("❌ Failed to reset the key. Check your input.", ephemeral=True)
            
            await msg.delete()

        except Exception as e:
            await interaction.followup.send("⏳ Timeout! Try again.", ephemeral=True)

bot.run(BOT_TOKEN)
