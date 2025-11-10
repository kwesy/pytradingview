import argparse
from datetime import timedelta, datetime
import math
import random
import re

def genSessionID(type='xs'):
    id = ''
    c = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    for i in range(12):
        id += c[math.floor(random.random()*len(c))]
    return  f'{type}_{id}'

def strip_html_tags(text):
    return re.sub(r"<[^>]+>", "", text)

def parse_datetime(value: str) -> datetime:
    now = datetime.now()

    if value.lower() == 'now':
        return now

    match = re.match(r'^([+-])(\d+)([smhdw])$', value)
    if match:
        sign, amount, unit = match.groups()
        amount = int(amount)
        delta = {
            's': timedelta(seconds=amount),
            'm': timedelta(minutes=amount),
            'h': timedelta(hours=amount),
            'd': timedelta(days=amount),
            'w': timedelta(weeks=amount),
        }[unit]

        return now + delta if sign == '+' else now - delta

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        pass

    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        pass

    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M")
    except ValueError:
        pass

    try:
        return datetime.fromtimestamp(int(value))
    except (ValueError, OSError):
        pass

    raise argparse.ArgumentTypeError(
        f"Invalid date/time format: '{value}'. Try ISO 8601, YYYY-MM-DD, timestamp, or relative format like -7d"
    )
