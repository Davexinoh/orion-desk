from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from uuid import uuid4

from .format_receipt import format_receipt
from .store import STORE

_APP = None


async def start_telegram() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return
    try:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
        from telegram.ext import (
            Application,
            CallbackQueryHandler,
            CommandHandler,
            ContextTypes,
            MessageHandler,
            filters,
        )
    except ImportError:
        print("python-telegram-bot not installed; skipping Telegram.")
        return

    from .agent import apply_resolution, run_goal

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(
            "Orion Desk.\n\n"
            "Say the outcome. I will gather context, do the safe work, "
            "and ask before anything goes out.\n\n"
            "Try: I have a client meeting with Acme tomorrow at 2 PM. Handle it."
        )

    async def memory_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        items = STORE.snapshot()["memory"][:8]
        if not items:
            await update.message.reply_text("Nothing stored yet.")
            return
        lines = []
        for m in items:
            lines.append(f"{m['layer'].upper()}  {m['title']}\n{m['body']}")
        await update.message.reply_text("\n\n".join(lines))

    async def receipts_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        recs = STORE.snapshot()["receipts"][:5]
        if not recs:
            await update.message.reply_text("No receipts yet. Give me something to handle.")
            return
        body = "\n".join(f"{r['id']}  {r['status']}  \"{r['intent']}\"" for r in recs)
        await update.message.reply_text(body)

    async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        intent = (update.message.text or "").strip()
        if not intent:
            return
        status = await update.message.reply_text("On it.")
        gid = f"tg-{uuid4().hex[:8]}"
        goal = {
            "id": gid,
            "receipt_id": "",
            "intent": intent,
            "status": "running",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "live_trace": ["On it."],
            "artifacts": [],
            "source": "telegram",
        }
        STORE.upsert_goal(goal)
        task = asyncio.create_task(run_goal(gid, intent))
        last = "On it."
        while not task.done():
            await asyncio.sleep(0.35)
            g = STORE.get_goal(gid)
            rec = STORE.get_receipt(g.get("receipt_id") or "") if g else None
            if rec:
                text = format_receipt(rec)
                if text != last:
                    await status.edit_text(text)
                    last = text
        receipt = await task
        text = format_receipt(receipt)
        if receipt.get("pending_actions"):
            action = receipt["pending_actions"][0]
            kb = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Do it",
                            callback_data=f"ok:{receipt['id']}:{action['id']}",
                        ),
                        InlineKeyboardButton(
                            "Keep as draft",
                            callback_data=f"no:{receipt['id']}:{action['id']}",
                        ),
                    ]
                ]
            )
            await status.edit_text(text, reply_markup=kb)
        else:
            await status.edit_text(text)
            for art in (STORE.get_goal(gid) or {}).get("artifacts") or []:
                body = f"{art['title']}\n\n{art['body']}"
                await update.message.reply_text(body[:3500])

    async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        q = update.callback_query
        await q.answer()
        data = q.data or ""
        parts = data.split(":")
        if len(parts) != 3:
            return
        kind, rid, action_id = parts
        outcome = "approved" if kind == "ok" else "declined"
        nxt = await apply_resolution(rid, action_id, outcome)
        if not nxt:
            await q.edit_message_text("That receipt is gone.")
            return
        await q.edit_message_text(format_receipt(nxt))
        note = "Sent. The receipt is closed." if outcome == "approved" else "Held. Nothing went out."
        await q.message.reply_text(note)

    global _APP
    application = Application.builder().token(token).build()
    _APP = application
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("memory", memory_cmd))
    application.add_handler(CommandHandler("receipts", receipts_cmd))
    application.add_handler(CallbackQueryHandler(on_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    async def _runner() -> None:
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        print("Telegram bot polling.")

    asyncio.create_task(_runner())
