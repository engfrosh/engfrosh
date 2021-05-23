import discord
from discord.ext import commands
import os
import random
import string

Client = discord.Client()
client = commands.Bot(command_prefix="!")

users = {}


@client.event
async def on_ready():
    print("Logged on as {}".format(client.user))
    game = discord.Game(name="\'q!hathelp\' for info!")
    await client.change_presence(activity=game)

@client.command(pass_context=True)
async def superhelp(ctx):
    print("Help message used in {}".format(ctx.message.channel.guild.name))
    string = "hey, type !react emoji" \

    embed = discord.Embed()
    embed.add_field(name="Bot Usage!", value=string)
    await ctx.channel.send(embed=embed)

@client.command(pass_context=True)
async def CHAMPION(ctx):
    await ctx.channel.send("THE CHAMPION!", file=discord.File("peepocheer.png"))


@client.command(pass_context=True)
async def ezclap(ctx):
    await ctx.channel.send("https://tenor.com/view/pepe-clap-gif-10184275")

@client.command(pass_context=True)
async def react(ctx):
    await ctx.message.add_reaction("🍋")
    await ctx.channel.send("did it work?")

client.run("ODQ1ODAzMTQ0ODAwNzYzOTI1.YKmRjw.Jn1VAgE-o8k3JDnx1BxA5uUQCeY")