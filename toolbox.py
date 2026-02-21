from datetime import datetime, timezone
import requests
import json
import wrangler
from info import info

with open("forecastlog.json", "r") as f:
    flog = json.load(f)

for category in flog:
    for item in flog[category]:
        if len(flog[category][item]) == 0:
            print(item)