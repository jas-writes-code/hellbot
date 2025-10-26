import re
from datetime import datetime, timezone
import json

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
            if objective == "2": # extract samples?
                content += "THIS MO TYPE IS NOT YET CONFIGURED!"
            elif objective == "3": # cull

                #lay out some variables to make the logic easier
                progress = element['progress'][element["tasks"].index(object)]
                planet = config[str(config['types'][str(object['valueTypes'][9])])][str(object['values'][9])]['name']

                content += f"{object['values'][2]} {config['enemies'][str(object['values'][0])]}"
                if object['values'][9] > 0:
                    content += f" on {planet}"
                content += f"\n*Progress: {progress}/{object['values'][2]} ({progress*100/object['values'][2]}%)*"
            elif objective == "7": # complete missions
                content += "THIS MO TYPE IS NOT YET CONFIGURED!"
            elif objective == "9": # complete operations
                content += "THIS MO TYPE IS NOT YET CONFIGURED!"
            elif objective == "11": # liberate
                content += config[str(config["types"][str(object["valueTypes"][2])])][str(object["values"][2])]["name"]
                if element["progress"][element["tasks"].index(object)] == 1:
                    content += " (:green_circle:)"
                else:
                    content += " (:red_circle:)"

            elif objective == "12": # defend
                content += "THIS MO TYPE IS NOT YET CONFIGURED!"
            elif objective == "13": # hold
                content += config[str(config["types"][str(object["valueTypes"][2])])][str(object["values"][2])]["name"]
                content += " when the order expires."
                if element["progress"][element["tasks"].index(object)] == 1:
                    content += " (:green_circle:)"
                else:
                    content += " (:red_circle:)"

            elif objective == "15":
                content += "THIS MO TYPE IS NOT YET CONFIGURED!"
            content += "\n"
        for object in element["rewards"]:
            content += f"Reward: {object['amount']} {config['rewards'][str(object['type'])]} | "
    return content
