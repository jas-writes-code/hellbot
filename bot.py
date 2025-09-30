from discord import *
import hellmonitor, wrangler
import json

client = Client(intents=Intents.all())
key = "OTQyNDk5OTU2NjU1MjY3ODkw.GDn1Sj.OcJyPpqybwdBoUqtt6yEYuy5NFuOgZxYwK3XpI"

async def major_order(message):
    async with message.channel.typing():
        content = ""
        mo, mostate = await hellmonitor.fetch("/api/v1/assignments")
        briefing, brstate = await hellmonitor.fetch("/raw/api/WarSeason/801/Status")
        briefing = briefing["globalEvents"]
        for event in briefing:
            briefing_content = await wrangler.sanitize(event["message"])
            content += f"**BRIEFING:**\n\n{briefing_content}"
        for event in mo:
            mo_content = await wrangler.sanitize(event["briefing"])
            content += f"\n\n**MAJOR ORDER:**\n\n{mo_content}"
            content += f'\n\n*Expires* <t:{int(await wrangler.retime(event["expiration"]))}:R>'

    await message.reply(content)

async def dispatch(message):
    async with message.channel.typing():
        content = ""
        dis, distate = await hellmonitor.fetch("/api/v1/dispatches")
        if str(distate)[0] == 2:
            content += "**NEW DISPATCHES:**"
        elif str(distate)[0] == 1:
            content += "No last-read detected. Most recent Dispatches:"
        for element in dis[:5]:
            content += f'\n\n{await wrangler.sanitize(element["message"])}'
            content += f'\n*Issued* <t:{int(await wrangler.retime(element["published"]))}:R>'

    await message.reply(content)

@client.event
async def on_ready():
    print('-----')
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('-----')
    print("The bot works -- this terminal will not provide further feedback unless there is an error. It's safe to detatch this window.")

@client.event
async def on_message(message):
    with open('commands.json', 'r') as f:
        commands = json.load(f)
    parts = message.content.strip().split()
    cmd = parts[0].lstrip("!")  # remove "!"
    args = parts[1:]
    if cmd in commands:
        action_name = commands[cmd]["action"]
        func = globals().get(action_name)  # look up function by name
        if callable(func):
            await func(message)
        else:
            print(f"No function defined for action '{action_name}'")
    else:
        print(f"Invalid command: {cmd}")

client.run(key)