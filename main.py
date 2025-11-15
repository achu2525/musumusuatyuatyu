import discord
from discord.ext import commands
import time
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ユーザー管理
message_history = {}   # {user_id: [timestamps]}
warning_count = {}     # {user_id: 警告回数}
timeout_users = {}     # {user_id: timeout_end_timestamp}

TIMEOUT_DURATION = 180  # 秒 (3分)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id
    now = time.time()

    # ------------------------------
    # タイムアウト中のユーザー
    # ------------------------------
    if user_id in timeout_users:
        if now < timeout_users[user_id]:
            try:
                await message.delete()
            except discord.Forbidden:
                pass
            return
        else:
            # タイムアウト終了
            del timeout_users[user_id]
            warning_count[user_id] = 0  # 警告リセット

    content = message.content

    # ------------------------------
    # ① 同じ文字が5文字以上
    # ------------------------------
    spam_detected = False
    for char in set(content):
        if content.count(char) >= 5:
            spam_detected = True
            break

    # ------------------------------
    # ② 連投（5秒以内に3回）
    # ------------------------------
    if user_id not in message_history:
        message_history[user_id] = []
    message_history[user_id].append(now)
    message_history[user_id] = [t for t in message_history[user_id] if now - t <= 5]
    if len(message_history[user_id]) >= 3:
        spam_detected = True

    if spam_detected:
        try:
            await message.delete()
        except discord.Forbidden:
            pass

        count = warning_count.get(user_id, 0)

        if count == 0:
            # 一回目の警告
            warning_count[user_id] = 1
            if len(content) >= 5:
                await message.channel.send(f"⚠️ {message.author.mention} 文字が多すぎます！次にスパムを行うと3分間のタイムアウトです！")
            else:
                await message.channel.send(f"⚠️ {message.author.mention} 連投が多すぎます！ 次にスパムを行うと3分間のタイムアウトです！")
        else:
            # 二回目でタイムアウト
            timeout_users[user_id] = now + TIMEOUT_DURATION
            warning_count[user_id] = 0  # リセット
            await message.channel.send(f"⚠️ {message.author.mention} 3分間タイムアウトです！")
        return

    await bot.process_commands(message)

bot.run(os.getenv("BOT_TOKEN"))
