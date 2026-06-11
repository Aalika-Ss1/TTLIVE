# Stream Schedule System

ระบบตารางไลฟ์ของ TTLIVE รองรับ 3 รูปแบบ

## 1. Weekly Schedule

ใช้สำหรับโพสต์ตารางประจำสัปดาห์ เหมาะกับ Facebook, Discord และ TikTok community post

คอลัมน์มาตรฐาน:

- วัน
- เกม
- เช้า
- เย็น

เกมหลักตอนนี้:

- Golden Spatula
- LoL Wild Rift
- Naraka: Bladepoint
- Soul Land: Awakening World

ช่วงเวลาหลักตอนนี้:

- 07:00-09:00
- 19:00 เป็นต้นไป
- เสาร์-อาทิตย์หรือวันหยุดเหมาะกับไลฟ์ยาว 2-4 ชั่วโมง

ตารางตั้งต้น:

- เช้า 3 วัน: Golden Spatula
- เย็น 4 วัน: Soul Land เป็นหลัก สลับ LoL Wild Rift และ Naraka
- ศุกร์ เสาร์ อาทิตย์ควรกันเวลาบางส่วนไว้พัก ตัดคลิป และสรุปผล
- อ่านรายละเอียดที่ `03_live_operations/default-weekly-schedule-plan.md`

## 2. Daily Schedule

ใช้เมื่ออยากลดข้อมูลให้สั้นลง หรือประกาศเฉพาะวันนี้

รูปแบบแนะนำ:

```text
วันนี้ Live อะไร
เวลาเริ่ม
กิจกรรมหลัก
ช่องทาง
```

เหมาะกับกรณีลดเวลาไลฟ์ เพราะคนดูไม่ต้องอ่านทั้งสัปดาห์

## 3. Monthly Schedule

ใช้เป็น roadmap แบบกว้าง ไม่ควรลงรายละเอียดเวลาแน่นเกินไป

รูปแบบแนะนำ:

- สัปดาห์ที่ 1: Golden Spatula focus
- สัปดาห์ที่ 2: LoL Wild Rift focus
- สัปดาห์ที่ 3: ทดลอง format ใหม่
- สัปดาห์ที่ 4: สรุปผล / community event

## Reduced Live Time Rules

ถ้าจะลดเวลาไลฟ์ ให้ใช้กฎนี้:

- ระบุ slot ให้ชัด เช่น `07.00 - 09.00`
- ถ้ามี 2 รอบในวันเดียว ให้ขึ้นบรรทัดใหม่ในช่องเวลา
- ถ้างดช่วงเย็น ใช้ `-`
- ถ้าวันนั้นยังไม่แน่นอน ใช้ `รอติดตาม`
- อย่าใส่ note ยาวในภาพตาราง ให้ไปใส่ใน caption แทน

## Data Source

ข้อมูลตารางควรอยู่ใน:

```text
07_data/weekly-schedules/
```

ไฟล์ภาพ final ควรออกที่:

```text
08_outputs/schedules/
```
