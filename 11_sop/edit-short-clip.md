# SOP: Edit Short Clip

## เป้าหมาย

ตัดคลิปจากไลฟ์ให้เร็วและสม่ำเสมอ โดยไม่ทำให้งานหนักเกินไป

## Input

- live recording หรือ replay
- clip candidate จาก `02_content/clips/clip-candidate-log.md`
- caption idea

## ขั้นตอน

1. เลือก clip candidate ที่ชัดที่สุด
2. ตัดเฉพาะช่วงที่มีเหตุการณ์หรือคำพูดน่าสนใจ
3. ความยาวเริ่มต้น 20-60 วินาที
4. ตัด dead air ออก
5. ใส่ subtitle เฉพาะจุดสำคัญถ้าทำทัน
6. ใส่ hook ช่วงแรก
7. export เป็นไฟล์แนวตั้งสำหรับ TikTok ถ้าคลิปเหมาะกับ short form
8. ตั้งชื่อไฟล์ตามมาตรฐาน

## Output

ชื่อไฟล์แนะนำ:

```text
YYYY-MM-DD_game_tiktok_clip_v01.mp4
```

วิดีโอขนาดใหญ่ไม่ควรเก็บใน Git ให้เก็บใน cloud storage แล้วใส่ link ใน report

## Quality Check

- [ ] 3 วินาทีแรกน่าสนใจ
- [ ] เสียงฟังรู้เรื่อง
- [ ] ไม่มีช่วงเงียบนาน
- [ ] มี context พอเข้าใจ
- [ ] ไม่มีข้อมูลส่วนตัวหรือข้อความเสี่ยง
