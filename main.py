import discord
from discord.ext import commands
import time
import re
import os  # 環境変数読み込み用

intents = discord.Intents.default()
intents.message_content = True  # Privileged Intent 必須

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
    user_id = message.author.id
    now = time.time()

    # ------ ① 同じ文字が5回以上 ------
    if re.search(r'(.)\1{4,}', content):  # {4,} → 5文字以上
        await message.delete()  # メッセージを削除
        await message.channel.send(f"⚠️ {message.author.mention} 渓谷です！")
        return

    # ------ ② 連投（5秒以内に3回以上） ------
    if user_id not in message_history:
        message_history[user_id] = []

    message_history[user_id].append(now)

    # 5秒より前の履歴を削除
    message_history[user_id] = [
        t for t in message_history[user_id] if now - t <= 5
    ]

    if len(message_history[user_id]) >= 3:
        await message.delete()
        await message.channel.send(f"⚠️ {message.author.mention} 連投が多すぎます！")

    await bot.process_commands(message)

# Bot起動
bot.run(os.getenv("BOT_TOKEN"))
