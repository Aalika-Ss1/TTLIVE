# TTLIVE System Map

แผนที่ระบบแบบย่อสำหรับดูว่าแต่ละส่วนเชื่อมกันอย่างไร

```text
Strategy
  -> Schedule
    -> Live Operation
      -> Report
      -> Clip Candidate
        -> Editing
          -> Upload
            -> Clip Performance
              -> Monthly Review

Brand
  -> Assets
    -> Templates
      -> Live Cover
      -> Schedule Image
      -> Starting Soon Image
      -> Offline / Recap Image
      -> In-Live Overlay

Data
  -> Automation
    -> Generated Outputs
      -> Posting / Live Use
```

## ระบบข้อมูลไหลอย่างไร

1. วางแผนใน `DASHBOARD.md`
2. สร้างตารางจาก `07_data/weekly-schedules/`
3. ใช้ template จาก `05_templates/`
4. เก็บ output ที่ `08_outputs/`
5. ไลฟ์ตาม checklist ใน `03_live_operations/`
6. หลังไลฟ์สรุปใน `09_reports/`
7. เอาช่วงดีไปตัดคลิป
8. เอาผลคลิปและผล live กลับมาปรับตารางรอบถัดไป

## จุดที่ต้องไม่ปนกัน

- `04_assets/` คือของต้นฉบับ
- `05_templates/` คือแม่แบบ
- `07_data/` คือข้อมูลที่เปลี่ยนรายสัปดาห์
- `08_outputs/` คือไฟล์ final
- `09_reports/` คือผลลัพธ์และบทเรียน

## หลักการตัดสินใจ

ถ้าสิ่งใหม่ไม่ช่วยเรื่อง live, clip, report, หรือการลดงานซ้ำ ให้เก็บไว้ทีหลัง
