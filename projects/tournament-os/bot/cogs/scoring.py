import disnake
from disnake.ext import commands

class ScoringCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        # Ignore bots
        if message.author.bot:
            return

        # Check if message is in the submit-scores channel
        # We match by name for simplicity in this MVP
        if getattr(message.channel, "name", "") == "📸-ส่งผลการแข่ง":
            # Check if it contains an image attachment
            if message.attachments:
                has_image = any(att.content_type and att.content_type.startswith("image/") for att in message.attachments)
                if has_image:
                    # In Phase 7 MVP, we just acknowledge receipt
                    # Later: we would send this to the OCR plugin and FastAPI Verification Queue
                    reply = await message.reply("📸 **Screenshot received!**\nYour score has been sent to the Verification Queue. Please wait for an Admin to approve it.")
                    
                    # Delete original message to keep the channel clean (optional, depends on preference)
                    # await message.delete()

def setup(bot):
    bot.add_cog(ScoringCog(bot))
