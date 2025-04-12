# OPENAI VERSION CHECK
import openai
print("OPENAI VERSION:", openai.__version__)

# DISCORD + SYSTEM IMPORTS
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import requests
import json

# ENV VARS
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
openai.api_key = os.getenv("OPENAI_API_KEY")

# DISCORD BOT CONFIG
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# 🔁 UPDATED MEMORY SERVER ENDPOINT (via Vercel Proxy)
MEMORY_ENDPOINT = "https://memory-proxy-albrenus.vercel.app/api/memory"

# SYNC MEMORY ON STARTUP
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    try:
        response = requests.get(MEMORY_ENDPOINT)
        memory_data = response.json()
        print("✅ Synced memory from shared server:")
        print(memory_data)
    except Exception as e:
        print(f"❌ Failed to sync memory on startup: {e}")

# BASIC PING
@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

# GPT COMMANDS
@bot.command(name="gpt")
async def gpt35(ctx, *, message):
    await handle_gpt_request(ctx, message, model="gpt-3.5-turbo")

@bot.command(name="gpt4")
async def gpt4(ctx, *, message):
    await handle_gpt_request(ctx, message, model="gpt-4")

# HANDLE GPT REQUEST
async def handle_gpt_request(ctx, message, model):
    try:
        print(f"[{model}] Message to GPT:", message)

        # 🔄 Pull latest memory from sync server
        memory_response = requests.get(MEMORY_ENDPOINT)
        memory_data = memory_response.json()

        # SYSTEM PROMPT WITH MEMORY INCLUDED
        system_prompt = (
            "You are ChatGPT, a helpful assistant who knows albre. "
            f"Use the following shared memory when responding: {json.dumps(memory_data)}"
        )

        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
        )

        reply = response["choices"][0]["message"]["content"]
        print("OpenAI reply:", reply)
        await ctx.send(reply[:2000])
    except Exception as e:
        print("Error occurred:", e)
        await ctx.send(f"Error: {e}")

# CHANNEL CHAT SUMMARIZER
@bot.command()
async def summarize(ctx, channel_name: str):
    channel = discord.utils.get(ctx.guild.text_channels, name=channel_name)
    if channel is None:
        await ctx.send("Channel not found.")
        return

    messages = []
    async for msg in channel.history(limit=50):
        if msg.author != bot.user:
            messages.append(f"{msg.author.name}: {msg.content}")

    convo = "\n".join(reversed(messages))

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Summarize the following chat history as if you're a helpful assistant tracking someone's progress or vibe."},
                {"role": "user", "content": convo}
            ]
        )
        reply = response["choices"][0]["message"]["content"]
        await ctx.send(reply[:2000])
    except Exception as e:
        await ctx.send(f"Error: {e}")

# VIEW MEMORY COMMAND
@bot.command()
async def memory(ctx):
    try:
        response = requests.get(MEMORY_ENDPOINT)
        memory_data = response.json()
        await ctx.send(f"🧠 Current memory: {memory_data}")
    except Exception as e:
        await ctx.send(f"⚠️ Error reading memory: {e}")

# ADD TO MEMORY COMMAND
@bot.command()
async def remember(ctx, key: str, *, value: str):
    try:
        data = {key: value}
        response = requests.post(MEMORY_ENDPOINT, json=data)
        if response.status_code == 200:
            await ctx.send(f"🧠 Got it! Remembered `{key}` as `{value}`.")
        else:
            await ctx.send("❌ Failed to update memory.")
    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")

# SYNC CHECK COMMAND
@bot.command()
async def checksync(ctx):
    try:
        response = requests.get(MEMORY_ENDPOINT)
        memory_data = response.json()

        if "favorite_support_marvel_rivals" in memory_data:
            await ctx.send(f"✅ Synced! Your favorite Marvel Rivals support is: **{memory_data['favorite_support_marvel_rivals']}**")
        else:
            await ctx.send("❌ Not synced yet. Still waiting for ChatGPT to update the memory.")
    except Exception as e:
        await ctx.send(f"⚠️ Error checking sync status: {e}")

# RUN BOT
bot.run(TOKEN)
