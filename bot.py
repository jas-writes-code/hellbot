from discord import *
import hellmonitor

client = Client(intents=Intents.all())
key = "OTQyNDk5OTU2NjU1MjY3ODkw.GDn1Sj.OcJyPpqybwdBoUqtt6yEYuy5NFuOgZxYwK3XpI"

@client.event
async def on_ready():
    print(f"Logged in as {client.user.name}")


#client.run(key)