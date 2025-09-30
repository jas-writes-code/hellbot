import requests
import json

def efetch(input):
    response = requests.get(f"https://api.helldivers2.dev{input}", headers={"x-super-client": "virgildoesthings.com", "x-super-contact": "virgil@virgildoesthings.com"})

    if not response:
        return "404 Not Found"
    else:
        return response

async def fetch(input):
    with open('log.json', 'r') as f:
        try:
            info = json.load(f)
        except json.decoder.JSONDecodeError:
            pass
    stream = efetch(input).json()
    if type(stream) == dict:
        return stream, 9
    elif type(stream) == list:
        state = 8
        item = input.split("/")[-1]
        if item not in info:
            info[item] = {"id": stream[0]["id"]}
            state = 18
        if stream[0]["id"] != info[item]["id"]:
            info[item]["id"] = stream[0]["id"]
            state = 28

        with open("log.json", "w") as f:
            json.dump(info, f, indent=4)
        return stream, state
    else:
        return stream, 0