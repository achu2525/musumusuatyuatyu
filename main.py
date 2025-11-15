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
message_history = defaultdict(list)
warning_count = defaultdict(int)

TIMEOUT_DURATION = 300  # 秒（5分）

def has_repeated_char(content, threshold=5):
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
    # メッセージ履歴更新
    # ------------------------------
    message_history[user_id].append(now)
    # 古い履歴を削除
    message_history[user_id] = [t for t in message_history[user_id] if now - t <= 3]

    # ------------------------------
    # スパム判定（文字5回以上 OR 3秒以内に5回連投）
    # ------------------------------
    spam_detected = has_repeated_char(content, 5) or len(message_history[user_id]) >= 5

    if spam_detected:
        # ------------------------------
        # メッセージ削除
        # ------------------------------
        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass

        # ------------------------------
        # 警告・タイムアウト処理
        # ------------------------------
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

    await bot.process_commands(message)

bot.run(os.getenv("BOT_TOKEN"))
