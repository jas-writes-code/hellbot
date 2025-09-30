from discord.ext import tasks
from discord import *
import hellmonitor, wrangler
import json
import asyncio

client = Client(intents=Intents.all())
with open("key.json", "r") as file:
    info = json.load(file)
key = info["key"]

@tasks.loop(minutes=1)
async def monitor():
    target = client.get_channel(int(info["news"]))
    discard, state = await hellmonitor.fetch("/api/v1/assignments")
    if state % 28 == 0:
        await major_order(target)
    discard, state = await hellmonitor.fetch("/api/v1/dispatches")
    if state % 28 == 0:
        await dispatch(target)

async def major_order(channel):
    async with channel.typing():
        content = ""
        mo, mostate = await hellmonitor.fetch("/api/v1/assignments")
        briefing, brstate = await hellmonitor.fetch("/raw/api/WarSeason/801/Status")
        if mo == "Error":
            channel.send(f"An error has occurred: {mostate}")
            return
        briefing = briefing["globalEvents"]
        for event in briefing:
            briefing_title = await wrangler.sanitize(event["title"])
            briefing_content = await wrangler.sanitize(event["message"])
            content += f"**BRIEFING:** {briefing_title}\n\n{briefing_content}"
        if mostate == 38:
            content += f"\n\n*No currently active Major Order.*"
        for event in mo:
            mo_content = await wrangler.sanitize(event["briefing"])
            content += f"\n\n**MAJOR ORDER:**\n\n{mo_content}"
            content += f'\n\n*Expires* <t:{int(await wrangler.retime(event["expiration"]))}:R>'

    await channel.send(content)

async def dispatch(channel):
    async with channel.typing():
        content = ""
        dis, distate = await hellmonitor.fetch("/api/v1/dispatches")
        if dis == "Error":
            channel.send(f"An error has occurred: {distate}")
            return
        if distate % 28 == 0:
            content += "**NEW DISPATCHES:**"
        elif str(distate)[0] == 1:
            content += "No last-read detected. Most recent Dispatches:"
        for element in dis[:5]:
            content += f'\n-----\n*Issued* <t:{int(await wrangler.retime(element["published"]))}:R>'
            if element["id"] < distate / 28:
                content += " **UNREAD**"
            content += f'\n{await wrangler.sanitize(element["message"])}'

    await channel.send(content)

@client.event
async def on_ready():
    print('-----')
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('-----')
    if info["monitor"]:
        print("\033[91mWARNING: Automated monitoring is enabled.\033[0m")
        print("If you don't want this, stop the bot and set the option in key.json to false.")
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