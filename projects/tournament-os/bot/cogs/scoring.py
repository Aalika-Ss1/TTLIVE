import disnake
from disnake.ext import commands
import aiohttp
import os
import re
from utils import get_localized_error

API_BASE_URL = os.getenv("TOURNAMENT_API_URL", "http://127.0.0.1:8011")
DEFAULT_TOURNAMENT_ID = os.getenv("TOURNAMENT_ID", "demo_tournament_1")

class ScoringCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        # Ignore bots
        if message.author.bot:
            return

        # Check if message is in the submit-scores channel
        if getattr(message.channel, "name", "") == "📸-ส่งผลการแข่ง":
            # Check if it contains an image attachment
            if message.attachments:
                attachments = [att for att in message.attachments if att.content_type and att.content_type.startswith("image/")]
                if not attachments:
                    return

                evidence = attachments[0]
                discord_user_id = str(message.author.id)
                content = message.content or ""

                # 1. Parse round from message (e.g. "รอบ 2" or "Round 2"), defaulting to "Round 1"
                round_name = "Round 1"
                match_round = re.search(r'(?:round|รอบ|รป|ร)\s*([1-4])', content.lower())
                if match_round:
                    round_name = f"Round {match_round.group(1)}"

                # 2. Parse placement from message (e.g. "ได้ที่ 2" or "ที่ 4"), defaulting to 1
                placement = 1
                match_place = re.search(r'(?:ที่|place|rank)?\s*([1-8])', content.lower())
                if match_place:
                    placement = int(match_place.group(1))

                # Let the user know the bot is processing the upload
                reply = await message.reply("⏳ **กำลังอัปโหลดและประมวลผลรูปภาพผลการแข่งด้วยระบบ OCR...**")

                payload = {
                    "tournament_id": DEFAULT_TOURNAMENT_ID,
                    "discord_user_id": discord_user_id,
                    "round_name": round_name,
                    "placement": placement,
                    "kills": 0,
                    "evidence_uri": evidence.url
                }

                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(f"{API_BASE_URL}/discord/scores/submit", json=payload) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                score_id = data.get("score_id")

                                # Download the image from Discord
                                async with session.get(evidence.url) as img_resp:
                                    if img_resp.status == 200:
                                        img_data = await img_resp.read()

                                        # Upload image to backend to run OCR
                                        form_data = aiohttp.FormData()
                                        form_data.add_field(
                                            "file",
                                            img_data,
                                            filename=evidence.filename or "evidence.png",
                                            content_type=evidence.content_type
                                        )

                                        admin_token = os.getenv("TOURNAMENT_OS_ADMIN_TOKEN", "demotoken123")
                                        headers = {"x-admin-token": admin_token}
                                        async with session.post(
                                            f"{API_BASE_URL}/admin/scores/{score_id}/evidence",
                                            data=form_data,
                                            headers=headers
                                        ) as ocr_resp:
                                            if ocr_resp.status != 200:
                                                print(f"Failed to submit evidence file for OCR: {ocr_resp.status}")

                                embed = disnake.Embed(title="📸 อัปโหลดผลการแข่งสำเร็จ!", color=0x2ECC71)
                                embed.description = (
                                    f"**ผู้เล่น:** {message.author.mention}\n"
                                    f"**รอบ:** {round_name}\n"
                                    f"**อันดับที่รายงาน:** {placement}\n\n"
                                    "ระบบส่งผลและแนบรูปภาพเข้าสู่คิวตรวจสอบของกรรมการ (Verification Queue) เรียบร้อยแล้วครับ"
                                )
                                embed.set_image(url=evidence.url)
                                embed.set_footer(text="ระบบจำลองการประมวลผล OCR และส่งข้อมูลไปยังผู้ตัดสินแล้ว")
                                await reply.edit(content=None, embed=embed)
                            else:
                                data = await resp.json()
                                err_msg = get_localized_error(data)
                                await reply.edit(content=f"❌ **ไม่สามารถส่งผลการแข่งได้:** {err_msg}")
                except Exception as e:
                    print(f"Error processing message score upload: {e}")
                    await reply.edit(content="⚠️ เกิดข้อผิดพลาดในการเชื่อมต่อกับระบบหลังบ้าน")

def setup(bot):
    bot.add_cog(ScoringCog(bot))
