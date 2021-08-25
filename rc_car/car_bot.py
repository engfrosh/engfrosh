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
    lst = message.content.split()

    if lst.__len__() == 2:
        pass

    if lst.__len__() == 1 or lst.__len__() == 3:
        # forward
        if "w" == message.content.lower():
            await message.channel.send("Moving Car Forward")
            benny.drive(60, 0.5)
        elif "w" == lst[0].lower():
            if lst[1].isdigit() and isfloat(lst[2]):
                await message.channel.send("Moving Car Forward")
                benny.drive(int(lst[1]), float(lst[2]))
            else:
                pass

        # left
        if "a" == message.content.lower():
            await message.channel.send("Moving Car Left")
            benny.turn_left(80, 0.5)
        elif "a" == lst[0].lower():
            if lst[1].isdigit() and isfloat(lst[2]):
                await message.channel.send("Moving Car Left")
                benny.turn_left(int(lst[1]), float(lst[2]))
            else:
                pass

        # reverse
        if "s" == message.content.lower():
            await message.channel.send("Moving Car Backwards")
            benny.back(60, 0.5)
        elif "s" == lst[0].lower():
            if lst[1].isdigit() and isfloat(lst[2]):
                await message.channel.send("Moving Car Left")
                benny.back(int(lst[1]), float(lst[2]))
            else:
                pass

        # right
        if "d" == message.content.lower():
            await message.channel.send("Moving Car Right")
            benny.turn_right(80, 0.5)
        elif "d" == lst[0].lower():
            if lst[1].isdigit() and isfloat(lst[2]):
                await message.channel.send("Moving Car Left")
                benny.turn_right(int(lst[1]), float(lst[2]))
            else:
                pass


def isfloat(msg):
    try:
        float(msg)
        return True
    except:
        print("not float")
        return False


client.run("ODc2OTYxODMzOTE4MDA1MjU4.YRrsWg.ie4fqSkSqrZ0gjhvX0dFMRJJ9PY")
