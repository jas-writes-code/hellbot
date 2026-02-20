import time
from discord.ext import tasks
from discord import *
import hellmonitor, wrangler, info
import json

client = Client(intents=Intents.all())
with open("key.json", "r") as file:
    info = json.load(file)
key = info["key"]
error_message = None
basetime = 1707760800 # used for briefings and things

@tasks.loop(seconds=60)
async def monitor():
    global error_message
    target = client.get_channel(int(info["news"]))
    test, state = await hellmonitor.fetch("/api/v1/assignments", False)
    if test == "Error":
        if error_message:
            await error_message.delete()
        error_message = await target.send(f"An Error occured. {state}")
        return
    if int(state) % 28 == 0:
        await major_order(target)
    test, state = await hellmonitor.fetch("/api/v1/dispatches", False)
    if test == "Error":
        if error_message:
            await error_message.delete()
        error_message = await target.send(f"An Error occured. {state}")
        return
    if int(state) % 28 == 0:
        await dispatch(target)

@tasks.loop(seconds=600)
async def forecastMonitor():
    print("updating forecast log at ", time.time())
    with open("forecastlog.json", "r") as f:
        flog = json.load(f)
    planets, discard = await hellmonitor.fetch("/api/v1/planets", False)
    sp = str(int(time.time()))
    for planet in planets:
        if type(planet["health"]) == int:
            if planet["health"] != planet["maxHealth"]:
                flog["planets"].setdefault(planet["index"], {})
                flog["planets"][planet["index"]][sp] = planet["health"]
        else:
            print(planet["health"])

        if len(planet["regions"]) > 0:
            for city in planet["regions"]:
                if city["health"] != city["maxHealth"] and city["health"] is not None:
                    flog["cities"].setdefault(city["hash"], {})
                    flog["cities"][city["hash"]][sp] = city["health"]

    for category in flog:
        for item in flog[category]:
            for stamp in list(flog[category][item].keys()):
                if int(stamp) < int(sp) - 8 * 3600:
                    del flog[category][item][stamp]

    with open("forecastlog.json", "w") as f:
        json.dump(flog, f)

async def prio(channel):
    async with (channel.typing()):
        content = "**High-Priority planet status:**\n\n"
        prios = []
        war, discard = await hellmonitor.fetch("/api/v1/war", False)
        if type(war) == tuple:
            await channel.send(f"An Error occured. (Status code {war[1]})")
            return
        players = war["statistics"]["playerCount"]
        planets, discard = await hellmonitor.fetch("/api/v1/planets", False)
        defcam, status = await hellmonitor.fetch("/api/v1/planet-events", False)
        for planet in planets:
            if planet["statistics"]["playerCount"] > players / 21:
                prios.append(planet)
        prios.sort(key=lambda p: p["statistics"]["playerCount"], reverse=True)
        for element in prios[:5]:
            content += f"**{element['name']}** ({element['currentOwner']})\n"
            content += f"*{element['statistics']['playerCount']}* players active ({int(element['statistics']['playerCount'] * 100 / players)}% of total)\n"
            content += f"{element['health']}/{element['maxHealth']}"
            if element['currentOwner'] == "Humans": # check for a active defense campaign, or mark the planet as liberated
                if type(defcam) == tuple:
                    await channel.send(f"An Error occured. (Status code {defcam[1]})")
                    continue
                else:
                    if status == 48: # if no defenses are active, continue as before
                        content += f" **({(element['health'] * 100 / element['maxHealth'])}% liberated)**\n"
                    else:
                        for campaign in defcam:
                            if campaign['index'] == element['index']:
                                content += f"\n**Active Defense:**"
                                start = int(await wrangler.retime(campaign['event']['startTime']))
                                end = int(await wrangler.retime(campaign['event']['endTime']))
                                duration = end - start
                                content += f" Expires <t:{end}:R> ({100 * (int(time.time()) - start) / duration}%)"
                                content += f"\n**Progress**: {100 - campaign['event']['health']*100/campaign['event']['maxHealth']}%"
                                content += f" (Invasion level {int(campaign['event']['maxHealth'] / 50000)})"
                            else: # if it's not a defense campaign, continue as before
                                content += f" **({(element['health']*100/element['maxHealth'])}% liberated)**\n"
            else:
                content += f" **({100-(element['health']*100/element['maxHealth'])}% liberated)**\n"
            if len(element['regions']) > 0:
                content += "\n*Megacity status:*"
                cities = await wrangler.megacities(element)
                content += cities
            content += "\n\n"
        content += f'*{war["statistics"]["playerCount"]} players online*'
    try:
        await channel.send(content)
    except errors.HTTPException:
        messages = wrangler.thatstoolong(content)
        for item in messages:
            await channel.send(item)

async def major_order(channel):
    async with (channel.typing()):
        content = ""
        mo, mostate = await hellmonitor.fetch("/api/v1/assignments", True)
        briefing, brstate = await hellmonitor.fetch("/raw/api/WarSeason/801/Status", True)
        briefing = briefing["globalEvents"]
        for event in briefing:
            briefing_title = await wrangler.sanitize(event["title"])
            briefing_content = await wrangler.sanitize(event["message"])
            content += f"\n\n**{briefing_title}**"
            if basetime + event['expireTime'] > int(time.time()):
                content += f" (*Expires <t:{basetime + int(event['expireTime'])}:R>*)\n\n{briefing_content}"
            else:
                content += f" (*Issued <t:{basetime + int(event['expireTime'])}:R>*)\n\n{briefing_content}"
        if mostate == 48:
            content += f"\n\n*No currently active Major Order.*"
        for event in mo:
            mo_content = await wrangler.sanitize(event["briefing"])
            if int(mostate) % 28 == 0:
                content += f"\n\n**NEW {event['title']}:**\n\n{mo_content}"
            else:
                content += f"\n\n**{event['title']}:**\n\n{mo_content}\n"
            content += await wrangler.mo_processing(event)
            content += f'*Expires <t:{int(await wrangler.retime(event["expiration"]))}:R>*'

    try:
        await channel.send(content)
    except errors.HTTPException:
        messages = wrangler.thatstoolong(content)
        for item in messages:
            await channel.send(item)

async def dispatch(channel):
    async with channel.typing():
        content = ""
        dis, distate = await hellmonitor.fetch("/api/v1/dispatches", True)
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
    forecastMonitor.start()
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

#monitor error handling
async def oopsie_daisy(exc):
    print(f"\033[91mAPI Error: {type(exc).__name__}: {exc}\033[0m")

#go go go
forecastMonitor.error(oopsie_daisy)
monitor.error(oopsie_daisy)
client.run(key)