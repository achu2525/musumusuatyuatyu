import discord
from discord.ext import commands
import time
import os
from collections import defaultdict
import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True  # タイムアウトに必要

bot = commands.Bot(command_prefix="!", intents=intents)

# ユーザー管理
message_history = defaultdict(list)  # {user_id: [timestamps]}
warning_count = defaultdict(int)     # {user_id: 警告回数}
timeout_users = {}                   # {user_id: timeout_end_timestamp}

TIMEOUT_DURATION = 300  # 5分

def has_repeated_char(content, threshold=5):
    """文章内で同じ文字が threshold 回以上出現したら True"""
    counts = {}
    for c in content:
        counts[c] = counts.get(c, 0) + 1
        if counts[c] >= threshold:
            return True
    return False

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id
    now = time.time()
    content = message.content

    # ------------------------------
    # タイムアウト中のユーザー
    # ------------------------------
    if user_id in timeout_users:
        if now < timeout_users[user_id]:
            try:
                await message.delete()
            except (discord.Forbidden, discord.NotFound):
                pass
            await message.channel.send(f"⚠️ {message.author.mention} タイムアウト中なのでしゃべれません。", delete_after=5)
            return
        else:
            # タイムアウト終了
            del timeout_users[user_id]
            warning_count[user_id] = 0  # リセット

    spam_detected = False

    # ------------------------------
    # 文字が5回以上出現
    # ------------------------------
    if has_repeated_char(content, 5):
        spam_detected = True

    # ------------------------------
    # 連投（5秒以内に3回以上）
    # ------------------------------
    message_history[user_id].append(now)
    message_history[user_id] = [t for t in message_history[user_id] if now - t <= 5]
    if len(message_history[user_id]) >= 3:
        spam_detected = True

    if spam_detected:
        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass

        count = warning_count[user_id]

        if count == 0:
            # 1回目警告
            warning_count[user_id] = 1
            await message.channel.send(
                f"⚠️ {message.author.mention} 次にスパムを行うと5分間のタイムアウトです！"
            )
        else:
            # 2回目 → Discord 公式タイムアウト
            warning_count[user_id] = 0
            member = message.author
            try:
                timeout_until = datetime.datetime.utcnow() + datetime.timedelta(seconds=TIMEOUT_DURATION)
                await member.timeout(duration=datetime.timedelta(seconds=TIMEOUT_DURATION))
                timeout_users[user_id] = now + TIMEOUT_DURATION
                await message.channel.send(f"⚠️ {member.mention} 5分間タイムアウトです！")
            except discord.Forbidden:
                await message.channel.send(
                    f"⚠️ {member.mention} タイムアウトに失敗しました。権限を確認してください。"
                )
        return

    await bot.process_commands(message)

bot.run(os.getenv("BOT_TOKEN"))
