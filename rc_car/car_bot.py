import discord
from discord.ext import commands
from rc_car_controller import RC_Car
import json

with open("car.json", "r") as jsonfile:
    data = json.load(jsonfile)
print(data)

speed = data["current_speed"]
duration = data["current_duration"]
benny = RC_Car(speed, duration)
is_on = True
debug = False
client = commands.Bot(command_prefix='%')


@client.event
async def on_ready():
    print("Bot is ready.")
    await client.get_channel(data["allowed_channels"][3]).send(f"Hello! I am Benny, my currenty speed is {speed}, and my default time is {duration}")


@client.event
async def on_message(message):

    lst = message.content.split()

# region commands
    # set speed and duration command
    if lst[0] == "%set" and message.author.id in data["manager_ids"]:
        try:
            change_value(lst[1], lst[2])
            await message.channel.send(f"Set speed to {speed} and time to {duration}")
        except:
            await message.channel.send("Paramaters were not changed")
            print("Not enough information provided")
            pass

    # reset command
    if lst[0] == "%reset" and message.author.id in data["manager_ids"]:
        change_value(str(data["default_speed"]), str(data["default_time"]))
        await message.channel.send("Parameters reset")

    # start command
    if lst[0] == "%start" and message.author.id in data["manager_ids"]:
        turn_on()

    # stop command
    if lst[0] == "%stop" and message.author.id in data["manager_ids"]:
        turn_off()

    # info command
    if lst[0] == "%info" and message.author.id in data["manager_ids"]:
        await message.channel.send(f"Current speed is {speed} and current duration is {duration}")

    # debug toggle command
    if lst[0] == "%debug" and message.author.id in data["manager_ids"]:
        debug_toggle(debug)
        await message.channel.send(f"Debug:{debug}")

# endregion

# region car controls
    if message.channel.id in data["allowed_channels"] and is_on == True:
        if len(lst) == 2:
            pass

        if len(lst) == 1 or len(lst) == 3:
            # forward
            if "w" == message.content.lower():
                if debug == True:
                    await message.channel.send("Moving Car Forward")
                benny.drive(speed, duration)
            elif "w" == lst[0].lower():
                if lst[1].isdigit() and isfloat(lst[2]):
                    if int(lst[1]) > speed or int(lst[1]) < 0 or float(lst[2]) > duration or float(lst[2]) < 0:
                        await message.channel.send("Too FAST!")
                    else:
                        if debug == True:
                            await message.channel.send("Moving Car Forward")
                        benny.drive(int(lst[1]), float(lst[2]))
                else:
                    pass

            # left
            if "a" == message.content.lower():
                if debug == True:
                    await message.channel.send("Moving Car Left")
                benny.turn_left(speed, duration)
            elif "a" == lst[0].lower():
                if lst[1].isdigit() and isfloat(lst[2]):
                    if int(lst[1]) > speed or int(lst[1]) < 0 or float(lst[2]) > duration or float(lst[2]) < 0:
                        await message.channel.send("Too FAST!")
                    else:
                        if debug == True:
                            await message.channel.send("Moving Car Left")
                        benny.turn_left(int(lst[1]), float(lst[2]))
                else:
                    pass

            # reverse
            if "s" == message.content.lower():
                if debug == True:
                    await message.channel.send("Moving Car Backwards")
                benny.back(speed, duration)
            elif "s" == lst[0].lower():
                if lst[1].isdigit() and isfloat(lst[2]):
                    if int(lst[1]) > speed or int(lst[1]) < 0 or float(lst[2]) > duration or float(lst[2]) < 0:
                        await message.channel.send("Too FAST!")
                    else:
                        if debug == True:
                            await message.channel.send("Moving Car Left")
                        benny.back(int(lst[1]), float(lst[2]))
                else:
                    pass

            # right
            if "d" == message.content.lower():
                if debug == True:
                    await message.channel.send("Moving Car Right")
                benny.turn_right(speed, duration)
            elif "d" == lst[0].lower():
                if lst[1].isdigit() and isfloat(lst[2]):
                    if int(lst[1]) > speed or int(lst[1]) < 0 or float(lst[2]) > duration or float(lst[2]) < 0:
                        await message.channel.send("Too FAST!")
                    else:
                        if debug == True:
                            await message.channel.send("Moving Car Left")
                        benny.turn_right(int(lst[1]), float(lst[2]))
                else:
                    pass
# endregion

# region misc functions


def isfloat(msg):
    try:
        float(msg)
        return True
    except:
        print("not float")
        return False


def change_value(new_speed, new_duration):
    global speed
    global duration

    if new_speed.isdigit() and isfloat(new_duration):
        speed = int(new_speed)
        duration = float(new_duration)
        print("Paramaters changed")
        data["current_speed"] = speed
        data["current_duration"] = duration

        with open("car.json", "w") as jsonfile:
            json.dump(data, jsonfile, indent=4)
    else:
        print("Paramaters not changed")
        pass


def turn_on():
    global is_on

    is_on = True
    print("Bot turned on ;)")


def turn_off():
    global is_on

    is_on = False
    print("Bot turned off")
# endregion


def debug_toggle(current):
    global debug

    debug = not current


client.run(data["bot_token"])
