import re
from datetime import datetime, timezone
import json
from info import info

with open('config.json', 'r') as f:
    config = json.load(f)

async def retime(iso_str):
    if '.' in iso_str:
        parts = iso_str.split('.')
        frac = parts[1].rstrip('Z')[:6]  # take first 6 digits
        iso_str_fixed = f"{parts[0]}.{frac}Z"
        fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
    else:
        iso_str_fixed = iso_str
        fmt = "%Y-%m-%dT%H:%M:%SZ"

    dt = datetime.strptime(iso_str_fixed, fmt)
    return dt.replace(tzinfo=timezone.utc).timestamp()

async def sanitize(content: str) -> str:
    # Replace <i=3>...</i> with bold (**text**)
    content = re.sub(r"<i=3>(.*?)</i>", r"**\1**", content)

    # Replace <i=1>...</i> with italics (*text*)
    content = re.sub(r"<i=1>(.*?)</i>", r"*\1*", content)

    return content

def thatstoolong(text: str, limit: int = 1900) -> list[str]:
    chunks = []
    remaining = text

    while len(remaining) > limit:
        # Try to split at the last double newline before limit
        split_index = remaining.rfind("\n\n", 0, limit)
        if split_index != -1:
            split_index += 2  # include the "\n\n"
            chunks.append(remaining[:split_index])
            remaining = remaining[split_index:]
            continue

        # If no "\n\n" found, try splitting at the last space before limit
        split_index = remaining.rfind(" ", 0, limit)
        if split_index != -1:
            chunks.append(remaining[:split_index])
            remaining = remaining[split_index + 1:]
            continue

        # As a last resort, hard cut
        chunks.append(remaining[:limit])
        remaining = remaining[limit:]

    # Add whatever is left
    if remaining:
        chunks.append(remaining)

    return chunks

async def mo_processing(orders):
    content = ""
    for element in orders:
        for object in element["tasks"]:
            objective = str(object["type"])
            content += f'{config["tasks"][objective]} '
            for value in object["valueTypes"]:
                if value == "3":
                    content += f" {object['values'][str(object['valueTypes'].index(value))]}"
                if value == "1":
                    content += f" {config['race'][str(object['values'].index(value))]}"
                if value == "2":
                    content += f" {config['enemies'][str(object['values'].index(value))]}"
                if value == "12":
                    content += "on" if objective != "11" else ""
                    content += f" {info.planets.planets[str(object['values'].index(value))]['name']}"
                if value == "5":
                    content += f" using {info.items.item_names[str(object['values'].index(object['valueTypes'][value]))]['name']}"


        for object in element["rewards"]:
            content += f"Reward: {object['amount']} {config['rewards'][str(object['type'])]} | "

    return content



async def megacities(planet):
    content = ""
    for city in planet['regions']:
        name = city.get('name') or "*Unknown Megacity*"
        available = city.get('isAvailable', False)
        health = city.get('health', 0)
        max_health = city.get('maxHealth', 1)
        phealth = planet.get('health', 0)
        pmhealth = planet.get('maxHealth', 1)
        avail_factor = city.get('availabilityFactor', 1)
        players = city.get('players', 0)

        degree = 1 - (phealth / pmhealth)

        # City availability string
        # Calculate liberation percentage for display
        lib_percent = (health * 100 / max_health)
        print(lib_percent, degree, avail_factor)

        status = ""
        # Determine city state
        if available:
            status = f"(available since {100 - (avail_factor * 100):.1f}% -- {players} players)"
        elif health == max_health and avail_factor <= degree:
            # City liberated
            status = f"(liberated; unlocked at {100 - (avail_factor * 100):.1f}%)"
        elif health == max_health and avail_factor > degree:
            # City unavailable
            status = f"(unavailable; unlocks at {100 - (avail_factor * 100):.1f}%)"
        else: status = "locked"

        # Display city information
        content += f"\n**{name}** {status}"
        content += f"\n{health}/{max_health} **({lib_percent:.1f}% liberated)**"

    return content