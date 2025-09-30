import requests
import json

def efetch(input):
    response = requests.get(f"https://api.helldivers2.dev{input}", headers={"x-super-client": "virgildoesthings.com", "x-super-contact": "virgil@virgildoesthings.com"})
    if response.status_code != 200:
        raise ValueError(f"Request failed with status {response.status_code}")
    return response

async def fetch(input):
    with open('log.json', 'r') as f:
        try:
            info = json.load(f)
        except json.decoder.JSONDecodeError:
            pass
    try:
        stream = efetch(input).json()
    except ValueError as e:
        status_code = e.args[0]  # recover the status code you passed
        return "Error", status_code
    if type(stream) == dict:
        return stream, 9
    elif type(stream) == list:
        state = 8
        item = input.split("/")[-1]
        if item not in info:
            info[item] = {"id": stream[0]["id"]}
            state = 18
        if stream:
            if stream[0]["id"] != info[item]["id"]:
                state = 28 * stream[0]["id"]
                info[item]["id"] = stream[0]["id"]
        else:
            stream = ""
            state = 38

        with open("log.json", "w") as f:
            json.dump(info, f, indent=4)
        return stream, state
    else:
        return stream, 0