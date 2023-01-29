# This example requires the 'message_content' privileged intents

import os
import requests
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

app_ws = 'https://expressjs-prisma-production-36b8.up.railway.app/commands/'
app_accounts_ws = 'https://expressjs-prisma-production-36b8.up.railway.app/accounts'

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send('pong')

@bot.command()
async def send(ctx):
    # send post to disc_notifications with the account and minutes_passed
    data = {
        "command": ctx.message.content[6:],
    }

    headers = {
        "Content-Type": "application/json"
    }

    result = requests.post(
        app_ws, json=data, headers=headers)

    if 200 <= result.status_code < 300:
        print(f"Webhook sent {result.status_code}")
        await ctx.send("Command retrieved!")

    else:
        print(
            f"Not sent with {result.status_code}, response:\n{result.json()}")
        await ctx.send("Failed retrieving command!")

@bot.command()
async def online(ctx):
    # send get request to app_accounts_ws
    result = requests.get(app_accounts_ws)
    msg = ''
    # iterate over result and add to msg the account and lastseen fields
    for account in result.json():
        print(account)
        msg += f"{account['account']} is online and was last seen at {account['lastseen']}\n"

    print(msg)
    
    await ctx.send(msg)

bot.run(os.environ["DISCORD_TOKEN"])
