# This example requires the 'message_content' privileged intents

import os
import requests
from datetime import datetime
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
        lastseen = account['lastseen']
        datetime_object = datetime.strptime(lastseen, "%Y-%m-%dT%H:%M:%S.%fZ")
        beauty_date = datetime_object.strftime("%B %d, %Y %I:%M %p")
        msg += f"{account['account']} was last seen on {beauty_date}\n"

    await ctx.send(msg)

bot.run(os.environ["DISCORD_TOKEN"])
