import requests

def fetch(input):
    response = requests.get(f"https://api.helldivers2.dev{input}", headers={"x-super-client": "virgildoesthings.com", "x-super-contact": "virgil@virgildoesthings.com"}).text
    print(response)

fetch("/api/v1/assignments")