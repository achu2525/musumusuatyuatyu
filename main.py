import discord
from discord.ext import commands
import os
import time
from collections import defaultdict
import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ユーザー管理
message_history = defaultdict(list)  # {user_id: [timestamps]}
warning_count = defaultdict(int)     # {user_id: 警告回数}

TIMEOUT_DURATION = 300  # 秒（5分）
REPEAT_THRESHOLD = 5    # 文字連続回数
SPAM_COUNT = 5          # 連投回数
SPAM_INTERVAL = 3       # 秒

def has_repeated_char(content, threshold=REPEAT_THRESHOLD):
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
    # メッセージ履歴更新（連投判定用）
    # ------------------------------
    message_history[user_id].append(now)
    message_history[user_id] = [t for t in message_history[user_id] if now - t <= SPAM_INTERVAL]

    # ------------------------------
    # スパム判定
    # ------------------------------
    spam_detected = has_repeated_char(content) or len(message_history[user_id]) >= SPAM_COUNT

    if spam_detected:
        # メッセージ削除
        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass

        # 警告・タイムアウト処理（絶対に1回だけ）
        if warning_count[user_id] == 0:
            # 1回目警告
            warning_count[user_id] = 1
            await message.channel.send(
                f"⚠️ {message.author.mention} 次にスパムを行うと5分間のタイムアウトです！"
            )
        else:
            # 2回目 → タイムアウト
            warning_count[user_id] = 0
            member = message.author
            try:
                timeout_until = discord.utils.utcnow() + datetime.timedelta(seconds=TIMEOUT_DURATION)
                await member.timeout(timeout_until)
                await message.channel.send(
                    f"⚠️ {member.mention} 5分間タイムアウトです！"
                )
            except discord.Forbidden:
                await message.channel.send(
                    f"⚠️ {member.mention} タイムアウトに失敗しました。権限を確認してください。"
                )
        return  # ここで処理を終えて二重警告を防ぐ

    # ------------------------------
    # 通常のコマンド処理
    # ------------------------------
    await bot.process_commands(message)

bot.run(os.getenv("BOT_TOKEN"))
