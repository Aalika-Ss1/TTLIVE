# SOP: Create Live Cover

## เป้าหมาย

สร้างปกไลฟ์ 16:9 ที่คุม layout และ brand ได้สม่ำเสมอ

## ขั้นตอน

1. เตรียม background, logo, character และ game icon ใน `04_assets/`
2. ใช้ layout จาก `05_templates/live-cover/layout.json`
3. ใส่ข้อมูลจริงโดยอ้างอิง `05_templates/live-cover/example-input.json`
4. Generate หรือประกอบภาพด้วย script ใน `06_automation/scripts/`
5. เก็บ output ใน `08_outputs/covers/`
6. ตรวจว่าข้อความอ่านได้บนมือถือ
