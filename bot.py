import os
import argparse
from typing import Optional, Tuple
from datetime import datetime, timedelta
from telegram import Bot
from telegram.request import HTTPXRequest


def resolve_token() -> str:
    raw = os.getenv("TELEGRAM_TOKEN")
    if not raw:
        raise ValueError("Не задан токен. Укажите TELEGRAM_TOKEN (env).")
    # Убираем пробелы/переносы, если токен случайно разбили при вставке в cron или shell
    token = "".join(raw.split())
    if not token:
        raise ValueError("TELEGRAM_TOKEN пустой после очистки.")
    return token


def build_bot(token: str) -> Bot:
    # По умолчанию в PTB connect/read ~5 с — на «медленных» или заблокированных сетях часто падает.
    connect = float(os.getenv("TELEGRAM_CONNECT_TIMEOUT", "60"))
    read = float(os.getenv("TELEGRAM_READ_TIMEOUT", "60"))
    request = HTTPXRequest(connect_timeout=connect, read_timeout=read)
    return Bot(token=token, request=request)

def get_next_friday_and_sunday():
    today = datetime.now()

    # Находим ближайшую пятницу
    days_until_friday = (4 - today.weekday()) % 7
    if days_until_friday == 0:
        days_until_friday = 7  # Если сегодня пятница, берём следующую
    next_friday = today + timedelta(days=days_until_friday)

    # Находим ближайшее воскресенье
    days_until_sunday = (6 - today.weekday()) % 7
    if days_until_sunday == 0:
        days_until_sunday = 7  # Если сегодня воскресенье, берём следующее
    next_sunday = today + timedelta(days=days_until_sunday)

    return next_friday, next_sunday


def resolve_once_target(args: argparse.Namespace) -> Tuple[int, Optional[int]]:
    chat_id = args.chat_id
    thread_id = args.thread_id
    if chat_id is None:
        raise ValueError("Не задан chat_id. Укажите --chat-id.")
    return int(chat_id), (int(thread_id) if thread_id is not None else None)


async def send_weekend_polls(
    *,
    bot: Bot,
    chat_id: int,
    message_thread_id: Optional[int] = None,
    reply_to_message_id: Optional[int] = None,
) -> None:
    next_friday, next_sunday = get_next_friday_and_sunday()

    friday_date = next_friday.strftime('%d-%m')
    sunday_date = next_sunday.strftime('%d-%m')

    options = ["Буду", "Буду, но позже"]

    question_friday = f"Настолки {friday_date} (Пятница) в 18:30"
    await bot.send_poll(
        chat_id=chat_id,
        message_thread_id=message_thread_id,
        question=question_friday,
        options=options,
        is_anonymous=False,
        reply_to_message_id=reply_to_message_id,
    )

    question_sunday = f"Настолки {sunday_date} (Воскресенье) в 14:00"
    await bot.send_poll(
        chat_id=chat_id,
        message_thread_id=message_thread_id,
        question=question_sunday,
        options=options,
        is_anonymous=False,
        reply_to_message_id=reply_to_message_id,
    )


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Create Telegram weekend polls and exit")
    p.add_argument(
        "--chat-id",
        type=int,
        help="chat_id (например -1002891058173).",
    )
    p.add_argument(
        "--thread-id",
        type=int,
        default=None,
        help="message_thread_id (id топика).",
    )
    return p


async def run_once_createpoll(args: argparse.Namespace) -> None:
    token = resolve_token()
    chat_id, thread_id = resolve_once_target(args)

    bot = build_bot(token)
    await send_weekend_polls(
        bot=bot,
        chat_id=chat_id,
        message_thread_id=thread_id,
        reply_to_message_id=None,
    )


if __name__ == '__main__':
    args = build_arg_parser().parse_args()

    import asyncio

    asyncio.run(run_once_createpoll(args))
