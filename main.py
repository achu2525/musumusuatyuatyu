import discord
from discord.ext import commands
import time
import os

# intentsの設定
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

    # ------------------------------
    # ① 文章内に同じ文字が5回以上
    # ------------------------------
    for char in set(content):
        if content.count(char) >= 5:
            try:
                await message.delete()
            except discord.Forbidden:
                pass
            try:
                await message.channel.send(
                    f"⚠️ {message.author.mention} 渓谷です！"
                )
            except discord.Forbidden:
                pass
            return  # ここで処理終了

    # ------------------------------
    # ② 5秒以内に3回以上投稿（連投）
    # ------------------------------
    user_id = message.author.id
    now = time.time()

    if user_id not in message_history:
        message_history[user_id] = []

    message_history[user_id].append(now)

    # 5秒より前の履歴を削除
    message_history[user_id] = [
        t for t in message_history[user_id] if now - t <= 5
    ]

    # 3回以上なら削除＋警告
    if len(message_history[user_id]) >= 3:
        try:
            await message.delete()
        except discord.Forbidden:
            pass
        try:
            await message.channel.send(
                f"⚠️ {message.author.mention} 連投が多すぎます！"
            )
        except discord.Forbidden:
            pass
        return

    await bot.process_commands(message)

# Bot起動
bot.run(os.getenv("BOT_TOKEN"))
