import discord
from discord.ext import commands
from rc_car_controller import RC_Car
import json

with open ("car.json", "r") as jsonfile:
    data = json.load(jsonfile)
print(data)

speed = data["default_speed"]
duration = data["default_time"]
benny = RC_Car(speed,duration)

client = commands.Bot(command_prefix = '%')

@client.event
async def on_ready():
    print("Bot is ready.")

@client.event
async def on_message(message):

    lst = message.content.split()

    #set speed and duration command
    if lst[0] == "%set" and message.author.id in data["manager_ids"]:
        try:
            change_value(lst[1],lst[2])
        except:
            print("Not enough information provided")
            pass

    #reset command 
    if lst[0] == "%reset" and message.author.id in data["manager_ids"]:
        change_value(str(data["default_speed"]),str(data["default_time"]))

    #stop/start
        #stop/start driving


    if message.channel.id in data["allowed_channels"]:
        if len(lst)==2:
            pass

        if len(lst)==1 or len(lst)==3:
            #forward
            if "w" == message.content.lower():
                await message.channel.send("Moving Car Forward")
                benny.drive(speed,duration)
            elif "w"==lst[0].lower():
                if lst[1].isdigit() and isfloat(lst[2]):
                    await message.channel.send("Moving Car Forward")
                    benny.drive(int(lst[1]),float(lst[2]))
                else:
                    pass

            #left 
            if "a" == message.content.lower():
                await message.channel.send("Moving Car Left")
                benny.turn_left(speed,duration)
            elif "a"==lst[0].lower():
                if lst[1].isdigit() and isfloat(lst[2]):
                    await message.channel.send("Moving Car Left")
                    benny.turn_left(int(lst[1]),float(lst[2]))
                else:
                    pass

            #reverse
            if "s" == message.content.lower():
                await message.channel.send("Moving Car Backwards")
                benny.back(speed,duration)
            elif "s"==lst[0].lower():
                if lst[1].isdigit() and isfloat(lst[2]):
                    await message.channel.send("Moving Car Left")
                    benny.back(int(lst[1]),float(lst[2]))
                else:
                    pass

            #right
            if "d" == message.content.lower():
                await message.channel.send("Moving Car Right")
                benny.turn_right(speed,duration)
            elif "d"==lst[0].lower():
                if lst[1].isdigit() and isfloat(lst[2]):
                    await message.channel.send("Moving Car Left")
                    benny.turn_right(int(lst[1]),float(lst[2]))
                else:
                    pass


def isfloat(msg):
    try:
        float(msg)
        return True
    except:
        print ("not float")
        return False

def change_value(new_speed,new_duration):
    global speed
    global duration

    if new_speed.isdigit() and isfloat(new_duration):
        speed = int(new_speed)
        duration = float(new_duration)
        print("Paramaters changed")
        data["current_speed"]=speed
        data["current_duration"]=duration

        with open("car.json", "w") as jsonfile:
            json.dump(data, jsonfile)
    else:
        print("Paramaters not changed")
        pass

client.run ("ODc2OTYxODMzOTE4MDA1MjU4.YRrsWg.ie4fqSkSqrZ0gjhvX0dFMRJJ9PY")