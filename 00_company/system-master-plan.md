# TTLIVE System Master Plan

เอกสารนี้คือแผนแม่บทของ TTLIVE ใช้กำหนดว่าระบบทั้งหมดควรมีอะไรบ้าง ทำเพื่ออะไร และควรสร้างลำดับไหนก่อน

## หลักคิด

TTLIVE ตอนนี้ทำโดยคนเดียว จึงต้องออกแบบระบบให้ช่วยลดงานซ้ำ ไม่เพิ่มภาระเอกสาร และต้องทำให้ทุกงานต่อยอดเป็นทีมได้ในอนาคต

ระบบที่ดีต้องตอบได้ 6 ข้อ:

- จะไลฟ์อะไร
- ไลฟ์เมื่อไร
- ต้องเตรียมอะไร
- หลังไลฟ์เอาอะไรไปทำต่อ
- ผลลัพธ์ดีหรือไม่ดีเพราะอะไร
- ครั้งหน้าจะปรับอะไร

## ระบบหลักที่ TTLIVE ควรมี

### 1. Strategy System

ใช้กำหนดทิศทางช่อง เป้าหมาย และ priority

ไฟล์หลัก:

- `00_company/vision.md`
- `00_company/system-master-plan.md`
- `00_company/roadmap.md`
- `00_company/current-priorities.md`
- `DASHBOARD.md`

สิ่งที่ต้องรู้:

- เกมหลักคือ Golden Spatula และ LoL Wild Rift
- ไลฟ์ขั้นต่ำ 1 ชั่วโมง
- ทำคนเดียว จึงต้องใช้ template และ automation ช่วย
- เป้าหมายระยะแรกคือทำให้ไลฟ์สม่ำเสมอและมี clip ออกต่อเนื่อง

### 2. Schedule System

ใช้วางแผนเวลาไลฟ์ รายสัปดาห์ รายวัน และอนาคตรายเดือน

ไฟล์หลัก:

- `03_live_operations/stream-schedule-system.md`
- `03_live_operations/schedules/`
- `07_data/weekly-schedules/`
- `05_templates/weekly-schedule/`

กฎเริ่มต้น:

- ไลฟ์แต่ละครั้งขั้นต่ำ 1 ชั่วโมง
- ถ้าเหนื่อยหรือเวลาน้อย ให้ลดจำนวนวันก่อนลดคุณภาพ
- ตารางรายสัปดาห์ใช้วางภาพรวม
- ตารางรายวันใช้ประกาศแบบเร็วในวันที่จะไลฟ์

### 3. Live Operation System

ใช้จัดการก่อนขึ้นไลฟ์ ระหว่างไลฟ์ และหลังลงไลฟ์

ไฟล์หลัก:

- `03_live_operations/checklists/`
- `03_live_operations/runbooks/`
- `11_sop/before-live.md`
- `11_sop/after-live.md`

สิ่งที่ต้องมี:

- checklist ก่อนขึ้นไลฟ์
- checklist หลังลงไลฟ์
- runbook เมื่อเน็ตหลุด เสียงหาย เกมพัง หรือ live delay
- note สำหรับ mark ช่วงที่น่าตัดคลิป

### 4. Asset And Layout System

ใช้คุมภาพลักษณ์ให้เหมือนเดิมทุกครั้ง

ไฟล์หลัก:

- `01_brand/`
- `04_assets/`
- `05_templates/`
- `08_outputs/`

ชนิดภาพที่ต้องมี:

- ตารางไลฟ์รายสัปดาห์
- ภาพประกาศก่อนขึ้นไลฟ์
- ภาพหลังลงไลฟ์หรือ recap
- ปกไลฟ์
- overlay ระหว่างไลฟ์
- thumbnail/cover สำหรับคลิป

หลักการ:

- template คงที่
- เปลี่ยนเฉพาะข้อความ เกม เวลา และ character/icon
- output แยกจาก asset ต้นฉบับเสมอ

### 5. Clip Production System

ใช้เปลี่ยนไลฟ์ยาวให้เป็นคลิปสั้น

ไฟล์หลักในอนาคต:

- `02_content/clips/`
- `11_sop/edit-short-clip.md`
- `11_sop/upload-clip.md`
- `09_reports/clip-performance/`

เป้าหมาย:

- หลังไลฟ์ 1 ครั้ง ควรหาได้อย่างน้อย 1-3 ช่วงสำหรับตัดคลิป
- ไม่จำเป็นต้องตัดเยอะในช่วงแรก
- เน้นทำซ้ำให้ได้ก่อน แล้วค่อยเพิ่มคุณภาพ

### 6. Analytics System

ใช้วิเคราะห์ผลไลฟ์และผลคลิป

ไฟล์หลักในอนาคต:

- `09_reports/live-analytics/`
- `09_reports/clip-performance/`
- `09_reports/monthly/`
- `09_reports/experiments/`

ตัวชี้วัดเริ่มต้น:

- ระยะเวลาไลฟ์
- จำนวนผู้ชมสูงสุด
- จำนวนผู้ชมเฉลี่ย
- chat/activity
- follower เพิ่ม
- ช่วงเวลาที่คนดูเยอะ
- clip ที่ตัดออกมาได้
- คลิปไหนยอดดูดี

### 7. Automation System

ใช้ลดงานซ้ำ แต่ไม่ควรเริ่มจาก automation หนักเกินไป

ไฟล์หลัก:

- `06_automation/`
- `07_data/`
- `05_templates/`

ลำดับ automation:

1. สร้างตาราง Markdown
2. สร้างภาพตารางรายสัปดาห์
3. สร้างปกไลฟ์
4. สร้าง caption/post
5. สรุปรายงานหลังไลฟ์
6. ช่วยหา clip candidate จาก note หรือ transcript

### 8. Community System

ใช้ดูแลคนดูและ moderator ในอนาคต

ไฟล์หลัก:

- `13_community/chat-rules.md`
- `13_community/moderator-guide.md`

ระยะแรกยังไม่ต้องซับซ้อน แค่ต้องมีกฎแชทและรูปแบบกิจกรรมเล่นกับคนดู

### 9. Monetization System

ใช้เตรียมรับ sponsor, affiliate หรือ donation ในอนาคต

ไฟล์หลัก:

- `14_monetization/`
- `12_legal/`

ตอนนี้ยังไม่ใช่ priority แรก แต่ควรเก็บโครงไว้เพื่อไม่ต้องเริ่มใหม่ภายหลัง

## ระบบที่ยังไม่ควรรีบทำ

- dashboard web app
- automation ตัดต่อเต็มรูปแบบ
- AI วิเคราะห์วิดีโอทั้งไฟล์
- ระบบหลายคนแบบละเอียด
- sponsor package จริงจัง

เหตุผล: ตอนนี้โจทย์หลักคือทำคนเดียวให้สม่ำเสมอและวัดผลได้ก่อน

## Definition Of Done

หนึ่งรอบการทำงานถือว่าเสร็จเมื่อมีครบ:

- ตารางไลฟ์
- ภาพหรือโพสต์ประกาศ
- ไลฟ์อย่างน้อย 1 ชั่วโมง
- note หลังไลฟ์
- clip candidate อย่างน้อย 1 ช่วง
- รายงานสั้นว่าอะไรเวิร์ก/ไม่เวิร์ก
