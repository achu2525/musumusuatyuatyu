import discord
from discord.ext import commands
import time
import re
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
message_history = {}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content
    user_id = message.author.id
    now = time.time()

    # 同じ文字5回以上
    if re.search(r'(.)\1{4,}', content):
        try:
            await message.delete()
        except discord.Forbidden:
            pass
        try:
            await message.channel.send(f"⚠️ {message.author.mention} 同じ文字が多すぎます！")
        except discord.Forbidden:
            pass
        return

    # 連投（5秒以内に3回以上）
    if user_id not in message_history:
        message_history[user_id] = []

    message_history[user_id].append(now)
    message_history[user_id] = [t for t in message_history[user_id] if now - t <= 5]

    if len(message_history[user_id]) >= 3:
        try:
            await message.delete()
        except discord.Forbidden:
            pass
        try:
            await message.channel.send(f"⚠️ {message.author.mention} 連投が多すぎます！")
        except discord.Forbidden:
            pass

    await bot.process_commands(message)

bot.run(os.getenv("BOT_TOKEN"))
