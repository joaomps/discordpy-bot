# This example requires the 'message_content' privileged intents

import os
import requests
from datetime import datetime
import discord
from discord.ext import commands

client = discord.Client()

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

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content == '!start':
        sent_message = await message.channel.send('Choose an option:', embed=create_options_embed())
        await sent_message.add_reaction('🛑')   # Reaction for "Quit"
        await sent_message.add_reaction('🗣️')  # Reaction for "Whisper"
        await sent_message.add_reaction('💻')   # Reaction for "Online"

@client.event
async def on_reaction_add(reaction, user):
    if user == client.user:
        return

    if str(reaction.emoji) == '🛑':  # "Quit" option
        await reaction.message.channel.send('You chose Quit!')

    elif str(reaction.emoji) == '🗣️':  # "Whisper" option
        await reaction.message.channel.send('You chose Whisper!')

    elif str(reaction.emoji) == '💻':  # "Online" option
        await reaction.message.channel.send('You chose Online!')

def create_options_embed():
    embed = discord.Embed(title='Options:', description='React to make your choice:', color=discord.Color.green())
    embed.add_field(name='Quit', value='🛑', inline=True)
    embed.add_field(name='Whisper', value='🗣️', inline=True)
    embed.add_field(name='Online', value='💻', inline=True)
    return embed

client.run(os.environ["DISCORD_TOKEN"])
bot.run(os.environ["DISCORD_TOKEN"])
