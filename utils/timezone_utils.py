from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from django.utils import timezone as django_timezone

NOVOSIBIRSK = ZoneInfo('Asia/Novosibirsk')

def utc_to_novosibirsk(dt):
    """Перевести UTC datetime в Новосибирск"""
    if dt is None:
        return None
    if django_timezone.is_aware(dt):
        return dt.astimezone(NOVOSIBIRSK)
    return django_timezone.make_aware(dt).astimezone(NOVOSIBIRSK)

def novosibirsk_to_utc(day, month, year, hour, minute):
    """Локальное время Новосибирска -> UTC"""
    local = datetime(year, month, day, hour, minute, tzinfo=NOVOSIBIRSK)
    # Используем datetime.timezone.utc вместо django.utils.timezone.utc
    return local.astimezone(timezone.utc)

def format_novosibirsk(dt):
    """Форматировать datetime по Новосибирску"""
    if dt is None:
        return None
    nsk = utc_to_novosibirsk(dt)
    return nsk.strftime('%d.%m.%Y %H:%M')

def parse_datetime_novosibirsk(date_str, time_str):
    """Парсит дату/время (ДД.ММ.ГГГГ, ЧЧ:ММ) как время в Новосибирске, возвращает UTC"""
    if not date_str or not time_str:
        return None
    try:
        parts = date_str.strip().split('.')
        tparts = time_str.strip().split(':')
        if len(parts) == 3 and len(tparts) >= 2:
            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
            h, m = int(tparts[0]), int(tparts[1])
            return novosibirsk_to_utc(day, month, year, h, m)
    except (ValueError, IndexError):
        pass
    return None