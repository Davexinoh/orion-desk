from __future__ import annotations

import asyncio
import os

from .approvals import ApprovalError, do_approval, keep_draft, list_needed
from .mission_store import MISSIONS
from .runner import run_mission
from .users import USERS

_APP = None
_STARTED = False

_STATUS = {
    "waiting_on_you": "Waiting on you",
    "running": "Running",
    "queued": "Running",
    "done": "Done",
    "failed": "Failed",
    "draft": "Draft",
    "idle": "Idle",
}


def _origin() -> str:
    return (os.getenv("APP_ORIGIN") or "").rstrip("/")


def _desk_url() -> str:
    origin = _origin()
    return f"{origin}/desk" if origin else "/desk"


def _signin_url() -> str:
    origin = _origin()
    return f"{origin}/sign-in" if origin else "/sign-in"


def _linked_user(update) -> dict | None:
    user = update.effective_user
    if not user:
        return None
    return USERS.by_telegram(str(user.id))


def _ids(mission: dict) -> str:
    mid = str(mission.get("id") or "")
    rec = mission.get("receipt") or {}
    rid = str(rec.get("id") or "")
    if mid and rid:
        return f"{mid} · {rid}"
    return mid or rid


def is_fake_receipt(mission: dict) -> bool:
    rec = mission.get("receipt") or {}
    if str(rec.get("id") or "") == "#00001":
        return True
    for step in list(mission.get("steps") or []) + list(rec.get("steps") or []):
        if "Work product generated" in (step.get("label") or ""):
            return True
    return False


def mission_card(mission: dict) -> str:
    status = _STATUS.get(mission.get("status") or "", "Running")
    intent = (mission.get("intent") or "").strip()
    steps = mission.get("steps") or []
    done = sum(1 for s in steps if s.get("state") == "done" or s.get("status") == "done")
    total = len(steps)
    tools = mission.get("tools") or []
    tools_s = " · ".join(tools) if tools else "—"
    ids = _ids(mission)
    return (
        "ORION DESK\n"
        f"{ids}\n"
        f"Mission · {status}\n"
        f"{intent}\n"
        f"{done}/{total} steps\n"
        f"{tools_s}"
    )


def tick_lines(mission: dict, limit: int = 8) -> str:
    lines: list[str] = []
    for step in mission.get("steps") or []:
        ev = (step.get("evidence") or step.get("detail") or "").strip()
        label = (step.get("label") or "").strip()
        line = ev or label
        if not line:
            continue
        if "Work product generated" in line:
            continue
        lines.append(line)
        if len(lines) >= limit:
            break
    return "\n".join(lines)


def mission_reply(mission: dict) -> str:
    parts = [mission_card(mission)]
    ticks = tick_lines(mission)
    if ticks:
        parts.append(ticks)
    return "\n\n".join(parts)[:4000]


def compact_receipt(mission: dict) -> str:
    parts = [mission_card(mission)]
    ticks = tick_lines(mission)
    if ticks:
        parts.append(ticks)
    rec = mission.get("receipt") or {}
    elapsed = rec.get("execution_time_seconds")
    if elapsed is None:
        elapsed = mission.get("elapsed_seconds")
    if elapsed:
        parts.append(f"Elapsed {elapsed}s")
    return "\n\n".join(parts)[:4000]


def _tg_log(handler: str, mission_id: str | None = None) -> None:
    print(f"tg {handler} {mission_id or '-'}")


def _needed(mission: dict) -> dict | None:
    for ap in mission.get("approvals") or []:
        if ap.get("status") == "needed":
            return ap
    return None


def _unlink_copy() -> str:
    return (
        f"Open {_signin_url()} and Continue with Telegram first.\n"
        f"{_desk_url()}"
    )


async def start_telegram() -> None:
    global _APP, _STARTED
    if _STARTED or _APP is not None:
        return
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return
    _STARTED = True
    try:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
        from telegram.error import BadRequest
        from telegram.ext import (
            Application,
            CallbackQueryHandler,
            CommandHandler,
            ContextTypes,
            MessageHandler,
            filters,
        )
    except ImportError:
        _STARTED = False
        print("python-telegram-bot not installed; skipping Telegram.")
        return

    def _clear_await(context: ContextTypes.DEFAULT_TYPE) -> None:
        context.user_data.pop("await_new", None)

    def _action_keyboard(approval_id: str, *, open_desk: bool) -> InlineKeyboardMarkup | None:
        if not approval_id:
            return None
        row = [
            InlineKeyboardButton("Do it", callback_data=f"do:{approval_id}"),
            InlineKeyboardButton("Keep as draft", callback_data=f"draft:{approval_id}"),
        ]
        rows = [row]
        if open_desk:
            origin = _origin()
            if origin.startswith("http"):
                rows.append([InlineKeyboardButton("Open desk", url=_desk_url())])
            else:
                rows.append([InlineKeyboardButton("Open desk", callback_data="desk")])
        return InlineKeyboardMarkup(rows)

    def _msg(update: Update):
        return update.effective_message

    def _markup_dict(markup):
        if markup is None:
            return None
        if hasattr(markup, "to_dict"):
            return markup.to_dict()
        return markup

    def _same_content(msg, text: str, reply_markup) -> bool:
        if not msg:
            return False
        current = msg.text or msg.caption or ""
        if current != text:
            return False
        return _markup_dict(getattr(msg, "reply_markup", None)) == _markup_dict(reply_markup)

    async def _reply(update: Update, text: str, reply_markup=None) -> None:
        msg = _msg(update)
        if not msg:
            return
        await msg.reply_text(text, reply_markup=reply_markup)

    async def _edit_or_send(update: Update, text: str, reply_markup=None) -> None:
        q = update.callback_query
        msg = q.message if q else None
        if not msg:
            msg = _msg(update)
        if _same_content(msg, text, reply_markup):
            return
        if q and msg:
            try:
                await q.edit_message_text(text, reply_markup=reply_markup)
                return
            except BadRequest as exc:
                low = (getattr(exc, "message", None) or str(exc) or "").lower()
                if "not modified" in low:
                    return
                stale = (
                    "too old" in low
                    or "not found" in low
                    or "can't be edited" in low
                    or "can’t be edited" in low
                    or "message_id_invalid" in low
                )
                if stale:
                    await _reply(update, text, reply_markup)
                    return
                await _reply(update, "Could not update that.")
                return
        await _reply(update, text, reply_markup)

    async def _run_intent(update: Update, intent: str) -> None:
        intent = (intent or "").strip()
        if not intent:
            await _reply(update, "What should get done?")
            return
        user = _linked_user(update)
        if not user:
            _tg_log("intent")
            await _reply(update, _unlink_copy())
            return
        try:
            mission = await asyncio.to_thread(run_mission, user["id"], intent)
        except Exception:
            _tg_log("intent")
            await _reply(update, "Could not run that.")
            return
        if is_fake_receipt(mission):
            _tg_log("intent", mission.get("id"))
            await _reply(update, "Could not run that.")
            return
        mid = str(mission.get("id") or "")
        _tg_log("intent", mid)
        waiting = mission.get("status") == "waiting_on_you"
        if waiting:
            ap = _needed(mission)
            kb = _action_keyboard(ap["id"], open_desk=True) if ap else None
            await _reply(update, mission_reply(mission), kb)
            return
        await _reply(update, compact_receipt(mission))

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        _clear_await(context)
        _tg_log("start")
        await _reply(
            update,
            "Orion Desk.\n\n"
            "Say the outcome. I will gather context, do the safe work, "
            "and ask before anything goes out.\n\n"
            "Try: I have a client meeting with Acme tomorrow at 2 PM. Handle it.\n\n"
            "Or tap Menu and pick New.",
        )

    async def new_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        context.user_data["await_new"] = True
        _tg_log("new")
        await _reply(update, "What should get done?")

    async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        _clear_await(context)
        user = _linked_user(update)
        if not user:
            _tg_log("status")
            await _reply(update, "Nothing on the desk.")
            return
        rows = [m for m in MISSIONS.list_for_user(user["id"]) if not is_fake_receipt(m)]
        if not rows:
            _tg_log("status")
            await _reply(update, "Nothing on the desk.")
            return
        _tg_log("status", rows[0].get("id"))
        await _reply(update, compact_receipt(rows[0]))

    async def approvals_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        _clear_await(context)
        user = _linked_user(update)
        if not user:
            _tg_log("approvals")
            await _reply(update, "Nothing needs your signature.")
            return
        needed = list_needed(user["id"])
        if not needed:
            _tg_log("approvals")
            await _reply(update, "Nothing needs your signature.")
            return
        _tg_log("approvals", needed[0].get("mission_id") or needed[0].get("missionId"))
        for ap in needed[:10]:
            verb = ap.get("verb_object") or ap.get("verbObject") or ""
            parent = ap.get("parent_intent") or ""
            age = ap.get("age") or "now"
            risk = ap.get("risk") or "External send"
            body = f"{verb}\n{parent}\n{age} · {risk}"
            kb = _action_keyboard(ap["id"], open_desk=False)
            await _reply(update, body, kb)

    async def desk_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        _clear_await(context)
        _tg_log("desk")
        await _reply(update, _desk_url())

    async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        _clear_await(context)
        _tg_log("help")
        await _reply(
            update,
            "/start — Orion Desk. Say the outcome.\n"
            "/new — Start a mission\n"
            "/status — Latest mission\n"
            "/approvals — What needs you\n"
            "/desk — Open the web desk\n"
            "/help — Commands\n\n"
            "or just type the outcome",
        )

    async def unknown_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        _clear_await(context)
        _tg_log("unknown")
        await _reply(update, "Unknown command. /help")

    async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        intent = ""
        if update.message:
            intent = (update.message.text or "").strip()
        if not intent:
            await _reply(update, "What should get done?")
            return
        if context.user_data.pop("await_new", None):
            await _run_intent(update, intent)
            return
        await _run_intent(update, intent)

    async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        q = update.callback_query
        if not q:
            return
        await q.answer()
        data = q.data or ""
        if data == "desk":
            _tg_log("callback-desk")
            await _reply(update, _desk_url())
            return
        if ":" not in data:
            _tg_log("callback")
            await _reply(update, "Unknown command. /help")
            return
        kind, approval_id = data.split(":", 1)
        if kind not in ("do", "draft") or not approval_id:
            _tg_log("callback")
            await _reply(update, "Unknown command. /help")
            return
        user = _linked_user(update)
        if not user:
            _tg_log("callback")
            await _edit_or_send(update, _unlink_copy())
            return
        try:
            if kind == "do":
                mission = await asyncio.to_thread(do_approval, user["id"], approval_id)
            else:
                mission = await asyncio.to_thread(keep_draft, user["id"], approval_id)
        except ApprovalError:
            _tg_log("callback")
            await _edit_or_send(update, "Not yours.")
            return
        except Exception:
            _tg_log("callback")
            await _edit_or_send(update, "Could not do that.")
            return
        if is_fake_receipt(mission):
            _tg_log("callback", mission.get("id"))
            await _edit_or_send(update, "Could not do that.")
            return
        _tg_log("callback", mission.get("id"))
        waiting = mission.get("status") == "waiting_on_you"
        if waiting:
            ap = _needed(mission)
            kb = _action_keyboard(ap["id"], open_desk=True) if ap else None
            await _edit_or_send(update, mission_reply(mission), kb)
            return
        await _edit_or_send(update, compact_receipt(mission))

    application = Application.builder().token(token).build()
    _APP = application
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("new", new_cmd))
    application.add_handler(CommandHandler("mission", new_cmd))
    application.add_handler(CommandHandler("status", status_cmd))
    application.add_handler(CommandHandler("approvals", approvals_cmd))
    application.add_handler(CommandHandler("desk", desk_cmd))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CallbackQueryHandler(on_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    application.add_handler(MessageHandler(filters.COMMAND, unknown_cmd))

    async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        err = context.error
        low = (getattr(err, "message", None) or str(err) or "").lower()
        _tg_log("error")
        if isinstance(err, BadRequest) and "not modified" in low:
            return
        print(f"tg error {type(err).__name__}")

    application.add_error_handler(on_error)

    async def _runner() -> None:
        await application.initialize()
        try:
            await application.bot.delete_webhook(drop_pending_updates=False)
        except Exception:
            pass
        await application.start()
        await application.updater.start_polling()
        print("tg polling once")

    asyncio.create_task(_runner())
