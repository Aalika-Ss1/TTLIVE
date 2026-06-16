import os
import sys
import disnake
from disnake.ext import commands

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables (In production, use python-dotenv)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_BOT_TOKEN_HERE")
API_BASE_URL = os.getenv("TOURNAMENT_API_URL", "http://127.0.0.1:8011")

# Configure Intents
intents = disnake.Intents.default()
intents.message_content = False  # Keep False to avoid PrivilegedIntents error
intents.members = True           # Enabled for Discord Role Sync (Phase 3)

bot = commands.InteractionBot(intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")
    print(f"API Backend URL: {API_BASE_URL}")

@bot.event
async def on_slash_command_error(inter: disnake.ApplicationCommandInteraction, error: Exception):
    if isinstance(error, commands.MissingAnyRole) or isinstance(error, commands.MissingRole):
        await inter.response.send_message("❌ **ขออภัยครับ คุณไม่มียศ (Role) ที่สามารถใช้งานคำสั่งนี้ได้!**", ephemeral=True)
    elif isinstance(error, commands.MissingPermissions):
        await inter.response.send_message("❌ **ขออภัยครับ คุณไม่มีสิทธิ์ (Permissions) ใช้งานคำสั่งนี้!**", ephemeral=True)
    else:
        # For other errors, just send a generic error to avoid 'App did not respond'
        print(f"Unhandled Slash Command Error: {error}")
        if not inter.response.is_done():
            await inter.response.send_message(f"⚠️ **เกิดข้อผิดพลาด:** `{error}`", ephemeral=True)
        else:
            await inter.edit_original_response(content=f"⚠️ **เกิดข้อผิดพลาด:** `{error}`")

if __name__ == "__main__":
    # Load cogs
    bot.load_extension("cogs.player")
    bot.load_extension("cogs.scoring")
    bot.load_extension("cogs.admin")
    bot.load_extension("cogs.welcome")
    
    # Start bot
    if DISCORD_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("WARNING: DISCORD_TOKEN not set. Bot will not start.")
    else:
        bot.run(DISCORD_TOKEN)
