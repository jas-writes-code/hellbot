# HellBot
Pulls data from Helldivers.

You'll need Python, obviously. I'm running 3.11.2 but it'll probably work with newer versions.
Apart from that, `pip install -r requirements.txt` should sort you.

##Config options
- If you don't want to use automatic monitoring, set the corresponding setting to `0` in key.json.
- If you do, leave it as is. You'll need to provide a channel id for the monitoring to take place in, in the corresponding setting in key.json.
- You MUST insert a bot token in the corresponding setting in key.json. The bot won't work very well otherwise.
