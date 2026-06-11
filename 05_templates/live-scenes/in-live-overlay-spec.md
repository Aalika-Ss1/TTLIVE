# In-Live Overlay

ใช้กำหนด layout ระหว่างไลฟ์

## หลักการ

- ต้องไม่บัง gameplay
- ต้องไม่บัง chat หรือ UI สำคัญของเกม
- ใช้เฉพาะข้อมูลที่ช่วยคนดู

## องค์ประกอบที่ควรมี

- Logo เล็ก
- ชื่อช่องหรือ handle
- หัวข้อไลฟ์สั้นๆ
- กล่องแจ้งกิจกรรม เช่น เล่นกับคนดู / ไต่แรงค์ / รีวิวแพตช์

## Layout Zones

```text
top-left      logo / handle
top-right     event tag
bottom-left   small status
bottom-right  optional alert
center        ห้ามวางของถาวร
```

## ข้อควรระวัง

- เกมมือถือมี UI หลายจุด ต้องทดสอบจาก screenshot จริง
- ถ้าบัง gameplay ให้ลด overlay ก่อนเพิ่มความสวย
