import disnake
from disnake.ext import commands
import aiohttp
import os
from utils import get_localized_error

API_BASE_URL = os.getenv("TOURNAMENT_API_URL", "http://127.0.0.1:8011")
DEFAULT_TOURNAMENT_ID = os.getenv("TOURNAMENT_ID", "demo_tournament_1")
DEFAULT_STAGE_ID = os.getenv("TOURNAMENT_STAGE_ID", "stage_1")

class AdminSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Auto-generate the Tournament OS Discord structure")
    @commands.default_member_permissions(administrator=True)
    async def setup_server(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        guild = inter.guild

        # 0. Clean up old English/default channels first
        categories_to_delete = ["📢 INFORMATION", "🎮 TOURNAMENT ZONE", "🔒 ADMIN & STAFF"]
        channels_to_delete = ["general", "ทั่วไป"]
        
        for cat_name in categories_to_delete:
            cat = disnake.utils.get(guild.categories, name=cat_name)
            if cat:
                for ch in cat.channels:
                    await ch.delete()
                await cat.delete()
                
        for ch in guild.channels:
            if ch.name in channels_to_delete and not getattr(ch.category, "name", "").startswith("📌"):
                await ch.delete()

        # 1. Create Roles from Specifications
        # According to EVIDENCE_AND_DISCORD_ROLE_ANALYSIS.md
        # Community roles come from Discord onboarding or manual admin setup.
        # Tournament roles must follow backend state; do not give "ผู้เข้าแข่งขัน"
        # to everyone who joins the community server.
        role_colors = {
            "สมาชิก": disnake.Color.light_grey(),          # Member
            "ผู้ชม": disnake.Color.light_grey(),            # Viewer
            "สนใจสมัครแข่ง": disnake.Color.teal(),         # Interested Player
            "รอตรวจสอบ": disnake.Color.blurple(),          # Pending Player
            "ผู้เข้าแข่งขัน": disnake.Color.blue(),         # Tournament Player
            "เช็คอินแล้ว": disnake.Color.green(),           # Checked In
            "เข้ารอบ": disnake.Color.gold(),                # Qualified
            "นักพากย์": disnake.Color.purple(),             # Caster
            "สมัครทีมงาน": disnake.Color.dark_grey(),       # Staff Applicant
            "ผู้ดูแลคะแนน": disnake.Color.orange(),        # Score Admin
            "กรรมการ": disnake.Color.orange(),              # Referee
            "แอดมินทัวร์นาเมนต์": disnake.Color.red(),      # Tournament Admin
        }
        roles_to_create = list(role_colors)
        created_roles = {}
        for role_name in roles_to_create:
            role = disnake.utils.get(guild.roles, name=role_name)
            if not role:
                role = await guild.create_role(
                    name=role_name,
                    hoist=role_name not in {"สมาชิก", "ผู้ชม", "สนใจสมัครแข่ง"},
                    mentionable=role_name in {
                        "สนใจสมัครแข่ง",
                        "รอตรวจสอบ",
                        "ผู้เข้าแข่งขัน",
                        "เช็คอินแล้ว",
                        "เข้ารอบ",
                        "ผู้ดูแลคะแนน",
                        "กรรมการ",
                        "แอดมินทัวร์นาเมนต์",
                    },
                    color=role_colors[role_name],
                )
            created_roles[role_name] = role

        # Helper to create category if not exists
        async def get_or_create_category(name, overwrites=None):
            cat = disnake.utils.get(guild.categories, name=name)
            if not cat:
                kwargs = {}
                if overwrites: kwargs['overwrites'] = overwrites
                cat = await guild.create_category(name, **kwargs)
            return cat

        # Helper to create text channel if not exists
        async def get_or_create_text_channel(category, name, overwrites=None):
            ch = disnake.utils.get(category.text_channels, name=name)
            if not ch:
                kwargs = {}
                if overwrites: kwargs['overwrites'] = overwrites
                ch = await category.create_text_channel(name, **kwargs)
            return ch
            
        # Helper to create voice channel if not exists
        async def get_or_create_voice_channel(category, name, overwrites=None):
            ch = disnake.utils.get(category.voice_channels, name=name)
            if not ch:
                kwargs = {}
                if overwrites: kwargs['overwrites'] = overwrites
                ch = await category.create_voice_channel(name, **kwargs)
            return ch

        # Base permissions
        everyone = guild.default_role
        viewer_role = created_roles["ผู้ชม"]
        interested_role = created_roles["สนใจสมัครแข่ง"]
        pending_role = created_roles["รอตรวจสอบ"]
        player_role = created_roles["ผู้เข้าแข่งขัน"]
        checked_in_role = created_roles["เช็คอินแล้ว"]
        qualified_role = created_roles["เข้ารอบ"]
        admin_role = created_roles["กรรมการ"]
        score_admin_role = created_roles["ผู้ดูแลคะแนน"]

        # 2. Category: COMMUNITY (Public)
        comm_cat = await get_or_create_category("📌 คอมมูนิตี้ทั่วไป")
        await get_or_create_text_channel(comm_cat, "👋-พูดคุยทั่วไป", overwrites={
            everyone: disnake.PermissionOverwrite(read_messages=True, send_messages=True)
        })
        await get_or_create_text_channel(comm_cat, "🎮-หาเพื่อนเล่น", overwrites={
            everyone: disnake.PermissionOverwrite(read_messages=True, send_messages=True)
        })
        await get_or_create_voice_channel(comm_cat, "🎧 ห้องนั่งเล่น 1", overwrites={
            everyone: disnake.PermissionOverwrite(connect=True, speak=True)
        })
        await get_or_create_voice_channel(comm_cat, "🎧 ห้องนั่งเล่น 2", overwrites={
            everyone: disnake.PermissionOverwrite(connect=True, speak=True)
        })

        # 3. Category: INFORMATION (Public)
        info_cat = await get_or_create_category("📢 ข่าวสารทัวร์นาเมนต์")
        read_only = {everyone: disnake.PermissionOverwrite(send_messages=False, read_messages=True)}
        await get_or_create_text_channel(info_cat, "📋-ประกาศ", overwrites=read_only)
        await get_or_create_text_channel(info_cat, "📚-กติกา", overwrites=read_only)
        await get_or_create_text_channel(info_cat, "🏆-ตารางคะแนน", overwrites=read_only)

        # 4. Category: TOURNAMENT ZONE
        # Interested/pending users can only see status/signup guidance.
        # Match operations stay limited to approved tournament players.
        tourney_cat = await get_or_create_category("🎮 โซนแข่งขัน", overwrites={
            everyone: disnake.PermissionOverwrite(read_messages=False),
            interested_role: disnake.PermissionOverwrite(read_messages=True),
            pending_role: disnake.PermissionOverwrite(read_messages=True),
            player_role: disnake.PermissionOverwrite(read_messages=True),
            checked_in_role: disnake.PermissionOverwrite(read_messages=True),
            qualified_role: disnake.PermissionOverwrite(read_messages=True),
        })
        # เช็คอิน: ห้ามพิมพ์ข้อความ ให้กดปุ่มอย่างเดียว
        await get_or_create_text_channel(tourney_cat, "🙋-เช็คอิน", overwrites={
            everyone: disnake.PermissionOverwrite(read_messages=False),
            interested_role: disnake.PermissionOverwrite(read_messages=False),
            pending_role: disnake.PermissionOverwrite(read_messages=False),
            player_role: disnake.PermissionOverwrite(read_messages=True, send_messages=False),
            checked_in_role: disnake.PermissionOverwrite(read_messages=True, send_messages=False),
            qualified_role: disnake.PermissionOverwrite(read_messages=True, send_messages=False),
        })
        # เช็คสถานะ: พิมพ์คำสั่ง /status อย่างเดียว
        await get_or_create_text_channel(tourney_cat, "📊-เช็คสถานะ", overwrites={
            everyone: disnake.PermissionOverwrite(read_messages=False),
            interested_role: disnake.PermissionOverwrite(read_messages=True, send_messages=False),
            pending_role: disnake.PermissionOverwrite(read_messages=True, send_messages=False),
            player_role: disnake.PermissionOverwrite(read_messages=True, send_messages=False),
            checked_in_role: disnake.PermissionOverwrite(read_messages=True, send_messages=False),
            qualified_role: disnake.PermissionOverwrite(read_messages=True, send_messages=False),
        })
        # ส่งผลการแข่ง: พิมพ์ได้ อัปโหลดรูปได้
        await get_or_create_text_channel(tourney_cat, "📸-ส่งผลการแข่ง", overwrites={
            everyone: disnake.PermissionOverwrite(read_messages=False),
            interested_role: disnake.PermissionOverwrite(read_messages=False),
            pending_role: disnake.PermissionOverwrite(read_messages=False),
            player_role: disnake.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            checked_in_role: disnake.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            qualified_role: disnake.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
        })
        # แจ้งปัญหา: พิมพ์ข้อความคุยได้
        await get_or_create_text_channel(tourney_cat, "⚖️-แจ้งปัญหา", overwrites={
            everyone: disnake.PermissionOverwrite(read_messages=False),
            interested_role: disnake.PermissionOverwrite(read_messages=True, send_messages=True),
            pending_role: disnake.PermissionOverwrite(read_messages=True, send_messages=True),
            player_role: disnake.PermissionOverwrite(read_messages=True, send_messages=True),
            checked_in_role: disnake.PermissionOverwrite(read_messages=True, send_messages=True),
            qualified_role: disnake.PermissionOverwrite(read_messages=True, send_messages=True),
        })

        # 5. Category: ADMIN & STAFF (Referees only)
        tourney_admin_role = created_roles["แอดมินทัวร์นาเมนต์"]
        admin_cat = await get_or_create_category("🔒 ทีมงาน", overwrites={
            everyone: disnake.PermissionOverwrite(read_messages=False),
            score_admin_role: disnake.PermissionOverwrite(read_messages=True, send_messages=True),
            admin_role: disnake.PermissionOverwrite(read_messages=True, send_messages=True),
            tourney_admin_role: disnake.PermissionOverwrite(read_messages=True, send_messages=True)
        })
        await get_or_create_text_channel(admin_cat, "⚙️-ควบคุมบอท", overwrites={
            everyone: disnake.PermissionOverwrite(read_messages=False),
            score_admin_role: disnake.PermissionOverwrite(read_messages=False),
            admin_role: disnake.PermissionOverwrite(read_messages=True, send_messages=True),
            tourney_admin_role: disnake.PermissionOverwrite(read_messages=True, send_messages=True)
        })
        await get_or_create_text_channel(admin_cat, "🚨-บันทึกกรรมการ", overwrites={
            everyone: disnake.PermissionOverwrite(read_messages=False),
            score_admin_role: disnake.PermissionOverwrite(read_messages=True, send_messages=True),
            admin_role: disnake.PermissionOverwrite(read_messages=True, send_messages=True),
            tourney_admin_role: disnake.PermissionOverwrite(read_messages=True, send_messages=True)
        })

        try:
            await inter.edit_original_response(content="✅ **สร้างโครงสร้าง Tournament OS สำเร็จแล้ว!**\nเซ็ต role ชุมชน, role สมัครแข่ง, role ผู้เข้าแข่งขันจริง และสิทธิ์ห้องตามสถานะเรียบร้อยครับ")
        except disnake.errors.NotFound:
            pass # Interaction message was likely deleted because it was in a channel we just deleted

    @commands.slash_command(description="ลบห้องเก่า (ภาษาอังกฤษ) และห้องที่ไม่ได้ใช้งานทิ้งทั้งหมด")
    @commands.default_member_permissions(administrator=True)
    async def cleanup_channels(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        guild = inter.guild

        channels_deleted = 0
        # หมวดหมู่ภาษาอังกฤษที่เคยสร้างไปตอนแรก
        categories_to_delete = ["📢 INFORMATION", "🎮 TOURNAMENT ZONE", "🔒 ADMIN & STAFF"]
        # ห้องเริ่มต้นของ Discord
        channels_to_delete = ["general", "ทั่วไป"]
        
        for cat_name in categories_to_delete:
            cat = disnake.utils.get(guild.categories, name=cat_name)
            if cat:
                for ch in cat.channels:
                    await ch.delete()
                    channels_deleted += 1
                await cat.delete()
                channels_deleted += 1
                
        # ลบห้องเริ่มต้นของ Discord ที่ไม่ได้อยู่ในหมวดหมู่ของเรา
        for ch in guild.channels:
            if ch.name in channels_to_delete and not getattr(ch.category, "name", "").startswith("📌"):
                await ch.delete()
                channels_deleted += 1

        if channels_deleted > 0:
            await inter.edit_original_response(content=f"🧹 **ลบห้องเก่าและห้องที่ไม่ใช้สำเร็จ!** (ลบไปทั้งหมด {channels_deleted} ห้อง/หมวดหมู่)")
        else:
            await inter.edit_original_response(content="✅ **เซิร์ฟเวอร์สะอาดอยู่แล้วครับ!** ไม่มีห้องเก่าหลงเหลืออยู่เลย")

    @commands.slash_command(description="Spawn the Admin Control Panel")
    @commands.has_any_role("แอดมินทัวร์นาเมนต์", "กรรมการ")
    async def spawn_admin_panel(self, inter: disnake.ApplicationCommandInteraction, tournament_id: str = None):
        await inter.response.defer()
        
        tid = tournament_id or DEFAULT_TOURNAMENT_ID
        
        embed = disnake.Embed(
            title="⚙️ ศูนย์ควบคุมแอดมิน (Admin Control Panel)",
            description="กดปุ่มด้านล่างเพื่อจัดการทัวร์นาเมนต์ได้ทันที โดยไม่ต้องพิมพ์คำสั่ง!",
            color=0xE74C3C
        )
        
        view = disnake.ui.View(timeout=None)
        view.add_item(disnake.ui.Button(label="✅ ยืนยันผู้เล่น", style=disnake.ButtonStyle.success, custom_id=f"admin_approve:{tid}"))
        view.add_item(disnake.ui.Button(label="🔓 เปิด/ปิด เช็คอิน", style=disnake.ButtonStyle.secondary, custom_id=f"admin_checkin:{tid}"))
        view.add_item(disnake.ui.Button(label="📢 ประกาศสายแข่ง", style=disnake.ButtonStyle.primary, custom_id=f"admin_announce_groups:{tid}"))
        view.add_item(disnake.ui.Button(label="📊 ประกาศคะแนน", style=disnake.ButtonStyle.primary, custom_id=f"admin_announce_leaderboard:{tid}"))
        
        await inter.channel.send(embed=embed, view=view)
        await inter.edit_original_response(content="✅ Admin Control Panel spawned successfully.")

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        if not hasattr(inter.author, "roles"):
            return
            
        cid_full = inter.component.custom_id
        if not cid_full:
            return
            
        parts = cid_full.split(":")
        cid = parts[0]
        tournament_id = parts[1] if len(parts) > 1 else DEFAULT_TOURNAMENT_ID
            
        is_admin = any(role.name in ["แอดมินทัวร์นาเมนต์", "กรรมการ"] for role in inter.author.roles)
        if not is_admin and cid.startswith("admin_"):
            await inter.response.send_message("❌ คุณไม่มีสิทธิ์ใช้งานปุ่มนี้!", ephemeral=True)
            return
            
        if cid == "admin_approve":
            await inter.response.send_modal(
                title="✅ ยืนยันผู้เล่น (Approve Player)",
                custom_id=f"modal_approve_player:{tournament_id}",
                components=[
                    disnake.ui.TextInput(
                        label="Discord User ID ของผู้เล่น",
                        placeholder="พิมพ์ ID ตัวเลขของผู้เล่น...",
                        custom_id="player_id",
                        style=disnake.TextInputStyle.short,
                        required=True
                    )
                ]
            )
            return

        elif cid == "admin_checkin":
            await inter.response.defer(ephemeral=True)
            try:
                async with aiohttp.ClientSession() as session:
                    payload = {
                        "tournament_id": tournament_id,
                        "action": "open",
                        "stage_id": DEFAULT_STAGE_ID,
                    }
                    async with session.post(f"{API_BASE_URL}/discord/admin/check-in-session", json=payload) as resp:
                        if resp.status == 200:
                            await inter.edit_original_response(content=f"✅ Check-in session has been opened.")
                        else:
                            data = await resp.json()
                            message = get_localized_error(data)
                            await inter.edit_original_response(content=f"❌ Failed to update check-in session: {message}")
            except Exception:
                await inter.edit_original_response(content="⚠️ Error connecting to backend.")
            return

        elif cid == "admin_announce_groups":
            await inter.response.defer(ephemeral=True)
            await inter.edit_original_response(
                content="⚠️ Group announcement ยังไม่เปิดใช้ จนกว่า backend จะมี endpoint ประกาศกลุ่มจากข้อมูลจริง"
            )
            return

        elif cid == "admin_announce_leaderboard":
            await inter.response.defer(ephemeral=True)
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{API_BASE_URL}/discord/leaderboard?tournament_id={tournament_id}") as resp:
                        if resp.status != 200:
                            await inter.edit_original_response(content="❌ ดึงข้อมูลตารางคะแนนจาก backend ไม่สำเร็จ")
                            return
                        data = await resp.json()
            except Exception:
                await inter.edit_original_response(content="⚠️ Error connecting to backend.")
                return

            rows = data.get("leaderboard", [])
            embed = disnake.Embed(title="🏆 Current Leaderboard", description="สรุปคะแนนล่าสุดจาก backend", color=0xFFD700)
            if rows:
                for item in rows[:10]:
                    embed.add_field(
                        name=f"#{item['rank']} {item['display_name']}",
                        value=f"{item['total_points']} pts / {item['games_played']} games",
                        inline=False,
                    )
            else:
                embed.description = "ยังไม่มีคะแนนที่ approved/final"

            score_channel = disnake.utils.get(inter.guild.channels, name="🏆-ตารางคะแนน")
            if score_channel:
                await score_channel.send(embed=embed)
                await inter.edit_original_response(content="✅ Leaderboard announced successfully.")
            else:
                await inter.edit_original_response(content="❌ Leaderboard channel not found.")
            return

    @commands.Cog.listener()
    async def on_modal_submit(self, inter: disnake.ModalInteraction):
        cid_full = inter.custom_id
        if not cid_full:
            return
            
        parts = cid_full.split(":")
        cid = parts[0]
        tournament_id = parts[1] if len(parts) > 1 else DEFAULT_TOURNAMENT_ID

        if cid == "modal_approve_player":
            await inter.response.defer(ephemeral=True)
            player_id = inter.text_values["player_id"]
            try:
                async with aiohttp.ClientSession() as session:
                    payload = {"tournament_id": tournament_id, "discord_user_id": player_id}
                    async with session.post(f"{API_BASE_URL}/discord/admin/approve-player", json=payload) as resp:
                        if resp.status == 200:
                            await inter.edit_original_response(content=f"✅ Approved player `{player_id}`!")
                        else:
                            data = await resp.json()
                            message = get_localized_error(data)
                            await inter.edit_original_response(content=f"❌ Failed to approve player: {message}")
            except Exception:
                await inter.edit_original_response(content="⚠️ Error connecting to backend.")

def setup(bot):
    bot.add_cog(AdminSetup(bot))
