# วิธีทำงานกับ Repo TTLIVE

## Branch

- `main` ใช้เก็บงานที่ผ่านมาตรฐานและพร้อมใช้งาน
- งานทดลองให้แยก branch หรือเก็บใน `projects/` พร้อมบอกสถานะให้ชัด

## Commit Message

ใช้รูปแบบสั้นและอ่านรู้เรื่อง:

```text
type: summary
```

ตัวอย่าง:

```text
docs: add weekly schedule template
assets: add wild rift icon
automation: add cover layout config
```

## ห้าม Commit

- password
- token
- stream key
- private key
- ไฟล์วิดีโอขนาดใหญ่
- ไฟล์ชั่วคราว เช่น `final-final-new.png`

## ชื่อไฟล์

ใช้รูปแบบ:

```text
YYYY-MM-DD_project_platform_type_v01.ext
```

ตัวอย่าง:

```text
2026-06-15_wild-rift_tiktok_cover_v01.png
2026-W25_weekly-schedule_discord_post_v01.md
```
