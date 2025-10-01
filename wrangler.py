import re
from datetime import datetime, timezone

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
