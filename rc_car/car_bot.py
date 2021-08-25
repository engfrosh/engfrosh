import discord
from discord.ext import commands
from rc_car_controller import RC_Car

client = commands.Bot(command_prefix='.')
benny = RC_Car(60)


@client.event
async def on_ready():
    print("Bot is ready.")


@client.event
async def on_message(message):
    if "w" == message.content.lower():
        print("FORWARD")
        await message.channel.send("Moving Car Forward")
        benny.drive(60)

    if "a" == message.content.lower():
        print("LEFT")
        await message.channel.send("Moving Car Left")
        benny.turn_left(80)

    if "s" == message.content.lower():
        print("REVERSE")
        await message.channel.send("Moving Car Backwards")
        benny.back(60)

    if "d" == message.content.lower():
        print("RIGHT")
        await message.channel.send("Moving Car Right")
        benny.turn_right(80)

client.run("ODc2OTYxODMzOTE4MDA1MjU4.YRrsWg.ie4fqSkSqrZ0gjhvX0dFMRJJ9PY")
