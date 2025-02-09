
import json
import os
import random
import requests
from datetime import datetime
import discord
from discord.ext import commands
import asyncio
import openai

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

app_ws = "https://expressjs-prisma-production.app/commands/"
app_createjob_ws = "https://expressjs-prisma-production.app/createjob/"
app_accounts_ws = "https://expressjs-prisma-production.app/accounts"
available_accounts_ws = 'https://expressjs-prisma-production.app/available-accounts'

headers = {"Content-Type": "application/json"}

EMOJI_NUMBERS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]

# OPEN AI CONFIG
personality_prompt = [
    "From now on you will act like a World of Warcraft player that prefers being left alone than having long conversations and dislikes joining any groups. Do not ask any questions. Without repeating the same responses and in their language, respond in less than 125 characters without being too chatty. Do not mention “Bot”, “Baneto”, “GMR”, “HWT”, “Tinkr”, “OpenAI”, “GPT”, “ChatGPT”, “AI language model” or anything that would let them know that you are not human. Do not use any commas, dots, periods, hashtags or proper grammar. You reply with brief, to-the-point answers with no elaboration. Don't use any punctuation or uppercase characters.",
]

TEMPERATURE = 0.5
MAX_TOKENS = 500
FREQUENCY_PENALTY = 0
PRESENCE_PENALTY = 0.6
# limits how many questions we include in the prompt
MAX_CONTEXT_QUESTIONS = 10

past_conversations = {}
openai.api_key = "123456"
model = "gpt-3.5-turbo"
##


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.event
async def on_message(message):
    # Ignore messages sent by the bot itself
    if message.author == bot.user:
        return

    # Check for embedded content with title "Whisper"
    # if message.embeds:
    #     for embed in message.embeds:
    #         if embed.title == "Whisper":
    #             await handle_whisper_embed(message, embed, message.author.name)

    # Continue processing commands
    await bot.process_commands(message)


async def handle_whisper_embed(message, embed, character_name):
    # Your logic to handle the whisper embed goes here
    # For example, you can send a message to the same channel
    message_field = None
    sender_name_field = None

    # Look for the fields with the names "Message" and "Sender Name"
    for field in embed.fields:
        if field.name == "Message":
            message_field = field
        elif field.name == "Sender Name":
            sender_name_field = field

        if message_field and sender_name_field:  # Exit the loop if both fields are found
            break

    if message_field and sender_name_field:

        messages = [
            {"role": "system", "content": personality_prompt[0]},
        ]

        user_history = past_conversations.get(sender_name_field.value, [])

        if len(user_history) > 0:
            for question, answer in user_history[-MAX_CONTEXT_QUESTIONS:]:
                messages.append({"role": "user", "content": question})
                messages.append({"role": "assistant", "content": answer})

        messages.append({"role": "user", "content": message_field.value})

        print(messages)

        completion = openai.ChatCompletion.create(
            model=model, messages=messages)

        # remove all commas from completion.choices[0].message.content
        msg_to__send = completion.choices[0].message.content.replace(",", "")

        # add response to history for the user
        past_conversations[sender_name_field.value] = [
            (message_field.value, msg_to__send)]

        # sleep randomly for 4-9 seconds
        await asyncio.sleep(random.randint(4, 9))

        data = {
            "command": f"Whisper,{character_name},{sender_name_field.value},{msg_to__send}"
        }

        result = requests.post(app_ws, json=data, headers=headers)
        if 200 <= result.status_code < 300:
            print(f"Webhook sent {result.status_code}")
            await message.channel.send("Chatgpt answer: " + msg_to__send)
        else:
            print(
                f"Not sent with {result.status_code}, response:\n{result.json()}")
            await message.channel.send("Could not send whisper reply from chatgpt!")


@bot.command()
async def send(ctx):
    # send post to disc_notifications with the account and minutes_passed
    data = {
        "command": ctx.message.content[6:],
    }

    headers = {"Content-Type": "application/json"}

    result = requests.post(app_ws, json=data, headers=headers)

    if 200 <= result.status_code < 300:
        print(f"Webhook sent {result.status_code}")
        await ctx.send("Command retrieved!")
    else:
        print(
            f"Not sent with {result.status_code}, response:\n{result.json()}")
        await ctx.send("Failed retrieving command!")


@bot.command(name="run")
async def run_command(ctx):
    # Make a GET request to fetch options
    result = requests.get(available_accounts_ws)
    data = result.json()

    # Send the new message with options
    sent_message = await ctx.send(
        "Choose an account to start:", embed=create_available_accounts_embed(data)
    )

    # Add number emojis as reactions
    for i in range(min(len(data), len(EMOJI_NUMBERS))):
        await sent_message.add_reaction(EMOJI_NUMBERS[i])

    # Create a check function to filter reactions
    def reaction_check(reaction, user):
        return (
            user == ctx.author
            and str(reaction.emoji)
            in EMOJI_NUMBERS[: min(len(data), len(EMOJI_NUMBERS))]
        )

    # Wait for a reaction matching the check function
    try:
        reaction, user = await bot.wait_for(
            "reaction_add", timeout=30.0, check=reaction_check
        )
    except asyncio.TimeoutError:
        await ctx.send("You did not make a selection in time.")
    else:
        # Get the account corresponding to the selected emoji
        account_index = EMOJI_NUMBERS.index(str(reaction.emoji))
        selected_account = data[account_index]
        print(selected_account)

        data = {
            "job": {
                "accounttorun": selected_account['accountname'],
                "pathtorun": selected_account['pathtorun'],
                "devicename": selected_account['devicename']
            }
        }

        result = requests.post(app_createjob_ws, json=data, headers=headers)

        if 200 <= result.status_code < 300:
            print(f"Webhook sent {result.status_code}")
            await ctx.send("Sent run command to: " + selected_account['accountname'] + "!")
        else:
            print(
                f"Not sent with {result.status_code}, response:\n{result.json()}")
            await ctx.send("Failed sending run command!")


@bot.command(name="start")
async def start_command(ctx):
    # Send the initial message with options and add reactions
    sent_message = await ctx.send("Choose an option:", embed=create_options_embed())
    await sent_message.add_reaction("🛑")  # Reaction for "Quit"
    await sent_message.add_reaction("🗣️")  # Reaction for "Whisper"
    await sent_message.add_reaction("💻")  # Reaction for "Online"
    await sent_message.add_reaction("📷")  # Reaction for "Screenshot"

    # Create a check function to filter reactions
    def reaction_check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["🛑", "🗣️", "💻", "📷"]

    # Wait for a reaction matching the check function
    try:
        reaction, user = await bot.wait_for(
            "reaction_add", timeout=30.0, check=reaction_check
        )
    except asyncio.TimeoutError:
        await ctx.send("You did not make a selection in time.")
    else:
        # Respond based on which option was chosen
        if str(reaction.emoji) == "🛑":  # "Quit" option
            await handle_quit(ctx)
        elif str(reaction.emoji) == "🗣️":  # "Whisper" option
            await handle_whisper(ctx)
        elif str(reaction.emoji) == "💻":  # "Online" option
            msg = await check_online()
            await ctx.send(msg)
        elif str(reaction.emoji) == "📷":  # Screenshot option
            await handle_screenshot(ctx)


async def handle_screenshot(ctx):
   # Make a GET request to fetch options
    result = requests.get(app_accounts_ws)
    data = result.json()

    # Send the new message with options
    sent_message = await ctx.send(
        "Choose an account:", embed=create_accounts_embed(data)
    )

    # Add number emojis as reactions
    for i in range(min(len(data), len(EMOJI_NUMBERS))):
        await sent_message.add_reaction(EMOJI_NUMBERS[i])

    # Create a check function to filter reactions
    def reaction_check(reaction, user):
        return (
            user == ctx.author
            and str(reaction.emoji)
            in EMOJI_NUMBERS[: min(len(data), len(EMOJI_NUMBERS))]
        )

    # Wait for a reaction matching the check function
    try:
        reaction, user = await bot.wait_for(
            "reaction_add", timeout=30.0, check=reaction_check
        )
    except asyncio.TimeoutError:
        await ctx.send("You did not make a selection in time.")
    else:
        # Get the account corresponding to the selected emoji
        account_index = EMOJI_NUMBERS.index(str(reaction.emoji))
        selected_account = data[account_index]
        account_name = selected_account["account"]

        data = {
            "command": "Screenshot," + account_name,
        }

        result = requests.post(app_ws, json=data, headers=headers)

        if 200 <= result.status_code < 300:
            print(f"Webhook sent {result.status_code}")
            await ctx.send("Sent screenshot command to: " + account_name + "!")
        else:
            print(
                f"Not sent with {result.status_code}, response:\n{result.json()}")
            await ctx.send("Failed sending screenshot command!")


async def handle_whisper(ctx):
    # Make a GET request to fetch options
    result = requests.get(app_accounts_ws)
    data = result.json()

    # Send the new message with options
    sent_message = await ctx.send(
        "Choose an account:", embed=create_accounts_embed(data)
    )

    # Add number emojis as reactions
    for i in range(min(len(data), len(EMOJI_NUMBERS))):
        await sent_message.add_reaction(EMOJI_NUMBERS[i])

    # Create a check function to filter reactions
    def reaction_check(reaction, user):
        return (
            user == ctx.author
            and str(reaction.emoji)
            in EMOJI_NUMBERS[: min(len(data), len(EMOJI_NUMBERS))]
        )

    # Wait for a reaction matching the check function
    try:
        reaction, user = await bot.wait_for(
            "reaction_add", timeout=30.0, check=reaction_check
        )
    except asyncio.TimeoutError:
        await ctx.send("You did not make a selection in time.")
    else:
        # Get the account corresponding to the selected emoji
        account_index = EMOJI_NUMBERS.index(str(reaction.emoji))
        selected_account = data[account_index]
        account_name = selected_account["account"]
        receiver_name = ""
        message_whisper = ""

        # await response for who to whisper and what message
        await ctx.send("Please enter the name of the receiver:")
        try:
            receiver_name = await bot.wait_for(
                "message", timeout=30.0, check=lambda m: m.author == ctx.author
            )
        except asyncio.TimeoutError:
            await ctx.send("You did not enter a receiver name in time.")
            return
        await ctx.send("Please enter the message:")
        try:
            message_whisper = await bot.wait_for(
                "message", timeout=30.0, check=lambda m: m.author == ctx.author
            )
        except asyncio.TimeoutError:
            await ctx.send("You did not enter a message in time.")
            return

        data = {
            "command": "Whisper,"
            + account_name
            + ","
            + receiver_name.content
            + ","
            + message_whisper.content
        }

        result = requests.post(app_ws, json=data, headers=headers)

        if 200 <= result.status_code < 300:
            print(f"Webhook sent {result.status_code}")
            await ctx.send(
                "Sent whisper from: "
                + account_name
                + " to "
                + receiver_name.content
                + "!"
            )
        else:
            print(
                f"Not sent with {result.status_code}, response:\n{result.json()}")
            await ctx.send("Failed sending whisper command!")


async def handle_quit(ctx):
    # Make a GET request to fetch options
    result = requests.get(app_accounts_ws)
    data = result.json()

    # Send the new message with options
    sent_message = await ctx.send(
        "Choose an account:", embed=create_accounts_embed(data)
    )

    # Add number emojis as reactions
    for i in range(min(len(data), len(EMOJI_NUMBERS))):
        await sent_message.add_reaction(EMOJI_NUMBERS[i])

    # Create a check function to filter reactions
    def reaction_check(reaction, user):
        return (
            user == ctx.author
            and str(reaction.emoji)
            in EMOJI_NUMBERS[: min(len(data), len(EMOJI_NUMBERS))]
        )

    # Wait for a reaction matching the check function
    try:
        reaction, user = await bot.wait_for(
            "reaction_add", timeout=30.0, check=reaction_check
        )
    except asyncio.TimeoutError:
        await ctx.send("You did not make a selection in time.")
    else:
        # Get the account corresponding to the selected emoji
        account_index = EMOJI_NUMBERS.index(str(reaction.emoji))
        selected_account = data[account_index]
        account_name = selected_account["account"]

        data = {
            "command": "Quit," + account_name,
        }

        result = requests.post(app_ws, json=data, headers=headers)

        if 200 <= result.status_code < 300:
            print(f"Webhook sent {result.status_code}")
            await ctx.send("Sent quit command to: " + account_name + "!")
        else:
            print(
                f"Not sent with {result.status_code}, response:\n{result.json()}")
            await ctx.send("Failed sending quit command!")


async def check_online():
    msg = ""
    # send get request to app_accounts_ws
    result = requests.get(app_accounts_ws)
    # iterate over result and add to msg the account and lastseen fields
    for account in result.json():
        lastseen = account["lastseen"]
        datetime_object = datetime.strptime(lastseen, "%Y-%m-%dT%H:%M:%S.%fZ")
        beauty_date = datetime_object.strftime("%B %d, %Y %I:%M %p")
        msg += f"{account['account']} was last seen on {beauty_date}\n"

    return msg


def create_options_embed():
    embed = discord.Embed(
        title="Commands:",
        description="React to make your choice:",
        color=discord.Color.green(),
    )
    embed.add_field(name="Quit", value="🛑", inline=True)
    embed.add_field(name="Whisper", value="🗣️", inline=True)
    embed.add_field(name="Online", value="💻", inline=True)
    embed.add_field(name='Screenshot', value='📷', inline=True)

    return embed


def create_accounts_embed(data):

    embed = discord.Embed(
        title="Accounts:",
        description="React to make your choice:",
        color=discord.Color.green(),
    )

    for i, account in enumerate(data):
        if i >= len(EMOJI_NUMBERS):
            break
        embed.add_field(
            name=f'{EMOJI_NUMBERS[i]} {account["account"]}', value="\u200b", inline=True
        )

    return embed


def create_available_accounts_embed(data):

    embed = discord.Embed(
        title="Accounts:",
        description="React to make your choice:",
        color=discord.Color.green(),
    )

    for i, account in enumerate(data):
        if i >= len(EMOJI_NUMBERS):
            break
        embed.add_field(
            name=f'{EMOJI_NUMBERS[i]} {account["accountname"]}', value="", inline=True
        )

    return embed


bot.run(os.environ["DISCORD_TOKEN"])
