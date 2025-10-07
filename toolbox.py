import requests
import json
import wrangler

with open("key.json", "r") as file:
    info = json.load(file)

def fetch(input):
    response = requests.get(f"https://api.helldivers2.dev{input}", headers={"x-super-client": info["client"], "x-super-contact": info["mail"]})
    data = response.json()
    for element in data:
        print(element)

fetch("/api/v1/assignments")