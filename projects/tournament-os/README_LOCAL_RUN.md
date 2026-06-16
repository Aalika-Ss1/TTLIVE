# คู่มือการติดตั้งและใช้งานจริงบนเครื่องโลคอล (Local Server & Discord Bot)

คู่มือนี้แนะนำวิธีการเปลี่ยนเครื่องคอมพิวเตอร์ของคุณเป็นเซิร์ฟเวอร์รันระบบ **Tournament OS** (FastAPI + Discord Bot + PostgreSQL Database) ให้สามารถบริการได้ตลอด 24 ชั่วโมง หรือใช้สำหรับรันจัดแมตช์แข่งจริง

---

## 📋 แผนภาพการเชื่อมต่อระดับเครื่องโลคอล

```text
[ ผู้แข่งขัน (Discord) ] ---> [ Discord Server ] 
                                     │
                                     ▼ (Internet)
[ เครื่องคอมคุณ ] <--- [ Cloudflare Tunnel ] <--- [ Discord Bot (main.py) ]
      │                                                │
      ├──> [ PostgreSQL (Docker Port 5433) ]           │ (HTTP ยิง API พอร์ต 8010)
      │                                                │
      └──> [ FastAPI Backend (Uvicorn Port 8010) ] <───┘
```

---

## 🛠️ ขั้นตอนการติดตั้งและรันใช้งานจริง

### ขั้นตอนที่ 1: สตาร์ท PostgreSQL Database บน Docker
ตัวระบบจะใช้ฐานข้อมูล PostgreSQL เป็นหลักสำหรับการบันทึกคะแนนและข้อมูลผู้เล่น
1. เปิดโปรแกรม **Docker Desktop** ในเครื่องคอมคุณให้เรียบร้อย
2. เปิด PowerShell/Terminal แล้วไปที่โฟลเดอร์ `backend`:
   ```powershell
   cd E:\TTLIVE\projects\tournament-os\backend
   ```
3. สั่งรัน PostgreSQL Container ขึ้นมาเบื้องหลัง:
   ```powershell
   docker compose up -d postgres
   ```
4. รันคำสั่งอัปเดตโครงสร้างตารางข้อมูล (Migrations) ให้เรียบร้อย:
   ```powershell
   alembic upgrade head
   ```

---

### ขั้นตอนที่ 2: ตั้งค่าระบบ (Environment Variables)
เราต้องทำให้บอทและหลังบ้านมองเห็นพอร์ตเดียวกัน เพื่อให้ส่งข้อมูลหากันได้

#### 1. ตั้งค่าไฟล์หลังบ้าน (`E:\TTLIVE\projects\tournament-os\backend\.env`):
สร้างหรือตรวจสอบไฟล์ `.env` ในโฟลเดอร์ `backend` ให้มีค่าดังนี้:
```ini
TOURNAMENT_OS_DATABASE_URL=postgresql+psycopg://tournament_os:tournament_os@localhost:5433/tournament_os
DISCORD_TOKEN=โทเค็นบอท_Discord_จริงของคุณ
DISCORD_GUILD_ID=ไอดีเซิร์ฟเวอร์_Discord_ของคุณ
TOURNAMENT_OS_ADMIN_TOKEN=รหัสผ่านแอดมินสุ่มของคุณเอง (เช่น mysecretadmintoken123)
```

#### 2. ตั้งค่าไฟล์บอท (`E:\TTLIVE\projects\tournament-os\bot\.env`):
สร้างหรือตรวจสอบไฟล์ `.env` ในโฟลเดอร์ `bot` ให้เชื่อมกับหลังบ้าน:
```ini
TOURNAMENT_API_URL=http://127.0.0.1:8010
DISCORD_TOKEN=โทเค็นบอท_Discord_จริงของคุณ
DISCORD_GUILD_ID=ไอดีเซิร์ฟเวอร์_Discord_ของคุณ
TOURNAMENT_OS_ADMIN_TOKEN=รหัสผ่านแอดมินสุ่มของคุณเอง (ต้องตรงกับของหลังบ้าน)
```
*(การระบุ `TOURNAMENT_API_URL=http://127.0.0.1:8010` จะทำให้บอทยิงหา FastAPI ที่พอร์ต 8010 ทันที)*

---

### ขั้นตอนที่ 3: สตาร์ทหลังบ้านและบอทให้รันเบื้องหลังด้วย PM2
เพื่อให้ทั้ง FastAPI และบอททำงานอยู่เบื้องหลัง ไม่ปิดตัวเองเมื่อเราปิด Terminal และรีสตาร์ทอัตโนมัติหากโปรแกรมแครช เราจะใช้เครื่องมือชื่อว่า **PM2**

1. ติดตั้ง Node.js ในเครื่องคอมพิวเตอร์ของคุณ (หากยังไม่มี)
2. เปิด Terminal/PowerShell แล้วติดตั้ง PM2 แบบ Global:
   ```powershell
   npm install -g pm2
   ```
3. **สั่งรัน FastAPI Backend:**
   เปิด PowerShell ไปที่โฟลเดอร์ `backend` แล้วรัน:
   ```powershell
   pm2 start "python -m uvicorn tournament_os.api.main:app --host 0.0.0.0 --port 8010" --name "tournament-backend"
   ```
4. **สั่งรัน Discord Bot:**
   เปิด PowerShell ไปที่โฟลเดอร์ `bot` แล้วรัน:
   ```powershell
   pm2 start "python main.py" --name "tournament-bot"
   ```

#### 💡 คำสั่งการควบคุม PM2 ที่ควรทราบ:
* `pm2 list` : ดูสถานะการทำงานของบอทและหลังบ้าน
* `pm2 logs` : ดูการอัปเดตข้อมูลหรือข้อผิดพลาดแบบสดๆ (สำคัญมากสำหรับดู Log การคีย์คะแนน)
* `pm2 stop all` : หยุดการทำงานของทุกตัวชั่วคราว
* `pm2 restart all` : สั่งเริ่มการทำงานใหม่ทั้งหมด (ใช้เมื่อมีการแก้ไขโค้ด)

---

### ขั้นตอนที่ 4: เปิดอุโมงค์เชื่อมต่อเพื่อแชร์ให้คนนอก (Cloudflare Tunnel)
เนื่องจาก Discord ต้องยิงไฟล์สกรีนช็อตรูปภาพมายังหลังบ้านของคุณ และคนนอกต้องติดต่อกับหลังบ้านได้ เราจึงต้องแชร์พอร์ต `8010` ของเราออกสู่อินเทอร์เน็ต

1. ดาวน์โหลดโปรแกรมติดตั้งเครื่องมือของ Cloudflare ชื่อว่า **cloudflared** 
2. รันคำสั่งเปิดอุโมงค์ชี้ไปที่พอร์ต `8010` บนคอมคุณ:
   ```powershell
   cloudflared tunnel --url http://localhost:8010
   ```
3. ดูผลลัพธ์ในหน้าจอ มองหาลิงก์ URL สาธารณะแบบ HTTPS เช่น:
   `https://your-unique-subdomain.trycloudflare.com`
4. **สำคัญมาก:** ก๊อปปี้ลิงก์นี้ไปใส่แทนค่าในไฟล์ `bot/.env`:
   ```ini
   TOURNAMENT_API_URL=https://your-unique-subdomain.trycloudflare.com
   ```
   จากนั้นสั่งรีสตาร์ทบอท: `pm2 restart tournament-bot`

เพียงเท่านี้ ผู้เล่นจากภายนอกก็จะส่งภาพ/พิมพ์คะแนน และมีบอทตอบโต้กลับโดยประมวลผลผ่านหลังบ้านบนคอมคุณแบบ 24 ชั่วโมงได้ทันทีครับ!
