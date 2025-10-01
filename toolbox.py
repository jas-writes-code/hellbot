import requests
import json

with open("key.json", "r") as file:
    info = json.load(file)

def fetch(input):
    response = requests.get(f"https://api.helldivers2.dev{input}", headers={"x-super-client": info["client"], "x-super-contact": info["mail"]})
    data = response.json()
    print(data["statistics"]["playerCount"])
fetch("/api/v1/war")