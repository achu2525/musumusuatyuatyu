import discord
from discord.ext import commands
import os
import time
from collections import defaultdict
import datetime
import re

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ユーザー管理
message_history = defaultdict(list)
warning_count = defaultdict(int)

TIMEOUT_DURATION = 300  # 秒（5分）
REPEAT_THRESHOLD = 5
SPAM_COUNT = 5
SPAM_INTERVAL = 3  # 秒

def find_repeated_substrings(content, threshold=REPEAT_THRESHOLD):
    """文字が threshold 回以上連続している部分を返す"""
    pattern = re.compile(r"(.)\1{" + str(threshold-1) + r",}")
    return pattern.findall(content)

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
    reason = None

    # ------------------------------
    # 文字連続判定
    # ------------------------------
    repeated_chars = find_repeated_substrings(content)
    if repeated_chars:
        spam_detected = True
        reason = "文字連続"

    # ------------------------------
    # 連投判定
    # ------------------------------
    message_history[user_id].append(now)
    message_history[user_id] = [t for t in message_history[user_id] if now - t <= SPAM_INTERVAL]
    if len(message_history[user_id]) >= SPAM_COUNT:
        spam_detected = True
        if not reason:
            reason = "連投"

    # ------------------------------
    # スパム検出時
    # ------------------------------
    if spam_detected:
        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass

        # 警告は1回だけ
        if warning_count[user_id] == 0:
            warning_count[user_id] = 1
            warn_msg = f"⚠️ {message.author.mention} 次にスパムを行うと5分間のタイムアウトです！"
        else:
            warning_count[user_id] = 0
            member = message.author
            try:
                timeout_until = discord.utils.utcnow() + datetime.timedelta(seconds=TIMEOUT_DURATION)
                await member.timeout(timeout_until)
                warn_msg = f"⚠️ {member.mention} 5分間タイムアウトです！"
            except discord.Forbidden:
                warn_msg = f"⚠️ {member.mention} タイムアウトに失敗しました。権限を確認してください。"

        # 警告メッセージ送信（必ず一回だけ）
        await message.channel.send(warn_msg)
        return

    await bot.process_commands(message)

bot.run(os.getenv("BOT_TOKEN"))
