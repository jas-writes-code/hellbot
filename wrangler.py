import re
from datetime import datetime, timezone

async def retime(iso_str):
    if '.' in iso_str:
        parts = iso_str.split('.')
        frac = parts[1].rstrip('Z')[:6]  # take first 6 digits
        iso_str_fixed = f"{parts[0]}.{frac}Z"
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