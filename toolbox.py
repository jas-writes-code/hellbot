from datetime import datetime, timezone
import requests
import json
import wrangler

def retime(iso_str):
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

with open("key.json", "r") as file:
    info = json.load(file)

def fetch(input):
    response = requests.get(f"https://api.helldivers2.dev{input}", headers={"x-super-client": info["client"], "x-super-contact": info["mail"]})
    data = response.json()
    print(data)
    times = []
    for element in data:
        times += int(retime(element["published"]))
    times.sort(key=lambda p: p["published"])

print(retime("2024-03-13T13:44:53Z"))

fetch("/api/v1/dispatches")