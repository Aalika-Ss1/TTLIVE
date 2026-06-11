# TTLIVE

TTLIVE คือ repository กลางสำหรับจัดการงาน TikTok Live แบบเป็นระบบ ตั้งแต่แบรนด์ ตารางไลฟ์ ปกไลฟ์ asset, template, automation, รายงานผล และคู่มือการทำงานของทีม

เป้าหมายของ repo นี้คือทำให้งานไลฟ์ทำซ้ำได้เร็วขึ้น คุมมาตรฐานได้ดีขึ้น และขยายเป็นทีมหลายคนหรือหลายโปรเจกต์ได้โดยไม่สับสน

## โครงสร้างหลัก

```text
00_company/          ภาพรวมทีม บทบาท workflow และการตัดสินใจ
01_brand/            มาตรฐานแบรนด์ สี ฟอนต์ น้ำเสียง โลโก้
02_content/          ไอเดีย สคริปต์ caption hashtag campaign
03_live_operations/  ตารางไลฟ์ checklist runbook และคู่มือ moderator
04_assets/           ไฟล์ต้นฉบับ เช่น logo background icon font overlay
05_templates/        แม่แบบปกไลฟ์ ตารางโพสต์ caption และ layout
06_automation/       script, prompt, config สำหรับระบบอัตโนมัติ
07_data/             ข้อมูลกลางที่ script และ AI อ่านได้
08_outputs/          ไฟล์ final ที่พร้อมใช้งาน
09_reports/          รายงานผล weekly/monthly และ experiment
10_archive/          ของเก่าที่เลิกใช้แต่ยังเก็บอ้างอิง
11_sop/              ขั้นตอนการทำงานซ้ำ
12_legal/            license, sponsor, music และข้อควรระวัง
13_community/        กฎแชท คู่มือ moderator และกิจกรรมคนดู
14_monetization/     sponsor package, rate card, affiliate, donation
projects/            โปรเจกต์แยกตามเกม แคมเปญ หรือรูปแบบรายการ
```

## วิธีเริ่มทำงาน

1. เปิด `DASHBOARD.md` เพื่อดูงานประจำสัปดาห์
2. วางตารางไลฟ์ใน `03_live_operations/schedules/`
3. ใช้ template จาก `05_templates/` เพื่อทำโพสต์หรือปกไลฟ์
4. เก็บ asset ต้นฉบับใน `04_assets/`
5. เก็บไฟล์พร้อมใช้ใน `08_outputs/`
6. สรุปผลหลังไลฟ์ใน `09_reports/`

## กฎสำคัญ

- ห้ามเก็บ password, token, stream key หรือข้อมูลลับลง GitHub
- ไฟล์วิดีโอขนาดใหญ่ควรเก็บใน cloud storage เช่น OneDrive/Google Drive แล้วใส่ link อ้างอิง
- งานทดลองควรแยกไว้ใน `projects/` หรือ `09_reports/experiments/`
- ชื่อไฟล์ต้องอ่านแล้วรู้ว่าเป็นงานอะไร วันที่เท่าไร และใช้กับ platform ไหน
