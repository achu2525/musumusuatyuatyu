import discord
from discord.ext import commands
import time
import os
import re
import datetime  # タイムアウト用

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True  # タイムアウトを使う場合は必須

bot = commands.Bot(command_prefix="!", intents=intents)

# ユーザー管理
message_history = {}   # {user_id: [timestamps]}
warning_count = {}     # {user_id: 警告回数}

TIMEOUT_DURATION = 300  # 5分

def is_repeated_pattern(content, min_length=5):
    """
    文章の中で5文字以上の繰り返しパターンがあればTrue
    例: abababab -> abの繰り返し
    """
    if len(content) < min_length:
        return False
    for size in range(1, len(content)//2 + 1):
        pattern = content[:size]
        repeats = len(content) // size
        if pattern * repeats == content:
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
    # ① 同じ文字5文字以上または繰り返しパターン
    # ------------------------------
    if len(content) >= 5 and (re.search(r'(.)\1{4,}', content) or is_repeated_pattern(content, 5)):
        spam_detected = True

    # ------------------------------
    # ② 連投（5秒以内3回以上）
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
        member = message.author

        if count == 0:
            # 一回目の警告
            warning_count[user_id] = 1
            await message.channel.send(
                f"⚠️ {member.mention} 次にスパムを行うと5分間のタイムアウトです！"
            )
        else:
            # 二回目でDiscordタイムアウト
            warning_count[user_id] = 0
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
