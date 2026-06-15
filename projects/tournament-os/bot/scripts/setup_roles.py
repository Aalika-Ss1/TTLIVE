import argparse
import asyncio
import os

import disnake


THAI_ROLES = {
    "member": "\u0e2a\u0e21\u0e32\u0e0a\u0e34\u0e01",
    "viewer": "\u0e1c\u0e39\u0e49\u0e0a\u0e21",
    "interested_player": "\u0e2a\u0e19\u0e43\u0e08\u0e2a\u0e21\u0e31\u0e04\u0e23\u0e41\u0e02\u0e48\u0e07",
    "pending_player": "\u0e23\u0e2d\u0e15\u0e23\u0e27\u0e08\u0e2a\u0e2d\u0e1a",
    "tournament_player": "\u0e1c\u0e39\u0e49\u0e40\u0e02\u0e49\u0e32\u0e41\u0e02\u0e48\u0e07\u0e02\u0e31\u0e19",
    "checked_in": "\u0e40\u0e0a\u0e47\u0e04\u0e2d\u0e34\u0e19\u0e41\u0e25\u0e49\u0e27",
    "qualified": "\u0e40\u0e02\u0e49\u0e32\u0e23\u0e2d\u0e1a",
    "caster": "\u0e19\u0e31\u0e01\u0e1e\u0e32\u0e01\u0e22\u0e4c",
    "staff_applicant": "\u0e2a\u0e21\u0e31\u0e04\u0e23\u0e17\u0e35\u0e21\u0e07\u0e32\u0e19",
    "score_admin": "\u0e1c\u0e39\u0e49\u0e14\u0e39\u0e41\u0e25\u0e04\u0e30\u0e41\u0e19\u0e19",
    "referee": "\u0e01\u0e23\u0e23\u0e21\u0e01\u0e32\u0e23",
    "tournament_admin": "\u0e41\u0e2d\u0e14\u0e21\u0e34\u0e19\u0e17\u0e31\u0e27\u0e23\u0e4c\u0e19\u0e32\u0e40\u0e21\u0e19\u0e15\u0e4c",
}


ROLE_POLICY = [
    {
        "key": "member",
        "label": "Member",
        "color": disnake.Color.light_grey(),
        "hoist": False,
        "mentionable": False,
    },
    {
        "key": "viewer",
        "label": "Viewer",
        "color": disnake.Color.light_grey(),
        "hoist": False,
        "mentionable": False,
    },
    {
        "key": "interested_player",
        "label": "Interested Player",
        "color": disnake.Color.teal(),
        "hoist": False,
        "mentionable": True,
    },
    {
        "key": "pending_player",
        "label": "Pending Player",
        "color": disnake.Color.blurple(),
        "hoist": True,
        "mentionable": True,
    },
    {
        "key": "tournament_player",
        "label": "Tournament Player",
        "color": disnake.Color.blue(),
        "hoist": True,
        "mentionable": True,
    },
    {
        "key": "checked_in",
        "label": "Checked In",
        "color": disnake.Color.green(),
        "hoist": True,
        "mentionable": True,
    },
    {
        "key": "qualified",
        "label": "Qualified",
        "color": disnake.Color.gold(),
        "hoist": True,
        "mentionable": True,
    },
    {
        "key": "caster",
        "label": "Caster",
        "color": disnake.Color.purple(),
        "hoist": True,
        "mentionable": False,
    },
    {
        "key": "staff_applicant",
        "label": "Staff Applicant",
        "color": disnake.Color.dark_grey(),
        "hoist": False,
        "mentionable": False,
    },
    {
        "key": "score_admin",
        "label": "Score Admin",
        "color": disnake.Color.orange(),
        "hoist": True,
        "mentionable": True,
    },
    {
        "key": "referee",
        "label": "Referee",
        "color": disnake.Color.orange(),
        "hoist": True,
        "mentionable": True,
    },
    {
        "key": "tournament_admin",
        "label": "Tournament Admin",
        "color": disnake.Color.red(),
        "hoist": True,
        "mentionable": True,
    },
]


async def get_roles(guild):
    if hasattr(guild, "fetch_roles"):
        return await guild.fetch_roles()
    return list(getattr(guild, "roles", []))


async def setup_roles(apply: bool) -> None:
    token = os.getenv("DISCORD_TOKEN")
    guild_id = os.getenv("DISCORD_GUILD_ID") or os.getenv("TOURNAMENT_GUILD_ID")
    if not token:
        raise SystemExit("DISCORD_TOKEN is not set.")
    if not guild_id:
        raise SystemExit("DISCORD_GUILD_ID or TOURNAMENT_GUILD_ID is not set.")

    intents = disnake.Intents.default()
    client = disnake.Client(intents=intents)

    @client.event
    async def on_ready():
        try:
            guild = client.get_guild(int(guild_id))
            if guild is None:
                guild = await client.fetch_guild(int(guild_id))

            print(f"Guild: {guild.name} ({guild.id})")
            existing_roles = {role.name: role for role in await get_roles(guild)}

            for spec in ROLE_POLICY:
                role_name = THAI_ROLES[spec["key"]]
                role = existing_roles.get(role_name)
                if role:
                    print(f"EXISTS  {role_name} ({spec['label']})")
                    continue

                if not apply:
                    print(f"MISSING {role_name} ({spec['label']})")
                    continue

                created = await guild.create_role(
                    name=role_name,
                    color=spec["color"],
                    hoist=spec["hoist"],
                    mentionable=spec["mentionable"],
                    reason="Tournament OS role policy setup",
                )
                print(f"CREATED {created.name} ({spec['label']})")
        finally:
            await client.close()

    await client.start(token)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create Tournament OS Discord roles.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Create missing roles. Without this flag the script only reports missing roles.",
    )
    args = parser.parse_args()
    asyncio.run(setup_roles(apply=args.apply))


if __name__ == "__main__":
    main()
