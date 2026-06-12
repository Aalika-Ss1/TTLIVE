import disnake
from disnake.ext import commands
import aiohttp
import os

API_BASE_URL = os.getenv("TOURNAMENT_API_URL", "http://127.0.0.1:8011")

TOURNAMENT_ID = "demo_tournament_1"

# Status labels in Thai
STATUS_LABELS = {
    "not_registered": "❌ ยังไม่ได้สมัคร",
    "submitted": "🕐 รอแอดมินตรวจสอบ",
    "approved": "✅ ผ่านการคัดเลือก",
    "waitlisted": "📋 อยู่ในรายสำรอง",
    "rejected": "❌ ไม่ผ่านการคัดเลือก",
    "withdrawn": "🚫 ถอนตัวแล้ว",
}

def build_status_view(allowed_actions: list, check_in_session_id: str = None) -> disnake.ui.View:
    """Build a View with buttons based on allowed_actions from the backend."""
    view = disnake.ui.View(timeout=None)
    
    if "register" in allowed_actions:
        view.add_item(disnake.ui.Button(
            label="📝 สมัครแข่งขัน", style=disnake.ButtonStyle.success,
            custom_id="panel_register", row=0
        ))
    if "check_in" in allowed_actions:
        cid = f"panel_checkin__{check_in_session_id}" if check_in_session_id else "panel_checkin"
        view.add_item(disnake.ui.Button(
            label="✅ เช็คอิน", style=disnake.ButtonStyle.success,
            custom_id=cid, row=0
        ))
    if "view_group" in allowed_actions:
        view.add_item(disnake.ui.Button(
            label="🎮 สายการแข่งของฉัน", style=disnake.ButtonStyle.primary,
            custom_id="panel_group", row=0
        ))
    if "submit_evidence" in allowed_actions:
        view.add_item(disnake.ui.Button(
            label="📸 ส่งภาพผลการแข่ง", style=disnake.ButtonStyle.secondary,
            custom_id="panel_evidence_hint", row=1
        ))
    if "view_status" in allowed_actions:
        view.add_item(disnake.ui.Button(
            label="📊 ดูสถานะ", style=disnake.ButtonStyle.secondary,
            custom_id="panel_status", row=1
        ))

    # Always show leaderboard and dispute
    view.add_item(disnake.ui.Button(
        label="🏆 ตารางคะแนน", style=disnake.ButtonStyle.secondary,
        custom_id="panel_leaderboard", row=1
    ))
    view.add_item(disnake.ui.Button(
        label="🚨 แจ้งปัญหา", style=disnake.ButtonStyle.danger,
        custom_id="panel_dispute", row=2
    ))
    return view


class PlayerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Spawn the Player Control Panel (Admin only)", default_member_permissions=disnake.Permissions(administrator=True))
    async def spawn_player_panel(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        
        embed = disnake.Embed(
            title="🎮 ศูนย์ควบคุมผู้เล่น (Player Control Panel)",
            description="กดปุ่ม **📊 เช็คสถานะ** เพื่อดูปุ่มที่คุณสามารถใช้งานได้ตามสถานะการสมัครของคุณครับ!",
            color=0x2E86C1
        )
        embed.set_footer(text="ปุ่มจะเปลี่ยนตามสถานะของคุณ - ไม่ใช่ทุกคนจะเห็นปุ่มเหมือนกัน")
        
        # Main entry point: just the status check button
        view = disnake.ui.View(timeout=None)
        view.add_item(disnake.ui.Button(
            label="📊 เช็คสถานะของฉัน", style=disnake.ButtonStyle.primary,
            custom_id="panel_status", emoji="🔍"
        ))
        
        await inter.channel.send(embed=embed, view=view)
        await inter.edit_original_response(content="✅ Player Control Panel spawned successfully.")

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        cid = inter.component.custom_id

        # ─── STATUS: Dynamic entry point ───────────────────────────────────
        if cid == "panel_status":
            await inter.response.defer(ephemeral=True)
            discord_user_id = str(inter.author.id)
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{API_BASE_URL}/discord/players/me/status?tournament_id={TOURNAMENT_ID}&discord_user_id={discord_user_id}"
                    async with session.get(url) as resp:
                        if resp.status != 200:
                            await inter.edit_original_response(content="⚠️ ไม่สามารถดึงข้อมูลสถานะได้ครับ")
                            return
                        data = await resp.json()
            except Exception:
                await inter.edit_original_response(content="⚠️ Error connecting to backend.")
                return

            status = data.get("status", "unknown")
            allowed = data.get("allowed_actions", [])
            check_in_session_id = data.get("current_check_in_session_id")
            display_name = data.get("display_name", inter.author.display_name)
            
            label = STATUS_LABELS.get(status, f"สถานะ: {status}")
            
            embed = disnake.Embed(title="📊 สถานะของคุณ", color=0x2E86C1)
            embed.add_field(name="ชื่อในเกม", value=display_name, inline=True)
            embed.add_field(name="สถานะ", value=label, inline=True)
            embed.set_thumbnail(url=inter.author.display_avatar.url if inter.author.display_avatar else None)
            
            # Status-specific messages
            if status == "not_registered":
                embed.description = "คุณยังไม่ได้สมัครแข่งขันครับ กดปุ่มด้านล่างเพื่อสมัครได้เลย!"
            elif status == "submitted":
                embed.description = "ข้อมูลสมัครของคุณถูกส่งแล้วครับ กรุณารอแอดมินตรวจสอบ"
            elif status == "approved":
                embed.description = "ยินดีด้วยครับ! คุณผ่านการคัดเลือกแล้ว"
                if "check_in" in allowed:
                    embed.description += "\n\n⏰ **เช็คอินตอนนี้ได้เลย! กรุณาเช็คอินก่อน Session ปิด**"
            elif status == "waitlisted":
                embed.description = "คุณอยู่ในรายสำรองครับ แอดมินจะแจ้งถ้ามีที่ว่าง"
            elif status == "rejected":
                embed.description = "ขออภัยครับ การสมัครของคุณไม่ผ่าน กรุณาติดต่อแอดมิน"
                
            view = build_status_view(allowed, check_in_session_id)
            await inter.edit_original_response(embed=embed, view=view)
            return

        # ─── REGISTER ──────────────────────────────────────────────────────
        if cid == "panel_register":
            await inter.response.send_modal(
                title="📝 สมัครแข่งขัน (Registration)",
                custom_id="modal_register",
                components=[
                    disnake.ui.TextInput(
                        label="ชื่อในเกม (In-game Name)",
                        placeholder="กรอกชื่อในเกมของคุณ...",
                        custom_id="in_game_name",
                        style=disnake.TextInputStyle.short,
                        required=True
                    ),
                    disnake.ui.TextInput(
                        label="รหัสในเกม (Game ID/UID)",
                        placeholder="กรอก ID ของคุณ (ตัวเลข/ตัวอักษร)...",
                        custom_id="game_id",
                        style=disnake.TextInputStyle.short,
                        required=True
                    ),
                    disnake.ui.TextInput(
                        label="ชื่อทีม (ถ้ามี)",
                        placeholder="เว้นว่างได้ถ้าไม่มีทีม",
                        custom_id="team_name",
                        style=disnake.TextInputStyle.short,
                        required=False
                    )
                ]
            )
            return

        # ─── CHECK-IN ──────────────────────────────────────────────────────
        if cid.startswith("panel_checkin"):
            await inter.response.defer(ephemeral=True)
            discord_user_id = str(inter.author.id)
            # Extract session_id from custom_id: "panel_checkin__<session_id>"
            parts = cid.split("__")
            session_id = parts[1] if len(parts) > 1 else None
            
            if not session_id:
                await inter.edit_original_response(content="❌ ไม่พบเซสชันเช็คอินที่เปิดอยู่ในขณะนี้ครับ")
                return
            
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{API_BASE_URL}/discord/check-in/{session_id}?discord_user_id={discord_user_id}"
                    async with session.post(url) as resp:
                        if resp.status == 200:
                            await inter.edit_original_response(
                                content="✅ **เช็คอินสำเร็จแล้วครับ!** ระบบบันทึกการเช็คอินของคุณเรียบร้อยแล้ว เตรียมตัวแข่งขันได้เลย!"
                            )
                        else:
                            data = await resp.json()
                            message = data.get("detail") or data.get("error", {}).get("message") or "เช็คอินไม่สำเร็จ"
                            await inter.edit_original_response(content=f"❌ {message}")
            except Exception:
                await inter.edit_original_response(content="⚠️ Error connecting to backend.")
            return

        # ─── GROUP ─────────────────────────────────────────────────────────
        elif cid == "panel_group":
            await inter.response.defer(ephemeral=True)
            discord_user_id = str(inter.author.id)
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{API_BASE_URL}/discord/players/me/group?tournament_id={TOURNAMENT_ID}&discord_user_id={discord_user_id}"
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            group = data.get("group", {})
                            participants = group.get("participants", [])
                            participant_names = "\n".join(
                                f"{p.get('seed', '-')}. {p.get('display_name', '-')}" for p in participants
                            )
                            embed = disnake.Embed(title="🎮 สายการแข่งของคุณ", color=0x3498DB)
                            embed.add_field(name="Stage", value=data.get("stage", "ยังไม่กำหนด"), inline=True)
                            embed.add_field(name="กลุ่ม", value=group.get("name", "ยังไม่กำหนด"), inline=True)
                            embed.add_field(
                                name="ผู้เล่นในกลุ่ม",
                                value=participant_names or "ยังไม่มีรายชื่อ",
                                inline=False,
                            )
                            await inter.edit_original_response(embed=embed)
                        else:
                            await inter.edit_original_response(content="❌ ยังไม่มีการกำหนดสายแข่ง กรุณารอแอดมินประกาศครับ")
            except Exception:
                await inter.edit_original_response(content="⚠️ Error connecting to backend.")
            return

        # ─── LEADERBOARD ───────────────────────────────────────────────────
        elif cid == "panel_leaderboard":
            await inter.response.defer(ephemeral=True)
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{API_BASE_URL}/discord/leaderboard?tournament_id={TOURNAMENT_ID}"
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            embed = disnake.Embed(title="🏆 ตารางคะแนน", color=0xFFD700)
                            desc = ""
                            for item in data.get("leaderboard", []):
                                desc += (
                                    f"**#{item['rank']}** {item['display_name']} — "
                                    f"{item['total_points']} pts ({item['games_played']} games)\n"
                                )
                            embed.description = desc if desc else "ยังไม่มีคะแนนในขณะนี้ครับ"
                            await inter.edit_original_response(embed=embed)
                        else:
                            await inter.edit_original_response(content="❌ ดึงข้อมูลตารางคะแนนไม่สำเร็จ")
            except Exception:
                await inter.edit_original_response(content="⚠️ Error connecting to backend.")
            return

        # ─── EVIDENCE HINT ─────────────────────────────────────────────────
        elif cid == "panel_evidence_hint":
            await inter.response.send_message(
                "📸 **วิธีส่งภาพผลการแข่ง:**\nพิมพ์คำสั่ง `/submit_evidence` แล้วเลือกรอบและแนบรูปภาพ Screenshot ได้เลยครับ!",
                ephemeral=True
            )
            return

        # ─── DISPUTE ───────────────────────────────────────────────────────
        elif cid == "panel_dispute":
            await inter.response.send_modal(
                title="🚨 แจ้งปัญหา (Dispute)",
                custom_id="modal_dispute",
                components=[
                    disnake.ui.TextInput(
                        label="รายละเอียดปัญหา",
                        placeholder="พิมพ์ปัญหาที่คุณพบที่นี่...",
                        custom_id="dispute_reason",
                        style=disnake.TextInputStyle.paragraph,
                        max_length=500,
                        required=True
                    )
                ]
            )
            return

    @commands.Cog.listener()
    async def on_modal_submit(self, inter: disnake.ModalInteraction):
        if inter.custom_id == "modal_dispute":
            reason = inter.text_values["dispute_reason"]
            await inter.response.send_message(
                f"🚨 **แจ้งปัญหาสำเร็จ!**\nรายละเอียด: `{reason}`\nแอดมินได้รับแจ้งปัญหาแล้ว กรุณารอการติดต่อกลับครับ",
                ephemeral=True
            )
            return
            
        elif inter.custom_id == "modal_register":
            await inter.response.defer(ephemeral=True)
            payload = {
                "tournament_id": TOURNAMENT_ID,
                "discord_user_id": str(inter.author.id),
                "discord_name": inter.author.display_name,
                "in_game_name": inter.text_values["in_game_name"],
                "game_id": inter.text_values["game_id"],
                "team_name": inter.text_values.get("team_name", "")
            }
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(f"{API_BASE_URL}/discord/register", json=payload) as resp:
                        if resp.status == 200:
                            embed = disnake.Embed(title="✅ สมัครสำเร็จ!", color=0x2ECC71)
                            embed.description = f"**ชื่อในเกม:** {payload['in_game_name']}\n**Game ID:** {payload['game_id']}\n\nกรุณารอแอดมินตรวจสอบและยืนยันครับ 🙏"
                            await inter.edit_original_response(embed=embed)
                        else:
                            data = await resp.json()
                            message = data.get("detail") or data.get("error", {}).get("message") or "Unknown error"
                            await inter.edit_original_response(content=f"❌ **สมัครไม่สำเร็จ:** {message}")
            except Exception:
                await inter.edit_original_response(content="⚠️ Error connecting to backend.")

    @commands.slash_command(description="Submit match screenshot as evidence for referees")
    async def submit_evidence(
        self, 
        inter: disnake.ApplicationCommandInteraction, 
        round_name: str = commands.Param(choices=["Round 1", "Round 2", "Round 3", "Round 4", "Finals"]),
        evidence: disnake.Attachment = commands.Param(description="อัปโหลดรูปภาพ Screenshot ผลการแข่ง")
    ):
        await inter.response.defer(ephemeral=True)
        
        if not evidence.content_type or not evidence.content_type.startswith("image/"):
            await inter.edit_original_response(content="❌ กรุณาอัปโหลดไฟล์รูปภาพเท่านั้นครับ (PNG, JPG)")
            return
            
        discord_user_id = str(inter.author.id)
        evidence_uri = evidence.url
        
        payload = {
            "tournament_id": TOURNAMENT_ID,
            "discord_user_id": discord_user_id,
            "round_name": round_name,
            "placement": 0,
            "kills": 0,
            "evidence_uri": evidence_uri
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{API_BASE_URL}/discord/scores/submit", json=payload) as resp:
                    if resp.status == 200:
                        embed = disnake.Embed(title="📸 ส่งภาพหลักฐานสำเร็จ!", color=0x2ECC71)
                        embed.description = f"**รอบ:** {round_name}\nคุณได้ส่งรูปภาพผลการแข่งให้กรรมการเรียบร้อยแล้ว"
                        embed.set_image(url=evidence_uri)
                        embed.set_footer(text="กรรมการจะทำการตรวจสอบและอัปเดตคะแนนให้คุณครับ")
                        await inter.edit_original_response(embed=embed)
                        
                        evidence_channel = disnake.utils.get(inter.guild.channels, name="📸-ส่งผลการแข่ง")
                        if evidence_channel:
                            admin_embed = disnake.Embed(title="🚨 [NEW EVIDENCE] มีภาพผลการแข่งใหม่รอตรวจ!", color=0xF1C40F)
                            admin_embed.add_field(name="ผู้เล่น", value=inter.author.mention, inline=True)
                            admin_embed.add_field(name="รอบ", value=round_name, inline=True)
                            admin_embed.set_image(url=evidence_uri)
                            await evidence_channel.send(embed=admin_embed)
                    else:
                        data = await resp.json()
                        message = data.get("detail") or data.get("error", {}).get("message") or "Unknown error"
                        await inter.edit_original_response(content=f"❌ **ส่งผลไม่สำเร็จ:** {message}")
        except Exception:
            await inter.edit_original_response(content="⚠️ Error connecting to backend.")

def setup(bot):
    bot.add_cog(PlayerCog(bot))
