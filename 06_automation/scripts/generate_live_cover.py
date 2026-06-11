from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def resolve_asset(path_value: str | None) -> Path | None:
    if not path_value:
        return None
    path = ROOT / path_value
    return path if path.exists() else None


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/tahoma.ttf"),
        Path("C:/Windows/Fonts/tahomabd.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/seguiemj.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def fit_text(draw: ImageDraw.ImageDraw, text: str, max_width: int, start_size: int) -> ImageFont.ImageFont:
    size = start_size
    while size > 24:
        current_font = font(size)
        box = draw.textbbox((0, 0), text, font=current_font)
        if box[2] - box[0] <= max_width:
            return current_font
        size -= 4
    return font(size)


def paste_fit(base: Image.Image, asset_path: Path, box: dict) -> None:
    image = Image.open(asset_path).convert("RGBA")
    image.thumbnail((box["width"], box["height"]))
    x = box["x"] + (box["width"] - image.width) // 2
    y = box["y"] + (box["height"] - image.height) // 2
    base.alpha_composite(image, (x, y))


def draw_placeholder(draw: ImageDraw.ImageDraw, box: dict, label: str, outline: str) -> None:
    x1 = box["x"]
    y1 = box["y"]
    x2 = x1 + box["width"]
    y2 = y1 + box["height"]
    draw.rounded_rectangle((x1, y1, x2, y2), radius=24, outline=outline, width=4)
    label_font = font(36)
    text_box = draw.textbbox((0, 0), label, font=label_font)
    tx = x1 + (box["width"] - (text_box[2] - text_box[0])) // 2
    ty = y1 + (box["height"] - (text_box[3] - text_box[1])) // 2
    draw.text((tx, ty), label, fill=outline, font=label_font)


def create_background(width: int, height: int) -> Image.Image:
    image = Image.new("RGBA", (width, height), "#111111")
    draw = ImageDraw.Draw(image)
    for y in range(height):
        ratio = y / height
        red = int(17 + 60 * ratio)
        green = int(17 + 10 * ratio)
        blue = int(17 + 50 * (1 - ratio))
        draw.line((0, y, width, y), fill=(red, green, blue, 255))
    return image


def draw_text_block(
    draw: ImageDraw.ImageDraw,
    text: str,
    box: dict,
    size: int,
    color: str,
) -> None:
    text_font = fit_text(draw, text, box["width"], size)
    text_box = draw.textbbox((0, 0), text, font=text_font)
    text_width = text_box[2] - text_box[0]
    text_height = text_box[3] - text_box[1]

    if box.get("align") == "center":
        x = box["x"] + (box["width"] - text_width) // 2
    else:
        x = box["x"]
    y = box["y"] + (box["height"] - text_height) // 2

    shadow_offset = 4
    draw.text((x + shadow_offset, y + shadow_offset), text, fill="#000000", font=text_font)
    draw.text((x, y), text, fill=color, font=text_font)


def generate(input_path: Path, output_override: str | None = None) -> Path:
    data = load_json(input_path)
    layout = load_json(ROOT / "05_templates/live-cover/layout.json")
    canvas = layout["canvas"]

    background_path = resolve_asset(data.get("background"))
    if background_path:
        image = Image.open(background_path).convert("RGBA").resize(
            (canvas["width"], canvas["height"])
        )
    else:
        image = create_background(canvas["width"], canvas["height"])

    draw = ImageDraw.Draw(image)

    character_path = resolve_asset(data.get("character"))
    if character_path:
        paste_fit(image, character_path, layout["character_box"])
    else:
        draw_placeholder(draw, layout["character_box"], "CHARACTER", "#00E5FF")

    game_icon_path = resolve_asset(data.get("game_icon"))
    if game_icon_path:
        paste_fit(
            image,
            game_icon_path,
            {
                "x": layout["game_icon"]["x"],
                "y": layout["game_icon"]["y"],
                "width": layout["game_icon"]["width"],
                "height": layout["game_icon"]["width"],
            },
        )
    else:
        draw_placeholder(
            draw,
            {
                "x": layout["game_icon"]["x"],
                "y": layout["game_icon"]["y"],
                "width": layout["game_icon"]["width"],
                "height": layout["game_icon"]["width"],
            },
            "GAME",
            "#FF2D55",
        )

    logo_path = resolve_asset(data.get("logo"))
    logo_box = {
        "x": layout["logo"]["x"],
        "y": layout["logo"]["y"],
        "width": layout["logo"]["width"],
        "height": layout["logo"]["width"],
    }
    if logo_path:
        paste_fit(image, logo_path, logo_box)
    else:
        draw.rounded_rectangle(
            (
                logo_box["x"],
                logo_box["y"],
                logo_box["x"] + logo_box["width"],
                logo_box["y"] + logo_box["height"],
            ),
            radius=18,
            fill="#FF2D55",
        )
        draw.text((logo_box["x"] + 28, logo_box["y"] + 64), "TTLIVE", fill="#FFFFFF", font=font(30))

    draw_text_block(
        draw,
        data["headline"],
        layout["headline"],
        layout["headline"]["font_size"],
        layout["headline"]["color"],
    )
    draw_text_block(
        draw,
        data["subtitle"],
        layout["subtitle"],
        layout["subtitle"]["font_size"],
        layout["subtitle"]["color"],
    )

    output_path = ROOT / (output_override or data["output"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(output_path, quality=95)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a TTLIVE live cover image.")
    parser.add_argument(
        "input",
        nargs="?",
        default="05_templates/live-cover/example-input.json",
        help="Input JSON path.",
    )
    parser.add_argument("--output", help="Override output path.")
    args = parser.parse_args()

    output_path = generate(ROOT / args.input, args.output)
    print(f"Generated {output_path}")


if __name__ == "__main__":
    main()
