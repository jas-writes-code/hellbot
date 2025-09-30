import requests
import json


def efetch(input):
    response = requests.get(f"https://api.helldivers2.dev{input}", headers={"x-super-client": "virgildoesthings.com", "x-super-contact": "virgil@virgildoesthings.com"})
    if not response:
        return "404 Not Found"
    else:
        return response

def fetch(input):
    stream = efetch(input).json()
    if type(stream) == dict:
        return stream, 1
    elif type(stream) == list:
        return stream, 2
    else:
        return stream, 0