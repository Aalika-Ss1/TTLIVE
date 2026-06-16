import disnake
from disnake.ext import commands
import aiohttp
import os
from utils import get_localized_error

API_BASE_URL = os.getenv("TOURNAMENT_API_URL", "http://127.0.0.1:8011")

DEFAULT_TOURNAMENT_ID = os.getenv("TOURNAMENT_ID", "demo_tournament_1")

# Status labels in Thai
STATUS_LABELS = {
    "not_registered": "❌ ยังไม่ได้สมัคร",
    "submitted": "🕐 รอแอดมินตรวจสอบ",
    "approved": "✅ ผ่านการคัดเลือก",
    "waitlisted": "📋 อยู่ในรายสำรอง",
    "rejected": "❌ ไม่ผ่านการคัดเลือก",
    "withdrawn": "🚫 ถอนตัวแล้ว",
}

def build_status_view(allowed_actions: list, check_in_session_id: str = None, tournament_id: str = None) -> disnake.ui.View:
    """Build a View with buttons based on allowed_actions from the backend."""
    view = disnake.ui.View(timeout=None)
    
    tid = tournament_id or DEFAULT_TOURNAMENT_ID
    
    if "register" in allowed_actions:
        view.add_item(disnake.ui.Button(
            label="📝 สมัครแข่งขัน", style=disnake.ButtonStyle.success,
            custom_id=f"panel_register:{tid}", row=0
        ))
    if "check_in" in allowed_actions:
        cid = f"panel_checkin__{check_in_session_id}:{tid}" if check_in_session_id else f"panel_checkin:{tid}"
        view.add_item(disnake.ui.Button(
            label="✅ เช็คอิน", style=disnake.ButtonStyle.success,
            custom_id=cid, row=0
        ))
    if "view_group" in allowed_actions:
        view.add_item(disnake.ui.Button(
            label="🎮 สายการแข่งของฉัน", style=disnake.ButtonStyle.primary,
            custom_id=f"panel_group:{tid}", row=0
        ))
    if "submit_evidence" in allowed_actions:
        view.add_item(disnake.ui.Button(
            label="📸 ส่งภาพผลการแข่ง", style=disnake.ButtonStyle.secondary,
            custom_id=f"panel_evidence_hint:{tid}", row=1
        ))
    if "view_status" in allowed_actions:
        view.add_item(disnake.ui.Button(
            label="📊 ดูสถานะ", style=disnake.ButtonStyle.secondary,
            custom_id=f"panel_status:{tid}", row=1
        ))

    # Always show leaderboard and dispute
    view.add_item(disnake.ui.Button(
        label="🏆 ตารางคะแนน", style=disnake.ButtonStyle.secondary,
        custom_id=f"panel_leaderboard:{tid}", row=1
    ))
    view.add_item(disnake.ui.Button(
        label="🚨 แจ้งปัญหา", style=disnake.ButtonStyle.danger,
        custom_id=f"panel_dispute:{tid}", row=2
    ))
    return view


class PlayerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Spawn the Player Control Panel (Admin only)", default_member_permissions=disnake.Permissions(administrator=True))
    async def spawn_player_panel(self, inter: disnake.ApplicationCommandInteraction, tournament_id: str = None):
        await inter.response.defer()
        
        tid = tournament_id or DEFAULT_TOURNAMENT_ID
        
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
            custom_id=f"panel_status:{tid}", emoji="🔍"
        ))
        
        await inter.channel.send(embed=embed, view=view)
        await inter.edit_original_response(content=f"✅ Player Control Panel spawned successfully for `{tid}`.")

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        cid_full = inter.component.custom_id
        if not cid_full:
            return

        parts = cid_full.split(":")
        cid = parts[0]
        tournament_id = parts[1] if len(parts) > 1 else DEFAULT_TOURNAMENT_ID

        # ─── STATUS: Dynamic entry point ───────────────────────────────────
        if cid == "panel_status":
            await inter.response.defer(ephemeral=True)
            discord_user_id = str(inter.author.id)
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{API_BASE_URL}/discord/players/me/status?tournament_id={tournament_id}&discord_user_id={discord_user_id}"
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
                
            view = build_status_view(allowed, check_in_session_id, tournament_id)
            await inter.edit_original_response(embed=embed, view=view)
            return

        # ─── REGISTER ──────────────────────────────────────────────────────
        if cid == "panel_register":
            # Phase 2: Send a link to the Web Profile page instead of a Modal
            web_url = f"{API_BASE_URL.replace('/api', '')}/web/tournaments/{tournament_id}/profile?discord_id={inter.author.id}"
            
            embed = disnake.Embed(
                title="📝 สมัครแข่งขันผ่าน Web Profile", 
                description="ใน Phase 2 นี้ การสมัครและจัดการโปรไฟล์จะย้ายไปที่หน้าเว็บไซต์เพื่อความสะดวกและรวดเร็วครับ\n\n**กรุณากดปุ่มด้านล่างเพื่อไปยังหน้าเว็บลงทะเบียนครับ**", 
                color=0x2ECC71
            )
            
            view = disnake.ui.View()
            view.add_item(disnake.ui.Button(label="ไปยังหน้าเว็บ Profile", url=web_url, style=disnake.ButtonStyle.link, emoji="🌐"))
            
            await inter.response.send_message(embed=embed, view=view, ephemeral=True)
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
                            message = get_localized_error(data)
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
                    url = f"{API_BASE_URL}/discord/players/me/group?tournament_id={tournament_id}&discord_user_id={discord_user_id}"
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
                    url = f"{API_BASE_URL}/discord/leaderboard?tournament_id={tournament_id}"
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
                custom_id=f"modal_dispute:{tournament_id}",
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
        cid_full = inter.custom_id
        if not cid_full:
            return
            
        parts = cid_full.split(":")
        cid = parts[0]
        tournament_id = parts[1] if len(parts) > 1 else DEFAULT_TOURNAMENT_ID

        if cid == "modal_dispute":
            reason = inter.text_values["dispute_reason"]
            await inter.response.send_message(
                f"🚨 **แจ้งปัญหาสำเร็จ!**\nรายละเอียด: `{reason}`\nแอดมินได้รับแจ้งปัญหาแล้ว กรุณารอการติดต่อกลับครับ",
                ephemeral=True
            )
            
            dispute_channel = disnake.utils.get(inter.guild.channels, name="⚖️-แจ้งปัญหา")
            if dispute_channel:
                embed = disnake.Embed(title="🚨 [NEW DISPUTE] มีการแจ้งปัญหาใหม่!", color=0xE74C3C)
                embed.add_field(name="ผู้แจ้ง (Player)", value=inter.author.mention, inline=False)
                embed.add_field(name="รายละเอียดปัญหา", value=reason, inline=False)
                
                referee_role = disnake.utils.get(inter.guild.roles, name="กรรมการ")
                mention = referee_role.mention if referee_role else ""
                
                await dispute_channel.send(content=f"🚨 {mention} มีการแจ้งปัญหาใหม่ครับ", embed=embed)
            return
            
        # Note: modal_register was deprecated in Phase 2 in favor of Web Profile Registration
    @commands.slash_command(description="Submit match screenshot as evidence for referees")
    async def submit_evidence(
        self, 
        inter: disnake.ApplicationCommandInteraction, 
        round_name: str = commands.Param(choices=["Round 1", "Round 2", "Round 3", "Round 4", "Finals"]),
        placement: int = commands.Param(ge=1, le=8, description="อันดับที่คุณได้ในการแข่ง (1-8)"),
        evidence: disnake.Attachment = commands.Param(description="อัปโหลดรูปภาพ Screenshot ผลการแข่ง"),
        tournament_id: str = commands.Param(default=None, description="รหัสทัวร์นาเมนต์ (เลือกข้ามได้)")
    ):
        await inter.response.defer(ephemeral=True)
        
        tid = tournament_id or DEFAULT_TOURNAMENT_ID
        
        if not evidence.content_type or not evidence.content_type.startswith("image/"):
            await inter.edit_original_response(content="❌ กรุณาอัปโหลดไฟล์รูปภาพเท่านั้นครับ (PNG, JPG)")
            return
            
        discord_user_id = str(inter.author.id)
        evidence_uri = evidence.url
        
        payload = {
            "tournament_id": tid,
            "discord_user_id": discord_user_id,
            "round_name": round_name,
            "placement": placement,
            "kills": 0,
            "evidence_uri": evidence_uri
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
                                
                                # Upload image to backend to trigger OCR
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

                        embed = disnake.Embed(title="📸 ส่งภาพหลักฐานสำเร็จ!", color=0x2ECC71)
                        embed.description = f"**รอบ:** {round_name}\nคุณได้ส่งรูปภาพผลการแข่งและอันดับที่ {placement} ให้กรรมการเรียบร้อยแล้ว"
                        embed.set_image(url=evidence_uri)
                        embed.set_footer(text="ระบบได้ประมวลผล OCR และส่งรายงานไปยังกรรมการแล้วครับ")
                        await inter.edit_original_response(embed=embed)
                        
                        evidence_channel = disnake.utils.get(inter.guild.channels, name="📸-ส่งผลการแข่ง")
                        if evidence_channel:
                            admin_embed = disnake.Embed(title="🚨 [NEW EVIDENCE] มีภาพผลการแข่งใหม่และผลสแกน OCR รอตรวจ!", color=0xF1C40F)
                            admin_embed.add_field(name="ผู้เล่น", value=inter.author.mention, inline=True)
                            admin_embed.add_field(name="รอบ", value=round_name, inline=True)
                            admin_embed.add_field(name="อันดับที่รายงาน", value=str(placement), inline=True)
                            admin_embed.set_image(url=evidence_uri)
                            await evidence_channel.send(embed=admin_embed)
                    else:
                        data = await resp.json()
                        message = get_localized_error(data)
                        await inter.edit_original_response(content=f"❌ **ส่งผลไม่สำเร็จ:** {message}")
        except Exception as e:
            print(f"Error in submit_evidence: {e}")
            await inter.edit_original_response(content="⚠️ Error connecting to backend.")
def setup(bot):
    bot.add_cog(PlayerCog(bot))
