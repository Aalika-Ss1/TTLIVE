from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict | list:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/tahomabd.ttf") if bold else Path("C:/Windows/Fonts/tahoma.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf") if bold else Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/seguiemj.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def text_center(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    fill: str,
    size: int,
    bold: bool = False,
    spacing: int = 4,
) -> None:
    lines = text.split("\n")
    current_font = font(size, bold)
    line_boxes = [draw.textbbox((0, 0), line, font=current_font) for line in lines]
    line_heights = [bbox[3] - bbox[1] for bbox in line_boxes]
    total_height = sum(line_heights) + spacing * (len(lines) - 1)
    y = box[1] + ((box[3] - box[1]) - total_height) // 2

    for line, bbox, line_height in zip(lines, line_boxes, line_heights):
        text_width = bbox[2] - bbox[0]
        x = box[0] + ((box[2] - box[0]) - text_width) // 2
        draw.text((x, y), line, fill=fill, font=current_font)
        y += line_height + spacing


def draw_background(draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
    for y in range(height):
        ratio = y / height
        r = int(245 - ratio * 20)
        g = int(228 + ratio * 10)
        b = int(255 - ratio * 30)
        draw.line((0, y, width, y), fill=(r, g, b))

    # Decorative swirls and clouds, intentionally simple so real assets can replace them later.
    for offset, color in [(0, "#B8E6FF"), (60, "#F6B8D6"), (120, "#B8F0D2")]:
        draw.arc((-180 + offset, 40 + offset, 360 + offset, 520 + offset), 280, 80, fill=color, width=8)
        draw.arc((700 - offset, 520 - offset, 1260 - offset, 1040 - offset), 100, 260, fill=color, width=8)

    for x, y in [(40, 920), (145, 965), (870, 940), (980, 900)]:
        draw.ellipse((x, y, x + 170, y + 70), fill="#FFF4CE", outline="#D8B46A", width=3)


def draw_table(image: Image.Image, schedule: dict, layout: dict) -> None:
    draw = ImageDraw.Draw(image)
    card = layout["card"]
    x0 = card["x"]
    y0 = card["y"]
    width = card["width"]
    header_h = layout["header"]["height"]
    row_h = (card["height"] - header_h) // len(schedule["items"])

    # Scroll-like panel.
    draw.rounded_rectangle(
        (x0 - 35, y0 - 48, x0 + width + 35, y0 + card["height"] + 48),
        radius=36,
        fill="#C98B2F",
        outline="#8B5A1D",
        width=4,
    )
    draw.rounded_rectangle(
        (x0, y0, x0 + width, y0 + card["height"]),
        radius=18,
        fill="#FFF3C7",
        outline="#B58B3A",
        width=4,
    )

    # Decorative rollers.
    draw.rounded_rectangle((x0 - 80, y0 - 70, x0 + width + 80, y0 - 24), radius=24, fill="#E6B64E", outline="#8B5A1D", width=4)
    draw.rounded_rectangle((x0 - 80, y0 + card["height"] + 24, x0 + width + 80, y0 + card["height"] + 70), radius=24, fill="#E6B64E", outline="#8B5A1D", width=4)

    title_box = (90, 28, 990, 80)
    text_center(draw, title_box, schedule["title"], "#5C3B18", 36, True)
    text_center(draw, (90, 82, 990, 122), schedule["date_range"], "#5C3B18", 22, True)

    columns = layout["columns"]
    x = x0
    for column in columns:
        next_x = x + column["width"]
        draw.line((next_x, y0, next_x, y0 + card["height"]), fill="#C9A35A", width=2)
        text_center(draw, (x, y0 + 8, next_x, y0 + header_h - 8), column["label"], "#3A2414", 26, True)
        x = next_x
    draw.line((x0, y0 + header_h, x0 + width, y0 + header_h), fill="#B58B3A", width=3)

    day_colors = layout["day_colors"]
    for index, item in enumerate(schedule["items"]):
        row_top = y0 + header_h + index * row_h
        row_bottom = row_top + row_h
        draw.line((x0, row_bottom, x0 + width, row_bottom), fill="#D2B36F", width=2)

        x = x0
        day_w = columns[0]["width"]
        draw.rounded_rectangle(
            (x + 8, row_top + 7, x + day_w - 8, row_bottom - 7),
            radius=10,
            fill=day_colors.get(item["day_en"], "#EEEEEE"),
        )
        text_center(
            draw,
            (x + 8, row_top + 7, x + day_w - 8, row_bottom - 7),
            f"{item['day_th']}\n{item['day_en']}",
            "#25170E",
            24,
            True,
        )

        x += day_w
        game_w = columns[1]["width"]
        game_color = "#6A3FE2" if item["game_id"] == "wild-rift" else "#C8841E"
        if item["game_id"] in {"break", "follow"}:
            game_color = "#555555"
        draw.ellipse((x + 18, row_top + 28, x + 62, row_top + 72), fill=game_color)
        text_center(draw, (x + 70, row_top + 8, x + game_w - 8, row_bottom - 8), item["game_label"], "#25170E", 24, True)

        x += game_w
        morning_w = columns[2]["width"]
        text_center(draw, (x + 4, row_top + 8, x + morning_w - 4, row_bottom - 8), item["morning"], "#25170E", 23, False)

        x += morning_w
        evening_w = columns[3]["width"]
        text_center(draw, (x + 4, row_top + 8, x + evening_w - 4, row_bottom - 8), item["evening"], "#25170E", 23, False)


def generate(schedule_path: Path, output_override: str | None = None) -> Path:
    schedule = load_json(schedule_path)
    layout = load_json(ROOT / "05_templates/weekly-schedule/stream-table-layout.json")
    canvas = layout["canvas"]
    image = Image.new("RGB", (canvas["width"], canvas["height"]), "#F7E9FF")
    draw = ImageDraw.Draw(image)
    draw_background(draw, canvas["width"], canvas["height"])
    draw_table(image, schedule, layout)

    output_path = ROOT / (output_override or schedule["output"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, quality=95)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate TTLIVE weekly schedule image.")
    parser.add_argument(
        "schedule",
        nargs="?",
        default="07_data/weekly-schedules/2026-W24_stream-table.json",
        help="Schedule JSON path.",
    )
    parser.add_argument("--output", help="Override output path.")
    args = parser.parse_args()

    output_path = generate(ROOT / args.schedule, args.output)
    print(f"Generated {output_path}")


if __name__ == "__main__":
    main()
