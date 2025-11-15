import discord
from discord.ext import commands
import os
import time
from collections import defaultdict
import datetime
import re
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ユーザー管理
message_history = defaultdict(list)   # {user_id: [timestamps]}
warning_count = defaultdict(int)      # {user_id: 警告回数}
user_locks = defaultdict(asyncio.Lock)  # ユーザーごとの警告ロック

TIMEOUT_DURATION = 300  # 秒（5分）
REPEAT_THRESHOLD = 5   # 同じ文字の出現回数
SPAM_COUNT = 5         # 連投回数
SPAM_INTERVAL = 3      # 秒

def find_repeated_substrings(content, threshold=REPEAT_THRESHOLD):
    """文字が threshold 回以上文章内で出現している文字を返す"""
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

    spam_detected = False

    # ------------------------------
    # 文字の出現回数判定
    # ------------------------------
    if find_repeated_substrings(content):
        spam_detected = True

    # ------------------------------
    # 連投判定
    # ------------------------------
    message_history[user_id].append(now)
    # 古い履歴を削除
    message_history[user_id] = [t for t in message_history[user_id] if now - t <= SPAM_INTERVAL]
    if len(message_history[user_id]) >= SPAM_COUNT:
        spam_detected = True

    # ------------------------------
    # スパム検出時の処理
    # ------------------------------
    if spam_detected:
        # メッセージ削除
        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass

        # ユーザーごとのロックで警告・タイムアウトを一回だけ
        async with user_locks[user_id]:
            if warning_count[user_id] == 0:
                warning_count[user_id] = 1
                await message.channel.send(
                    f"⚠️ {message.author.mention} 次にスパムを行うと5分間のタイムアウトです！"
                )
            else:
                warning_count[user_id] = 0
                member = message.author
                timeout_until = discord.utils.utcnow() + datetime.timedelta(seconds=TIMEOUT_DURATION)
                try:
                    await member.timeout(timeout_until)
                    await message.channel.send(
                        f"⚠️ {member.mention} 5分間タイムアウトです！"
                    )
                except discord.Forbidden:
                    await message.channel.send(
                        f"⚠️ {member.mention} タイムアウトに失敗しました。権限を確認してください。"
                    )
        return  # ここで処理を終了し二重警告を防ぐ

    # ------------------------------
    # 通常のコマンド処理
    # ------------------------------
    await bot.process_commands(message)

bot.run(os.getenv("BOT_TOKEN"))
