"""
SB244Luckybot — Telegram Bot
Sends daily productivity, focus, and life-skill tips on request or subscription.

Run locally:
    export BOT_TOKEN="your-token-from-botfather"
    python bot.py

Deployed on Railway, BOT_TOKEN is read from an environment variable you set
in the Railway dashboard (Variables tab) — never hard-code it in this file.
"""

import json
import logging
import os
import random
from datetime import time as dtime

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

SUBSCRIBERS_FILE = "subscribers.json"

# ---------------------------------------------------------------------------
# CONTENT LIBRARY — add new entries any time, no other code needs to change
# ---------------------------------------------------------------------------

TIPS = [
    {
        "title": "⏱️ The Two-Minute Rule",
        "body": (
            "If a task takes less than two minutes, do it immediately instead of "
            "adding it to a list.\n\n"
            "Small tasks pile up mental clutter faster than they take to actually finish."
        ),
    },
    {
        "title": "🎯 Single-Tasking Beats Multitasking",
        "body": (
            "Switching between tasks has a real cost — your brain needs time to "
            "re-focus every time you switch.\n\n"
            "Block focused time for one task at a time instead of juggling several."
        ),
    },
    {
        "title": "🧩 The Eisenhower Matrix",
        "body": (
            "Sort tasks into four boxes: urgent+important, important but not urgent, "
            "urgent but not important, neither.\n\n"
            "Most people spend too much time on 'urgent but not important' tasks that "
            "feel productive but don't move anything forward."
        ),
    },
    {
        "title": "🌱 Habit Stacking",
        "body": (
            "Attach a new habit to an existing one: 'After I [current habit], I will "
            "[new habit].'\n\n"
            "Using an existing routine as a trigger makes new habits far easier to stick to."
        ),
    },
    {
        "title": "🔋 Protect Your Peak Hours",
        "body": (
            "Most people have 2-4 hours a day where focus and energy are naturally "
            "highest.\n\n"
            "Guard that window for your hardest, highest-value work — not email or "
            "meetings."
        ),
    },
    {
        "title": "📝 Write Tomorrow's Plan Tonight",
        "body": (
            "Deciding your top 3 priorities the night before removes the decision "
            "fatigue of figuring it out in the morning.\n\n"
            "You start the day already moving instead of still deciding what to do."
        ),
    },
    {
        "title": "🛑 The Power of Saying No",
        "body": (
            "Every 'yes' to a new commitment is a 'no' to something else — usually "
            "your own priorities.\n\n"
            "Protecting your time deliberately is not selfish; it's what makes focused "
            "work possible."
        ),
    },
    {
        "title": "🔄 Review Weekly, Not Just Daily",
        "body": (
            "A short weekly review — what worked, what didn't, what's next — catches "
            "patterns that day-to-day planning misses.\n\n"
            "Fifteen minutes a week can save hours of drift."
        ),
    },
]

WELCOME_MESSAGE = (
    "👋 Welcome!\n\n"
    "This bot sends you short, practical tips on productivity, focus, and "
    "building better habits.\n\n"
    "Commands:\n"
    "/tip — get a random tip\n"
    "/subscribe — get a daily tip automatically\n"
    "/unsubscribe — stop daily tips\n"
    "/help — show this message again"
)

# ---------------------------------------------------------------------------
# SUBSCRIBER STORAGE
# ---------------------------------------------------------------------------


def load_subscribers() -> set:
    if os.path.exists(SUBSCRIBERS_FILE):
        with open(SUBSCRIBERS_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_subscribers(subscribers: set) -> None:
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump(list(subscribers), f)


subscribers = load_subscribers()

# ---------------------------------------------------------------------------
# COMMAND HANDLERS
# ---------------------------------------------------------------------------


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(WELCOME_MESSAGE)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(WELCOME_MESSAGE)


async def tip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pick = random.choice(TIPS)
    text = f"{pick['title']}\n\n{pick['body']}"
    await update.message.reply_text(text)


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        await update.message.reply_text("You're already subscribed to daily tips.")
        return
    subscribers.add(chat_id)
    save_subscribers(subscribers)
    await update.message.reply_text(
        "✅ Subscribed! You'll get one tip a day. Use /unsubscribe to stop anytime."
    )


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id not in subscribers:
        await update.message.reply_text("You're not currently subscribed.")
        return
    subscribers.discard(chat_id)
    save_subscribers(subscribers)
    await update.message.reply_text("You've been unsubscribed from daily tips.")


async def send_daily_tip(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Runs once a day, sends one random tip to every subscriber."""
    if not subscribers:
        return
    pick = random.choice(TIPS)
    text = f"{pick['title']}\n\n{pick['body']}"
    for chat_id in list(subscribers):
        try:
            await context.bot.send_message(chat_id=chat_id, text=text)
        except Exception as exc:
            logger.warning("Failed to send to %s: %s", chat_id, exc)


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------


def main() -> None:
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "BOT_TOKEN environment variable is not set. "
            "Set it locally with `export BOT_TOKEN=...` or in Railway's Variables tab."
        )

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("tip", tip))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))

    # Daily tip at 09:00 UTC — adjust the hour to suit your audience's timezone.
    job_queue = application.job_queue
    job_queue.run_daily(send_daily_tip, time=dtime(hour=9, minute=0))

    logger.info("Bot starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
