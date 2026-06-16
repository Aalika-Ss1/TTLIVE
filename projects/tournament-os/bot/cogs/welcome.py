import disnake
from disnake.ext import commands
import os

class WelcomeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member):
        guild = member.guild
        print(f"New member joined: {member.name} (ID: {member.id}) in guild {guild.name}")

        # 1. Automatically assign the "สมาชิก" (Member) role
        member_role = disnake.utils.get(guild.roles, name="สมาชิก")
        if member_role:
            try:
                await member.add_roles(member_role)
                print(f"Successfully auto-assigned 'สมาชิก' role to {member.name}")
            except Exception as e:
                print(f"Failed to auto-assign 'สมาชิก' role: {e}")
        else:
            print("Role 'สมาชิก' not found in this guild.")

        # 2. Send welcome embed card to "👋-ยินดีต้อนรับ" channel
        welcome_channel = disnake.utils.get(guild.text_channels, name="👋-ยินดีต้อนรับ")
        if welcome_channel:
            try:
                # Find channels to mention in description
                status_channel = disnake.utils.get(guild.text_channels, name="📊-เช็คสถานะ")
                chat_channel = disnake.utils.get(guild.text_channels, name="👋-พูดคุยทั่วไป")
                
                status_mention = status_channel.mention if status_channel else "`📊-เช็คสถานะ`"
                chat_mention = chat_channel.mention if chat_channel else "`👋-พูดคุยทั่วไป`"

                embed = disnake.Embed(
                    title="👋 ยินดีต้อนรับผู้เข้าแข่งขันใหม่!",
                    description=(
                        f"สวัสดีครับ {member.mention} ยินดีต้อนรับเข้าสู่คอมมูนิตี้ทัวร์นาเมนต์การแข่งขันของเราครับ!\n\n"
                        f"📢 **วิธีเริ่มลงทะเบียนเข้าร่วมแข่งขัน:**\n"
                        f"1. ไปที่ช่อง {status_mention} เพื่อดูข้อมูลและปุ่มควบคุม\n"
                        f"2. กดปุ่ม **📝 สมัครแข่งขัน** เพื่อพิมพ์ข้อมูลชื่อสมัครแข่งได้ทันที!\n\n"
                        f"💬 แวะเข้าไปทำความรู้จักและหาห้องเล่นร่วมกันได้ที่ช่อง {chat_mention} นะครับ!"
                    ),
                    color=0x2ECC71  # Modern Emerald Green
                )
                
                if member.display_avatar:
                    embed.set_thumbnail(url=member.display_avatar.url)
                    
                embed.set_footer(text="Tournament OS Onboarding Assistant", icon_url=self.bot.user.display_avatar.url if self.bot.user and self.bot.user.display_avatar else None)
                
                await welcome_channel.send(content=f"ต้อนรับสมาชิกใหม่! {member.mention}", embed=embed)
                print(f"Successfully sent welcome card for {member.name}")
            except Exception as e:
                print(f"Failed to send welcome message: {e}")
        else:
            print("Channel '👋-ยินดีต้อนรับ' not found in this guild.")

def setup(bot):
    bot.add_cog(WelcomeCog(bot))
