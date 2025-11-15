import discord
from discord.ext import commands
import time
import re

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ユーザーごとの投稿時間
message_history = {}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content

    # ------ ① 同じ文字が7回以上 ------
    if re.search(r'(.)\1{6,}', content):
        await message.reply("⚠️ 同じ文字の連続が多すぎます！")
        return

    # ------ ② 連投（8秒以内に3回以上） ------
    user_id = message.author.id
    now = time.time()

    if user_id not in message_history:
        message_history[user_id] = []

    message_history[user_id].append(now)

    # 8秒より前の履歴を削除
    message_history[user_id] = [
        t for t in message_history[user_id] if now - t <= 8
    ]

    # 3回以上なら警告
    if len(message_history[user_id]) >= 3:
        await message.reply("⚠️ 連投が多すぎます！")

    await bot.process_commands(message)

# Bot起動
bot.run("BOT_TOKEN")


