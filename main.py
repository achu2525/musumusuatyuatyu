import discord
from discord.ext import commands
import time
import os
from collections import Counter
import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True  # タイムアウトには必須

bot = commands.Bot(command_prefix="!", intents=intents)

# ------------------------------
# ユーザー管理
# ------------------------------
message_history = {}  # {user_id: [timestamps]}
warning_count = {}    # {user_id: 警告回数}

TIMEOUT_DURATION = 300  # 秒 (5分)

# ------------------------------
# 関数: 同じ文字が5回以上あるか
# ------------------------------
def has_five_or_more_chars(content, threshold=5):
    counts = Counter(content)
    for count in counts.values():
        if count >= threshold:
            return True
    return False

# ------------------------------
# ボット起動
# ------------------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# ------------------------------
# メッセージ監視
# ------------------------------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id
    now = time.time()
    content = message.content
    spam_detected = False

    # ------------------------------
    # ① 文章内の文字が5回以上
    # ------------------------------
    if has_five_or_more_chars(content, 5):
        spam_detected = True

    # ------------------------------
    # ② 連投（5秒以内に3回以上）
    # ------------------------------
    if user_id not in message_history:
        message_history[user_id] = []
    message_history[user_id].append(now)
    # 古い履歴を削除
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
        member = message.author

        if count == 0:
            # 一回目の警告
            warning_count[user_id] = 1
            await message.channel.send(
                f"⚠️ {member.mention} 次にスパムを行うと5分間のタイムアウトです！"
            )
        else:
            # 二回目 → Discord タイムアウト
            warning_count[user_id] = 0
            try:
                timeout_until = datetime.datetime.utcnow() + datetime.timedelta(seconds=TIMEOUT_DURATION)
                await member.edit(timeout=timeout_until)
                await message.channel.send(
                    f"⚠️ {member.mention} 5分間タイムアウトです！"
                )
            except discord.Forbidden:
                await message.channel.send(
                    f"⚠️ {member.mention} タイムアウトに失敗しました。権限を確認してください。"
                )
        return

    await bot.process_commands(message)

bot.run(os.getenv("BOT_TOKEN"))
