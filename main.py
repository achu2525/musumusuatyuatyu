import discord
from discord.ext import commands
import time
import os
import datetime
from collections import Counter

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True  # タイムアウトには必要

bot = commands.Bot(command_prefix="!", intents=intents)

# ユーザー管理
message_history = {}  # {user_id: [timestamps]}
warning_count = {}    # {user_id: 警告回数}

TIMEOUT_DURATION = 300  # 秒 (5分)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

def has_five_or_more_chars(content, threshold=5):
    """文章の中で同じ文字が threshold 回以上出現しているか判定"""
    counts = Counter(content)
    for char, count in counts.items():
        if count >= threshold:
            return True
    return False

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id
    now = time.time()
    content = message.content
    spam_detected = False

    # ------------------------------
    # ① 同じ文字が文章内で5回以上
    # ------------------------------
    if has_five_or_more_chars(content, 5):
        spam_detected = True

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
        # メッセージ削除
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
            warning_count[user_id] = 0
            member = message.author
            try:
                timeout_until = datetime.datetime.utcnow() + datetime.timedelta(seconds=TIMEOUT_DURATION)
                await member.edit(timeout=timeout_until)
                await message.channel.send(f"⚠️ {member.mention} 5分間タイムアウトです！")
            except discord.Forbidden:
                await message.channel.send(
                    f"⚠️ {member.mention} タイムアウトに失敗しました。権限を確認してください。"
                )
        return

    await bot.process_commands(message)

bot.run(os.getenv("BOT_TOKEN"))
