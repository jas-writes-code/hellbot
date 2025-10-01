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
    paragraphs = text.split("\n\n")  # keep paragraphs first

    for para in paragraphs:
        if len(para) <= limit:
            # paragraph fits -> push directly
            chunks.append(para)
        else:
            words = para.split(" ")
            current = ""
            for word in words:
                if len(current) + len(word) + 1 > limit:
                    chunks.append(current)
                    current = word
                else:
                    current += (" " if current else "") + word

            if current:
                chunks.append(current)

    # final safeguard: hard-split anything that still exceeds limit
    final_chunks = []
    for chunk in chunks:
        if len(chunk) > limit:
            for i in range(0, len(chunk), limit):
                final_chunks.append(chunk[i:i+limit])
        else:
            final_chunks.append(chunk)

    return final_chunks