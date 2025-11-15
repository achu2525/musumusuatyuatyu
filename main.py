import discord
from discord.ext import commands
import time
import os
import re

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ユーザー管理
message_history = {}   # {user_id: [timestamps]}
warning_count = {}     # {user_id: 警告回数}
timeout_users = {}     # {user_id: timeout_end_timestamp}

TIMEOUT_DURATION = 300  # 秒 (5分)

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
            except (discord.Forbidden, discord.NotFound):
                pass
            return
        else:
            # タイムアウト終了
            del timeout_users[user_id]
            warning_count[user_id] = 0  # 警告リセット

    content = message.content
    spam_detected = False

    # ------------------------------
    # ① 同じ文字が5文字以上連続
    # ------------------------------
    if re.search(r'(.)\1{4,}', content):
        spam_detected = True

    # ------------------------------
    # ② 連投（5秒以内に3回以上）
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
        except (discord.Forbidden, discord.NotFound):
            pass

        count = warning_count.get(user_id, 0)

        if count == 0:
            # 一回目の警告
            warning_count[user_id] = 1
            await message.channel.send(
                f"⚠️ {message.author.mention} 次にスパムを行うと5分間のタイムアウトです！"
            )
        else:
            # 二回目でタイムアウト
            timeout_users[user_id] = now + TIMEOUT_DURATION
            warning_count[user_id] = 0  # リセット
            await message.channel.send(
                f"⚠️ {message.author.mention} 5分間タイムアウトです！"
            )
        return

    await bot.process_commands(message)

bot.run(os.getenv("BOT_TOKEN"))
