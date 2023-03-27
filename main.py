# This example requires the 'message_content' privileged intents

import json
import os
import requests
from datetime import datetime
import discord
from discord.ext import commands
import asyncio

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

app_ws = 'https://expressjs-prisma-production-36b8.up.railway.app/commands/'
app_accounts_ws = 'https://expressjs-prisma-production-36b8.up.railway.app/accounts'

headers = {
            "Content-Type": "application/json"
        }

EMOJI_NUMBERS = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

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

@bot.command(name='start')
async def start_command(ctx):
    # Send the initial message with options and add reactions
    sent_message = await ctx.send('Choose an option:', embed=create_options_embed())
    await sent_message.add_reaction('🛑')   # Reaction for "Quit"
    await sent_message.add_reaction('🗣️')  # Reaction for "Whisper"
    await sent_message.add_reaction('💻')   # Reaction for "Online"

    # Create a check function to filter reactions
    def reaction_check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ['🛑', '🗣️', '💻']

    # Wait for a reaction matching the check function
    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=reaction_check)
    except asyncio.TimeoutError:
        await ctx.send('You did not make a selection in time.')
    else:
        # Respond based on which option was chosen
        if str(reaction.emoji) == '🛑':  # "Quit" option
            await handle_quit(ctx)
        elif str(reaction.emoji) == '🗣️':  # "Whisper" option
            await handle_whisper(ctx)
        elif str(reaction.emoji) == '💻':  # "Online" option
            msg = await check_online()
            await ctx.send(msg)

async def handle_whisper(ctx):
    # Make a GET request to fetch options
    result = requests.get(app_accounts_ws)
    data = result.json()

    # Send the new message with options
    sent_message = await ctx.send('Choose an account:', embed=create_accounts_embed(data))
    
    # Add number emojis as reactions
    for i in range(min(len(data), len(EMOJI_NUMBERS))):
        await sent_message.add_reaction(EMOJI_NUMBERS[i])

    # Create a check function to filter reactions
    def reaction_check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in EMOJI_NUMBERS[:min(len(data), len(EMOJI_NUMBERS))]

    # Wait for a reaction matching the check function
    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=reaction_check)
    except asyncio.TimeoutError:
        await ctx.send('You did not make a selection in time.')
    else:
        # Get the account corresponding to the selected emoji
        account_index = EMOJI_NUMBERS.index(str(reaction.emoji))
        selected_account = data[account_index]
        account_name = selected_account["account"]
        receiver_name = ''
        message_whisper = ''

        # await response for who to whisper and what message
        await ctx.send('Please enter the name of the receiver:')
        try:
            receiver_name = await bot.wait_for('message', timeout=30.0, check=lambda m: m.author == ctx.author)
        except asyncio.TimeoutError:
            await ctx.send('You did not enter a receiver name in time.')
            return
        await ctx.send('Please enter the message:')
        try:
            message_whisper = await bot.wait_for('message', timeout=30.0, check=lambda m: m.author == ctx.author)
        except asyncio.TimeoutError:
            await ctx.send('You did not enter a message in time.')
            return

        data = {
            "command": 'Whisper,' + account_name+","+receiver_name+","+message_whisper.content
        }

        print(data)
        await ctx.send("Sent whisper from: " + account_name + "to " + receiver_name + "!")

        # result = requests.post(
        #     app_ws, json=data, headers=headers)

        # if 200 <= result.status_code < 300:
        #     print(f"Webhook sent {result.status_code}")
        #     await ctx.send("Sent whisper from: " + account_name + "to " + receiver_name + "!")
        # else:
        #     print(
        #         f"Not sent with {result.status_code}, response:\n{result.json()}")
        #     await ctx.send("Failed sending whisper command!")
            
            
async def handle_quit(ctx):
    # Make a GET request to fetch options
    result = requests.get(app_accounts_ws)
    data = result.json()

    # Send the new message with options
    sent_message = await ctx.send('Choose an account:', embed=create_accounts_embed(data))
    
    # Add number emojis as reactions
    for i in range(min(len(data), len(EMOJI_NUMBERS))):
        await sent_message.add_reaction(EMOJI_NUMBERS[i])

    # Create a check function to filter reactions
    def reaction_check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in EMOJI_NUMBERS[:min(len(data), len(EMOJI_NUMBERS))]

    # Wait for a reaction matching the check function
    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=reaction_check)
    except asyncio.TimeoutError:
        await ctx.send('You did not make a selection in time.')
    else:
        # Get the account corresponding to the selected emoji
        account_index = EMOJI_NUMBERS.index(str(reaction.emoji))
        selected_account = data[account_index]
        account_name = selected_account["account"]

        data = {
                "command": 'Quit,' + account_name,
        }

        result = requests.post(
            app_ws, json=data, headers=headers)

        if 200 <= result.status_code < 300:
            print(f"Webhook sent {result.status_code}")
            await ctx.send("Sent quit command to: " + account_name + "!")
        else:
            print(
                f"Not sent with {result.status_code}, response:\n{result.json()}")
            await ctx.send("Failed sending quit command!")


async def check_online():
    msg = ''
    # send get request to app_accounts_ws
    result = requests.get(app_accounts_ws)
    # iterate over result and add to msg the account and lastseen fields
    for account in result.json():
        lastseen = account['lastseen']
        datetime_object = datetime.strptime(lastseen, "%Y-%m-%dT%H:%M:%S.%fZ")
        beauty_date = datetime_object.strftime("%B %d, %Y %I:%M %p")
        msg += f"{account['account']} was last seen on {beauty_date}\n"

    return msg

def create_options_embed():
    embed = discord.Embed(title='Commands:', description='React to make your choice:', color=discord.Color.green())
    embed.add_field(name='Quit', value='🛑', inline=True)
    embed.add_field(name='Whisper', value='🗣️', inline=True)
    embed.add_field(name='Online', value='💻', inline=True)
    return embed

def create_accounts_embed(data):
    embed = discord.Embed(title='Accounts:', description='React to make your choice:', color=discord.Color.green())

    index = 1
    for account in data:
        embed.add_field(name=account['account'], value=index, inline=True)
        index = index + 1

    return embed

bot.run(os.environ["DISCORD_TOKEN"])
