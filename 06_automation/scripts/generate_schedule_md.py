from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict | list:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def game_lookup(games: list[dict]) -> dict[str, dict]:
    return {game["id"]: game for game in games}


def build_markdown(schedule: dict, games_by_id: dict[str, dict]) -> str:
    title = f"# ตาราง Live ประจำสัปดาห์ {schedule['date_range']}"
    lines = [
        title,
        "",
        f"Theme: {schedule.get('theme', '-')}",
        "",
        "| วัน | เวลา | เกม/หัวข้อ | หมายเหตุ / กิจกรรมพิเศษ |",
        "| :---: | :---: | :--- | :--- |",
    ]

    for item in schedule["items"]:
        game = games_by_id.get(item.get("game_id", ""), {})
        topic = item.get("topic") or game.get("name", "-")
        lines.append(
            f"| {item['day']} | {item['time']} | {topic} | {item.get('note', '-')} |"
        )

    hashtags = " ".join(schedule.get("hashtags", []))
    platforms = ", ".join(schedule.get("platforms", []))

    lines.extend(
        [
            "",
            "## Caption",
            "",
            schedule.get("caption", ""),
            "",
            "## Hashtags",
            "",
            hashtags,
            "",
            "## Platforms",
            "",
            platforms,
            "",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate weekly schedule Markdown.")
    parser.add_argument("schedule", help="Path to weekly schedule JSON.")
    parser.add_argument(
        "--output",
        help="Output Markdown path. Defaults to 08_outputs/schedules/<week>_schedule.md",
    )
    args = parser.parse_args()

    schedule_path = (ROOT / args.schedule).resolve()
    schedule = load_json(schedule_path)
    games = load_json(ROOT / "07_data/games.json")
    markdown = build_markdown(schedule, game_lookup(games))

    output_path = (
        (ROOT / args.output).resolve()
        if args.output
        else ROOT / "08_outputs/schedules" / f"{schedule['week']}_schedule.md"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    print(f"Generated {output_path}")


if __name__ == "__main__":
    main()
