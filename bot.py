from discord.ext import tasks
from discord import *
import hellmonitor, wrangler
import json

client = Client(intents=Intents.all())
with open("key.json", "r") as file:
    info = json.load(file)
key = info["key"]
error_message = None

@tasks.loop(minutes=1)
async def monitor():
    global error_message
    target = client.get_channel(int(info["news"]))
    test, state = await hellmonitor.fetch("/api/v1/assignments")
    if test == "Error":
        if error_message:
            await error_message.delete()
        error_message = await target.send(f"An Error occured. {state}")
        return
    if int(state) % 28 == 0:
        await major_order(target)
    test, state = await hellmonitor.fetch("/api/v1/dispatches")
    if test == "Error":
        if error_message:
            await error_message.delete()
        error_message = await target.send(f"An Error occured. {state}")
        return
    if int(state) % 28 == 0:
        await dispatch(target)

async def prio(channel):
    async with channel.typing():
        content = "**High-Priority planet status:**\n\n"
        prios = []
        war, discard = await hellmonitor.fetch("/api/v1/war")
        if type(war) == tuple:
            await channel.send(f"An Error occured. (Status code {war[1]})")
            return
        players = war["statistics"]["playerCount"]
        planets, discard = await hellmonitor.fetch("/api/v1/planets")
        for planet in planets:
            if planet["statistics"]["playerCount"] > players / 21:
                prios.append(planet)
        prios.sort(key=lambda p: p["statistics"]["playerCount"], reverse=True)
        for element in prios[:5]:
            content += f"**{element['name']}** ({element['currentOwner']})\n"
            content += f"*{element['statistics']['playerCount']}* players active ({int(element['statistics']['playerCount'] * 100 / players)}% of total)\n"
            content += f"{element['health']}/{element['maxHealth']} **({100-(element['health']*100/element['maxHealth'])}% liberated)**\n"
            try:
                content += "\n*Megacity status:*\n"
                for city in element['regions']:
                    if city['isAvailable']:
                        if city['name']:
                            content += f"**{city['name']}** "
                        elif not city['name']:
                            content += f"*Unknown Megacity* "
                        content += f"(available since {100 - (city['availabilityFactor'] * 100)}% -- {city['players']} players)\n"
                    else:
                        if city['name']:
                            content += f"**{city['name']}** "
                        elif not city['name']:
                            content += f"*Unknown Megacity* "
                        content += f"(unavailable; unlocks at {100 - (city['availabilityFactor'] * 100)}%)\n"
                    content += f"{city['health']}/{city['maxHealth']} **({100 - (city['health'] * 100 / city['maxHealth'])}% liberated)**\n"
            except KeyError:
                pass
            content += "\n\n"
        content += f'*{war["statistics"]["playerCount"]} players online*'
    try:
        await channel.send(content)
    except errors.HTTPException:
        messages = wrangler.thatstoolong(content)
        for item in messages:
            await channel.send(item)

async def major_order(channel):
    async with channel.typing():
        content = ""
        mo, mostate = await hellmonitor.fetch("/api/v1/assignments")
        briefing, brstate = await hellmonitor.fetch("/raw/api/WarSeason/801/Status")
        briefing = briefing["globalEvents"]
        for event in briefing:
            briefing_title = await wrangler.sanitize(event["title"])
            briefing_content = await wrangler.sanitize(event["message"])
            content += f"\n\nBriefing: **{briefing_title}** (*Due <t:{1707696000 + int(event['expireTime'])}:R>*)\n\n{briefing_content}"
        if mostate == 48:
            content += f"\n\n*No currently active Major Order.*"
        for event in mo:
            mo_content = await wrangler.sanitize(event["briefing"])
            if int(mostate) % 28 == 0:
                content += f"\n\n**NEW MAJOR ORDER:**\n\n{mo_content}"
            else:
                content += f"\n\n**MAJOR ORDER:**\n\n{mo_content}"
            content += f'\n\n*Expires <t:{int(await wrangler.retime(event["expiration"]))}:R>*'

    try:
        await channel.send(content)
    except errors.HTTPException:
        messages = wrangler.thatstoolong(content)
        for item in messages:
            await channel.send(item)

async def dispatch(channel):
    async with channel.typing():
        content = ""
        dis, distate = await hellmonitor.fetch("/api/v1/dispatches")
        if dis == "Error":
            await channel.send(f"An error has occurred: {distate}")
            return
        if int(distate) % 28 == 0:
            content += "**NEW DISPATCHES:**\n\n"
        else:
            content += "No updates since last check. Most recent Dispatches:\n\n"
        for element in dis[:5]:
            content += f'*Issued <t:{int(await wrangler.retime(element["published"]))}:R>*'
            if element["id"] > distate / 28 and distate % 28 == 0:
                content += "      **UNREAD**"
            content += f'\n{await wrangler.sanitize(element["message"])}\n-----\n\n'
    content += '*Showing 5 most recent Dispatches.*'
    try:
        await channel.send(content)
    except errors.HTTPException:
        messages = wrangler.thatstoolong(content)
        for item in messages:
            await channel.send(item)

@client.event
async def on_ready():
    print('-----')
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('-----')
    if info["monitor"] == 1:
        print("\033[91mWARNING: Automated monitoring is enabled.\033[0m")
        print("If you don't want this, stop the bot and set the option in key.json to 0.")
        monitor.start()
    print("The bot works -- this terminal will not provide further feedback unless there is an error. It's safe to detatch this window.")

@client.event
async def on_message(message):
    if not message.author.bot or message.author.system:
        with open('config.json', 'r') as f:
            commands = json.load(f)
        parts = message.content.strip().split()
        cmd = parts[0].lstrip("!")  # remove "!"
        args = parts[1:]
        if cmd in commands:
            action_name = commands[cmd]["action"]
            func = globals().get(action_name)  # look up function by name
            if callable(func):
                await func(message.channel)
            else:
                print(f"No function defined for action '{action_name}'")

client.run(key)
