# Automation

พื้นที่สำหรับ script, prompt และ config ที่ช่วยสร้างงานซ้ำ เช่น ปกไลฟ์ ตารางรายสัปดาห์ caption และรายงาน

## โครงสร้างแนะนำ

```text
scripts/   Python หรือเครื่องมือ automation
prompts/   prompt มาตรฐานสำหรับ AI
config/    ค่า config กลาง เช่น path, สี, ขนาดภาพ
```

## หลักการ

- AI ควรกรอกข้อมูลลง template ไม่ควรออกแบบใหม่ทุกครั้ง
- Layout ควรอ่านจาก JSON เพื่อควบคุมตำแหน่งให้คงที่
- Output ต้องถูกเก็บใน `08_outputs/`
